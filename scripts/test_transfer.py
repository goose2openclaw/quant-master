#!/usr/bin/env python3
import requests, hmac, hashlib, time, json

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def sign(params):
    params['recvWindow'] = 5000
    params['timestamp'] = int(time.time()*1000)
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + '&signature=' + sig

def api_post(url, params):
    r = requests.post(url + '?' + sign(params),
                    headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.status_code, r.json()

# 测试转ADA
url = 'https://api.binance.com/sapi/v1/margin/isolated/transfer'
params = {
    'asset': 'ADA',
    'symbol': 'ADAUSDT',
    'transFrom': 'ISOLATED_MARGIN',
    'transTo': 'SPOT',
    'amount': '22.4775'
}

print("测试转账 ADA...")
status, result = api_post(url, params)
print(f"状态码: {status}")
print(f"响应: {json.dumps(result)}")

# 测试转USDT
params2 = {
    'asset': 'USDT',
    'symbol': 'ADAUSDT',
    'transFrom': 'ISOLATED_MARGIN',
    'transTo': 'SPOT',
    'amount': '4.357'
}

print("\n测试转账 USDT...")
status2, result2 = api_post(url, params2)
print(f"状态码: {status2}")
print(f"响应: {json.dumps(result2)}")
