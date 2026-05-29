#!/usr/bin/env python3
"""
G44 v4.2 - 30天回测 + 7天预测 (杠杆版)
"""
import json, time, urllib.request
from collections import defaultdict

PROXY = 'http://172.29.144.1:7897'
POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}
COINS = {'mainstream':['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB'],'meme':['DOGE','SHIB','PEPE','BONK','NEIRO','BOME','FTM','MATIC','AVAX']}
SKIP = ['FTM','NEIRO','BOME','SHIB','PEPE','BONK']
BUY_T, SELL_T = 0.035, -0.035

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

def get_leverage(signal, market):
    abs_sig = abs(signal)
    if market == 'trend':
        if abs_sig > 0.10: return 2.5
        elif abs_sig > 0.05: return 2.0
        return 1.5
    else:
        if abs_sig > 0.08: return 2.0
        elif abs_sig > 0.04: return 1.5
        return 1.0

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

def simulate_trades(prices_data, coin_type, market_type, leverage=True):
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
            lev = get_leverage(signal, market) if leverage else 1.0
            ret = (float(data[i+1][4]) - float(data[i][4])) / float(data[i][4])
            leveraged_ret = ret * lev
            if signal > BUY_T:
                trades.append({'type':'buy','return': leveraged_ret,'leverage': lev,'coin': sym})
            elif signal < SELL_T:
                trades.append({'type':'sell','return': -leveraged_ret,'leverage': lev,'coin': sym})
    return trades

def metrics(trades):
    if not trades: return {'wr':0,'avg':0,'total':0,'count':0,'avg_lev':1.0,'max_lev':1.0,'min_lev':1.0}
    wins = [t for t in trades if t['return'] > 0]
    wr = len(wins)/len(trades)*100 if trades else 0
    avg = sum(t['return'] for t in trades)/len(trades)*100 if trades else 0
    total = ((1+sum(t['return'] for t in trades))-1)*100
    levs = [t['leverage'] for t in trades]
    return {'wr':wr,'avg':avg,'total':total,'count':len(trades),'avg_lev':sum(levs)/len(levs),'max_lev':max(levs),'min_lev':min(levs)}

def predict_7d(prices_data):
    predictions = {}
    for ct in ['mainstream','meme']:
        predictions[ct] = {}
        for sym in COINS[ct]:
            if sym in SKIP or sym not in prices_data: continue
            data = prices_data[sym]
            if len(data) < 100: continue
            closes = [float(k[4]) for k in data[-100:]]
            volumes = [float(k[5]) for k in data[-100:]]
            market = detect_market(closes)
            signal = calc_signal(closes, volumes, market, POLYMARKET.get(sym, 0))
            lev = get_leverage(signal, market)
            ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
            trend_pct = (ma5 - ma20)/ma20*100 if ma20 > 0 else 0
            pred = trend_pct * 3 + signal * 60
            leveraged_pred = pred * lev
            direction = 'UP' if signal > 0.05 else 'DOWN' if signal < -0.05 else 'SIDEWAYS'
            predictions[ct][sym] = {'signal':signal,'pred':pred,'lev_pred':leveraged_pred,'leverage':lev,'market':market,'direction':direction}
    return predictions

print('='*80)
print('G44 v4.2 - 30天回测 + 7天预测 (杠杆版)')
print('='*80)

print('\n获取数据...')
prices_data = {s: get_klines(s) for s in list(set(COINS['mainstream']+COINS['meme'])) if get_klines(s)}
print('完成:', len(prices_data), '币种')

print('\n'+'='*80)
print('30天回测 - 胜率/收益/30天收益/杠杆范围')
print('='*80)

results = {}
for ct in ['mainstream','meme']:
    results[ct] = {}
    for m in ['trend','range']:
        t_no = simulate_trades(prices_data, ct, m, leverage=False)
        t_lev = simulate_trades(prices_data, ct, m, leverage=True)
        mm_no = metrics(t_no)
        mm_lev = metrics(t_lev)
        results[ct][m] = {'no_lev':mm_no,'lev':mm_lev}

# 打印矩阵
print('\n{:<12} {:>6} {:>10} {:>10} {:>10} {:>8}'.format('', '胜率', '平均收益', '30天收益', '平均杠杆', '范围'))
print('-'*66)
for ct in ['mainstream','meme']:
    ct_name = '主流币' if ct == 'mainstream' else 'Meme币'
    for m in ['trend','range']:
        m_name = '趋势' if m == 'trend' else '震荡'
        r = results[ct][m]['lev']
        final = 1000*(1+r['total']/100)
        print('{:<12} {:>6} {:>10} {:>10} {:>10} {:>8}'.format(
            ct_name+m_name, '{:.1f}%'.format(r['wr']), '{:+.2f}%'.format(r['avg']),
            '${:.0f}'.format(final), '{:.1f}x'.format(r['avg_lev']), '{:.1f}-{:.1f}x'.format(r['min_lev'],r['max_lev'])))

print('\n'+'='*80)
print('7天预测 (加强杠杆)')
print('='*80)

predictions = predict_7d(prices_data)
for ct in ['mainstream','meme']:
    print('\n{}:'.format('主流币' if ct == 'mainstream' else 'Meme币'))
    for sym, pred in sorted(predictions[ct].items(), key=lambda x: -x[1]['signal']):
        emoji = '📈' if pred['direction']=='UP' else '📉' if pred['direction']=='DOWN' else '➡️'
        print('  {} {} 信号{:+.2f} 预测:{:+.1f}% 杠杆: {:.1f}x {}'.format(
            sym, pred['market'][:3], pred['signal'], pred['lev_pred'], pred['leverage'], emoji))

print('\n'+'='*80)
