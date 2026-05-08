#!/usr/bin/env python3
"""
Hermes G12 v16 - 精简版 (核心功能集成)
"""
import requests, time, json, numpy as np
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

CONFIG = {
    'version': 'v16-G12完整版',
    'rsi_buy': 43, 'rsi_sell': 53,
    'bb_buy': 25, 'bb_sell': 75,
    'take_profit': 0.08, 'stop_loss': 0.035,
    'position': 0.35, 'leverage': 3,
    'short_rsi': 70, 'short_bb': 85,
    'decision_threshold': 0.70,
    'rsi_period': 7,
}

def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3]),'open':float(k[1])} for k in r.json()]
    except: return []

def get_24hr(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', proxies=PROXIES, timeout=5)
        d = r.json()
        return {'price':float(d['lastPrice']),'chg':float(d['priceChangePercent']),'high':float(d['highPrice']),'low':float(d['lowPrice'])}
    except: return None

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

def volatility(closes, period=20):
    if len(closes) < period: return 0
    returns = np.diff(closes[-period:]) / closes[-period:-1]
    return np.std(returns) * 100

def detect_spike(klines):
    """插针检测"""
    if len(klines) < 2: return None
    current = klines[-1]
    price = current['close']
    upper_wick = current['high'] - max(price, current['open'])
    lower_wick = min(price, current['open']) - current['low']
    body = abs(price - current['open'])
    if body > 0:
        if upper_wick / body > 3: return {'type': 'upper', 'action': 'short'}
        if lower_wick / body > 3: return {'type': 'lower', 'action': 'long'}
    return None

def sentiment(closes, price):
    sma20 = np.mean(closes[-20:]) if len(closes) >= 20 else price
    return 'BULL' if price > sma20 else 'BEAR'

def simulate_v16(initial_capital, price_data, cfg):
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 100]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    entry_prices = {c: 0 for c in valid_coins}
    short_qtys = {c: 0 for c in valid_coins}
    short_entries = {c: 0 for c in valid_coins}
    trades = []
    equity_curve = [initial_capital]
    
    leverage = cfg.get('leverage', 3)
    position_ratio = cfg.get('position', 0.35)
    decisions = {'long':0,'short':0,'sell':0,'cover':0,'spike':0}
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            closes = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            klines_20 = price_data[c][max(0,day_idx-20):day_idx+1]
            
            rsi = get_rsi(closes, 7)
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            macd = get_macd(closes)
            vol = volatility(closes)
            
            decision = 0.30 * (50 - min(rsi, 50)) / 50
            decision += 0.25 * (100 - bb_pos) / 100
            decision += 0.20 * min(macd / (d['close'] * 0.005), 1)
            
            # 插针捕捉
            spike = detect_spike(klines_20)
            
            # 动态止盈 (波动率调整)
            tp = cfg['take_profit'] * (1.2 if vol > 3 else 0.9)
            
            # ========== 交易逻辑 ==========
            # 插针优先
            if spike and spike['action'] == 'long' and capital > 10 and positions[c] == 0:
                invest = capital * position_ratio * leverage * 1.5
                qty = invest / d['close']
                capital -= invest * 0.001
                positions[c] = qty
                entry_prices[c] = d['close']
                trades.append({'type':'LONG_OPEN','coin':c,'reason':'spike'})
                decisions['spike'] += 1
                decisions['long'] += 1
                continue
            
            if spike and spike['action'] == 'short' and capital > 20 and short_qtys[c] == 0:
                qty = (capital * position_ratio * leverage * 1.5) / d['close']
                capital -= qty * d['close'] * 0.001
                short_qtys[c] = qty
                short_entries[c] = d['close']
                trades.append({'type':'SHORT_OPEN','coin':c,'reason':'spike'})
                decisions['spike'] += 1
                decisions['short'] += 1
                continue
            
            # 标准做多
            buy = (rsi < cfg['rsi_buy'] and bb_pos < cfg['bb_buy'] and decision > cfg['decision_threshold'])
            if buy and capital > 10 and positions[c] == 0 and short_qtys[c] == 0:
                invest = capital * position_ratio * leverage
                qty = invest / d['close']
                capital -= invest * 0.001
                positions[c] = qty
                entry_prices[c] = d['close']
                trades.append({'type':'LONG_OPEN','coin':c,'reason':'g12'})
                decisions['long'] += 1
            
            # 平多
            if positions[c] > 0:
                pnl_ratio = (d['close'] - entry_prices[c]) / entry_prices[c] * leverage
                sell = (rsi > cfg['rsi_sell'] and bb_pos > cfg['bb_sell']) or pnl_ratio >= tp or pnl_ratio <= -cfg['stop_loss']
                if sell:
                    pnl = (d['close'] - entry_prices[c]) * positions[c] * leverage
                    capital += pnl - positions[c] * d['close'] * 0.001
                    positions[c] = 0
                    entry_prices[c] = 0
                    trades.append({'type':'LONG_CLOSE','coin':c,'pnl_ratio':pnl_ratio})
                    decisions['sell'] += 1
            
            # 标准做空
            short = (rsi > cfg['short_rsi'] and bb_pos > cfg['short_bb'])
            if short and capital > 20 and short_qtys[c] == 0 and positions[c] == 0:
                qty = (capital * position_ratio * leverage) / d['close']
                capital -= qty * d['close'] * 0.001
                short_qtys[c] = qty
                short_entries[c] = d['close']
                trades.append({'type':'SHORT_OPEN','coin':c,'reason':'g12'})
                decisions['short'] += 1
            
            # 平空
            if short_qtys[c] > 0:
                pnl_ratio = (short_entries[c] - d['close']) / short_entries[c] * leverage
                cover = (rsi < cfg['rsi_buy'] or bb_pos < cfg['bb_buy']) or pnl_ratio >= tp or pnl_ratio <= -cfg['stop_loss']
                if cover:
                    pnl = (short_entries[c] - d['close']) * short_qtys[c] * leverage
                    capital += pnl - short_qtys[c] * d['close'] * 0.001
                    short_qtys[c] = 0
                    short_entries[c] = 0
                    trades.append({'type':'SHORT_CLOSE','coin':c,'pnl_ratio':pnl_ratio})
                    decisions['cover'] += 1
        
        day_value = capital
        for c in valid_coins:
            day_value += positions[c] * day_data[c]['close']
            day_value += short_qtys[c] * (short_entries[c] - day_data[c]['close'])
        equity_curve.append(day_value)
    
    final_value = capital
    for c in valid_coins:
        final_value += positions[c] * price_data[c][-1]['close']
    
    closed = [t for t in trades if t['type'] in ['LONG_CLOSE','SHORT_CLOSE']]
    wins = sum(1 for t in closed if t.get('pnl_ratio', 0) > 0)
    
    peak = initial_capital
    max_dd = 0
    for v in equity_curve:
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak * 100)
    
    return {
        'return': (final_value - initial_capital) / initial_capital * 100,
        'win_rate': wins / len(closed) * 100 if closed else 0,
        'trades': len(trades), 'wins': wins, 'losses': len(closed) - wins,
        'decisions': decisions, 'max_drawdown': max_dd
    }

