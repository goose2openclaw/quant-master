#!/usr/bin/env python3
"""G13 v1.0 多因子策略"""
import requests, numpy as np, time
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

CONFIG = {
    '单边趋势': {'rsi_buy': 28, 'rsi_sell': 70, 'bb_buy': 20, 'tp': 0.15, 'sl': 0.05, 'pos': 0.35, 'lev': 5, 'pos_th': 70},
    '震荡回调': {'rsi_buy': 35, 'rsi_sell': 65, 'bb_buy': 25, 'tp': 0.08, 'sl': 0.04, 'pos': 0.25, 'lev': 3, 'pos_th': 70},
}

def get_klines(sym, limit=720):
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

def calc_bb(closes):
    std = np.std(closes[-20:])
    mean = np.mean(closes[-20:])
    bb_high = mean + 2*std
    bb_low = mean - 2*std
    curr = closes[-1]
    return (curr - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def backtest(state_name, cfg, data):
    valid = [c for c in COINS if c in data]
    min_d = min(len(data[c]) for c in valid)
    capital = 1000
    pos, entry = {c:0 for c in valid}, {c:0 for c in valid}
    trades = wins = losses = 0
    
    for d in range(50, min_d):
        for c in valid:
            closes = [data[c][i]['close'] for i in range(max(0,d-50),d+1)]
            if len(closes) < 50: continue
            rsi = calc_rsi(closes)
            bb = calc_bb(closes)
            bb_now = np.std(closes[-20:]) / np.mean(closes[-20:]) * 100
            bb_hist = np.std(closes) / np.mean(closes) * 100
            ratio = bb_now / bb_hist if bb_hist > 0 else 1
            
            if pos[c] == 0 and ratio < 0.20:
                if rsi < cfg['rsi_buy'] and bb < cfg['bb_buy']:
                    pos[c] = 1; entry[c] = closes[-1]; trades += 1
                elif rsi > cfg['rsi_sell'] and bb >= cfg['pos_th']:
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

print("获取数据...")
data = {c: get_klines(f'{c}USDT')[-720:] for c in COINS}
print(f"数据: {len(data['BTC'])}条")

print("\n" + "=" * 60)
print("G13 30天回测数据矩阵")
print("=" * 60)
print(f"{'配置':<12} {'RSI买':>5} {'RSI卖':>5} {'TP':>6} {'SL':>5} {'仓位':>6} {'杠杆':>4} {'收益':>10} {'胜率':>7} {'交易':>5}")
print("-" * 60)

for name, cfg in CONFIG.items():
    r = backtest(name, cfg, data)
    print(f"{name:<12} {cfg['rsi_buy']:>5} {cfg['rsi_sell']:>5} {cfg['tp']*100:>5.1f}% {cfg['sl']*100:>4.1f}% {cfg['pos']*100:>5.0f}% {cfg['lev']:>4}x {r['return']:>+10.2f}% {r['win']:>6.1f}% {r['trades']:>5}")

print("=" * 60)
