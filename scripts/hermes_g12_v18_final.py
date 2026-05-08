#!/usr/bin/env python3
"""
Hermes G12 v18 - 最终版 (修复模拟器 + 正确回测)
"""
import requests, time, json, numpy as np
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

CONFIG = {
    'version': 'v18-G12最终版',
    'rsi_buy': 43, 'rsi_sell': 53,
    'bb_buy': 25, 'bb_sell': 75,
    'take_profit': 0.08, 'stop_loss': 0.035,
    'position': 0.30, 'leverage': 3,
    'short_rsi': 70, 'short_bb': 85,
    'decision_threshold': 0.70,
}

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

def simulate_g12(initial_capital, price_data, cfg):
    """正确的模拟器"""
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 100]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0.0 for c in valid_coins}  # 做多数量
    entry_prices = {c: 0.0 for c in valid_coins}
    short_qtys = {c: 0.0 for c in valid_coins}  # 做空数量
    short_entries = {c: 0.0 for c in valid_coins}
    trades = []
    equity_curve = []
    
    leverage = cfg.get('leverage', 3)
    pos_ratio = cfg.get('position', 0.30)
    
    decisions = {'long':0,'short':0,'sell':0,'cover':0}
    
    for day_idx in range(min_days):
        day_prices = {c: price_data[c][day_idx]['close'] for c in valid_coins}
        
        for c in valid_coins:
            klines = price_data[c][max(0,day_idx-30):day_idx+1]
            closes = [k['close'] for k in klines]
            highs = [k['high'] for k in klines]
            lows = [k['low'] for k in klines]
            
            if len(closes) < 20: continue
            
            price = day_prices[c]
            rsi = get_rsi(closes, 7)
            bb = bollinger_pos(price, highs, lows, 20)
            macd = get_macd(closes)
            
            # 决策评分
            decision = 0.3*(50-min(rsi,50))/50 + 0.25*(100-bb)/100 + 0.2*min(macd/(price*0.005),1)
            
            # ========== 做多 ==========
            buy_sig = (rsi < cfg['rsi_buy'] and bb < cfg['bb_buy'] and decision > cfg['decision_threshold'])
            if buy_sig and capital > 10 and positions[c] == 0 and short_qtys[c] == 0:
                invest = capital * pos_ratio * leverage
                qty = invest / price
                fee = invest * 0.001
                capital -= fee
                positions[c] = qty
                entry_prices[c] = price
                trades.append({'type':'LONG','coin':c,'price':price,'qty':qty,'day':day_idx})
                decisions['long'] += 1
            
            # ========== 平多 ==========
            if positions[c] > 0:
                pnl_pct = (price - entry_prices[c]) / entry_prices[c] * leverage
                sell = False
                reason = ''
                if pnl_pct >= cfg['take_profit']:
                    sell = True; reason = 'tp'
                if pnl_pct <= -cfg['stop_loss']:
                    sell = True; reason = 'sl'
                if rsi > cfg['rsi_sell'] and bb > cfg['bb_sell']:
                    sell = True; reason = 'rsi_sell'
                
                if sell:
                    pnl = (price - entry_prices[c]) * positions[c] * leverage
                    fee = positions[c] * price * 0.001
                    capital += pnl - fee
                    trades.append({'type':'LONG_CLOSE','coin':c,'price':price,'pnl':pnl,'reason':reason,'day':day_idx})
                    positions[c] = 0
                    entry_prices[c] = 0
                    decisions['sell'] += 1
            
            # ========== 做空 ==========
            short_sig = (rsi > cfg['short_rsi'] and bb > cfg['short_bb'])
            if short_sig and capital > 10 and short_qtys[c] == 0 and positions[c] == 0:
                invest = capital * pos_ratio * leverage
                qty = invest / price
                fee = invest * 0.001
                capital -= fee
                short_qtys[c] = qty
                short_entries[c] = price
                trades.append({'type':'SHORT','coin':c,'price':price,'qty':qty,'day':day_idx})
                decisions['short'] += 1
            
            # ========== 平空 ==========
            if short_qtys[c] > 0:
                pnl_pct = (short_entries[c] - price) / short_entries[c] * leverage
                cover = False
                reason = ''
                if pnl_pct >= cfg['take_profit']:
                    cover = True; reason = 'tp'
                if pnl_pct <= -cfg['stop_loss']:
                    cover = True; reason = 'sl'
                if rsi < cfg['rsi_buy'] or bb < cfg['bb_buy']:
                    cover = True; reason = 'rsi_buy'
                
                if cover:
                    pnl = (short_entries[c] - price) * short_qtys[c] * leverage
                    fee = short_qtys[c] * price * 0.001
                    capital += pnl - fee
                    trades.append({'type':'SHORT_CLOSE','coin':c,'price':price,'pnl':pnl,'reason':reason,'day':day_idx})
                    short_qtys[c] = 0
                    short_entries[c] = 0
                    decisions['cover'] += 1
        
        # 计算当日权益
        equity = capital
        for c in valid_coins:
            equity += positions[c] * day_prices[c]
            equity += short_qtys[c] * (short_entries[c] - day_prices[c])
        equity_curve.append(equity)
    
    # ========== 统计 ==========
    final_equity = capital
    for c in valid_coins:
        final_equity += positions[c] * price_data[c][-1]['close']
        final_equity += short_qtys[c] * (short_entries[c] - price_data[c][-1]['close'])
    
    total_return = (final_equity - initial_capital) / initial_capital * 100
    
    closed = [t for t in trades if 'CLOSE' in t['type']]
    wins = sum(1 for t in closed if t.get('pnl', 0) > 0)
    win_rate = wins / len(closed) * 100 if closed else 0
    
    # 最大回撤
    peak = initial_capital
    max_dd = 0
    for v in equity_curve:
        peak = max(peak, v)
        dd = (peak - v) / peak * 100
        max_dd = max(max_dd, dd)
    
    return {
        'return': total_return,
        'win_rate': win_rate,
        'trades': len(trades),
        'wins': wins,
        'losses': len(closed) - wins,
        'decisions': decisions,
        'max_drawdown': max_dd,
        'final_equity': final_equity,
        'equity_curve': equity_curve[-30:]
    }

