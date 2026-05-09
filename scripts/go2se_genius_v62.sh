#!/bin/bash
# GO2SE Genius v6.2 - 资金效率最大化版
# 币种间条件调配 + 卖出后杠杆加码 + 资金效率优化
LOG_FILE="/tmp/go2se_v62.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "GO2SE Genius v6.2 $(date)"
echo "资金效率最大化版"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== v6.2 资金效率配置 ==========
CONFIG = {
    # 资金分配
    'max_coins': 3,           # 最多持有3个币种
    'concentration_ratio': 0.5,  # 集中仓位50%
    
    # 币种调配
    'rebalance_threshold': 0.2,  # 币种偏离20%则调配
    'top_coin_ratio': 0.7,      # 最强币种占70%
    
    # 卖出加杠杆
    'leverage_after_sell': 2,   # 卖出后2x杠杆加码
    'leverage_ratio': 0.3,      # 杠杆加码比例
    
    # 止盈止损
    'take_profit': 0.08,        # 8%止盈
    'stop_loss': 0.03,          # 3%止损
    
    # 信号
    'bb_buy': 25, 'bb_sell': 80,
    'zt_threshold': -1.5, 'ft_threshold': 2.0,
    'rsi_buy': 40, 'rsi_sell': 60,
    
    'min_notional': 10,
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
        return {'price':float(d['lastPrice']),'chg':float(d['priceChangePercent'])}
    except: return None

def get_klines(sym, interval='1h', limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]
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
    if len(highs) < period: return 50
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    return round(round(qty/10**(-p))*10**(-p), p)

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

def analyze_coin(c):
    klines = get_klines(f'{c}USDT', '1h', 100)
    d = get_24hr(f'{c}USDT')
    if not klines or not d: return None
    closes = [k['close'] for k in klines]
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]
    rsi = get_rsi(closes, 7)
    bb_pos = bollinger_pos(d['price'], highs, lows, 20)
    return {'price':d['price'],'chg':d['chg'],'rsi':rsi,'bb_pos':bb_pos}

# ========== 主程序 ==========
print("\n【v6.2 全域扫描】")
spot = get_spot()
cross, level = get_cross()
prices = {}
analyses = {}
for c in COINS:
    a = analyze_coin(c)
    if a: analyses[c] = a; prices[c] = a['price']
    time.sleep(0.1)

total_spot = sum(spot.get(c, 0)*prices.get(c,0) for c in COINS) + spot.get('USDT',0)
total_cross = sum(cross.get(c,0)*prices.get(c,0) for c in COINS) + cross.get('USDT',0)
total_value = total_spot + total_cross

print(f"总资产: ${total_value:.2f}")
print(f"SPOT: ${total_spot:.2f} | CROSS: ${total_cross:.2f}")

# ========== 信号评分 ==========
print("\n【v6.2 信号评分】")
signals = []
for c in COINS:
    if c not in analyses: continue
    a = analyses[c]
    
    score = 0
    reasons = []
    
    # 买入信号
    if a['bb_pos'] < CONFIG['bb_buy']: score += 30; reasons.append(f"BB{a['bb_pos']:.0f}%")
    if a['chg'] < CONFIG['zt_threshold']: score += 25; reasons.append(f"正T{a['chg']:.1f}%")
    if a['rsi'] < CONFIG['rsi_buy']: score += 20; reasons.append(f"RSI{a['rsi']:.0f}")
    if a['rsi'] < 30: score += 15; reasons.append("RSI极")
    if a['bb_pos'] < 15: score += 10; reasons.append("BB极")
    
    # 卖出信号
    if a['bb_pos'] > CONFIG['bb_sell']: score -= 25; reasons.append(f"BB高{a['bb_pos']:.0f}%")
    if a['chg'] > CONFIG['ft_threshold']: score -= 20; reasons.append(f"反T{a['chg']:.1f}%")
    if a['rsi'] > CONFIG['rsi_sell']: score -= 20; reasons.append(f"RSI{a['rsi']:.0f}")
    
    signals.append({
        'coin': c, 'price': a['price'], 'chg': a['chg'],
        'rsi': a['rsi'], 'bb_pos': a['bb_pos'],
        'score': score, 'reasons': reasons,
        'spot_qty': spot.get(c, 0), 'cross_qty': cross.get(c, 0)
    })

signals.sort(key=lambda x: -x['score'])

print(f"\n{'币种':6} {'评分':6} {'价格':12} {'BB':6} {'RSI':6} {'涨跌':8} {'信号'}")
print("-"*70)
for s in signals:
    reason_str = ' '.join(s['reasons'][:3])
    print(f"{s['coin']:6} {s['score']:>+6.0f} ${s['price']:>10.4f} {s['bb_pos']:>5.1f}% {s['rsi']:>5.1f} {s['chg']:>+7.2f}% {reason_str[:20]}")

# ========== 币种调配分析 ==========
print("\n【v6.2 币种调配分析】")

# 当前持仓分布
holdings = [(s['coin'], s['spot_qty'] * prices.get(s['coin'], 0)) for s in signals if s['spot_qty'] > 0.1]
holdings.sort(key=lambda x: -x[1])
total_holding_value = sum(h for _, h in holdings)

print("当前持仓分布:")
for coin, value in holdings:
    ratio = value / total_holding_value * 100 if total_holding_value > 0 else 0
    print(f"  {coin}: ${value:.2f} ({ratio:.1f}%)")

