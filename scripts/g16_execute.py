#!/usr/bin/env python3
"""
G16 v2.0 自主执行 - 做空BTC/ETH
"""
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

def get_price(symbol):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', 
                        proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def place_order(symbol, side, qty):
    try:
        url = 'https://api.binance.com/api/v3/order'
        params = {'symbol': symbol, 'side': side, 'type': 'MARKET', 'quantity': qty}
        r = requests.post(url + '?' + sign(params),
                        headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def get_futures_balance():
    try:
        url = 'https://fapi.binance.com/fapi/v2/account'
        r = requests.get(url + '?' + sign({}), 
                        headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

print("=" * 60)
print("G16 v2.0 自主执行")
print("=" * 60)

# 检查余额
print("\n余额检查:")
fut = get_futures_balance()
if fut:
    available = float(fut.get('availableBalance', 0))
    total = float(fut.get('totalMarginBalance', 0))
    print(f"  可用: ${available:.2f}")
    print(f"  总资产: ${total:.2f}")

# 获取价格
btc_price = get_price('BTCUSDT')
eth_price = get_price('ETHUSDT')
print(f"\n当前价格:")
print(f"  BTC: ${btc_price:.2f}")
print(f"  ETH: ${eth_price:.2f}")

# 计算仓位
position_pct = 0.35  # 35%仓位
leverage = 5
use_amount = available * position_pct / leverage

# BTC做空
btc_qty = use_amount / btc_price
btc_qty = round(btc_qty, 4)  # BTC 4位精度
print(f"\n执行做空:")
print(f"  BTC SHORT: {btc_qty} BTC @ ${btc_price:.2f}")
print(f"  预计保证金: ${btc_qty * btc_price / leverage:.2f}")

# ETH做空
eth_qty = use_amount / eth_price
eth_qty = round(eth_qty, 3)  # ETH 3位精度
print(f"  ETH SHORT: {eth_qty} ETH @ ${eth_price:.2f}")
print(f"  预计保证金: ${eth_qty * eth_price / leverage:.2f}")

# 执行
print("\n正在下单...")
print("-" * 40)

# BTC
result_btc = place_order('BTCUSDT', 'SELL', btc_qty)
if 'error' in result_btc:
    print(f"  BTC: ❌ {result_btc['error']}")
else:
    print(f"  BTC: ✅ 订单已提交")
    print(f"       订单ID: {result_btc.get('orderId', 'N/A')}")
    print(f"       状态: {result_btc.get('status', 'N/A')}")

# ETH
result_eth = place_order('ETHUSDT', 'SELL', eth_qty)
if 'error' in result_eth:
    print(f"  ETH: ❌ {result_eth['error']}")
else:
    print(f"  ETH: ✅ 订单已提交")
    print(f"       订单ID: {result_eth.get('orderId', 'N/A')}")
    print(f"       状态: {result_eth.get('status', 'N/A')}")

print("=" * 60)
