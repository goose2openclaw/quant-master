#!/usr/bin/env python3
"""
G23 Meme币交易版 v2
===================
17个已确认的Binance可交易Meme币:
DOGE, PEPE, PENGU, BONK, SHIB, TRUMP, PUMP, WIF, FLOKI,
NEIRO, VANA, PNUT, BOME, TURBO, MEME, KAITO, 1MBABYDOGE

风控参数:
- RSI < 35 且下跌 -> BUY
- RSI > 65 且上涨 -> SELL
- 止损: -5%
- 止盈: +15%
- 仓位: 10%
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 17个已确认Meme币
MEME_COINS = [
    'DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
    'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE'
]

# 风控参数
RSI_PERIOD = 14
OVERSOLD = 35
OVERBOUGHT = 65
MIN_VOLUME = 500000   # 24h成交量>$500k
POSITION_SIZE = 0.1    # 10%仓位

def api(url):
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=15)
        return json.loads(resp.read().decode())
    except: return {}

def binance_24hr(symbol):
    url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'
    return api(url)

def klines(symbol, limit=100):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    data = api(url)
    if data:
        return [float(k[4]) for k in data]
    return []

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

def buy(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url)

def sell(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url)

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
            if free > 10:  # 现货
                asset = b['asset']
                if asset != 'USDT':
                    try:
                        price_url = f'https://api.binance.com/api/v3/ticker/price?symbol={asset}USDT'
                        pdata = api(price_url)
                        if 'price' in pdata:
                            positions[asset] = free
                    except: pass
    return positions

def main():
    print("=" * 80)
    print("G23 Meme币交易版 v2 (17币种)")
    print("=" * 80)
    
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] Meme币扫描\n")
    
    usdt = get_balance()
    positions = get_positions()
    print(f"可用USDT: ${usdt:.2f}")
    print(f"持仓: {list(positions.keys())}\n")
    
    # 分析信号
    buy_signals = []
    sell_signals = []
    
    print(f"{'币种':15} {'RSI':>6} {'24h涨跌':>10} {'成交量':>12} {'信号':>8}")
    print("-" * 60)
    
    for coin in MEME_COINS:
        symbol = f"{coin}USDT"
        h24 = binance_24hr(symbol)
        if not h24 or 'lastPrice' not in h24:
            continue
        
        price = float(h24.get('lastPrice', 0))
        volume = float(h24.get('quoteVolume', 0))
        change_24h = float(h24.get('priceChangePercent', 0))
        
        if volume < MIN_VOLUME:
            continue
        
        prices = klines(symbol, 50)
        if len(prices) < 20:
            continue
        
        rsi = calc_rsi(prices)
        
        # 信号
        signal = 'HOLD'
        if rsi < OVERSOLD and change_24h < -3:
            signal = 'BUY'
            buy_signals.append((coin, rsi, change_24h, volume, price))
        elif rsi > OVERBOUGHT and change_24h > 3:
            signal = 'SELL'
            if coin in positions:
                sell_signals.append((coin, rsi, change_24h, volume, price))
        
        emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '⚪'
        vol_str = f"${volume/1000000:.1f}M"
        print(f"{emoji} {coin:13} {rsi:>6.1f} {change_24h:>+9.2f}% {vol_str:>12} {signal:>8}")
    
    # 执行交易
    print(f"\n{'='*80}")
    print("[决策]")
    
    # 卖出信号优先
    if sell_signals:
        coin, rsi, change, volume, price = sell_signals[0]
        qty = positions.get(coin, 0)
        if qty > 0:
            # 计算精度
            qty_str = f"{qty:.0f}" if qty > 1 else f"{qty:.6f}"
            print(f"  🔴 卖出 {coin}: RSI={rsi:.1f} 24h={change:+.2f}%")
            print(f"     数量: {qty_str} 当前价${price:.8f}")
            result = sell(symbol, qty_str)
            if 'orderId' in result:
                print(f"     ✅ 成功! 订单ID: {result['orderId']}")
            else:
                print(f"     ❌ 失败: {result.get('msg', result)}")
    
    # 买入信号
    elif buy_signals and usdt > 20:
        buy_signals.sort(key=lambda x: (x[1], x[2]), reverse=True)  # RSI低优先
        coin, rsi, change, volume, price = buy_signals[0]
        amount = usdt * POSITION_SIZE
        qty = amount / price
        
        # 计算精度
        if qty > 1:
            qty_str = f"{qty:.0f}"
        elif qty > 0.001:
            qty_str = f"{qty:.2f}"
        else:
            qty_str = f"{qty:.6f}"
        
        print(f"  🟢 买入 {coin}")
        print(f"     RSI={rsi:.1f} 24h={change:+.2f}% 数量={qty_str}")
        print(f"     金额=${amount:.2f} 价格${price:.8f}")
        
        result = buy(f"{coin}USDT", qty_str)
        if 'orderId' in result:
            print(f"     ✅ 成功! 订单ID: {result['orderId']}")
        else:
            print(f"     ❌ 失败: {result.get('msg', result)}")
    
    else:
        print(f"  ⏸️ 无信号 (资金${usdt:.2f})")
        if buy_signals:
            print(f"  买入候选: {[(b[0], b[1]) for b in buy_signals[:3]]}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
