#!/bin/bash
# Hermes v5.10 - 全功能增强版
# 正T/反T | 高抛低吸 | 做多做空 | 币种转换 | 自主决策
LOG_FILE="/tmp/hermes_v510.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "Hermes v5.10 $(date)"
echo "全功能增强版"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== 核心配置 ==========
CONFIG = {
    # 基础参数
    'min_balance': 10,          # 最小余额
    'position_ratio': 0.4,      # 仓位比例
    
    # 正T/反T
    'zt_threshold': -2.0,       # 正T: 跌幅>%买入
    'ft_threshold': 3.0,        # 反T: 涨幅>%卖出
    
    # 高抛低吸
    'buy_threshold': 25,         # 布林位置<25%买入
    'sell_threshold': 75,       # 布林位置>75%卖出
    
    # 做多做空
    'long_threshold': 30,       # RSI<30做多
    'short_threshold': 70,      # RSI>70做空
    
    # 止盈止损
    'take_profit': 0.08,       # 8%止盈
    'stop_loss': 0.03,         # 3%止损
    
    # 币种转换
    'convert_enabled': True,
    'convert_threshold': 0.3,   # 分数差距>30%则转换
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

def get_klines(sym, interval='1h', limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'open':float(k[1]),'high':float(k[2]),'low':float(k[3]),'close':float(k[4]),'volume':float(k[5])} for k in r.json()]
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

# ========== 评估单个币种 ==========
def evaluate_coin(c, spot_balance, prices, total_value):
    """全面评估单个币种"""
    d = get_24hr(f'{c}USDT')
    klines = get_klines(f'{c}USDT', '1h', 100)
    if not d or not klines: return None
    
    price = d['price']
    chg = d['chg']
    high, low = d['high'], d['low']
    
    bb_pos = bollinger_pos(price, high, low)
    prices_list = [k['close'] for k in klines]
    rsi = get_rsi(prices_list)
    
    current_qty = spot_balance.get(c, 0)
    current_value = current_qty * price
    current_ratio = current_value / total_value if total_value > 0 else 0
    
    # 评分
    scores = {}
    actions = {}
    
    # 1. 正T (逢低买入)
    if chg < CONFIG['zt_threshold']:
        zt_score = abs(chg) * 10
        scores['ZT'] = zt_score
        actions['ZT'] = {'type': 'BUY', 'reason': f'正T 跌幅{chg:.1f}%'}
    
    # 2. 反T (逢高卖出)
    if chg > CONFIG['ft_threshold'] and current_qty > 0:
        ft_score = chg * 10
        scores['FT'] = ft_score
        actions['FT'] = {'type': 'SELL', 'reason': f'反T 涨幅{chg:.1f}%'}
    
    # 3. 高抛低吸 (布林带)
    if bb_pos < CONFIG['buy_threshold'] and current_qty > 0:
        # 买入信号
        bb_score = (CONFIG['buy_threshold'] - bb_pos) * 3
        scores['BB_BUY'] = bb_score
        actions['BB_BUY'] = {'type': 'BUY', 'reason': f'布林买入 位置{bb_pos:.0f}%'}
    elif bb_pos > CONFIG['sell_threshold'] and current_qty > 0:
        # 卖出信号
        bb_score = (bb_pos - CONFIG['sell_threshold']) * 3
        scores['BB_SELL'] = bb_score
        actions['BB_SELL'] = {'type': 'SELL', 'reason': f'布林卖出 位置{bb_pos:.0f}%'}
    
    # 4. 做多做空 (RSI)
    if rsi < CONFIG['long_threshold'] and current_qty > 0:
        long_score = (CONFIG['long_threshold'] - rsi) * 5
        scores['LONG'] = long_score
        actions['LONG'] = {'type': 'BUY', 'reason': f'RSI做多 RSI={rsi:.0f}'}
    elif rsi > CONFIG['short_threshold'] and current_qty > 0:
        short_score = (rsi - CONFIG['short_threshold']) * 5
        scores['SHORT'] = short_score
        actions['SHORT'] = {'type': 'SELL', 'reason': f'RSI做空 RSI={rsi:.0f}'}
    
    # 选择最佳动作
    best_action = None
    best_score = 0
    if scores:
        best_name = max(scores, key=scores.get)
        best_score = scores[best_name]
        best_action = actions[best_name]
        best_action['name'] = best_name
        best_action['score'] = best_score
    
    return {
        'coin': c,
        'price': price,
        'chg': chg,
        'bb_pos': bb_pos,
        'rsi': rsi,
        'qty': current_qty,
        'value': current_value,
        'ratio': current_ratio,
        'action': best_action,
        'score': best_score
    }

