#!/bin/bash
# Hermes v5.2 - SPOT+CROSS+ISOLATED全模式
# 日期: 2026-05-07
# 功能: 三账户全模式支持

LOG_FILE="/tmp/hermes_v52.log"
exec >> $LOG_FILE 2>&1

SCRIPT_DIR="$HOME/.openclaw/workspace/scripts"
LAST_CALL_FILE="/tmp/hermes_last_calls.json"

echo "=========================================="
echo "Hermes v5.2 $(date)"
echo "SPOT + CROSS + ISOLATED 全模式"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json, math, subprocess
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION={'BTC':6,'ETH':5,'BNB':5,'SOL':5,'XRP':0,'ADA':0,'DOGE':0,'LINK':2}
TRADE_HISTORY_FILE='/tmp/hermes_trade_history.json'
VERIFY_LOG='/tmp/hermes_v52_verification.log'

CONFIG={
    'rsi_short': 71, 'rsi_long': 32,
    'tp': 0.08, 'sl': 0.015,
    'position': 0.25, 'leverage': 5,
    'min_notional': 10,
    'spot_position': 0.30,
}

SCRIPT_DIR='/home/goose/.openclaw/workspace/scripts'
LAST_CALL_FILE='/tmp/hermes_last_calls.json'

def load_last_calls():
    try:
        with open(LAST_CALL_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_last_calls(calls):
    try:
        with open(LAST_CALL_FILE, 'w') as f: json.dump(calls, f)
    except: pass

def should_run(task, interval_sec):
    calls=load_last_calls()
    last=calls.get(task, 0)
    now=int(time.time())
    return (now - last) >= interval_sec

def mark_run(task):
    calls=load_last_calls()
    calls[task]=int(time.time())
    save_last_calls(calls)

def call_script(name, timeout=60):
    try:
        result=subprocess.run(['bash', f'{SCRIPT_DIR}/{name}'], capture_output=True, text=True, timeout=timeout)
        return result.returncode==0, result.stdout[-500:] if result.stdout else ''
    except Exception as e: return False, str(e)[:200]

def get_price(sym):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=60):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}', proxies=PROXIES, timeout=10)
        return [(float(d[2]),float(d[3]),float(d[4])) for d in r.json()]
    except: return None

