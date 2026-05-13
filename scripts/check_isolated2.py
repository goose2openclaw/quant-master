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

def api_get(url, params=None):
    params = params or {}
    r = requests.get(url + '?' + sign(params),
                    headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

# 检查所有逐仓账户
url = 'https://api.binance.com/sapi/v1/margin/isolated/account'
data = api_get(url, {})

print("完整响应:")
print(json.dumps(data, indent=2)[:2000])
