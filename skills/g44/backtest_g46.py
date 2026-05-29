#!/usr/bin/env python3
"""
G46 回测 - 30天全面测试
"""
import json, time, urllib.request, hmac, hashlib, math
from collections import defaultdict

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}

MAINSTREAM = ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB']
MEME = ['DOGE','SHIB','PEPE','BONK','BOME']

def calc_rsi(closes, period=14):
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains[-period:])/period if gains else 0.001
    avg_loss = sum(losses[-period:])/period if losses else 0.001
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    return 100 - (100/(1+rs))

def calc_stoch_rsi(closes, period=14):
    rsi = calc_rsi(closes, period)
    if rsi < 20: return 1.0
    elif rsi > 80: return -1.0
    return 0

def calc_bollinger_bands(closes, period=20, std_dev=2):
    if len(closes) < period: return 0, 0, 0, 0.5
    ma = sum(closes[-period:])/period
    variance = sum((c - ma)**2 for c in closes[-period:])/period
    std = math.sqrt(variance)
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    position = (closes[-1] - lower)/(upper - lower) if upper != lower else 0.5
    return upper, ma, lower, position

def calc_macd(closes, fast=12, slow=26):
    if len(closes) < slow: return 0, 0, 0
    ema_fast = sum(closes[-fast:])/fast
    ema_slow = sum(closes[-slow:])/slow
    macd_line = ema_fast - ema_slow
    signal_line = macd_line * 0.9
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def detect_market(closes, volumes):
    if len(closes) < 50: return 'range', 0.5
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    rsi = calc_rsi(closes)
    range_strength = 1 - min(abs(trend) * 10, 1)
    if bb_pos < 0.2 or bb_pos > 0.8: range_strength *= 0.8
    if rsi < 30 or rsi > 70: range_strength *= 0.7
    range_conf = min(range_strength, 1.0)
    if trend > 0.03: return 'trend', range_conf
    elif trend < -0.03: return 'downtrend', range_conf
    elif range_conf > 0.6: return 'range', range_conf
    return 'range', 0.5

def calc_signal_g46(closes, highs, lows, volumes, market, polymarket=0):
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    rsi6 = calc_rsi(closes, 6)
    rsi14 = calc_rsi(closes, 14)
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    macd, signal_macd, histogram = calc_macd(closes)
    macd_norm = histogram / closes[-1] if closes[-1] > 0 else 0
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum_short = sum(returns[-3:])/3 if len(returns) >= 3 else 0
    momentum_mid = sum(returns[-7:])/7 if len(returns) >= 7 else 0
    
    if market == 'range':
        bb_deviation = (closes[-1] - bb_ma) / bb_ma if bb_ma > 0 else 0
        bb_mean_rev = -bb_deviation * 20 if bb_deviation < 0 else -bb_deviation * 15
        
        grid_signal = 0
        if bb_pos < 0.2: grid_signal = (0.2 - bb_pos) * 10 * 1.5
        elif bb_pos > 0.8: grid_signal = -(bb_pos - 0.8) * 10 * 1.5
        
        rsi_signal = 0
        if rsi6 < 25 and rsi14 < 35: rsi_signal = 1.5
        elif rsi6 > 75 and rsi14 > 65: rsi_signal = -1.5
        elif rsi6 < 35: rsi_signal = (35 - rsi6) / 35 * 1.0
        elif rsi6 > 65: rsi_signal = -(rsi6 - 65) / 35 * 1.0
        
        stoch_rsi = calc_stoch_rsi(closes, 14)
        
        macd_signal = 0
        if histogram < -0.0005 and closes[-1] < closes[-2]: macd_signal = 1.0
        elif histogram > 0.0005 and closes[-1] > closes[-2]: macd_signal = -1.0
        elif histogram < 0 and histogram > -0.0002: macd_signal = 0.5
        elif histogram > 0 and histogram < 0.0002: macd_signal = -0.5
        
        short_rev = -momentum_short * 20 if abs(momentum_short) > 0.005 else 0
        mid_trend = momentum_mid * 5
        
        vol_confirm = 0
        if vol_ratio > 1.5:
            if rsi14 < 40: vol_confirm = 0.8
            elif rsi14 > 60: vol_confirm = -0.8
        
        bb_squeeze = 0
        bb_width = (bb_upper - bb_ma)/bb_ma if bb_ma > 0 else 0
        if bb_width < 0.02:
            if closes[-1] > bb_upper: bb_squeeze = 1.2
            elif closes[-1] < bb_lower: bb_squeeze = -1.2
        
        final = (
            bb_mean_rev * 0.20 +
            grid_signal * 0.15 +
            rsi_signal * 0.15 +
            stoch_rsi * 0.10 +
            macd_signal * 0.10 +
            short_rev * 0.08 +
            mid_trend * 0.05 +
            vol_confirm * 0.05 +
            bb_squeeze * 0.07 +
            polymarket * 0.30
        )
    else:
        final = trend * 20 + momentum_short * 80 + polymarket * 0.30
    return final

