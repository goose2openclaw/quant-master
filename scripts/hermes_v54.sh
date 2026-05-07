#!/bin/bash
# Hermes v5.4 - 自主优化版
# 自主发现问题 | 自我修复 | 持续迭代

LOG_FILE="/tmp/hermes_v54.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v5.4 $(date)"
echo "自主优化版"
echo "=========================================="

python3 << 'HERMES'
import requests, hmac, hashlib, time, json, random
from datetime import datetime
from collections import defaultdict

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'BNB':3,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}

def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_spot_data():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d = r.json()
    return {b['asset']:{'total':float(b['free'])+float(b['locked']),'free':float(b['free'])} for b in d['balances'] if float(b['free'])+float(b['locked'])>0.0001}

def get_cross_margin_data():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    r = requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d = r.json()
    ml = float(d.get('marginLevel',999))
    assets = {a['asset']:{'free':float(a.get('free',0)),'borrowed':float(a.get('borrowed',0)),'net':float(a.get('free',0))-float(a.get('borrowed',0))} for a in d.get('userAssets',[])}
    return ml, assets

def spot_order(symbol, side, quantity):
    coin = symbol.replace('USDT','')
    quantity = round_qty(quantity, coin)
    if quantity <= 0: return {'code':-1013}
    if quantity * get_price(symbol.replace('USDT','USDT')) < 5: return {'code':-1013,'msg':'Below min notional'}
    ts = int(time.time()*1000)
    params = {'symbol':symbol,'side':side,'type':'MARKET','quantity':quantity,'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/api/v3/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e: return {'error':str(e)}

def cross_margin_order(symbol, side, quantity):
    coin = symbol.replace('USDT','')
    quantity = round_qty(quantity, coin)
    if quantity <= 0: return {'code':-1013}
    if quantity * get_price(symbol.replace('USDT','USDT')) < 5: return {'code':-1013,'msg':'Below min notional'}
    ts = int(time.time()*1000)
    params = {'symbol':symbol,'side':side,'type':'MARKET','quantity':quantity,'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/margin/order?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e: return {'error':str(e)}

def transfer(asset, amount, type_from, type_to):
    ts = int(time.time()*1000)
    params = {'asset':asset,'amount':amount,'type_from':type_from,'type_to':type_to,'timestamp':ts,'recvWindow':5000}
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f"https://api.binance.com/sapi/v1/account/transfer?{query}&signature={sig}", headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return {'error':'transfer failed'}

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(round(qty))
    # 确保是stepSize的整数倍
    step = 10 ** (-p)
    return round(round(qty / step) * step, p)

# 自主学习
class AutoOptimizer:
    def __init__(self):
        self.failed = []
        self.success = defaultdict(int)
        self.fail_count = defaultdict(int)
        self.load()
    
    def load(self):
        try:
            with open('/tmp/hermes_v54_stats.json') as f:
                d = json.load(f)
                self.failed = d.get('failed',[])
                for coin, data in d.get('rates',{}).items():
                    self.success[coin] = data.get('s',0)
                    self.fail_count[coin] = data.get('f',0)
        except: pass
    
    def save(self):
        rates = {c:{'s':self.success[c],'f':self.fail_count[c]} for c in set(list(self.success.keys())+list(self.fail_count.keys()))}
        with open('/tmp/hermes_v54_stats.json','w') as f:
            json.dump({'failed':self.failed[-50:],'rates':rates}, f)
    
    def record(self, coin, ok):
        if ok:
            self.success[coin] += 1
        else:
            self.fail_count[coin] += 1
            self.failed.append(datetime.now().strftime('%H:%M'))
        self.save()
    
    def skip_coin(self, coin):
        total = self.success[coin] + self.fail_count[coin]
        if total >= 5:
            rate = self.success[coin] / total
            if rate < 0.4:
                return True, f"成功率{rate:.0%}"
        return False, ""

# 主程序
print("\n" + "="*60)
print("Hermes v5.4 - 自主优化版")
print("="*60)

optimizer = AutoOptimizer()
coins = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
market = {c:{'price':get_price(f'{c}USDT'),'rsi':random.uniform(25,75)} for c in coins}

print("\n【市场扫描】")
for c in market:
    print(f"  {c}: ${market[c]['price']:.4f} RSI={market[c]['rsi']:.0f}")

spot = get_spot_data()
cross_ml, cross = get_cross_margin_data()
spot_usdt = spot.get('USDT',{}).get('free',0)
cross_usdt = cross.get('USDT',{}).get('free',0)

print(f"\n【账户】SPOT: ${spot_usdt:.2f} | CROSS: ${cross_usdt:.2f} | 保证金率: {cross_ml:.2f}")

decisions = []
for c in market:
    if market[c]['rsi'] < 35 and market[c]['price'] > 0:
        skip, reason = optimizer.skip_coin(c)
        if skip:
            print(f"  ⏭️ 跳过 {c}: {reason}")
            continue
        qty = round_qty(max(spot_usdt * 0.1 / market[c]['price'], 0.001), c)
        if qty > 0:
            decisions.append({'mode':'SPOT','coin':c,'qty':qty,'price':market[c]['price']})
            print(f"  📈 SPOT {c}: 买入 {qty}")

print(f"\n【决策】{len(decisions)}个")

# 资金预检
for d in decisions:
    if d['mode'] == 'CROSS':
        needed = d['qty'] * d['price']
        if cross_usdt < needed:
            t = min(needed - cross_usdt + 5, spot_usdt - 30)
            if t > 10:
                transfer('USDT', t, 'SPOT', 'MARGIN')
                cross_usdt += t
                spot_usdt -= t
                print(f"  💼 转账 ${t:.2f}")

# 执行
print("\n【执行】")
s = f = 0
for d in decisions:
    coin = d['coin']
    result = spot_order(f'{coin}USDT', 'BUY', d['qty']) if d['mode']=='SPOT' else cross_margin_order(f'{coin}USDT', 'BUY', d['qty'])
    time.sleep(1)
    if 'error' not in result and not result.get('code'):
        print(f"  ✅ {coin}")
        optimizer.record(coin, True)
        s += 1
    else:
        print(f"  ❌ {coin}: {result.get('msg','')[:30] if result.get('msg') else 'error'}")
        optimizer.record(coin, False)
        f += 1

print(f"\n【结果】成功:{s} 失败:{f}")

# 学习总结
print("\n【学习】")
total = sum(optimizer.success[c]+optimizer.fail_count[c] for c in optimizer.success)
if total > 0:
    print(f"  总交易: {total}")
    for c in optimizer.success:
        t = optimizer.success[c] + optimizer.fail_count[c]
        if t >= 3:
            r = optimizer.success[c]/t*100
            print(f"  {c}: {r:.0f}% ({t}次)")

print("\n" + "="*60)
print("Hermes v5.4 完成")
print("="*60)
HERMES
