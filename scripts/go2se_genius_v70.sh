#!/bin/bash
# GO2SE Genius v7.0 - 上帝视角全知版
# 全局扫描 + 自主迭代 + 主动决策 + 自动执行
LOG_FILE="/tmp/go2se_v70.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "GO2SE Genius v7.0 $(date)"
echo "上帝视角全知版"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime
import subprocess

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== v7.0 上帝视角配置 ==========
CONFIG = {
    # 资源调配
    'spot_ratio': 0.7,
    'cross_ratio': 0.3,
    'reserve_ratio': 0.1,  # 预留10%
    
    # 全局优化
    'max_positions': 3,      # 最多3个持仓
    'concentration': 0.6,    # 集中度60%
    
    # 止盈止损
    'take_profit': 0.10,     # 10%止盈
    'stop_loss': 0.04,       # 4%止损
    
    # 信号
    'bb_buy': 25, 'bb_sell': 80,
    'zt_threshold': -1.5, 'ft_threshold': 2.0,
    'rsi_buy': 40, 'rsi_sell': 60,
    
    # 执行
    'min_notional': 10,
    'leverage': 2,
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

# ========== 上帝视角扫描 ==========
print("\n" + "="*70)
print("【v7.0 上帝视角 - 全局扫描】")
print("="*70)

spot = get_spot()
cross, level = get_cross()
prices = {}
analyses = {}

for c in COINS:
    a = analyze_coin(c)
    if a: analyses[c] = a; prices[c] = a['price']
    time.sleep(0.1)

total_spot = sum(spot.get(c,0)*prices.get(c,0) for c in COINS) + spot.get('USDT',0)
total_cross = sum(cross.get(c,0)*prices.get(c,0) for c in COINS) + cross.get('USDT',0)
total_value = total_spot + total_cross

print(f"\n【上帝视角 - 资源总览】")
print(f"  总资产: ${total_value:.2f}")
print(f"  SPOT: ${total_spot:.2f} ({total_spot/total_value*100:.1f}%)")
print(f"  CROSS: ${total_cross:.2f} ({total_cross/total_value*100:.1f}%)")
print(f"  保证金率: {level:.2f}")

# ========== 全局信号评分 ==========
print("\n【上帝视角 - 全局信号】")

signals = []
for c in COINS:
    if c not in analyses: continue
    a = analyses[c]
    
    score = 0
    tags = []
    
    # 买入信号
    if a['bb_pos'] < CONFIG['bb_buy']: score += 30; tags.append(f"BB{a['bb_pos']:.0f}%")
    if a['chg'] < CONFIG['zt_threshold']: score += 25; tags.append(f"正T{a['chg']:.1f}%")
    if a['rsi'] < CONFIG['rsi_buy']: score += 20; tags.append(f"RSI{a['rsi']:.0f}")
    if a['rsi'] < 30: score += 15; tags.append("RSI极")
    
    # 卖出信号
    if a['bb_pos'] > CONFIG['bb_sell']: score -= 25; tags.append(f"BB高{a['bb_pos']:.0f}%")
    if a['chg'] > CONFIG['ft_threshold']: score -= 20; tags.append(f"反T{a['chg']:.1f}%")
    if a['rsi'] > CONFIG['rsi_sell']: score -= 20; tags.append(f"RSI{a['rsi']:.0f}")
    
    signals.append({
        'coin': c, 'price': a['price'], 'chg': a['chg'],
        'rsi': a['rsi'], 'bb_pos': a['bb_pos'],
        'score': score, 'tags': tags,
        'spot_qty': spot.get(c, 0), 'cross_qty': cross.get(c, 0)
    })

signals.sort(key=lambda x: -x['score'])

print(f"\n{'排名':4} {'币种':6} {'评分':6} {'价格':12} {'RSI':6} {'BB':6} {'信号'}")
print("-"*70)
for i, s in enumerate(signals, 1):
    tag_str = ' '.join(s['tags'][:3])
    print(f"  {i:2}. {s['coin']:6} {s['score']:>+6.0f} ${s['price']:>10.4f} {s['rsi']:>5.1f} {s['bb_pos']:>5.1f}% {tag_str[:25]}")

# ========== 资源最优调配 ==========
print("\n【上帝视角 - 资源最优调配】")

# 当前持仓价值
holdings = []
for s in signals:
    spot_val = s['spot_qty'] * s['price']
    cross_val = s['cross_qty'] * s['price']
    total_val = spot_val + cross_val
    if total_val > 1:
        holdings.append({
            'coin': s['coin'],
            'spot_val': spot_val,
            'cross_val': cross_val,
            'total_val': total_val,
            'ratio': total_val / total_value * 100,
            'score': s['score']
        })

holdings.sort(key=lambda x: -x['total_val'])

print("\n当前持仓排名:")
for i, h in enumerate(holdings, 1):
    print(f"  {i}. {h['coin']:6} ${h['total_val']:.2f} ({h['ratio']:.1f}%) 评分:{h['score']}")

# 调配建议
print("\n调配建议:")
for h in holdings:
    if h['ratio'] > 30 and h['score'] < 0:
        print(f"  ⚠️ {h['coin']}: 持仓{h['ratio']:.1f}%偏高, 评分{h['score']}偏低 → 建议卖出")
    elif h['ratio'] < 10 and h['score'] > 50:
        print(f"  💡 {h['coin']}: 持仓{h['ratio']:.1f}%偏低, 评分{h['score']}高 → 建议加仓")

# ========== 自主迭代决策 ==========
print("\n【上帝视角 - 自主决策】")

# 决策矩阵
decisions = []

# 决策1: 卖出低分持仓
for s in signals:
    if s['score'] < -20 and s['spot_qty'] > 1:
        decisions.append(('SELL_SPOT', s['coin'], s['spot_qty'] * 0.5, s['price'], '低分止损'))

# 决策2: 卖出高分持仓(止盈)
for s in signals:
    if s['score'] > 60 and s['spot_qty'] > 1:
        pnl_est = s['chg']  # 简化估算
        if pnl_est > 5:
            decisions.append(('TAKE_PROFIT', s['coin'], s['spot_qty'] * 0.5, s['price'], '高分止盈'))

# 决策3: 买入最强币种
top_coin = signals[0] if signals else None
if top_coin and top_coin['score'] > 50 and spot.get('USDT', 0) > CONFIG['min_notional']:
    buy_amount = spot.get('USDT', 0) * 0.5
    decisions.append(('BUY_STRONG', top_coin['coin'], buy_amount / top_coin['price'], top_coin['price'], f"最强{top_coin['coin']}"))

# 决策4: 杠杆加码
if len(decisions) > 0 and cross.get('USDT', 0) > 20:
    for d in decisions:
        if d[0] == 'SELL_SPOT':
            proceeds = d[2] * d[3]
            lev_amount = min(proceeds * 0.3, cross.get('USDT', 0))
            if lev_amount > 10:
                decisions.append(('LEVERAGE_BUY', top_coin['coin'] if top_coin else 'BTC', lev_amount / (top_coin['price'] if top_coin else 0), top_coin['price'] if top_coin else 0, '卖出加杠杆'))

print("\n决策列表:")
for i, d in enumerate(decisions, 1):
    print(f"  {i}. {d[0]} {d[1]}: {d[2]:.4f} @ ${d[3]:.4f} ({d[4]})")

# ========== 自动执行 ==========
print("\n【上帝视角 - 自动执行】")
executions = []

for d in decisions[:5]:  # 最多执行5个
    action, coin, qty, price, reason = d
    
    if action == 'SELL_SPOT':
        qty = round_qty(qty, coin)
        if qty > 0:
            r = spot_order(f'{coin}USDT', 'SELL', qty)
            if r and 'orderId' in r:
                print(f"  ✅ {reason}: 卖出{coin} {qty}")
                executions.append({'action':action,'coin':coin,'qty':qty,'price':price})
                time.sleep(1)
    
    elif action == 'TAKE_PROFIT':
        qty = round_qty(qty, coin)
        if qty > 0:
            r = spot_order(f'{coin}USDT', 'SELL', qty)
            if r and 'orderId' in r:
                print(f"  ✅ {reason}: 止盈{coin} {qty}")
                executions.append({'action':action,'coin':coin,'qty':qty,'price':price})
                time.sleep(1)
    
    elif action == 'BUY_STRONG':
        qty = round_qty(qty, coin)
        if qty > 0:
            r = spot_order(f'{coin}USDT', 'BUY', qty)
            if r and 'orderId' in r:
                print(f"  ✅ {reason}: 买入{coin} {qty}")
                executions.append({'action':action,'coin':coin,'qty':qty,'price':price})
                time.sleep(1)
    
    elif action == 'LEVERAGE_BUY':
        if qty > 0 and cross.get('USDT', 0) > 10:
            borrow = min(qty * 0.5, 30)
            r = cross_borrow('USDT', borrow)
            if r and r.get('tranId'):
                print(f"  ✅ 杠杆借入USDT: ${borrow:.2f}")
                time.sleep(1)
                buy_qty = round_qty((qty + borrow) / price, coin)
                r = cross_order(f'{coin}USDT', 'BUY', buy_qty)
                if r and 'orderId' in r:
                    print(f"  ✅ 杠杆买入{coin}: {buy_qty}")
                    executions.append({'action':action,'coin':coin,'qty':buy_qty,'price':price})
                time.sleep(1)

# ========== 验证 ==========
print("\n【上帝视角 - 验证】")
final_spot = get_spot()
final_cross, final_level = get_cross()

spot_total = sum(final_spot.get(c,0)*prices.get(c,0) for c in COINS) + final_spot.get('USDT',0)
cross_total = sum(final_cross.get(c,0)*prices.get(c,0) for c in COINS) + final_cross.get('USDT',0)
final_total = spot_total + cross_total

print(f"  执行: {len(executions)}笔")
print(f"  资产: ${total_value:.2f} → ${final_total:.2f} ({(final_total-total_value)/total_value*100:+.2f}%)")
print(f"  SPOT: ${spot_total:.2f} | CROSS: ${cross_total:.2f}")
print(f"  保证金率: {final_level:.2f}")

# 保存
with open('/tmp/go2se_v70_log.json', 'w') as f:
    json.dump({
        'version': 'v7.0',
        'timestamp': datetime.now().isoformat(),
        'decisions': decisions,
        'executions': executions,
        'total_before': total_value,
        'total_after': final_total
    }, f, indent=2)

print("\n" + "="*70)
print("✅ GO2SE Genius v7.0 上帝视角全知版 完成!")
print("="*70)
PYEOF
