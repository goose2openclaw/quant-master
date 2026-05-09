#!/usr/bin/env python3
"""GO2SE Genius v6.0 30天回测 - 普通模式 vs 专家模式"""
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

def bollinger_pos(price, highs, lows, period=20):
    if len(highs) < period or len(lows) < period: return 50
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def simulate(initial_capital, price_data, cfg):
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 0]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    trades = []
    history = []
    leverage = cfg.get('leverage', 1)
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        pos_value = sum(positions[c] * day_data[c]['close'] for c in valid_coins)
        total = capital + pos_value
        used_ratio = pos_value / total if total > 0 else 0
        history.append({'portfolio': total, 'used': used_ratio})
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            prices = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            
            rsi_7 = get_rsi(prices, 7)
            rsi_14 = get_rsi(prices, 14)
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            cur_qty = positions[c]
            
            # 买入信号
            buy = False
            if cfg['mode'] == 'normal':
                # 普通模式
                if rsi_7 < cfg['rsi_buy'] or bb_pos < cfg['bb_buy']:
                    buy = True
            else:
                # 专家模式 - 更严格
                if rsi_7 < cfg['rsi_buy'] and bb_pos < cfg['bb_buy']:
                    buy = True
            
            if buy and capital > 10:
                invest = capital * cfg['position_ratio'] * leverage
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    trades.append({'type':'BUY','coin':c,'price':d['close'],'mode':cfg['mode']})
            
            # 卖出信号
            sell = False
            if cur_qty > 0:
                if cfg['mode'] == 'normal':
                    if rsi_7 > cfg['rsi_sell'] or bb_pos > cfg['bb_sell']:
                        sell = True
                else:
                    if rsi_7 > cfg['rsi_sell'] and bb_pos > cfg['bb_sell']:
                        sell = True
                
                # 止盈止损
                entry = [t['price'] for t in reversed(trades) if t['coin']==c and t['type']=='BUY' and t.get('mode')==cfg['mode']]
                if entry:
                    pnl = (d['close'] - entry[0]) / entry[0] * leverage
                    if pnl >= cfg['take_profit'] or pnl <= -cfg['stop_loss']:
                        sell = True
            
            if sell:
                qty = cur_qty * cfg['sell_ratio']
                revenue = qty * d['close'] * 0.999
                capital += revenue
                positions[c] -= qty
                trades.append({'type':'SELL','coin':c,'price':d['close'],'mode':cfg['mode']})
    
    final_prices = {c: price_data[c][-1]['close'] for c in valid_coins}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in valid_coins)
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    sells = [t for t in trades if t['type'] == 'SELL']
    
    # 计算胜负
    wins = 0
    for i, sell_t in enumerate(sells):
        buy_t = [t for t in trades if t['coin']==sell_t['coin'] and t['type']=='BUY' and t.get('mode')==cfg['mode']]
        if buy_t:
            pnl = (sell_t['price'] - buy_t[-1]['price']) / buy_t[-1]['price'] * leverage
            if pnl > 0: wins += 1
    
    win_rate = wins / len(sells) * 100 if sells else 0
    avg_used = np.mean([h['used'] for h in history]) * 100 if history else 0
    max_used = max([h['used'] for h in history]) * 100 if history else 0
    
    return {
        'return': total_return, 'win_rate': win_rate,
        'capital_usage_avg': avg_used, 'capital_usage_max': max_used,
        'total_trades': len(trades), 'wins': wins, 'losses': len(sells)-wins
    }

print("="*70)
print("GO2SE Genius v6.0 - 30天回测")
print("普通模式 vs 专家模式")
print("="*70)

