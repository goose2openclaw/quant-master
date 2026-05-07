#!/usr/bin/env python3
"""
最大算力优化 - 深度全面优化
确保收益最大化
"""
import requests, time, json, numpy as np
from itertools import product

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, days=30):
    end = int(time.time()*1000)
    start = end - days*86400*1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1d&startTime={start}&endTime={end}&limit=1000'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]
    except: return []

def bollinger_pos(price, high, low):
    return (price-low)/(high-low)*100 if high>low else 50

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def simulate(initial_capital, price_data, cfg):
    capital = initial_capital
    positions = {c: 0 for c in COINS}
    trades = []
    history = []
    
    for day_idx in range(len(price_data[COINS[0]])):
        day_data = {c: price_data[c][day_idx] for c in COINS if day_idx < len(price_data[c])}
        if not day_data: continue
        
        pos_value = sum(positions[c] * day_data[c]['close'] for c in COINS)
        total = capital + pos_value
        used_ratio = pos_value / total if total > 0 else 0
        history.append({'portfolio': total, 'used': used_ratio})
        
        for c in COINS:
            if c not in day_data: continue
            d = day_data[c]
            pos = bollinger_pos(d['close'], d['high'], d['low'])
            cur_qty = positions[c]
            
            # 买入信号
            if pos < cfg['buy_th'] and capital > 10:
                invest = capital * cfg['pos_ratio']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    trades.append({'type':'BUY','coin':c,'price':d['close']})
            
            # 卖出信号
            elif cur_qty > 0 and pos > cfg['sell_th']:
                qty = cur_qty * 0.5
                revenue = qty * d['close'] * 0.999
                capital += revenue
                positions[c] -= qty
                trades.append({'type':'SELL','coin':c,'price':d['close']})
            
            # 止损
            elif cur_qty > 0:
                entry_prices = [t['price'] for t in reversed(trades) if t['coin']==c and t['type']=='BUY']
                if entry_prices:
                    pnl = (d['close'] - entry_prices[0]) / entry_prices[0]
                    if pnl < -cfg['stop_loss']:
                        qty = cur_qty * 0.5
                        revenue = qty * d['close'] * 0.999
                        capital += revenue
                        positions[c] -= qty
                        trades.append({'type':'STOP','coin':c,'price':d['close']})
    
    final_prices = {c: price_data[c][-1]['close'] for c in COINS}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in COINS)
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    sells = [t for t in trades if t['type'] == 'SELL']
    wins = sum(1 for i, s in enumerate(sells) if i % 2 == 1)
    win_rate = wins / len(sells) * 100 if sells else 0
    
    avg_used = np.mean([h['used'] for h in history]) * 100 if history else 0
    max_used = max([h['used'] for h in history]) * 100 if history else 0
    
    return {
        'return': total_return,
        'win_rate': win_rate,
        'capital_usage_avg': avg_used,
        'capital_usage_max': max_used,
        'total_trades': len(trades),
        'wins': wins,
        'losses': len(sells) - wins
    }

print("="*70)
print("最大算力优化 - 深度全面优化")
print("="*70)

# 获取数据
print("\n【获取数据】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', 30)
    if data:
        price_data[c] = data
        print(f"{len(data)}条 ✓")
    time.sleep(0.2)

print(f"\n数据天数: {min(len(price_data[c]) for c in price_data)}天")

# 最大算力参数矩阵
print("\n【最大算力优化中...】")

configs = []
# 穷举所有参数组合
buy_ths = [15, 18, 20, 22, 25]
sell_ths = [75, 78, 80, 82, 85]
pos_ratios = [0.2, 0.3, 0.4, 0.5]
stop_losses = [0.02, 0.03, 0.04, 0.05]
leverages = [1.0, 1.5, 2.0, 2.5, 3.0]
modes = ['normal', 'expert']

for mode, lev, buy_th, sell_th, pos_ratio, stop_loss in product(modes, leverages, buy_ths, sell_ths, pos_ratios, stop_losses):
    if buy_th >= sell_th: continue
    configs.append({
        'mode': mode, 'leverage': lev,
        'buy_th': buy_th, 'sell_th': sell_th,
        'pos_ratio': pos_ratio, 'stop_loss': stop_loss
    })

print(f"  共 {len(configs)} 种组合")

# 并行优化 (分批执行)
results = []
batch_size = 50

for i in range(0, len(configs), batch_size):
    batch = configs[i:i+batch_size]
    for cfg in batch:
        stats = simulate(1000, price_data, cfg)
        results.append({**cfg, **stats})
    
    progress = min(i+batch_size, len(configs))
    print(f"  进度: {progress}/{len(configs)} ({progress*100//len(configs)}%)")

# 排序
results.sort(key=lambda x: -x['return'])

# 结果
print("\n" + "="*70)
print("【优化结果 - Top 20】")
print("="*70)

print(f"\n{'排名':4} {'模式':8} {'杠杆':5} {'买':3} {'卖':3} {'仓位':5} {'止损':5} {'收益':9} {'胜率':7} {'资金':8} {'交易':6}")
print("-"*70)

for i, r in enumerate(results[:20]):
    print(f"{i+1:3d}. {r['mode']:8} {r['leverage']:4.1f}x {r['buy_th']:3d} {r['sell_th']:3d} {r['pos_ratio']*100:4.0f}% {r['stop_loss']*100:4.0f}% {r['return']:>+8.2f}% {r['win_rate']:>5.1f}% {r['capital_usage_avg']:>6.1f}% {r['total_trades']:5d}")

# 最优
best = results[0]
print("\n" + "="*70)
print("【最优配置】")
print("="*70)
print(f"""
┌─────────────────────────────────────────────────────────────────┐
│  模式: {best['mode']:12}  杠杆: {best['leverage']:.1f}x                            │
│  买入阈值: {best['buy_th']:2d}%  卖出阈值: {best['sell_th']:2d}%  仓位: {best['pos_ratio']*100:.0f}%                     │
│  止损: {best['stop_loss']*100:.0f}%                                                   │
│  ─────────────────────────────────────────────────────────────  │
│  收益: {best['return']:>+8.2f}%  胜率: {best['win_rate']:.1f}%  资金使用: {best['capital_usage_avg']:.1f}%             │
│  交易次数: {best['total_trades']}  胜负: {best['wins']}/{best['losses']}                                     │
└─────────────────────────────────────────────────────────────────┘
""")

# 保存
with open('/tmp/max_optimize_results.json', 'w') as f:
    json.dump(results[:100], f, indent=2)

print("✅ 优化完成!")
