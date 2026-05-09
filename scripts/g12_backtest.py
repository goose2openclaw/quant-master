#!/usr/bin/env python3
"""G12 30天回测"""
import requests, time, json, numpy as np

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BNB','AVAX','MATIC']

def get_klines(sym, days=30):
    end = int(time.time()*1000)
    start = end - days*86400*1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit=720'
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

def get_macd(prices):
    if len(prices) < 26: return 0
    ema12 = np.mean(prices[-12:])
    ema26 = np.mean(prices[-26:])
    return ema12 - ema26

def simulate(initial_capital, price_data, cfg):
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 100]
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
            macd = get_macd(prices)
            
            # G12 决策值
            decision = 0
            decision += 0.25 * (50 - min(rsi, 50)) / 50
            decision += 0.20 * (100 - bb_pos) / 100
            decision += 0.20 * (macd / (d['close'] * 0.01))
            
            # 买入
            buy = False
            if cfg['mode'] == 'normal':
                buy = rsi < cfg['rsi_buy'] or bb_pos < cfg['bb_buy']
            else:
                buy = rsi < cfg['rsi_buy'] and bb_pos < cfg['bb_buy']
            
            if buy and capital > 10 and decision > cfg['decision_threshold']:
                invest = capital * cfg['position_ratio']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    entry_prices[c] = d['close']
                    trades.append({'type':'BUY','coin':c,'price':d['close']})
            
            # 卖出
            if positions[c] > 0:
                pnl = (d['close'] - entry_prices[c]) / entry_prices[c]
                sell = False
                if cfg['mode'] == 'normal':
                    sell = rsi > cfg['rsi_sell'] or bb_pos > cfg['bb_sell']
                else:
                    sell = rsi > cfg['rsi_sell'] and bb_pos > cfg['bb_sell']
                
                if pnl >= cfg['take_profit'] or pnl <= -cfg['stop_loss']:
                    sell = True
                
                if sell:
                    revenue = positions[c] * d['close'] * 0.999
                    capital += revenue
                    positions[c] = 0
                    entry_prices[c] = 0
                    trades.append({'type':'SELL','coin':c,'pnl':pnl})
    
    final_prices = {c: price_data[c][-1]['close'] for c in valid_coins}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in valid_coins)
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    sells = [t for t in trades if t['type'] == 'SELL']
    wins = sum(1 for t in sells if t.get('pnl', 0) > 0)
    win_rate = wins / len(sells) * 100 if sells else 0
    
    return {'return': total_return, 'win_rate': win_rate, 'total_trades': len(trades), 'wins': wins, 'losses': len(sells)-wins}

print("="*70)
print("G12 30天回测")
print("="*70)

print("\n【获取数据】")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', 30)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

configs = [
    {'name':'G12-普通','mode':'normal','rsi_period':7,'rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.30,'take_profit':0.10,'stop_loss':0.04,'decision_threshold':0.6},
    {'name':'G12-保守','mode':'normal','rsi_period':14,'rsi_buy':30,'rsi_sell':70,'bb_buy':15,'bb_sell':85,'position_ratio':0.25,'take_profit':0.12,'stop_loss':0.05,'decision_threshold':0.65},
    {'name':'G12-激进','mode':'normal','rsi_period':7,'rsi_buy':40,'rsi_sell':60,'bb_buy':25,'bb_sell':75,'position_ratio':0.40,'take_profit':0.08,'stop_loss':0.03,'decision_threshold':0.55},
    {'name':'G12-专家','mode':'expert','rsi_period':7,'rsi_buy':35,'rsi_sell':65,'bb_buy':20,'bb_sell':80,'position_ratio':0.30,'take_profit':0.10,'stop_loss':0.04,'decision_threshold':0.6},
    {'name':'G12-专家保守','mode':'expert','rsi_period':14,'rsi_buy':30,'rsi_sell':70,'bb_buy':15,'bb_sell':85,'position_ratio':0.25,'take_profit':0.12,'stop_loss':0.05,'decision_threshold':0.65},
    {'name':'G12-专家激进','mode':'expert','rsi_period':7,'rsi_buy':40,'rsi_sell':60,'bb_buy':25,'bb_sell':75,'position_ratio':0.40,'take_profit':0.08,'stop_loss':0.03,'decision_threshold':0.55},
]

results = []
print(f"\n【执行{len(configs)}种配置回测】")
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    if stats:
        results.append({**cfg, **stats})
        print(f"  {cfg['name']:14} RSI:{cfg['rsi_buy']}/{cfg['rsi_sell']} 仓:{cfg['position_ratio']*100:.0f}% → 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}% 交易:{stats['total_trades']}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【G12 回测结果】")
print("="*70)

normal = [r for r in results if '普通' in r['name']]
expert = [r for r in results if '专家' in r['name']]

print(f"\n{'配置':16} {'RSI':8} {'仓位':6} {'止盈':6} {'止损':6} {'收益':10} {'胜率':7} {'交易':6}")
print("-"*70)
for r in normal:
    print(f"{r['name']:16} {r['rsi_buy']}/{r['rsi_sell']:5} {r['position_ratio']*100:5.0f}% {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['total_trades']:5d}")

print("\n" + "="*70)
print("【专家模式】")
print("="*70)
for r in expert:
    print(f"{r['name']:16} {r['rsi_buy']}/{r['rsi_sell']:5} {r['position_ratio']*100:5.0f}% {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['total_trades']:5d}")

best = results[0] if results else None
if best:
    print(f"\n最优配置: {best['name']} 收益:{best['return']:+.2f}% 胜率:{best['win_rate']:.1f}%")

with open('/tmp/g12_backtest.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("\n✅ G12 回测完成!")
