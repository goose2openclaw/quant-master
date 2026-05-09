#!/usr/bin/env python3
"""
G16 Pro v2.0 - 自我学习迭代系统
目标: 月收益184%+
核心: 自适应参数优化, 模式自动切换, 收益最大化
"""
import requests, numpy as np, time, json
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# 目标收益
TARGET_MONTHLY = 184.0  # 月化184%

# ========== 参数搜索空间 ==========
PARAM_GRID = {
    '单边趋势': {
        'rsi_buy': [25, 28, 30],
        'rsi_sell': [68, 70, 72],
        'bb_buy': [15, 20, 25],
        'tp': [0.12, 0.15, 0.18],
        'sl': [0.04, 0.05, 0.06],
        'pos': [0.30, 0.35, 0.40],
        'lev': [5, 7],
    },
    '震荡回调': {
        'rsi_buy': [32, 35, 38],
        'rsi_sell': [62, 65, 68],
        'bb_buy': [25, 28, 30],
        'tp': [0.05, 0.08, 0.10],
        'sl': [0.02, 0.03, 0.04],
        'pos': [0.20, 0.25, 0.30],
        'lev': [3, 5],
    }
}

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

def get_momentum(closes):
    return (closes[-1] - closes[-24]) / closes[-24] * 100 if len(closes) >= 24 else 0

def backtest(params, data):
    """回测单组参数"""
    cfg = params
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
            bb_pos, ratio = calc_bb(closes)
            
            if pos[c] == 0 and ratio < 0.20:
                if rsi < cfg['rsi_buy'] and bb_pos < cfg['bb_buy']:
                    pos[c] = 1; entry[c] = closes[-1]; trades += 1
                elif rsi > cfg['rsi_sell'] and bb_pos >= 70:
                    pos[c] = -1; entry[c] = closes[-1]; trades += 1
            elif pos[c] != 0:
                pct = (closes[-1] - entry[c]) / entry[c] if pos[c] == 1 else (entry[c] - closes[-1]) / entry[c]
                if pct >= cfg['tp'] or pct <= -cfg['sl']:
                    if pct > 0: wins += 1
                    else: losses += 1
                    capital *= (1 + cfg['pos'] * pct * cfg['lev'])
                    pos[c] = 0
    
    t = wins + losses
    return {
        'return': (capital - 1000) / 1000 * 100,
        'win_rate': wins / t * 100 if t > 0 else 0,
        'trades': t,
        'wins': wins,
        'losses': losses
    }

def grid_search(state_name, data):
    """网格搜索最优参数"""
    grid = PARAM_GRID[state_name]
    keys = list(grid.keys())
    values = list(grid.values())
    
    best = None
    best_return = -999
    
    # 简化搜索
    for i in range(len(values[0])):
        params = {keys[j]: values[j][i % len(values[j])] for j in range(len(keys))}
        r = backtest(params, data)
        if r['return'] > best_return and r['trades'] >= 3:
            best_return = r['return']
            best = params.copy()
            best.update(r)
    
    return best

def adaptive_optimize(data):
    """自适应优化"""
    print("=" * 65)
    print("G16 Pro v2.0 - 自我学习迭代系统")
    print("=" * 65)
    
    print("\n📊 获取数据...")
    for c in COINS:
        data[c] = get_klines(f'{c}USDT')[-720:]
    print(f"   数据: {len(data['BTC'])}条")
    
    # 网格搜索
    print("\n🔍 网格搜索最优参数...")
    results = {}
    for state in PARAM_GRID.keys():
        r = grid_search(state, data)
        if r:
            results[state] = r
            print(f"   {state}: 收益{r['return']:+.2f}% 胜率{r['win_rate']:.1f}% 交易{r['trades']}次")
    
    # 选择最优配置
    best_state = max(results, key=lambda x: results[x]['return'])
    best = results[best_state]
    
    print("\n" + "=" * 65)
    print("G16 Pro 30天回测结果 (最优配置)")
    print("=" * 65)
    print(f"最优配置: {best_state}")
    print(f"参数: RSI {best.get('rsi_buy','')}/{best.get('rsi_sell','')} TP {best.get('tp',0)*100:.0f}% SL {best.get('sl',0)*100:.0f}%")
    print(f"收益: {best['return']:+.2f}%")
    print(f"胜率: {best['win_rate']:.1f}%")
    print(f"交易: {best['trades']}次")
    print("=" * 65)
    
    # 检查是否达到目标
    if best['return'] >= TARGET_MONTHLY:
        print(f"✅ 已达成目标! {TARGET_MONTHLY}%+")
    else:
        print(f"⚠️ 未达成目标 {TARGET_MONTHLY}%")
        print(f"   当前: {best['return']:.2f}%")
        print(f"   差距: {TARGET_MONTHLY - best['return']:.2f}%")
    
    return results, best_state, best

if __name__ == '__main__':
    data = {}
    adaptive_optimize(data)
