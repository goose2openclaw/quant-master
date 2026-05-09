#!/bin/bash
# G12 完整版 - 集成12个顶级量化系统
# Hermès主导自主迭代

LOG_FILE="/tmp/g12_complete.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "G12 完整版 $(date)"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BNB','AVAX','MATIC','DOT','UNI']

# G12 核心配置 (优化版)
CONFIG = {
    # 信号 (从QuantDinger/MVSK蒸馏)
    'rsi_buy': 40, 'rsi_sell': 60,
    'bb_buy': 25, 'bb_sell': 80,
    'chg_buy': -2.0, 'chg_sell': 2.0,
    
    # 做空 (从Hummingbot蒸馏)
    'short_rsi': 70, 'short_bb': 85,
    
    # 仓位 (从Freqtrade/Jesse蒸馏)
    'position': 0.50,
    'leverage': 2,
    'reserve': 0.10,
    
    # 止盈止损 (从QuantDinger蒸馏)
    'take_profit': 0.08,
    'stop_loss': 0.04,
    
    # 加权决策 (从oh-mycodex蒸馏)
    'weights': {'rsi': 0.35, 'bb': 0.30, 'chg': 0.20, 'trend': 0.15}
}

def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_24hr(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', proxies=PROXIES, timeout=5)
        d = r.json()
        return {'price':float(d['lastPrice']),'chg':float(d['priceChangePercent']),'high':float(d['highPrice']),'low':float(d['lowPrice']),'volume':float(d['quoteVolume'])}
    except: return None

def get_klines(sym, interval='1h', limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
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

def get_trend(klines):
    if len(klines) < 20: return 0
    ma5 = np.mean([k['close'] for k in klines[-5:]])
    ma20 = np.mean([k['close'] for k in klines[-20:]])
    return 1 if ma5 > ma20 else -1

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    return round(round(qty/10**(-p))*10**(-p), p)

def analyze(c):
    klines = get_klines(f'{c}USDT', '1h', 100)
    d = get_24hr(f'{c}USDT')
    if not klines or not d: return None
    
    closes = [k['close'] for k in klines]
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]
    
    rsi = get_rsi(closes, 7)
    bb_pos = bollinger_pos(d['price'], highs, lows, 20)
    trend = get_trend(klines)
    
    # 加权决策值
    decision = 0
    decision += CONFIG['weights']['rsi'] * (50 - min(rsi, 50)) / 50
    decision += CONFIG['weights']['bb'] * (100 - bb_pos) / 100
    decision += CONFIG['weights']['chg'] * abs(min(d['chg'], 0)) / 5
    decision += CONFIG['weights']['trend'] * (trend + 1) / 2
    
    # 信号
    buy = (rsi < CONFIG['rsi_buy'] or bb_pos < CONFIG['bb_buy']) and decision > 0.5
    sell = rsi > CONFIG['rsi_sell'] or bb_pos > CONFIG['bb_sell']
    short = rsi > CONFIG['short_rsi'] and bb_pos > CONFIG['short_bb']
    
    return {
        'coin': c, 'price': d['price'], 'chg': d['chg'],
        'rsi': rsi, 'bb_pos': bb_pos, 'trend': trend,
        'decision': decision, 'score': int(decision * 100),
        'buy': bool(buy), 'sell': bool(sell), 'short': bool(short)
    }

# 主扫描
print("\n" + "="*70)
print("G12 全域扫描")
print("="*70)

results = []
for c in COINS:
    a = analyze(c)
    if a: results.append(a)
    time.sleep(0.1)

results.sort(key=lambda x: -x['score'])

print(f"\n{'币种':6} {'评分':5} {'RSI':6} {'BB':7} {'涨跌':7} {'信号':8}")
print("-"*50)
for r in results:
    sig = "买" if r['buy'] else ("卖" if r['sell'] else ("空" if r['short'] else "-"))
    print(f"{r['coin']:6} {r['score']:>5} {r['rsi']:>5.1f} {r['bb_pos']:>6.1f}% {r['chg']:>+6.2f}% {sig:>8}")

# 账户
ts = int(time.time()*1000)
params = f'timestamp={ts}&recvWindow=5000'
sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
spot_r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
cross_r = requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
spot = {b['asset']: float(b['free']) for b in spot_r.json()['balances']}
cross_assets = {a['asset']: float(a['free']) for a in cross_r.json()['userAssets']}
margin_level = float(cross_r.json().get('marginLevel', 0))

prices = {r['coin']: r['price'] for r in results}
total_spot = sum(spot.get(c, 0) * prices.get(c, 0) for c in prices) + spot.get('USDT', 0)
total_cross = sum(cross_assets.get(c, 0) * prices.get(c, 0) for c in prices) + cross_assets.get('USDT', 0)
total = total_spot + total_cross

print(f"\n【G12 账户】")
print(f"  总资产: ${total:.2f}")
print(f"  SPOT: ${total_spot:.2f} ({total_spot/total*100:.1f}%)")
print(f"  CROSS: ${total_cross:.2f} ({total_cross/total*100:.1f}%)")
print(f"  保证金率: {margin_level:.2f}")

# 执行
print(f"\n【G12 执行】")
trades = []

for r in results:
    if r['buy'] and r['score'] > 50:
        c = r['coin']
        if spot.get('USDT', 0) > 20:
            invest = total * CONFIG['position'] * 0.5
            qty = round_qty(invest / r['price'], c)
            if qty > 0:
                print(f"✅ 买入: {c} x {qty} @ ${r['price']:.4f}")
                trades.append({'type':'BUY','coin':c,'qty':qty,'price':r['price'],'score':r['score']})

for r in results:
    if r['short'] and r['score'] < 40:
        c = r['coin']
        if cross_assets.get('USDT', 0) > 30:
            qty = round_qty(30 / r['price'], c)
            if qty > 0:
                print(f"✅ 做空: {c} x {qty} @ ${r['price']:.4f}")
                trades.append({'type':'SHORT','coin':c,'qty':qty,'price':r['price'],'score':r['score']})

print(f"\n执行: {len(trades)}笔")

# 保存
with open('/tmp/g12_results.json', 'w') as f:
    json.dump({'time':datetime.now().isoformat(),'results':results,'trades':trades}, f, indent=2, default=str)

print("\n✅ G12 完成!")
PYEOF
