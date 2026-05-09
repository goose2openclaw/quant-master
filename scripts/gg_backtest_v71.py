#!/usr/bin/env python3
"""GO2SE Genius v7.1 30天回测 - 完整版"""
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
    short_positions = {c: 0 for c in valid_coins}
    short_entries = {c: 0 for c in valid_coins}
    trades = []
    leverage = cfg.get('leverage', 1)
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            prices = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            
            rsi = get_rsi(prices, cfg['rsi_period'])
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            
            # ========== 买入 ==========
            buy = False
            if cfg['mode'] == 'normal':
                if rsi < cfg['rsi_buy'] or bb_pos < cfg['bb_buy']:
                    buy = True
            else:
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
            
            # ========== 卖出 ==========
            if positions[c] > 0:
                pnl = (d['close'] - entry_prices[c]) / entry_prices[c]
                sell = False
                
                if cfg['mode'] == 'normal':
                    if rsi > cfg['rsi_sell'] or bb_pos > cfg['bb_sell']:
                        sell = True
                else:
                    if rsi > cfg['rsi_sell'] and bb_pos > cfg['bb_sell']:
                        sell = True
                
                if pnl >= cfg['take_profit'] or pnl <= -cfg['stop_loss']:
                    sell = True
                
                if sell:
                    revenue = positions[c] * d['close'] * 0.999
                    capital += revenue
                    positions[c] = 0
                    entry_prices[c] = 0
                    trades.append({'type':'SELL','coin':c,'price':d['close'],'pnl':pnl})
            
            # ========== 做空 ==========
            if cfg.get('short_enabled') and short_positions[c] == 0:
                short = False
                if cfg['mode'] == 'normal':
                    if rsi > cfg['short_rsi'] or bb_pos > cfg['short_bb']:
                        short = True
                else:
                    if rsi > cfg['short_rsi'] and bb_pos > cfg['short_bb']:
                        short = True
                
                if short and capital > 20:
                    short_qty = capital * cfg['position_ratio'] * 0.5 / d['close']
                    cost = short_qty * d['close'] * 1.002
                    if cost <= capital * 0.5:
                        capital -= cost
                        short_positions[c] += short_qty
                        short_entries[c] = d['close']
                        trades.append({'type':'SHORT_OPEN','coin':c,'price':d['close']})
            
            # ========== 做空平仓 ==========
            if short_positions[c] > 0:
                pnl = (short_entries[c] - d['close']) / short_entries[c]
                cover = False
                
                if rsi < cfg['rsi_buy'] or bb_pos < cfg['bb_buy']:
                    cover = True
                
                if pnl >= cfg['take_profit'] or pnl <= -cfg['stop_loss'] * leverage:
                    cover = True
                
                if cover:
                    revenue = short_positions[c] * d['close'] * 0.999
                    capital += revenue + short_positions[c] * short_entries[c]
                    short_positions[c] = 0
                    short_entries[c] = 0
                    trades.append({'type':'SHORT_CLOSE','coin':c,'price':d['close'],'pnl':pnl})
    
    final_prices = {c: price_data[c][-1]['close'] for c in valid_coins}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in valid_coins)
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    sells = [t for t in trades if t['type'] in ['SELL','SHORT_CLOSE']]
    wins = sum(1 for t in sells if t.get('pnl', 0) > 0)
    win_rate = wins / len(sells) * 100 if sells else 0
    
    return {'return': total_return, 'win_rate': win_rate, 'total_trades': len(trades), 'wins': wins, 'losses': len(sells)-wins}

print("="*70)
print("GO2SE Genius v7.1 - 30天回测")
print("="*70)

print("\n【获取数据】")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100: price_data[c] = data; print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

# 配置
configs = [
    # 普通模式
    {'name':'普通-v71','mode':'normal','rsi_period':7,'rsi_buy':40,'rsi_sell':60,'bb_buy':25,'bb_sell':80,'position_ratio':0.65,'take_profit':0.08,'stop_loss':0.04,'leverage':3,'short_enabled':True,'short_rsi':70,'short_bb':85},
    {'name':'普通-保守','mode':'normal','rsi_period':14,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'position_ratio':0.5,'take_profit':0.10,'stop_loss':0.05,'leverage':3,'short_enabled':True,'short_rsi':70,'short_bb':85},
    {'name':'普通-激进','mode':'normal','rsi_period':7,'rsi_buy':45,'rsi_sell':55,'bb_buy':30,'bb_sell':75,'position_ratio':0.7,'take_profit':0.06,'stop_loss':0.03,'leverage':3,'short_enabled':True,'short_rsi':65,'short_bb':80},
    # 专家模式
    {'name':'专家-v71','mode':'expert','rsi_period':7,'rsi_buy':40,'rsi_sell':60,'bb_buy':25,'bb_sell':80,'position_ratio':0.65,'take_profit':0.08,'stop_loss':0.04,'leverage':3,'short_enabled':True,'short_rsi':70,'short_bb':85},
    {'name':'专家-保守','mode':'expert','rsi_period':14,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'position_ratio':0.5,'take_profit':0.10,'stop_loss':0.05,'leverage':3,'short_enabled':True,'short_rsi':70,'short_bb':85},
    {'name':'专家-激进','mode':'expert','rsi_period':7,'rsi_buy':45,'rsi_sell':55,'bb_buy':30,'bb_sell':75,'position_ratio':0.7,'take_profit':0.06,'stop_loss':0.03,'leverage':3,'short_enabled':True,'short_rsi':65,'short_bb':80},
]

results = []

print(f"\n【执行{len(configs)}种配置回测】")
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    if stats:
        results.append({**cfg, **stats})
        print(f"  {cfg['name']:12} {cfg['mode']:7} RSI:{cfg['rsi_buy']}/{cfg['rsi_sell']} 仓:{cfg['position_ratio']*100:.0f}% → 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}% 交易:{stats['total_trades']}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【结果矩阵 - v7.1完整版】")
print("="*70)

normal_results = [r for r in results if r['mode']=='normal']
expert_results = [r for r in results if r['mode']=='expert']

print(f"\n{'配置':14} {'RSI':8} {'BB':8} {'仓位':6} {'止盈':6} {'止损':6} {'收益':10} {'胜率':7} {'交易':6}")
print("-"*75)
for r in normal_results:
    print(f"{r['name']:14} {r['rsi_buy']}/{r['rsi_sell']:5} {r['bb_buy']}/{r['bb_sell']:5} {r['position_ratio']*100:5.0f}% {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['total_trades']:5d}")

print("\n" + "="*70)
print("【专家模式】")
print("="*70)
for r in expert_results:
    print(f"{r['name']:14} {r['rsi_buy']}/{r['rsi_sell']:5} {r['bb_buy']}/{r['bb_sell']:5} {r['position_ratio']*100:5.0f}% {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['total_trades']:5d}")

best_normal = normal_results[0] if normal_results else None
best_expert = expert_results[0] if expert_results else None

print("\n" + "="*70)
print("【最优配置 - v7.1】")
print("="*70)
if best_normal:
    print(f"普通模式最优: {best_normal['name']} 收益:{best_normal['return']:+.2f}% 胜率:{best_normal['win_rate']:.1f}%")
if best_expert:
    print(f"专家模式最优: {best_expert['name']} 收益:{best_expert['return']:+.2f}% 胜率:{best_expert['win_rate']:.1f}%")

print("\n✅ v7.1回测完成!")
