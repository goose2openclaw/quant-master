#!/usr/bin/env python3
"""Hermes v5.10 30天回测"""
import requests, time, json, numpy as np

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
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 0]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    trades = []
    history = []
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        pos_value = sum(positions[c] * day_data[c]['close'] for c in valid_coins)
        total = capital + pos_value
        used_ratio = pos_value / total if total > 0 else 0
        history.append({'portfolio': total, 'used': used_ratio})
        
        for c in valid_coins:
            d = day_data[c]
            bb_pos = bollinger_pos(d['close'], d['high'], d['low'])
            rsi_prices = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            rsi = get_rsi(rsi_prices)
            cur_qty = positions[c]
            
            # v5.10信号
            chg_pct = (d['close'] - price_data[c][max(0,day_idx-1)]['close']) / price_data[c][max(0,day_idx-1)]['close'] * 100
            
            # 买入信号
            buy = False
            if bb_pos < cfg['buy_th'] or rsi < cfg['rsi_long'] or chg_pct < -2:
                buy = True
            
            if buy and capital > 10:
                invest = capital * cfg['pos_ratio']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    trades.append({'type':'BUY','coin':c,'price':d['close']})
            
            # 卖出信号
            elif cur_qty > 0 and (bb_pos > cfg['sell_th'] or rsi > cfg['rsi_short'] or chg_pct > 3):
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
                        trades.append({'type':'STOP','coin':c,'price':d['close'],'pnl':pnl})
    
    final_prices = {c: price_data[c][-1]['close'] for c in valid_coins}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in valid_coins)
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    sells = [t for t in trades if t['type'] in ['SELL','STOP']]
    wins = sum(1 for t in sells if t.get('pnl', 0) > 0 or t['type'] == 'SELL')
    losses = len(sells) - wins
    win_rate = wins / len(sells) * 100 if sells else 0
    
    avg_used = np.mean([h['used'] for h in history]) * 100 if history else 0
    max_used = max([h['used'] for h in history]) * 100 if history else 0
    
    return {'return': total_return, 'win_rate': win_rate,
            'capital_usage_avg': avg_used, 'capital_usage_max': max_used,
            'total_trades': len(trades), 'wins': wins, 'losses': losses}

print("="*70)
print("Hermes v5.10 - 30天回测")
print("="*70)

print("\n【获取数据】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', 30)
    if data: price_data[c] = data; print(f"{len(data)}条")
    time.sleep(0.2)

configs = [
    {'name':'普通均衡','buy_th':25,'sell_th':75,'rsi_long':30,'rsi_short':70,'pos_ratio':0.4,'stop_loss':0.03},
    {'name':'普通积极','buy_th':20,'sell_th':80,'rsi_long':28,'rsi_short':72,'pos_ratio':0.5,'stop_loss':0.03},
    {'name':'普通保守','buy_th':30,'sell_th':70,'rsi_long':35,'rsi_short':65,'pos_ratio':0.3,'stop_loss':0.05},
    {'name':'布林为主','buy_th':25,'sell_th':75,'rsi_long':25,'rsi_short':75,'pos_ratio':0.4,'stop_loss':0.04},
    {'name':'RSI为主','buy_th':35,'sell_th':65,'rsi_long':30,'rsi_short':70,'pos_ratio':0.4,'stop_loss':0.03},
]

results = []

print("\n【执行回测】")
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    if stats:
        results.append({**cfg, **stats})
        print(f"  {cfg['name']:10} 买:{cfg['buy_th']} 卖:{cfg['sell_th']} 仓:{cfg['pos_ratio']*100:.0f}% -> 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}%")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【结果矩阵】")
print("="*70)
print(f"\n{'配置':12} {'买':4} {'卖':4} {'RSI买':6} {'RSI卖':6} {'仓位':6} {'止损':6} {'收益':9} {'胜率':7} {'资金(均/最大)':18} {'交易':6}")
print("-"*90)
for r in results:
    print(f"{r['name']:12} {r['buy_th']:4d} {r['sell_th']:4d} {r['rsi_long']:6d} {r['rsi_short']:6d} {r['pos_ratio']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+8.2f}% {r['win_rate']:>5.1f}% {r['capital_usage_avg']:>5.1f}%/{r['capital_usage_max']:>5.1f}% {r['total_trades']:5d}")

if results:
    best = results[0]
    print(f"""
======================================================================
【最优配置 - v5.10】
======================================================================
配置: {best['name']}
买入:{best['buy_th']}% 卖出:{best['sell_th']}% RSI买:{best['rsi_long']} RSI卖:{best['rsi_short']}
仓位:{best['pos_ratio']*100:.0f}% 止损:{best['stop_loss']*100:.1f}%
收益:{best['return']:>+8.2f}% 胜率:{best['win_rate']:.1f}%
资金:{best['capital_usage_avg']:.1f}/{best['capital_usage_max']:.1f}% 交易:{best['total_trades']}
======================================================================
""")

with open('/tmp/backtest_v510.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ 回测完成!")
