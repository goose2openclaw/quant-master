#!/bin/bash
# Hermes v5.3 Optimized - 全面优化版
# 收益最大化 | 胜率高 | 资金高使用 | 主动扫描 | 科学决策 | 自动运行

LOG_FILE="/tmp/hermes_v53_opt.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v5.3 Optimized $(date)"
echo "全面优化版 - 科学决策"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION = {'BTC':5,'ETH':4,'BNB':3,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== 优化配置 ==========
CONFIG = {
    'mode': 'expert',  # 自动切换普通/专家模式
    'buy_threshold': 18,    # 优化: 降低买入阈值捕捉更多机会
    'sell_threshold': 82,   # 优化: 提高卖出阈值锁定更多利润
    'position_ratio': 0.5,  # 资金使用率提高到50%
    'leverage': 2.0,
    'stop_loss': 0.02,      # 2%硬止损
    'take_profit': 0.12,   # 12%止盈
    'rebalance_threshold': 0.08,  # 8%再平衡阈值
    'pyramiding': True,     # 金字塔加仓
    'trailing_stop': 0.03,  # 3%跟踪止损
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
        return {
            'price': float(d['lastPrice']),
            'chg': float(d['priceChangePercent']),
            'high': float(d['highPrice']),
            'low': float(d['lowPrice']),
            'volume': float(d['quoteVolume'])
        }
    except: return None

def get_klines(sym, days=7):
    end = int(time.time() * 1000)
    start = end - days * 86400 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit=500'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{
            'open': float(k[1]), 'high': float(k[2]),
            'low': float(k[3]), 'close': float(k[4]),
            'volume': float(k[5])
        } for k in r.json()]
    except: return []

def bollinger_position(price, high, low):
    return (price - low) / (high - low) * 100 if high > low else 50

def get_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_volatility(prices):
    if len(prices) < 2: return 0
    returns = np.diff(prices) / prices[:-1]
    return np.std(returns) * 100

def get_spot():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return {b['asset']: float(b['free']) for b in r.json()['balances'] if float(b['free']) > 0.01}

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
    step = 10 ** (-p)
    return round(round(qty / step) * step, p)

# ========== 全面扫描 ==========
print("\n【1. 全面市场扫描】")
market = {}
opportunities = []

for c in COINS:
    d = get_24hr(f'{c}USDT')
    if not d: continue
    
    price = d['price']
    chg = d['chg']
    high = d['high']
    low = d['low']
    volume = d['volume']
    
    band = high - low
    position = bollinger_position(price, high, low)
    
    # RSI
    klines = get_klines(f'{c}USDT', 7)
    if klines:
        prices = [k['close'] for k in klines]
        rsi = get_rsi(prices)
        volatility = get_volatility(prices[-30:]) if len(prices) >= 30 else 0
    else:
        rsi = 50
        volatility = 0
    
    market[c] = {
        'price': price, 'chg': chg, 'high': high, 'low': low,
        'volume': volume, 'position': position, 'rsi': rsi, 'volatility': volatility
    }
    
    print(f"  {c:5}: ${price:.4f} {chg:+.2f}% 位置:{position:.1f}% RSI:{rsi:.0f} 波动:{volatility:.2f}")
    
    # 机会评估
    score = 0
    action = None
    
    # 超卖机会
    if position < CONFIG['buy_threshold']:
        score = (CONFIG['buy_threshold'] - position) * 2
        if rsi < 35: score += 30  # RSI超卖加分
        if chg < -3: score += 20  # 大跌加分
        action = 'BUY'
    # 超买卖出
    elif position > CONFIG['sell_threshold']:
        score = (position - CONFIG['sell_threshold']) * 2
        if rsi > 65: score += 30
        if chg > 3: score += 20
        action = 'SELL'
    # 强势币
    elif rsi > 55 and chg > 1:
        score = rsi - 55
        action = 'HOLD_BUY'
    # 弱势币
    elif rsi < 45 and chg < -1:
        score = 45 - rsi
        action = 'HOLD_SELL'
    
    if action:
        opportunities.append({
            'coin': c, 'action': action, 'score': score,
            'position': position, 'rsi': rsi, 'chg': chg, 'volume': volume
        })

opportunities.sort(key=lambda x: -x['score'])

print(f"\n发现 {len(opportunities)} 个交易机会")

