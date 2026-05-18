#!/usr/bin/env python3
"""
G44 v4.1 - 30天回测 + 7天预测 (加强杠杆版)
==========================================
功能:
- 自主杠杆 (2x-3x)
- 30天回测矩阵
- 7天预测
- 胜率/收益分析
"""

import json, time, urllib.request
from collections import defaultdict

PROXY = 'http://172.29.144.1:7897'
POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}
COINS = {
    'mainstream': ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB'],
    'meme': ['DOGE','SHIB','PEPE','BONK','NEIRO','BOME','FTM','MATIC','AVAX']
}
SKIP = ['FTM','NEIRO','BOME','SHIB','PEPE','BONK']
BUY_T, SELL_T = 0.03, -0.03

def get_klines(sym, limit=500):
    try:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=1h&limit=' + str(limit)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=15).read().decode())
    except: return []

def detect_market(closes):
    if len(closes) < 100: return 'neutral'
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    vol = sum(abs(r) for r in returns[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    if trend > 0.03: return 'trend'
    elif vol < 0.015: return 'range'
    return 'range'

def calc_signal(closes, volumes, market, polymarket=0):
    """G43原始信号"""
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains)/len(gains) if gains else 0
    avg_loss = sum(losses)/len(losses) if losses else 0
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100/(1+rs))
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
    
    if market == 'range':
        go_pool = (vol_ratio - 1) * 0.8
        mean_rev = -((closes[-1] - ma20)/ma20 * 15) if ma20 > 0 else 0
        go_rotate = trend * 1.2
    else:
        go_pool = (vol_ratio - 1) * 0.5
        mean_rev = -((closes[-1] - ma20)/ma20 * 8) if ma20 > 0 else 0
        go_rotate = trend * 0.5
    
    go_core = trend * 12
    go_ls = (rsi - 50) / 50
    go_detect = trend50 * 6
    momentum_sig = momentum * 120
    breakout = 1.5 if closes[-1] > max(closes[-20:-1]) else -0.5 if closes[-1] < min(closes[-20:-1]) else 0
    vol_profile = 1.2 if vol_ratio > 1.5 and closes[-1] > ma20 else 0
    sentiment = trend * 25 + polymarket * 1.5
    
    go_signal = (go_core*0.15 + go_pool*0.15 + go_rotate*0.12 + go_ls*0.10 +
                 go_detect*0.08 + momentum_sig*0.08 + mean_rev*0.10 +
                 breakout*0.07 + vol_profile*0.08 + sentiment*0.07)
    
    return go_signal * 0.65 + polymarket * 0.35

def get_leverage(signal, market, coin_type):
    """G44自主杠杆 - 信号越强杠杆越高"""
    abs_sig = abs(signal)
    # 趋势市场用更高杠杆
    if market == 'trend':
        if abs_sig > 0.10: return 3.0
        elif abs_sig > 0.05: return 2.5
        else: return 2.0
    else:  # range市场
        if abs_sig > 0.08: return 2.5
        elif abs_sig > 0.04: return 2.0
        else: return 1.5

def simulate_trades(prices_data, coin_type, market_type, leverage_enabled=True):
    """模拟交易 (带杠杆)"""
    trades = []
    for sym in COINS[coin_type]:
        if sym in SKIP or sym not in prices_data: continue
        data = prices_data[sym]
        for i in range(50, len(data)-1):
            closes = [float(k[4]) for k in data[:i]]
            volumes = [float(k[5]) for k in data[:i]]
            market = detect_market(closes)
            if market != market_type: continue
            
            signal = calc_signal(closes, volumes, market, POLYMARKET.get(sym, 0))
            lev = get_leverage(signal, market, coin_type) if leverage_enabled else 1.0
            ret = (float(data[i+1][4]) - float(data[i][4])) / float(data[i][4])
            
            # 杠杆收益
            leveraged_ret = ret * lev
            
            if signal > BUY_T:
                trades.append({'type': 'buy', 'return': leveraged_ret, 'leverage': lev, 'coin': sym})
            elif signal < SELL_T:
                trades.append({'type': 'sell', 'return': -leveraged_ret, 'leverage': lev, 'coin': sym})
    return trades

def calc_metrics(trades):
    if not trades: return {'wr': 0, 'avg': 0, 'total': 0, 'count': 0, 'avg_lev': 1.0}
    wins = [t for t in trades if t['return'] > 0]
    wr = len(wins) / len(trades) * 100 if trades else 0
    avg = sum(t['return'] for t in trades) / len(trades) * 100 if trades else 0
    total = ((1 + sum(t['return'] for t in trades)) - 1) * 100
    avg_lev = sum(t.get('leverage', 1) for t in trades) / len(trades)
    return {'wr': wr, 'avg': avg, 'total': total, 'count': len(trades), 'avg_lev': avg_lev}

def predict_7d(prices_data):
    """7天预测"""
    predictions = {}
    for coin_type in ['mainstream', 'meme']:
        predictions[coin_type] = {}
        for sym in COINS[coin_type]:
            if sym in SKIP or sym not in prices_data: continue
            data = prices_data[sym]
            if len(data) < 100: continue
            closes = [float(k[4]) for k in data[-100:]]
            volumes = [float(k[5]) for k in data[-100:]]
            market = detect_market(closes)
            signal = calc_signal(closes, volumes, market, POLYMARKET.get(sym, 0))
            lev = get_leverage(signal, market, coin_type)
            ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
            trend_pct = (ma5 - ma20)/ma20 * 100 if ma20 > 0 else 0
            pred_7d = trend_pct * 3 + signal * 60
            leveraged_pred = pred_7d * lev
            direction = 'UP' if signal > 0.05 else 'DOWN' if signal < -0.05 else 'SIDEWAYS'
            predictions[coin_type][sym] = {
                'signal': signal, 'pred_7d': pred_7d, 'leveraged_pred': leveraged_pred,
                'leverage': lev, 'market': market, 'direction': direction
            }
    return predictions

