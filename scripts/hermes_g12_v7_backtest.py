#!/usr/bin/env python3
"""
Hermes G12 v7 回测 - 高收益策略版
目标: 400%+/月
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

def simulate_v7(initial_capital, price_data, cfg):
    """高收益策略模拟"""
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 100]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    entry_prices = {c: 0 for c in valid_coins}
    short_qtys = {c: 0 for c in valid_coins}
    short_entries = {c: 0 for c in valid_coins}
    martingale_multiplier = {c: 1.0 for c in valid_coins}
    loss_count = {c: 0 for c in valid_coins}
    trades = []
    
    leverage = cfg.get('leverage', 1)
    position_ratio = cfg.get('position', 0.3)
    
    # Scalping配置
    scalp_tp = cfg.get('scalp_tp', 0.005)   # 0.5%
    scalp_sl = cfg.get('scalp_sl', 0.002)     # 0.2%
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            closes = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            
            rsi = get_rsi(closes, 7)
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            macd = get_macd(closes)
            
            # 决策值
            decision = 0
            decision += 0.30 * (50 - min(rsi, 50)) / 50
            decision += 0.25 * (100 - bb_pos) / 100
            decision += 0.20 * min(macd / (d['close'] * 0.005), 1)
            
            # ========== 高频Scalping ==========
            if cfg.get('scalping') and positions[c] == 0 and short_qtys[c] == 0:
                scalp_signal = False
                # 布林触及+ RSI极端
                if bb_pos < 20 and rsi < 30:
                    scalp_signal = True
                elif bb_pos > 80 and rsi > 70:
                    scalp_signal = True
                
                if scalp_signal and capital > 10:
                    invest = capital * position_ratio * leverage * martingale_multiplier[c]
                    qty = invest / d['close']
                    entry_fee = invest * 0.001
                    capital -= entry_fee
                    positions[c] = qty
                    entry_prices[c] = d['close']
                    trades.append({'type':'SCALP_OPEN','coin':c,'price':d['close'],'strategy':'scalping'})
            
            # ========== Scalping平仓 ==========
            if positions[c] > 0:
                pnl_ratio = (d['close'] - entry_prices[c]) / entry_prices[c] * leverage
                
                # 止盈止损
                if pnl_ratio >= scalp_tp or pnl_ratio <= -scalp_sl:
                    pnl = (d['close'] - entry_prices[c]) * positions[c] * leverage
                    exit_fee = positions[c] * d['close'] * 0.001
                    capital += pnl - exit_fee
                    positions[c] = 0
                    entry_prices[c] = 0
                    
                    # Martingale更新
                    if pnl > 0:
                        loss_count[c] = 0
                        martingale_multiplier[c] = 1.0
                    else:
                        loss_count[c] += 1
                        martingale_multiplier[c] = min(martingale_multiplier[c] * cfg.get('martingale_mult', 2.0), 4.0)
                    
                    trades.append({'type':'SCALP_CLOSE','coin':c,'pnl_ratio':pnl_ratio,'strategy':'scalping'})
            
            # ========== 做空 ==========
            if short_qtys[c] == 0 and positions[c] == 0:
                short = bb_pos > 85 and rsi > 70
                if short and capital > 20:
                    qty = (capital * position_ratio * leverage) / d['close']
                    entry_fee = qty * d['close'] * 0.001
                    capital -= entry_fee
                    short_qtys[c] = qty
                    short_entries[c] = d['close']
                    trades.append({'type':'SHORT_OPEN','coin':c,'price':d['close']})
            
            # ========== 做空平仓 ==========
            if short_qtys[c] > 0:
                pnl_ratio = (short_entries[c] - d['close']) / short_entries[c] * leverage
                
                cover = pnl_ratio >= scalp_tp or pnl_ratio <= -scalp_sl or rsi < 30
                
                if cover:
                    pnl = (short_entries[c] - d['close']) * short_qtys[c] * leverage
                    exit_fee = short_qtys[c] * d['close'] * 0.001
                    capital += pnl - exit_fee
                    short_qtys[c] = 0
                    short_entries[c] = 0
                    trades.append({'type':'SHORT_CLOSE','coin':c,'pnl_ratio':pnl_ratio})
    
    final_value = capital
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    closed = [t for t in trades if t['type'] in ['SCALP_CLOSE','SHORT_CLOSE']]
    wins = sum(1 for t in closed if t.get('pnl_ratio', 0) > 0)
    win_rate = wins / len(closed) * 100 if closed else 0
    
    return {'return': total_return, 'win_rate': win_rate, 'trades': len(trades), 'wins': wins, 'losses': len(closed)-wins}

print("="*70)
print("Hermes G12 v7 回测 - 高收益策略版")
print("目标: 400%+/月")
print("="*70)

print("\n获取数据")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

# 高收益配置
configs = [
    # Scalping基础
    {'name':'Scalp-2x','scalping':True,'leverage':2,'position':0.5,'scalp_tp':0.005,'scalp_sl':0.002,'martingale_mult':1.5},
    {'name':'Scalp-3x','scalping':True,'leverage':3,'position':0.4,'scalp_tp':0.005,'scalp_sl':0.002,'martingale_mult':1.5},
    # Martingale加强
    {'name':'Mart-2x','scalping':True,'leverage':2,'position':0.5,'scalp_tp':0.005,'scalp_sl':0.003,'martingale_mult':2.0},
    {'name':'Mart-3x','scalping':True,'leverage':3,'position':0.4,'scalp_tp':0.005,'scalp_sl':0.002,'martingale_mult':2.0},
    # 小止盈高频
    {'name':'高频-2x','scalping':True,'leverage':2,'position':0.5,'scalp_tp':0.003,'scalp_sl':0.001,'martingale_mult':1.5},
    {'name':'高频-3x','scalping':True,'leverage':3,'position':0.4,'scalp_tp':0.003,'scalp_sl':0.001,'martingale_mult':2.0},
    # 激进配置
    {'name':'激进-2x','scalping':True,'leverage':2,'position':0.6,'scalp_tp':0.004,'scalp_sl':0.002,'martingale_mult':2.0},
    {'name':'激进-3x','scalping':True,'leverage':3,'position':0.5,'scalp_tp':0.004,'scalp_sl':0.002,'martingale_mult':2.0},
]

results = []
print(f"\n执行{len(configs)}种配置回测")
for cfg in configs:
    stats = simulate_v7(1000, price_data, cfg)
    if stats:
        result = {**cfg, **stats}
        results.append(result)
        mark = "⭐" if stats['return'] > 100 else ""
        print(f"  {cfg['name']:12} 止:{cfg['scalp_tp']*100:.1f}%损:{cfg['scalp_sl']*100:.1f}%马:{cfg['martingale_mult']} → 收益:{stats['return']:>+9.2f}% 胜率:{stats['win_rate']:>5.1f}% {mark}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("G12 v7 高收益回测结果")
print("="*70)

print(f"\n{'配置':12} {'止盈':6} {'止损':6} {'马丁':5} {'收益':10} {'胜率':7} {'交易':6}")
print("-"*60)
for r in results:
    print(f"{r['name']:12} {r['scalp_tp']*100:5.1f}% {r['scalp_sl']*100:5.1f}% {r['martingale_mult']:4.1f} {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['trades']:>5d}")

best = results[0] if results else None
if best:
    print(f"\n🏆 最优: {best['name']}")
    print(f"   收益: {best['return']:+.2f}%")
    print(f"   胜率: {best['win_rate']:.1f}%")
    print(f"   止盈: {best['scalp_tp']*100:.1f}% | 止损: {best['scalp_sl']*100:.1f}%")
    print(f"   马丁: {best['martingale_mult']}x")

with open('/tmp/g12_v7_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("\n✅ G12 v7 回测完成!")
