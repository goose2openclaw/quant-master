#!/bin/bash
# Hermes v5.9 - 全功能增强版
# 全域扫描 | 币种转换 | gstack复盘 | mirofish仿真 | 收益最大化
LOG_FILE="/tmp/hermes_v59.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "Hermes v5.9 $(date)"
echo "全功能增强版"
echo "=========================================="
python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime
from itertools import product

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# EXPERT配置
CONFIG = {
    'rsi_long': 32, 'rsi_short': 71,
    'take_profit': 0.08, 'stop_loss': 0.015,
    'position_size': 0.25, '主动性': 0.90
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

def get_klines(sym, days=30):
    end = int(time.time()*1000)
    start = end - days*86400*1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1d&startTime={start}&endTime={end}&limit=1000'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]
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

# ========== gstack复盘模拟 ==========
def gstack_review(coin, action, price, klines):
    """gstack复盘评估"""
    if not klines or len(klines) < 20:
        return {'score': 50, 'risk': 'medium', 'recommend': 'proceed'}
    
    prices = [k['close'] for k in klines]
    returns = np.diff(prices) / prices[:-1]
    
    # 计算指标
    volatility = np.std(returns) * 100
    avg_return = np.mean(returns) * 100
    max_loss = np.min(returns) * 100
    sharpe = avg_return / volatility if volatility > 0 else 0
    
    # 趋势判断
    recent = prices[-7:]
    trend = 'up' if recent[-1] > recent[0] else 'down'
    
    score = 50 + sharpe * 20 + avg_return * 5
    if action == 'BUY' and trend == 'up':
        score += 20
    elif action == 'BUY' and trend == 'down':
        score -= 10
    
    risk = 'high' if volatility > 5 else 'medium' if volatility > 2 else 'low'
    
    return {
        'score': min(100, max(0, score)),
        'risk': risk,
        'volatility': volatility,
        'trend': trend,
        'sharpe': sharpe,
        'recommend': 'proceed' if score > 40 else 'wait'
    }

# ========== mirofish 1000智能体仿真 ==========
def mirofish_simulation(coin, action, price, klines, iterations=1000):
    """mirofish 1000智能体仿真"""
    if not klines or len(klines) < 10:
        return {'success_rate': 0.5, 'avg_return': 0, 'risk_score': 50}
    
    prices = [k['close'] for k in klines]
    returns = np.diff(prices) / prices[:-1]
    
    mu = np.mean(returns)
    sigma = np.std(returns)
    
    successes = 0
    total_returns = []
    
    for _ in range(iterations):
        # 模拟价格路径
        simulated_returns = np.random.normal(mu, sigma, len(returns))
        final_price = price * np.prod(1 + simulated_returns)
        ret = (final_price - price) / price
        
        total_returns.append(ret)
        if action == 'BUY' and ret > 0:
            successes += 1
        elif action == 'SELL' and ret < 0:
            successes += 1
    
    success_rate = successes / iterations
    avg_return = np.mean(total_returns) * 100
    risk_score = np.percentile(total_returns, 5) * 100  # VaR
    
    return {
        'success_rate': success_rate,
        'avg_return': avg_return,
        'risk_score': risk_score,
        'recommend': 'proceed' if success_rate > 0.55 else 'wait'
    }

# ========== 综合评估 ==========
def comprehensive_evaluation(coin, action, price, klines):
    """综合评估: gstack + mirofish"""
    gstack = gstack_review(coin, action, price, klines)
    mirofish = mirofish_simulation(coin, action, price, klines)
    
    # 综合评分
    gstack_weight = 0.4
    mirofish_weight = 0.6
    
    combined_score = (
        gstack['score'] * gstack_weight +
        mirofish['success_rate'] * 100 * mirofish_weight
    )
    
    recommend = 'proceed'
    if gstack['risk'] == 'high' and mirofish['risk_score'] < -5:
        recommend = 'wait'
    
    return {
        'coin': coin,
        'action': action,
        'price': price,
        'gstack': gstack,
        'mirofish': mirofish,
        'combined_score': combined_score,
        'recommend': recommend
    }

# ========== 币种转换评估 ==========
def evaluate_conversion(from_coin, to_coin, positions, prices):
    """评估币种转换"""
    from_val = positions.get(from_coin, {}).get('value', 0)
    to_opp = opportunities_by_coin.get(to_coin, {})
    
    if from_val < 50 or not to_opp:
        return None
    
    # 转换收益评估
    conversion_cost = from_val * 0.001  # 手续费
    potential_gain = to_opp.get('expected_return', 0) * from_val
    
    net_gain = potential_gain - conversion_cost
    
    return {
        'from': from_coin,
        'to': to_coin,
        'from_value': from_val,
        'conversion_cost': conversion_cost,
        'potential_gain': potential_gain,
        'net_gain': net_gain,
        'recommend': net_gain > conversion_cost * 2
    }

# === MAIN ===
print("\n【1. 全域扫描 - 新趋势新机会】")
opportunities = []
prices_dict = {}
opportunities_by_coin = {}

for c in COINS:
    d = get_24hr(f'{c}USDT')
    if not d: continue
    klines = get_klines(f'{c}USDT', 30)
    prices = [k['close'] for k in klines] if klines else [d['price']]
    rsi = get_rsi(prices)
    pos = bollinger_pos(d['price'], d['high'], d['low'])
    
    prices_dict[c] = d['price']
    
    score = 0
    action = None
    
    if rsi < CONFIG['rsi_long']:
        score = (CONFIG['rsi_long'] - rsi) * 3
        action = 'BUY'
    elif rsi > CONFIG['rsi_short']:
        score = (rsi - CONFIG['rsi_short']) * 3
        action = 'SELL'
    elif d['chg'] < -3:
        score = abs(d['chg']) * 2
        action = 'BUY'
    
    if action:
        opportunities.append({'coin':c,'action':action,'score':score,'rsi':rsi,'pos':pos,'chg':d['chg'],'price':d['price'],'klines':klines})
        opportunities_by_coin[c] = {'action':action,'score':score,'rsi':rsi,'price':d['price'],'klines':klines}
    
    emoji = '📈' if action=='BUY' else '📉' if action=='SELL' else '➡️'
    print(f"  {c:5}: ${d['price']:.4f} {d['chg']:+.2f}% RSI:{rsi:.0f} {emoji}")
    time.sleep(0.1)

opportunities.sort(key=lambda x: -x['score'])

# === 账户 ===
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
        ratio = positions[c]['value']/total*100 if total > 0 else 0
        print(f"  {c:5}: {positions[c]['qty']:.4f} (${positions[c]['value']:.2f}) {ratio:.1f}%")

print(f"\n  USDT: ${usdt:.2f}")
print(f"  总资产: ${total:.2f}")

# === gstack + mirofish 综合评估 ===
print("\n【3. gstack复盘 + mirofish仿真评估】")
evaluations = []

for opp in opportunities[:5]:
    c = opp['coin']
    action = opp['action']
    price = opp['price']
    klines = opp.get('klines', [])
    
    eval_result = comprehensive_evaluation(c, action, price, klines)
    evaluations.append(eval_result)
    
    g = eval_result['gstack']
    m = eval_result['mirofish']
    
    print(f"\n  {c} {action}:")
    print(f"    gstack: 评分:{g['score']:.0f} 风险:{g['risk']} 趋势:{g['trend']}")
    print(f"    mirofish: 成功率:{m['success_rate']*100:.1f}% 预期收益:{m['avg_return']:+.2f}%")
    print(f"    综合评分: {eval_result['combined_score']:.1f} → {eval_result['recommend']}")

evaluations.sort(key=lambda x: -x['combined_score'])

# === 币种转换评估 ===
print("\n【4. 币种转换评估】")
conversions = []

if positions and opportunities:
    # 找到最低分持仓
    low_coin = min(positions.keys(), key=lambda c: opportunities_by_coin.get(c, {}).get('score', 0))
    
    # 找到最高分机会
    high_opp = opportunities[0] if opportunities else None
    
    if low_coin and high_opp and low_coin != high_opp['coin']:
        conv = evaluate_conversion(low_coin, high_opp['coin'], positions, prices_dict)
        if conv and conv['recommend']:
            conversions.append(conv)
            print(f"  🔄 建议转换: {low_coin} -> {high_opp['coin']}")
            print(f"     价值: ${conv['from_value']:.2f}")
            print(f"     成本: ${conv['conversion_cost']:.2f}")
            print(f"     潜在收益: ${conv['potential_gain']:.2f}")
            print(f"     净收益: ${conv['net_gain']:.2f}")

# === 执行币种转换 ===
print("\n【5. 执行币种转换】")
for conv in conversions:
    from_c = conv['from']
    to_c = [e for e in evaluations if e['recommend']=='proceed'][0]['coin'] if evaluations else None
    
    if to_c and from_c in positions and positions[from_c]['qty'] > 0:
        # 卖出
        sell_qty = round_qty(positions[from_c]['qty'] * 0.5, from_c)
        if sell_qty > 0:
            result = spot_order(f'{from_c}USDT', 'SELL', sell_qty)
            time.sleep(1)
            if result and 'orderId' in result:
                revenue = sell_qty * prices_dict[from_c]
                usdt += revenue
                positions[from_c]['qty'] -= sell_qty
                positions[from_c]['value'] -= revenue
                print(f"  ✅ 卖出 {from_c}: {sell_qty} -> ${revenue:.2f}")
                
                # 买入
                buy_qty = round_qty(usdt * 0.9 / prices_dict[to_c], to_c)
                if buy_qty > 0:
                    result2 = spot_order(f'{to_c}USDT', 'BUY', buy_qty)
                    time.sleep(1)
                    if result2 and 'orderId' in result2:
                        cost = buy_qty * prices_dict[to_c]
                        usdt -= cost
                        if to_c in positions:
                            positions[to_c]['qty'] += buy_qty
                            positions[to_c]['value'] += cost
                        else:
                            positions[to_c] = {'qty': buy_qty, 'value': cost}
                        print(f"  ✅ 买入 {to_c}: {buy_qty} <- ${cost:.2f}")

# === 执行最优决策 ===
print("\n【6. 执行综合评估后的决策】")
decisions = []

for eval_result in evaluations:
    if eval_result['recommend'] != 'proceed':
        continue
    c = eval_result['coin']
    action = eval_result['action']
    price = eval_result['price']
    
    if action == 'BUY' and usdt > 10:
        invest = total * CONFIG['position_size'] * CONFIG['主动性']
        qty = round_qty(invest / price, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'BUY','qty':qty,'action':action,'score':eval_result['combined_score']})
            print(f"  📈 BUY {c}: {qty} @ ${price:.4f} (评分:{eval_result['combined_score']:.0f})")
    
    elif action == 'SELL' and c in positions and positions[c]['qty'] > 0:
        qty = round_qty(positions[c]['qty'] * 0.5, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'SELL','qty':qty,'action':action,'score':eval_result['combined_score']})
            print(f"  📉 SELL {c}: {qty} @ ${price:.4f}")

