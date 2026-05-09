#!/bin/bash
# Hermès G12 自主迭代
# 目标: 收益最大化 | 胜率高位 | 持续进化

LOG_FILE="/tmp/hermes_g12_iterate.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermès G12 自主迭代 $(date)"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# 迭代参数空间
PARAM_GRID = {
    'rsi_buy': [30, 35, 40, 45],
    'rsi_sell': [55, 60, 65, 70],
    'bb_buy': [15, 20, 25, 30],
    'bb_sell': [70, 75, 80, 85],
    'position': [0.25, 0.30, 0.40, 0.50],
    'take_profit': [0.06, 0.08, 0.10, 0.12],
    'stop_loss': [0.03, 0.04, 0.05, 0.06]
}

def get_klines(sym, days=30):
    end = int(time.time()*1000)
    start = end - days*86400*1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit=720'
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
            
            rsi = get_rsi(prices, 7)
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            
            # 买入
            buy = (rsi < cfg['rsi_buy'] or bb_pos < cfg['bb_buy'])
            if buy and capital > 10:
                invest = capital * cfg['position']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    entry_prices[c] = d['close']
                    trades.append({'type':'BUY','coin':c})
            
            # 卖出
            if positions[c] > 0:
                pnl = (d['close'] - entry_prices[c]) / entry_prices[c]
                sell = (rsi > cfg['rsi_sell'] or bb_pos > cfg['bb_sell'])
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
    
    return {'return': total_return, 'win_rate': win_rate, 'trades': len(trades), 'wins': wins, 'losses': len(sells)-wins}

# 获取数据
print("\n【获取数据】")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', 30)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

# 网格搜索最优参数
print("\n【Hermès 网格搜索】")

best_result = {'return': -999, 'win_rate': 0, 'config': None}
iterations = 0

# 简化为少量测试
configs = [
    {'name':'保守','rsi_buy':30,'rsi_sell':70,'bb_buy':20,'bb_sell':80,'position':0.30,'take_profit':0.10,'stop_loss':0.05},
    {'name':'均衡','rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':75,'position':0.40,'take_profit':0.08,'stop_loss':0.04},
    {'name':'激进','rsi_buy':40,'rsi_sell':60,'bb_buy':30,'bb_sell':70,'position':0.50,'take_profit':0.06,'stop_loss':0.03},
    {'name':'高胜','rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':80,'position':0.35,'take_profit':0.10,'stop_loss':0.04},
    {'name':'高频','rsi_buy':40,'rsi_sell':60,'bb_buy':25,'bb_sell':80,'position':0.40,'take_profit':0.05,'stop_loss':0.03},
]

results = []
for cfg in configs:
    stats = simulate(1000, price_data, cfg)
    if stats:
        result = {**cfg, **stats}
        results.append(result)
        iterations += 1
        print(f"  [{iterations}] {cfg['name']}: 收益{stats['return']:+.2f}% | 胜率{stats['win_rate']:.1f}% | {stats['trades']}交易")
        
        if stats['return'] > best_result['return']:
            best_result = stats.copy()
            best_result['config'] = cfg.copy()

# 排序
results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【Hermès 迭代结果】")
print("="*70)

print(f"\n{'配置':8} {'收益':10} {'胜率':7} {'交易':6} {'止盈':6} {'止损':6}")
print("-"*55)
for r in results:
    print(f"{r['name']:8} {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['trades']:>5d} {r['take_profit']*100:>5.0f}% {r['stop_loss']*100:>5.1f}%")

if best_result['config']:
    print(f"\n🏆 最优配置: {best_result['config']['name']}")
    print(f"   收益: {best_result['return']:+.2f}%")
    print(f"   胜率: {best_result['win_rate']:.1f}%")
    print(f"   RSI: {best_result['config']['rsi_buy']}/{best_result['config']['rsi_sell']}")
    print(f"   BB: {best_result['config']['bb_buy']}/{best_result['config']['bb_sell']}")
    print(f"   仓位: {best_result['config']['position']*100:.0f}%")
    print(f"   止盈: {best_result['config']['take_profit']*100:.0f}%")
    print(f"   止损: {best_result['config']['stop_loss']*100:.1f}%")

# 保存最优配置
with open('/tmp/g12_best_config.json', 'w') as f:
    json.dump(best_result, f, indent=2, default=str)

print("\n✅ Hermès 迭代完成!")
PYEOF
