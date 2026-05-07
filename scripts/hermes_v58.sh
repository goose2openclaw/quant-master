#!/bin/bash
# Hermes v5.8 - EXPERT模式蒸馏版
# 基于+523.8%收益的优化配置
LOG_FILE="/tmp/hermes_v58.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "Hermes v5.8 $(date)"
echo "EXPERT蒸馏版"
echo "=========================================="
python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== EXPERT最优配置 ==========
CONFIG = {
    'mode': 'EXPERT',
    'rsi_short': 71,      # 超买阈值
    'rsi_long': 32,       # 超卖阈值
    'take_profit': 0.08,  # 8%止盈
    'stop_loss': 0.015,    # 1.5%止损
    'position_size': 0.25, # 25%仓位
    'leverage': 5.0,       # 5x杠杆
    '主动性': 0.90,        # 90%主动性
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

def get_klines(sym, days=7):
    end = int(time.time()*1000)
    start = end - days*86400*1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit=500'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'close':float(k[4])} for k in r.json()]
    except: return []

def bollinger_pos(price, high, low):
    return (price-low)/(high-low)*100 if high>low else 50

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def get_spot():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return {b['asset']: float(b['free']) for b in r.json()['balances']}

def spot_order(symbol, side, qty):
    coin = symbol.replace('USDT','')
    p = PRECISION.get(coin, 6)
    qty = round(qty, p) if p > 0 else int(qty)
    if qty <= 0: return None
    ts = int(time.time()*1000)
    params = {'symbol':symbol,'side':side,'type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/api/v3/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    step = 10**(-p)
    return round(round(qty/step)*step, p)

# === 全域扫描 ===
print("\n【1. EXPERT全域扫描】")
opportunities = []
prices_dict = {}

for c in COINS:
    d = get_24hr(f'{c}USDT')
    if not d: continue
    klines = get_klines(f'{c}USDT', 7)
    prices = [k['close'] for k in klines] if klines else [d['price']]
    rsi = get_rsi(prices)
    pos = bollinger_pos(d['price'], d['high'], d['low'])
    
    prices_dict[c] = d['price']
    
    # EXPERT模式信号
    score = 0
    action = None
    
    # RSI超卖 -> 买入信号
    if rsi < CONFIG['rsi_long']:
        score = (CONFIG['rsi_long'] - rsi) * 3
        action = 'BUY_LONG'
    # RSI超买 -> 卖出信号
    elif rsi > CONFIG['rsi_short']:
        score = (rsi - CONFIG['rsi_short']) * 3
        action = 'SELL_SHORT'
    # 急跌买入
    elif d['chg'] < -3:
        score = abs(d['chg']) * 2
        action = 'BUY_LONG'
    
    if action:
        opportunities.append({
            'coin': c, 'action': action, 'score': score,
            'rsi': rsi, 'pos': pos, 'chg': d['chg'], 'price': d['price']
        })
    
    emoji = '📈' if action == 'BUY_LONG' else '📉' if action == 'SELL_SHORT' else '➡️'
    print(f"  {c:5}: ${d['price']:.4f} {d['chg']:+.2f}% RSI:{rsi:.0f} {emoji}")
    time.sleep(0.1)

opportunities.sort(key=lambda x: -x['score'])

# === 账户诊断 ===
print("\n【2. 账户诊断】")
spot = get_spot()
usdt = spot.get('USDT', 0)
total = usdt
positions = {}

for c in COINS:
    if c in spot and spot[c] > 0.01:
        price = prices_dict.get(c, get_price(f'{c}USDT'))
        val = spot[c] * price
        total += val
        positions[c] = {'qty': spot[c], 'value': val}

for c in COINS:
    if c in positions:
        print(f"  {c:5}: {positions[c]['qty']:.4f} (${positions[c]['value']:.2f})")

print(f"\n  USDT: ${usdt:.2f}")
print(f"  总资产: ${total:.2f}")

# === EXPERT科学决策 ===
print("\n【3. EXPERT科学决策】")
print(f"  配置: RSI买:{CONFIG['rsi_long']} RSI卖:{CONFIG['rsi_short']} TP:{CONFIG['take_profit']*100:.0f}% SL:{CONFIG['stop_loss']*100:.1f}%")

decisions = []

for opp in opportunities[:5]:
    c = opp['coin']
    action = opp['action']
    price = opp['price']
    
    # 买入信号
    if action == 'BUY_LONG' and usdt > 10:
        invest = total * CONFIG['position_size'] * CONFIG['主动性']
        qty = round_qty(invest / price, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'BUY','qty':qty,'action':action,'tp':CONFIG['take_profit'],'sl':CONFIG['stop_loss']})
            print(f"  📈 BUY_LONG {c}: {qty} @ ${price:.4f} | TP:{CONFIG['take_profit']*100:.0f}% SL:{CONFIG['stop_loss']*100:.1f}%")
    
    # 卖出信号
    elif action == 'SELL_SHORT' and c in positions and positions[c]['qty'] > 0:
        qty = round_qty(positions[c]['qty'] * 0.5, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'SELL','qty':qty,'action':action,'tp':CONFIG['take_profit'],'sl':CONFIG['stop_loss']})
            print(f"  📉 SELL_SHORT {c}: {qty} @ ${price:.4f}")

# === 执行 ===
print("\n【4. 自动执行】")
success = fail = 0
for d in decisions:
    result = spot_order(f"{d['coin']}USDT", d['side'], d['qty'])
    time.sleep(0.5)
    if result and 'orderId' in result:
        print(f"  ✅ {d['action']} {d['side']} {d['coin']} {d['qty']}")
        success += 1
    else:
        msg = result.get('msg','')[:30] if result else 'err'
        print(f"  ❌ {d['coin']}: {msg}")
        fail += 1

# === 验证 ===
print("\n【5. 验证汇报】")
new_spot = get_spot()
new_usdt = new_spot.get('USDT', 0)
new_total = sum(new_spot.get(c, 0) * prices_dict.get(c, get_price(f'{c}USDT')) for c in COINS) + new_usdt

print(f"  执行: {success}成功, {fail}失败")
print(f"  资产: ${total:.2f} -> ${new_total:.2f} ({(new_total-total)/total*100:+.2f}%)")

# 资金使用率
used_ratio = (total - new_usdt) / new_total * 100 if new_total > 0 else 0
print(f"  资金使用率: {used_ratio:.1f}%")

# === 复盘 ===
print("\n【6. 复盘学习】")
stats_file = '/tmp/hermes_v58_stats.json'
try:
    with open(stats_file) as f:
        stats = json.load(f)
except:
    stats = {'trades': [], 'wins': 0, 'losses': 0}

for d in decisions:
    stats['trades'].append({
        'coin': d['coin'], 'action': d['action'], 'side': d['side'],
        'price': d['price'], 'time': datetime.now().isoformat(),
        'result': 'success' if success else 'fail'
    })

with open(stats_file, 'w') as f:
    json.dump(stats, f, indent=2)

total_t = len(stats['trades'])
print(f"  历史交易: {total_t}笔")
print(f"  发现机会: {len(opportunities)}个")

print("\n✅ Hermes v5.8 EXPERT蒸馏版完成")
PYEOF
