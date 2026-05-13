#!/usr/bin/env python3
import requests, hmac, hashlib, time

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
    return r.json()

print("=" * 60)
print("逐仓账户详情")
print("=" * 60)

symbols = ['ADAUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']

for symbol in symbols:
    url = 'https://api.binance.com/sapi/v1/margin/isolated/account'
    data = api_post(url, {'symbol': symbol})
    
    if 'error' in data:
        print(f"\n{symbol}: 错误 {data['error']}")
        continue
    
    base = data.get('baseAsset', {})
    quote = data.get('quoteAsset', {})
    
    base_free = float(base.get('free', 0))
    quote_free = float(quote.get('free', 0))
    base_lock = float(base.get('locked', 0))
    quote_lock = float(quote.get('locked', 0))
    
    print(f"\n{symbol}:")
    print(f"  基础资产: {base_free} (锁定: {base_lock})")
    print(f"  报价资产: {quote_free} USDT (锁定: {quote_lock})")
    
    # 如果有余额,尝试转出
    if base_free > 0.00001 or quote_free > 0.01:
        print(f"  → 准备转出...")

print("\n" + "=" * 60)
