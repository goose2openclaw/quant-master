#!/usr/bin/env python3
"""G16 激进参数测试"""
import requests, numpy as np, time

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    r = requests.get(url, proxies=PROXIES, timeout=15)
    return [{'close':float(k[4])} for k in r.json()]

def calc_rsi(prices):
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-7:])
    avg_loss = np.mean(loss[-7:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 50

def calc_bb(closes):
    std = np.std(closes[-20:])
    mean = np.mean(closes[-20:])
    upper, lower = mean + 2*std, mean - 2*std
    pos = (closes[-1] - lower) / (upper - lower) * 100 if upper > lower else 50
    ratio = std / mean * 100 if mean > 0 else 0
    return pos, ratio

def backtest(params, data):
    cfg = params
    valid = [c for c in COINS if c in data]
    min_d = min(len(data[c]) for c in valid)
    capital = 1000
    pos, entry = {c:0 for c in valid}, {c:0 for c in valid}
    trades = wins = losses = 0
    
    for d in range(30, min_d):  # 从30天前开始
        for c in valid:
            closes = [data[c][i]['close'] for i in range(max(0,d-30),d+1)]
            if len(closes) < 30: continue
            rsi = calc_rsi(closes)
            bb_pos, ratio = calc_bb(closes)
            
            if pos[c] == 0 and ratio < 0.25:  # 放宽到0.25
                if rsi < cfg['rsi_buy'] and bb_pos < cfg['bb_buy']:
                    pos[c] = 1; entry[c] = closes[-1]; trades += 1
                elif rsi > cfg['rsi_sell'] and bb_pos >= cfg['bb_sell']:
                    pos[c] = -1; entry[c] = closes[-1]; trades += 1
            elif pos[c] != 0:
                pct = (closes[-1] - entry[c]) / entry[c] if pos[c] == 1 else (entry[c] - closes[-1]) / entry[c]
                if pct >= cfg['tp'] or pct <= -cfg['sl']:
                    if pct > 0: wins += 1
                    else: losses += 1
                    capital *= (1 + cfg['pos'] * pct * cfg['lev'])
                    pos[c] = 0
    t = wins + losses
    return {'return': (capital-1000)/1000*100, 'win': wins/t*100 if t>0 else 0, 'trades': t, 'wins': wins, 'losses': losses}

# 激进参数配置
AGGRESSIVE = {
    '激进A': {'rsi_buy': 20, 'rsi_sell': 80, 'bb_buy': 15, 'bb_sell': 85, 'tp': 0.20, 'sl': 0.08, 'pos': 0.50, 'lev': 10},
    '激进B': {'rsi_buy': 25, 'rsi_sell': 75, 'bb_buy': 20, 'bb_sell': 80, 'tp': 0.18, 'sl': 0.06, 'pos': 0.45, 'lev': 8},
    '激进C': {'rsi_buy': 30, 'rsi_sell': 70, 'bb_buy': 25, 'bb_sell': 75, 'tp': 0.15, 'sl': 0.05, 'pos': 0.40, 'lev': 7},
    '超激进': {'rsi_buy': 35, 'rsi_sell': 65, 'bb_buy': 30, 'bb_sell': 70, 'tp': 0.12, 'sl': 0.04, 'pos': 0.35, 'lev': 5},
}

print("获取数据...")
data = {c: get_klines(f'{c}USDT')[-720:] for c in COINS}
print(f"数据: {len(data['BTC'])}条")

print("\n" + "=" * 70)
print("G16 激进参数回测 (目标184%+)")
print("=" * 70)
print(f"{'配置':<12} {'RSI买':>5} {'RSI卖':>5} {'TP':>6} {'SL':>5} {'仓位':>6} {'杠杆':>4} {'收益':>10} {'胜率':>7} {'交易':>5}")
print("-" * 70)

for name, cfg in AGGRESSIVE.items():
    r = backtest(cfg, data)
    print(f"{name:<12} {cfg['rsi_buy']:>5} {cfg['rsi_sell']:>5} {cfg['tp']*100:>5.1f}% {cfg['sl']*100:>4.1f}% {cfg['pos']*100:>5.0f}% {cfg['lev']:>4}x {r['return']:>+10.2f}% {r['win']:>6.1f}% {r['trades']:>5}")

print("=" * 70)
