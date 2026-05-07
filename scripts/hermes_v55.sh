#!/bin/bash
# Hermes v5.5 - 高抛低吸版 (蒸馏前版本)
LOG_FILE="/tmp/hermes_v55.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v5.5 $(date)"
echo "长线高抛低吸 - 仓位不变"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION = {'BTC':5,'ETH':4,'BNB':3,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}

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

def get_spot():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return {b['asset']: float(b['free']) for b in r.json()['balances'] if float(b['free']) > 0}

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

# 主程序
coins = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
print("\n【市场扫描】")
market = {}
for c in coins:
    d = get_24hr(f'{c}USDT')
    if d:
        market[c] = d
        print(f"  {c:5}: ${d['price']:.4f} {d['chg']:+.2f}%")

spot = get_spot()
spot_usdt = spot.get('USDT', 0)
print(f"\n【账户】SPOT: ${spot_usdt:.2f}")

# 高抛低吸策略
print("\n【执行计划】")
decisions = []
for c in coins:
    if c not in market: continue
    d = market[c]
    price, chg = d['price'], d['chg']
    high, low = d['high'], d['low']
    
    band = high - low
    position = (price - low) / band * 100 if band > 0 else 50
    
    # 布林位置 < 20% = 低吸
    if position < 20:
        qty = round(10 / price, PRECISION.get(c, 6))
        if qty > 0:
            decisions.append({'coin':c,'side':'BUY','qty':qty,'price':price})
            print(f"  📈 BUY {c} {qty} (位置:{position:.1f}%)")
    # 布林位置 > 80% = 高抛
    elif position > 80:
        qty = round(spot.get(c, 0) * 0.3, PRECISION.get(c, 6))
        if qty > 0:
            decisions.append({'coin':c,'side':'SELL','qty':qty,'price':price})
            print(f"  📉 SELL {c} {qty} (位置:{position:.1f}%)")

print(f"\n【执行结果】")
success = fail = 0
for d in decisions:
    result = spot_order(f"{d['coin']}USDT", d['side'], d['qty'])
    time.sleep(1)
    if result and 'orderId' in result:
        print(f"  ✅ {d['side']} {d['coin']} {d['qty']}")
        success += 1
    else:
        msg = result.get('msg','')[:30] if result else 'error'
        print(f"  ❌ {d['coin']}: {msg}")
        fail += 1

print(f"\n【结果】成功:{success} 失败:{fail}")
print("Hermes v5.5 完成")
PYEOF
