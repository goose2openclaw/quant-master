#!/usr/bin/env python3
"""
GBrain Leverage v2.0 - 优化版
结合网格+马丁格尔+趋势跟踪
"""
import requests, time, json, numpy as np

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
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

def bollinger_pos(price, high, low):
    return (price-low)/(high-low)*100 if high>low else 50

def simulate_grid_martingale(initial_capital, price_data, cfg):
    """网格+马丁格尔策略"""
    capital = initial_capital
    grid_levels = cfg['grid_levels']
    position = 0
    avg_entry = 0
    leverage = cfg['leverage']
    trades = []
    
    for day_idx in range(len(price_data.get('BTC',[])) - 1):
        signals_buy = []
        signals_sell = []
        
        for c in COINS:
            if c not in price_data or day_idx >= len(price_data[c]) - 1:
                continue
            d = price_data[c][day_idx]
            prices = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            rsi = get_rsi(prices, cfg['rsi_period'])
            bb_pos = bollinger_pos(d['close'], d['high'], d['low'])
            
            if rsi < cfg['rsi_buy'] and bb_pos < cfg['bb_buy']:
                signals_buy.append((c, rsi, bb_pos))
            elif rsi > cfg['rsi_sell'] and bb_pos > cfg['bb_sell']:
                signals_sell.append((c, rsi, bb_pos))
        
        # 买入信号
        if signals_buy and position == 0:
            signals_buy.sort(key=lambda x: x[1])
            coin, rsi, bb = signals_buy[0]
            price = price_data[coin][day_idx]['close']
            size = capital * leverage * cfg['position_ratio']
            qty = size / price
            position = qty
            avg_entry = price
            trades.append({'type':'BUY','coin':coin,'price':price})
        
        # 持仓管理 - 网格加仓
        elif position > 0:
            coin = trades[-1]['coin']
            price = price_data[coin][day_idx]['close']
            pnl_pct = (price - avg_entry) / avg_entry
            
            # 止损
            if pnl_pct <= -cfg['stop_loss']:
                pnl = capital * pnl_pct * leverage
                capital += pnl
                position = 0
                trades.append({'type':'STOP','coin':coin,'pnl':pnl_pct*100})
            
            # 止盈
            elif pnl_pct >= cfg['take_profit']:
                pnl = capital * pnl_pct * leverage
                capital += pnl
                position = 0
                trades.append({'type':'TAKE_PROFIT','coin':coin,'pnl':pnl_pct*100})
            
            # 网格加仓
            elif pnl_pct <= -cfg['grid_threshold'] and len([t for t in trades if t['type']=='BUY']) < grid_levels:
                add_size = capital * leverage * cfg['grid_ratio']
                add_qty = add_size / price
                new_avg = (avg_entry * position + price * add_qty) / (position + add_qty)
                avg_entry = new_avg
                position += add_qty
                capital -= add_size / leverage
                trades.append({'type':'GRID_ADD','coin':coin,'price':price,'avg':new_avg})
            
            # RSI平仓
            prices = [price_data[coin][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            rsi = get_rsi(prices, cfg['rsi_period'])
            if rsi > cfg['rsi_sell']:
                pnl = capital * pnl_pct * leverage
                capital += pnl
                position = 0
                trades.append({'type':'RSI_CLOSE','coin':coin,'pnl':pnl_pct*100})
        
        # 空仓检查卖出信号
        elif position == 0 and signals_sell and cfg.get('allow_short'):
            signals_sell.sort(key=lambda x: x[1], reverse=True)
            coin, rsi, bb = signals_sell[0]
            price = price_data[coin][day_idx]['close']
            # 做空
            position = -1
            avg_entry = price
            trades.append({'type':'SHORT','coin':coin,'price':price})
    
    final_return = (capital - initial_capital) / initial_capital * 100
    
    closes = [t for t in trades if t['type'] in ['STOP','TAKE_PROFIT','RSI_CLOSE']]
    wins = sum(1 for t in closes if t.get('pnl', 0) > 0)
    
    return {
        'return': final_return,
        'win_rate': wins / len(closes) * 100 if closes else 0,
        'total_trades': len(trades),
        'wins': wins,
        'losses': len(closes) - wins
    }

# ==================== 主程序 ====================
print("="*70)
print("GBrain Leverage v2.0 - 网格+马丁格尔优化版")
print("="*70)

print("\n【获取数据】")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

# 配置矩阵 - 优化参数
configs = [
    # 网格基础配置
    {'name':'3x网格','leverage':3,'rsi_period':14,'rsi_buy':30,'rsi_sell':70,'bb_buy':25,'bb_sell':75,'position_ratio':0.3,'take_profit':0.06,'stop_loss':0.03,'grid_levels':3,'grid_threshold':-0.02,'grid_ratio':0.2,'allow_short':True},
    {'name':'5x网格','leverage':5,'rsi_period':14,'rsi_buy':30,'rsi_sell':70,'bb_buy':25,'bb_sell':75,'position_ratio':0.2,'take_profit':0.05,'stop_loss':0.025,'grid_levels':3,'grid_threshold':-0.015,'grid_ratio':0.15,'allow_short':True},
    {'name':'3x激进','leverage':3,'rsi_period':7,'rsi_buy':25,'rsi_sell':75,'bb_buy':20,'bb_sell':80,'position_ratio':0.4,'take_profit':0.08,'stop_loss':0.04,'grid_levels':2,'grid_threshold':-0.025,'grid_ratio':0.25,'allow_short':True},
    {'name':'5x保守','leverage':5,'rsi_period':14,'rsi_buy':35,'rsi_sell':65,'bb_buy':30,'bb_sell':70,'position_ratio':0.15,'take_profit':0.04,'stop_loss':0.02,'grid_levels':4,'grid_threshold':-0.01,'grid_ratio':0.1,'allow_short':True},
    {'name':'3x马丁','leverage':3,'rsi_period':14,'rsi_buy':30,'rsi_sell':70,'bb_buy':25,'bb_sell':75,'position_ratio':0.25,'take_profit':0.10,'stop_loss':0.05,'grid_levels':5,'grid_threshold':-0.03,'grid_ratio':0.3,'allow_short':False},
    {'name':'5x趋势','leverage':5,'rsi_period':7,'rsi_buy':25,'rsi_sell':80,'bb_buy':20,'bb_sell':85,'position_ratio':0.25,'take_profit':0.08,'stop_loss':0.03,'grid_levels':2,'grid_threshold':-0.02,'grid_ratio':0.2,'allow_short':True},
    {'name':'3x双RSI','leverage':3,'rsi_period':7,'rsi_buy':28,'rsi_sell':72,'bb_buy':25,'bb_sell':75,'position_ratio':0.35,'take_profit':0.07,'stop_loss':0.035,'grid_levels':3,'grid_threshold':-0.02,'grid_ratio':0.2,'allow_short':True},
]

results = []

print(f"\n【执行{len(configs)}种配置回测】")
for cfg in configs:
    stats = simulate_grid_martingale(1000, price_data, cfg)
    results.append({**cfg, **stats})
    print(f"  {cfg['name']:12} {cfg['leverage']}x 仓:{cfg['position_ratio']*100:.0f}% RSI:{cfg['rsi_buy']}/{cfg['rsi_sell']} BB:{cfg['bb_buy']}/{cfg['bb_sell']} -> 收益:{stats['return']:>+8.2f}% 胜率:{stats['win_rate']:>5.1f}%")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【GBrain Leverage v2 结果矩阵】")
print("="*70)
print(f"\n{'配置':14} {'杠杆':5} {'仓位':6} {'RSI买':6} {'RSI卖':6} {'BB买':5} {'BB卖':5} {'止盈':6} {'止损':6} {'收益':9}")
print("-"*85)
for r in results:
    print(f"{r['name']:14} {r['leverage']:4d}x {r['position_ratio']*100:5.0f}% {r['rsi_buy']:6d} {r['rsi_sell']:6d} {r['bb_buy']:5d} {r['bb_sell']:5d} {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+8.2f}%")

best = results[0]
print(f"""
======================================================================
【最优配置 - GBrain Leverage v2】
======================================================================
配置: {best['name']}
杠杆: {best['leverage']}x 仓位:{best['position_ratio']*100:.0f}%
RSI: {best['rsi_buy']}/{best['rsi_sell']} 布林:{best['bb_buy']}/{best['bb_sell']}
止盈:{best['take_profit']*100:.0f}% 止损:{best['stop_loss']*100:.1f}%
网格层数:{best['grid_levels']} 网格阈值:{best['grid_threshold']*100:.1f}%
收益: {best['return']:+.2f}% 胜率:{best['win_rate']:.1f}% 交易:{best['total_trades']}
======================================================================
""")

# 100%目标
if best['return'] >= 100:
    print("🎉 达到100%月收益目标!")
else:
    print(f"当前最高: {best['return']:+.2f}%")

with open('/tmp/backtest_leverage_v2.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ 完成!")
