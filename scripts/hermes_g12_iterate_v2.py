#!/usr/bin/env python3
"""
Hermes G12 v6 - 迭代优化版
目标: 收益100%/月 | 胜率90%+
"""
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

def get_macd(prices):
    if len(prices) < 26: return 0
    return np.mean(prices[-12:]) - np.mean(prices[-26:])

def simulate_v6(initial_capital, price_data, cfg):
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 100]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    entry_prices = {c: 0 for c in valid_coins}
    short_qtys = {c: 0 for c in valid_coins}
    short_entries = {c: 0 for c in valid_coins}
    trades = []
    
    leverage = cfg.get('leverage', 1)
    position_ratio = cfg.get('position', 0.3)
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            closes = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            
            rsi = get_rsi(closes, cfg.get('rsi_period', 7))
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            macd = get_macd(closes)
            
            # G12 决策值
            decision = 0
            decision += 0.30 * (50 - min(rsi, 50)) / 50
            decision += 0.25 * (100 - bb_pos) / 100
            decision += 0.20 * min(macd / (d['close'] * 0.005), 1)
            
            # 做多 - 严格AND条件
            buy = False
            if cfg.get('mode') == 'expert':
                buy = (rsi < cfg.get('rsi_buy', 30) and bb_pos < cfg.get('bb_buy', 20) and decision > cfg.get('decision_threshold', 0.7))
            else:
                buy = (rsi < cfg.get('rsi_buy', 30) or bb_pos < cfg.get('bb_buy', 20)) and decision > cfg.get('decision_threshold', 0.7)
            
            if buy and capital > 10 and positions[c] == 0 and short_qtys[c] == 0:
                invest = capital * position_ratio * leverage
                qty = invest / d['close']
                entry_fee = invest * 0.001
                capital -= entry_fee
                positions[c] = qty
                entry_prices[c] = d['close']
                trades.append({'type':'LONG_OPEN','coin':c,'price':d['close']})
            
            # 做多平仓
            if positions[c] > 0:
                pnl = (d['close'] - entry_prices[c]) * positions[c] * leverage
                sell = False
                if cfg.get('mode') == 'expert':
                    sell = (rsi > cfg.get('rsi_sell', 70) and bb_pos > cfg.get('bb_sell', 80))
                else:
                    sell = (rsi > cfg.get('rsi_sell', 70) or bb_pos > cfg.get('bb_sell', 80))
                
                pnl_ratio = (d['close'] - entry_prices[c]) / entry_prices[c] * leverage
                if pnl_ratio >= cfg.get('take_profit', 0.08) or pnl_ratio <= -cfg.get('stop_loss', 0.04):
                    sell = True
                
                if sell:
                    exit_fee = positions[c] * d['close'] * 0.001
                    capital += pnl - exit_fee
                    positions[c] = 0
                    entry_prices[c] = 0
                    trades.append({'type':'LONG_CLOSE','coin':c,'pnl_ratio':pnl_ratio})
            
            # 做空
            if short_qtys[c] == 0 and positions[c] == 0:
                short = False
                if cfg.get('mode') == 'expert':
                    short = rsi > cfg.get('short_rsi', 70) and bb_pos > cfg.get('short_bb', 85) and decision < 0.3
                else:
                    short = rsi > cfg.get('short_rsi', 70) or bb_pos > cfg.get('short_bb', 85)
                
                if short and capital > 20:
                    qty = (capital * position_ratio * leverage) / d['close']
                    entry_fee = qty * d['close'] * 0.001
                    capital -= entry_fee
                    short_qtys[c] = qty
                    short_entries[c] = d['close']
                    trades.append({'type':'SHORT_OPEN','coin':c,'price':d['close']})
            
            # 做空平仓
            if short_qtys[c] > 0:
                pnl = (short_entries[c] - d['close']) * short_qtys[c] * leverage
                cover = False
                pnl_ratio = (short_entries[c] - d['close']) / short_entries[c] * leverage
                if pnl_ratio >= cfg.get('take_profit', 0.08) or pnl_ratio <= -cfg.get('stop_loss', 0.04):
                    cover = True
                if rsi < cfg.get('rsi_buy', 30) or bb_pos < cfg.get('bb_buy', 20):
                    cover = True
                
                if cover:
                    exit_fee = short_qtys[c] * d['close'] * 0.001
                    capital += pnl - exit_fee
                    short_qtys[c] = 0
                    short_entries[c] = 0
                    trades.append({'type':'SHORT_CLOSE','coin':c,'pnl_ratio':pnl_ratio})
    
    final_value = capital
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    closed = [t for t in trades if t['type'] in ['LONG_CLOSE','SHORT_CLOSE']]
    wins = sum(1 for t in closed if t.get('pnl_ratio', 0) > 0)
    win_rate = wins / len(closed) * 100 if closed else 0
    
    return {'return': total_return, 'win_rate': win_rate, 'trades': len(trades), 'wins': wins, 'losses': len(closed)-wins}