# ========== 主程序 ==========
print("\n【1. 全域扫描 & 评估】")
spot = get_spot()
prices_dict = {}
evaluations = []

for c in COINS:
    d = get_24hr(f'{c}USDT')
    if d: prices_dict[c] = d['price']

total_value = sum(spot.get(c, 0) * prices_dict.get(c, 0) for c in COINS) + spot.get('USDT', 0)

for c in COINS:
    eval_result = evaluate_coin(c, spot, prices_dict, total_value)
    if eval_result:
        evaluations.append(eval_result)
        
        action_str = eval_result['action']['name'] if eval_result['action'] else 'HOLD'
        emoji = '📈' if action_str in ['ZT','BB_BUY','LONG'] else '📉' if action_str in ['FT','BB_SELL','SHORT'] else '➡️'
        
        print(f"  {c:5}: ${eval_result['price']:.4f} {eval_result['chg']:+.2f}% BB:{eval_result['bb_pos']:.0f}% RSI:{eval_result['rsi']:.0f} {emoji} {action_str}({eval_result['score']:.0f})")
    time.sleep(0.1)

evaluations.sort(key=lambda x: -x['score'])

# ========== 币种转换决策 ==========
print("\n【2. 币种转换决策】")
if CONFIG['convert_enabled'] and len(evaluations) >= 2:
    # 最低分持仓
    held_evals = [e for e in evaluations if e['qty'] > 0]
    if held_evals:
        low_eval = min(held_evals, key=lambda x: x['score'])
        
        # 最高分机会(无持仓或轻仓)
        high_eval = evaluations[0]
        
        if low_eval['score'] < high_eval['score'] * CONFIG['convert_threshold']:
            print(f"  🔄 建议转换: {low_eval['coin']}({low_eval['score']:.0f}分) -> {high_eval['coin']}({high_eval['score']:.0f}分)")
            print(f"     {low_eval['coin']}持仓: {low_eval['qty']:.4f} (${low_eval['value']:.2f})")

# ========== 执行决策 ==========
print("\n【3. 执行决策】")
decisions = []

for eval_result in evaluations[:4]:
    action = eval_result['action']
    if not action: continue
    
    c = eval_result['coin']
    price = eval_result['price']
    qty = eval_result['qty']
    side = action['type']
    
    if side == 'BUY':
        usdt = spot.get('USDT', 0)
        if usdt > CONFIG['min_balance']:
            invest = total_value * CONFIG['position_ratio']
            buy_qty = round_qty(invest / price, c)
            if buy_qty > 0:
                decisions.append({'coin':c,'side':'BUY','qty':buy_qty,'action':action['name'],'reason':action['reason']})
                print(f"  📈 {action['name']} {c}: {buy_qty} @ ${price:.4f} | {action['reason']}")
    
    elif side == 'SELL' and qty > 0:
        sell_qty = round_qty(qty * 0.5, c)
        if sell_qty > 0:
            decisions.append({'coin':c,'side':'SELL','qty':sell_qty,'action':action['name'],'reason':action['reason']})
            print(f"  📉 {action['name']} {c}: {sell_qty} @ ${price:.4f} | {action['reason']}")

# ========== 执行交易 ==========
print("\n【4. 执行交易】")
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

# ========== 验证 ==========
print("\n【5. 验证汇报】")
new_spot = get_spot()
new_total = sum(new_spot.get(c, 0) * prices_dict.get(c, 0) for c in COINS) + new_spot.get('USDT', 0)

print(f"  执行: {success}成功, {fail}失败")
print(f"  资产: ${total_value:.2f} -> ${new_total:.2f} ({(new_total-total_value)/total_value*100:+.2f}%)")

print("\n✅ Hermes v5.10 完成")
PYEOF