def get_klines(sym, limit=100):
    for retry in range(3):
        try:
            url = f'https://api.binance.com/api/v3/klines?symbol={sym}USDT&interval=15m&limit={limit}'
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            data = json.loads(opener.open(urllib.request.Request(url), timeout=20).read().decode())
            return data if data and len(data) >= 100 else []
        except: time.sleep(1)
    return []

def backtest_coin(sym):
    print(f'  {sym}...', end=' ', flush=True)
    balance = 100.0
    trades = wins = 0
    market_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0})
    data = get_klines(sym, 2880)
    if not data or len(data) < 100: print('失败'); return None
    closes = [float(k[4]) for k in data]
    volumes = [float(k[5]) for k in data]
    highs = [float(k[2]) for k in data]
    lows = [float(k[3]) for k in data]
    pm = POLYMARKET.get(sym, 0)
    position = None
    for i in range(50, len(closes)-1):
        market, _ = detect_market(closes[:i], volumes[:i])
        signal = calc_signal_g46(closes[:i+1], highs[:i+1], lows[:i+1], volumes[:i+1], market, pm)
        if not position and signal > 0.015:
            position = closes[i+1]
            trades += 1
        elif position and (signal < -0.015 or closes[i+1] < position * 0.97):
            ret = (closes[i+1] - position) / position * 100
            market_stats[market]['trades'] += 1
            market_stats[market]['pnl'] += ret
            if ret > 0: wins += 1; market_stats[market]['wins'] += 1
            balance *= (1 + (closes[i+1] - position) / position)
            position = None
    if position:
        ret = (closes[-1] - position) / position * 100
        market_stats['range']['trades'] += 1
        market_stats['range']['pnl'] += ret
    wr = wins/trades*100 if trades > 0 else 0
    total_ret = (balance - 100) * 100
    print(f'收益:{total_ret:.1f}% 胜率:{wr:.1f}% 交易:{trades}')
    return {'symbol': sym, 'total_return': total_ret, 'win_rate': wr, 'trades': trades, 'stats': dict(market_stats)}

def main():
    print('='*70)
    print('G46 30天回测')
    print('='*70)
    print('\n[主流币]')
    mr = [r for r in [backtest_coin(s) for s in MAINSTREAM] if r]
    print('\n[Meme币]')
    mrer = [r for r in [backtest_coin(s) for s in MEME] if r]

    print('\n' + '='*70)
    print('结果汇总')
    print('='*70)
    print(f"\n{'币种':<8} {'30天收益':>10} {'胜率':>8} {'交易':>6} {'趋势收益':>10} {'震荡收益':>10}")
    print('-'*60)
    for r in mr:
        ts = r['stats'].get('trend',{}).get('pnl',0)
        rs = r['stats'].get('range',{}).get('pnl',0)
        print(f"{r['symbol']:<8} {r['total_return']:>9.1f}% {r['win_rate']:>7.1f}% {r['trades']:>6} {ts:>9.1f}% {rs:>9.1f}%")
    print()
    for r in mrer:
        ts = r['stats'].get('trend',{}).get('pnl',0)
        rs = r['stats'].get('range',{}).get('pnl',0)
        print(f"{r['symbol']:<8} {r['total_return']:>9.1f}% {r['win_rate']:>7.1f}% {r['trades']:>6} {ts:>9.1f}% {rs:>9.1f}%")

    m_trend = sum([r['stats'].get('trend',{}).get('pnl',0) for r in mr])
    m_range = sum([r['stats'].get('range',{}).get('pnl',0) for r in mr])
    me_trend = sum([r['stats'].get('trend',{}).get('pnl',0) for r in mrer])
    me_range = sum([r['stats'].get('range',{}).get('pnl',0) for r in mrer])

    print('\n' + '='*70)
    print('收益矩阵')
    print('='*70)
    print(f"{'':>12} {'趋势市场':>12} {'震荡市场':>12}")
    print(f"{'主流币':<12} {m_trend:>11.1f}% {m_range:>11.1f}%")
    print(f"{'Meme币':<12} {me_trend:>11.1f}% {me_range:>11.1f}%")

    print('\n' + '='*70)
    print('7天价格预测')
    print('='*70)
    for sym in ['BTC','ETH','SOL','DOGE']:
        try:
            url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT'
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            price = float(json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())['price'])
            data = get_klines(sym, 168)
            if data and len(data) > 50:
                closes = [float(k[4]) for k in data]
                returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
                avg_r = sum(returns)/len(returns) if returns else 0
                pred = avg_r * 7 * 100
                d = '📈' if pred > 0 else '📉'
                print(f'{sym}: ${price:.2f} | 7天: {d} {pred:+.2f}%')
        except: pass
    print('='*70)

if __name__ == '__main__': main()
