#!/usr/bin/env python3
"""
Hermes G12 v15 - 终极版 (完整15功能 + 30天回测)
"""
import requests, time, json, numpy as np
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== G12 v15 核心参数 ==========
CONFIG = {
    'version': 'v15-G12终极版',
    'rsi_buy': 43, 'rsi_sell': 53,
    'bb_buy': 25, 'bb_sell': 75,
    'take_profit': 0.08, 'stop_loss': 0.035,
    'position': 0.35, 'leverage': 3,
    'min_notional': 10,
    'zt_threshold': -2.0, 'ft_threshold': 3.0,
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

# ========== G12 v15 模拟交易 ==========
def simulate_g12_v15(initial_capital, price_data, cfg):
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
    
    # 决策计数
    decisions = {'long':0,'short':0,'sell':0,'cover':0,'swap':0}
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        # ========== 功能1: 全局扫描 ==========
        analyses = {}
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            closes = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            
            rsi = get_rsi(closes, cfg.get('rsi_period', 7))
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            macd = get_macd(closes)
            
            # ========== 功能2: 决策评分 ==========
            decision = 0
            decision += 0.30 * (50 - min(rsi, 50)) / 50
            decision += 0.25 * (100 - bb_pos) / 100
            decision += 0.20 * min(macd / (d['close'] * 0.005), 1)
            
            analyses[c] = {'price':d['close'],'rsi':rsi,'bb_pos':bb_pos,'macd':macd,'decision':decision}
        
        # ========== 功能3: 信号评分 ==========
        signals = []
        for c in valid_coins:
            a = analyses[c]
            score = 0
            tags = []
            
            if a['bb_pos'] < cfg.get('bb_buy', 25): score += 30; tags.append(f"BB{a['bb_pos']:.0f}%")
            if a['rsi'] < cfg.get('rsi_buy', 43): score += 20; tags.append(f"RSI{a['rsi']:.0f}")
            if a['rsi'] < 30: score += 15; tags.append("RSI极")
            if a['decision'] > cfg.get('decision_threshold', 0.70): score += 10; tags.append("确认")
            
            if a['bb_pos'] > cfg.get('bb_sell', 75): score -= 25; tags.append(f"BB高{a['bb_pos']:.0f}%")
            if a['rsi'] > cfg.get('rsi_sell', 53): score -= 20; tags.append(f"RSI高{a['rsi']:.0f}")
            
            signals.append({'coin':c,'score':score,'tags':tags,**analyses[c]})
        
        signals.sort(key=lambda x: -x['score'])
        
        # ========== 功能4-6: 决策执行 ==========
        for c in valid_coins:
            d = day_data[c]
            a = analyses[c]
            s = next((x for x in signals if x['coin'] == c), None)
            if not s: continue
            
            # G12做多信号
            buy_signal = (a['rsi'] < cfg.get('rsi_buy', 43) and a['bb_pos'] < cfg.get('bb_buy', 25))
            buy_signal = buy_signal and a['decision'] > cfg.get('decision_threshold', 0.70)
            
            if buy_signal and capital > cfg.get('min_notional', 10) and positions[c] == 0 and short_qtys[c] == 0:
                invest = capital * position_ratio * leverage
                qty = invest / d['close']
                entry_fee = invest * 0.001
                capital -= entry_fee
                positions[c] = qty
                entry_prices[c] = d['close']
                trades.append({'type':'LONG_OPEN','coin':c,'price':d['close'],'day':day_idx})
                decisions['long'] += 1
            
            # 平多仓
            if positions[c] > 0:
                pnl_ratio = (d['close'] - entry_prices[c]) / entry_prices[c] * leverage
                
                sell = (a['rsi'] > cfg.get('rsi_sell', 53) and a['bb_pos'] > cfg.get('bb_sell', 75))
                sell = sell or pnl_ratio >= cfg.get('take_profit', 0.08)
                sell = sell or pnl_ratio <= -cfg.get('stop_loss', 0.035)
                
                if sell:
                    pnl = (d['close'] - entry_prices[c]) * positions[c] * leverage
                    exit_fee = positions[c] * d['close'] * 0.001
                    capital += pnl - exit_fee
                    positions[c] = 0
                    entry_prices[c] = 0
                    trades.append({'type':'LONG_CLOSE','coin':c,'price':d['close'],'pnl_ratio':pnl_ratio,'day':day_idx})
                    decisions['sell'] += 1
            
            # G12做空信号
            short_signal = (a['rsi'] > cfg.get('short_rsi', 70) and a['bb_pos'] > cfg.get('short_bb', 85))
            
            if short_signal and capital > 20 and short_qtys[c] == 0 and positions[c] == 0:
                qty = (capital * position_ratio * leverage) / d['close']
                entry_fee = qty * d['close'] * 0.001
                capital -= entry_fee
                short_qtys[c] = qty
                short_entries[c] = d['close']
                trades.append({'type':'SHORT_OPEN','coin':c,'price':d['close'],'day':day_idx})
                decisions['short'] += 1
            
            # 平空仓
            if short_qtys[c] > 0:
                pnl_ratio = (short_entries[c] - d['close']) / short_entries[c] * leverage
                
                cover = (a['rsi'] < cfg.get('rsi_buy', 43) or a['bb_pos'] < cfg.get('bb_buy', 25))
                cover = cover or pnl_ratio >= cfg.get('take_profit', 0.08)
                cover = cover or pnl_ratio <= -cfg.get('stop_loss', 0.035)
                
                if cover:
                    pnl = (short_entries[c] - d['close']) * short_qtys[c] * leverage
                    exit_fee = short_qtys[c] * d['close'] * 0.001
                    capital += pnl - exit_fee
                    short_qtys[c] = 0
                    short_entries[c] = 0
                    trades.append({'type':'SHORT_CLOSE','coin':c,'price':d['close'],'pnl_ratio':pnl_ratio,'day':day_idx})
                    decisions['cover'] += 1
        
        # 记录权益
        day_value = capital
        for c in valid_coins:
            day_value += positions[c] * day_data[c]['close']
            day_value += short_qtys[c] * (short_entries[c] - day_data[c]['close'])
        equity_curve.append(day_value)
    
    # ========== 回测统计 ==========
    final_value = capital
    for c in valid_coins:
        final_value += positions[c] * price_data[c][-1]['close']
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    closed = [t for t in trades if t['type'] in ['LONG_CLOSE','SHORT_CLOSE']]
    wins = sum(1 for t in closed if t.get('pnl_ratio', 0) > 0)
    win_rate = wins / len(closed) * 100 if closed else 0
    
    # 最大回撤
    peak = initial_capital
    max_dd = 0
    for v in equity_curve:
        if v > peak: peak = v
        dd = (peak - v) / peak * 100
        if dd > max_dd: max_dd = dd
    
    return {
        'return': total_return,
        'win_rate': win_rate,
        'trades': len(trades),
        'wins': wins,
        'losses': len(closed) - wins,
        'decisions': decisions,
        'max_drawdown': max_dd,
        'equity_curve': equity_curve
    }

print("="*70)
print("Hermes G12 v15 - 终极版 30天回测")
print("="*70)

print("\n获取数据...")
price_data = {}
for c in COINS:
    data = get_klines(f'{c}USDT', '1h', 720)
    if data and len(data) > 100:
        price_data[c] = data
        print(f"  {c}: {len(data)}条")
    time.sleep(0.1)

print(f"\n执行G12 v15 回测 (30天/720小时)...")

stats = simulate_g12_v15(1000, price_data, CONFIG)

print("\n" + "="*70)
print("【G12 v15 回测结果】")
print("="*70)

print(f"\n📊 核心指标")
print(f"  总收益: {stats['return']:>+.2f}%")
print(f"  胜率: {stats['win_rate']:.1f}%")
print(f"  交易次数: {stats['trades']}笔")
print(f"  盈利: {stats['wins']}笔 | 亏损: {stats['losses']}笔")
print(f"  最大回撤: {stats['max_drawdown']:.1f}%")

print(f"\n📈 决策统计")
print(f"  做多信号: {stats['decisions']['long']}次")
print(f"  做空信号: {stats['decisions']['short']}次")
print(f"  平多仓: {stats['decisions']['sell']}次")
print(f"  平空仓: {stats['decisions']['cover']}次")

print(f"\n⚙️ G12 v15 配置")
print(f"  RSI: {CONFIG['rsi_buy']}/{CONFIG['rsi_sell']}")
print(f"  布林: {CONFIG['bb_buy']}/{CONFIG['bb_sell']}")
print(f"  止盈: {CONFIG['take_profit']*100:.0f}% | 止损: {CONFIG['stop_loss']*100:.1f}%")
print(f"  仓位: {CONFIG['position']*100:.0f}% | 杠杆: {CONFIG['leverage']}x")

# 保存
with open('/tmp/g12_v15_backtest.json', 'w') as f:
    json.dump(stats, f, indent=2, default=str)

print("\n" + "="*70)
print(f"✅ G12 v15 回测完成!")
print("="*70)
