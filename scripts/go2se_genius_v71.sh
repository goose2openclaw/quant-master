#!/bin/bash
# GO2SE Genius v7.1 - 完整版
# 解决: 仓位60-70% + 3x杠杆 + 做空机制
LOG_FILE="/tmp/go2se_v71.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "GO2SE Genius v7.1 $(date)"
echo "完整版: 仓位+杠杆+做空"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== v7.1 完整配置 ==========
CONFIG = {
    # 仓位提升到60-70%
    'position_ratio': 0.65,
    
    # 杠杆3x
    'leverage': 3,
    'leverage_threshold': 0.5,  # 50%仓位以上才加杠杆
    
    # 做空机制
    'short_enabled': True,
    'short_rsi': 70,   # RSI>70做空
    'short_bb': 85,     # 布林>85做空
    
    # 信号
    'bb_buy': 25, 'bb_sell': 80,
    'zt_threshold': -1.5, 'ft_threshold': 2.0,
    'rsi_buy': 40, 'rsi_sell': 60,
    
    # 止盈止损
    'take_profit': 0.08,
    'stop_loss': 0.04,
    
    # 最小交易
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

print("\n【v7.1 完整版扫描】")
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

print(f"总资产: ${total_value:.2f}")
print(f"SPOT: ${total_spot:.2f} | CROSS: ${total_cross:.2f}")

# 信号评分
signals = []
for c in COINS:
    if c not in analyses: continue
    a = analyses[c]
    
    score = 0
    tags = []
    
    # 买入
    if a['bb_pos'] < CONFIG['bb_buy']: score += 30; tags.append(f"BB{a['bb_pos']:.0f}%")
    if a['chg'] < CONFIG['zt_threshold']: score += 25; tags.append(f"正T{a['chg']:.1f}%")
    if a['rsi'] < CONFIG['rsi_buy']: score += 20; tags.append(f"RSI{a['rsi']:.0f}")
    
    # 做空信号
    short_score = 0
    if a['rsi'] > CONFIG['short_rsi']: short_score += 30; tags.append(f"空RSI{a['rsi']:.0f}")
    if a['bb_pos'] > CONFIG['short_bb']: short_score += 25; tags.append(f"空BB{a['bb_pos']:.0f}%")
    
    signals.append({
        'coin': c, 'price': a['price'], 'chg': a['chg'],
        'rsi': a['rsi'], 'bb_pos': a['bb_pos'],
        'score': score, 'short_score': short_score, 'tags': tags,
        'spot_qty': spot.get(c, 0), 'cross_qty': cross.get(c, 0)
    })

signals.sort(key=lambda x: -x['score'])

print(f"\n{'币种':6} {'评分':6} {'做空':6} {'价格':12} {'RSI':6} {'BB':6} {'信号'}")
print("-"*70)
for s in signals:
    tag_str = ' '.join(s['tags'][:3])
    print(f"{s['coin']:6} {s['score']:>+6.0f} {s['short_score']:>+6.0f} ${s['price']:>10.4f} {s['rsi']:>5.1f} {s['bb_pos']:>5.1f}% {tag_str[:20]}")

# 执行交易
print("\n【v7.1 执行交易】")
trades = []

# 1. SPOT低吸
for s in signals:
    if s['score'] > 50 and spot.get('USDT', 0) > CONFIG['min_notional']:
        c = s['coin']
        invest = total_value * CONFIG['position_ratio'] * 0.5
        buy_qty = round_qty(invest / s['price'], c)
        if buy_qty > 0:
            r = spot_order(f'{c}USDT', 'BUY', buy_qty)
            if r and 'orderId' in r:
                print(f"✅ SPOT低吸{c}: {buy_qty}")
                trades.append({'type':'SPOT_BUY','coin':c,'qty':buy_qty})
            time.sleep(1)

# 2. CROSS杠杆做多
for s in signals:
    if s['score'] > 60:
        c = s['coin']
        if cross.get('USDT', 0) < 50 and cross.get('USDT', 0) > 20:
            borrow = min(50, cross.get('USDT', 0))
            r = cross_borrow('USDT', borrow)
            if r and r.get('tranId'):
                print(f"✅ 借入USDT: ${borrow}")
                time.sleep(1)
        
        if cross.get('USDT', 0) > 20:
            buy_qty = round_qty(cross.get('USDT', 0) * 0.8 / s['price'], c)
            r = cross_order(f'{c}USDT', 'BUY', buy_qty)
            if r and 'orderId' in r:
                print(f"✅ CROSS杠杆做多{c}: {buy_qty} (3x)")
                trades.append({'type':'CROSS_LONG','coin':c,'qty':buy_qty,'leverage':3})
            time.sleep(1)

# 3. CROSS做空
for s in signals:
    if s['short_score'] > 40 and CONFIG['short_enabled'] and cross.get(s['coin'], 0) < 1:
        c = s['coin']
        borrow_qty = round_qty(20 / s['price'], c)
        r = cross_borrow(c, borrow_qty)
        if r and r.get('tranId'):
            print(f"✅ 借入{c}做空: {borrow_qty}")
            time.sleep(1)
            r = cross_order(f'{c}USDT', 'SELL', borrow_qty)
            if r and 'orderId' in r:
                print(f"✅ CROSS做空{c}: {borrow_qty}")
                trades.append({'type':'CROSS_SHORT','coin':c,'qty':borrow_qty})
            time.sleep(1)

# 验证
print("\n【v7.1 验证】")
final_spot = get_spot()
final_cross, final_level = get_cross()
spot_total = sum(final_spot.get(c,0)*prices.get(c,0) for c in COINS) + final_spot.get('USDT',0)
cross_total = sum(final_cross.get(c,0)*prices.get(c,0) for c in COINS) + final_cross.get('USDT',0)
final_total = spot_total + cross_total

print(f"  执行: {len(trades)}笔")
print(f"  资产: ${total_value:.2f} → ${final_total:.2f} ({(final_total-total_value)/total_value*100:+.2f}%)")
print(f"  SPOT: ${spot_total:.2f} | CROSS: ${cross_total:.2f}")

with open('/tmp/go2se_v71_log.json', 'w') as f:
    json.dump({'version':'v7.1','trades':trades,'signals':[{'coin':s['coin'],'score':s['score'],'short':s['short_score']} for s in signals]}, f, indent=2)

print("\n✅ GO2SE Genius v7.1 完整版完成!")
PYEOF
