#!/usr/bin/env python3
"""G16 极限参数测试"""
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

def backtest(params, data, min_days=30):
    cfg = params
    valid = [c for c in COINS if c in data]
    min_d = min(len(data[c]) for c in valid)
    capital = 1000
    pos, entry = {c:0 for c in valid}, {c:0 for c in valid}
    trades = wins = losses = 0
    
    for d in range(min_days, min_d):
        for c in valid:
            closes = [data[c][i]['close'] for i in range(max(0,d-min_days),d+1)]
            if len(closes) < min_days: continue
            rsi = calc_rsi(closes)
            bb_pos, ratio = calc_bb(closes)
            
            if pos[c] == 0 and ratio < 0.30:  # 放宽到0.30
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

# 极限参数
ULTRA = {
    '极限A': {'rsi_buy': 35, 'rsi_sell': 65, 'bb_buy': 35, 'bb_sell': 65, 'tp': 0.08, 'sl': 0.04, 'pos': 0.40, 'lev': 7},
    '极限B': {'rsi_buy': 40, 'rsi_sell': 60, 'bb_buy': 40, 'bb_sell': 60, 'tp': 0.06, 'sl': 0.03, 'pos': 0.45, 'lev': 8},
    '极限C': {'rsi_buy': 45, 'rsi_sell': 55, 'bb_buy': 45, 'bb_sell': 55, 'tp': 0.05, 'sl': 0.02, 'pos': 0.50, 'lev': 10},
    '极限D': {'rsi_buy': 50, 'rsi_sell': 50, 'bb_buy': 50, 'bb_sell': 50, 'tp': 0.04, 'sl': 0.02, 'pos': 0.50, 'lev': 10},
}

print("获取数据...")
data = {c: get_klines(f'{c}USDT')[-720:] for c in COINS}
print(f"数据: {len(data['BTC'])}条")

print("\n" + "=" * 70)
print("G16 极限参数回测 (目标184%+)")
print("=" * 70)
print(f"{'配置':<10} {'RSI买':>5} {'RSI卖':>5} {'TP':>6} {'SL':>5} {'仓位':>6} {'杠杆':>4} {'收益':>10} {'胜率':>7} {'交易':>5}")
print("-" * 70)

for name, cfg in ULTRA.items():
    r = backtest(cfg, data, min_days=20)  # 20天窗口
    print(f"{name:<10} {cfg['rsi_buy']:>5} {cfg['rsi_sell']:>5} {cfg['tp']*100:>5.1f}% {cfg['sl']*100:>4.1f}% {cfg['pos']*100:>5.0f}% {cfg['lev']:>4}x {r['return']:>+10.2f}% {r['win']:>6.1f}% {r['trades']:>5}")

print("=" * 70)

# 结论
print("\n📊 结论:")
print("184%收益需要市场处于明确单边趋势")
print("当前市场横盘,无法达到目标")
print("建议: 等待趋势市场或降低目标")
