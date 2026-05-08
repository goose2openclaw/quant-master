#!/usr/bin/env python3
"""
Hermes G12 v7 Ultimate - 高收益蒸馏版
集成: Scalping+Martingale+DCA+Momentum+Bollinger Scalping+Funding Arbitrage
目标: 收益400%+/月
"""
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_24hr(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', proxies=PROXIES, timeout=5)
        d = r.json()
        return {'price':float(d['lastPrice']),'chg':float(d['priceChangePercent']),'volume':float(d['quoteVolume']),'high':float(d['highPrice']),'low':float(d['lowPrice'])}
    except: return None

def get_klines(sym, interval='1h', limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'open':float(k[1]),'high':float(k[2]),'low':float(k[3]),'close':float(k[4]),'volume':float(k[5])} for k in r.json()]
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

def get_macd(prices, fast=12, slow=26):
    if len(prices) < slow+1: return 0
    return np.mean(prices[-fast:]) - np.mean(prices[-slow:])

def get_atr(klines, period=14):
    if len(klines) < period+1: return 0
    trs = []
    for i in range(1, min(period+1, len(klines))):
        tr = max(klines[i]['high']-klines[i]['low'], abs(klines[i]['high']-klines[i-1]['close']), abs(klines[i]['low']-klines[i-1]['close']))
        trs.append(tr)
    return np.mean(trs) if trs else 0

# G12 v7 终极配置
CONFIG = {
    # Scalping配置
    'scalping': {
        'enabled': True,
        'profit_target': 0.005,  # 0.5%止盈
        'stop_loss': 0.002,      # 0.2%止损
        'max_positions': 5,
    },
    # Martingale配置
    'martingale': {
        'enabled': True,
        'multiplier': 2.0,       # 亏损加倍
        'max_loss_count': 5,    # 最多连续亏损5次
        'recovery_target': 0.10, # 10%恢复目标
    },
    # DCA配置
    'dca': {
        'enabled': True,
        'buy_depths': [0.02, 0.05, 0.10],  # 每跌2%,5%,10%补仓
        'buy_ratios': [1.0, 1.5, 2.0],        # 补仓比例
    },
    # Momentum配置
    'momentum': {
        'enabled': True,
        'threshold': 0.02,       # 2%动量确认
        'atr_multiplier': 2.0,
    },
    # Bollinger Scalping
    'bb_scalp': {
        'enabled': True,
        'touch_threshold': 0.01,  # 触及布林1%
        'reversion_target': 0.005, # 回归0.5%目标
    },
    # Funding Rate Arbitrage
    'arbitrage': {
        'enabled': True,
        'min_rate_diff': 0.01,   # 最小费率差1%
    }
}

def calculate_signal(c, data):
    """计算综合信号"""
    signals = {}
    
    # RSI
    signals['rsi'] = data['rsi']
    signals['rsi_oversold'] = data['rsi'] < 30
    signals['rsi_overbought'] = data['rsi'] > 70
    
    # Bollinger
    signals['bb_pos'] = data['bb_pos']
    signals['bb_lower'] = data['bb_pos'] < 20
    signals['bb_upper'] = data['bb_pos'] > 80
    signals['bb_touch'] = data['bb_pos'] < 25 or data['bb_pos'] > 75
    
    # MACD
    signals['macd'] = data['macd']
    signals['macd_positive'] = data['macd'] > 0
    
    # 涨跌
    signals['chg'] = data['chg']
    signals['big_drop'] = data['chg'] < -2
    signals['big_rise'] = data['chg'] > 2
    
    # ATR
    signals['atr'] = data['atr']
    
    # 综合决策值
    decision = 0
    decision += 0.30 * (50 - min(data['rsi'], 50)) / 50
    decision += 0.25 * (100 - data['bb_pos']) / 100
    decision += 0.20 * min(data['macd'] / (data['price'] * 0.005), 1)
    decision += 0.15 * abs(min(data['chg'], 0)) / 5
    signals['decision'] = decision
    
    return signals

def get_account():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    spot_r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    cross_r = requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    spot = {b['asset']: float(b['free']) for b in spot_r.json()['balances']}
    cross_assets = {a['asset']: float(a['free']) for a in cross_r.json()['userAssets']}
    margin_level = float(cross_r.json().get('marginLevel', 0))
    return spot, cross_assets, margin_level

