#!/usr/bin/env python3
import requests, hmac, hashlib, time

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def fut_get(endpoint, params=None):
    timestamp = int(time.time() * 1000)
    params = params or {}
    params['timestamp'] = timestamp
    query = '&'.join([f'{k}={v}' for k,v in params.items()])
    signature = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    url = f'https://fapi.binance.com{endpoint}?{query}&signature={signature}'
    r = requests.get(url, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r

# 测试余额
print("测试合约API...")
r = fut_get('/fapi/v2/balance')
print(f"状态码: {r.status_code}")
print(f"响应: {r.text[:200] if r.text else 'Empty'}")

print("\n测试持仓...")
r2 = fut_get('/fapi/v2/positionRisk')
print(f"状态码: {r2.status_code}")
print(f"响应: {r2.text[:200] if r2.text else 'Empty'}")