print("\n【获取数据】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', 30)
    if data: price_data[c] = data; print(f"{len(data)}条")
    time.sleep(0.2)

# 配置矩阵
configs = [
    # 普通模式 - 无杠杆
    {'name':'普通-1x','mode':'normal','rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.7,'take_profit':0.15,'stop_loss':0.05,'sell_ratio':0.5,'leverage':1},
    {'name':'普通-2x','mode':'normal','rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.5,'take_profit':0.10,'stop_loss':0.05,'sell_ratio':0.5,'leverage':2},
    {'name':'普通-3x','mode':'normal','rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.4,'take_profit':0.08,'stop_loss':0.04,'sell_ratio':0.5,'leverage':3},
    {'name':'普通-5x','mode':'normal','rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.3,'take_profit':0.06,'stop_loss':0.03,'sell_ratio':0.5,'leverage':5},
    # 普通模式 - RSI变化
    {'name':'普通-R40','mode':'normal','rsi_buy':40,'rsi_sell':60,'bb_buy':25,'bb_sell':75,'position_ratio':0.6,'take_profit':0.12,'stop_loss':0.05,'sell_ratio':0.5,'leverage':1},
    {'name':'普通-R30','mode':'normal','rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'position_ratio':0.6,'take_profit':0.12,'stop_loss':0.05,'sell_ratio':0.5,'leverage':1},
    # 专家模式 - 无杠杆
    {'name':'专家-1x','mode':'expert','rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.7,'take_profit':0.15,'stop_loss':0.05,'sell_ratio':0.5,'leverage':1},
    {'name':'专家-2x','mode':'expert','rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.5,'take_profit':0.10,'stop_loss':0.05,'sell_ratio':0.5,'leverage':2},
    {'name':'专家-3x','mode':'expert','rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.4,'take_profit':0.08,'stop_loss':0.04,'sell_ratio':0.5,'leverage':3},
    {'name':'专家-5x','mode':'expert','rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.3,'take_profit':0.06,'stop_loss':0.03,'sell_ratio':0.5,'leverage':5},
    # 专家模式 - RSI变化
    {'name':'专家-R40','mode':'expert','rsi_buy':40,'rsi_sell':60,'bb_buy':25,'bb_sell':75,'position_ratio':0.6,'take_profit':0.12,'stop_loss':0.05,'sell_ratio':0.5,'leverage':1},
    {'name':'专家-R30','mode':'expert','rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'position_ratio':0.6,'take_profit':0.12,'stop_loss':0.05,'sell_ratio':0.5,'leverage':1},
]

results = []

print(f"\n【执行{len(configs)}种配置回测】")
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    if stats:
        results.append({**cfg, **stats})
        print(f"  {cfg['name']:12} {cfg['mode']:7} {cfg['leverage']}x 仓:{cfg['position_ratio']*100:.0f}% RSI:{cfg['rsi_buy']}/{cfg['rsi_sell']} -> 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}% 交易:{stats['total_trades']}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【结果矩阵 - v6.0 普通模式】")
print("="*70)

normal_results = [r for r in results if r['mode'] == 'normal']
print(f"\n{'配置':12} {'杠杆':5} {'仓位':6} {'RSI':8} {'止盈':6} {'止损':6} {'收益':10} {'胜率':7} {'资金(均/最大)':18} {'交易':6}")
print("-"*90)
for r in normal_results:
    print(f"{r['name']:12} {r['leverage']:4d}x {r['position_ratio']*100:5.0f}% {r['rsi_buy']}/{r['rsi_sell']:5} {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['capital_usage_avg']:>5.1f}%/{r['capital_usage_max']:>5.1f}% {r['total_trades']:5d}")

print("\n" + "="*70)
print("【结果矩阵 - v6.0 专家模式】")
print("="*70)

expert_results = [r for r in results if r['mode'] == 'expert']
print(f"\n{'配置':12} {'杠杆':5} {'仓位':6} {'RSI':8} {'止盈':6} {'止损':6} {'收益':10} {'胜率':7} {'资金(均/最大)':18} {'交易':6}")
print("-"*90)
for r in expert_results:
    print(f"{r['name']:12} {r['leverage']:4d}x {r['position_ratio']*100:5.0f}% {r['rsi_buy']}/{r['rsi_sell']:5} {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['capital_usage_avg']:>5.1f}%/{r['capital_usage_max']:>5.1f}% {r['total_trades']:5d}")

# 最优配置
best_normal = normal_results[0] if normal_results else None
best_expert = expert_results[0] if expert_results else None

print("\n" + "="*70)
print("【最优配置 - v6.0】")
print("="*70)

if best_normal:
    print(f"""
┌─────────────────────────────────────────────────────────────────┐
│                    普通模式最优                                     │
├─────────────────────────────────────────────────────────────────┤
│  配置: {best_normal['name']}                                        │
│  杠杆: {best_normal['leverage']}x 仓位: {best_normal['position_ratio']*100:.0f}%                               │
│  RSI: {best_normal['rsi_buy']}/{best_normal['rsi_sell']} 止盈: {best_normal['take_profit']*100:.0f}% 止损: {best_normal['stop_loss']*100:.1f}%                   │
│  收益: {best_normal['return']:>+8.2f}% 胜率: {best_normal['win_rate']:.1f}%                           │
│  资金: {best_normal['capital_usage_avg']:.1f}/{best_normal['capital_usage_max']:.1f}% 交易: {best_normal['total_trades']}                          │
└─────────────────────────────────────────────────────────────────┘
""")

if best_expert:
    print(f"""
┌─────────────────────────────────────────────────────────────────┐
│                    专家模式最优                                     │
├─────────────────────────────────────────────────────────────────┤
│  配置: {best_expert['name']}                                        │
│  杠杆: {best_expert['leverage']}x 仓位: {best_expert['position_ratio']*100:.0f}%                               │
│  RSI: {best_expert['rsi_buy']}/{best_expert['rsi_sell']} 止盈: {best_expert['take_profit']*100:.0f}% 止损: {best_expert['stop_loss']*100:.1f}%                   │
│  收益: {best_expert['return']:>+8.2f}% 胜率: {best_expert['win_rate']:.1f}%                           │
│  资金: {best_expert['capital_usage_avg']:.1f}/{best_expert['capital_usage_max']:.1f}% 交易: {best_expert['total_trades']}                          │
└─────────────────────────────────────────────────────────────────┘
""")

# 对比
if best_normal and best_expert:
    print("\n【普通 vs 专家 对比】")
    print(f"  普通模式: {best_normal['return']:+.2f}% ({best_normal['win_rate']:.1f}%胜率)")
    print(f"  专家模式: {best_expert['return']:+.2f}% ({best_expert['win_rate']:.1f}%胜率)")
    better = "普通" if best_normal['return'] > best_expert['return'] else "专家"
    print(f"  推荐: {better}模式")

with open('/tmp/backtest_v60.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ v6.0回测完成!")
