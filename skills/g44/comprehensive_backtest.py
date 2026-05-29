#!/usr/bin/env python3
"""
G40-G44全部版本 30天综合回测
==============================
比较版本:
- G40: 基础版
- G41: 优化版
- G42: 加强版
- G43: 自主决策版
- G44v4.0-v4.5: 各子版本
"""
import json, time, urllib.request, hmac, hashlib, math
from collections import defaultdict

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}

MAINSTREAM = ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB']
MEME = ['DOGE','SHIB','PEPE','BONK','BOME']

# 版本信号函数
def calc_signal_g40(closes, volumes, market, polymarket=0):
    """G40: 基础版"""
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    momentum = sum([(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))][-10:])/10
    go_pool = (vol_ratio - 1) * 0.5
    go_core = trend * 8
    go_rotate = trend * 0.8
    go_signal = go_core + go_pool + go_rotate
    return go_signal * 0.65 + polymarket * 0.35

def calc_signal_g41(closes, volumes, market, polymarket=0):
    """G41: 优化版"""
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
    go_core = trend * 10
    go_pool = (vol_ratio - 1) * 0.6
    go_rotate = trend * 1.0
    go_ls = momentum * 80
    go_detect = trend50 * 5
    go_signal = go_core*0.15 + go_pool*0.15 + go_rotate*0.12 + go_ls*0.10 + go_detect*0.08
    return go_signal * 0.65 + polymarket * 0.35

def calc_signal_g42(closes, volumes, market, polymarket=0):
    """G42: 加强版"""
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains)/len(gains) if gains else 0
    avg_loss = sum(losses)/len(losses) if losses else 0
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100/(1+rs))
    go_core = trend * 12
    go_pool = (vol_ratio - 1) * 0.7
    go_rotate = trend * 1.2
    go_ls = (rsi - 50) / 50
    go_detect = trend50 * 6
    momentum_sig = momentum * 100
    go_signal = go_core*0.15 + go_pool*0.15 + go_rotate*0.12 + go_ls*0.10 + go_detect*0.08 + momentum_sig*0.08
    return go_signal * 0.65 + polymarket * 0.35

def calc_signal_g43(closes, volumes, market, polymarket=0):
    """G43: 自主决策版"""
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains)/len(gains) if gains else 0
    avg_loss = sum(losses)/len(losses) if losses else 0
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100/(1+rs))
    if market == 'range':
        go_pool = (vol_ratio - 1) * 0.8
        mean_rev = -((closes[-1] - ma20)/ma20 * 15) if ma20 > 0 else 0
        go_rotate = trend * 1.2
    else:
        go_pool = (vol_ratio - 1) * 0.5
        mean_rev = -((closes[-1] - ma20)/ma20 * 8) if ma20 > 0 else 0
        go_rotate = trend * 0.5
    go_core = trend * 12
    go_ls = (rsi - 50) / 50
    go_detect = trend50 * 6
    momentum_sig = momentum * 120
    breakout = 1.5 if closes[-1] > max(closes[-20:-1]) else -0.5 if closes[-1] < min(closes[-20:-1]) else 0
    sentiment = trend * 25 + polymarket * 1.5
    go_signal = (go_core*0.15 + go_pool*0.15 + go_rotate*0.12 + go_ls*0.10 + go_detect*0.08 + momentum_sig*0.08 + mean_rev*0.10 + breakout*0.07 + sentiment*0.07)
    return go_signal * 0.65 + polymarket * 0.35

def calc_signal_g44v44(closes, volumes, market, polymarket=0):
    """G44 v4.4: 修复版"""
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains)/len(gains) if gains else 0
    avg_loss = sum(losses)/len(losses) if losses else 0
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100/(1+rs))
    if market == 'range':
        go_pool = (vol_ratio - 1) * 0.8
        mean_rev = -((closes[-1] - ma20)/ma20 * 15) if ma20 > 0 else 0
        go_rotate = trend * 1.2
    else:
        go_pool = (vol_ratio - 1) * 0.5
        mean_rev = -((closes[-1] - ma20)/ma20 * 8) if ma20 > 0 else 0
        go_rotate = trend * 0.5
    go_core = trend * 12
    go_ls = (rsi - 50) / 50
    go_detect = trend50 * 6
    momentum_sig = momentum * 120
    breakout = 1.5 if closes[-1] > max(closes[-20:-1]) else -0.5 if closes[-1] < min(closes[-20:-1]) else 0
    vol_profile = 1.2 if vol_ratio > 1.5 and closes[-1] > ma20 else 0
    sentiment = trend * 25 + polymarket * 1.5
    go_signal = (go_core*0.15 + go_pool*0.15 + go_rotate*0.12 + go_ls*0.10 + go_detect*0.08 + momentum_sig*0.08 + mean_rev*0.10 + breakout*0.07 + vol_profile*0.08 + sentiment*0.07)
    return go_signal * 0.65 + polymarket * 0.35

def calc_signal_g44v45(closes, highs, lows, volumes, market, polymarket=0):
    """G44 v4.5: 震荡市场增强版"""
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    rsi14 = calc_rsi(closes, 14)
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum_short = sum(returns[-3:])/3 if len(returns) >= 3 else 0
    
    if market == 'range':
        bb_mean_rev = -((closes[-1] - bb_ma)/bb_ma * 20) if bb_ma > 0 else 0
        rsi_signal = (30 - rsi14) / 30 * 1.5 if rsi14 < 30 else -(rsi14 - 70) / 30 * 1.5 if rsi14 > 70 else 0
        short_rev = -momentum_short * 15 if abs(momentum_short) > 0.01 else 0
        range_pos = bb_pos
        range_signal = (0.25 - range_pos) * 4 * 1.2 if range_pos < 0.25 else -(range_pos - 0.75) * 4 * 1.2 if range_pos > 0.75 else 0
        final = (bb_mean_rev * 0.25 + rsi_signal * 0.20 + short_rev * 0.15 + range_signal * 0.10 + polymarket * 0.30)
    else:
        final = trend * 20 + polymarket * 0.30
    return final

