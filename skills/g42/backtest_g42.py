#!/usr/bin/env python3
"""
G42 - 30天回测 + 7天预测矩阵
===========================
"""

import json, time, urllib.request
from collections import defaultdict

PROXY = 'http://172.29.144.1:7897'

POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}

COINS = {
    'mainstream': ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'BNB'],
    'meme': ['DOGE', 'SHIB', 'PEPE', 'BONK', 'NEIRO', 'BOME', 'FTM', 'MATIC', 'AVAX']
}

def get_klines(sym, interval='1h', limit=500):
    try:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=' + interval + '&limit=' + str(limit)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=15).read().decode())
    except: return []

def detect_market(closes, volumes):
    if len(closes) < 100: return 'neutral'
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    vol = sum(abs(r) for r in returns[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    if trend > 0.03: return 'trend'
    elif vol < 0.015: return 'range'
    elif trend > 0.015 and vol > 0.025: return 'breakout'
    return 'range'

def calc_g42_signals(closes, volumes, polymarket=0):
    """G42 10+策略融合"""
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
    volatility = sum(abs(r) for r in returns[-20:])/20
    momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
    
    # G42 策略
    go_core = trend * 10
    go_pool = (vol_ratio - 1) * 0.5
    go_rotate = trend * 0.8
    go_ls = (rsi - 50) / 50
    go_detect = trend50 * 5
    momentum_sig = momentum * 100
    mean_rev = -(closes[-1] - ma20)/ma20 * 10 if ma20 > 0 else 0
    breakout = 1 if closes[-1] > max(closes[-20:-1]) else -0.5 if closes[-1] < min(closes[-20:-1]) else 0
    vol_profile = 1 if vol_ratio > 1.5 and closes[-1] > ma20 else 0
    sentiment = trend * 20 + polymarket
    
    # 融合
    go_signal = go_core*0.15 + go_pool*0.12 + go_rotate*0.10 + go_ls*0.10 + go_detect*0.08 + momentum_sig*0.08 + mean_rev*0.08 + breakout*0.07 + vol_profile*0.07 + sentiment*0.05
    
    return go_signal * 0.7 + polymarket * 0.3

def simulate_trades(prices_data, coin_type, market_type):
    trades = []
    for sym in COINS[coin_type]:
        if sym not in prices_data: continue
        data = prices_data[sym]
        for i in range(50, len(data)-1):
            closes = [float(k[4]) for k in data[:i]]
            volumes = [float(k[5]) for k in data[:i]]
            market = detect_market(closes, volumes)
            if market != market_type: continue
            
            signal = calc_g42_signals(closes, volumes, POLYMARKET.get(sym, 0))
            current_price = float(data[i][4])
            next_price = float(data[i+1][4])
            ret = (next_price - current_price) / current_price
            
            if signal > 0.08:
                trades.append({'type': 'buy', 'return': ret, 'coin': sym})
            elif signal < -0.05:
                trades.append({'type': 'sell', 'return': -ret, 'coin': sym})
    return trades

def calc_metrics(trades):
    if not trades: return {'win_rate': 0, 'avg_return': 0, 'total_return': 0, 'count': 0}
    wins = [t for t in trades if t['return'] > 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    avg_return = sum(t['return'] for t in trades) / len(trades) * 100 if trades else 0
    total_return = (1 + sum(t['return'] for t in trades)) - 1
    return {'win_rate': win_rate, 'avg_return': avg_return, 'total_return': total_return * 100, 'count': len(trades)}

def predict_7d(prices_data):
    predictions = {}
    for coin_type in ['mainstream', 'meme']:
        predictions[coin_type] = {}
        for sym in COINS[coin_type]:
            if sym not in prices_data: continue
            data = prices_data[sym]
            if len(data) < 100: continue
            closes = [float(k[4]) for k in data[-100:]]
            volumes = [float(k[5]) for k in data[-100:]]
            market = detect_market(closes, volumes)
            signal = calc_g42_signals(closes, volumes, POLYMARKET.get(sym, 0))
            ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
            trend_pct = (ma5 - ma20)/ma20 * 100 if ma20 > 0 else 0
            direction = 'UP' if signal > 0.1 else 'DOWN' if signal < -0.1 else 'SIDEWAYS'
            pred = trend_pct * 3 + signal * 50
            predictions[coin_type][sym] = {'direction': direction, 'signal': signal, 'pred_7d': pred, 'market': market}
    return predictions

print('=' * 80)
print('G42 - 30天回测 + 7天预测矩阵')
print('=' * 80)

print('\n获取数据...')
prices_data = {}
for sym in list(set(COINS['mainstream'] + COINS['meme'])):
    data = get_klines(sym, '1h', 500)
    if data: prices_data[sym] = data
    print('  {}: {}条'.format(sym, len(data)))

print('\n' + '=' * 80)
print('30天回测结果矩阵 (胜率/平均收益)')
print('=' * 80)
print('\n{:<15} {:>12} {:>12} {:>12} {:>12}'.format('', '趋势市场', '震荡市场', '突破市场', '平均'))
print('-' * 65)

results = {}
for coin_type in ['mainstream', 'meme']:
    results[coin_type] = {}
    type_name = '主流币' if coin_type == 'mainstream' else 'Meme币'
    row = []
    for market in ['trend', 'range', 'breakout']:
        trades = simulate_trades(prices_data, coin_type, market)
        m = calc_metrics(trades)
        results[coin_type][market] = m
        row.append('{:.1f}%/{:+.2f}%'.format(m['win_rate'], m['avg_return']))
    avg_wr = sum(results[coin_type][m]['win_rate'] for m in ['trend', 'range', 'breakout']) / 3
    avg_ret = sum(results[coin_type][m]['avg_return'] for m in ['trend', 'range', 'breakout']) / 3
    row.append('{:.1f}%/{:+.2f}%'.format(avg_wr, avg_ret))
    print('{:<15} {:>12} {:>12} {:>12} {:>12}'.format(type_name, *row))

print('\n' + '=' * 80)
print('30天收益矩阵 ($1000初始)')
print('=' * 80)
print('\n{:<15} {:>12} {:>12} {:>12} {:>12}'.format('', '趋势市场', '震荡市场', '突破市场', '平均'))
print('-' * 65)

for coin_type in ['mainstream', 'meme']:
    type_name = '主流币' if coin_type == 'mainstream' else 'Meme币'
    row = []
    for market in ['trend', 'range', 'breakout']:
        m = results[coin_type][market]
        final = 1000 * (1 + m['total_return']/100)
        row.append('${:.0f}'.format(final))
    avg_final = sum(float(r.replace('$','')) for r in row) / 3
    row.append('${:.0f}'.format(avg_final))
    print('{:<15} {:>12} {:>12} {:>12} {:>12}'.format(type_name, *row))

print('\n' + '=' * 80)
print('7天价格预测')
print('=' * 80)

predictions = predict_7d(prices_data)
for coin_type in ['mainstream', 'meme']:
    type_name = '主流币' if coin_type == 'mainstream' else 'Meme币'
    print('\n{}:'.format(type_name))
    for sym, pred in predictions[coin_type].items():
        print('  {}: {} 信号{:+.2f} 预测: {:+.1f}% ({})'.format(
            sym, pred['market'][:3], pred['signal'], pred['pred_7d'], pred['direction']))

print('\n' + '=' * 80)
