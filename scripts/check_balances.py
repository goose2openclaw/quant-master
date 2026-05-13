#!/usr/bin/env python3
import requests, hmac, hashlib, time

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

def sign(params):
    query = '&'.join([f'{k}={v}' for k,v in params.items()])
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def fut_get(endpoint, params=None):
    params = params or {}
    params['timestamp'] = int(time.time()*1000)
    params['signature'] = sign(params)
    url = f'https://fapi.binance.com{endpoint}'
    r = requests.get(url, params=params, headers={'X-MBX-APIKEY': API_KEY}, timeout=10)
    return r.json()

print("合约账户检查(无代理):")
try:
    bal = fut_get('/fapi/v2/balance')
    for item in bal:
        if item['asset'] in ['USDT', 'FDUSD']:
            print(f"  {item['asset']}: 可用={item['availableBalance']} 余额={item['balance']}")
except Exception as e:
    print(f"  错误: {e}")

print("\n持仓检查:")
try:
    pos = fut_get('/fapi/v2/positionRisk')
    active = [p for p in pos if float(p['positionAmt']) != 0]
    if active:
        for p in active:
            print(f"  {p['symbol']}: {p['positionAmt']} 浮亏:{p['unrealizedProfit']}")
    else:
        print("  无持仓")
except Exception as e:
    print(f"  错误: {e}")
