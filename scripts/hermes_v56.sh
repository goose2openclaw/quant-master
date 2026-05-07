#!/bin/bash
# Hermes v5.6 - 全功能增强版
LOG_FILE="/tmp/hermes_v56.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "Hermes v5.6 $(date)"
echo "=========================================="
python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

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

def get_account():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    spot = {b['asset']: float(b['free']) for b in r.json()['balances']}
    return spot

def do_transfer(asset, amount, src, dst):
    ts = int(time.time()*1000)
    params = f'asset={asset}&amount={amount}&fromAccount={src}&toAccount={dst}&timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f'https://api.binance.com/sapi/v1/account/transfer?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return 'tranId' in str(r.json())
    except: return False

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

# MAIN
print("\n【1. 全域扫描】")
opportunities = []
for c in ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK','AVAX','DOT']:
    d = get_24hr(f'{c}USDT')
    if not d: continue
    klines = get_klines(f'{c}USDT', 7)
    prices = [k['close'] for k in klines] if klines else [d['price']]
    rsi = get_rsi(prices)
    pos = bollinger_pos(d['price'], d['high'], d['low'])
    
    action = None
    if pos < 25 and rsi < 40:
        action = 'LONG'
    elif pos > 75 and rsi > 60:
        action = 'SHORT'
    elif d['chg'] < -2:
        action = 'ZT'
    
    if action:
        opportunities.append({'coin':c,'action':action,'score':(25-pos)+(40-rsi),'pos':pos,'rsi':rsi,'price':d['price']})
    print(f"  {c:5}: ${d['price']:.4f} {d['chg']:+.2f}% 位置:{pos:.0f}% RSI:{rsi:.0f} {'📈' if action=='LONG' else '📉' if action=='SHORT' else '🔄' if action=='ZT' else ''}")
    time.sleep(0.1)

opportunities.sort(key=lambda x: -x['score'])

print("\n【2. 账户诊断】")
spot = get_account()
spot_usdt = spot.get('USDT', 0)
positions = {}
total = spot_usdt
for c in COINS:
    if c in spot and spot[c] > 0:
        price = get_price(f'{c}USDT')
        val = spot[c] * price
        total += val
        positions[c] = {'qty': spot[c], 'value': val}

print(f"  SPOT USDT: ${spot_usdt:.2f}")
for c in COINS:
    if c in positions:
        print(f"  {c}: {positions[c]['qty']:.4f} (${positions[c]['value']:.2f})")
print(f"  总资产: ${total:.2f}")

print("\n【3. 自主解决资金】")
# 尝试从CROSS转钱
if spot_usdt < 50:
    print("  尝试CROSS转账到SPOT...")
    if do_transfer('USDT', 50, 'CROSS', 'SPOT'):
        print("  ✅ CROSS->SPOT 转账成功")
        spot = get_account()
        spot_usdt = spot.get('USDT', 0)
    else:
        print("  ⚠️ 转账失败或无可用资金")

# 如果还不够，卖出持仓
if spot_usdt < 30:
    print("  卖出部分持仓获取USDT...")
    for opp in opportunities:
        c = opp['coin']
        if c in positions and positions[c]['value'] > 100:
            qty = round_qty(positions[c]['qty'] * 0.3, c)
            if qty > 0:
                result = spot_order(f'{c}USDT', 'SELL', qty)
                time.sleep(1)
                if result and 'orderId' in result:
                    revenue = qty * opp['price']
                    spot_usdt += revenue
                    positions[c]['qty'] -= qty
                    positions[c]['value'] -= revenue
                    print(f"  ✅ 卖出 {c} {qty} -> ${revenue:.2f}")
                    if spot_usdt >= 50:
                        break

print(f"  调整后SPOT USDT: ${spot_usdt:.2f}")

print("\n【4. 科学决策】")
decisions = []
for opp in opportunities[:5]:
    c = opp['coin']
    action = opp['action']
    price = opp['price']
    
    if action == 'LONG' and spot_usdt > 10:
        qty = round_qty(spot_usdt * 0.8 / price, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'BUY','qty':qty,'action':action})
            print(f"  📈 LONG {c} {qty}")
    elif action in ['SHORT','ZT'] and c in positions and positions[c]['qty'] > 0:
        qty = round_qty(positions[c]['qty'] * 0.5, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'SELL','qty':qty,'action':action})
            print(f"  📉 {action} {c} {qty}")

print("\n【5. 执行】")
success = fail = 0
for d in decisions:
    result = spot_order(f"{d['coin']}USDT", d['side'], d['qty'])
    time.sleep(0.5)
    if result and 'orderId' in result:
        print(f"  ✅ {d['action']} {d['side']} {d['coin']} {d['qty']}")
        success += 1
    else:
        print(f"  ❌ {d['coin']}: {result.get('msg','')[:30] if result else 'err'}")
        fail += 1

print(f"\n【6. 结果】执行:{success}成功,{fail}失败")
print("✅ 完成")
PYEOF
