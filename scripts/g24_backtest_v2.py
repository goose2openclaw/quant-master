#!/usr/bin/env python3
"""
G24 回测 - 主流币 vs Meme币
"""
import urllib.request, json, time
import numpy as np

PROXY = "http://172.29.144.1:7897"

# G24 币种分层
TOP_COINS = ['DOGE', 'LINK']
SECOND_TIER = ['ETH', 'SOL']
MAJOR_COINS = ['BTC', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE']

# G24 v4 参数
def get_config(coin, is_meme=False):
    if coin in TOP_COINS:
        return {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.20}
    elif coin in SECOND_TIER:
        return {'oversold': 40, 'overbought': 75, 'stop': 0.05, 'take': 0.15}
    elif not is_meme:
        return {'oversold': 40, 'overbought': 75, 'stop': 0.03, 'take': 0.10}
    else:
        return {'oversold': 35, 'overbought': 80, 'stop': 0.07, 'take': 0.15}

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

def backtest(prices, oversold, overbought, stop_loss, take_profit):
    if len(prices) < 100: return None
    rsi_values = calc_rsi(prices)
    position = None
    wins = 0
    losses = 0
    total_return = 0
    
    for i in range(50, len(prices)):
        price = prices[i]
        rsi = rsi_values[i]
        
        if position is None:
            if rsi < oversold:
                position = {'entry': price, 'index': i}
        else:
            pnl = (price - position['entry']) / position['entry']
            if pnl <= -stop_loss or pnl >= take_profit or rsi > overbought:
                if pnl > 0: wins += 1
                else: losses += 1
                total_return += pnl
                position = None
    
    if position:
        pnl = (prices[-1] - position['entry']) / position['entry']
        total_return += pnl
        if pnl > 0: wins += 1
        else: losses += 1
    
    total = wins + losses
    if total == 0: return None
    
    return {
        'trades': total, 'wins': wins, 'losses': losses,
        'win_rate': wins / total * 100,
        'total_return': total_return * 100,
        'avg_return': (total_return / total) * 100 if total > 0 else 0
    }

def main():
    print("=" * 80)
    print("G24 30天回测 - 主流币 vs Meme币")
    print("=" * 80)
    
    all_major = []
    all_meme = []
    major_coins_list = TOP_COINS + SECOND_TIER + MAJOR_COINS
    
    # 主流币回测
    print("\n【🏆 TOP表现层 - DOGE/LINK】")
    print(f"{'币种':10} {'交易':>6} {'胜':>4} {'负':>4} {'胜率':>8} {'总收益':>10} {'均收益':>10}")
    print("-" * 58)
    for coin in TOP_COINS:
        prices = get_klines(f"{coin}USDT", 30)
        if len(prices) < 500: continue
        cfg = get_config(coin)
        result = backtest(prices, cfg['oversold'], cfg['overbought'], cfg['stop'], cfg['take'])
        if result:
            emoji = '🟢' if result['total_return'] > 0 else '🔴'
            print(f"{emoji}{coin:9} {result['trades']:>6} {result['wins']:>4} {result['losses']:>4} {result['win_rate']:>7.1f}% {result['total_return']:>+9.1f}% {result['avg_return']:>+9.1f}%")
            all_major.append({**result, 'coin': coin})
    
    print("\n【🥈 SECOND层 - ETH/SOL】")
    for coin in SECOND_TIER:
        prices = get_klines(f"{coin}USDT", 30)
        if len(prices) < 500: continue
        cfg = get_config(coin)
        result = backtest(prices, cfg['oversold'], cfg['overbought'], cfg['stop'], cfg['take'])
        if result:
            emoji = '🟢' if result['total_return'] > 0 else '🔴'
            print(f"{emoji}{coin:9} {result['trades']:>6} {result['wins']:>4} {result['losses']:>4} {result['win_rate']:>7.1f}% {result['total_return']:>+9.1f}% {result['avg_return']:>+9.1f}%")
            all_major.append({**result, 'coin': coin})
    
    print("\n【📊 STANDARD层 - 其他主流币】")
    for coin in MAJOR_COINS:
        prices = get_klines(f"{coin}USDT", 30)
        if len(prices) < 500: continue
        cfg = get_config(coin)
        result = backtest(prices, cfg['oversold'], cfg['overbought'], cfg['stop'], cfg['take'])
        if result:
            emoji = '🟢' if result['total_return'] > 0 else '🔴'
            print(f"{emoji}{coin:9} {result['trades']:>6} {result['wins']:>4} {result['losses']:>4} {result['win_rate']:>7.1f}% {result['total_return']:>+9.1f}% {result['avg_return']:>+9.1f}%")
            all_major.append({**result, 'coin': coin})
    
    # Meme币回测
    print("\n" + "=" * 80)
    print("【🔥 MEME币回测】")
    print(f"{'币种':15} {'交易':>6} {'胜':>4} {'负':>4} {'胜率':>8} {'总收益':>10} {'均收益':>10}")
    print("-" * 70)
    for coin in sorted(set(MEME_COINS)):
        prices = get_klines(f"{coin}USDT", 30)
        if len(prices) < 500: continue
        cfg = get_config(coin, is_meme=True)
        result = backtest(prices, cfg['oversold'], cfg['overbought'], cfg['stop'], cfg['take'])
        if result:
            emoji = '🟢' if result['total_return'] > 0 else '🔴'
            print(f"{emoji}{coin:14} {result['trades']:>6} {result['wins']:>4} {result['losses']:>4} {result['win_rate']:>7.1f}% {result['total_return']:>+9.1f}% {result['avg_return']:>+9.1f}%")
            all_meme.append({**result, 'coin': coin})
    
    # 汇总
    print("\n" + "=" * 80)
    print("【汇总】")
    print("=" * 80)
    
    if all_major:
        mw = sum(m['wins'] for m in all_major)
        mt = sum(m['trades'] for m in all_major)
        mr = sum(m['total_return'] for m in all_major) / len(all_major)
        wr = mw / mt * 100 if mt > 0 else 0
        print(f"\n📊 主流币: {len(all_major)}个币, {mt}笔交易")
        print(f"   胜率: {wr:.1f}%")
        print(f"   平均总收益: {mr:+.1f}%")
    
    if all_meme:
        kw = sum(m['wins'] for m in all_meme)
        kt = sum(m['trades'] for m in all_meme)
        kr = sum(m['total_return'] for m in all_meme) / len(all_meme)
        wr = kw / kt * 100 if kt > 0 else 0
        print(f"\n🔥 Meme币: {len(all_meme)}个币, {kt}笔交易")
        print(f"   胜率: {wr:.1f}%")
        print(f"   平均总收益: {kr:+.1f}%")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
