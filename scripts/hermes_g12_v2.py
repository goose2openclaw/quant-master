#!/usr/bin/env python3
"""
Hermès G12 v2 - 收益100%/月 自主迭代
解决核心问题: 杠杆+做空+仓位+高频
"""
import requests, time, json, numpy as np
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'open':float(k[1]),'high':float(k[2]),'low':float(k[3]),'close':float(k[4]),'volume':float(k[5])} for k in r.json()]
    except: return []

def get_rsi(prices, period=7):
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

def get_atr(klines, period=14):
    if len(klines) < period+1: return 0
    trs = []
    for i in range(1, min(period+1, len(klines))):
        tr = max(klines[i]['high']-klines[i]['low'], abs(klines[i]['high']-klines[i-1]['close']), abs(klines[i]['low']-klines[i-1]['close']))
        trs.append(tr)
    return np.mean(trs) if trs else 0

def simulate_v2(initial_capital, price_data, cfg):
    """v2模拟器: 支持杠杆+做空+复利"""
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 100]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    entry_prices = {c: 0 for c in valid_coins}
    short_positions = {c: 0 for c in valid_coins}
    short_entries = {c: 0 for c in valid_coins}
    trades = []
    
    leverage = cfg.get('leverage', 1)
    position_ratio = cfg.get('position', 0.5)
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            closes = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            
            rsi = get_rsi(closes, cfg.get('rsi_period', 7))
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            
            # ========== 买入 (杠杆) ==========
            buy = False
            if cfg.get('mode') == 'normal':
                buy = rsi < cfg.get('rsi_buy', 35) or bb_pos < cfg.get('bb_buy', 25)
            else:
                buy = rsi < cfg.get('rsi_buy', 35) and bb_pos < cfg.get('bb_buy', 25)
            
            if buy and capital > 10:
                invest = capital * position_ratio * leverage
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    entry_prices[c] = d['close']
                    trades.append({'type':'BUY','coin':c,'price':d['close'],'leverage':leverage})
            
            # ========== 卖出 ==========
            if positions[c] > 0:
                pnl = (d['close'] - entry_prices[c]) / entry_prices[c] * leverage
                sell = False
                if cfg.get('mode') == 'normal':
                    sell = rsi > cfg.get('rsi_sell', 65) or bb_pos > cfg.get('bb_sell', 80)
                else:
                    sell = rsi > cfg.get('rsi_sell', 65) and bb_pos > cfg.get('bb_sell', 80)
                
                # 止盈止损
                if pnl >= cfg.get('take_profit', 0.05) or pnl <= -cfg.get('stop_loss', 0.03):
                    sell = True
                
                if sell:
                    revenue = positions[c] * d['close'] * 0.999
                    capital += revenue
                    positions[c] = 0
                    entry_prices[c] = 0
                    trades.append({'type':'SELL','coin':c,'pnl':pnl})
            
            # ========== 做空 (杠杆) ==========
            if short_positions[c] == 0:
                short = False
                if cfg.get('mode') == 'normal':
                    short = rsi > cfg.get('short_rsi', 70) or bb_pos > cfg.get('short_bb', 85)
                else:
                    short = rsi > cfg.get('short_rsi', 70) and bb_pos > cfg.get('short_bb', 85)
                
                if short and capital > 20:
                    short_qty = (capital * position_ratio * 0.5 * leverage) / d['close']
                    cost = short_qty * d['close'] * 1.002
                    if cost <= capital * 0.5:
                        capital -= cost
                        short_positions[c] += short_qty
                        short_entries[c] = d['close']
                        trades.append({'type':'SHORT_OPEN','coin':c,'price':d['close']})
            
            # ========== 做空平仓 ==========
            if short_positions[c] > 0:
                pnl = (short_entries[c] - d['close']) / short_entries[c] * leverage
                cover = False
                if pnl >= cfg.get('take_profit', 0.05) or pnl <= -cfg.get('stop_loss', 0.03):
                    cover = True
                if rsi < cfg.get('rsi_buy', 35) or bb_pos < cfg.get('bb_buy', 25):
                    cover = True
                
                if cover:
                    revenue = short_positions[c] * d['close'] * 0.999
                    capital += revenue + short_positions[c] * short_entries[c]
                    short_positions[c] = 0
                    short_entries[c] = 0
                    trades.append({'type':'SHORT_CLOSE','coin':c,'pnl':pnl})
    
    final_prices = {c: price_data[c][-1]['close'] for c in valid_coins}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in valid_coins)
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    closed = [t for t in trades if t['type'] in ['SELL','SHORT_CLOSE']]
    wins = sum(1 for t in closed if t.get('pnl', 0) > 0)
    win_rate = wins / len(closed) * 100 if closed else 0
    
    return {'return': total_return, 'win_rate': win_rate, 'trades': len(trades), 'wins': wins, 'losses': len(closed)-wins}

