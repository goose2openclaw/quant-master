#!/usr/bin/env python3
"""
G23 资金整合 + 合约准备
=======================
1. 变现逐仓小额资产
2. 转入合约账户
3. 准备资金费率套利
"""
import urllib.request, hmac, hashlib, time, json

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

def api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=10)
    return float(json.loads(resp.read().decode())['price'])

def get_margin_balance():
    """获取逐仓账户所有资产"""
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/sapi/v1/margin/account?timestamp={ts}&signature={sig}"
    data = api(url)
    assets = []
    if 'userAssets' in data:
        for a in data['userAssets']:
            free = float(a.get('free', 0))
            if free > 0.0001:  # 最小清算数量
                asset = a['asset']
                try:
                    p = price(asset + 'USDT')
                    value = free * p
                    assets.append({
                        'asset': asset,
                        'qty': free,
                        'price': p,
                        'value': value
                    })
                except: pass
    return assets

def margin_sell(asset, qty):
    """逐仓卖出"""
    ts = int(time.time() * 1000)
    q = f"symbol={asset}USDT&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/sapi/v1/margin/order?{q}&signature={sig}"
    return api(url, 'POST')

def get_spot_balance():
    """获取现货USDT"""
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    if 'balances' in data:
        for b in data['balances']:
            if b['asset'] == 'USDT':
                return float(b['free'])
    return 0

def transfer_to_futures(amount):
    """转账到合约账户"""
    ts = int(time.time() * 1000)
    q = f"asset=USDT&amount={amount}&type=FUTURE&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/sapi/v1/asset/transfer?{q}&signature={sig}"
    return api(url, 'POST')

print("=" * 70)
print("G23 资金整合")
print("=" * 70)

# 1. 获取逐仓资产
print("\n[1] 逐仓资产清单:")
assets = get_margin_balance()
total_margin = sum(a['value'] for a in assets)
print(f"  总计: ${total_margin:.2f}")

# 2. 确定变现资产 (小额,非核心)
KEEP_ASSETS = ['LINK', 'BTC', 'ETH']  # 保留核心仓位
liquidate = [a for a in assets if a['asset'] not in KEEP_ASSETS and a['value'] > 1]  # 变现>$1的
keep = [a for a in assets if a['asset'] in KEEP_ASSETS]

print(f"\n[2] 保留资产:")
for a in keep:
    print(f"  ✅ {a['asset']}: {a['qty']:.6f} (${a['value']:.2f})")

print(f"\n[3] 待变现资产:")
liquidate_value = 0
for a in liquidate:
    print(f"  💰 {a['asset']}: {a['qty']:.6f} (${a['value']:.2f})")
    liquidate_value += a['value']
    
    # 执行卖出
    try:
        result = margin_sell(a['asset'], a['qty'])
        if 'orderId' in result:
            print(f"     -> 卖出成功!")
        else:
            print(f"     -> 失败: {result.get('msg', result)}")
    except Exception as e:
        print(f"     -> 错误: {e}")

print(f"\n[4] 变现总额: ${liquidate_value:.2f}")

# 5. 转账到合约
spot_usdt = get_spot_balance()
print(f"\n[5] 现货USDT余额: ${spot_usdt:.2f}")

if spot_usdt > 10:
    amount = round(spot_usdt * 0.95, 2)
    print(f"  转账 ${amount:.2f} 到合约账户...")
    result = transfer_to_futures(amount)
    if 'tranId' in result:
        print(f"  ✅ 转账成功! TranID: {result['tranId']}")
    else:
        print(f"  ❌ 转账失败: {result.get('msg', result)}")

print("\n" + "=" * 70)
print("资金整合完成!")
