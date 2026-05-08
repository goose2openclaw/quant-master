#!/usr/bin/env python3
"""
GBrain Extreme - 极端参数探索
目标: 月收益100%+
"""
import requests, time, json, numpy as np

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, days=30):
    end = int(time.time()*1000)
    start = end - days*86400*1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1d&startTime={start}&endTime={end}&limit=1000'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'open':float(k[1]),'high':float(k[2]),'low':float(k[3]),'close':float(k[4]),'volume':float(k[5])} for k in r.json()]
    except: return []

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def simulate_aggressive(initial_capital, price_data, cfg):
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 0]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    trades = []
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        for c in valid_coins:
            d = day_data[c]
            prices = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            rsi = get_rsi(prices, cfg['rsi_period'])
            cur_qty = positions[c]
            
            # 买入: RSI低于阈值
            if rsi < cfg['rsi_buy'] and capital > 10:
                invest = capital * cfg['position_size']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    trades.append({'type':'BUY','coin':c,'price':d['close']})
            
            # 卖出: RSI高于阈值
            elif cur_qty > 0 and rsi > cfg['rsi_sell']:
                qty = cur_qty * cfg['sell_ratio']
                revenue = qty * d['close'] * 0.999
                capital += revenue
                positions[c] -= qty
                trades.append({'type':'SELL','coin':c,'price':d['close']})
    
    final_prices = {c: price_data[c][-1]['close'] for c in valid_coins}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in valid_coins)
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    sells = [t for t in trades if t['type'] == 'SELL']
    return {'return': total_return, 'total_trades': len(trades)}

print("="*70)
print("GBrain Extreme - 极端参数探索")
print("="*70)

price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', 30)
    if data: price_data[c] = data
    time.sleep(0.1)

# 极端参数矩阵 - 穷举RSI组合
results = []

# RSI极值组合
rsi_combinations = [
    (20, 80), (15, 85), (10, 90), (25, 75), (30, 70), (35, 65), (40, 60), (45, 55)
]

for rsi_buy, rsi_sell in rsi_combinations:
    for pos in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        for sell_r in [0.5, 0.6, 0.7, 0.8, 1.0]:
            cfg = {'rsi_buy': rsi_buy, 'rsi_sell': rsi_sell, 'rsi_period': 7, 'position_size': pos, 'sell_ratio': sell_r}
            stats = simulate_aggressive(1000, price_data, cfg)
            if stats:
                results.append({**cfg, **stats})

results.sort(key=lambda x: -x['return'])

print(f"\n【测试了{len(results)}种极端配置】")

print("\nTop 20 配置:")
print(f"{'RSI买':7} {'RSI卖':7} {'仓位':6} {'卖比':6} {'收益':10} {'交易':6}")
print("-"*50)
for r in results[:20]:
    print(f"{r['rsi_buy']:7d} {r['rsi_sell']:7d} {r['position_size']*100:5.0f}% {r['sell_ratio']*100:5.0f}% {r['return']:>+9.2f}% {r['total_trades']:5d}")

# 最佳结果
best = results[0] if results else None
print(f"""
======================================================================
【GBrain Extreme最优结果】
======================================================================
""")
if best:
    print(f"RSI买入: {best['rsi_buy']}  RSI卖出: {best['rsi_sell']}")
    print(f"仓位: {best['position_size']*100:.0f}%  卖出比例: {best['sell_ratio']*100:.0f}%")
    print(f"收益: {best['return']:+.2f}%  交易次数: {best['total_trades']}")

print("\n【分析】")
print("100%月收益需要:")
print("1. 约2x现货涨幅(持有不动)")
print("2. 或使用杠杆+合约")
print("3. 或日内高频(当前数据为日线,受限)")
print("="*70)

with open('/tmp/backtest_gbrain_extreme.json', 'w') as f:
    json.dump(results[:50], f, indent=2)