# === 执行 ===
print("\n【7. 执行】")
success = fail = 0
for d in decisions:
    result = spot_order(f"{d['coin']}USDT", d['side'], d['qty'])
    time.sleep(0.5)
    if result and 'orderId' in result:
        print(f"  ✅ {d['action']} {d['side']} {d['coin']} {d['qty']}")
        success += 1
    else:
        print(f"  ❌ {d['coin']}: {result.get('msg','')[:30] if result else 'err'}")
        fail += 1

# === 验证 ===
print("\n【8. 验证汇报】")
new_spot = get_spot()
new_usdt = new_spot.get('USDT', 0)
new_total = sum(new_spot.get(c, 0) * prices_dict.get(c, get_price(f'{c}USDT')) for c in COINS) + new_usdt

print(f"  执行: {success}成功, {fail}失败")
print(f"  资产: ${total:.2f} -> ${new_total:.2f} ({(new_total-total)/total*100:+.2f}%)")
print(f"  资金使用率: {(new_total-new_usdt)/new_total*100:.1f}%")

# === 复盘学习 ===
stats_file = '/tmp/hermes_v59_stats.json'
try:
    with open(stats_file) as f:
        stats = json.load(f)
except:
    stats = {'trades': [], 'evaluations': []}

for d in decisions:
    stats['trades'].append({'coin':d['coin'],'action':d['action'],'price':d['price'],'score':d['score'],'time':datetime.now().isoformat()})

stats['evaluations'] = [{'coin':e['coin'],'action':e['action'],'score':e['combined_score'],'recommend':e['recommend']} for e in evaluations]

with open(stats_file, 'w') as f:
    json.dump(stats, f, indent=2)

print(f"  历史交易: {len(stats['trades'])}笔")
print(f"  发现机会: {len(opportunities)}个")

print("\n✅ Hermes v5.9 完成")
PYEOF
