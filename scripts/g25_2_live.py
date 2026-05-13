#!/usr/bin/env python3
"""
G25.2 实盘交易版
================
接管实盘交易:
1. 使用精细优化后的参数
2. 全市场扫描
3. 自动下单
4. 严格风控
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime
from itertools import product

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 全市场币种
MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI', 'BCH', 'LTC', 'ATOM']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE']

# 预优化的G25.2参数
OPTIMIZED_PARAMS = {
    'DOGE': {'oversold': 45, 'overbought': 70, 'stop': 0.05, 'take': 0.10},
    'LINK': {'oversold': 40, 'overbought': 75, 'stop': 0.05, 'take': 0.10},
    'ETH': {'oversold': 45, 'overbought': 75, 'stop': 0.03, 'take': 0.10},
    'SOL': {'oversold': 45, 'overbought': 75, 'stop': 0.05, 'take': 0.10},
    'BTC': {'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.10},
    'XRP': {'oversold': 40, 'overbought': 75, 'stop': 0.03, 'take': 0.10},
    'ADA': {'oversold': 30, 'overbought': 75, 'stop': 0.03, 'take': 0.10},
    'AVAX': {'oversold': 30, 'overbought': 75, 'stop': 0.07, 'take': 0.10},
    'DOT': {'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.10},
    'UNI': {'oversold': 40, 'overbought': 75, 'stop': 0.05, 'take': 0.10},
    'PENGU': {'oversold': 45, 'overbought': 55, 'stop': 0.07, 'take': 0.10},
    'BOME': {'oversold': 35, 'overbought': 75, 'stop': 0.07, 'take': 0.10},
    'WIF': {'oversold': 45, 'overbought': 75, 'stop': 0.07, 'take': 0.20},
    'PNUT': {'oversold': 40, 'overbought': 65, 'stop': 0.07, 'take': 0.10},
    'PUMP': {'oversold': 45, 'overbought': 75, 'stop': 0.07, 'take': 0.15},
    'TURBO': {'oversold': 40, 'overbought': 65, 'stop': 0.07, 'take': 0.10},
    'NEIRO': {'oversold': 45, 'overbought': 75, 'stop': 0.07, 'take': 0.10},
    'SHIB': {'oversold': 45, 'overbought': 75, 'stop': 0.05, 'take': 0.10},
    'PEPE': {'oversold': 45, 'overbought': 75, 'stop': 0.03, 'take': 0.10},
    'MEME': {'oversold': 30, 'overbought': 75, 'stop': 0.07, 'take': 0.10},
    'FLOKI': {'oversold': 35, 'overbought': 75, 'stop': 0.07, 'take': 0.10},
    'BONK': {'oversold': 40, 'overbought': 70, 'stop': 0.07, 'take': 0.10},
    'VANA': {'oversold': 45, 'overbought': 65, 'stop': 0.05, 'take': 0.10},
    'KAITO': {'oversold': 45, 'overbought': 60, 'stop': 0.07, 'take': 0.10},
    '1MBABYDOGE': {'oversold': 30, 'overbought': 70, 'stop': 0.07, 'take': 0.10},
    'TRUMP': {'oversold': 40, 'overbought': 75, 'stop': 0.03, 'take': 0.10},
}

DEFAULT_PARAMS = {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.15}
POSITION_MAP = {
    'DOGE': 0.15, 'LINK': 0.15, 'ETH': 0.10, 'SOL': 0.10,
    'BTC': 0.10, 'XRP': 0.10, 'ADA': 0.10, 'UNI': 0.10,
    'BOME': 0.05, 'TURBO': 0.05, 'NEIRO': 0.05, 'PENGU': 0.05, 'PEPE': 0.05
}
MIN_VOLUME = 500000

MAX_POSITIONS = 3

def api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except: return {}

def price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return float(json.loads(opener.open(req, timeout=10).read().decode())['price'])
    except: return 0

def binance_24hr(symbol):
    url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return json.loads(opener.open(req, timeout=10).read().decode())
    except: return {}

def klines(sym, limit=100, interval='1h'):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return [float(k[4]) for k in json.loads(opener.open(req, timeout=15).read().decode())]
    except: return []

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

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
            if free > 10:
                asset = b['asset']
                if asset != 'USDT':
                    p = price(f'{asset}USDT')
                    if p > 0: positions[asset] = free
    return positions

def buy(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, method='POST')

def sell(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, method='POST')

def analyze_coin(coin):
    symbol = f"{coin}USDT"
    h24 = binance_24hr(symbol)
    if not h24 or 'lastPrice' not in h24: return None
    
    p = float(h24['lastPrice'])
    v = float(h24['quoteVolume'])
    chg = float(h24['priceChangePercent'])
    
    if v < MIN_VOLUME: return None
    
    prices = klines(symbol, 50)
    if len(prices) < 20: return None
    
    rsi = calc_rsi(prices)
    params = OPTIMIZED_PARAMS.get(coin, DEFAULT_PARAMS)
    position = POSITION_MAP.get(coin, 0.10)
    
    signal = 'HOLD'
    if rsi < params['oversold'] and chg < -2:
        signal = 'BUY'
    elif rsi > params['overbought'] and chg > 2:
        signal = 'SELL'
    
    return {
        'coin': coin, 'symbol': symbol, 'price': p, 'rsi': rsi,
        'change_24h': chg, 'volume': v, 'signal': signal,
        'params': params, 'position': position
    }

def main():
    print("=" * 80)
    print("G25.2 实盘交易版")
    print("=" * 80)
    
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{ts}] G25.2 实盘扫描\n")
    
    usdt = get_balance()
    positions = get_positions()
    
    print(f"【账户状态】")
    print(f"  可用USDT: ${usdt:.2f}")
    print(f"  当前持仓: {list(positions.keys())}")
    print(f"  持仓数量: {len(positions)}/{MAX_POSITIONS}")
    print()
    
    all_coins = list(set(MAJOR_COINS + MEME_COINS))
    signals = []
    
    print("【扫描信号】")
    for coin in all_coins:
        result = analyze_coin(coin)
        if result and result['signal'] != 'HOLD':
            signals.append(result)
            emoji = '🟢' if result['signal'] == 'BUY' else '🔴'
            p = result['params']
            print(f"  {emoji} {coin}: RSI={result['rsi']:.1f} 24h={result['change_24h']:+.1f}% -> {result['signal']}")
            print(f"      参数: RSI {p['oversold']}/{p['overbought']} SL={p['stop']:.0%} TP={p['take']:.0%}")
    
    if not signals:
        print("  无交易信号")
        return
    
    # 决策
    print(f"\n{'='*80}")
    print("[交易决策]")
    
    buy_signals = [s for s in signals if s['signal'] == 'BUY']
    sell_signals = [s for s in signals if s['signal'] == 'SELL']
    
    # 优先卖出
    if sell_signals and positions:
        for sig in sell_signals[:1]:
            coin = sig['coin']
            if coin in positions:
                qty = positions[coin]
                qty_str = f"{qty:.0f}" if qty > 1 else f"{qty:.6f}"
                print(f"  🔴 卖出 {coin}")
                result = sell(f"{coin}USDT", qty_str)
                if 'orderId' in result:
                    print(f"     ✅ 成功! 订单ID: {result['orderId']}")
                else:
                    print(f"     ❌ {result.get('msg', result)}")
    
    # 买入
    elif buy_signals and usdt > 20 and len(positions) < MAX_POSITIONS:
        # 按RSI排序
        buy_signals.sort(key=lambda x: x['rsi'])
        sig = buy_signals[0]
        coin = sig['coin']
        amount = usdt * sig['position']
        qty = amount / sig['price']
        qty_str = f"{qty:.0f}" if qty > 1 else f"{qty:.2f}" if qty > 0.001 else f"{qty:.6f}"
        
        print(f"  🟢 买入 {coin}")
        print(f"     RSI={sig['rsi']:.1f} 24h={sig['change_24h']:+.2f}%")
        print(f"     仓位={sig['position']:.0%} 数量={qty_str} 金额=${amount:.2f}")
        
        result = buy(f"{coin}USDT", qty_str)
        if 'orderId' in result:
            print(f"     ✅ 成功! 订单ID: {result['orderId']}")
        else:
            print(f"     ❌ {result.get('msg', result)}")
    else:
        print(f"  ⏸️ 无交易")
        print(f"     资金: ${usdt:.2f} | 持仓: {len(positions)}/{MAX_POSITIONS}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
