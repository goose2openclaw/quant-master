#!/usr/bin/env python3
"""QuantDinger蒸馏策略 - 30天回测"""
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

def bollinger_bands(prices, period=20):
    if len(prices) < period: return prices[-1], prices[-1], prices[-1]
    ma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    return ma - 2*std, ma, ma + 2*std

def bollinger_pos(price, bb_low, bb_high):
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def get_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow+signal: return 0, 0, 0
    ema_fast = np.mean(prices[-fast:])  # simplified
    ema_slow = np.mean(prices[-slow:])
    macd = ema_fast - ema_slow
    signal_line = macd * 0.9  # simplified
    return macd, signal_line, macd - signal_line

def get_atr(klines, period=14):
    if len(klines) < period+1: return 0
    trs = []
    for i in range(1, min(period+1, len(klines))):
        high = klines[i]['high']
        low = klines[i]['low']
        prev_close = klines[i-1]['close']
        tr = max(high-low, abs(high-prev_close), abs(low-prev_close))
        trs.append(tr)
    return np.mean(trs) if trs else 0

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
            klines = price_data[c][:day_idx+1]
            prices = [k['close'] for k in klines]
            
            # QuantDinger核心指标
            bb_low, bb_mid, bb_high = bollinger_bands(prices, cfg['bb_period'])
            bb_pos = bollinger_pos(d['close'], bb_low, bb_high)
            rsi = get_rsi(prices, cfg['rsi_period'])
            macd, signal, histogram = get_macd(prices)
            atr = get_atr(klines, cfg['atr_period'])
            
            cur_qty = positions[c]
            
            # QuantDinger买入信号
            buy_signal = False
            
            # 信号1: RSI超卖
            if rsi < cfg['rsi_oversold']:
                buy_signal = True
            
            # 信号2: 布林下轨
            if bb_pos < cfg['bb_oversold']:
                buy_signal = True
            
            # 信号3: MACD金叉
            if cfg['use_macd'] and histogram > 0:
                buy_signal = True
            
            # 信号4: 价格触及布林下轨
            if d['close'] <= bb_low * (1 + cfg['bb_touch']):
                buy_signal = True
            
            # 执行买入
            if buy_signal and capital > 10:
                invest = capital * cfg['position_size']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    trades.append({'type':'BUY','coin':c,'price':d['close'],'rsi':rsi,'bb_pos':bb_pos})
            
            # QuantDinger卖出信号
            sell_signal = False
            
            # 信号1: RSI超买
            if cur_qty > 0 and rsi > cfg['rsi_overbought']:
                sell_signal = True
            
            # 信号2: 布林上轨
            if cur_qty > 0 and bb_pos > cfg['bb_overbought']:
                sell_signal = True
            
            # 信号3: MACD死叉
            if cfg['use_macd'] and cur_qty > 0 and histogram < 0:
                sell_signal = True
            
            # 信号4: 止盈止损
            if cur_qty > 0:
                entry = [t['price'] for t in reversed(trades) if t['coin']==c and t['type']=='BUY']
                if entry:
                    pnl = (d['close'] - entry[0]) / entry[0]
                    if pnl >= cfg['take_profit'] or pnl <= -cfg['stop_loss']:
                        sell_signal = True
            
            if sell_signal:
                qty = cur_qty * cfg['sell_ratio']
                revenue = qty * d['close'] * 0.999
                capital += revenue
                positions[c] -= qty
                trades.append({'type':'SELL','coin':c,'price':d['close'],'rsi':rsi,'bb_pos':bb_pos})
    
    final_prices = {c: price_data[c][-1]['close'] for c in valid_coins}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in valid_coins)
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    sells = [t for t in trades if t['type'] == 'SELL']
    wins = sum(1 for t in sells if t.get('price', 0) > 0)
    win_rate = wins / len(sells) * 100 if sells else 0
    
    avg_used = np.mean([h['used'] for h in history]) * 100 if history else 0
    max_used = max([h['used'] for h in history]) * 100 if history else 0
    
    return {'return': total_return, 'win_rate': win_rate,
            'capital_usage_avg': avg_used, 'capital_usage_max': max_used,
            'total_trades': len(trades), 'wins': wins, 'losses': len(sells)-wins}

print("="*70)
print("QuantDinger蒸馏策略 - 30天回测")
print("="*70)

