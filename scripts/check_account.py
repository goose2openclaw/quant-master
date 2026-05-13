#!/usr/bin/env python3
import requests, hmac, hashlib, time

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def binance_get(endpoint, params=None):
    timestamp = int(time.time() * 1000)
    params = params or {}
    params['timestamp'] = timestamp
    query = '&'.join([f'{k}={v}' for k,v in params.items()])
    signature = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    url = f'https://api.binance.com{endpoint}?{query}&signature={signature}'
    r = requests.get(url, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

print("账户检查...")
print("-" * 40)

# 现货账户
try:
    spot = binance_get('/api/v3/account')
    print(f"现货余额:")
    for b in spot.get('balances', [])[:5]:
        free = float(b['free'])
        locked = float(b['locked'])
        if free > 0 or locked > 0:
            print(f"  {b['asset']}: {free:.8f} (锁定: {locked})")
except Exception as e:
    print(f"现货查询失败: {e}")

print("-" * 40)

# 合约账户
try:
    fut = binance_get('/fapi/v2/balance')
    print(f"合约USDT余额:")
    for item in fut:
        if item['asset'] == 'USDT':
            print(f"  可用: {float(item['availableBalance']):.2f}")
            print(f"  余额: {float(item['balance']):.2f}")
            print(f"  冻结: {float(item['withdrawAvailable']):.2f}")
except Exception as e:
    print(f"合约查询失败: {e}")

print("-" * 40)

# 持仓
try:
    pos = binance_get('/fapi/v2/positionRisk', {'pair': 'BTCUSDT'})
    for p in pos:
        if float(p['positionAmt']) != 0:
            print(f"持仓: {p['symbol']} 数量:{p['positionAmt']} 盈亏:{p['unrealizedProfit']}")
except Exception as e:
    print(f"持仓查询失败: {e}")
