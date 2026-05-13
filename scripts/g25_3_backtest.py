#!/usr/bin/env python3
"""
G25.3 回测 - 主流币 vs Meme币
"""
import urllib.request, json, time
import numpy as np

PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE']

RANGE_LONG = {'oversold': 30, 'overbought': 70, 'stop': 0.03, 'take': 0.10, 'leverage': 3}
RANGE_SHORT = {'oversold': 70, 'overbought': 30, 'stop': 0.03, 'take': 0.10, 'leverage': 3}

def get_config(coin, is_meme=False):
    lev = 10 if is_meme else 5
    return {
        'long': {'oversold': 45, 'overbought': 55, 'stop': 0.02, 'take': 0.15, 'leverage': lev},
        'short': {'oversold': 55, 'overbought': 45, 'stop': 0.02, 'take': 0.15, 'leverage': lev}
    }

def api(url):
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return json.loads(opener.open(req, timeout=30).read().decode())
    except: return None

def klines(sym, days=30, interval='1h'):
    end = int(time.time() * 1000)
    start = end - days * 24 * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit=1000'
    data = api(url)
    if data: return [float(k[4]) for k in data]
    return []

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return [50] * len(prices)
    rsi = []
    for i in range(len(prices)):
        if i < period: rsi.append(50)
        else:
            d = np.diff(prices[i-period:i+1])
            g = np.where(d > 0, d, 0)
            l = np.where(d < 0, -d, 0)
            ag, al = np.mean(g), np.mean(l)
            rsi.append(100 - (100 / (1 + ag/al)) if al != 0 else 100)
    return rsi

def calc_momentum(prices, period=10):
    if len(prices) < period + 1: return [0] * len(prices)
    return [(prices[i] / prices[i-period] - 1) * 100 for i in range(period, len(prices))]

def detect_market(prices):
    rsi = calc_rsi(prices)
    mom = calc_momentum(prices)
    r = rsi[-1]
    m = mom[-1] if mom else 0
    if r > 60 and m > 2: return 'TREND_UP'
    if r < 40 and m < -2: return 'TREND_DOWN'
    return 'RANGE'

def backtest_coin(coin, is_meme=False):
    prices = klines(f"{coin}USDT", 30)
    if len(prices) < 500: return None
    
    cfg_long = get_config(coin, is_meme)['long']
    cfg_short = get_config(coin, is_meme)['short']
    rsi_vals = calc_rsi(prices)
    mom_vals = calc_momentum(prices)
    
    position = None
    wins, losses = 0, 0
    long_wins, long_losses, short_wins, short_losses = 0, 0, 0, 0
    long_ret, short_ret = 0.0, 0.0
    total_return = 0.0
    
    for i in range(20, len(prices)):
        rsi = rsi_vals[i]
        mom = mom_vals[i-10] if i >= 10 else 0
        market = detect_market(prices[:i+1])
        
        if position is None:
            if market == 'TREND_UP' and rsi < cfg_long['oversold']:
                position = {'entry': prices[i], 'type': 'LONG', 'cfg': cfg_long}
            elif market == 'TREND_DOWN' and rsi > cfg_short['oversold']:
                position = {'entry': prices[i], 'type': 'SHORT', 'cfg': cfg_short}
            elif market == 'RANGE':
                if rsi < RANGE_LONG['oversold']:
                    position = {'entry': prices[i], 'type': 'LONG', 'cfg': RANGE_LONG}
                elif rsi > RANGE_SHORT['oversold']:
                    position = {'entry': prices[i], 'type': 'SHORT', 'cfg': RANGE_SHORT}
        else:
            cfg = position['cfg']
            if position['type'] == 'LONG':
                pnl = (prices[i] - position['entry']) / position['entry']
            else:
                pnl = (position['entry'] - prices[i]) / position['entry']
            
            if pnl <= -cfg['stop'] or pnl >= cfg['take']:
                if pnl > 0:
                    wins += 1
                    if position['type'] == 'LONG':
                        long_wins += 1
                        long_ret += pnl
                    else:
                        short_wins += 1
                        short_ret += pnl
                else:
                    losses += 1
                    if position['type'] == 'LONG':
                        long_losses += 1
                    else:
                        short_losses += 1
                total_return += pnl
                position = None
    
    if position:
        cfg = position['cfg']
        if position['type'] == 'LONG':
            pnl = (prices[-1] - position['entry']) / position['entry']
        else:
            pnl = (position['entry'] - prices[-1]) / position['entry']
        total_return += pnl
        if pnl > 0: wins += 1
        else: losses += 1
    
    total = wins + losses
    if total == 0: return None
    
    return {
        'coin': coin, 'trades': total, 'wins': wins, 'losses': losses,
        'win_rate': wins/total*100, 'total_return': total_return*100,
        'long_trades': long_wins + long_losses, 'long_wins': long_wins, 'long_ret': long_ret*100,
        'short_trades': short_wins + short_losses, 'short_wins': short_wins, 'short_ret': short_ret*100,
        'is_meme': is_meme
    }