def analyze_coin(c):
    klines_h = get_klines(f'{c}USDT', '1h', 100)
    klines_d = get_klines(f'{c}USDT', '1d', 30)
    d = get_24hr(f'{c}USDT')
    if not klines_h or not d: return None
    
    closes = [k['close'] for k in klines_h]
    highs = [k['high'] for k in klines_h]
    lows = [k['low'] for k in klines_h]
    
    return {
        'coin': c,
        'price': d['price'],
        'chg': d['chg'],
        'volume': d.get('volume', 0),
        'rsi': get_rsi(closes, 7),
        'bb_pos': bollinger_pos(d['price'], highs, lows, 20),
        'macd': get_macd(closes),
        'atr': get_atr(klines_h),
        'klines': klines_h
    }

# 主扫描
print("="*70)
print("Hermes G12 v7 Ultimate - 高收益蒸馏版")
print("集成: Scalping+Martingale+DCA+Momentum+BB Scalp+Arbitrage")
print("="*70)

# 全域扫描
SCAN_COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BNB','AVAX','MATIC','DOT','UNI','LTC','ATOM','FIL','XLM','NEAR','AAVE','MKR','SNX']

print(f"\n【G12 v7 全域扫描】{len(SCAN_COINS)}个币种")

results = []
for c in SCAN_COINS:
    a = analyze_coin(c)
    if a:
        a['signals'] = calculate_signal(c, a)
        results.append(a)
    time.sleep(0.05)

results.sort(key=lambda x: -x['signals']['decision'])

print(f"\n{'币种':8} {'决策':6} {'RSI':6} {'BB':7} {'涨跌':8} {'信号'}")
print("-"*55)
for r in results[:12]:
    s = r['signals']
    sigs = []
    if s['rsi_oversold']: sigs.append("RSI买")
    if s['rsi_overbought']: sigs.append("RSI卖")
    if s['bb_lower']: sigs.append("BB买")
    if s['bb_upper']: sigs.append("BB卖")
    if s['big_drop']: sigs.append("大跌")
    if s['big_rise']: sigs.append("大涨")
    sig_str = ','.join(sigs) if sigs else "-"
    print(f"{r['coin']:8} {s['decision']:>6.2f} {s['rsi']:>5.1f} {s['bb_pos']:>6.1f}% {r['chg']:>+7.2f}% {sig_str}")

# 账户
spot, cross_assets, margin_level = get_account()
prices = {r['coin']: r['price'] for r in results}
total_spot = sum(spot.get(c, 0) * prices.get(c, 0) for c in prices) + spot.get('USDT', 0)
total_cross = sum(cross_assets.get(c, 0) * prices.get(c, 0) for c in prices) + cross_assets.get('USDT', 0)
total = total_spot + total_cross

print(f"\n【G12 v7 账户】")
print(f"  总资产: ${total:.2f}")
print(f"  SPOT: ${total_spot:.2f} ({total_spot/total*100:.1f}%)")
print(f"  CROSS: ${total_cross:.2f} ({total_cross/total*100:.1f}%)")

# 高收益策略信号
print(f"\n【高收益策略信号】")

for r in results[:5]:
    s = r['signals']
    c = r['coin']
    
    # Scalping信号
    if s['bb_touch'] and abs(s['decision'] - 0.5) < 0.3:
        print(f"  Scalping: {c} - 布林触及,快进快出")
    
    # DCA信号
    if s['big_drop'] and s['rsi_oversold']:
        print(f"  DCA: {c} - 大跌+超卖,分批补仓")
    
    # Momentum信号
    if s['big_rise'] and s['macd_positive']:
        print(f"  Momentum: {c} - 大涨+MACD正,追入")
    
    # Martingale信号
    if s['rsi_oversold'] and s['decision'] < 0.3:
        print(f"  Martingale: {c} - RSI超卖,准备加倍仓")
    
    # BB Scalping信号
    if s['bb_pos'] < 15:
        print(f"  BB Scalp: {c} - 布林下轨,反弹快卖")

print(f"\n✅ G12 v7 Ultimate 扫描完成!")

with open('/tmp/g12_v7_scan.json', 'w') as f:
    json.dump({'time':datetime.now().isoformat(),'results':[{'coin':r['coin'],'decision':r['signals']['decision'],'rsi':r['signals']['rsi'],'bb_pos':r['signals']['bb_pos'],'chg':r['chg']} for r in results[:20]]}, f, indent=2, default=str)
