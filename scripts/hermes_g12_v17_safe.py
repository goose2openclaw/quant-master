#!/usr/bin/env python3
"""
Hermes G12 v17 - 安全版 (加强风控 + 插针限制)
修复: 回撤控制 | 极端保护 | 交易频率限制
"""
import requests, time, json, numpy as np
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

CONFIG = {
    'version': 'v17-G12安全版',
    # G12核心
    'rsi_buy': 43, 'rsi_sell': 53,
    'bb_buy': 25, 'bb_sell': 75,
    'take_profit': 0.06,  # 降低止盈期望
    'stop_loss': 0.025,   # 更严格止损
    'position': 0.25,     # 降低仓位
    'leverage': 2,        # 降低杠杆
    'short_rsi': 70, 'short_bb': 85,
    'decision_threshold': 0.70,
    # 风控
    'max_daily_loss': 0.05,   # 每日最大亏损5%
    'max_position_loss': 0.03, # 单笔最大亏损3%
    'max_spike_ratio': 0.1,   # 插针交易占比≤10%
    'min_trade_interval': 3,   # 最小交易间隔(小时)
}

def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3]),'open':float(k[1])} for k in r.json()]
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

def volatility(closes, period=20):
    if len(closes) < period: return 0
    returns = np.diff(closes[-period:]) / closes[-period:-1]
    return np.std(returns) * 100

def detect_spike(klines):
    """改进的插针检测"""
    if len(klines) < 2: return None
    current = klines[-1]
    price = current['close']
    upper_wick = current['high'] - max(price, current['open'])
    lower_wick = min(price, current['open']) - current['low']
    body = abs(price - current['open'])
    if body > 0:
        if upper_wick / body > 4: return {'type': 'upper', 'action': 'short', 'strength': upper_wick/body}
        if lower_wick / body > 4: return {'type': 'lower', 'action': 'long', 'strength': lower_wick/body}
    return None

def simulate_v17(initial_capital, price_data, cfg):
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
    
    leverage = cfg.get('leverage', 2)
    position_ratio = cfg.get('position', 0.25)
    
    decisions = {'long':0,'short':0,'sell':0,'cover':0,'spike':0}
    last_trade_time = {c: -999 for c in valid_coins}
    daily_loss = 0
    last_day = 0
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        # 每日重置亏损计数
        if day_idx % 24 == 0 and day_idx > 0:
            daily_loss = 0
        
        # ========== 风控检查 ==========
        # 触发日止损,停止交易一天
        if daily_loss < -cfg['max_daily_loss']:
            equity_curve.append(capital)
            continue
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            closes = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            klines_20 = price_data[c][max(0,day_idx-20):day_idx+1]
            
            rsi = get_rsi(closes, 7)
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            macd = get_macd(closes)
            
            decision = 0.30 * (50 - min(rsi, 50)) / 50
            decision += 0.25 * (100 - bb_pos) / 100
            decision += 0.20 * min(macd / (d['close'] * 0.005), 1)
            
            # 交易间隔检查
            if day_idx - last_trade_time.get(c, -999) < cfg['min_trade_interval']:
                continue
            
            # 插针检测 (限制使用)
            spike = detect_spike(klines_20)
            spike_used = False
            
            # ========== 交易逻辑 ==========
            # 插针捕捉 (仅在极端情况下,且不超过总交易10%)
            if spike and spike['strength'] > 5 and decisions['spike'] < len(trades) * cfg['max_spike_ratio']:
                if spike['action'] == 'long' and capital > 15 and positions[c] == 0:
                    invest = capital * position_ratio * leverage
                    qty = invest / d['close']
                    capital -= invest * 0.001
                    positions[c] = qty
                    entry_prices[c] = d['close']
                    last_trade_time[c] = day_idx
                    trades.append({'type':'LONG_OPEN','coin':c,'reason':'spike','price':d['close'],'day':day_idx})
                    decisions['spike'] += 1
                    decisions['long'] += 1
                    continue
                
                if spike['action'] == 'short' and capital > 20 and short_qtys[c] == 0:
                    qty = (capital * position_ratio * leverage) / d['close']
                    capital -= qty * d['close'] * 0.001
                    short_qtys[c] = qty
                    short_entries[c] = d['close']
                    last_trade_time[c] = day_idx
                    trades.append({'type':'SHORT_OPEN','coin':c,'reason':'spike','price':d['close'],'day':day_idx})
                    decisions['spike'] += 1
                    decisions['short'] += 1
                    continue
            
            # 标准做多
            buy = (rsi < cfg['rsi_buy'] and bb_pos < cfg['bb_buy'] and decision > cfg['decision_threshold'])
            if buy and capital > 15 and positions[c] == 0 and short_qtys[c] == 0:
                invest = capital * position_ratio * leverage
                qty = invest / d['close']
                capital -= invest * 0.001
                positions[c] = qty
                entry_prices[c] = d['close']
                last_trade_time[c] = day_idx
                trades.append({'type':'LONG_OPEN','coin':c,'reason':'g12','price':d['close'],'day':day_idx})
                decisions['long'] += 1
            
            # 平多 (严格止损)
            if positions[c] > 0:
                pnl_ratio = (d['close'] - entry_prices[c]) / entry_prices[c] * leverage
                
                sell = False
                # 止盈
                if pnl_ratio >= cfg['take_profit']:
                    sell = True
                # 止损 (严格执行)
                if pnl_ratio <= -cfg['max_position_loss']:
                    sell = True
                    daily_loss += pnl_ratio
                # RSI超买
                if rsi > cfg['rsi_sell'] and bb_pos > cfg['bb_sell']:
                    sell = True
                
                if sell:
                    pnl = (d['close'] - entry_prices[c]) * positions[c] * leverage
                    capital += pnl - positions[c] * d['close'] * 0.001
                    positions[c] = 0
                    entry_prices[c] = 0
                    last_trade_time[c] = day_idx
                    trades.append({'type':'LONG_CLOSE','coin':c,'pnl_ratio':pnl_ratio,'reason':'g12_close','day':day_idx})
                    decisions['sell'] += 1
            
            # 标准做空
            short = (rsi > cfg['short_rsi'] and bb_pos > cfg['short_bb'])
            if short and capital > 20 and short_qtys[c] == 0 and positions[c] == 0:
                qty = (capital * position_ratio * leverage) / d['close']
                capital -= qty * d['close'] * 0.001
                short_qtys[c] = qty
                short_entries[c] = d['close']
                last_trade_time[c] = day_idx
                trades.append({'type':'SHORT_OPEN','coin':c,'reason':'g12','price':d['close'],'day':day_idx})
                decisions['short'] += 1
            
            # 平空
            if short_qtys[c] > 0:
                pnl_ratio = (short_entries[c] - d['close']) / short_entries[c] * leverage
                
                cover = False
                if pnl_ratio >= cfg['take_profit']:
                    cover = True
                if pnl_ratio <= -cfg['max_position_loss']:
                    cover = True
                    daily_loss += pnl_ratio
                if rsi < cfg['rsi_buy'] or bb_pos < cfg['bb_buy']:
                    cover = True
                
                if cover:
                    pnl = (short_entries[c] - d['close']) * short_qtys[c] * leverage
                    capital += pnl - short_qtys[c] * d['close'] * 0.001
                    short_qtys[c] = 0
                    short_entries[c] = 0
                    last_trade_time[c] = day_idx
                    trades.append({'type':'SHORT_CLOSE','coin':c,'pnl_ratio':pnl_ratio,'reason':'g12_close','day':day_idx})
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
        'decisions': decisions, 'max_drawdown': max_dd,
        'equity_curve': equity_curve[-30:]
    }