print('=' * 80)
print('G44 v4.1 - 30天回测 + 7天预测 (加强杠杆版)')
print('=' * 80)

print('\n获取数据...')
prices_data = {}
for sym in list(set(COINS['mainstream'] + COINS['meme'])):
    data = get_klines(sym)
    if data: prices_data[sym] = data
print('完成:', len(prices_data), '币种')

# ========== 30天回测 (无杠杆 vs 有杠杆) ==========
print('\n' + '=' * 80)
print('30天回测矩阵 - 无杠杆')
print('=' * 80)
print('\n{:<15} {:>10} {:>10} {:>10} {:>10}'.format('', '趋势市场', '震荡市场', '突破市场', '平均'))
print('-' * 55)

results_no_lev = {}
for ct in ['mainstream', 'meme']:
    results_no_lev[ct] = {}
    row = ['主流币' if ct == 'mainstream' else 'Meme币']
    vals = []
    for m in ['trend', 'range', 'breakout']:
        t = simulate_trades(prices_data, ct, m, leverage_enabled=False)
        mm = calc_metrics(t)
        results_no_lev[ct][m] = mm
        final = 1000 * (1 + mm['total'] / 100)
        row.append('${:.0f}'.format(final))
        vals.append(final)
    row.append('${:.0f}'.format(sum(vals) / 3))
    print('{:<15} {:>10} {:>10} {:>10} {:>10}'.format(*row))

print('\n' + '=' * 80)
print('30天回测矩阵 - 有杠杆 (2x-3x)')
print('=' * 80)
print('\n{:<15} {:>10} {:>10} {:>10} {:>10}'.format('', '趋势市场', '震荡市场', '突破市场', '平均'))
print('-' * 55)

results_lev = {}
for ct in ['mainstream', 'meme']:
    results_lev[ct] = {}
    row = ['主流币' if ct == 'mainstream' else 'Meme币']
    vals = []
    for m in ['trend', 'range', 'breakout']:
        t = simulate_trades(prices_data, ct, m, leverage_enabled=True)
        mm = calc_metrics(t)
        results_lev[ct][m] = mm
        final = 1000 * (1 + mm['total'] / 100)
        row.append('${:.0f}'.format(final))
        vals.append(final)
    row.append('${:.0f}'.format(sum(vals) / 3))
    print('{:<15} {:>10} {:>10} {:>10} {:>10}'.format(*row))

# ========== 胜率矩阵 ==========
print('\n' + '=' * 80)
print('胜率矩阵 (有杠杆)')
print('=' * 80)
print('\n{:<15} {:>10} {:>10} {:>10} {:>10}'.format('', '趋势市场', '震荡市场', '突破市场', '平均'))
print('-' * 55)

for ct in ['mainstream', 'meme']:
    row = ['主流币' if ct == 'mainstream' else 'Meme币']
    vals = []
    for m in ['trend', 'range', 'breakout']:
        mm = results_lev[ct][m]
        row.append('{:.1f}%'.format(mm['wr']))
        vals.append(mm['wr'])
    row.append('{:.1f}%'.format(sum(vals) / 3))
    print('{:<15} {:>10} {:>10} {:>10} {:>10}'.format(*row))

# ========== 平均收益矩阵 ==========
print('\n' + '=' * 80)
print('平均收益矩阵 (有杠杆)')
print('=' * 80)
print('\n{:<15} {:>10} {:>10} {:>10} {:>10}'.format('', '趋势市场', '震荡市场', '突破市场', '平均'))
print('-' * 55)

for ct in ['mainstream', 'meme']:
    row = ['主流币' if ct == 'mainstream' else 'Meme币']
    vals = []
    for m in ['trend', 'range', 'breakout']:
        mm = results_lev[ct][m]
        row.append('{:+.2f}%'.format(mm['avg']))
        vals.append(mm['avg'])
    row.append('{:+.2f}%'.format(sum(vals) / 3))
    print('{:<15} {:>10} {:>10} {:>10} {:>10}'.format(*row))

# ========== 7天预测 ==========
print('\n' + '=' * 80)
print('7天价格预测 (加强杠杆)')
print('=' * 80)

predictions = predict_7d(prices_data)
for ct in ['mainstream', 'meme']:
    print('\n{}:'.format('主流币' if ct == 'mainstream' else 'Meme币'))
    for sym, pred in sorted(predictions[ct].items(), key=lambda x: -x[1]['signal']):
        emoji = '📈' if pred['direction'] == 'UP' else '📉' if pred['direction'] == 'DOWN' else '➡️'
        lev_info = '(杠杆 {:.1f}x)'.format(pred['leverage'])
        print('  {} {} 信号{:+.2f} 预测: {:+.1f}% {} {}'.format(
            sym, pred['market'][:3], pred['signal'], pred['leveraged_pred'], lev_info, emoji
        ))

# ========== 杠杆使用统计 ==========
print('\n' + '=' * 80)
print('杠杆使用统计')
print('=' * 80)
for ct in ['mainstream', 'meme']:
    for m in ['trend', 'range']:
        mm = results_lev[ct][m]
        print('{} {}: 平均杠杆 {:.1f}x, 交易次数 {}'.format(
            ct, m, mm['avg_lev'], mm['count']))

print('\n' + '=' * 80)
