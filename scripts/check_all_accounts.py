#!/usr/bin/env python3
"""全面检查所有Binance账户"""
import requests, hmac, hashlib, time

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def sign(params):
    params['recvWindow'] = 5000
    params['timestamp'] = int(time.time()*1000)
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return f'{query}&signature={sig}'

def api_get(url, params):
    try:
        r = requests.get(url + '?' + sign(params), 
                       headers={'X-MBX-APIKEY': API_KEY}, 
                       proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

print("=" * 60)
print("Binance 全账户检查")
print("=" * 60)

# 1. 现货账户
print("\n[1] 现货账户 (SPOT)")
url = 'https://api.binance.com/api/v3/account'
data = api_get(url, {})
if 'error' not in data and 'balances' in data:
    for b in data['balances']:
        free = float(b.get('free', 0))
        if free > 0.00001:
            print(f"  {b['asset']}: {free:.8f}")

# 2. 全仓杠杆账户
print("\n[2] 全仓杠杆账户 (MARGIN)")
url = 'https://api.binance.com/sapi/v1/margin/account'
data = api_get(url, {})
if 'error' not in data:
    print(f"  总资产: {data.get('totalAssetOfBtc', 'N/A')} BTC")
    if 'userAssets' in data:
        for b in data['userAssets']:
            net = float(b.get('net', 0))
            if net > 0:
                print(f"  {b['asset']}: {net:.8f}")
else:
    print(f"  错误: {data}")

# 3. 逐仓杠杆账户
print("\n[3] 逐仓杠杆账户 (ISOLATED MARGIN)")
url = 'https://api.binance.com/sapi/v1/margin/isolated/account'
data = api_get(url, {})
if 'error' not in data:
    assets = data.get('assets', [])
    if assets:
        for a in assets:
            print(f"  {a['symbol']}: {a['baseAsset']['free']} {a['quoteAsset']['free']}")
    else:
        print("  无逐仓持仓")
else:
    print(f"  错误: {data}")

# 4. USDT合约账户 (逐仓)
print("\n[4] USDT合约逐仓账户 (USDT-FUTURES ISOLATED)")
url = 'https://fapi.binance.com/fapi/v2/positionRisk'
data = api_get(url, {'pair': 'BTCUSDT'})
if 'error' not in data:
    for p in data:
        if float(p.get('positionAmt', 0)) != 0:
            print(f"  {p['symbol']}: {p['positionAmt']} 盈亏:{p['unrealizedProfit']}")
    if not any(float(p.get('positionAmt', 0)) != 0 for p in data):
        print("  无逐仓持仓")
else:
    print(f"  错误: {data}")

# 5. USDT合约账户 (全仓)
print("\n[5] USDT合约全仓账户 (USDT-FUTURES CROSS)")
url = 'https://fapi.binance.com/fapi/v2/account'
data = api_get(url, {})
if 'error' not in data:
    print(f"  总余额: {data.get('totalMarginBalance', 'N/A')}")
    print(f"  可用余额: {data.get('availableBalance', 'N/A')}")
    print(f"  冻结: {data.get('totalInitialMargin', 'N/A')}")
else:
    print(f"  错误: {data}")

# 6. 合约持仓
print("\n[6] 合约持仓详情 (FUTURES POSITIONS)")
url = 'https://fapi.binance.com/fapi/v2/positionRisk'
positions = api_get(url, {})
if 'error' not in positions:
    active = [p for p in positions if float(p.get('positionAmt', 0)) != 0]
    if active:
        for p in active:
            print(f"  {p['symbol']}: {p['positionAmt']} 模式:{p['marginType']}")
    else:
        print("  无持仓")
else:
    print(f"  错误: {positions}")

print("\n" + "=" * 60)
