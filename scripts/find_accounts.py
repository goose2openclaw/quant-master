#!/usr/bin/env python3
import requests, hmac, hashlib, time

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def sign(params):
    query = '&'.join([f'{k}={v}' for k,v in params.items()])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return sig

def api_get(endpoint, params=None):
    params = params or {}
    params['timestamp'] = int(time.time()*1000)
    params['signature'] = sign(params)
    url = f'https://api.binance.com{endpoint}'
    r = requests.get(url, params=params, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

print("=" * 60)
print("多账户查找")
print("=" * 60)

# 1. 主账户信息
print("\n[1] 主账户信息:")
try:
    acc = api_get('/api/v3/account')
    print(f"   账户ID: {acc.get('accountType', 'N/A')}")
    print(f"   交易对数量: {len(acc.get('balances', []))}")
    for b in acc.get('balances', []):
        free = float(b.get('free', 0))
        if free > 0:
            print(f"   {b['asset']}: {free:.8f}")
except Exception as e:
    print(f"   错误: {e}")

# 2. 合约账户
print("\n[2] USDT合约账户:")
try:
    url = 'https://fapi.binance.com/fapi/v2/balance'
    params = {'timestamp': int(time.time()*1000)}
    params['signature'] = sign(params)
    r = requests.get(url, params=params, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    for item in r.json():
        if float(item.get('availableBalance', 0)) > 0 or float(item.get('balance', 0)) > 0:
            print(f"   {item['asset']}: 可用={item['availableBalance']} 余额={item['balance']}")
except Exception as e:
    print(f"   错误: {e}")

# 3. 查询所有合约持仓
print("\n[3] 所有合约持仓:")
try:
    url = 'https://fapi.binance.com/fapi/v2/positionRisk'
    params = {'timestamp': int(time.time()*1000)}
    params['signature'] = sign(params)
    r = requests.get(url, params=params, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    positions = [p for p in r.json() if float(p.get('positionAmt', 0)) != 0]
    if positions:
        for p in positions:
            print(f"   {p['symbol']}: {p['positionAmt']} 盈亏:{p['unrealizedProfit']}")
    else:
        print("   无持仓")
except Exception as e:
    print(f"   错误: {e}")

# 4. 矿池/理财账户
print("\n[4] 查询子账户:")
try:
    url = 'https://api.binance.com/sapi/v1/sub-account/list'
    params = {'timestamp': int(time.time()*1000)}
    params['signature'] = sign(params)
    r = requests.get(url, params=params, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    print(f"   响应: {str(r.json())[:200]}")
except Exception as e:
    print(f"   错误: {e}")

# 5. 杠杆账户
print("\n[5] 杠杆账户:")
try:
    url = 'https://api.binance.com/margin/api/v3/account'
    params = {'timestamp': int(time.time()*1000)}
    params['signature'] = sign(params)
    r = requests.get(url, params=params, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    print(f"   状态: {r.status_code}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
