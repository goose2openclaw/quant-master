#!/usr/bin/env python3
"""G16 30天回测"""
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
    
    for d in range(30, min_d):
        for c in valid:
            closes = [data[c][i]['close'] for i in range(max(0,d-30),d+1)]
            if len(closes) < 30: continue
            rsi = calc_rsi(closes)
            bb_pos, ratio = calc_bb(closes)
            
            if pos[c] == 0 and ratio < 0.35:
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
    return {'return': (capital-1000)/1000*100, 'win': wins/t*100 if t>0 else 0, 'trades': t}

# G16配置
CONFIGS = {
    'G16-激进': {'rsi_buy': 25, 'rsi_sell': 75, 'bb_buy': 20, 'bb_sell': 80, 'tp': 0.18, 'sl': 0.06, 'pos': 0.45, 'lev': 8},
    'G16-标准': {'rsi_buy': 35, 'rsi_sell': 65, 'bb_buy': 30, 'bb_sell': 70, 'tp': 0.12, 'sl': 0.04, 'pos': 0.35, 'lev': 5},
    'G16-保守': {'rsi_buy': 40, 'rsi_sell': 60, 'bb_buy': 35, 'bb_sell': 65, 'tp': 0.08, 'sl': 0.03, 'pos': 0.30, 'lev': 3},
    'G16-网格': {'rsi_buy': 45, 'rsi_sell': 55, 'bb_buy': 40, 'bb_sell': 60, 'tp': 0.05, 'sl': 0.02, 'pos': 0.25, 'lev': 3},
}

print("获取数据...")
data = {c: get_klines(f'{c}USDT')[-720:] for c in COINS}
print(f"数据: {len(data['BTC'])}条")

print("\n" + "=" * 75)
print("G16 30天回测数据矩阵 (720小时)")
print("=" * 75)
print(f"{'配置':<12} {'RSI买':>5} {'RSI卖':>5} {'TP':>6} {'SL':>5} {'仓位':>6} {'杠杆':>4} {'收益':>10} {'胜率':>7} {'交易':>5}")
print("-" * 75)

results = []
for name, cfg in CONFIGS.items():
    r = backtest(cfg, data)
    results.append((name, cfg, r))
    print(f"{name:<12} {cfg['rsi_buy']:>5} {cfg['rsi_sell']:>5} {cfg['tp']*100:>5.1f}% {cfg['sl']*100:>4.1f}% {cfg['pos']*100:>5.0f}% {cfg['lev']:>4}x {r['return']:>+10.2f}% {r['win']:>6.1f}% {r['trades']:>5}")

print("=" * 75)

# 最佳配置
best = max(results, key=lambda x: x[2]['return'])
print(f"\n🏆 最佳: {best[0]}")
print(f"   收益: {best[2]['return']:+.2f}% | 胜率: {best[2]['win']:.1f}% | 交易: {best[2]['trades']}次")
print(f"   参数: RSI {best[1]['rsi_buy']}/{best[1]['rsi_sell']} TP {best[1]['tp']*100:.0f}% SL {best[1]['sl']*100:.0f}%")