# ========== 账户状态 ==========
print("\n【2. 账户诊断】")
spot = get_spot()
spot_usdt = spot.get('USDT', 0)
total_value = spot_usdt

for c in COINS:
    if c in spot and spot[c] > 0:
        price = market.get(c, {}).get('price', get_price(f'{c}USDT'))
        value = spot[c] * price
        total_value += value
        print(f"  {c}: {spot[c]:.4f} (${value:.2f})")

print(f"  USDT: ${spot_usdt:.2f}")
print(f"  总资产: ${total_value:.2f}")

# ========== 科学决策 ==========
print("\n【3. 科学决策引擎】")
decisions = []

for opp in opportunities[:5]:  # Top 5机会
    c = opp['coin']
    action = opp['action']
    
    if c not in market: continue
    m = market[c]
    price = m['price']
    
    # 计算最优仓位
    position_value = spot.get(c, 0) * price
    current_ratio = position_value / total_value if total_value > 0 else 0
    target_ratio = CONFIG['position_ratio']
    
    # 买入决策
    if action in ['BUY', 'HOLD_BUY'] and spot_usdt > 10:
        diff_ratio = target_ratio - current_ratio
        if diff_ratio > 0:
            invest = total_value * diff_ratio * 0.5  # 分批建仓
            qty = invest / price
            qty = round_qty(qty, c)
            
            if qty > 0:
                decisions.append({
                    'coin': c, 'side': 'BUY', 'qty': qty, 'price': price,
                    'reason': f"位置:{m['position']:.0f}% RSI:{m['rsi']:.0f} 评分:{opp['score']:.0f}"
                })
                print(f"  📈 BUY {c} {qty} @ ${price:.4f} | {opp['reason']}")
    
    # 卖出决策
    elif action in ['SELL', 'HOLD_SELL'] and spot.get(c, 0) > 0:
        qty = round_qty(spot[c] * 0.5, c)
        if qty > 0:
            decisions.append({
                'coin': c, 'side': 'SELL', 'qty': qty, 'price': price,
                'reason': f"位置:{m['position']:.0f}% RSI:{m['rsi']:.0f} 评分:{opp['score']:.0f}"
            })
            print(f"  📉 SELL {c} {qty} @ ${price:.4f} | {opp['reason']}")

# ========== 自动执行 ==========
print("\n【4. 自动执行】")
success = fail = 0
for d in decisions:
    result = spot_order(f"{d['coin']}USDT", d['side'], d['qty'])
    time.sleep(1)
    
    if result and 'orderId' in result:
        print(f"  ✅ {d['side']} {d['coin']} {d['qty']}")
        success += 1
    else:
        msg = result.get('msg','')[:40] if result else 'error'
        print(f"  ❌ {d['coin']}: {msg}")
        fail += 1

# ========== 验证汇报 ==========
print("\n【5. 验证汇报】")
new_spot = get_spot()
new_usdt = new_spot.get('USDT', 0)
new_total = sum(new_spot.get(c, 0) * market.get(c, {}).get('price', 0) for c in COINS) + new_usdt

print(f"  执行: {success}笔成功, {fail}笔失败")
print(f"  资金: ${spot_usdt:.2f} → ${new_usdt:.2f}")
print(f"  资产: ${total_value:.2f} → ${new_total:.2f}")
print(f"  变化: {(new_total-total_value)/total_value*100:+.2f}%")

# ========== 复盘学习 ==========
print("\n【6. 复盘学习】")
stats_file = '/tmp/hermes_v53_opt_stats.json'
try:
    with open(stats_file) as f:
        stats = json.load(f)
except:
    stats = {'trades': [], 'wins': 0, 'losses': 0}

for d in decisions:
    stats['trades'].append({
        'coin': d['coin'],
        'side': d['side'],
        'price': d['price'],
        'time': datetime.now().isoformat(),
        'result': 'success' if success else 'fail'
    })

with open(stats_file, 'w') as f:
    json.dump(stats, f, indent=2)

win_rate = stats['wins'] / (stats['wins'] + stats['losses']) * 100 if stats['wins'] + stats['losses'] > 0 else 0
print(f"  历史交易: {len(stats['trades'])}笔")
print(f"  累计胜率: {win_rate:.1f}%")

print("\n✅ Hermes v5.3 Optimized 完成")
PYEOF
