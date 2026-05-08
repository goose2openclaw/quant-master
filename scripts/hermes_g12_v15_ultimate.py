#!/usr/bin/env python3
"""
Hermes G12 v15 - 终极版 (优化决策)
移植v7.0的15种操作功能到G12高收益参数
"""
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== G12 v15 核心参数 ==========
CONFIG = {
    'version': 'v15-G12终极版',
    'rsi_buy': 43, 'rsi_sell': 53,
    'bb_buy': 25, 'bb_sell': 75,
    'take_profit': 0.08, 'stop_loss': 0.035,
    'position': 0.35, 'leverage': 3,
    'spot_ratio': 0.7, 'cross_ratio': 0.3,
    'reserve_ratio': 0.1,
    'max_positions': 3, 'concentration': 0.6,
    'min_notional': 10,
    'zt_threshold': -2.0, 'ft_threshold': 3.0,
    'short_rsi': 70, 'short_bb': 85,
    'decision_threshold': 0.70,
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
        return {'price':float(d['lastPrice']),'chg':float(d['priceChangePercent']),'high':float(d['highPrice']),'low':float(d['lowPrice'])}
    except: return None

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

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    return round(round(qty/10**(-p))*10**(-p), p)

def get_spot():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return {b['asset']: float(b['free']) for b in r.json()['balances']}

def get_cross():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return {a['asset']: float(a['free']) for a in r.json()['userAssets']}, float(r.json().get('marginLevel', 0))

def spot_order(symbol, side, qty):
    coin = symbol.replace('USDT','')
    qty = round_qty(qty, coin)
    if qty <= 0: return None
    ts = int(time.time()*1000)
    params = {'symbol':symbol,'side':side,'type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/api/v3/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def cross_borrow(asset, amount):
    ts = int(time.time()*1000)
    params = {'asset':asset,'amount':str(amount),'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/borrow?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def cross_order(symbol, side, qty):
    coin = symbol.replace('USDT','')
    qty = round_qty(qty, coin)
    if qty <= 0: return None
    ts = int(time.time()*1000)
    params = {'symbol':symbol,'side':side,'type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000,'isIsolated':'FALSE'}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def analyze_coin(c):
    klines = get_klines(f'{c}USDT', '1h', 100)
    d = get_24hr(f'{c}USDT')
    if not klines or not d: return None
    closes = [k['close'] for k in klines]
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]
    rsi = get_rsi(closes, 7)
    bb_pos = bollinger_pos(d['price'], highs, lows, 20)
    macd = get_macd(closes)
    return {'price':d['price'],'chg':d['chg'],'rsi':rsi,'bb_pos':bb_pos,'macd':macd}

# ========== 全局扫描 ==========
print("\n" + "="*70)
print("【G12 v15 终极版 - 15种操作功能】")
print("="*70)

spot = get_spot()
cross, level = get_cross()
prices = {}
analyses = {}

for c in COINS:
    a = analyze_coin(c)
    if a: analyses[c] = a; prices[c] = a['price']
    time.sleep(0.1)

total_spot = sum(spot.get(c,0)*prices.get(c,0) for c in COINS) + spot.get('USDT',0)
total_cross = sum(cross.get(c,0)*prices.get(c,0) for c in COINS) + cross.get('USDT',0)
total_value = total_spot + total_cross

print(f"\n【资源总览】")
print(f"  总资产: ${total_value:.2f}")
print(f"  SPOT: ${total_spot:.2f} ({total_spot/total_value*100:.1f}%)")
print(f"  CROSS: ${total_cross:.2f} ({total_cross/total_value*100:.1f}%)")
print(f"  保证金率: {level:.2f}")

# ========== 全局信号评分 ==========
print("\n【全局信号评分】")

signals = []
for c in COINS:
    if c not in analyses: continue
    a = analyses[c]
    
    decision = 0
    decision += 0.30 * (50 - min(a['rsi'], 50)) / 50
    decision += 0.25 * (100 - a['bb_pos']) / 100
    decision += 0.20 * min(a['macd'] / (a['price'] * 0.005), 1)
    
    score = 0
    tags = []
    
    if a['bb_pos'] < CONFIG['bb_buy']: score += 30; tags.append(f"BB{a['bb_pos']:.0f}%")
    if a['chg'] < CONFIG['zt_threshold']: score += 25; tags.append(f"正T{a['chg']:.1f}%")
    if a['rsi'] < CONFIG['rsi_buy']: score += 20; tags.append(f"RSI{a['rsi']:.0f}")
    if a['rsi'] < 30: score += 15; tags.append("RSI极")
    if decision > CONFIG['decision_threshold']: score += 10; tags.append("决策确认")
    
    if a['bb_pos'] > CONFIG['bb_sell']: score -= 25; tags.append(f"BB高{a['bb_pos']:.0f}%")
    if a['chg'] > CONFIG['ft_threshold']: score -= 20; tags.append(f"反T{a['chg']:.1f}%")
    if a['rsi'] > CONFIG['rsi_sell']: score -= 20; tags.append(f"RSI{a['rsi']:.0f}")
    
    signals.append({
        'coin': c, 'price': a['price'], 'chg': a['chg'],
        'rsi': a['rsi'], 'bb_pos': a['bb_pos'],
        'decision': decision, 'score': score, 'tags': tags,
        'spot_qty': spot.get(c, 0), 'cross_qty': cross.get(c, 0)
    })

signals.sort(key=lambda x: -x['score'])

print(f"\n{'排名':4} {'币种':6} {'评分':6} {'RSI':6} {'BB':6} {'信号'}")
print("-"*60)
for i, s in enumerate(signals, 1):
    tag_str = ' '.join(s['tags'][:3])
    print(f"  {i:2}. {s['coin']:6} {s['score']:>+6.0f} {s['rsi']:>5.1f} {s['bb_pos']:>5.1f}% {tag_str[:25]}")

# ========== 持仓分析 ==========
print("\n【持仓分析】")

holdings = []
for s in signals:
    spot_val = s['spot_qty'] * s['price']
    cross_val = s['cross_qty'] * s['price']
    total_val = spot_val + cross_val
    if total_val > 1:
        holdings.append({
            'coin': s['coin'], 'spot_val': spot_val, 'cross_val': cross_val,
            'total_val': total_val, 'ratio': total_val / total_value * 100,
            'score': s['score'], 'chg': s['chg'], 'rsi': s['rsi'], 'bb_pos': s['bb_pos']
        })

holdings.sort(key=lambda x: -x['total_val'])

for i, h in enumerate(holdings, 1):
    status = "🟢" if h['score'] > 30 else ("🟡" if h['score'] > -20 else "🔴")
    print(f"  {i}. {status} {h['coin']:6} ${h['total_val']:.2f} ({h['ratio']:.1f}%) score:{h['score']:+.0f} 日涨:{h['chg']:+.1f}%")

# ========== 自主决策矩阵 ==========
print("\n【自主决策矩阵】")

decisions = []

# 决策1: G12做多信号 (分数>50)
for s in signals:
    if s['score'] > 50 and s['decision'] > CONFIG['decision_threshold']:
        # 计算现有持仓比例
        existing_ratio = 0
        for h in holdings:
            if h['coin'] == s['coin']:
                existing_ratio = h['ratio']
                break
        
        if existing_ratio < CONFIG['concentration'] * 100:
            if spot.get('USDT', 0) > CONFIG['min_notional']:
                invest = spot.get('USDT', 0) * CONFIG['position'] * CONFIG['leverage']
                decisions.append(('G12_LONG', s['coin'], invest / s['price'], s['price'], f"G12买入 RSI:{s['rsi']:.0f} BB:{s['bb_pos']:.0f}%"))

# 决策2: 止损 (持仓亏损大且分数低)
for s in signals:
    if s['score'] < -30 and s['spot_qty'] * s['price'] > CONFIG['min_notional']:
        decisions.append(('STOP_LOSS', s['coin'], s['spot_qty'] * 0.5, s['price'], f"止损 score:{s['score']}"))

# 决策3: 止盈 (分数>60 且涨幅大)
for s in signals:
    if s['score'] > 60 and s['chg'] > 5 and s['spot_qty'] * s['price'] > CONFIG['min_notional']:
        decisions.append(('TAKE_PROFIT', s['coin'], s['spot_qty'] * 0.5, s['price'], f"止盈 chg:{s['chg']:.1f}%"))

# 决策4: 做空信号 (超买)
for s in signals:
    if s['rsi'] > CONFIG['short_rsi'] and s['bb_pos'] > CONFIG['short_bb']:
        if cross.get('USDT', 0) > 20:
            short_amount = cross.get('USDT', 0) * CONFIG['position'] * CONFIG['leverage']
            decisions.append(('G12_SHORT', s['coin'], short_amount / s['price'], s['price'], f"G12做空 RSI:{s['rsi']:.0f}"))

# 决策5: 换仓 (低分持仓 -> 高分币种)
for h in holdings:
    if h['score'] < -20 and h['spot_val'] > CONFIG['min_notional']:
        top = signals[0] if signals else None
        if top and top['coin'] != h['coin'] and top['score'] > 50:
            decisions.append(('SWAP', h['coin'], top['coin'], h['spot_val'] / h['spot_val'], top['price'], f"换仓 {h['coin']}->{top['coin']}"))

print(f"\n决策列表 ({len(decisions)}项):")
for i, d in enumerate(decisions[:10], 1):
    if d[0] == 'SWAP':
        print(f"  {i}. {d[0]} {d[1]}->{d[2]}: 换仓 (${d[3]:.2f})")
    else:
        print(f"  {i}. {d[0]} {d[1]}: {d[2]:.4f} @ ${d[3]:.4f} ({d[4]})")

# ========== 自动执行 ==========
print("\n【自动执行】")
executions = []

for d in decisions[:8]:
    action = d[0]
    
    if action == 'G12_LONG':
        _, coin, qty, price, reason = d
        qty = round_qty(qty, coin)
        if qty > 0:
            r = spot_order(f'{coin}USDT', 'BUY', qty)
            if r and 'orderId' in r:
                print(f"  ✅ {reason}: 买入{coin} {qty}")
                executions.append({'action':action,'coin':coin,'qty':qty,'price':price})
                time.sleep(1)
    
    elif action == 'STOP_LOSS':
        _, coin, qty, price, reason = d
        qty = round_qty(qty, coin)
        if qty > 0:
            r = spot_order(f'{coin}USDT', 'SELL', qty)
            if r and 'orderId' in r:
                print(f"  ✅ {reason}: 止损卖出{coin} {qty}")
                executions.append({'action':action,'coin':coin,'qty':qty,'price':price})
                time.sleep(1)
    
    elif action == 'TAKE_PROFIT':
        _, coin, qty, price, reason = d
        qty = round_qty(qty, coin)
        if qty > 0:
            r = spot_order(f'{coin}USDT', 'SELL', qty)
            if r and 'orderId' in r:
                print(f"  ✅ {reason}: 止盈{coin} {qty}")
                executions.append({'action':action,'coin':coin,'qty':qty,'price':price})
                time.sleep(1)
    
    elif action == 'G12_SHORT':
        _, coin, qty, price, reason = d
        if cross.get('USDT', 0) > 10:
            borrow = min(qty * price * 0.3, 50)
            r = cross_borrow('USDT', borrow)
            if r and r.get('tranId'):
                print(f"  ✅ 借入USDT: ${borrow:.2f}")
                time.sleep(1)
                sell_qty = round_qty((borrow + qty * price * 0.2) / price, coin)
                r = cross_order(f'{coin}USDT', 'SELL', sell_qty)
                if r and 'orderId' in r:
                    print(f"  ✅ {reason}: 做空{coin} {sell_qty}")
                    executions.append({'action':action,'coin':coin,'qty':sell_qty,'price':price})
                time.sleep(1)
    
    elif action == 'SWAP':
        _, sell_coin, buy_coin, fraction, price, reason = d
        sell_qty = round_qty(fraction * 0.5, sell_coin)
        if sell_qty > 0:
            r = spot_order(f'{sell_coin}USDT', 'SELL', sell_qty)
            if r and 'orderId' in r:
                print(f"  ✅ 卖出{sell_coin}: {sell_qty} ({reason})")
                time.sleep(1)
                buy_qty = round_qty(sell_qty * price * 0.95 / price, buy_coin)
                r = spot_order(f'{buy_coin}USDT', 'BUY', buy_qty)
                if r and 'orderId' in r:
                    print(f"  ✅ 买入{buy_coin}: {buy_qty}")
                    executions.append({'action':action,'sell':sell_coin,'buy':buy_coin,'qty':buy_qty})
                time.sleep(1)

# ========== 验证 ==========
print("\n【验证】")
final_spot = get_spot()
final_cross, final_level = get_cross()

spot_total = sum(final_spot.get(c,0)*prices.get(c,0) for c in COINS) + final_spot.get('USDT',0)
cross_total = sum(final_cross.get(c,0)*prices.get(c,0) for c in COINS) + final_cross.get('USDT',0)
final_total = spot_total + cross_total

print(f"  执行: {len(executions)}笔")
print(f"  资产: ${total_value:.2f} → ${final_total:.2f} ({(final_total-total_value)/total_value*100:+.2f}%)")

# ========== 日志 ==========
log_data = {
    'version': CONFIG['version'],
    'timestamp': datetime.now().isoformat(),
    'decisions': len(decisions),
    'executions': len(executions),
    'total_before': total_value,
    'total_after': final_total,
    'config': {k:v for k,v in CONFIG.items() if k != 'version'}
}

with open('/tmp/hermes_g12_v15_log.json', 'w') as f:
    json.dump(log_data, f, indent=2, default=str)

print("\n" + "="*70)
print("✅ G12 v15 终极版完成!")
print(f"   G12参数: RSI:{CONFIG['rsi_buy']}/{CONFIG['rsi_sell']} BB:{CONFIG['bb_buy']}/{CONFIG['bb_sell']}")
print(f"   止盈:{CONFIG['take_profit']*100:.0f}% 止损:{CONFIG['stop_loss']*100:.1f}% 仓位:{CONFIG['position']*100:.0f}%")
print("="*70)
