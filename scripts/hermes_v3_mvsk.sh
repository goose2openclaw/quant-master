#!/bin/bash
# Hermes v3.mvsk - MVSK组合优化版
# 集成yand-mvsk二阶矩-方差-偏度-峰度优化器
# 收益最大化 + 风险控制

LOG_FILE="/tmp/hermes_v3_mvsk.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v3.mvsk $(date)"
echo "MVSK组合优化版"
echo "=========================================="

python3 << 'INNER'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

# yand-mvsk导入
from yand_mvsk import yand_mvsk_solve, crra_coefficients

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'BNB':3,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}

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

def get_spot():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return {b['asset']: float(b['free']) for b in r.json()['balances'] if float(b['free']) > 0}

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
    if p == 0: return int(round(qty))
    step = 10 ** (-p)
    return round(round(qty / step) * step, p)

# ========== MVSK优化 ==========
def mvsk_optimize(returns_matrix, gamma=2.0):
    """使用MVSK优化器计算最优权重"""
    c = crra_coefficients(gamma)  # [c1,c2,c3,c4]
    result = yand_mvsk_solve(returns_matrix, c, max_iter=200, verbose=False)
    return result.x  # 最优权重

# ========== 主程序 ==========
print("\n" + "="*60)
print("Hermes v3.mvsk - MVSK组合优化")
print("="*60)

# 持仓币种
coins = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# 获取历史数据计算收益率矩阵
print("\n【1. 获取历史数据】")
# 用24h价格模拟历史收益率
returns_matrix = []
for c in coins:
    d = get_24hr(f'{c}USDT')
    if d:
        # 用近期价格变动模拟收益率序列
        ret = np.random.normal(d['chg']/100, 0.02, 30)  # 30天模拟
        returns_matrix.append(ret)
    else:
        returns_matrix.append(np.zeros(30))

returns_matrix = np.array(returns_matrix).T  # (30, n_assets)

# MVSK优化
print("\n【2. MVSK组合优化】")
try:
    weights = mvsk_optimize(returns_matrix, gamma=2.0)
    print(f"  优化完成!")
    for i, c in enumerate(coins):
        if weights[i] > 0.01:
            print(f"  {c}: {weights[i]*100:.1f}%")
except Exception as e:
    print(f"  优化失败: {e}, 使用均匀权重")
    weights = np.ones(len(coins)) / len(coins)

# 市场扫描
print("\n【3. 市场扫描】")
market = {}
for c in coins:
    d = get_24hr(f'{c}USDT')
    if d:
        market[c] = d
        print(f"  {c}: ${d['price']:.4f} {d['chg']:+.2f}%")

spot = get_spot()
spot_usdt = spot.get('USDT', 0)
print(f"\n  SPOT USDT: ${spot_usdt:.2f}")

# 生成交易决策
print("\n【4. MVSK优化决策】")
decisions = []
for i, c in enumerate(coins):
    if c not in market: continue
    
    w = weights[i]
    price = market[c]['price']
    chg = market[c]['chg']
    
    # 布林带位置
    high = market[c]['high']
    low = market[c]['low']
    band = high - low
    position = (price - low) / band * 100 if band > 0 else 50
    
    # MVSK建议权重w,当前位置偏离则交易
    target_qty = spot.get(c, 0) + (w * spot_usdt / price - spot.get(c, 0)) * 0.5  # 渐进调整
    
    if target_qty > spot.get(c, 0) * 1.05:  # 需要买入
        qty = target_qty - spot.get(c, 0)
        qty = round_qty(qty, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'BUY','qty':qty,'price':price,'weight':w})
            print(f"  📈 BUY {c} {qty} (目标权重:{w*100:.1f}%)")
    elif target_qty < spot.get(c, 0) * 0.95:  # 需要卖出
        qty = spot.get(c, 0) - target_qty
        qty = round_qty(qty, c)
        if qty > 0:
            decisions.append({'coin':c,'side':'SELL','qty':qty,'price':price,'weight':w})
            print(f"  📉 SELL {c} {qty} (目标权重:{w*100:.1f}%)")

# 执行
print("\n【5. 执行交易】")
success = fail = 0
for d in decisions:
    result = spot_order(f"{d['coin']}USDT", d['side'], d['qty'])
    time.sleep(1)
    if result and 'orderId' in result:
        print(f"  ✅ {d['side']} {d['coin']} {d['qty']}")
        success += 1
    else:
        msg = result.get('msg','')[:30] if result else 'error'
        print(f"  ❌ {d['coin']}: {msg}")
        fail += 1

print(f"\n【结果】成功:{success} 失败:{fail}")
print("Hermes v3.mvsk 完成")
INNER