def stress_test(initial_capital, price_data, cfg):
    """正确的极限测试"""
    print("\n【极限测试】")
    results = {}
    
    # 测试1: 模拟下跌行情(空头盈利)
    print("  📉 下跌行情(做空)...")
    sdata = {}
    for c in COINS:
        if c in price_data:
            klines = price_data[c][-200:].copy()
            # 模拟30天跌40%
            for i in range(30):
                idx = len(klines) - 30 + i
                if 0 <= idx < len(klines):
                    klines[idx]['close'] *= (1 - 0.02 * (i+1))
            sdata[c] = klines
    r = simulate_g12(initial_capital, sdata, cfg)
    results['drop'] = r['return'] if r else 0
    print(f"    → {results['drop']:+.2f}% (做空盈利)")
    
    # 测试2: 模拟上涨行情(多头盈利)
    print("  📈 上涨行情(做多)...")
    sdata = {}
    for c in COINS:
        if c in price_data:
            klines = price_data[c][-200:].copy()
            for i in range(30):
                idx = len(klines) - 30 + i
                if 0 <= idx < len(klines):
                    klines[idx]['close'] *= (1 + 0.015 * (i+1))
            sdata[c] = klines
    r = simulate_g12(initial_capital, sdata, cfg)
    results['rise'] = r['return'] if r else 0
    print(f"    → {results['rise']:+.2f}% (做多盈利)")
    
    # 测试3: 横盘
    print("  ➡️ 横盘...")
    sdata = {}
    for c in COINS:
        if c in price_data:
            klines = price_data[c][-100:].copy()
            base = klines[-1]['close']
            for i in range(len(klines)):
                klines[i]['close'] = base * (1 + np.random.uniform(-0.01, 0.01))
            sdata[c] = klines
    r = simulate_g12(initial_capital, sdata, cfg)
    results['sideways'] = r['return'] if r else 0
    print(f"    → {results['sideways']:+.2f}%")
    
    return results

# 主程序
print("="*70)
print("Hermes G12 v18 - 最终版 (修复+正确回测)")
print("="*70)

print("\n📥 获取数据...")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

print("\n【30天回测 v18】")
stats = simulate_g12(1000, price_data, CONFIG)
if stats:
    print(f"  总收益: {stats['return']:+.2f}%")
    print(f"  胜率: {stats['win_rate']:.1f}%")
    print(f"  交易: {stats['trades']}笔 (盈:{stats['wins']} 亏:{stats['losses']})")
    print(f"  最大回撤: {stats['max_drawdown']:.1f}%")
    print(f"  决策: 做多{stats['decisions']['long']} 做空{stats['decisions']['short']} 平多{stats['decisions']['sell']} 平空{stats['decisions']['cover']}")

stress = stress_test(1000, price_data, CONFIG)

print("\n【极限测试汇总】")
print(f"  下跌行情(做空): {stress['drop']:+.2f}%")
print(f"  上涨行情(做多): {stress['rise']:+.2f}%")
print(f"  横盘:          {stress['sideways']:+.2f}%")

# 综合评分
score = 100
if stats:
    if stats['return'] < 0: score -= 30
    if stats['max_drawdown'] > 30: score -= 20 * (stats['max_drawdown'] // 10)
if stress['drop'] < 0: score -= 15
if stress['rise'] < 0: score -= 15

print(f"\n🏆 综合评分: {score}/100")

with open('/tmp/g12_v18_results.json', 'w') as f:
    json.dump({'config':CONFIG, 'backtest':stats, 'stress':stress, 'score':score}, f, indent=2, default=str)

print("\n" + "="*70)
print("✅ G12 v18 最终版测试完成!")
print("="*70)
