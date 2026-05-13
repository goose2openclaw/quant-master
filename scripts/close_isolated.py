#!/usr/bin/env python3
"""
关闭逐仓杠杆仓位
需要: 卖出资产 + 归还借款
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

def api_post(url, params):
    r = requests.post(url + '?' + sign(params),
                    headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.status_code, r.json()

def api_get(url, params=None):
    params = params or {}
    r = requests.get(url + '?' + sign(params),
                    headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

def get_price(symbol):
    r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', 
                    proxies=PROXIES, timeout=5)
    return float(r.json()['price'])

def get_isolated_account(symbol):
    url = 'https://api.binance.com/sapi/v1/margin/isolated/account'
    return api_get(url, {'symbol': symbol})

print("=" * 60)
print("关闭逐仓杠杆仓位")
print("=" * 60)

# 获取所有逐仓账户
url = 'https://api.binance.com/sapi/v1/margin/isolated/account'
all_data = api_get(url, {})

for asset_info in all_data.get('assets', []):
    symbol = asset_info['symbol']
    base = asset_info['baseAsset']
    quote = asset_info['quoteAsset']
    
    base_asset = base['asset']
    base_free = float(base['free'])
    base_borrowed = float(base['borrowed'])
    quote_free = float(quote['free'])
    quote_borrowed = float(quote['borrowed'])
    
    # 跳过空的
    total_base = base_free + base_borrowed
    total_quote = quote_free + quote_borrowed
    if total_base < 0.00001 and total_quote < 0.01:
        continue
    
    print(f"\n{symbol}:")
    print(f"  {base_asset}: free={base_free}, borrowed={base_borrowed}")
    print(f"  USDT: free={quote_free}, borrowed={quote_borrowed}")
    
    # 如果有借款,需要先还款才能转出
    # 但如果没有借款,可以直接转出
    if base_borrowed > 0 or quote_borrowed > 0:
        print(f"  ⚠️ 有借款,需要先卖出资产还款")
        
        # 卖出base资产还款
        if base_free > 0:
            # 市价卖出base
            price = get_price(symbol)
            # 在现货市场卖出
            print(f"  → 需要在现货市场卖出{base_free} {base_asset}")
    else:
        print(f"  ✅ 无借款,可直接转出")
        # 转出所有
        if base_free > 0.00001:
            print(f"  → 可转{base_free} {base_asset}到现货")
        if quote_free > 0.01:
            print(f"  → 可转{quote_free} USDT到现货")

print("\n" + "=" * 60)