# 目标分布: 集中到评分最高的币种
if len(signals) > 0:
    top_coin = signals[0]['coin']
    print(f"\n最强币种: {top_coin} (评分:{signals[0]['score']})")
    
    # 需要卖出的币种(低评分)
    for s in signals:
        if s['coin'] != top_coin and s['spot_qty'] > 1:
            ratio = s['spot_qty'] * prices[s['coin']] / total_holding_value * 100 if total_holding_value > 0 else 0
            if ratio > 20:  # 偏离20%以上
                print(f"建议卖出: {s['coin']} ({ratio:.1f}% → 0%)")

# ========== 执行交易 ==========
print("\n【v6.2 执行交易】")
trades = []

# 1. 币种集中调配 - 卖出低评分币种
print("\n--- 币种集中调配 ---")
for s in signals[2:]:  # 排名靠后的币种
    if s['spot_qty'] > 1:
        ratio = s['spot_qty'] * prices[s['coin']] / total_holding_value * 100 if total_holding_value > 0 else 0
        if ratio > 20:  # 持仓>20%则卖出
            sell_qty = round_qty(s['spot_qty'] * 0.7, s['coin'])
            if sell_qty > 0:
                r = spot_order(f"{s['coin']}USDT", 'SELL', sell_qty)
                if r and 'orderId' in r:
                    proceeds = sell_qty * s['price']
                    print(f"✅ 卖出{s['coin']}: {sell_qty} ({ratio:.1f}%→{ratio*0.3:.1f}%) 获得${proceeds:.2f}")
                    trades.append({'type':'REBALANCE_SELL','coin':s['coin'],'qty':sell_qty,'proceeds':proceeds})
                    time.sleep(1)

# 2. 卖出后杠杆加码买入最强币种
print("\n--- 卖出后杠杆加码 ---")
if len(signals) > 0 and len(trades) > 0:
    top = signals[0]
    
    # 从卖出收益中提取加码资金
    leverage_fund = sum(t.get('proceeds', 0) for t in trades) * CONFIG['leverage_ratio']
    
    if leverage_fund > CONFIG['min_notional'] and cross.get('USDT', 0) > 10:
        # CROSS借入加码
        borrow_amt = min(leverage_fund * (CONFIG['leverage_after_sell'] - 1), 50)
        r = cross_borrow('USDT', borrow_amt)
        if r and r.get('tranId'):
            print(f"✅ 杠杆借入USDT: ${borrow_amt:.2f}")
            time.sleep(1)
            
            # 买入最强币种
            buy_qty = round_qty((leverage_fund + borrow_amt) / top['price'], top['coin'])
            if buy_qty > 0:
                r = cross_order(f"{top['coin']}USDT", 'BUY', buy_qty)
                if r and 'orderId' in r:
                    print(f"✅ 杠杆加码买入{top['coin']}: {buy_qty} @ ${top['price']:.4f}")
                    trades.append({'type':'LEVERAGE_ADD','coin':top['coin'],'qty':buy_qty,'leverage':CONFIG['leverage_after_sell']})
                    time.sleep(1)

# 3. SPOT低吸最强币种
print("\n--- SPOT低吸 ---")
new_spot = get_spot()
for s in signals[:2]:  # 评分最高的币种
    if s['score'] > 50 and new_spot.get('USDT', 0) > CONFIG['min_notional']:
        invest = new_spot.get('USDT', 0) * 0.8
        buy_qty = round_qty(invest / s['price'], s['coin'])
        if buy_qty > 0:
            r = spot_order(f"{s['coin']}USDT", 'BUY', buy_qty)
            if r and 'orderId' in r:
                print(f"✅ SPOT低吸{s['coin']}: {buy_qty} @ ${s['price']:.4f}")
                trades.append({'type':'SPOT_BUY','coin':s['coin'],'qty':buy_qty})
                time.sleep(1)

# 4. 高抛止盈
print("\n--- 高抛止盈 ---")
for s in signals:
    if s['score'] < -30 and s['spot_qty'] > 1:
        sell_qty = round_qty(s['spot_qty'] * 0.5, s['coin'])
        if sell_qty > 0:
            r = spot_order(f"{s['coin']}USDT", 'SELL', sell_qty)
            if r and 'orderId' in r:
                print(f"✅ 高抛{s['coin']}: {sell_qty} @ ${s['price']:.4f}")
                trades.append({'type':'TAKE_PROFIT','coin':s['coin'],'qty':sell_qty})
                time.sleep(1)

# ========== 验证 ==========
print("\n【v6.2 验证】")
final_spot = get_spot()
final_cross, final_level = get_cross()

spot_total = sum(final_spot.get(c,0)*prices.get(c,0) for c in COINS) + final_spot.get('USDT',0)
cross_total = sum(final_cross.get(c,0)*prices.get(c,0) for c in COINS) + final_cross.get('USDT',0)
final_total = spot_total + cross_total

print(f"  执行: {len(trades)}笔")
print(f"  资产: ${total_value:.2f} → ${final_total:.2f} ({(final_total-total_value)/total_value*100:+.2f}%)")
print(f"  SPOT: ${spot_total:.2f} | CROSS: ${cross_total:.2f}")
print(f"  保证金率: {final_level:.2f}")

with open('/tmp/go2se_v62_log.json', 'w') as f:
    json.dump({'version':'v6.2','trades':trades,'signals':[{'coin':s['coin'],'score':s['score']} for s in signals]}, f, indent=2)

print("\n✅ GO2SE Genius v6.2 完成!")
PYEOF
