#!/usr/bin/env python3
"""
GBrain v1.0 - 全面深刻迭代
目标: 月收益100%+
"""
import requests, time, json, numpy as np
from itertools import product
from datetime import datetime

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

def get_stoch(klines, period=14):
    if len(klines) < period+1: return 50
    highs = [k['high'] for k in klines[-period:]]
    lows = [k['low'] for k in klines[-period:]]
    close = klines[-1]['close']
    k = 100 * (close - min(lows)) / (max(highs) - min(lows)) if max(highs) > min(lows) else 50
    return k

def get_adx(klines, period=14):
    if len(klines) < period+1: return 0
    # Simplified ADX
    closes = [k['close'] for k in klines]
    price_diff = np.diff(closes)
    plus_dm = np.where(price_diff > 0, price_diff, 0)
    minus_dm = np.where(price_diff < 0, -price_diff, 0)
    adx = min(np.mean(plus_dm[-period:]) / (np.mean(plus_dm[-period:]) + np.mean(minus_dm[-period:])) * 100, 100) if np.sum(plus_dm[-period:]) + np.sum(minus_dm[-period:]) > 0 else 0
    return adx

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
        history.append({'portfolio': total})
        
        for c in valid_coins:
            d = day_data[c]
            klines = price_data[c][:day_idx+1]
            prices = [k['close'] for k in klines]
            
            bb_low, bb_mid, bb_high = np.mean(prices[-20:]) - 2*np.std(prices[-20:]), np.mean(prices[-20:]), np.mean(prices[-20:]) + 2*np.std(prices[-20:])
            bb_pos = bollinger_pos(d['close'], bb_low, bb_high)
            rsi = get_rsi(prices, cfg['rsi_period'])
            stoch = get_stoch(klines, cfg['stoch_period'])
            adx = get_adx(klines)
            
            cur_qty = positions[c]
            
            # 多重买入信号
            buy_score = 0
            buy_reasons = []
            
            # RSI超卖
            if rsi < cfg['rsi_oversold']:
                buy_score += cfg['rsi_weight']
                buy_reasons.append(f'RSI={rsi:.0f}<{cfg["rsi_oversold"]}')
            
            # 布林超卖
            if bb_pos < cfg['bb_oversold']:
                buy_score += cfg['bb_weight']
                buy_reasons.append(f'BB={bb_pos:.0f}<{cfg["bb_oversold"]}')
            
            # Stochastic超卖
            if stoch < cfg['stoch_oversold']:
                buy_score += cfg['stoch_weight']
                buy_reasons.append(f'Stoch={stoch:.0f}<{cfg["stoch_oversold"]}')
            
            # ADX趋势确认
            if adx > cfg['adx_min']:
                buy_score += cfg['adx_weight']
                buy_reasons.append(f'ADX={adx:.0f}>{cfg["adx_min"]}')
            
            # 买入执行
            if buy_score >= cfg['buy_threshold'] and capital > 10:
                invest = capital * cfg['position_size']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    trades.append({'type':'BUY','coin':c,'price':d['close'],'score':buy_score})
            
            # 多重卖出信号
            sell_score = 0
            if cur_qty > 0:
                # RSI超买
                if rsi > cfg['rsi_overbought']:
                    sell_score += cfg['rsi_weight']
                
                # 布林超买
                if bb_pos > cfg['bb_overbought']:
                    sell_score += cfg['bb_weight']
                
                # Stochastic超买
                if stoch > cfg['stoch_overbought']:
                    sell_score += cfg['stoch_weight']
                
                # 止盈止损
                entry = [t['price'] for t in reversed(trades) if t['coin']==c and t['type']=='BUY']
                if entry:
                    pnl = (d['close'] - entry[0]) / entry[0]
                    if pnl >= cfg['take_profit']:
                        sell_score += cfg['tp_weight']
                    elif pnl <= -cfg['stop_loss']:
                        sell_score += cfg['sl_weight']
                
                if sell_score >= cfg['sell_threshold']:
                    qty = cur_qty * cfg['sell_ratio']
                    revenue = qty * d['close'] * 0.999
                    capital += revenue
                    positions[c] -= qty
                    trades.append({'type':'SELL','coin':c,'price':d['close'],'score':sell_score,'pnl':pnl})
    
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
print("GBrain v1.0 - 全面深刻迭代")
print("目标: 月收益100%+")
print("="*70)