print("="*70)
print("Hermes G12 v6 - 迭代优化版")
print("目标: 收益100%/月 | 胜率90%+")
print("="*70)

print("\n获取数据")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

# 大量配置测试
configs = [
    # 基础
    {'name':'基础-2x','mode':'normal','leverage':2,'position':0.40,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.08,'stop_loss':0.04,'decision_threshold':0.65,'rsi_period':7},
    {'name':'基础-3x','mode':'normal','leverage':3,'position':0.30,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.06,'stop_loss':0.03,'decision_threshold':0.65,'rsi_period':7},
    # 专家
    {'name':'专家-2x','mode':'expert','leverage':2,'position':0.40,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.08,'stop_loss':0.04,'decision_threshold':0.70,'rsi_period':7},
    {'name':'专家-3x','mode':'expert','leverage':3,'position':0.30,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.06,'stop_loss':0.03,'decision_threshold':0.70,'rsi_period':7},
    # 严格
    {'name':'严格-2x','mode':'expert','leverage':2,'position':0.35,'rsi_buy':25,'rsi_sell':75,'bb_buy':15,'bb_sell':85,'short_rsi':65,'short_bb':80,'take_profit':0.10,'stop_loss':0.04,'decision_threshold':0.75,'rsi_period':7},
    {'name':'严格-3x','mode':'expert','leverage':3,'position':0.25,'rsi_buy':25,'rsi_sell':75,'bb_buy':15,'bb_sell':85,'short_rsi':65,'short_bb':80,'take_profit':0.08,'stop_loss':0.03,'decision_threshold':0.75,'rsi_period':7},
    # 高决策
    {'name':'高决策-2x','mode':'expert','leverage':2,'position':0.40,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.08,'stop_loss':0.04,'decision_threshold':0.80,'rsi_period':7},
    {'name':'高决策-3x','mode':'expert','leverage':3,'position':0.30,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.06,'stop_loss':0.03,'decision_threshold':0.80,'rsi_period':7},
    # RSI周期
    {'name':'RSI14-2x','mode':'expert','leverage':2,'position':0.40,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.08,'stop_loss':0.04,'decision_threshold':0.70,'rsi_period':14},
    {'name':'RSI14-3x','mode':'expert','leverage':3,'position':0.30,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.06,'stop_loss':0.03,'decision_threshold':0.70,'rsi_period':14},
    # 小止盈
    {'name':'小止盈-2x','mode':'expert','leverage':2,'position':0.40,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.05,'stop_loss':0.03,'decision_threshold':0.70,'rsi_period':7},
    {'name':'小止盈-3x','mode':'expert','leverage':3,'position':0.30,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':70,'short_bb':85,'take_profit':0.04,'stop_loss':0.02,'decision_threshold':0.70,'rsi_period':7},
    # 做空加强
    {'name':'空强-2x','mode':'expert','leverage':2,'position':0.40,'rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'short_rsi':60,'short_bb':75,'take_profit':0.08,'stop_loss':0.04,'decision_threshold':0.70,'rsi_period':7},
]

results = []
print(f"\n执行{len(configs)}种配置回测")
for cfg in configs:
    stats = simulate_v6(1000, price_data, cfg)
    if stats:
        result = {**cfg, **stats}
        results.append(result)
        mark = "⭐" if stats['return'] > 50 else ""
        print(f"  {cfg['name']:14} 决:{cfg['decision_threshold']} → 收益:{stats['return']:>+8.2f}% 胜率:{stats['win_rate']:>5.1f}% {mark}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("G12 v6 回测结果 TOP 10")
print("="*70)

print(f"\n{'配置':16} {'决策':5} {'收益':10} {'胜率':7} {'交易':6}")
print("-"*50)
for r in results[:10]:
    print(f"{r['name']:16} {r['decision_threshold']:5.2f} {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['trades']:>5d}")

best = results[0] if results else None
if best:
    print(f"\n🏆 最优: {best['name']}")
    print(f"   收益: {best['return']:+.2f}%")
    print(f"   胜率: {best['win_rate']:.1f}%")
    print(f"   决策阈值: {best['decision_threshold']}")
    print(f"   杠杆: {best['leverage']}x | 仓位: {best['position']*100:.0f}%")
    print(f"   RSI: {best['rsi_buy']}/{best['rsi_sell']} | BB: {best['bb_buy']}/{best['bb_sell']}")
    print(f"   止盈: {best['take_profit']*100:.0f}% | 止损: {best['stop_loss']*100:.1f}%")

with open('/tmp/g12_v6_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("\n✅ Hermes G12 v6 完成!")