print("\n【获取数据】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', 30)
    if data: price_data[c] = data; print(f"{len(data)}条")
    time.sleep(0.2)

# QuantDinger配置矩阵
configs = [
    {'name':'QD标准','bb_period':20,'rsi_period':14,'atr_period':14,'rsi_oversold':30,'rsi_overbought':70,'bb_oversold':20,'bb_overbought':80,'bb_touch':0.01,'use_macd':True,'position_size':0.25,'sell_ratio':0.5,'take_profit':0.08,'stop_loss':0.03},
    {'name':'QD激进','bb_period':20,'rsi_period':14,'atr_period':14,'rsi_oversold':25,'rsi_overbought':75,'bb_oversold':15,'bb_overbought':85,'bb_touch':0.005,'use_macd':True,'position_size':0.35,'sell_ratio':0.6,'take_profit':0.10,'stop_loss':0.025},
    {'name':'QD保守','bb_period':25,'rsi_period':14,'atr_period':14,'rsi_oversold':35,'rsi_overbought':65,'bb_oversold':25,'bb_overbought':75,'bb_touch':0.02,'use_macd':False,'position_size':0.20,'sell_ratio':0.4,'take_profit':0.06,'stop_loss':0.04},
    {'name':'QD双B','bb_period':20,'rsi_period':7,'atr_period':14,'rsi_oversold':30,'rsi_overbought':70,'bb_oversold':20,'bb_overbought':80,'bb_touch':0.01,'use_macd':True,'position_size':0.30,'sell_ratio':0.5,'take_profit':0.08,'stop_loss':0.03},
    {'name':'QD长RSI','bb_period':20,'rsi_period':21,'atr_period':14,'rsi_oversold':35,'rsi_overbought':65,'bb_oversold':20,'bb_overbought':80,'bb_touch':0.01,'use_macd':True,'position_size':0.30,'sell_ratio':0.5,'take_profit':0.10,'stop_loss':0.03},
    {'name':'QD无MACD','bb_period':20,'rsi_period':14,'atr_period':14,'rsi_oversold':30,'rsi_overbought':70,'bb_oversold':20,'bb_overbought':80,'bb_touch':0.01,'use_macd':False,'position_size':0.30,'sell_ratio':0.5,'take_profit':0.08,'stop_loss':0.03},
]

results = []

print("\n【执行回测】")
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    if stats:
        results.append({**cfg, **stats})
        print(f"  {cfg['name']:12} RSI:{cfg['rsi_oversold']}/{cfg['rsi_overbought']} BB:{cfg['bb_oversold']}/{cfg['bb_overbought']} 仓:{cfg['position_size']*100:.0f}% -> 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}%")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【结果矩阵 - QuantDinger蒸馏策略】")
print("="*70)
print(f"\n{'配置':14} {'RSI买':6} {'RSI卖':6} {'BB买':5} {'BB卖':5} {'MACD':5} {'仓位':6} {'收益':9} {'胜率':7} {'资金(均/最大)':18} {'交易':6}")
print("-"*95)
for r in results:
    macd = 'Yes' if r['use_macd'] else 'No'
    print(f"{r['name']:14} {r['rsi_oversold']:6d} {r['rsi_overbought']:6d} {r['bb_oversold']:5d} {r['bb_overbought']:5d} {macd:5} {r['position_size']*100:5.0f}% {r['return']:>+8.2f}% {r['win_rate']:>5.1f}% {r['capital_usage_avg']:>5.1f}%/{r['capital_usage_max']:>5.1f}% {r['total_trades']:5d}")

if results:
    best = results[0]
    print(f"""
======================================================================
【最优QuantDinger配置】
======================================================================
配置: {best['name']}
RSI: {best['rsi_oversold']}/{best['rsi_overbought']} 布林: {best['bb_oversold']}/{best['bb_overbought']}
MACD: {'Yes' if best['use_macd'] else 'No'} 仓位:{best['position_size']*100:.0f}%
止盈:{best['take_profit']*100:.0f}% 止损:{best['stop_loss']*100:.1f}%
收益:{best['return']:>+8.2f}% 胜率:{best['win_rate']:.1f}%
资金:{best['capital_usage_avg']:.1f}/{best['capital_usage_max']:.1f}% 交易:{best['total_trades']}
======================================================================
""")

with open('/tmp/backtest_quantdinger.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ QuantDinger回测完成!")