def calc_rsi(closes, period=14):
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains[-period:])/period if gains else 0.001
    avg_loss = sum(losses[-period:])/period if losses else 0.001
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    return 100 - (100/(1+rs))

def calc_bollinger_bands(closes, period=20, std_dev=2):
    if len(closes) < period: return 0, 0, 0, 0.5
    ma = sum(closes[-period:])/period
    variance = sum((c - ma)**2 for c in closes[-period:])/period
    std = math.sqrt(variance)
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    position = (closes[-1] - lower)/(upper - lower) if upper != lower else 0.5
    return upper, ma, lower, position

def detect_market(closes, volumes):
    if len(closes) < 50: return 'range'
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    rsi = calc_rsi(closes)
    range_strength = 1 - min(abs(trend) * 10, 1)
    if bb_pos < 0.2 or bb_pos > 0.8: range_strength *= 0.8
    if rsi < 30 or rsi > 70: range_strength *= 0.7
    if trend > 0.03: return 'trend'
    elif trend < -0.03: return 'downtrend'
    elif range_strength > 0.6: return 'range'
    return 'range'

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

def backtest_version(calc_sig_func, version_name, extra_args=None):
    print(f"  {version_name}...", end=' ', flush=True)
    results = []
    for sym in MAINSTREAM + MEME:
        balance = 100.0
        trades = wins = 0
        market_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0})
        data = get_klines(sym, 2880)
        if not data or len(data) < 100: continue
        closes = [float(k[4]) for k in data]
        volumes = [float(k[5]) for k in data]
        highs = [float(k[2]) for k in data]
        lows = [float(k[3]) for k in data]
        pm = POLYMARKET.get(sym, 0)
        position = None
        
        for i in range(50, len(closes)-1):
            market = detect_market(closes[:i], volumes[:i])
            if extra_args:
                signal = calc_sig_func(closes[:i+1], highs[:i+1], lows[:i+1], volumes[:i+1], market, pm)
            else:
                signal = calc_sig_func(closes[:i+1], volumes[:i+1], market, pm)
            
            if not position and signal > 0.025:
                position = closes[i+1]
                trades += 1
            elif position and (signal < -0.025 or closes[i+1] < position * 0.97):
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
        results.append({
            'symbol': sym,
            'total_return': total_ret,
            'win_rate': wr,
            'trades': trades,
            'stats': dict(market_stats)
        })
    
    if not results: return None
    avg_ret = sum(r['total_return'] for r in results) / len(results)
    avg_wr = sum(r['win_rate'] for r in results) / len(results)
    total_trades = sum(r['trades'] for r in results)
    
    m_trend = sum([r['stats'].get('trend',{}).get('pnl',0) for r in results])
    m_range = sum([r['stats'].get('range',{}).get('pnl',0) for r in results])
    mainstream = [r for r in results if r['symbol'] in MAINSTREAM]
    meme = [r for r in results if r['symbol'] in MEME]
    
    ms_trend = sum([r['stats'].get('trend',{}).get('pnl',0) for r in mainstream])
    ms_range = sum([r['stats'].get('range',{}).get('pnl',0) for r in mainstream])
    me_trend = sum([r['stats'].get('trend',{}).get('pnl',0) for r in meme])
    me_range = sum([r['stats'].get('range',{}).get('pnl',0) for r in meme])
    
    print(f"收益:{avg_ret:.1f}% 胜率:{avg_wr:.1f}%")
    return {
        'version': version_name,
        'avg_return': avg_ret,
        'avg_win_rate': avg_wr,
        'total_trades': total_trades,
        'mainstream': {'trend': ms_trend, 'range': ms_range},
        'meme': {'trend': me_trend, 'range': me_range}
    }

def price_prediction():
    print("\n" + "="*70)
    print("7天价格预测")
    print("="*70)
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

def main():
    print("="*70)
    print("G40-G44全部版本 30天综合回测")
    print("="*70)
    
    versions = [
        (calc_signal_g40, "G40基础版", False),
        (calc_signal_g41, "G41优化版", False),
        (calc_signal_g42, "G42加强版", False),
        (calc_signal_g43, "G43自主决策版", False),
        (calc_signal_g44v44, "G44v4.4修复版", False),
        (calc_signal_g44v45, "G44v4.5震荡增强", True),
    ]
    
    all_results = []
    for calc_func, name, extra in versions:
        r = backtest_version(calc_func, name, extra)
        if r: all_results.append(r)
    
    print("\n" + "="*70)
    print("版本比较矩阵")
    print("="*70)
    print(f"\n{'版本':<20} {'平均收益':>10} {'平均胜率':>10} {'交易数':>8}")
    print("-"*50)
    for r in all_results:
        print(f"{r['version']:<20} {r['avg_return']:>9.1f}% {r['avg_win_rate']:>9.1f}% {r['total_trades']:>8}")
    
    print("\n" + "="*70)
    print("市场收益矩阵")
    print("="*70)
    print(f"\n{'版本':<20} {'主流趋势':>10} {'主流震荡':>10} {'Meme趋势':>10} {'Meme震荡':>10}")
    print("-"*65)
    for r in all_results:
        print(f"{r['version']:<20} {r['mainstream']['trend']:>9.1f}% {r['mainstream']['range']:>9.1f}% {r['meme']['trend']:>9.1f}% {r['meme']['range']:>9.1f}%")
    
    price_prediction()
    print("="*70)

if __name__ == '__main__': main()
