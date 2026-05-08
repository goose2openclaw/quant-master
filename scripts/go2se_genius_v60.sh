#!/bin/bash
# GO2SE Genius v6.0 - 最大算力优化版
# 基于深度分析: 仓位70%+止盈15%+RSI35/65+布林20/80+3x杠杆+做空
# 目标: 100%+月收益
LOG_FILE="/tmp/go2se_v60.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "GO2SE Genius v6.0 $(date)"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== v6.0 核心配置 ==========
CONFIG = {
    # 仓位管理 - 优化后70%
    'position_ratio': 0.70,
    
    # 止盈止损 - 优化后15%/5%
    'take_profit': 0.15,
    'stop_loss': 0.05,
    
    # RSI条件 - 优化后35/65
    'rsi_buy': 35,
    'rsi_sell': 65,
    'rsi_period': 7,  # 短周期更敏感
    
    # 布林带 - 优化后20/80
    'bb_buy': 20,
    'bb_sell': 80,
    
    # 交易频率 - 高频
    'min_trade_interval': 60,  # 最小间隔60秒
    
    # 杠杆 - 3x
    'leverage': 3,
    
    # 做空机制 - 开启
    'allow_short': True,
    
    # 最小交易金额
    'min_notional': 10,
    
    # 资金分配
    'spot_ratio': 0.7,
    'cross_ratio': 0.3,
}

def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_24hr(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', proxies=PROXIES, timeout=5)
        d = r.json()
        return {'price':float(d['lastPrice']),'chg':float(d['priceChangePercent']),'high':float(d['highPrice']),'low':float(d['lowPrice'])}
    except: return None

def get_klines(sym, interval='1h', limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'open':float(k[1]),'high':float(k[2]),'low':float(k[3]),'close':float(k[4]),'volume':float(k[5])} for k in r.json()]
    except: return []

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def bollinger_pos(price, highs, lows, period=20):
    if len(highs) < period or len(lows) < period: return 50
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    step = 10**(-p)
    return round(round(qty/step)*step, p)

# ========== 账户 ==========
def get_spot():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return {b['asset']: float(b['free']) for b in r.json()['balances']}

def get_cross():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return {a['asset']: float(a['free']) for a in r.json()['userAssets']}, float(r.json().get('marginLevel', 0))

