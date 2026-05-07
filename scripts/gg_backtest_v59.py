#!/usr/bin/env python3
"""
Hermes v5.9 - 30天回测
普通模式 vs 专家模式
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
            klines = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            rsi = get_rsi(klines)
            cur_qty = positions[c]
            
            # v5.9 EXPERT信号
            if cfg['mode'] == 'expert':
                # 买入: RSI < rsi_long
                if rsi < cfg['rsi_long'] and capital > 10:
                    invest = capital * cfg['pos_ratio']
                    qty = invest / d['close']
                    cost = qty * d['close'] * 1.001
                    if cost <= capital:
                        capital -= cost
                        positions[c] += qty
                        trades.append({'type':'BUY','coin':c,'price':d['close']})
                # 卖出: RSI > rsi_short
                elif cur_qty > 0 and rsi > cfg['rsi_short']:
                    qty = cur_qty * 0.5
                    revenue = qty * d['close'] * 0.999
                    capital += revenue
                    positions[c] -= qty
                    trades.append({'type':'SELL','coin':c,'price':d['close']})
                # 止损
                elif cur_qty > 0:
                    entry = [t['price'] for t in reversed(trades) if t['coin']==c and t['type']=='BUY']
                    if entry:
                        pnl = (d['close'] - entry[0]) / entry[0]
                        if pnl < -cfg['stop_loss']:
                            qty = cur_qty * 0.5
                            revenue = qty * d['close'] * 0.999
                            capital += revenue
                            positions[c] -= qty
                            trades.append({'type':'STOP','coin':c,'price':d['close']})
            else:  # normal模式
                # 买入: 位置 < buy_th
                if pos < cfg['buy_th'] and capital > 10:
                    invest = capital * cfg['pos_ratio']
                    qty = invest / d['close']
                    cost = qty * d['close'] * 1.001
                    if cost <= capital:
                        capital -= cost
                        positions[c] += qty
                        trades.append({'type':'BUY','coin':c,'price':d['close']})
                # 卖出: 位置 > sell_th
                elif cur_qty > 0 and pos > cfg['sell_th']:
                    qty = cur_qty * 0.5
                    revenue = qty * d['close'] * 0.999
                    capital += revenue
                    positions[c] -= qty
                    trades.append({'type':'SELL','coin':c,'price':d['close']})
    
    final_prices = {c: price_data[c][-1]['close'] for c in COINS}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in COINS)
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    sells = [t for t in trades if t['type'] == 'SELL']
    
    wins = losses = 0
    for i, sell in enumerate(sells):
        prev_buys = [b for b in reversed(trades) if b['coin']==sell['coin'] and b['type']=='BUY' and b['price'] < sell['price']]
        if prev_buys and sell['price'] > prev_buys[0]['price']:
            wins += 1
        else:
            losses += 1
    
    win_rate = wins / len(sells) * 100 if sells else 0
    avg_used = np.mean([h['used'] for h in history]) * 100 if history else 0
    max_used = max([h['used'] for h in history]) * 100 if history else 0
    
    return {
        'return': total_return, 'win_rate': win_rate,
        'capital_usage_avg': avg_used, 'capital_usage_max': max_used,
        'total_trades': len(trades), 'wins': wins, 'losses': losses
    }

print("="*70)
print("Hermes v5.9 - 30天回测")
print("普通模式 vs 专家模式")
print("="*70)

print("\n【获取数据】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', 30)
    if data:
        price_data[c] = data
        print(f"{len(data)}条 ✓")
    time.sleep(0.2)

days = min(len(price_data[c]) for c in price_data)
print(f"\n数据天数: {days}天")

# 配置矩阵
configs = [
    # Normal模式
    {'mode':'normal','buy_th':20,'sell_th':80,'pos_ratio':0.3,'stop_loss':0.05,'rsi_long':32,'rsi_short':71},
    {'mode':'normal','buy_th':22,'sell_th':78,'pos_ratio':0.35,'stop_loss':0.04,'rsi_long':32,'rsi_short':71},
    {'mode':'normal','buy_th':25,'sell_th':75,'pos_ratio':0.4,'stop_loss':0.04,'rsi_long':32,'rsi_short':71},
    {'mode':'normal','buy_th':25,'sell_th':80,'pos_ratio':0.5,'stop_loss':0.03,'rsi_long':32,'rsi_short':71},
    # Expert模式
    {'mode':'expert','buy_th':20,'sell_th':80,'pos_ratio':0.25,'stop_loss':0.015,'rsi_long':32,'rsi_short':71},
    {'mode':'expert','buy_th':20,'sell_th':80,'pos_ratio':0.3,'stop_loss':0.02,'rsi_long':32,'rsi_short':71},
    {'mode':'expert','buy_th':22,'sell_th':75,'pos_ratio':0.35,'stop_loss':0.02,'rsi_long':32,'rsi_short':71},
    {'mode':'expert','buy_th':25,'sell_th':75,'pos_ratio':0.4,'stop_loss':0.015,'rsi_long':32,'rsi_short':71},
]

results = []

print("\n【执行回测】")
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    results.append({**cfg, **stats})
    print(f"  {cfg['mode']:8} 买:{cfg['buy_th']} 卖:{cfg['sell_th']} 仓:{cfg['pos_ratio']*100:.0f}% 损:{cfg['stop_loss']*100:.0f}% → 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}% 资金:{stats['capital_usage_avg']:.0f}%")

normal = sorted([r for r in results if r['mode']=='normal'], key=lambda x: -x['return'])
expert = sorted([r for r in results if r['mode']=='expert'], key=lambda x: -x['return'])

print("\n" + "="*70)
print("【结果矩阵 - 普通模式】")
print("="*70)
print(f"\n{'买':3} {'卖':3} {'仓位':5} {'止损':5} {'收益':9} {'胜率':7} {'资金(均/最大)':18} {'交易':6} {'胜负':8}")
print("-"*70)
for r in normal:
    print(f"{r['buy_th']:3d} {r['sell_th']:3d} {r['pos_ratio']*100:5.0f}% {r['stop_loss']*100:5.0f}% {r['return']:>+8.2f}% {r['win_rate']:>5.1f}% {r['capital_usage_avg']:>5.1f}%/{r['capital_usage_max']:>5.1f}% {r['total_trades']:5d} {r['wins']:3d}/{r['losses']:<3d}")

print("\n" + "="*70)
print("【结果矩阵 - 专家模式】")
print("="*70)
print(f"\n{'买':3} {'卖':3} {'仓位':5} {'止损':5} {'收益':9} {'胜率':7} {'资金(均/最大)':18} {'交易':6} {'胜负':8}")
print("-"*70)
for r in expert:
    print(f"{r['buy_th']:3d} {r['sell_th']:3d} {r['pos_ratio']*100:5.0f}% {r['stop_loss']*100:5.0f}% {r['return']:>+8.2f}% {r['win_rate']:>5.1f}% {r['capital_usage_avg']:>5.1f}%/{r['capital_usage_max']:>5.1f}% {r['total_trades']:5d} {r['wins']:3d}/{r['losses']:<3d}")

bn, be = normal[0], expert[0]

print("\n" + "="*70)
print("【最优配置 - v5.9】")
print("="*70)
print(f"""
┌─────────────────────────────────────────────────────────────────┐
│                     普通模式最优                                    │
├─────────────────────────────────────────────────────────────────┤
│  买入:{bn['buy_th']}% 卖出:{bn['sell_th']}%  仓位:{bn['pos_ratio']*100:.0f}% 止损:{bn['stop_loss']*100:.0f}%                  │
│  收益:{bn['return']:>+8.2f}%  胜率:{bn['win_rate']:.1f}%  资金使用:{bn['capital_usage_avg']:.1f}/{bn['capital_usage_max']:.1f}%  交易:{bn['total_trades']}次   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     专家模式最优                                    │
├─────────────────────────────────────────────────────────────────┤
│  买入:{be['buy_th']}% 卖出:{be['sell_th']}%  仓位:{be['pos_ratio']*100:.0f}% 止损:{be['stop_loss']*100:.1f}%                  │
│  收益:{be['return']:>+8.2f}%  胜率:{be['win_rate']:.1f}%  资金使用:{be['capital_usage_avg']:.1f}/{be['capital_usage_max']:.1f}%  交易:{be['total_trades']}次   │
└─────────────────────────────────────────────────────────────────┘
""")

with open('/tmp/backtest_v59.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ 回测完成!")