# 极限测试
def stress_test(initial_capital, price_data, cfg):
    print("\n【极限测试 v17安全版】")
    results = {}
    
    # 极端下跌
    print("  📉 极端下跌...")
    stress = {c: price_data[c][-200:].copy() if c in price_data else [] for c in COINS}
    for c in stress:
        for i in range(30):
            idx = len(stress[c]) - 30 + i
            if 0 <= idx < len(stress[c]):
                stress[c][idx]['close'] *= (1 - 0.03 * i)
    r = simulate_v17(initial_capital, stress, cfg)
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
    r = simulate_v17(initial_capital, stress, cfg)
    results['rise'] = r['return'] if r else 0
    print(f"    → {results['rise']:+.2f}%")
    
    # 高波动
    print("  ⚡ 高波动...")
    stress = {c: price_data[c][-100:].copy() if c in price_data else [] for c in COINS}
    for c in stress:
        for i in range(len(stress[c])):
            stress[c][i]['close'] *= (1 + np.random.uniform(-0.08, 0.08))
    r = simulate_v17(initial_capital, stress, cfg)
    results['highvol'] = r['return'] if r else 0
    print(f"    → {results['highvol']:+.2f}%")
    
    # 横盘
    print("  ➡️ 横盘...")
    stress = {c: price_data[c][-100:].copy() if c in price_data else [] for c in COINS}
    for c in stress:
        base = stress[c][-1]['close']
        for i in range(len(stress[c])):
            stress[c][i]['close'] = base * (1 + np.random.uniform(-0.02, 0.02))
    r = simulate_v17(initial_capital, stress, cfg)
    results['sideways'] = r['return'] if r else 0
    print(f"    → {results['sideways']:+.2f}%")
    
    return results

# 主程序
print("="*70)
print("Hermes G12 v17 - 安全版 (加强风控)")
print("="*70)

print("\n📥 获取数据...")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

print("\n【30天回测 v17】")
stats = simulate_v17(1000, price_data, CONFIG)
if stats:
    print(f"  总收益: {stats['return']:+.2f}%")
    print(f"  胜率: {stats['win_rate']:.1f}%")
    print(f"  交易: {stats['trades']}笔 (盈:{stats['wins']} 亏:{stats['losses']})")
    print(f"  最大回撤: {stats['max_drawdown']:.1f}%")
    print(f"  决策: 做多{stats['decisions']['long']} 做空{stats['decisions']['short']} 插针{stats['decisions']['spike']}")

stress = stress_test(1000, price_data, CONFIG)

print("\n【极限测试汇总】")
print(f"  极端下跌: {stress['drop']:+.2f}%")
print(f"  极端上涨: {stress['rise']:+.2f}%")
print(f"  高波动:   {stress['highvol']:+.2f}%")
print(f"  横盘:     {stress['sideways']:+.2f}%")

# 评分
safety_score = 100
if stats and stats['max_drawdown'] > 20: safety_score -= 20
if stats and stats['max_drawdown'] > 50: safety_score -= 30
if stress['drop'] < -50: safety_score -= 20
if stress['rise'] < -50: safety_score -= 20

print(f"\n🏆 安全评分: {safety_score}/100")

with open('/tmp/g12_v17_results.json', 'w') as f:
    json.dump({'config':CONFIG, 'backtest':stats, 'stress':stress, 'safety_score':safety_score}, f, indent=2, default=str)

print("\n" + "="*70)
print("✅ G12 v17 安全版测试完成!")
print("="*70)
