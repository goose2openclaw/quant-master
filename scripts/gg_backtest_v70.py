#!/usr/bin/env python3
"""GO2SE Genius v7.0 30天回测"""
import requests, time, json, numpy as np

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
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

def bollinger_pos(price, highs, lows, period=20):
    if len(highs) < period: return 50
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def simulate(initial_capital, price_data, cfg):
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 0]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    entry_prices = {c: 0 for c in valid_coins}
    trades = []
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            prices = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            
            rsi = get_rsi(prices, cfg['rsi_period'])
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            cur_qty = positions[c]
            
            # 买入信号
            buy = False
            if cfg['mode'] == 'normal':
                # 普通: OR条件
                if rsi < cfg['rsi_buy'] or bb_pos < cfg['bb_buy']:
                    buy = True
            else:
                # 专家: AND条件
                if rsi < cfg['rsi_buy'] and bb_pos < cfg['bb_buy']:
                    buy = True
            
            if buy and capital > 10:
                invest = capital * cfg['position_ratio']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    entry_prices[c] = d['close']
                    trades.append({'type':'BUY','coin':c,'price':d['close']})
            
            # 卖出信号
            if cur_qty > 0:
                pnl = (d['close'] - entry_prices[c]) / entry_prices[c]
                
                sell = False
                if cfg['mode'] == 'normal':
                    if rsi > cfg['rsi_sell'] or bb_pos > cfg['bb_sell']:
                        sell = True
                else:
                    if rsi > cfg['rsi_sell'] and bb_pos > cfg['bb_sell']:
                        sell = True
                
                # 止盈止损
                if pnl >= cfg['take_profit'] or pnl <= -cfg['stop_loss']:
                    sell = True
                
                if sell:
                    revenue = cur_qty * d['close'] * 0.999
                    capital += revenue
                    positions[c] = 0
                    entry_prices[c] = 0
                    trades.append({'type':'SELL','coin':c,'price':d['close'],'pnl':pnl})
    
    final_prices = {c: price_data[c][-1]['close'] for c in valid_coins}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in valid_coins)
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    sells = [t for t in trades if t['type'] == 'SELL']
    wins = sum(1 for t in sells if t.get('pnl', 0) > 0)
    win_rate = wins / len(sells) * 100 if sells else 0
    
    return {
        'return': total_return, 'win_rate': win_rate,
        'total_trades': len(trades), 'wins': wins, 'losses': len(sells)-wins
    }

print("="*70)
print("GO2SE Genius v7.0 - 30天回测")
print("="*70)

