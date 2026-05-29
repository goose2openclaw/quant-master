#!/usr/bin/env python3
"""
G44 v4.5 回测 - 30天
====================
测试: 主流币 + Meme币 在 趋势市场 + 震荡市场
"""
import json, time, urllib.request, hmac, hashlib, math
from datetime import datetime, timedelta
from collections import defaultdict

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'

POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}

MAINSTREAM = ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB']
MEME = ['DOGE','SHIB','PEPE','BONK','BOME','NEIRO']

def api_signed(endpoint, params=None, method='GET'):
    ts = int(time.time() * 1000)
    base = {'timestamp': ts, 'recvWindow': 5000}
    if params: base.update(params)
    q = '&'.join('{}={}'.format(k, v) for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com{}?{}&signature={}'.format(endpoint, q, sig)
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=15).read().decode())

def get_klines(sym, interval='15m', limit=100):
    for retry in range(3):
        try:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=' + interval + '&limit=' + str(limit)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            data = json.loads(opener.open(urllib.request.Request(url), timeout=15).read().decode())
            return data if data and len(data) >= 50 else []
        except: time.sleep(1)
    return []

def calc_rsi(closes, period=14):
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains[-period:])/period if gains else 0.001
    avg_loss = sum(losses[-period:])/period if losses else 0.001
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    return 100 - (100/(1+rs))

def calc_macd(closes, fast=12, slow=26):
    if len(closes) < slow: return 0, 0
    ema_fast = sum(closes[-fast:])/fast
    ema_slow = sum(closes[-slow:])/slow
    macd_line = ema_fast - ema_slow
    return macd_line, macd_line * 0.9

def calc_bollinger_bands(closes, period=20, std_dev=2):
    if len(closes) < period: return 0, 0, 0
    ma = sum(closes[-period:])/period
    variance = sum((c - ma)**2 for c in closes[-period:])/period
    std = math.sqrt(variance)
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    position = (closes[-1] - lower)/(upper - lower) if upper != lower else 0.5
    return upper, ma, lower, position

def detect_market(closes, volumes):
    if len(closes) < 50: return 'range', 0.5
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    vol = sum(abs(r) for r in returns[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    rsi = calc_rsi(closes)
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    range_strength = 1 - min(abs(trend) * 10, 1)
    if bb_pos < 0.2 or bb_pos > 0.8: range_strength *= 0.8
    if rsi < 30 or rsi > 70: range_strength *= 0.7
    range_conf = min(range_strength, 1.0)
    if trend > 0.03: return 'trend', range_conf
    elif trend < -0.03: return 'downtrend', range_conf
    elif range_conf > 0.6: return 'range', range_conf
    return 'range', 0.5

def calc_signal_v45(closes, highs, lows, volumes, market, polymarket=0):
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
    rsi6 = calc_rsi(closes, 6)
    rsi14 = calc_rsi(closes, 14)
    macd, signal_macd = calc_macd(closes)
    histogram = macd - signal_macd
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
    momentum_short = sum(returns[-3:])/3 if len(returns) >= 3 else 0
    atr = sum([max(highs[i+1]-lows[i+1], abs(highs[i+1]-closes[i]), abs(lows[i+1]-closes[i])) for i in range(len(closes)-1)])/14 if len(closes) > 14 else 0
    if market == 'range':
        bb_mean_rev = -((closes[-1] - bb_ma)/bb_ma * 20) if bb_ma > 0 else 0
        rsi_signal = (30 - rsi14) / 30 * 1.5 if rsi14 < 30 else -(rsi14 - 70) / 30 * 1.5 if rsi14 > 70 else 0
        macd_rev = 0.8 if histogram < 0 and histogram > -0.001 else -0.8 if histogram > 0 and histogram < 0.001 else 0
        short_rev = -momentum_short * 15 if abs(momentum_short) > 0.01 else 0
        range_pos = bb_pos
        range_signal = (0.25 - range_pos) * 4 * 1.2 if range_pos < 0.25 else -(range_pos - 0.75) * 4 * 1.2 if range_pos > 0.75 else 0
        final = (bb_mean_rev * 0.20 + rsi_signal * 0.15 + macd_rev * 0.10 + short_rev * 0.10 + range_signal * 0.05 + trend * 5 * 0.08 + polymarket * 0.35)
    elif market == 'trend':
        final = trend * 15 * 0.35 + momentum * 100 * 0.20 + (vol_ratio - 1) * 1.5 * 0.15 + histogram/closes[-1]*30 * 0.15 + polymarket * 0.35
    else:
        final = trend * 12 + polymarket * 0.35
    return final

def backtest_coin(sym, days=30):
    print(f"  回测 {sym}...", end=" ", flush=True)
    initial_balance = 100
    balance = initial_balance
    trades = 0
    wins = 0
    losses = 0
    pnl = 0
    market_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0})
    
    for retry in range(3):
        try:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=15m&limit=2880'
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            data = json.loads(opener.open(urllib.request.Request(url), timeout=20).read().decode())
            if not data or len(data) < 100: time.sleep(2); continue
            break
        except: time.sleep(2)
    else: 
        print("获取失败"); return None
    
    closes = [float(k[4]) for k in data]
    volumes = [float(k[5]) for k in data]
    highs = [float(k[2]) for k in data]
    lows = [float(k[3]) for k in data]
    pm = POLYMARKET.get(sym, 0)
    
    positions = []
    buy_price = 0
    BUY_T, SELL_T = 0.025, -0.025
    
    for i in range(50, len(closes)-1):
        market, _ = detect_market(closes[:i], volumes[:i])
        signal = calc_signal_v45(closes[:i+1], highs[:i+1], lows[:i+1], volumes[:i+1], market, pm)
        
        if not positions and signal > BUY_T:
            buy_price = closes[i+1]
            positions.append({'price': buy_price, 'entry': i})
            trades += 1
        elif positions and (signal < SELL_T or closes[i+1] < buy_price * 0.97):
            sell_price = closes[i+1]
            pnl += (sell_price - buy_price) / buy_price
            ret = (sell_price - buy_price) / buy_price * 100
            if ret > 0: wins += 1
            else: losses += 1
            market_stats[market]['trades'] += 1
            if ret > 0: market_stats[market]['wins'] += 1
            else: market_stats[market]['losses'] += 1
            market_stats[market]['pnl'] += ret
            balance *= (1 + (sell_price - buy_price) / buy_price)
            positions = []
    
    if positions:
        last_price = closes[-1]
        pnl += (last_price - buy_price) / buy_price
        ret = (last_price - buy_price) / buy_price * 100
        if ret > 0: wins += 1
        else: losses += 1
    
    win_rate = wins / trades * 100 if trades > 0 else 0
    total_return = (balance - initial_balance) * 100
    
    print(f"收益:{total_return:.1f}% 胜率:{win_rate:.1f}% 交易:{trades}")
    
    return {
        'symbol': sym,
        'total_return': total_return,
        'win_rate': win_rate,
        'trades': trades,
        'wins': wins,
        'losses': losses,
        'market_stats': dict(market_stats)
    }

