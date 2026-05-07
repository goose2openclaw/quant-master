#!/usr/bin/env python3
"""
Hermes EXPERT模式 - 30天回测
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
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]
    except: return []

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def simulate(initial_capital, price_data, cfg):
    # 确保所有coin都有数据
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
            
            # RSI计算
            rsi_prices = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            rsi = get_rsi(rsi_prices)
            
            cur_qty = positions[c]
            
            # EXPERT买入: RSI < rsi_long
            if rsi < cfg['rsi_long'] and capital > 10:
                invest = capital * cfg['position_size']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    trades.append({'type':'BUY','coin':c,'price':d['close'],'rsi':rsi})
            
            # EXPERT卖出: RSI > rsi_short
            elif cur_qty > 0 and rsi > cfg['rsi_short']:
                qty = cur_qty * 0.5
                revenue = qty * d['close'] * 0.999
                capital += revenue
                positions[c] -= qty
                trades.append({'type':'SELL','coin':c,'price':d['close'],'rsi':rsi})
            
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
    wins = sum(1 for t in sells if t.get('pnl', 0) > 0)
    losses = len(sells) - wins
    win_rate = wins / len(sells) * 100 if sells else 0
    
    avg_used = np.mean([h['used'] for h in history]) * 100 if history else 0
    max_used = max([h['used'] for h in history]) * 100 if history else 0
    
    return {
        'return': total_return, 'win_rate': win_rate,
        'capital_usage_avg': avg_used, 'capital_usage_max': max_used,
        'total_trades': len(trades), 'wins': wins, 'losses': losses
    }

print("="*70)
print("Hermes EXPERT模式 - 30天回测")
print("="*70)

# 获取数据
print("\n【获取数据】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', 30)
    if data and len(data) > 0:
        price_data[c] = data
        print(f"{len(data)}条 ✓")
    else:
        print("获取失败")
    time.sleep(0.2)

valid = [c for c in COINS if c in price_data and len(price_data[c]) > 0]
print(f"\n有效数据: {len(valid)}个币种")

# 配置
configs = [
    {'name':'RSI标准','rsi_long':32,'rsi_short':71,'position_size':0.25,'stop_loss':0.015},
    {'name':'RSI激进','rsi_long':30,'rsi_short':75,'position_size':0.30,'stop_loss':0.02},
    {'name':'RSI保守','rsi_long':35,'rsi_short':68,'position_size':0.20,'stop_loss':0.01},
    {'name':'RSI平衡','rsi_long':28,'rsi_short':72,'position_size':0.35,'stop_loss':0.025},
    {'name':'RSI高仓','rsi_long':32,'rsi_short':70,'position_size':0.40,'stop_loss':0.02},
    {'name':'RSI低位','rsi_long':25,'rsi_short':75,'position_size':0.30,'stop_loss':0.02},
]

results = []

print("\n【执行回测】")
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    if stats:
        results.append({**cfg, **stats})
        print(f"  {cfg['name']:15} RSI买:{cfg['rsi_long']} RSI卖:{cfg['rsi_short']} 仓:{cfg['position_size']*100:.0f}% → 收益:{stats['return']:>+8.2f}% 胜率:{stats['win_rate']:>5.1f}% 资金:{stats['capital_usage_avg']:.0f}%")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【回测结果矩阵 - EXPERT模式】")
print("="*70)

print(f"\n{'配置名称':18} {'RSI买':6} {'RSI卖':6} {'仓位':6} {'止损':6} {'收益':10} {'胜率':8} {'资金':12} {'交易':6}")
print("-"*80)
for r in results:
    print(f"{r['name']:18} {r['rsi_long']:6d} {r['rsi_short']:6d} {r['position_size']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>6.1f}% {r['capital_usage_avg']:>5.1f}%/{r['capital_usage_max']:>5.1f}% {r['total_trades']:5d}")

if results:
    best = results[0]
    print(f"""
======================================================================
【最优EXPERT配置】
======================================================================
配置名称: {best['name']}
RSI Long: {best['rsi_long']}  RSI Short: {best['rsi_short']}
仓位: {best['position_size']*100:.0f}%  止损: {best['stop_loss']*100:.1f}%
收益: {best['return']:>+8.2f}%  胜率: {best['win_rate']:.1f}%
资金使用: {best['capital_usage_avg']:.1f}/{best['capital_usage_max']:.1f}%  交易: {best['total_trades']}
======================================================================
""")

with open('/tmp/backtest_expert.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ 回测完成!")