def calc_rsi(closes, period=14):
    if len(closes)<2: return 50
    deltas=[closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains=[d if d>0 else 0 for d in deltas]
    losses=[-d if d<0 else 0 for d in deltas]
    avg_gain=sum(gains[-period:])/period if len(gains)>=period else sum(gains)/len(gains)
    avg_loss=sum(losses[-period:])/period if len(losses)>=period else sum(losses)/len(losses)
    rs=avg_gain/(avg_loss+0.0001)
    return 100-(100/(1+rs))

# ========== 三账户数据获取 ==========
def get_spot_data():
    ts=int(time.time()*1000)
    params=f'timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d=r.json()
    balances={}
    for b in d.get('balances',[]):
        free=float(b.get('free',0)); locked=float(b.get('locked',0)); total=free+locked
        if total>0.0001:
            balances[b['asset']]={'free':free,'locked':locked,'total':total}
    return balances

def get_cross_margin_data():
    """全仓保证金数据"""
    ts=int(time.time()*1000)
    params=f'timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d=r.json()
    ml=float(d.get('marginLevel',999))
    assets={}
    for a in d.get('userAssets',[]):
        free=float(a.get('free',0)); borrowed=float(a.get('borrowed',0)); net=free-borrowed
        assets[a['asset']]={'free':free,'borrowed':borrowed,'net':net}
    return ml, assets

def get_isolated_margin_data():
    """逐仓保证金数据"""
    ts=int(time.time()*1000)
    params=f'timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get(f'https://api.binance.com/sapi/v2/margin/isolated/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d=r.json()
    isolated={}
    for account in d.get('accounts',[]):
        symbol=account.get('symbol','')
        base=account.get('baseAsset',{})
        quote=account.get('quoteAsset',{})
        net_base=float(base.get('free',0))-float(base.get('borrowed',0))
        net_quote=float(quote.get('free',0))-float(quote.get('borrowed',0))
        if abs(net_base)>0.0001 or abs(net_quote)>0.0001:
            isolated[symbol]={
                'base':{'asset':base.get('asset',''),'net':net_base},
                'quote':{'asset':quote.get('asset',''),'net':net_quote}
            }
    return isolated

# ========== 三账户下单 ==========
def spot_order(symbol, side, quantity):
    ts=int(time.time()*1000)
    params={'symbol':symbol,'side':side,'type':'MARKET','quantity':quantity,'timestamp':ts,'recvWindow':5000}
    query_string='&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig=hmac.new(API_SECRET.encode(),query_string.encode(),hashlib.sha256).hexdigest()
    url=f"https://api.binance.com/api/v3/order?{query_string}&signature={sig}"
    try:
        r=requests.post(url, headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e: return {'error': str(e)}

def cross_margin_order(symbol, side, quantity):
    """全仓下单"""
    ts=int(time.time()*1000)
    params={'symbol':symbol,'side':side,'type':'MARKET','quantity':quantity,'timestamp':ts,'recvWindow':5000}
    query_string='&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig=hmac.new(API_SECRET.encode(),query_string.encode(),hashlib.sha256).hexdigest()
    url=f"https://api.binance.com/sapi/v1/margin/order?{query_string}&signature={sig}"
    try:
        r=requests.post(url, headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e: return {'error': str(e)}

def isolated_margin_order(symbol, side, quantity):
    """逐仓下单"""
    ts=int(time.time()*1000)
    params={'symbol':symbol,'side':side,'type':'MARKET','quantity':quantity,'isolatedSymbol':symbol,'timestamp':ts,'recvWindow':5000}
    query_string='&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig=hmac.new(API_SECRET.encode(),query_string.encode(),hashlib.sha256).hexdigest()
    url=f"https://api.binance.com/sapi/v1/margin/isolated/order?{query_string}&signature={sig}"
    try:
        r=requests.post(url, headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e: return {'error': str(e)}

def transfer(asset, amount, type_from, type_to):
    ts=int(time.time()*1000)
    params={'asset':asset,'amount':amount,'type_from':type_from,'type_to':type_to,'timestamp':ts,'recvWindow':5000}
    query_string='&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig=hmac.new(API_SECRET.encode(),query_string.encode(),hashlib.sha256).hexdigest()
    url=f"https://api.binance.com/sapi/v1/account/transfer?{query_string}&signature={sig}"
    try:
        r=requests.post(url, headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e: return {'error': str(e)}

def round_qty(qty, coin):
    p=PRECISION.get(coin, 6)
    if p==0: return int(round(qty))
    return round(qty, p)

def load_trade_history():
    try:
        with open(TRADE_HISTORY_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_trade_history(history):
    try:
        with open(TRADE_HISTORY_FILE, 'w') as f: json.dump(history, f)
    except: pass

def log_verify(msg):
    with open(VERIFY_LOG, 'a') as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} | {msg}\n")

# ========== 市场感知 ==========
def market_sensing():
    print("\n"+"="*60)
    print("🔍 积极觉察 - 市场扫描 v5.2")
    print("="*60)
    coins=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']
    market={}
    for coin in coins:
        sym=f"{coin}USDT"; price=get_price(sym)
        k1h=get_klines(sym,'1h',60)
        if k1h:
            rsi_1h=calc_rsi([k[2] for k in k1h])
            chg_1h=(k1h[-1][2]-k1h[0][2])/k1h[0][2]*100 if len(k1h)>=2 else 0
            score=3 if rsi_1h<35 else 1 if rsi_1h<40 else 0
            signal="📈" if score>=3 else "📊" if score>=1 else "⚪"
            market[coin]={'price':price,'rsi_1h':rsi_1h,'chg_1h':chg_1h,'score':score,'signal':signal}
            print(f"  {coin}: ${price:.4f} RSI={rsi_1h:.0f} {chg_1h:+.1f}% {signal}")
    return market

# ========== 三账户15种操作 ==========
MODE_ORDER_FUNCS = {
    'SPOT': spot_order,
    'CROSS': cross_margin_order,
    'ISOLATED': isolated_margin_order,
}

def execute_trade(mode, symbol, side, quantity):
    """统一交易接口"""
    order_func = MODE_ORDER_FUNCS.get(mode, spot_order)
    return order_func(symbol, side, quantity)

def op_build_all(market, spot_balances, cross_assets, isolated_assets, cross_ml, usdt_spot, usdt_cross):
    """1. 建仓 - 三账户"""
    decisions=[]
    for coin in market:
        # 检查是否已持仓
        in_cross = any(abs(cross_assets.get(a,{}).get('net',0))>0.0001 for a in [coin])
        in_isolated = any(coin in sym for sym in isolated_assets.keys())
        in_spot = spot_balances.get(coin,{}).get('total',0)>0.001
        
        if in_cross or in_isolated or in_spot: continue
        
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<32 and price>0:
            # SPOT建仓
            qty_spot=round_qty((usdt_spot*CONFIG['spot_position']/price)*0.99, coin)
            if price*qty_spot>=CONFIG['min_notional']:
                decisions.append({'mode':'SPOT','coin':coin,'action':'BUILD','side':'BUY','qty':qty_spot,'price':price})
                print(f"  🏗️ {coin}: SPOT建仓 BUY {qty_spot} (RSI={rsi:.0f})")
            
            # CROSS建仓
            if cross_ml>=4.0:
                qty_cross=round_qty((usdt_cross*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
                if price*qty_cross>=CONFIG['min_notional']:
                    decisions.append({'mode':'CROSS','coin':coin,'action':'BUILD','side':'BUY','qty':qty_cross,'price':price})
                    print(f"  🏗️ {coin}: CROSS建仓 BUY {qty_cross} (RSI={rsi:.0f})")
            
            # ISOLATED建仓(新币)
            if cross_ml>=4.0:
                qty_iso=round_qty((usdt_cross*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
                if price*qty_iso>=CONFIG['min_notional']:
                    decisions.append({'mode':'ISOLATED','coin':coin,'action':'BUILD','side':'BUY','qty':qty_iso,'price':price})
                    print(f"  🏗️ {coin}: ISOLATED建仓 BUY {qty_iso} (RSI={rsi:.0f})")
    return decisions

def op_add_all(market, cross_assets, isolated_assets, cross_ml, usdt_cross):
    """2. 加仓 - CROSS+ISOLATED"""
    decisions=[]
    if cross_ml<4.0: return decisions
    
    # CROSS加仓
    cross_positions=[a for a,m in cross_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']
    for coin in cross_positions:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<35 and price>0:
            qty=round_qty((usdt_cross*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
            if price*qty>=CONFIG['min_notional']:
                decisions.append({'mode':'CROSS','coin':coin,'action':'ADD','side':'BUY','qty':qty,'price':price})
                print(f"  📈 {coin}: CROSS加仓 BUY {qty} (RSI={rsi:.0f})")
    
    # ISOLATED加仓
    for sym in isolated_assets:
        coin=sym.replace('USDT','')
        if coin in market:
            rsi=market[coin]['rsi_1h']; price=market[coin]['price']
            if rsi<35 and price>0:
                qty=round_qty((usdt_cross*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
                if price*qty>=CONFIG['min_notional']:
                    decisions.append({'mode':'ISOLATED','coin':coin,'action':'ADD','side':'BUY','qty':qty,'price':price})
                    print(f"  📈 {coin}: ISOLATED加仓 BUY {qty} (RSI={rsi:.0f})")
    return decisions

def op_stop_loss_all(market, cross_assets, isolated_assets, trade_history):
    """3. 止损 - CROSS+ISOLATED"""
    decisions=[]
    
    # CROSS止损
    for coin in list(cross_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=cross_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(f'CROSS_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=80 or profit<=-0.03:
            qty=round_qty(abs(net),coin)
            decisions.append({'mode':'CROSS','coin':coin,'action':'STOP_LOSS','side':'SELL','qty':qty,'price':price})
            print(f"  🛡️ {coin}: CROSS止损 SELL {qty} (RSI={rsi:.0f}, {profit*100:+.1f}%)")
    
    # ISOLATED止损
    for sym in list(isolated_assets.keys()):
        coin=sym.replace('USDT','')
        if coin not in market: continue
        base=isolated_assets[sym].get('base',{}).get('net',0)
        if abs(base)<0.0001: continue
        price=market[coin]['price']
        entry=trade_history.get(f'ISOLATED_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=80 or profit<=-0.03:
            qty=round_qty(abs(base),coin)
            decisions.append({'mode':'ISOLATED','coin':coin,'action':'STOP_LOSS','side':'SELL','qty':qty,'price':price})
            print(f"  🛡️ {coin}: ISOLATED止损 SELL {qty} (RSI={rsi:.0f}, {profit*100:+.1f}%)")
    return decisions

def op_take_profit_all(market, cross_assets, isolated_assets, trade_history):
    """4. 止盈 - CROSS+ISOLATED"""
    decisions=[]
    for coin in list(cross_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=cross_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(f'CROSS_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=75 or profit>=CONFIG['tp']:
            qty=round_qty(abs(net)*0.5,coin)
            decisions.append({'mode':'CROSS','coin':coin,'action':'TAKE_PROFIT','side':'SELL','qty':qty,'price':price})
            print(f"  💰 {coin}: CROSS止盈50% SELL {qty} (RSI={rsi:.0f}, {profit*100:+.1f}%)")
    return decisions

def op_reduce_all(market, cross_assets, isolated_assets):
    """5. 减仓"""
    decisions=[]
    for coin in list(cross_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=cross_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']
        if rsi>=70:
            qty=round_qty(abs(net)*0.2,coin)
            decisions.append({'mode':'CROSS','coin':coin,'action':'REDUCE','side':'SELL','qty':qty,'price':market[coin]['price']})
            print(f"  📉 {coin}: CROSS减仓20% SELL {qty} (RSI={rsi:.0f})")
    return decisions

def op_close_all(market, cross_assets, isolated_assets, cross_ml):
    """6-7. 平仓/全部平仓"""
    decisions=[]
    # CROSS全部平仓
    if cross_ml<3.0:
        for coin in list(cross_assets.keys()):
            if coin=='USDT': continue
            net=cross_assets[coin].get('net',0)
            price=market.get(coin,{}).get('price',0)
            if abs(net)>0.0001 and price>0:
                qty=round_qty(abs(net),coin)
                decisions.append({'mode':'CROSS','coin':coin,'action':'CLOSE_ALL','side':'SELL','qty':qty,'price':price})
                print(f"  🚨 {coin}: CROSS全部平仓 SELL {qty}")
    
    # ISOLATED全部平仓
    for sym in list(isolated_assets.keys()):
        coin=sym.replace('USDT','')
        base=isolated_assets[sym].get('base',{}).get('net',0)
        price=market.get(coin,{}).get('price',0)
        if abs(base)>0.0001 and price>0:
            rsi=market.get(coin,{}).get('rsi_1h',50)
            if rsi>=85:
                qty=round_qty(abs(base),coin)
                decisions.append({'mode':'ISOLATED','coin':coin,'action':'CLOSE','side':'SELL','qty':qty,'price':price})
                print(f"  🚨 {coin}: ISOLATED平仓 SELL {qty}")
    return decisions

def op_wallet_transfer(spot_balances, cross_assets, cross_ml):
    """14. 钱包转账 SPOT↔CROSS"""
    transfers=[]
    spot_usdt=spot_balances.get('USDT',{}).get('total',0)
    cross_usdt=cross_assets.get('USDT',{}).get('free',0)
    
    if spot_usdt>500 and cross_ml>5.0:
        amount=min(spot_usdt-100, 200)
        if amount>10:
            result=transfer('USDT', amount, 'SPOT', 'MARGIN')
            transfers.append({'from':'SPOT','to':'CROSS','amount':amount})
            print(f"  💼 SPOT→CROSS ${amount:.2f}")
    elif cross_ml<4.0 and cross_usdt>50:
        amount=min(cross_usdt-20, 100)
        if amount>10:
            result=transfer('USDT', amount, 'MARGIN', 'SPOT')
            transfers.append({'from':'CROSS','to':'SPOT','amount':amount})
            print(f"  💼 CROSS→SPOT ${amount:.2f}")
    return transfers

def op_execution_verification(coin, side, qty, mode, result):
    """15. 执行验证"""
    time.sleep(3)
    try:
        if 'error' not in result and 'code' not in result:
            log_verify(f"VERIFIED: {mode} {coin} {side} {qty}")
            print(f"  ✅ {mode} {coin} {side} {qty}")
            return True
    except: pass
    log_verify(f"FAILED: {mode} {coin} {side} {qty}")
    return False

# ========== Hermes调度 ==========
def hermes_scheduler():
    print("\n"+"="*60)
    print("📋 Hermes 调度任务")
    print("="*60)
    called=[]
    
    if should_run('gg_spike', 300):
        print("\n📡 调用: gg_spike_system.sh")
        ok, _=call_script('gg_spike_system.sh', 120)
        mark_run('gg_spike')
        called.append(('spike', ok))
        print(f"  {'✅' if ok else '❌'} gg_spike")
    
    if should_run('gg_autonomous', 1800):
        print("\n🔄 调用: gg_autonomous_iterate.sh")
        ok, _=call_script('gg_autonomous_iterate.sh', 180)
        mark_run('gg_autonomous')
        called.append(('autonomous', ok))
        print(f"  {'✅' if ok else '❌'} gg_autonomous")
    
    if should_run('gg_asset', 1800):
        print("\n💰 调用: gg_asset_scanner.sh")
        ok, _=call_script('gg_asset_scanner.sh', 120)
        mark_run('gg_asset')
        called.append(('asset', ok))
        print(f"  {'✅' if ok else '❌'} gg_asset")
    
    return called

# ========== 执行引擎 ==========
def execute_all(decisions, trade_history):
    print("\n"+"="*60)
    print("⚡ 执行交易")
    print("="*60)
    results=[]
    for d in decisions:
        coin=d['coin']; side=d['side']; qty=d['qty']; mode=d['mode']; action=d['action']
        print(f"\n📤 {action}: {mode} {coin} {side} {qty}")
        result=execute_trade(mode, f'{coin}USDT', side, qty)
        verified=op_execution_verification(coin, side, qty, mode, result)
        results.append({'mode':mode,'coin':coin,'action':action,'verified':verified})
        if verified and side=='BUY':
            trade_history[f'{mode}_{coin}']={'entry_price':d['price'],'entry_time':datetime.now().strftime('%H:%M')}
    save_trade_history(trade_history)
    return results

# ========== 主程序 ==========
print("\n"+"="*70)
print("🎯 Hermes v5.2 - SPOT + CROSS + ISOLATED")
print("="*70)

trade_history=load_trade_history()

market=market_sensing()
spot_balances=get_spot_data()
cross_ml, cross_assets=get_cross_margin_data()
isolated_assets=get_isolated_margin_data()

prices={'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
        'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
        'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1}

spot_total=sum(spot_balances.get(a,{}).get('total',0)*prices.get(a,1) for a in spot_balances)
cross_total=sum(abs(m.get('net',0))*prices.get(a,1) for a,m in cross_assets.items())
total_assets=spot_total+cross_total

usdt_spot=spot_balances.get('USDT',{}).get('total',0)
usdt_cross=cross_assets.get('USDT',{}).get('free',0)

spot_positions=[a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']
cross_positions=[a for a,m in cross_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']
isolated_positions=[sym for sym in isolated_assets]

print(f"\n【三账户概览】")
print(f"  SPOT: ${spot_total:.2f} (USDT: ${usdt_spot:.2f})")
print(f"  CROSS: ${cross_total:.2f} (保证金率: {cross_ml:.3f})")
print(f"  ISOLATED: {len(isolated_positions)}个仓位")
print(f"  总资产: ${total_assets:.2f}")
print(f"  SPOT持仓: {spot_positions}")
print(f"  CROSS持仓: {cross_positions}")
print(f"  ISOLATED: {isolated_positions}")

scheduled=hermes_scheduler()

# 风险评估
print("\n"+"="*60)
print("⚠️ 风险评估")
print("="*60)
risks=[]
if cross_ml<3.0: risks.append(f"CROSS保证金率过低: {cross_ml:.2f}")
if cross_ml<4.0: risks.append(f"CROSS保证金率预警: {cross_ml:.2f}")
for r in risks: print(f"  ⚠️ {r}")
if not risks: print("  ✅ 无风险")

# 生成决策
all_decisions=[]
all_decisions.extend(op_close_all(market, cross_assets, isolated_assets, cross_ml))
all_decisions.extend(op_stop_loss_all(market, cross_assets, isolated_assets, trade_history))
all_decisions.extend(op_take_profit_all(market, cross_assets, isolated_assets, trade_history))
all_decisions.extend(op_reduce_all(market, cross_assets, isolated_assets))
all_decisions.extend(op_add_all(market, cross_assets, isolated_assets, cross_ml, usdt_cross))
all_decisions.extend(op_build_all(market, spot_balances, cross_assets, isolated_assets, cross_ml, usdt_spot, usdt_cross))

transfers=op_wallet_transfer(spot_balances, cross_assets, cross_ml)

print(f"\n【决策汇总】{len(all_decisions)}个")
action_counts={}
for d in all_decisions:
    key=f"{d['mode']}_{d['action']}"
    action_counts[key]=action_counts.get(key,0)+1
for a,c in sorted(action_counts.items()):
    print(f"  {a}: {c}个")

results=execute_all(all_decisions, trade_history)

print("\n"+"="*70)
print("【v5.2总结】")
print("="*70)
for mode in ['SPOT','CROSS','ISOLATED']:
    v=sum(1 for r in results if r.get('mode')==mode and r.get('verified'))
    print(f"{mode}执行: {v}笔")
print(f"总执行: {len(results)}笔")
print(f"风险: {len(risks)}个")
print(f"调度: {len(scheduled)}个")
print("="*70)
PYEOF
