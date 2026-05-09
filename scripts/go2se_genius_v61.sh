#!/bin/bash
# GO2SE Genius v6.1 - 做多做空加强版
LOG_FILE="/tmp/go2se_v61.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "GO2SE Genius v6.1 $(date)"
echo "做多做空加强版"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

CONFIG = {
    'position_ratio': 0.6,
    'bb_buy': 25, 'bb_sell': 80, 'bb_squeeze': 10,
    'zt_threshold': -1.5, 'ft_threshold': 2.0,
    'rsi_buy': 40, 'rsi_sell': 60,
    'rsi_extreme_buy': 30, 'rsi_extreme_sell': 70,
    'long_enabled': True, 'short_enabled': True,
    'take_profit': 0.05, 'stop_loss': 0.02,
    'min_notional': 10, 'sell_ratio': 0.5,
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

def bollinger_width(highs, lows, period=20):
    if len(highs) < period: return 0
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (bb_high - bb_low) / np.mean(highs[-period:]) * 100 if np.mean(highs[-period:]) > 0 else 0

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    step = 10**(-p)
    return round(round(qty/step)*step, p)

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
    rsi_7 = get_rsi(closes, 7)
    rsi_14 = get_rsi(closes, 14)
    bb_pos = bollinger_pos(d['price'], highs, lows, 20)
    bb_width = bollinger_width(highs, lows, 20)
    return {
        'price': d['price'], 'chg': d['chg'],
        'rsi_7': rsi_7, 'rsi_14': rsi_14,
        'bb_pos': bb_pos, 'bb_width': bb_width
    }

print("\n【v6.1 全域扫描 & 多维度信号评估】")
spot = get_spot()
cross, level = get_cross()
prices = {}
analyses = {}
for c in COINS:
    a = analyze_coin(c)
    if a: analyses[c] = a; prices[c] = a['price']
    time.sleep(0.1)

total_spot = sum(spot.get(c, 0) * prices.get(c, 0) for c in COINS) + spot.get('USDT', 0)
total_cross = sum(cross.get(c, 0) * prices.get(c, 0) for c in COINS) + cross.get('USDT', 0)
total_value = total_spot + total_cross

print(f"总资产: ${total_value:.2f}")

signals = []
for c in COINS:
    if c not in analyses: continue
    a = analyses[c]
    
    bb_buy = a['bb_pos'] < CONFIG['bb_buy']
    bb_sell = a['bb_pos'] > CONFIG['bb_sell']
    bb_squeeze = a['bb_width'] < CONFIG['bb_squeeze']
    zt = a['chg'] < CONFIG['zt_threshold']
    ft = a['chg'] > CONFIG['ft_threshold']
    rsi_oversold = a['rsi_7'] < CONFIG['rsi_buy']
    rsi_overbought = a['rsi_7'] > CONFIG['rsi_sell']
    rsi_extreme_buy = a['rsi_7'] < CONFIG['rsi_extreme_buy']
    rsi_extreme_sell = a['rsi_7'] > CONFIG['rsi_extreme_sell']
    long_sig = (bb_buy or rsi_oversold) and not rsi_overbought
    short_sig = (bb_sell or rsi_overbought) and not rsi_oversold
    
    score = 0
    actions = []
    if bb_buy: score += 30; actions.append(f"BB低{a['bb_pos']:.0f}%")
    if zt: score += 25; actions.append(f"正T{a['chg']:.1f}%")
    if rsi_oversold: score += 20; actions.append(f"RSI{a['rsi_7']:.0f}")
    if rsi_extreme_buy: score += 15; actions.append("RSI极买")
    if bb_squeeze: score += 10; actions.append("BB挤压")
    if bb_sell: score -= 25; actions.append(f"BB高{a['bb_pos']:.0f}%")
    if ft: score -= 20; actions.append(f"反T{a['chg']:.1f}%")
    if rsi_overbought: score -= 20; actions.append(f"RSI{a['rsi_7']:.0f}")
    if rsi_extreme_sell: score -= 15; actions.append("RSI极卖")
    if short_sig: score -= 30; actions.append("做空")
    
    signals.append({
        'coin': c, 'price': a['price'], 'bb_pos': a['bb_pos'], 'rsi': a['rsi_7'], 'chg': a['chg'],
        'score': score, 'actions': actions,
        'bb_buy': bb_buy, 'bb_sell': bb_sell, 'zt': zt, 'ft': ft,
        'rsi_oversold': rsi_oversold, 'rsi_overbought': rsi_overbought,
        'rsi_extreme_buy': rsi_extreme_buy, 'rsi_extreme_sell': rsi_extreme_sell,
        'long': long_sig, 'short': short_sig,
        'spot_qty': spot.get(c, 0), 'cross_qty': cross.get(c, 0)
    })

signals.sort(key=lambda x: -x['score'])

print("\n【v6.1 多维度信号】")
print(f"{'币种':6} {'评分':6} {'价格':12} {'BB':6} {'RSI':6} {'涨跌':8} {'信号'}")
print("-"*70)
for s in signals:
    action_str = ' '.join(s['actions'][:3])
    print(f"{s['coin']:6} {s['score']:>+6.0f} ${s['price']:>10.4f} {s['bb_pos']:>5.1f}% {s['rsi']:>5.1f} {s['chg']:>+7.2f}% {action_str[:25]}")

print("\n【v6.1 执行交易】")
trades = []

# 高抛
for s in signals:
    if s['bb_sell'] or s['ft'] or s['rsi_overbought']:
        c, qty = s['coin'], s['spot_qty']
        if qty > 1:
            sqty = round_qty(qty * CONFIG['sell_ratio'], c)
            if sqty > 0:
                r = spot_order(f'{c}USDT', 'SELL', sqty)
                if r and 'orderId' in r:
                    print(f"✅ 高抛 {c}: {sqty}")
                    trades.append({'type':'SPOT_SELL','coin':c,'qty':sqty})
                time.sleep(1)

# 低吸
for s in signals:
    if s['bb_buy'] or s['zt'] or (s['rsi_oversold'] and s['spot_qty'] < 10):
        c = s['coin']
        if spot.get('USDT', 0) > CONFIG['min_notional']:
            invest = total_value * CONFIG['position_ratio'] * 0.3
            bqty = round_qty(invest / s['price'], c)
            if bqty > 0:
                r = spot_order(f'{c}USDT', 'BUY', bqty)
                if r and 'orderId' in r:
                    print(f"✅ 低吸 {c}: {bqty}")
                    trades.append({'type':'SPOT_BUY','coin':c,'qty':bqty})
                time.sleep(1)

# CROSS做多
for s in signals:
    if s['long'] and (s['rsi_extreme_buy'] or s['bb_pos'] < 15):
        c = s['coin']
        if cross.get('USDT', 0) < 50 and cross.get('USDT', 0) > 10:
            r = cross_borrow('USDT', min(30, cross.get('USDT', 0)))
            if r and r.get('tranId'):
                print(f"✅ CROSS借入USDT")
                time.sleep(1)
        if cross.get('USDT', 0) > 10:
            bqty = round_qty(cross.get('USDT', 0) * 0.8 / s['price'], c)
            if bqty > 0:
                r = cross_order(f'{c}USDT', 'BUY', bqty)
                if r and 'orderId' in r:
                    print(f"✅ CROSS做多 {c}: {bqty}")
                    trades.append({'type':'CROSS_LONG','coin':c,'qty':bqty})
                time.sleep(1)

# CROSS做空
for s in signals:
    if s['short'] and CONFIG['short_enabled'] and s['cross_qty'] < 1:
        c = s['coin']
        bqty = round_qty(20 / s['price'], c)
        r = cross_borrow(c, bqty)
        if r and r.get('tranId'):
            print(f"✅ CROSS借入{c}做空")
            time.sleep(1)
            r = cross_order(f'{c}USDT', 'SELL', bqty)
            if r and 'orderId' in r:
                print(f"✅ CROSS做空 {c}: {bqty}")
                trades.append({'type':'CROSS_SHORT','coin':c,'qty':bqty})
            time.sleep(1)

print("\n【v6.1 验证】")
new_spot = get_spot()
new_cross, new_level = get_cross()
spot_total = sum(new_spot.get(c, 0) * prices.get(c, 0) for c in COINS) + new_spot.get('USDT', 0)
cross_total = sum(new_cross.get(c, 0) * prices.get(c, 0) for c in COINS) + new_cross.get('USDT', 0)
new_total = spot_total + cross_total

print(f"  执行: {len(trades)}笔")
print(f"  资产: ${total_value:.2f} → ${new_total:.2f} ({(new_total-total_value)/total_value*100:+.2f}%)")
print(f"  SPOT: ${spot_total:.2f} | CROSS: ${cross_total:.2f}")

with open('/tmp/go2se_v61_log.json', 'w') as f:
    json.dump({'version':'v6.1','trades':trades,'signals':[{'coin':s['coin'],'score':s['score']} for s in signals]}, f, indent=2)

print("\n✅ GO2SE Genius v6.1 完成!")
PYEOF
