#!/usr/bin/env python3
"""G44 30天回测"""
import json, time, urllib.request
from collections import defaultdict

PROXY = 'http://172.29.144.1:7897'
POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}
COINS = {'mainstream':['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB'],'meme':['DOGE','SHIB','PEPE','BONK','NEIRO','BOME','FTM','MATIC','AVAX']}
SKIP = ['FTM','NEIRO','BOME','SHIB','PEPE','BONK']
BUY_T, SELL_T = 0.05, -0.03

def get_klines(sym, limit=500):
    try:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=1h&limit=' + str(limit)
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

def calc_signal(closes, volumes, market, polymarket=0):
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
        go_pool = (vol_ratio - 1) * 1.0
        mean_rev = -((closes[-1] - ma20)/ma20 * 18) if ma20 > 0 else 0
        go_rotate = trend * 1.5
    elif market == 'breakout':
        go_pool = (vol_ratio - 1) * 0.6
        mean_rev = -((closes[-1] - ma20)/ma20 * 5) if ma20 > 0 else 0
        go_rotate = trend * 0.8
    else:
        go_pool = (vol_ratio - 1) * 0.5
        mean_rev = -((closes[-1] - ma20)/ma20 * 8) if ma20 > 0 else 0
        go_rotate = trend * 0.5
    
    go_core = trend * 15
    go_ls = (rsi - 50) / 50
    go_detect = trend50 * 8
    momentum_sig = momentum * 150
    breakout = 2.0 if closes[-1] > max(closes[-20:-1]) else -1.0 if closes[-1] < min(closes[-20:-1]) else 0
    vol_profile = 1.5 if vol_ratio > 1.5 and closes[-1] > ma20 else 0
    sentiment = trend * 30 + polymarket * 2.0
    
    go_signal = (go_core*0.15 + go_pool*0.15 + go_rotate*0.12 + go_ls*0.10 +
                 go_detect*0.08 + momentum_sig*0.08 + mean_rev*0.10 +
                 breakout*0.07 + vol_profile*0.08 + sentiment*0.07)
    
    return go_signal * 0.60 + polymarket * 0.40

def simulate(prices_data, coin_type, market_type):
    trades = []
    for sym in COINS[coin_type]:
        if sym in SKIP or sym not in prices_data: continue
        data = prices_data[sym]
        for i in range(50, len(data)-1):
            closes = [float(k[4]) for k in data[:i]]
            volumes = [float(k[5]) for k in data[:i]]
            market = detect_market(closes, volumes)
            if market != market_type: continue
            signal = calc_signal(closes, volumes, market, POLYMARKET.get(sym, 0))
            ret = (float(data[i+1][4]) - float(data[i][4])) / float(data[i][4])
            if signal > BUY_T: trades.append({'type':'buy','return':ret})
            elif signal < SELL_T: trades.append({'type':'sell','return':-ret})
    return trades

def metrics(trades):
    if not trades: return {'wr':0,'avg':0,'total':0,'count':0}
    wins = [t for t in trades if t['return'] > 0]
    wr = len(wins)/len(trades)*100 if trades else 0
    avg = sum(t['return'] for t in trades)/len(trades)*100 if trades else 0
    total = ((1+sum(t['return'] for t in trades))-1)*100
    return {'wr':wr,'avg':avg,'total':total,'count':len(trades)}

print('='*60)
print('G44 v4.0 - 30天回测')
print('='*60)

print('\n获取数据...')
prices_data = {s: get_klines(s) for s in list(set(COINS['mainstream']+COINS['meme'])) if get_klines(s)}
print('完成:', len(prices_data), '币种')

print('\n'+'='*60)
print('30天收益矩阵 ($1000初始)')
print('='*60)
print('\n{:<12} {:>10} {:>10} {:>10} {:>10}'.format('','趋势','震荡','突破','平均'))
print('-'*52)

for ct in ['mainstream','meme']:
    row = ['主流币' if ct=='mainstream' else 'Meme币']
    vals = []
    for m in ['trend','range','breakout']:
        t = simulate(prices_data, ct, m)
        mm = metrics(t)
        final = 1000*(1+mm['total']/100)
        row.append('${:.0f}'.format(final))
        vals.append(final)
    row.append('${:.0f}'.format(sum(vals)/3))
    print('{:<12} {:>10} {:>10} {:>10} {:>10}'.format(*row))

print('\n'+'='*60)
