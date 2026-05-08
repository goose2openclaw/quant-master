#!/bin/bash
# 15种操作优化迭代版
LOG_FILE="/tmp/gg_15_operations_opt.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "15种操作优化迭代 $(date)"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

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

def bollinger_pos(price, high, low):
    return (price-low)/(high-low)*100 if high>low else 50

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

def margin_borrow(asset, amount):
    ts = int(time.time()*1000)
    params = {'asset':asset,'amount':str(amount),'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/borrow?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def margin_repay(asset, amount):
    ts = int(time.time()*1000)
    params = {'asset':asset,'amount':str(amount),'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/repay?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def analyze(coin):
    klines = get_klines(f'{coin}USDT', '1h', 100)
    if not klines: return None
    d = get_24hr(f'{coin}USDT')
    if not d: return None
    prices = [k['close'] for k in klines]
    rsi = get_rsi(prices)
    bb = bollinger_pos(d['price'], d['high'], d['low'])
    return {'price': d['price'], 'chg': d['chg'], 'rsi': rsi, 'bb': bb}

print("="*70)
print("15种操作优化迭代")
print("="*70)

spot = get_spot()
cross, level = get_cross()

print(f"\n【初始状态】")
print(f"  SPOT USDT: ${spot.get('USDT', 0):.2f}")
print(f"  CROSS USDT: ${cross.get('USDT', 0):.2f}, Level: {level:.2f}")

prices = {c: get_price(f'{c}USDT') for c in COINS}
analyzes = {c: analyze(c) for c in COINS}

results = []

print("\n" + "="*70)
print("【SPOT操作 1-5】")
print("="*70)

# SPOT 1: 低吸
print("\n[1] SPOT低吸")
for c in ['DOGE', 'XRP', 'ADA']:
    a = analyzes.get(c)
    if a and a['bb'] < 25 and a['chg'] < -1:
        usdt = spot.get('USDT', 0)
        if usdt > 5:
            qty = round_qty(usdt * 0.1 / a['price'], c)
            if qty > 0:
                r = spot_order(f'{c}USDT', 'BUY', qty)
                if r and 'orderId' in r:
                    print(f"  ✅ 买入{c}: {qty} @ ${a['price']:.4f} (BB={a['bb']:.0f}%, RSI={a['rsi']:.0f})")
                    results.append({'op':1,'type':'SPOT_BUY',f'{c}':qty})
                else:
                    print(f"  ❌ {c}: {r.get('msg','')[:30] if r else 'err'}")
                time.sleep(1)

# SPOT 2: 高抛
print("\n[2] SPOT高抛")
for c in ['DOGE', 'ETH', 'LINK']:
    a = analyzes.get(c)
    qty = spot.get(c, 0)
    if a and a['bb'] > 75 and qty > 1:
        sell_qty = round_qty(qty * 0.2, c)
        if sell_qty > 0:
            r = spot_order(f'{c}USDT', 'SELL', sell_qty)
            if r and 'orderId' in r:
                print(f"  ✅ 卖出{c}: {sell_qty} @ ${a['price']:.4f} (BB={a['bb']:.0f}%)")
                results.append({'op':2,'type':'SPOT_SELL',f'{c}':sell_qty})
            else:
                print(f"  ❌ {c}")
            time.sleep(1)

# SPOT 3: 止损
print("\n[3] SPOT止损")
for c in ['XRP', 'ADA']:
    a = analyzes.get(c)
    qty = spot.get(c, 0)
    if a and (a['bb'] > 90 or a['chg'] < -10) and qty > 10:
        sell_qty = round_qty(qty * 0.5, c)
        r = spot_order(f'{c}USDT', 'SELL', sell_qty)
        if r and 'orderId' in r:
            print(f"  ✅ 止损{c}: {sell_qty}")
            results.append({'op':3,'type':'SPOT_STOP',f'{c}':sell_qty})
        time.sleep(1)

# SPOT 4: 追涨
print("\n[4] SPOT追涨")
for c in ['SOL', 'LINK']:
    a = analyzes.get(c)
    if a and a['chg'] > 2 and a['bb'] > 70 and spot.get('USDT', 0) > 5:
        qty = round_qty(spot.get('USDT', 0) * 0.1 / a['price'], c)
        r = spot_order(f'{c}USDT', 'BUY', qty)
        if r and 'orderId' in r:
            print(f"  ✅ 追涨{c}: {qty} (涨幅{a['chg']:.1f}%)")
            results.append({'op':4,'type':'SPOT_CHASE',f'{c}':qty})
        time.sleep(1)

# SPOT 5: 反转
print("\n[5] SPOT反转")
for c in COINS:
    a = analyzes.get(c)
    qty = spot.get(c, 0)
    if a and a['bb'] > 85 and qty > 1:
        sell_qty = round_qty(qty * 0.5, c)
        r = spot_order(f'{c}USDT', 'SELL', sell_qty)
        if r and 'orderId' in r:
            print(f"  ✅ 反转{c}: {sell_qty}")
            results.append({'op':5,'type':'SPOT_REVERSE',f'{c}':sell_qty})
        time.sleep(1)

print("\n" + "="*70)
print("【CROSS操作 6-10】")
print("="*70)

# CROSS 6: 做多
print("\n[6] CROSS做多")
for c in ['XRP', 'ADA', 'DOGE']:
    a = analyzes.get(c)
    if a and a['bb'] < 30 and a['rsi'] < 40:
        if cross.get('USDT', 0) < 50:
            # 借入USDT
            borrow_amt = 20
            r = margin_borrow('USDT', borrow_amt)
            if r and r.get('tranId'):
                print(f"  ✅ 借入USDT: {borrow_amt}")
                time.sleep(1)
        
        usdt = cross.get('USDT', 0)
        if usdt > 5:
            qty = round_qty(usdt * 0.5 / a['price'], c)
            r = cross_order(f'{c}USDT', 'BUY', qty)
            if r and 'orderId' in r:
                print(f"  ✅ CROSS做多{c}: {qty} @ ${a['price']:.4f}")
                results.append({'op':6,'type':'CROSS_LONG',f'{c}':qty})
            time.sleep(1)

# CROSS 7: 做空
print("\n[7] CROSS做空")
for c in ['SOL', 'ETH']:
    a = analyzes.get(c)
    if a and a['bb'] > 80 and a['rsi'] > 60:
        # 借入币
        borrow_qty = min(10, a['price'] * 10)
        r = margin_borrow(c, borrow_qty)
        if r and r.get('tranId'):
            print(f"  ✅ 借入{c}: {borrow_qty}")
            time.sleep(1)
            r = cross_order(f'{c}USDT', 'SELL', borrow_qty)
            if r and 'orderId' in r:
                print(f"  ✅ CROSS做空{c}: {borrow_qty}")
                results.append({'op':7,'type':'CROSS_SHORT',f'{c}':borrow_qty})
        time.sleep(1)

# CROSS 8: CROSS买入
print("\n[8] CROSS买入")
for c in ['BTC', 'ETH']:
    a = analyzes.get(c)
    if a and a['bb'] < 25 and cross.get('USDT', 0) > 10:
        qty = round_qty(cross.get('USDT', 0) * 0.2 / a['price'], c)
        r = cross_order(f'{c}USDT', 'BUY', qty)
        if r and 'orderId' in r:
            print(f"  ✅ CROSS买入{c}: {qty}")
            results.append({'op':8,'type':'CROSS_BUY',f'{c}':qty})
        time.sleep(1)

# CROSS 9: CROSS卖出
print("\n[9] CROSS卖出")
for c in COINS:
    a = analyzes.get(c)
    if a and a['bb'] > 80 and cross.get(c, 0) > 1:
        sell_qty = round_qty(cross.get(c, 0) * 0.3, c)
        r = cross_order(f'{c}USDT', 'SELL', sell_qty)
        if r and 'orderId' in r:
            print(f"  ✅ CROSS卖出{c}: {sell_qty}")
            results.append({'op':9,'type':'CROSS_SELL',f'{c}':sell_qty})
        time.sleep(1)

# CROSS 10: 还款
print("\n[10] CROSS还款")
for c in ['USDT', 'XRP']:
    balance = cross.get(c, 0)
    if c == 'USDT' and balance > 15:
        repay = min(10, balance * 0.3)
        r = margin_repay(c, repay)
        if r and r.get('tranId'):
            print(f"  ✅ 归还{c}: {repay}")
            results.append({'op':10,'type':'CROSS_REPAY',f'{c}':repay})
    elif c != 'USDT' and balance > 50:
        repay = min(balance * 0.5, 100)
        r = margin_repay(c, repay)
        if r and r.get('tranId'):
            print(f"  ✅ 归还{c}: {repay}")
            results.append({'op':10,'type':'CROSS_REPAY',f'{c}':repay})

print("\n" + "="*70)
print("【ISOLATED操作 11-15】")
print("="*70)

# ISOLATED 11-15 简化实现
print("\n[11-15] ISOLATED操作")
print("  ⏭️ ISOLATED需要先创建交易对")

# 汇总
print("\n" + "="*70)
print("【操作汇总】")
print("="*70)

print(f"\n执行操作: {len(results)}/15")
for r in results:
    print(f"  {r}")

# 资产验证
new_spot = get_spot()
new_cross, new_level = get_cross()
spot_total = sum(new_spot.get(c, 0) * prices.get(c, 0) for c in COINS) + new_spot.get('USDT', 0)
cross_total = sum(new_cross.get(c, 0) * prices.get(c, 0) for c in COINS) + new_cross.get('USDT', 0)

print(f"\n【资产验证】")
print(f"  SPOT: ${spot_total:.2f}")
print(f"  CROSS: ${cross_total:.2f}")
print(f"  总计: ${spot_total + cross_total:.2f}")
print(f"  CROSS Level: {new_level:.2f}")

with open('/tmp/15_operations_opt.json', 'w') as f:
    json.dump({'results': results, 'spot_total': spot_total, 'cross_total': cross_total, 'timestamp': datetime.now().isoformat()}, f, indent=2)

print("\n✅ 优化迭代完成!")
PYEOF
