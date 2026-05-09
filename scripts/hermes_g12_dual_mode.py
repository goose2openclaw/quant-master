#!/usr/bin/env python3
"""
G12 双模式策略
- 严格模式(主): RSI<28+BB<20买入, RSI>70+BB>80卖出
- 趋势模式(副): 动能突破+趋势跟随
"""
import requests, numpy as np, time, json, hmac, hashlib
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

# ========== 配置 ==========
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# 严格模式参数
STRICT = {
    'rsi_buy': 28, 'rsi_sell': 70,
    'bb_buy': 20, 'bb_sell': 80,
    'tp': 0.15, 'sl': 0.05,
    'position': 0.35, 'leverage': 5
}

# 趋势模式参数
TREND = {
    'momentum_th': 5,      # 24h动能阈值
    'rsi_upper': 75,       # RSI上限(追涨时允许RSI更高)
    'rsi_lower': 40,       # RSI下限(超卖买入)
    'tp': 0.10, 'sl': 0.03,
    'position': 0.25, 'leverage': 3
}

# ========== 工具函数 ==========
def get_klines(sym, limit=200):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    r = requests.get(url, proxies=PROXIES, timeout=15)
    return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]

def calc_rsi(prices, period=7):
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 50

def calc_bb_pos(closes, highs, lows, period=20):
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    curr = closes[-1]
    return (curr - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def get_momentum(closes, period=24):
    if len(closes) < period: return 0
    return (closes[-1] - closes[-period]) / closes[-period] * 100

# ========== 严格模式信号 ==========
def strict_signal(rsi, bb):
    if rsi < STRICT['rsi_buy'] and bb < STRICT['bb_buy']:
        return 'LONG'
    if rsi > STRICT['rsi_sell'] and bb > STRICT['bb_sell']:
        return 'SHORT'
    return None

# ========== 趋势模式信号 ==========
def trend_signal(rsi, momentum, bb):
    # 追涨: 高动能 + RSI不是极端
    if momentum > TREND['momentum_th'] and rsi > TREND['rsi_lower'] and rsi < TREND['rsi_upper']:
        return 'LONG'
    # 做空: 负动能 + RSI高位
    if momentum < -TREND['momentum_th'] and rsi > 60:
        return 'SHORT'
    return None

# ========== 回测 ==========
def backtest(mode='both'):
    """回测双模式策略"""
    print("=" * 60)
    print(f"G12 双模式策略回测")
    print("=" * 60)
    
    # 获取数据
    print("\n获取数据...")
    data = {}
    for coin in COINS:
        klines = get_klines(f'{coin}USDT', 500)
        if klines:
            data[coin] = klines
            print(f"  {coin}: {len(klines)}条")
    
    if not data:
        print("数据获取失败")
        return
    
    # 统计
    strict_trades = strict_backtest(data)
    trend_trades = trend_backtest(data)
    combined_trades = combined_backtest(data)
    
    print("\n" + "=" * 60)
    print("回测结果对比:")
    print("=" * 60)
    print(f"{'模式':<15} {'收益':>10} {'胜率':>8} {'交易':>6}")
    print("-" * 60)
    print(f"{'严格模式':<15} {strict_trades['return']:>+10.2f}% {strict_trades['win_rate']:>7.1f}% {strict_trades['trades']:>6}")
    print(f"{'趋势模式':<15} {trend_trades['return']:>+10.2f}% {trend_trades['win_rate']:>7.1f}% {trend_trades['trades']:>6}")
    print(f"{'双模式合并':<15} {combined_trades['return']:>+10.2f}% {combined_trades['win_rate']:>7.1f}% {combined_trades['trades']:>6}")
    print("=" * 60)
    
    return {
        'strict': strict_trades,
        'trend': trend_trades,
        'combined': combined_trades
    }

def strict_backtest(data):
    """严格模式回测"""
    valid = [c for c in COINS if c in data and len(data[c]) > 100]
    min_d = min(len(data[c]) for c in valid)
    
    capital = 1000
    pos = {c: 0 for c in valid}
    entry = {c: 0 for c in valid}
    trades = wins = losses = 0
    
    for d in range(min_d):
        for c in valid:
            closes = [data[c][i]['close'] for i in range(max(0,d-30),d+1)]
            highs = [data[c][i]['high'] for i in range(max(0,d-19),d+1)]
            lows = [data[c][i]['low'] for i in range(max(0,d-19),d+1)]
            if len(closes) < 30: continue
            
            rsi = calc_rsi(closes)
            bb = calc_bb_pos(closes, highs, lows)
            
            if pos[c] == 0:
                sig = strict_signal(rsi, bb)
                if sig == 'LONG':
                    pos[c] = 1; entry[c] = closes[-1]; trades += 1
                elif sig == 'SHORT':
                    pos[c] = -1; entry[c] = closes[-1]; trades += 1
            else:
                pct = (closes[-1] - entry[c]) / entry[c] if pos[c] == 1 else (entry[c] - closes[-1]) / entry[c]
                if pct >= STRICT['tp'] or pct <= -STRICT['sl']:
                    if pct > 0: wins += 1
                    else: losses += 1
                    capital *= (1 + STRICT['position'] * pct * STRICT['leverage'])
                    pos[c] = 0
    
    t = wins + losses
    return {
        'return': (capital - 1000) / 1000 * 100,
        'win_rate': wins / t * 100 if t > 0 else 0,
        'trades': t, 'wins': wins, 'losses': losses
    }

def trend_backtest(data):
    """趋势模式回测"""
    valid = [c for c in COINS if c in data and len(data[c]) > 100]
    min_d = min(len(data[c]) for c in valid)
    
    capital = 1000
    pos = {c: 0 for c in valid}
    entry = {c: 0 for c in valid}
    trades = wins = losses = 0
    
    for d in range(min_d):
        for c in valid:
            closes = [data[c][i]['close'] for i in range(max(0,d-30),d+1)]
            highs = [data[c][i]['high'] for i in range(max(0,d-19),d+1)]
            lows = [data[c][i]['low'] for i in range(max(0,d-19),d+1)]
            if len(closes) < 30: continue
            
            rsi = calc_rsi(closes)
            bb = calc_bb_pos(closes, highs, lows)
            mom = get_momentum(closes)
            
            if pos[c] == 0:
                sig = trend_signal(rsi, mom, bb)
                if sig == 'LONG':
                    pos[c] = 1; entry[c] = closes[-1]; trades += 1
                elif sig == 'SHORT':
                    pos[c] = -1; entry[c] = closes[-1]; trades += 1
            else:
                pct = (closes[-1] - entry[c]) / entry[c] if pos[c] == 1 else (entry[c] - closes[-1]) / entry[c]
                if pct >= TREND['tp'] or pct <= -TREND['sl']:
                    if pct > 0: wins += 1
                    else: losses += 1
                    capital *= (1 + TREND['position'] * pct * TREND['leverage'])
                    pos[c] = 0
    
    t = wins + losses
    return {
        'return': (capital - 1000) / 1000 * 100,
        'win_rate': wins / t * 100 if t > 0 else 0,
        'trades': t, 'wins': wins, 'losses': losses
    }

def combined_backtest(data):
    """双模式合并回测"""
    valid = [c for c in COINS if c in data and len(data[c]) > 100]
    min_d = min(len(data[c]) for c in valid)
    
    capital = 1000
    pos = {c: 0 for c in valid}
    entry = {c: 0 for c in valid}
    mode_used = {c: None for c in valid}
    trades = wins = losses = 0
    
    for d in range(min_d):
        for c in valid:
            closes = [data[c][i]['close'] for i in range(max(0,d-30),d+1)]
            highs = [data[c][i]['high'] for i in range(max(0,d-19),d+1)]
            lows = [data[c][i]['low'] for i in range(max(0,d-19),d+1)]
            if len(closes) < 30: continue
            
            rsi = calc_rsi(closes)
            bb = calc_bb_pos(closes, highs, lows)
            mom = get_momentum(closes)
            
            if pos[c] == 0:
                # 优先严格模式
                sig = strict_signal(rsi, bb)
                if sig:
                    pos[c] = 1 if sig == 'LONG' else -1
                    entry[c] = closes[-1]
                    mode_used[c] = 'strict'
                    trades += 1
                else:
                    # 次选趋势模式
                    sig = trend_signal(rsi, mom, bb)
                    if sig:
                        pos[c] = 1 if sig == 'LONG' else -1
                        entry[c] = closes[-1]
                        mode_used[c] = 'trend'
                        trades += 1
            else:
                # 使用对应模式的止盈止损
                cfg = STRICT if mode_used[c] == 'strict' else TREND
                pct = (closes[-1] - entry[c]) / entry[c] if pos[c] == 1 else (entry[c] - closes[-1]) / entry[c]
                if pct >= cfg['tp'] or pct <= -cfg['sl']:
                    if pct > 0: wins += 1
                    else: losses += 1
                    capital *= (1 + cfg['position'] * pct * cfg['leverage'])
                    pos[c] = 0
    
    t = wins + losses
    return {
        'return': (capital - 1000) / 1000 * 100,
        'win_rate': wins / t * 100 if t > 0 else 0,
        'trades': t, 'wins': wins, 'losses': losses
    }

if __name__ == '__main__':
    backtest()
