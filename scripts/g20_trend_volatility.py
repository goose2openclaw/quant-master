#!/usr/bin/env python3
"""
G20 趋势震荡双策略版
- 趋势市场: 追涨杀跌 (顺趋势)
- 震荡市场: 高抛低吸 (逆趋势)
"""
import urllib.request, hmac, hashlib, time, json, numpy as np

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

def api(url, method='GET'):
    req = urllib.request.Request(url, method=method)
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

def klines(sym, limit=100):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=15)
    return [float(k[4]) for k in json.loads(resp.read().decode())]

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_ema(prices, period):
    if len(prices) < period: return prices[-1]
    return np.mean(prices[-period:])

def detect_trend(prices):
    """检测市场类型: 趋势 or 震荡"""
    if len(prices) < 50: return 'unknown'
    
    # 趋势强度
    ema20 = calc_ema(prices, 20)
    ema50 = calc_ema(prices, 50)
    trend_ratio = (ema20 - ema50) / ema50 * 100
    
    # 波动率
    vol = np.std(prices[-20:]) / np.mean(prices[-20:]) * 100
    
    # 趋势判断
    if abs(trend_ratio) > 2 and vol > 1.5:
        return 'TREND'  # 趋势市场
    else:
        return 'RANGE'  # 震荡市场

def get_signal_trend(rsi, prices):
    """趋势策略: 追涨杀跌"""
    # RSI > 70 且上涨 -> 追涨买入
    # RSI < 30 且下跌 -> 杀跌卖出
    if rsi > 70:
        return 'BUY'  # 追涨
    elif rsi < 30:
        return 'SELL'  # 杀跌
    return 'HOLD'

def get_signal_range(rsi):
    """震荡策略: 高抛低吸"""
    # RSI > 70 -> 高抛卖出
    # RSI < 30 -> 低吸买入
    if rsi > 70:
        return 'SELL'  # 高抛
    elif rsi < 30:
        return 'BUY'  # 低吸
    return 'HOLD'

def get_balance():
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

def buy(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, 'POST')

def sell(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, 'POST')

COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']

print("=" * 80)
print("G20 双策略版 - 趋势/震荡自适应")
print("=" * 80)

usdt = get_balance()
print(f"\n[资金] USDT: ${usdt:.2f}")

print("\n[分析] 市场检测:")
results = []
for coin in COINS:
    prices = klines(f'{coin}USDT')
    if len(prices) < 50: continue
    
    rsi = calc_rsi(prices)
    market = detect_trend(prices)
    
    if market == 'TREND':
        signal = get_signal_trend(rsi, prices)
        strategy = '趋势(追涨杀跌)'
    else:
        signal = get_signal_range(rsi)
        strategy = '震荡(高抛低吸)'
    
    emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
    print(f"  {emoji} {coin}: RSI={rsi:.0f} {market} {strategy} -> {signal}")
    
    results.append({
        'coin': coin,
        'rsi': rsi,
        'market': market,
        'signal': signal,
        'strategy': strategy
    })

print("\n[决策]")
buy_signals = [r for r in results if r['signal'] == 'BUY']
sell_signals = [r for r in results if r['signal'] == 'SELL']

if buy_signals and usdt > 10:
    coin = buy_signals[0]['coin']
    amount = usdt * 0.9
    p = price(f'{coin}USDT')
    qty = round(amount / p, 4)
    print(f"  ✅ 买入 {coin}: ${amount:.2f} -> {qty}")
    result = buy(f'{coin}USDT', qty)
    if 'orderId' in result:
        print(f"     成功! 订单ID: {result['orderId']}")
    else:
        print(f"     失败: {result.get('msg', result)}")
elif sell_signals:
    coin = sell_signals[0]['coin']
    print(f"  🔴 卖出信号: {coin}")
    print(f"     但需要持仓才能执行卖出")
else:
    print(f"  ⏸️ 无信号")

print("\n" + "=" * 80)
