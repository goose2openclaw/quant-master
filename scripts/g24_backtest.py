#!/usr/bin/env python3
"""
G24 30天回测
"""
import urllib.request, json, time
import numpy as np

PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE']

RSI_PERIOD = 14
MAJOR_OVERSOLD = 35
MAJOR_OVERBOUGHT = 65
MEME_OVERSOLD = 30
MEME_OVERBOUGHT = 70
STOP_LOSS = 0.05
TAKE_PROFIT = 0.15

def api(url):
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except: return None

def get_klines(symbol, days=30, interval='1h'):
    end = int(time.time() * 1000)
    start = end - days * 24 * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start}&endTime={end}&limit=1000'
    data = api(url)
    if data:
        return [float(k[4]) for k in data]
    return []

def calc_rsi(prices, period=14):
    if len(prices) < period + 2: return [50] * len(prices)
    rsi_values = []
    # Start from the beginning, pad with 50s
    for i in range(len(prices)):
        if i < period:
            rsi_values.append(50)
        else:
            deltas = np.diff(prices[i-period:i+1])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
    return rsi_values

def backtest(prices, oversold, overbought):
    if len(prices) < 100: return None
    
    rsi_values = calc_rsi(prices)
    
    trades = []
    position = None
    wins = 0
    losses = 0
    total_return = 0
    
    for i in range(50, len(prices)):  # Start from index 50 to have enough RSI data
        price = prices[i]
        rsi = rsi_values[i]
        
        if position is None:
            if rsi < oversold:
                position = {'entry': price, 'index': i}
        else:
            pnl = (price - position['entry']) / position['entry']
            if pnl <= -STOP_LOSS or pnl >= TAKE_PROFIT or rsi > overbought:
                if pnl > 0:
                    wins += 1
                else:
                    losses += 1
                total_return += pnl
                trades.append({'pnl': pnl, 'hold': i - position['index']})
                position = None
    
    if position:
        pnl = (prices[-1] - position['entry']) / position['entry']
        total_return += pnl
        trades.append({'pnl': pnl, 'hold': len(prices) - position['index']})
        if pnl > 0: wins += 1
        else: losses += 1
    
    total = wins + losses
    if total == 0: return None
    
    return {
        'trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': wins / total * 100,
        'total_return': total_return * 100,
        'avg_return': (total_return / total) * 100 if total > 0 else 0
    }

def main():
    print("=" * 80)
    print("G24 30天回测报告")
    print("=" * 80)
    
    all_major = []
    all_meme = []
    
    # 主流币
    print("\n【主流币回测】")
    print(f"{'币种':10} {'交易':>6} {'胜':>4} {'负':>4} {'胜率':>8} {'总收益':>10} {'均收益':>10}")
    print("-" * 58)
    
    for coin in MAJOR_COINS:
        prices = get_klines(f"{coin}USDT", 30)
        if len(prices) < 500:
            print(f"{coin:10} 数据不足")
            continue
        result = backtest(prices, MAJOR_OVERSOLD, MAJOR_OVERBOUGHT)
        if result:
            emoji = '🟢' if result['total_return'] > 0 else '🔴'
            print(f"{emoji}{coin:9} {result['trades']:>6} {result['wins']:>4} {result['losses']:>4} {result['win_rate']:>7.1f}% {result['total_return']:>+9.1f}% {result['avg_return']:>+9.1f}%")
            all_major.append({**result, 'coin': coin})
        else:
            print(f"⚪{coin:9} 无交易")
    
    # Meme币
    print("\n【Meme币回测】")
    print(f"{'币种':15} {'交易':>6} {'胜':>4} {'负':>4} {'胜率':>8} {'总收益':>10} {'均收益':>10}")
    print("-" * 65)
    
    for coin in sorted(set(MEME_COINS)):
        prices = get_klines(f"{coin}USDT", 30)
        if len(prices) < 500:
            continue
        result = backtest(prices, MEME_OVERSOLD, MEME_OVERBOUGHT)
        if result:
            emoji = '🟢' if result['total_return'] > 0 else '🔴'
            print(f"{emoji}{coin:14} {result['trades']:>6} {result['wins']:>4} {result['losses']:>4} {result['win_rate']:>7.1f}% {result['total_return']:>+9.1f}% {result['avg_return']:>+9.1f}%")
            all_meme.append({**result, 'coin': coin})
        else:
            print(f"⚪{coin:14} 无交易")
    
    # 汇总
    print("\n" + "=" * 80)
    print("【汇总】")
    print("=" * 80)
    
    if all_major:
        mw = sum(m['wins'] for m in all_major)
        mt = sum(m['trades'] for m in all_major)
        mr = sum(m['total_return'] for m in all_major) / len(all_major)
        print(f"\n📊 主流币: {len(all_major)}个币, {mt}笔交易, 胜率{mw/mt*100:.1f}%, 平均总收益{mr:+.1f}%")
    
    if all_meme:
        kw = sum(m['wins'] for m in all_meme)
        kt = sum(m['trades'] for m in all_meme)
        kr = sum(m['total_return'] for m in all_meme) / len(all_meme)
        print(f"📊 Meme币: {len(all_meme)}个币, {kt}笔交易, 胜率{kw/kt*100:.1f}%, 平均总收益{kr:+.1f}%")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