def main():
    print("=" * 70)
    print("G44 v4.5 回测 - 30天")
    print("=" * 70)
    
    print("\n[主流币回测]")
    main_results = []
    for sym in MAINSTREAM:
        r = backtest_coin(sym, 30)
        if r: main_results.append(r)
    
    print("\n[Meme币回测]")
    meme_results = []
    for sym in MEME:
        r = backtest_coin(sym, 30)
        if r: meme_results.append(r)
    
    print("\n" + "=" * 70)
    print("回测结果汇总")
    print("=" * 70)
    
    print("\n【主流币】")
    print(f"{'币种':<8} {'30天收益':>10} {'胜率':>8} {'交易数':>8} {'趋势胜率':>10} {'震荡胜率':>10}")
    print("-" * 60)
    for r in main_results:
        m = r['market_stats']
        trend_wr = m['trend']['wins']/m['trend']['trades']*100 if m['trend']['trades'] > 0 else 0
        range_wr = m['range']['wins']/m['range']['trades']*100 if m['range']['trades'] > 0 else 0
        print(f"{r['symbol']:<8} {r['total_return']:>9.1f}% {r['win_rate']:>7.1f}% {r['trades']:>8} {trend_wr:>9.1f}% {range_wr:>9.1f}%")
    
    main_trend_pnl = sum([r['market_stats']['trend']['pnl'] for r in main_results])
    main_range_pnl = sum([r['market_stats']['range']['pnl'] for r in main_results])
    print(f"\n主流币趋势市场总收益: {main_trend_pnl:.1f}%")
    print(f"主流币震荡市场总收益: {main_range_pnl:.1f}%")
    
    print("\n【Meme币】")
    print(f"{'币种':<8} {'30天收益':>10} {'胜率':>8} {'交易数':>8} {'趋势胜率':>10} {'震荡胜率':>10}")
    print("-" * 60)
    for r in meme_results:
        m = r['market_stats']
        trend_wr = m['trend']['wins']/m['trend']['trades']*100 if m['trend']['trades'] > 0 else 0
        range_wr = m['range']['wins']/m['range']['trades']*100 if m['range']['trades'] > 0 else 0
        print(f"{r['symbol']:<8} {r['total_return']:>9.1f}% {r['win_rate']:>7.1f}% {r['trades']:>8} {trend_wr:>9.1f}% {range_wr:>9.1f}%")
    
    meme_trend_pnl = sum([r['market_stats']['trend']['pnl'] for r in meme_results])
    meme_range_pnl = sum([r['market_stats']['range']['pnl'] for r in meme_results])
    print(f"\nMeme币趋势市场总收益: {meme_trend_pnl:.1f}%")
    print(f"Meme币震荡市场总收益: {meme_range_pnl:.1f}%")
    
    print("\n" + "=" * 70)
    print("7天价格预测")
    print("=" * 70)
    for sym in ['BTC','ETH','SOL','DOGE']:
        price = 0
        for retry in range(3):
            try:
                url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT'
                proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
                opener = urllib.request.build_opener(proxy_handler)
                price = float(json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())['price'])
                break
            except: time.sleep(1)
        if price:
            data = get_klines(sym, '1h', 168)
            if data and len(data) > 50:
                closes = [float(k[4]) for k in data]
                returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
                avg_return = sum(returns[-168:])/168 if len(returns) >= 168 else 0
                pred_7d = avg_return * 7 * 100
                direction = "📈" if pred_7d > 0 else "📉"
                print(f"{sym}: 当前${price:.2f} | 7天预测: {direction} {pred_7d:+.2f}%")
    
    print("\n" + "=" * 70)

if __name__ == '__main__': main()
