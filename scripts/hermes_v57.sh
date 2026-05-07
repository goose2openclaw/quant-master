#!/bin/bash
# Hermes v5.7 - 资金优化+币种转换版
LOG_FILE="/tmp/hermes_v57.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "Hermes v5.7 $(date)"
echo "资金优化+币种转换版"
echo "=========================================="
python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
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
print("\n【1. 全域扫描 & 评分】")
opportunities = []
prices_dict = {}

for c in COINS:
    d = get_24hr(f'{c}USDT')
    if not d: continue
    klines = get_klines(f'{c}USDT', 7)
    prices = [k['close'] for k in klines] if klines else [d['price']]
    rsi = get_rsi(prices)
    pos = bollinger_pos(d['price'], d['high'], d['low'])
    
    # 综合评分
    score = 0
    action = None
    # 做多机会
    if pos < 25 and rsi < 40:
        score = (25-pos)*4 + (40-rsi)*3
        action = 'BUY'
    # 做空机会
    elif pos > 75 and rsi > 60:
        score = (pos-75)*4 + (rsi-60)*3
        action = 'SELL'
    # 反弹机会
    elif d['chg'] < -3 and pos < 30:
        score = abs(d['chg'])*3 + (30-pos)*2
        action = 'BUY'
    
    prices_dict[c] = d['price']
    opportunities.append({
        'coin': c, 'action': action, 'score': score,
        'pos': pos, 'rsi': rsi, 'chg': d['chg'], 'price': d['price']
    })
    emoji = '📈' if action == 'BUY' else '📉' if action == 'SELL' else '➡️'
    print(f"  {c:5}: ${d['price']:.4f} {d['chg']:+.2f}% 位置:{pos:.0f}% RSI:{rsi:.0f} {emoji} {score:.0f}分")
    time.sleep(0.1)

opportunities.sort(key=lambda x: -x['score'])

# === 账户 & 资金优化 ===
print("\n【2. 账户诊断 & 资金优化】")
spot = get_spot()
usdt = spot.get('USDT', 0)
total = usdt
positions = {}

for c in COINS:
    if c in spot and spot[c] > 0.01:
        val = spot[c] * prices_dict.get(c, get_price(f'{c}USDT'))
        total += val
        positions[c] = {'qty': spot[c], 'value': val, 'price': prices_dict.get(c, get_price(f'{c}USDT'))}

for c in COINS:
    if c in positions:
        ratio = positions[c]['value']/total*100 if total > 0 else 0
        print(f"  {c:5}: {positions[c]['qty']:.4f} (${positions[c]['value']:.2f}) {ratio:.1f}%")

print(f"\n  USDT: ${usdt:.2f}")
print(f"  总资产: ${total:.2f}")

# === 币种转换决策 ===
print("\n【3. 币种转换决策】")
print("  评估持有币种是否应转换为更高机会币种...")

convert_decisions = []

# 找到最低分持仓和最高分机会
if positions and opportunities:
    # 最低分持仓
    low_score_coin = None
    low_score = 999
    for c in positions:
        for opp in opportunities:
            if opp['coin'] == c:
                if opp['score'] < low_score:
                    low_score = opp['score']
                    low_score_coin = c
                break
    
    # 最高分机会
    high_score_opp = opportunities[0] if opportunities else None
    
    # 如果持仓分数低，机会分数高，则转换
    if low_score_coin and high_score_opp and low_score_coin != high_score_opp['coin']:
        if low_score < high_score_opp['score'] * 0.5:  # 分数差距大于50%
            convert_decisions.append({
                'from': low_score_coin,
                'to': high_score_opp['coin'],
                'reason': f"{low_score_coin}({low_score:.0f}分) -> {high_score_opp['coin']}({high_score_opp['score']:.0f}分)"
            })
            print(f"  🔄 建议转换: {low_score_coin} -> {high_score_opp['coin']} (机会更好)")

# === 执行币种转换 ===
print("\n【4. 执行币种转换】")
for conv in convert_decisions:
    from_c = conv['from']
    to_c = conv['to']
    
    if from_c in positions and positions[from_c]['qty'] > 0:
        # 卖出低分币
        sell_qty = round_qty(positions[from_c]['qty'] * 0.5, from_c)
        if sell_qty > 0:
            result = spot_order(f'{from_c}USDT', 'SELL', sell_qty)
            time.sleep(1)
            if result and 'orderId' in result:
                revenue = sell_qty * positions[from_c]['price']
                usdt += revenue
                positions[from_c]['qty'] -= sell_qty
                positions[from_c]['value'] -= revenue
                print(f"  ✅ 卖出 {from_c}: {sell_qty} -> ${revenue:.2f}")
                
                # 买入高分币
                to_price = prices_dict.get(to_c, get_price(f'{to_c}USDT'))
                buy_qty = round_qty(usdt * 0.9 / to_price, to_c)
                if buy_qty > 0:
                    result2 = spot_order(f'{to_c}USDT', 'BUY', buy_qty)
                    time.sleep(1)
                    if result2 and 'orderId' in result2:
                        cost = buy_qty * to_price
                        usdt -= cost
                        if to_c in positions:
                            positions[to_c]['qty'] += buy_qty
                            positions[to_c]['value'] += cost
                        else:
                            positions[to_c] = {'qty': buy_qty, 'value': cost, 'price': to_price}
                        print(f"  ✅ 买入 {to_c}: {buy_qty} <- ${cost:.2f}")

# === 科学决策 & 执行 ===
print("\n【5. 科学决策 & 执行】")
decisions = []

for opp in opportunities[:4]:
    c = opp['coin']
    action = opp['action']
    price = opp['price']
    
    if action == 'BUY' and usdt > 10:
        qty = round_qty(usdt * 0.9 / price, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'BUY','qty':qty,'action':action})
            print(f"  📈 BUY {c}: {qty} @ ${price:.4f}")
    
    elif action == 'SELL' and c in positions and positions[c]['qty'] > 0:
        qty = round_qty(positions[c]['qty'] * 0.5, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'SELL','qty':qty,'action':action})
            print(f"  📉 SELL {c}: {qty} @ ${price:.4f}")

success = fail = 0
for d in decisions:
    result = spot_order(f"{d['coin']}USDT", d['side'], d['qty'])
    time.sleep(0.5)
    if result and 'orderId' in result:
        print(f"  ✅ {d['action']} {d['coin']} {d['qty']}")
        success += 1
    else:
        print(f"  ❌ {d['coin']}: {result.get('msg','')[:30] if result else 'err'}")
        fail += 1

# === 验证汇报 ===
print("\n【6. 验证汇报】")
new_spot = get_spot()
new_usdt = new_spot.get('USDT', 0)
new_total = sum(new_spot.get(c, 0) * prices_dict.get(c, get_price(f'{c}USDT')) for c in COINS) + new_usdt

print(f"  执行: {success}成功, {fail}失败")
print(f"  USDT: ${usdt:.2f} -> ${new_usdt:.2f}")
print(f"  资产: ${total:.2f} -> ${new_total:.2f} ({(new_total-total)/total*100:+.2f}%)")

# 资金使用率
used_ratio = (total - new_usdt) / new_total * 100 if new_total > 0 else 0
print(f"  资金使用率: {used_ratio:.1f}%")

print("\n✅ Hermes v5.7 完成")
PYEOF