def main():
    print("=" * 90)
    print("G25.3 30天回测 - 主流币 vs Meme币")
    print("=" * 90)
    
    major_results = []
    meme_results = []
    
    print("\n【主流币回测】")
    print(f"{'币种':10} {'交易':>6} {'做多胜':>8} {'做空胜':>8} {'胜率':>8} {'总收益':>10} {'做多收益':>10} {'做空收益':>10}")
    print("-" * 85)
    
    for coin in MAJOR_COINS:
        r = backtest_coin(coin, is_meme=False)
        if r:
            major_results.append(r)
            lw = f"{r['long_wins']}/{r['long_trades']}" if r['long_trades'] > 0 else '-'
            sw = f"{r['short_wins']}/{r['short_trades']}" if r['short_trades'] > 0 else '-'
            e = '🟢' if r['total_return'] > 0 else '🔴'
            print(f"{e}{coin:9} {r['trades']:>6} {lw:>10} {sw:>10} {r['win_rate']:>7.1f}% {r['total_return']:>+9.1f}% {r['long_ret']:>+9.1f}% {r['short_ret']:>+9.1f}%")
    
    print("\n【Meme币回测】")
    print(f"{'币种':15} {'交易':>6} {'做多胜':>8} {'做空胜':>8} {'胜率':>8} {'总收益':>10} {'做多收益':>10} {'做空收益':>10}")
    print("-" * 90)
    
    for coin in sorted(set(MEME_COINS)):
        r = backtest_coin(coin, is_meme=True)
        if r:
            meme_results.append(r)
            lw = f"{r['long_wins']}/{r['long_trades']}" if r['long_trades'] > 0 else '-'
            sw = f"{r['short_wins']}/{r['short_trades']}" if r['short_trades'] > 0 else '-'
            e = '🟢' if r['total_return'] > 0 else '🔴'
            print(f"{e}{coin:14} {r['trades']:>6} {lw:>10} {sw:>10} {r['win_rate']:>7.1f}% {r['total_return']:>+9.1f}% {r['long_ret']:>+9.1f}% {r['short_ret']:>+9.1f}%")
    
    print("\n" + "=" * 90)
    print("【汇总】")
    print("=" * 90)
    
    if major_results:
        mw = sum(r['wins'] for r in major_results)
        mt = sum(r['trades'] for r in major_results)
        mr = sum(r['total_return'] for r in major_results) / len(major_results)
        mwr = mw/mt*100 if mt > 0 else 0
        m_lr = sum(r['long_ret'] for r in major_results) / len(major_results)
        m_sr = sum(r['short_ret'] for r in major_results) / len(major_results)
        print(f"\n📊 主流币: {len(major_results)}个币, {mt}笔交易, 胜率{mwr:.1f}%")
        print(f"   总收益: {mr:+.1f}% | 做多收益: {m_lr:+.1f}% | 做空收益: {m_sr:+.1f}%")
    
    if meme_results:
        kw = sum(r['wins'] for r in meme_results)
        kt = sum(r['trades'] for r in meme_results)
        kr = sum(r['total_return'] for r in meme_results) / len(meme_results)
        kwr = kw/kt*100 if kt > 0 else 0
        k_lr = sum(r['long_ret'] for r in meme_results) / len(meme_results)
        k_sr = sum(r['short_ret'] for r in meme_results) / len(meme_results)
        print(f"\n🔥 Meme币: {len(meme_results)}个币, {kt}笔交易, 胜率{kwr:.1f}%")
        print(f"   总收益: {kr:+.1f}% | 做多收益: {k_lr:+.1f}% | 做空收益: {k_sr:+.1f}%")
    
    print("\n" + "=" * 90)

if __name__ == '__main__':
    main()