print("="*70)
print("Hermès G12 v2 - 收益100%/月 自主迭代")
print("="*70)

print("\n【获取数据】")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

# v2 配置 - 高收益目标
configs = [
    # 基础配置
    {'name':'v2-1x基础','mode':'normal','leverage':1,'position':0.5,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.08,'stop_loss':0.04,'rsi_period':7},
    # 杠杆配置
    {'name':'v2-2x杠杆','mode':'normal','leverage':2,'position':0.4,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.06,'stop_loss':0.03,'rsi_period':7},
    {'name':'v2-3x杠杆','mode':'normal','leverage':3,'position':0.3,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.05,'stop_loss':0.025,'rsi_period':7},
    # 专家模式
    {'name':'v2-专家2x','mode':'expert','leverage':2,'position':0.4,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.06,'stop_loss':0.03,'rsi_period':7},
    {'name':'v2-专家3x','mode':'expert','leverage':3,'position':0.3,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.05,'stop_loss':0.025,'rsi_period':7},
    # 激进配置
    {'name':'v2-激进2x','mode':'normal','leverage':2,'position':0.5,'rsi_buy':40,'rsi_sell':60,'bb_buy':30,'bb_sell':75,'short_rsi':65,'short_bb':80,'take_profit':0.04,'stop_loss':0.02,'rsi_period':7},
    {'name':'v2-激进3x','mode':'normal','leverage':3,'position':0.5,'rsi_buy':40,'rsi_sell':60,'bb_buy':30,'bb_sell':75,'short_rsi':65,'short_bb':80,'take_profit':0.03,'stop_loss':0.015,'rsi_period':7},
    # 做空加强
    {'name':'v2-做空王','mode':'normal','leverage':2,'position':0.4,'rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'short_rsi':60,'short_bb':75,'take_profit':0.06,'stop_loss':0.03,'rsi_period':7},
    # 高频
    {'name':'v2-高频3x','mode':'normal','leverage':3,'position':0.4,'rsi_buy':45,'rsi_sell':55,'bb_buy':30,'bb_sell':70,'short_rsi':65,'short_bb':80,'take_profit':0.03,'stop_loss':0.02,'rsi_period':5},
]

results = []
print(f"\n【执行{len(configs)}种配置回测】")
for cfg in configs:
    stats = simulate_v2(1000, price_data, cfg)
    if stats:
        result = {**cfg, **stats}
        results.append(result)
        print(f"  {cfg['name']:12} 2x:{cfg['leverage']} 仓:{cfg['position']*100:.0f}% → 收益:{stats['return']:>+8.2f}% 胜率:{stats['win_rate']:>5.1f}% 交易:{stats['trades']}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【G12 v2 回测结果】")
print("="*70)

print(f"\n{'配置':14} {'杠杆':4} {'仓位':5} {'收益':10} {'胜率':7} {'交易':6}")
print("-"*55)
for r in results:
    print(f"{r['name']:14} {r['leverage']:4}x {r['position']*100:4.0f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['trades']:>5d}")

best = results[0] if results else None
if best:
    print(f"\n🏆 最优: {best['name']}")
    print(f"   收益: {best['return']:+.2f}%")
    print(f"   胜率: {best['win_rate']:.1f}%")
    print(f"   杠杆: {best['leverage']}x | 仓位: {best['position']*100:.0f}%")
    print(f"   RSI: {best['rsi_buy']}/{best['rsi_sell']} | BB: {best['bb_buy']}/{best['bb_sell']}")
    print(f"   止盈: {best['take_profit']*100:.0f}% | 止损: {best['stop_loss']*100:.1f}%")

with open('/tmp/g12_v2_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("\n✅ Hermès G12 v2 迭代完成!")
