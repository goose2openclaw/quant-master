#!/usr/bin/env python3
"""
G23 资金整合完整解决方案 V2
==========================
功能:
1. 逐仓转现货 (type=2)
2. 变现小额资产
3. USDT转入合约账户
4. 准备资金费率套利
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

def get_margin_assets():
    """获取逐仓所有资产"""
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/sapi/v1/margin/account?timestamp={ts}&signature={sig}"
    data = api(url)
    assets = []
    if 'userAssets' in data:
        for a in data['userAssets']:
            free = float(a.get('free', 0))
            if free > 0:
                asset = a['asset']
                try:
                    p = price(asset + 'USDT')
                    assets.append({'asset': asset, 'qty': free, 'price': p, 'value': free * p})
                except:
                    assets.append({'asset': asset, 'qty': free, 'price': 0, 'value': 0})
    return assets

def margin_to_spot(asset, qty):
    """逐仓转现货 (type=2)"""
    ts = int(time.time() * 1000)
    q = f"asset={asset}&symbol={asset}USDT&amount={qty}&type=2&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/sapi/v1/margin/transfer?{q}&signature={sig}"
    return api(url, 'POST')

def spot_sell(asset, qty):
    """现货卖出"""
    ts = int(time.time() * 1000)
    q = f"symbol={asset}USDT&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
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
    """转入合约账户"""
    ts = int(time.time() * 1000)
    q = f"asset=USDT&amount={amount}&type=FUTURE&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/sapi/v1/asset/transfer?{q}&signature={sig}"
    return api(url, 'POST')

def get_futures_balance():
    """获取合约USDT"""
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.bapi.com/fapi/v1/balance?timestamp={ts}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode())
        for item in data:
            if item.get('asset') == 'USDT':
                return float(item.get('availableBalance', 0))
    except:
        return 0

# ========== 主程序 ==========
def main():
    print("=" * 70)
    print("G23 资金整合完整解决方案 V2")
    print("=" * 70)
    
    # Step 1: 获取逐仓资产
    print("\n[Step 1] 获取逐仓资产...")
    assets = get_margin_assets()
    total_margin = sum(a['value'] for a in assets)
    print(f"  逐仓总计: ${total_margin:.2f}")
    
    # Step 2: 确定保留和变现资产
    KEEP = ['LINK', 'BTC', 'ETH']
    liquidatable = [a for a in assets if a['asset'] not in KEEP and a['value'] >= 1]
    to_keep = [a for a in assets if a['asset'] in KEEP]
    
    print(f"\n[Step 2] 资产分类:")
    print(f"  保留 ({len(to_keep)}个):")
    for a in to_keep:
        print(f"    ✅ {a['asset']}: {a['qty']:.6f} (${a['value']:.2f})")
    
    print(f"  变现 ({len(liquidatable)}个):")
    for a in liquidatable:
        print(f"    💰 {a['asset']}: {a['qty']:.6f} (${a['value']:.2f})")
    
    # Step 3: 逐仓转现货
    print(f"\n[Step 3] 逐仓转现货...")
    for a in liquidatable:
        if a['value'] >= 1:
            print(f"  转账 {a['asset']}: {a['qty']:.6f}...")
            result = margin_to_spot(a['asset'], a['qty'])
            if 'tranId' in result:
                print(f"    ✅ 成功! TranID: {result['tranId']}")
            else:
                print(f"    ❌ 失败: {result.get('msg', result)}")
            time.sleep(0.5)
    
    # Step 4: 现货卖出
    print(f"\n[Step 4] 现货卖出...")
    spot_assets = get_margin_assets()
    for a in spot_assets:
        if a['asset'] not in KEEP and a['value'] >= 1:
            print(f"  卖出 {a['asset']}: {a['qty']:.6f}...")
            result = spot_sell(a['asset'], a['qty'])
            if 'orderId' in result:
                print(f"    ✅ 成功! 订单ID: {result['orderId']}")
            else:
                print(f"    ❌ 失败: {result.get('msg', result)}")
            time.sleep(0.5)
    
    # Step 5: 转入合约
    print(f"\n[Step 5] 转入合约...")
    usdt_spot = get_spot_balance()
    print(f"  现货USDT: ${usdt_spot:.2f}")
    
    if usdt_spot >= 10:
        amount = round(usdt_spot * 0.99, 2)
        print(f"  转账 ${amount:.2f} 到合约...")
        result = transfer_to_futures(amount)
        if 'tranId' in result:
            print(f"    ✅ 成功! TranID: {result['tranId']}")
        else:
            print(f"    ❌ 失败: {result.get('msg', result)}")
    
    # Step 6: 最终状态
    print(f"\n[Step 6] 最终状态...")
    usdt_final = get_spot_balance()
    fut_final = get_futures_balance()
    final_margin = get_margin_assets()
    
    print(f"  现货USDT: ${usdt_final:.2f}")
    print(f"  合约USDT: ${fut_final:.2f}")
    print(f"  逐仓资产: {len(final_margin)}个")
    
    print("\n" + "=" * 70)
    print("资金整合完成!")
    print("=" * 70)

if __name__ == '__main__':
    main()