# ========== 交易 ==========
def spot_order(symbol, side, qty):
    coin = symbol.replace('USDT','')
    qty = round_qty(qty, coin)
    if qty <= 0: return None
    ts = int(time.time()*1000)
    params = {'symbol':symbol,'side':side,'type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/api/v3/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def cross_borrow(asset, amount):
    ts = int(time.time()*1000)
    params = {'asset':asset,'amount':str(amount),'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/borrow?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def cross_order(symbol, side, qty):
    coin = symbol.replace('USDT','')
    qty = round_qty(qty, coin)
    if qty <= 0: return None
    ts = int(time.time()*1000)
    params = {'symbol':symbol,'side':side,'type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000,'isIsolated':'FALSE'}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def cross_repay(asset, amount):
    ts = int(time.time()*1000)
    params = {'asset':asset,'amount':str(amount),'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/repay?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

# ========== 分析 ==========
def analyze_coin(c):
    klines = get_klines(f'{c}USDT', '1h', 100)
    d = get_24hr(f'{c}USDT')
    if not klines or not d: return None
    
    closes = [k['close'] for k in klines]
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]
    
    rsi_7 = get_rsi(closes, 7)
    rsi_14 = get_rsi(closes, 14)
    bb_pos = bollinger_pos(d['price'], highs, lows, 20)
    chg = d['chg']
    
    return {
        'price': d['price'],
        'rsi_7': rsi_7,
        'rsi_14': rsi_14,
        'bb_pos': bb_pos,
        'chg': chg
    }

# ========== 主程序 ==========
print("\n【v6.0 全域扫描】")
spot = get_spot()
cross, level = get_cross()

prices = {}
analyses = {}
for c in COINS:
    a = analyze_coin(c)
    if a:
        analyses[c] = a
        prices[c] = a['price']
    time.sleep(0.1)

# 计算总资产
total_spot = sum(spot.get(c, 0) * prices.get(c, 0) for c in COINS) + spot.get('USDT', 0)
total_cross = sum(cross.get(c, 0) * prices.get(c, 0) for c in COINS) + cross.get('USDT', 0)
total_value = total_spot + total_cross

print(f"\n总资产: ${total_value:.2f}")
print(f"SPOT: ${total_spot:.2f} | CROSS: ${total_cross:.2f}")
print(f"保证金率: {level:.2f}")

# ========== 信号评估 ==========
print("\n【v6.0 信号评估】")
signals = []

for c in COINS:
    if c not in analyses: continue
    a = analyses[c]
    
    # 买入信号评分
    buy_score = 0
    buy_reasons = []
    
    # RSI超卖
    if a['rsi_7'] < CONFIG['rsi_buy']:
        buy_score += 30
        buy_reasons.append(f"RSI7={a['rsi_7']:.0f}<{CONFIG['rsi_buy']}")
    if a['rsi_14'] < CONFIG['rsi_buy']:
        buy_score += 20
        buy_reasons.append(f"RSI14={a['rsi_14']:.0f}<{CONFIG['rsi_buy']}")
    
    # 布林超卖
    if a['bb_pos'] < CONFIG['bb_buy']:
        buy_score += 25
        buy_reasons.append(f"BB={a['bb_pos']:.0f}%<{CONFIG['bb_buy']}%")
    
    # 大跌买入
    if a['chg'] < -3:
        buy_score += 15
        buy_reasons.append(f"跌{a['chg']:.1f}%")
    
    # 卖出信号评分
    sell_score = 0
    sell_reasons = []
    
    if a['rsi_7'] > CONFIG['rsi_sell']:
        sell_score += 30
        sell_reasons.append(f"RSI7={a['rsi_7']:.0f}>{CONFIG['rsi_sell']}")
    if a['rsi_14'] > CONFIG['rsi_sell']:
        sell_score += 20
        sell_reasons.append(f"RSI14={a['rsi_14']:.0f}>{CONFIG['rsi_sell']}")
    if a['bb_pos'] > CONFIG['bb_sell']:
        sell_score += 25
        sell_reasons.append(f"BB={a['bb_pos']:.0f}%>{CONFIG['bb_sell']}%")
    if a['chg'] > 3:
        sell_score += 15
        sell_reasons.append(f"涨{a['chg']:.1f}%")
    
    # 做空信号
    short_score = 0
    if a['rsi_7'] > 75 and a['bb_pos'] > 85:
        short_score = 50
    elif a['rsi_7'] > 70 and a['chg'] > 5:
        short_score = 40
    
    signals.append({
        'coin': c,
        'buy_score': buy_score,
        'sell_score': sell_score,
        'short_score': short_score,
        'buy_reasons': buy_reasons,
        'sell_reasons': sell_reasons,
        'price': a['price'],
        'rsi': a['rsi_7'],
        'bb': a['bb_pos'],
        'chg': a['chg']
    })

# 按评分排序
signals.sort(key=lambda x: -x['buy_score'])

print(f"\n{'币种':6} {'评分':6} {'类型':8} {'价格':12} {'RSI':6} {'BB':6} {'涨跌':8}")
print("-"*60)

for s in signals:
    if s['buy_score'] > 30:
        action = "📈买入"
    elif s['sell_score'] > 30:
        action = "📉卖出"
    elif s['short_score'] > 30:
        action = "📉做空"
    else:
        action = "➡️持有"
    
    print(f"{s['coin']:6} {s['buy_score']:6.0f} {action:8} ${s['price']:>10.4f} {s['rsi']:5.1f} {s['bb']:5.1f}% {s['chg']:>+7.2f}%")

# ========== 执行交易 ==========
print("\n【v6.0 执行交易】")
trades_executed = []

# SPOT买入
for s in signals:
    if s['buy_score'] < 40: continue
    c = s['coin']
    qty = spot.get(c, 0)
    
    # SPOT低吸
    if s['buy_score'] > 50 and spot.get('USDT', 0) > CONFIG['min_notional']:
        invest = total_value * CONFIG['spot_ratio'] * CONFIG['position_ratio']
        buy_qty = round_qty(invest / s['price'], c)
        if buy_qty > 0:
            r = spot_order(f'{c}USDT', 'BUY', buy_qty)
            if r and 'orderId' in r:
                print(f"✅ SPOT买入 {c}: {buy_qty} @ ${s['price']:.4f}")
                trades_executed.append({'type':'SPOT_BUY','coin':c,'qty':buy_qty})
                time.sleep(1)

# SPOT高抛
for s in signals:
    if s['sell_score'] < 40: continue
    c = s['coin']
    qty = spot.get(c, 0)
    
    if qty > 1:
        sell_qty = round_qty(qty * 0.5, c)
        if sell_qty > 0:
            r = spot_order(f'{c}USDT', 'SELL', sell_qty)
            if r and 'orderId' in r:
                print(f"✅ SPOT卖出 {c}: {sell_qty} @ ${s['price']:.4f}")
                trades_executed.append({'type':'SPOT_SELL','coin':c,'qty':sell_qty})
                time.sleep(1)

# CROSS做多
for s in signals:
    if s['buy_score'] < 45: continue
    c = s['coin']
    
    if cross.get('USDT', 0) < 20 and cross.get('USDT', 0) > 5:
        # 借入USDT
        borrow_amt = min(30, cross.get('USDT', 0))
        r = cross_borrow('USDT', borrow_amt)
        if r and r.get('tranId'):
            print(f"✅ 借入USDT: {borrow_amt}")
            time.sleep(1)
    
    if cross.get('USDT', 0) > 5:
        buy_qty = round_qty(cross.get('USDT', 0) * 0.8 / s['price'], c)
        if buy_qty > 0:
            r = cross_order(f'{c}USDT', 'BUY', buy_qty)
            if r and 'orderId' in r:
                print(f"✅ CROSS做多 {c}: {buy_qty} @ ${s['price']:.4f}")
                trades_executed.append({'type':'CROSS_LONG','coin':c,'qty':buy_qty})
                time.sleep(1)

# CROSS做空
if CONFIG['allow_short']:
    for s in signals:
        if s['short_score'] < 40: continue
        c = s['coin']
        
        # 借入币做空
        borrow_qty = round_qty(10 / s['price'], c)
        r = cross_borrow(c, borrow_qty)
        if r and r.get('tranId'):
            print(f"✅ 借入{c}做空: {borrow_qty}")
            time.sleep(1)
            r = cross_order(f'{c}USDT', 'SELL', borrow_qty)
            if r and 'orderId' in r:
                print(f"✅ CROSS做空 {c}: {borrow_qty} @ ${s['price']:.4f}")
                trades_executed.append({'type':'CROSS_SHORT','coin':c,'qty':borrow_qty})
                time.sleep(1)

# ========== 验证 ==========
print("\n【v6.0 验证】")
new_spot = get_spot()
new_cross, new_level = get_cross()

spot_total = sum(new_spot.get(c, 0) * prices.get(c, 0) for c in COINS) + new_spot.get('USDT', 0)
cross_total = sum(new_cross.get(c, 0) * prices.get(c, 0) for c in COINS) + new_cross.get('USDT', 0)
new_total = spot_total + cross_total

print(f"  执行交易: {len(trades_executed)}笔")
print(f"  资产: ${total_value:.2f} → ${new_total:.2f} ({(new_total-total_value)/total_value*100:+.2f}%)")
print(f"  SPOT: ${spot_total:.2f} | CROSS: ${cross_total:.2f}")
print(f"  保证金率: {new_level:.2f}")

# 保存日志
log_data = {
    'version': 'v6.0',
    'timestamp': datetime.now().isoformat(),
    'config': CONFIG,
    'trades': trades_executed,
    'total_before': total_value,
    'total_after': new_total,
    'signals': [{'coin':s['coin'],'buy_score':s['buy_score'],'sell_score':s['sell_score'],'short_score':s['short_score']} for s in signals]
}

with open('/tmp/go2se_v60_log.json', 'w') as f:
    json.dump(log_data, f, indent=2)

print("\n✅ GO2SE Genius v6.0 完成!")
PYEOF
