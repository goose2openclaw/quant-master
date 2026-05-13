#!/usr/bin/env python3
"""
G20 增强版 - 自主变现 + 交易
"""
import urllib.request, urllib.parse, hmac, hashlib, time, json, numpy as np
from datetime import datetime

PROXY = "http://172.29.144.1:7897"
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

def api_request(url, method='GET', params=None):
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    data = api_request(url)
    return float(data['price'])

def get_margin_balance():
    """获取全仓逐仓余额"""
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/margin/account?timestamp={ts}&signature={sig}"
    data = api_request(url)
    if 'userAssets' in data:
        assets = {}
        for a in data['userAssets']:
            free = float(a.get('free', 0))
            if free > 0:
                assets[a['asset']] = free
        return assets
    return {}

def get_spot_balance():
    """获取现货余额"""
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api_request(url)
    if 'balances' in data:
        assets = {}
        for b in data['balances']:
            free = float(b.get('free', 0))
            if free > 0:
                assets[b['asset']] = free
        return assets
    return {}

def sell_margin(asset, qty):
    """全仓逐仓卖出"""
    ts = int(time.time() * 1000)
    q = f"symbol={asset}USDT&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api_request(url, 'POST')

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def get_klines(sym, limit=100):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    r = api_request(url)
    return [float(k[4]) for k in r]

def buy_spot(symbol, qty):
    """现货买入"""
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api_request(url, 'POST')

# G20参数
PARAMS = {
    'BTC': {'rsi_buy': 45, 'rsi_sell': 79, 'tp': 0.092, 'sl': 0.034},
    'ETH': {'rsi_buy': 29, 'rsi_sell': 79, 'tp': 0.054, 'sl': 0.042},
    'DOGE': {'rsi_buy': 45, 'rsi_sell': 80, 'tp': 0.07, 'sl': 0.03},
    'LINK': {'rsi_buy': 44, 'rsi_sell': 77, 'tp': 0.06, 'sl': 0.045},
}

print("=" * 70)
print("G20 增强版 - 自主变现 + 交易")
print("=" * 70)

# Step 1: 检查全仓逐仓资产
print("\n[Step 1] 检查全仓逐仓资产...")
margin_assets = get_margin_balance()
print(f"全仓逐仓资产: {margin_assets}")

# Step 2: 变现 (ADA, XRP, DOGE)
print("\n[Step 2] 执行变现...")
SELL_ASSETS = ['ADA', 'XRP', 'DOGE']
for asset in SELL_ASSETS:
    if asset in margin_assets and margin_assets[asset] > 1:
        qty = margin_assets[asset]
        price = get_price(f"{asset}USDT")
        val = qty * price
        if val > 1:  # 只变现大于$1的
            print(f"卖出 {asset}: {qty} @ ${price:.4f} = ${val:.2f}")
            result = sell_margin(asset, qty)
            if 'orderId' in result:
                print(f"  ✅ 成功卖出 {asset}")
            else:
                print(f"  ❌ 失败: {result.get('msg', result)}")

# Step 3: 检查余额
print("\n[Step 3] 检查可用资金...")
spot = get_spot_balance()
usdt = spot.get('USDT', 0)
print(f"现货USDT: ${usdt:.2f}")

# Step 4: 获取交易信号
print("\n[Step 4] 检查G20交易信号...")
signals = []
for coin, params in PARAMS.items():
    prices = get_klines(f'{coin}USDT')
    if len(prices) < 50:
        continue
    rsi = calc_rsi(prices)
    if rsi < params['rsi_buy']:
        signal = 'BUY'
    elif rsi > params['rsi_sell']:
        signal = 'SELL'
    else:
        signal = 'HOLD'
    signals.append({'coin': coin, 'rsi': rsi, 'signal': signal, 'params': params})
    emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
    print(f"  {emoji} {coin}: RSI={rsi:.1f}, Signal={signal}")

# Step 5: 执行交易
print("\n[Step 5] 执行交易...")
buy_signals = [s for s in signals if s['signal'] == 'BUY']

if buy_signals and usdt > 5:
    per_coin = (usdt * 0.9) / len(buy_signals)  # 保留10%备用
    print(f"可用资金: ${usdt:.2f}, 每币分配: ${per_coin:.2f}")
    
    for sig in buy_signals:
        coin = sig['coin']
        price = get_price(f'{coin}USDT')
        qty = per_coin / price
        
        # 调整数量精度
        if coin == 'BTC':
            qty = round(qty, 5)
        elif coin == 'ETH':
            qty = round(qty, 4)
        elif coin == 'DOGE':
            qty = int(qty)
        else:
            qty = round(qty, 2)
        
        print(f"买入 {coin}: ${per_coin:.2f} -> {qty} @ ${price:.4f}")
        result = buy_spot(f'{coin}USDT', qty)
        if 'orderId' in result:
            print(f"  ✅ 成功买入 {coin}")
        else:
            print(f"  ❌ 失败: {result.get('msg', result)}")
else:
    print("无买入信号或资金不足")

print("\n" + "=" * 70)