# ========== 极限测试 ==========
def stress_test(initial_capital, price_data, cfg):
    print("\n【极限测试】")
    results = {}
    
    # 极端下跌
    print("  📉 极端下跌...")
    stress = {c: price_data[c][-200:].copy() if c in price_data else [] for c in COINS}
    for c in stress:
        for i in range(30):
            idx = len(stress[c]) - 30 + i
            if 0 <= idx < len(stress[c]):
                stress[c][idx]['close'] *= (1 - 0.03 * i)
    r = simulate_v16(initial_capital, stress, cfg)
    results['drop'] = r['return'] if r else 0
    print(f"    → {results['drop']:+.2f}%")
    
    # 极端上涨
    print("  📈 极端上涨...")
    stress = {c: price_data[c][-200:].copy() if c in price_data else [] for c in COINS}
    for c in stress:
        for i in range(30):
            idx = len(stress[c]) - 30 + i
            if 0 <= idx < len(stress[c]):
                stress[c][idx]['close'] *= (1 + 0.025 * i)
    r = simulate_v16(initial_capital, stress, cfg)
    results['rise'] = r['return'] if r else 0
    print(f"    → {results['rise']:+.2f}%")
    
    # 高波动
    print("  ⚡ 高波动...")
    stress = {c: price_data[c][-100:].copy() if c in price_data else [] for c in COINS}
    for c in stress:
        for i in range(len(stress[c])):
            stress[c][i]['close'] *= (1 + np.random.uniform(-0.1, 0.1))
    r = simulate_v16(initial_capital, stress, cfg)
    results['highvol'] = r['return'] if r else 0
    print(f"    → {results['highvol']:+.2f}%")
    
    return results

# ========== 主程序 ==========
print("="*70)
print("Hermes G12 v16 - 完整版 (核心功能集成)")
print("="*70)

print("\n📥 获取数据...")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

# 功能展示
print("\n【新增功能检测】")
for c in ['BTC','ETH','DOGE'][:2]:
    if c not in price_data: continue
    closes = [k['close'] for k in price_data[c][-50:]]
    d = get_24hr(f'{c}USDT')
    if d:
        vol = volatility(closes)
        sent = sentiment(closes, d['price'])
        print(f"  {c}: 波动率={vol:.2f}% 情绪={sent} 价格=${d['price']:.4f}")
    time.sleep(0.1)

# 30天回测
print("\n【30天回测】")
stats = simulate_v16(1000, price_data, CONFIG)
if stats:
    print(f"  总收益: {stats['return']:+.2f}%")
    print(f"  胜率: {stats['win_rate']:.1f}%")
    print(f"  交易: {stats['trades']}笔 (盈:{stats['wins']} 亏:{stats['losses']})")
    print(f"  最大回撤: {stats['max_drawdown']:.1f}%")
    print(f"  决策: 做多{stats['decisions']['long']} 做空{stats['decisions']['short']} 插针{stats['decisions']['spike']}")

# 极限测试
stress = stress_test(1000, price_data, CONFIG)

print("\n【极限测试汇总】")
print(f"  极端下跌: {stress['drop']:+.2f}%")
print(f"  极端上涨: {stress['rise']:+.2f}%")
print(f"  高波动:   {stress['highvol']:+.2f}%")

# 保存
with open('/tmp/g12_v16_results.json', 'w') as f:
    json.dump({'config':CONFIG, 'backtest':stats, 'stress':stress}, f, indent=2, default=str)

print("\n" + "="*70)
print("✅ G12 v16 完整版测试完成!")
print("="*70)