print("\n【获取数据】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', 30)
    if data: price_data[c] = data; print(f"{len(data)}条")
    time.sleep(0.2)

# GBrain配置矩阵 - 激进参数
configs = [
    # 高频交易配置
    {'name':'高频激进','rsi_period':7,'stoch_period':9,'rsi_oversold':25,'rsi_overbought':75,'bb_oversold':15,'bb_overbought':85,'stoch_oversold':20,'stoch_overbought':80,'adx_min':15,'rsi_weight':3,'bb_weight':2,'stoch_weight':2,'adx_weight':1,'buy_threshold':5,'sell_threshold':4,'position_size':0.50,'sell_ratio':0.8,'take_profit':0.15,'stop_loss':0.05,'tp_weight':5,'sl_weight':5},
    {'name':'高频平衡','rsi_period':7,'stoch_period':9,'rsi_oversold':30,'rsi_overbought':70,'bb_oversold':20,'bb_overbought':80,'stoch_oversold':25,'stoch_overbought':75,'adx_min':15,'rsi_weight':3,'bb_weight':2,'stoch_weight':2,'adx_weight':1,'buy_threshold':5,'sell_threshold':4,'position_size':0.45,'sell_ratio':0.7,'take_profit':0.12,'stop_loss':0.04,'tp_weight':5,'sl_weight':5},
    {'name':'高频保守','rsi_period':7,'stoch_period':9,'rsi_oversold':35,'rsi_overbought':65,'bb_oversold':25,'bb_overbought':75,'stoch_oversold':30,'stoch_overbought':70,'adx_min':15,'rsi_weight':3,'bb_weight':2,'stoch_weight':2,'adx_weight':1,'buy_threshold':5,'sell_threshold':4,'position_size':0.40,'sell_ratio':0.6,'take_profit':0.10,'stop_loss':0.03,'tp_weight':5,'sl_weight':5},
    # 多重信号配置
    {'name':'多重共振','rsi_period':14,'stoch_period':14,'rsi_oversold':30,'rsi_overbought':70,'bb_oversold':20,'bb_overbought':80,'stoch_oversold':20,'stoch_overbought':80,'adx_min':20,'rsi_weight':2,'bb_weight':2,'stoch_weight':2,'adx_weight':2,'buy_threshold':6,'sell_threshold':5,'position_size':0.50,'sell_ratio':0.7,'take_profit':0.12,'stop_loss':0.04,'tp_weight':5,'sl_weight':5},
    {'name':'三重共振','rsi_period':14,'stoch_period':14,'rsi_oversold':25,'rsi_overbought':75,'bb_oversold':15,'bb_overbought':85,'stoch_oversold':15,'stoch_overbought':85,'adx_min':20,'rsi_weight':3,'bb_weight':3,'stoch_weight':3,'adx_weight':1,'buy_threshold':7,'sell_threshold':6,'position_size':0.55,'sell_ratio':0.8,'take_profit':0.15,'stop_loss':0.05,'tp_weight':5,'sl_weight':5},
    # 超级激进配置
    {'name':'超级激进','rsi_period':7,'stoch_period':5,'rsi_oversold':20,'rsi_overbought':80,'bb_oversold':10,'bb_overbought':90,'stoch_oversold':15,'stoch_overbought':85,'adx_min':10,'rsi_weight':4,'bb_weight':3,'stoch_weight':3,'adx_weight':1,'buy_threshold':8,'sell_threshold':7,'position_size':0.60,'sell_ratio':0.9,'take_profit':0.20,'stop_loss':0.06,'tp_weight':5,'sl_weight':5},
    {'name':'极限高频','rsi_period':5,'stoch_period':5,'rsi_oversold':25,'rsi_overbought':75,'bb_oversold':15,'bb_overbought':85,'stoch_oversold':20,'stoch_overbought':80,'adx_min':10,'rsi_weight':5,'bb_weight':3,'stoch_weight':3,'adx_weight':1,'buy_threshold':9,'sell_threshold':8,'position_size':0.65,'sell_ratio':0.9,'take_profit':0.18,'stop_loss':0.05,'tp_weight':5,'sl_weight':5},
    # 稳健配置
    {'name':'稳健高频','rsi_period':7,'stoch_period':7,'rsi_oversold':30,'rsi_overbought':70,'bb_oversold':20,'bb_overbought':80,'stoch_oversold':25,'stoch_overbought':75,'adx_min':15,'rsi_weight':3,'bb_weight':2,'stoch_weight':2,'adx_weight':1,'buy_threshold':5,'sell_threshold':4,'position_size':0.40,'sell_ratio':0.6,'take_profit':0.10,'stop_loss':0.03,'tp_weight':5,'sl_weight':5},
]

results = []

print(f"\n【执行{len(configs)}种配置回测】")
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    if stats:
        results.append({**cfg, **stats})
        print(f"  {cfg['name']:12} 仓:{cfg['position_size']*100:.0f}% 买:{cfg['buy_threshold']} 卖:{cfg['sell_threshold']} -> 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}% 交易:{stats['total_trades']}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【GBrain迭代结果】")
print("="*70)
print(f"\n{'配置':14} {'仓位':6} {'买阀值':6} {'卖阀值':6} {'止盈':6} {'止损':6} {'收益':9} {'胜率':7} {'交易':6}")
print("-"*75)
for r in results:
    print(f"{r['name']:14} {r['position_size']*100:5.0f}% {r['buy_threshold']:6d} {r['sell_threshold']:6d} {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+8.2f}% {r['win_rate']:>5.1f}% {r['total_trades']:5d}")

# 提取最优配置
if results:
    best = results[0]
    print(f"""
======================================================================
【GBrain最优配置】
======================================================================
配置: {best['name']}
收益: {best['return']:>+8.2f}% 胜率:{best['win_rate']:.1f}% 交易:{best['total_trades']}
仓位:{best['position_size']*100:.0f}% 止盈:{best['take_profit']*100:.0f}% 止损:{best['stop_loss']*100:.1f}%
买入阀值:{best['buy_threshold']} 卖出阀值:{best['sell_threshold']}
RSI周期:{best['rsi_period']} Stochastic周期:{best['stoch_period']}
ADX阈值:{best['adx_min']}
======================================================================
""")

# 达到100%目标检查
high_return_configs = [r for r in results if r['return'] >= 100]
if high_return_configs:
    print(f"🎉 找到{len(high_return_configs)}种配置达到100%目标!")
    for hrc in high_return_configs:
        print(f"  {hrc['name']}: {hrc['return']:+.2f}%")

with open('/tmp/backtest_gbrain.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ GBrain迭代完成!")
