#!/usr/bin/env python3
"""
Hermes v5.3 Optimized - 全面优化版
"""
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

CONFIG = {
    'buy_th': 18, 'sell_th': 82, 'position_ratio': 0.5,
    'leverage': 2.0, 'stop_loss': 0.02, 'take_profit': 0.12,
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
        return {'price':float(d['lastPrice']),'chg':float(d['priceChangePercent']),'high':float(d['highPrice']),'low':float(d['lowPrice']),'volume':float(d['quoteVolume'])}
    except: return None

def get_klines(sym, days=7):
    end = int(time.time()*1000)
    start = end - days*86400*1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit=500'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'close':float(k[4])} for k in r.json()]
    except: return []

def bollinger_pos(price, high, low):
    return (price-low)/(high-low)*100 if high>low else 50

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def get_spot():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return {b['asset']: float(b['free']) for b in r.json()['balances'] if float(b['free']) > 0.01}

def spot_order(symbol, side, qty):
    coin = symbol.replace('USDT','')
    p = PRECISION.get(coin, 6)
    qty = round(qty, p) if p > 0 else int(qty)
    if qty <= 0: return None
    ts = int(time.time()*1000)
    params = {'symbol':symbol,'side':side,'type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/api/v3/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    step = 10**(-p)
    return round(round(qty/step)*step, p)

# === MAIN ===
print("="*60)
print("Hermes v5.3 Optimized")
print("="*60)

print("\n【1. 全面市场扫描】")
market = {}
opportunities = []

for c in COINS:
    d = get_24hr(f'{c}USDT')
    if not d: continue
    price, chg, high, low = d['price'], d['chg'], d['high'], d['low']
    pos = bollinger_pos(price, high, low)
    
    klines = get_klines(f'{c}USDT', 7)
    prices = [k['close'] for k in klines] if klines else [price]
    rsi = get_rsi(prices)
    
    market[c] = {'price':price,'chg':chg,'high':high,'low':low,'pos':pos,'rsi':rsi,'volume':d['volume']}
    print(f"  {c:5}: ${price:.4f} {chg:+.2f}% 位置:{pos:.1f}% RSI:{rsi:.0f}")
    
    score = 0
    if pos < CONFIG['buy_th']:
        score = (CONFIG['buy_th']-pos)*2 + (50-rsi) if rsi<50 else 0
        action = 'BUY'
    elif pos > CONFIG['sell_th']:
        score = (pos-CONFIG['sell_th'])*2 + (rsi-50) if rsi>50 else 0
        action = 'SELL'
    else:
        continue
    
    if score > 0:
        opportunities.append({'coin':c,'action':action,'score':score,'pos':pos,'rsi':rsi,'chg':chg})

opportunities.sort(key=lambda x: -x['score'])
print(f"\n发现 {len(opportunities)} 个机会")

print("\n【2. 账户诊断】")
spot = get_spot()
spot_usdt = spot.get('USDT', 0)
total_value = spot_usdt

for c in COINS:
    if c in spot and spot[c] > 0:
        price = market.get(c, {}).get('price', get_price(f'{c}USDT'))
        value = spot[c] * price
        total_value += value
        print(f"  {c}: {spot[c]:.4f} (${value:.2f})")

print(f"  USDT: ${spot_usdt:.2f}")
print(f"  总资产: ${total_value:.2f}")

print("\n【3. 科学决策】")
decisions = []

for opp in opportunities[:5]:
    c = opp['coin']
    action = opp['action']
    if c not in market: continue
    
    m = market[c]
    price = m['price']
    pos_value = spot.get(c, 0) * price
    current_ratio = pos_value / total_value if total_value > 0 else 0
    
    if action == 'BUY' and spot_usdt > 10:
        diff = CONFIG['position_ratio'] - current_ratio
        if diff > 0:
            invest = total_value * diff * 0.5
            qty = round_qty(invest / price, c)
            if qty > 0:
                decisions.append({'coin':c,'side':'BUY','qty':qty,'price':price,'reason':f"位置:{m['pos']:.0f}%"})
                print(f"  📈 BUY {c} {qty}")
    
    elif action == 'SELL' and spot.get(c, 0) > 0:
        qty = round_qty(spot[c] * 0.5, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'SELL','qty':qty,'price':price,'reason':f"位置:{m['pos']:.0f}%"})
            print(f"  📉 SELL {c} {qty}")

print("\n【4. 自动执行】")
success = fail = 0
for d in decisions:
    result = spot_order(f"{d['coin']}USDT", d['side'], d['qty'])
    time.sleep(1)
    if result and 'orderId' in result:
        print(f"  ✅ {d['side']} {d['coin']} {d['qty']}")
        success += 1
    else:
        print(f"  ❌ {d['coin']}: {result.get('msg','')[:30] if result else 'error'}")
        fail += 1

print("\n【5. 验证汇报】")
new_spot = get_spot()
new_total = sum(new_spot.get(c, 0) * market.get(c, {}).get('price', 0) for c in COINS) + new_spot.get('USDT', 0)
print(f"  执行: {success}成功, {fail}失败")
print(f"  资产: ${total_value:.2f} → ${new_total:.2f} ({(new_total-total_value)/total_value*100:+.2f}%)")
print("="*60)