print("\n【获取小时级数据】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"{len(data)}条")
    time.sleep(0.1)

# 配置矩阵
configs = [
    # 普通模式
    {'name':'普通-v70','mode':'normal','rsi_period':7,'rsi_buy':40,'rsi_sell':60,'bb_buy':25,'bb_sell':80,'position_ratio':0.6,'take_profit':0.08,'stop_loss':0.04},
    {'name':'普通-R40','mode':'normal','rsi_period':7,'rsi_buy':40,'rsi_sell':60,'bb_buy':30,'bb_sell':75,'position_ratio':0.5,'take_profit':0.06,'stop_loss':0.03},
    {'name':'普通-R50','mode':'normal','rsi_period':7,'rsi_buy':50,'rsi_sell':50,'bb_buy':35,'bb_sell':65,'position_ratio':0.5,'take_profit':0.05,'stop_loss':0.025},
    {'name':'普通-激进','mode':'normal','rsi_period':7,'rsi_buy':45,'rsi_sell':55,'bb_buy':30,'bb_sell':70,'position_ratio':0.6,'take_profit':0.07,'stop_loss':0.035},
    {'name':'普通-保守','mode':'normal','rsi_period':14,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'position_ratio':0.4,'take_profit':0.10,'stop_loss':0.05},
    # 专家模式
    {'name':'专家-v70','mode':'expert','rsi_period':7,'rsi_buy':40,'rsi_sell':60,'bb_buy':25,'bb_sell':80,'position_ratio':0.6,'take_profit':0.08,'stop_loss':0.04},
    {'name':'专家-R40','mode':'expert','rsi_period':7,'rsi_buy':40,'rsi_sell':60,'bb_buy':30,'bb_sell':75,'position_ratio':0.5,'take_profit':0.06,'stop_loss':0.03},
    {'name':'专家-R50','mode':'expert','rsi_period':7,'rsi_buy':50,'rsi_sell':50,'bb_buy':35,'bb_sell':65,'position_ratio':0.5,'take_profit':0.05,'stop_loss':0.025},
    {'name':'专家-激进','mode':'expert','rsi_period':7,'rsi_buy':45,'rsi_sell':55,'bb_buy':30,'bb_sell':70,'position_ratio':0.6,'take_profit':0.07,'stop_loss':0.035},
    {'name':'专家-保守','mode':'expert','rsi_period':14,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'position_ratio':0.4,'take_profit':0.10,'stop_loss':0.05},
]

results = []

print(f"\n【执行{len(configs)}种配置回测】")
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    if stats:
        results.append({**cfg, **stats})
        print(f"  {cfg['name']:12} {cfg['mode']:7} RSI:{cfg['rsi_buy']}/{cfg['rsi_sell']} BB:{cfg['bb_buy']}/{cfg['bb_sell']} -> 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}% 交易:{stats['total_trades']}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【结果矩阵 - v7.0 普通模式】")
print("="*70)

normal_results = [r for r in results if r['mode'] == 'normal']
print(f"\n{'配置':14} {'RSI':8} {'BB':8} {'仓位':6} {'止盈':6} {'止损':6} {'收益':10} {'胜率':7} {'交易':6}")
print("-"*75)
for r in normal_results:
    print(f"{r['name']:14} {r['rsi_buy']}/{r['rsi_sell']:5} {r['bb_buy']}/{r['bb_sell']:5} {r['position_ratio']*100:5.0f}% {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['total_trades']:5d}")

print("\n" + "="*70)
print("【结果矩阵 - v7.0 专家模式】")
print("="*70)

expert_results = [r for r in results if r['mode'] == 'expert']
print(f"\n{'配置':14} {'RSI':8} {'BB':8} {'仓位':6} {'止盈':6} {'止损':6} {'收益':10} {'胜率':7} {'交易':6}")
print("-"*75)
for r in expert_results:
    print(f"{r['name']:14} {r['rsi_buy']}/{r['rsi_sell']:5} {r['bb_buy']}/{r['bb_sell']:5} {r['position_ratio']*100:5.0f}% {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['total_trades']:5d}")

# 最优
best_normal = normal_results[0] if normal_results else None
best_expert = expert_results[0] if expert_results else None

print("\n" + "="*70)
print("【最优配置 - v7.0】")
print("="*70)

if best_normal:
    print(f"""
┌─────────────────────────────────────────────────────────────────┐
│                    普通模式最优                                     │
├─────────────────────────────────────────────────────────────────┤
│  配置: {best_normal['name']}                                        │
│  RSI: {best_normal['rsi_buy']}/{best_normal['rsi_sell']}  BB: {best_normal['bb_buy']}/{best_normal['bb_sell']}                           │
│  仓位: {best_normal['position_ratio']*100:.0f}%  止盈: {best_normal['take_profit']*100:.0f}%  止损: {best_normal['stop_loss']*100:.1f}%                      │
│  收益: {best_normal['return']:>+8.2f}%  胜率: {best_normal['win_rate']:.1f}%  交易: {best_normal['total_trades']}                       │
└─────────────────────────────────────────────────────────────────┘
""")

if best_expert:
    print(f"""
┌─────────────────────────────────────────────────────────────────┐
│                    专家模式最优                                     │
├─────────────────────────────────────────────────────────────────┤
│  配置: {best_expert['name']}                                        │
│  RSI: {best_expert['rsi_buy']}/{best_expert['rsi_sell']}  BB: {best_expert['bb_buy']}/{best_expert['bb_sell']}                           │
│  仓位: {best_expert['position_ratio']*100:.0f}%  止盈: {best_expert['take_profit']*100:.0f}%  止损: {best_expert['stop_loss']*100:.1f}%                      │
│  收益: {best_expert['return']:>+8.2f}%  胜率: {best_expert['win_rate']:.1f}%  交易: {best_expert['total_trades']}                       │
└─────────────────────────────────────────────────────────────────┘
""")

# 对比
if best_normal and best_expert:
    print("\n【普通 vs 专家 对比】")
    print(f"  普通模式: {best_normal['return']:+.2f}% ({best_normal['win_rate']:.1f}%胜率)")
    print(f"  专家模式: {best_expert['return']:+.2f}% ({best_expert['win_rate']:.1f}%胜率)")
    better = "普通" if best_normal['return'] > best_expert['return'] else "专家"
    print(f"  推荐: {better}模式")

with open('/tmp/backtest_v70.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ v7.0回测完成!")
