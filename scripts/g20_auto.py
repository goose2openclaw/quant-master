#!/usr/bin/env python3
"""G20 完全自主版 - 自主决策+自动执行"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

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

def detect_market(prices):
    if len(prices) < 50: return 'RANGE'
    ema20 = calc_ema(prices, 20)
    ema50 = calc_ema(prices, 50)
    trend = (ema20 - ema50) / ema50 * 100
    vol = np.std(prices[-20:]) / np.mean(prices[-20:]) * 100
    if abs(trend) > 2 and vol > 1.5: return 'TREND'
    return 'RANGE'

def get_signal(rsi, market):
    if market == 'TREND':
        return 'BUY' if rsi > 70 else 'SELL' if rsi < 30 else 'HOLD'
    else:
        return 'BUY' if rsi < 30 else 'SELL' if rsi > 70 else 'HOLD'

def get_balance():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    if 'balances' in data:
        for b in data['balances']:
            if b['asset'] == 'USDT': return float(b['free'])
    return 0

def get_positions():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    positions = {}
    if 'balances' in data:
        for b in data['balances']:
            free = float(b.get('free', 0))
            if free > 0.00001 and b['asset'] != 'USDT':
                try:
                    p = price(b['asset']+'USDT')
                    positions[b['asset']] = {'qty': free, 'price': p, 'value': free * p}
                except: pass
    return positions

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

def main():
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] G20 自主运行")
    
    # 获取资金和持仓
    usdt = get_balance()
    positions = get_positions()
    
    # 分析所有币种
    decisions = []
    for coin in COINS:
        prices = klines(f'{coin}USDT')
        if len(prices) < 50: continue
        rsi = calc_rsi(prices)
        market = detect_market(prices)
        signal = get_signal(rsi, market)
        decisions.append({
            'coin': coin, 'rsi': rsi, 'market': market, 'signal': signal,
            'prices': prices
        })
    
    # 决策执行
    for d in decisions:
        coin = d['coin']
        signal = d['signal']
        
        if signal == 'BUY' and usdt > 10:
            # 买入
            amount = usdt * 0.95
            p = price(f'{coin}USDT')
            qty = round(amount / p, 4)
            result = buy(f'{coin}USDT', qty)
            if 'orderId' in result:
                print(f"  ✅ BUY {coin}: {qty} @ ${p:.2f}")
                usdt -= amount
            else:
                print(f"  ❌ BUY {coin}: {result.get('msg', 'failed')}")
        
        elif signal == 'SELL' and coin in positions:
            # 卖出
            pos = positions[coin]
            qty = round(pos['qty'] * 0.95, 4)
            result = sell(f'{coin}USDT', qty)
            if 'orderId' in result:
                print(f"  ✅ SELL {coin}: {qty} @ ${pos['price']:.2f}")
            else:
                print(f"  ❌ SELL {coin}: {result.get('msg', 'failed')}")

if __name__ == '__main__':
    main()
