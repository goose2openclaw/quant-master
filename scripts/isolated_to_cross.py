#!/usr/bin/env python3
"""
逐仓杠杆转现货 - 转移所有资产
"""
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

def api_post(url, params):
    r = requests.post(url + '?' + sign(params),
                    headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

print("=" * 60)
print("逐仓转现货")
print("=" * 60)

# 获取所有逐仓账户
url = 'https://api.binance.com/sapi/v1/margin/isolated/account'
data = api_get(url, {})

total_transferred = {}

for asset_info in data.get('assets', []):
    symbol = asset_info['symbol']
    base = asset_info['baseAsset']
    quote = asset_info['quoteAsset']
    
    base_asset = base['asset']
    base_free = float(base['free'])
    quote_free = float(quote['free'])
    
    # 跳过空的
    if base_free < 0.00001 and quote_free < 0.01:
        continue
    
    print(f"\n{symbol}:")
    print(f"  {base_asset}: {base_free}")
    print(f"  USDT: {quote_free}")
    
    # 转移base asset
    if base_free >= 0.00001:
        url = 'https://api.binance.com/sapi/v1/margin/isolated/transfer'
        params = {
            'asset': base_asset,
            'symbol': symbol,
            'transFrom': 'ISOLATED_MARGIN',
            'transTo': 'SPOT',
            'amount': str(base_free)
        }
        result = api_post(url, params)
        if result.get('code') == 0:
            print(f"  ✅ 转{base_free} {base_asset}成功")
            total_transferred[base_asset] = total_transferred.get(base_asset, 0) + base_free
        else:
            print(f"  ❌ 转{base_asset}失败: {result.get('msg')}")
    
    # 转移quote asset (USDT)
    if quote_free >= 0.01:
        url = 'https://api.binance.com/sapi/v1/margin/isolated/transfer'
        params = {
            'asset': 'USDT',
            'symbol': symbol,
            'transFrom': 'ISOLATED_MARGIN',
            'transTo': 'SPOT',
            'amount': str(quote_free)
        }
        result = api_post(url, params)
        if result.get('code') == 0:
            print(f"  ✅ 转{quote_free} USDT成功")
            total_transferred['USDT'] = total_transferred.get('USDT', 0) + quote_free
        else:
            print(f"  ❌ 转USDT失败: {result.get('msg')}")

print("\n" + "=" * 60)
print("转移汇总:")
for asset, qty in total_transferred.items():
    print(f"  {asset}: {qty}")
print("=" * 60)
