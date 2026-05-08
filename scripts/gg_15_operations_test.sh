#!/bin/bash
# 15种操作全面测试、优化、迭代
LOG_FILE="/tmp/gg_15_operations.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "15种操作全面测试 $(date)"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== 工具函数 ==========
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

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def bollinger_pos(price, high, low):
    return (price-low)/(high-low)*100 if high>low else 50

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    step = 10**(-p)
    return round(round(qty/step)*step, p)

# ========== 账户获取 ==========
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

def get_isolated(coin):
    ts = int(time.time()*1000)
    params = f'asset={coin}&timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.get(f'https://api.binance.com/sapi/v1/margin/isolated/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        pairs = r.json().get('assets', [])
        for p in pairs:
            if p['asset'] == coin:
                return {'free': float(p['free']), 'borrowed': float(p['borrowed']), 'interest': float(p['interest']), 'net': float(p['netAsset'])}
        return None
    except: return None

# ========== SPOT操作 ==========
def spot_buy(coin, qty):
    qty = round_qty(qty, coin)
    if qty <= 0: return None
    ts = int(time.time()*1000)
    params = {'symbol':f'{coin}USDT','side':'BUY','type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/api/v3/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def spot_sell(coin, qty):
    qty = round_qty(qty, coin)
    if qty <= 0: return None
    ts = int(time.time()*1000)
    params = {'symbol':f'{coin}USDT','side':'SELL','type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/api/v3/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

# ========== CROSS操作 ==========
def cross_borrow(coin, qty):
    ts = int(time.time()*1000)
    params = {'asset':coin,'amount':str(qty),'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/borrow?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def cross_repay(coin, qty):
    ts = int(time.time()*1000)
    params = {'asset':coin,'amount':str(qty),'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/repay?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def cross_buy(coin, qty):
    ts = int(time.time()*1000)
    params = {'symbol':f'{coin}USDT','side':'BUY','type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000,'isIsolated':'FALSE'}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def cross_sell(coin, qty):
    ts = int(time.time()*1000)
    params = {'symbol':f'{coin}USDT','side':'SELL','type':'MARKET','quantity':qty,'timestamp':ts,'recvWindow':5000,'isIsolated':'FALSE'}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

# ========== 15种操作测试 ==========
print("\n" + "="*70)
print("【15种操作全面测试】")
print("="*70)

# 获取当前状态
spot = get_spot()
cross_bal, cross_level = get_cross()

print(f"\n【初始状态】")
print(f"  SPOT USDT: {spot.get('USDT', 0):.2f}")
print(f"  CROSS USDT: {cross_bal.get('USDT', 0):.2f}, Level: {cross_level:.2f}")

# 获取市场数据
prices = {}
for c in COINS:
    d = get_24hr(f'{c}USDT')
    if d: prices[c] = d

# 分析信号
def analyze_signal(coin):
    klines = get_klines(f'{coin}USDT', '1h', 100)
    if not klines: return None
    d = get_24hr(f'{coin}USDT')
    if not d: return None
    
    prices_list = [k['close'] for k in klines]
    rsi = get_rsi(prices_list)
    bb_pos = bollinger_pos(d['price'], d['high'], d['low'])
    chg = d['chg']
    
    return {'rsi': rsi, 'bb_pos': bb_pos, 'chg': chg, 'price': d['price']}

# 测试结果记录
test_results = []

print("\n【开始15种操作测试】")
print("-"*70)

# 操作1-5: SPOT操作
print("\n【SPOT操作 (1-5)】")
spot_ops = []

# SPOT操作1: 低吸买入
print("\n[操作1] SPOT低吸 - 买入DOGE")
sig = analyze_signal('DOGE')
if sig and spot.get('USDT', 0) > 10:
    invest = min(spot.get('USDT', 0) * 0.1, 10)  # 用10%或$10
    qty = invest / sig['price']
    result = spot_buy('DOGE', qty)
    if result and 'orderId' in result:
        print(f"  ✅ 买入DOGE: {qty:.0f} @ ${sig['price']:.4f}")
        spot_ops.append({'op':1,'type':'SPOT_BUY','coin':'DOGE','qty':qty,'price':sig['price'],'signal':f"BB:{sig['bb_pos']:.0f}% RSI:{sig['rsi']:.0f}"})
    else:
        print(f"  ❌ 失败: {result.get('msg','')[:50] if result else 'err'}")
        spot_ops.append({'op':1,'type':'SPOT_BUY','coin':'DOGE','result':'FAIL'})

# SPOT操作2: 高抛卖出
print("\n[操作2] SPOT高抛 - 卖出DOGE")
new_spot = get_spot()
doge_qty = new_spot.get('DOGE', 0)
if doge_qty > 100:
    sell_qty = doge_qty * 0.1
    result = spot_sell('DOGE', sell_qty)
    if result and 'orderId' in result:
        print(f"  ✅ 卖出DOGE: {sell_qty:.0f}")
        spot_ops.append({'op':2,'type':'SPOT_SELL','coin':'DOGE','qty':sell_qty})
    else:
        print(f"  ❌ 失败: {result.get('msg','')[:50] if result else 'err'}")
        spot_ops.append({'op':2,'type':'SPOT_SELL','coin':'DOGE','result':'FAIL'})
else:
    print(f"  ⏭️ 跳过: DOGE不足")

# SPOT操作3: 止损
print("\n[操作3] SPOT止损 - XRP")
new_spot = get_spot()
xrp_qty = new_spot.get('XRP', 0)
if xrp_qty > 50:
    sig = analyze_signal('XRP')
    if sig and sig['bb_pos'] > 85:
        sell_qty = xrp_qty * 0.3
        result = spot_sell('XRP', sell_qty)
        if result and 'orderId' in result:
            print(f"  ✅ 止损卖出XRP: {sell_qty:.2f}")
            spot_ops.append({'op':3,'type':'SPOT_STOP_LOSS','coin':'XRP','qty':sell_qty})
        else:
            print(f"  ❌ 失败")
    else:
        print(f"  ⏭️ 条件不满足: BB={sig['bb_pos']:.0f}%")
else:
    print(f"  ⏭️ 跳过: XRP不足")

# SPOT操作4: 追涨
print("\n[操作4] SPOT追涨 - SOL")
sig = analyze_signal('SOL')
if sig and sig['chg'] > 3 and sig['bb_pos'] > 70:
    if spot.get('USDT', 0) > 10:
        invest = min(spot.get('USDT', 0) * 0.1, 10)
        qty = invest / sig['price']
        result = spot_buy('SOL', qty)
        if result and 'orderId' in result:
            print(f"  ✅ 追涨买入SOL: {qty:.3f}")
            spot_ops.append({'op':4,'type':'SPOT_CHASE','coin':'SOL','qty':qty})
        else:
            print(f"  ❌ 失败")
else:
    print(f"  ⏭️ 条件不满足: 涨幅{sig['chg']:.1f}%, BB={sig['bb_pos']:.0f}%")

# SPOT操作5: 反转卖出
print("\n[操作5] SPOT反转 - ADA")
sig = analyze_signal('ADA')
new_spot = get_spot()
ada_qty = new_spot.get('ADA', 0)
if sig and ada_qty > 50 and sig['bb_pos'] > 80:
    sell_qty = ada_qty * 0.5
    result = spot_sell('ADA', sell_qty)
    if result and 'orderId' in result:
        print(f"  ✅ 反转卖出ADA: {sell_qty:.2f}")
        spot_ops.append({'op':5,'type':'SPOT_REVERSE','coin':'ADA','qty':sell_qty})
    else:
        print(f"  ❌ 失败")
else:
    print(f"  ⏭️ 条件不满足: BB={sig['bb_pos']:.0f}%")

# CROSS操作6-10
print("\n【CROSS操作 (6-10)】")

# CROSS操作6: CROSS做多
print("\n[操作6] CROSS做多 - 借入USDT买入XRP")
if cross_bal.get('USDT', 0) < 10 and cross_bal.get('USDT', 0) < 100:
    borrow_amount = min(50, cross_bal.get('USDT', 0) * 0.5)
    result = cross_borrow('USDT', borrow_amount)
    if result and result.get('tranId'):
        print(f"  ✅ 借入USDT: {borrow_amount}")
        time.sleep(1)
        sig = analyze_signal('XRP')
        if sig and sig['bb_pos'] < 30:
            qty = borrow_amount / sig['price']
            order = cross_buy('XRP', qty)
            if order and 'orderId' in order:
                print(f"  ✅ CROSS做多XRP: {qty:.2f}")
                spot_ops.append({'op':6,'type':'CROSS_LONG','coin':'XRP','qty':qty,'borrow':borrow_amount})
            else:
                print(f"  ❌ 买入失败")
        else:
            print(f"  ⏭️ 信号不满足")
    else:
        print(f"  ❌ 借款失败")

# CROSS操作7: CROSS做空
print("\n[操作7] CROSS做空 - 借入XRP卖出")
sig = analyze_signal('XRP')
if sig and sig['bb_pos'] > 75:
    borrow_xrp = min(100, sig['price'] * 100)
    result = cross_borrow('XRP', borrow_xrp)
    if result and result.get('tranId'):
        print(f"  ✅ 借入XRP: {borrow_xrp}")
        time.sleep(1)
        order = cross_sell('XRP', borrow_xrp)
        if order and 'orderId' in order:
            print(f"  ✅ CROSS做空XRP: {borrow_xrp}")
            spot_ops.append({'op':7,'type':'CROSS_SHORT','coin':'XRP','qty':borrow_xrp})
        else:
            print(f"  ❌ 卖出失败")
else:
    print(f"  ⏭️ 信号不满足: BB={sig['bb_pos']:.0f}%")

# CROSS操作8: CROSS买入
print("\n[操作8] CROSS买入 - BTC")
if cross_bal.get('USDT', 0) > 10:
    sig = analyze_signal('BTC')
    if sig and sig['bb_pos'] < 25:
        invest = min(cross_bal.get('USDT', 0) * 0.1, 20)
        qty = invest / sig['price']
        order = cross_buy('BTC', qty)
        if order and 'orderId' in order:
            print(f"  ✅ CROSS买入BTC: {qty:.5f}")
            spot_ops.append({'op':8,'type':'CROSS_BUY','coin':'BTC','qty':qty})
        else:
            print(f"  ❌ 失败")
    else:
        print(f"  ⏭️ 信号不满足")

# CROSS操作9: CROSS卖出
print("\n[操作9] CROSS卖出 - ETH")
sig = analyze_signal('ETH')
if sig and sig['bb_pos'] > 75:
    eth_qty = cross_bal.get('ETH', 0)
    if eth_qty > 0.01:
        order = cross_sell('ETH', eth_qty * 0.5)
        if order and 'orderId' in order:
            print(f"  ✅ CROSS卖出ETH: {eth_qty * 0.5:.4f}")
            spot_ops.append({'op':9,'type':'CROSS_SELL','coin':'ETH','qty':eth_qty*0.5})
        else:
            print(f"  ❌ 失败")
    else:
        print(f"  ⏭️ 无ETH持仓")
else:
    print(f"  ⏭️ 信号不满足")

# CROSS操作10: CROSS还款
print("\n[操作10] CROSS还款 - 归还USDT")
new_cross, new_level = get_cross()
usdt_borrowed = 10  # 估算
if new_cross.get('USDT', 0) > usdt_borrowed + 5:
    repay_qty = min(usdt_borrowed, new_cross.get('USDT', 0) * 0.5)
    result = cross_repay('USDT', repay_qty)
    if result and result.get('tranId'):
        print(f"  ✅ 归还USDT: {repay_qty}")
        spot_ops.append({'op':10,'type':'CROSS_REPAY','coin':'USDT','qty':repay_qty})
    else:
        print(f"  ❌ 失败")

# ISOLATED操作11-15
print("\n【ISOLATED操作 (11-15)】")

# ISOLATED操作11: ISOLATED做多
print("\n[操作11] ISOLATED做多 - DOGE")
iso_doge = get_isolated('DOGE')
if iso_doge:
    sig = analyze_signal('DOGE')
    if sig and sig['bb_pos'] < 25:
        print(f"  ⏭️ 已在ISOLATED持仓")
    else:
        print(f"  ⏭️ 信号不满足")
else:
    print(f"  ⏭️ ISOLATED DOGE不存在")

# ISOLATED操作12: ISOLATED做空
print("\n[操作12] ISOLATED做空 - XRP")
print(f"  ⏭️ ISOLATED做空待实现")

# ISOLATED操作13: ISOLATED买入
print("\n[操作13] ISOLATED买入 - LINK")
print(f"  ⏭️ ISOLATED LINK待实现")

# ISOLATED操作14: ISOLATED卖出
print("\n[操作14] ISOLATED卖出 - SOL")
print(f"  ⏭️ ISOLATED SOL待实现")

# ISOLATED操作15: ISOLATED平仓
print("\n[操作15] ISOLATED平仓")
print(f"  ⏭️ ISOLATED平仓待实现")

# ========== 结果汇总 ==========
print("\n" + "="*70)
print("【15种操作测试结果】")
print("="*70)

success = sum(1 for op in spot_ops if 'result' not in op)
fail = sum(1 for op in spot_ops if op.get('result') == 'FAIL')
skip = sum(1 for op in spot_ops if 'result' in ('SKIP', 'N/A'))

print(f"\n完成: {len(spot_ops)}/15 操作")
print(f"  ✅ 成功: {success}")
print(f"  ❌ 失败: {fail}")
print(f"  ⏭️ 跳过: {skip}")

print("\n【操作详情】")
for i, op in enumerate(spot_ops, 1):
    status = "✅" if 'result' not in op else "❌" if op.get('result') == 'FAIL' else "⏭️"
    if 'type' in op:
        print(f"  {i:2}. {status} {op.get('type','N/A')} - {op.get('coin','N/A')} {op.get('qty','')} {op.get('signal','')}")

# 验证资产变化
print("\n【资产验证】")
new_spot = get_spot()
new_cross, new_level = get_cross()
spot_total = sum(new_spot.get(c, 0) * prices.get(c, {}).get('price', 0) for c in COINS) + new_spot.get('USDT', 0)
cross_total = sum(new_cross.get(c, 0) * prices.get(c, {}).get('price', 0) for c in COINS) + new_cross.get('USDT', 0)

print(f"  SPOT: ${spot_total:.2f}")
print(f"  CROSS: ${cross_total:.2f}")
print(f"  总计: ${spot_total + cross_total:.2f}")

# 保存结果
with open('/tmp/15_operations_result.json', 'w') as f:
    json.dump({'operations': spot_ops, 'spot_total': spot_total, 'cross_total': cross_total, 'timestamp': datetime.now().isoformat()}, f, indent=2)

print("\n✅ 15种操作测试完成!")
PYEOF
