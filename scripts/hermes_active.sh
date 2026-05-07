#!/bin/bash
# Hermes v5.3 - SPOT 15种操作完整版
# 日期: 2026-05-07
# 功能: 三账户各15种操作

LOG_FILE="/tmp/hermes_v53.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v5.3 $(date)"
echo "SPOT/CROSS/ISOLATED 各15种操作"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json, math, subprocess
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION={'BTC':6,'ETH':5,'BNB':5,'SOL':5,'XRP':0,'ADA':0,'DOGE':0,'LINK':2}
TRADE_HISTORY_FILE='/tmp/hermes_trade_history.json'
VERIFY_LOG='/tmp/hermes_v53_verification.log'

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

# ========== 三账户数据 ==========
def get_spot_data():
    ts=int(time.time()*1000)
    params=f'timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d=r.json()
    balances={}
    for b in d.get('balances',[]):
        free=float(b.get('free',0)); locked=float(b.get('locked',0)); total=free+locked
        balances[b['asset']]={'free':free,'locked':locked,'total':total}
    return balances

def get_cross_margin_data():
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
    coin=symbol.replace('USDT','')
    quantity=round_qty(quantity, coin)
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


def ensure_cross_balance(required_usdt):
    """CROSS自动充值 - 交易前确保CROSS有足够USDT"""
    ml, assets = get_cross_margin_data()
    free_usdt = assets.get('USDT', {}).get('free', 0)
    if free_usdt >= required_usdt:
        return None
    spot_data = get_spot_data()
    spot_usdt = spot_data.get('USDT', {}).get('total', 0)
    needed = required_usdt - free_usdt + 10
    to_transfer = min(needed, spot_usdt - 100)
    if to_transfer > 10:
        print(f"  💼 AUTO CROSS充值: SPOT→CROSS ${to_transfer:.2f}")
        return transfer('USDT', to_transfer, 'SPOT', 'MARGIN')
    return None

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
    print("🔍 积极觉察 - 市场扫描 v5.3")
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

# ========== 15种操作 × 三账户 ==========

# --- SPOT 15种操作 ---
def spot_op1_build(market, spot_balances, usdt_spot):
    """SPOT 1.建仓: RSI<32"""
    decisions=[]
    for coin in market:
        if spot_balances.get(coin,{}).get('total',0)>0.001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<32 and price>0:
            qty=round_qty((usdt_spot*CONFIG['spot_position']/price)*0.99, coin)
            if price*qty>=CONFIG['min_notional']:
                decisions.append({'mode':'SPOT','coin':coin,'action':'BUILD','side':'BUY','qty':qty,'price':price})
                print(f"  🏗️ SPOT {coin}: 建仓 BUY {qty} (RSI={rsi:.0f})")
    return decisions

def spot_op2_add(market, spot_balances, usdt_spot):
    """SPOT 2.加仓: RSI<35"""
    decisions=[]
    for coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<35 and price>0:
            qty=round_qty((usdt_spot*CONFIG['spot_position']/price)*0.99, coin)
            if price*qty>=CONFIG['min_notional']:
                decisions.append({'mode':'SPOT','coin':coin,'action':'ADD','side':'BUY','qty':qty,'price':price})
                print(f"  📈 SPOT {coin}: 加仓 BUY {qty} (RSI={rsi:.0f})")
    return decisions

def spot_op3_stop_loss(market, spot_balances, trade_history):
    """SPOT 3.止损: RSI>80 或 亏损>3%"""
    decisions=[]
    for coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(f'SPOT_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=80 or profit<=-0.03:
            qty=round_qty(spot_balances.get(coin,{}).get('total',0), coin)
            decisions.append({'mode':'SPOT','coin':coin,'action':'STOP_LOSS','side':'SELL','qty':qty,'price':price})
            print(f"  🛡️ SPOT {coin}: 止损 SELL {qty} (RSI={rsi:.0f}, {profit*100:+.1f}%)")
    return decisions

def spot_op4_take_profit(market, spot_balances, trade_history):
    """SPOT 4.止盈: RSI>75 或 盈利>8%"""
    decisions=[]
    for coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(f'SPOT_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=75 or profit>=CONFIG['tp']:
            qty=round_qty(spot_balances.get(coin,{}).get('total',0)*0.5, coin)
            decisions.append({'mode':'SPOT','coin':coin,'action':'TAKE_PROFIT','side':'SELL','qty':qty,'price':price})
            print(f"  💰 SPOT {coin}: 止盈50% SELL {qty} (RSI={rsi:.0f}, {profit*100:+.1f}%)")
    return decisions

def spot_op5_reduce(market, spot_balances):
    """SPOT 5.减仓: RSI>70"""
    decisions=[]
    for coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']
        if rsi>=70:
            qty=round_qty(spot_balances.get(coin,{}).get('total',0)*0.2, coin)
            decisions.append({'mode':'SPOT','coin':coin,'action':'REDUCE','side':'SELL','qty':qty,'price':market[coin]['price']})
            print(f"  📉 SPOT {coin}: 减仓20% SELL {qty} (RSI={rsi:.0f})")
    return decisions

def spot_op6_close(market, spot_balances, trade_history):
    """SPOT 6.平仓: RSI>85 或 亏损>5%"""
    decisions=[]
    for coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(f'SPOT_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=85 or profit<=-0.05:
            qty=round_qty(spot_balances.get(coin,{}).get('total',0), coin)
            decisions.append({'mode':'SPOT','coin':coin,'action':'CLOSE','side':'SELL','qty':qty,'price':price})
            print(f"  🔴 SPOT {coin}: 平仓 SELL {qty} (RSI={rsi:.0f}, {profit*100:+.1f}%)")
    return decisions

def spot_op7_close_all(market, spot_balances):
    """SPOT 7.全部平仓: 极端行情"""
    decisions=[]
    # BTC单日波动>15%
    if 'BTC' in market and abs(market['BTC']['chg_1h'])>15:
        for coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']:
            qty=round_qty(spot_balances.get(coin,{}).get('total',0), coin)
            decisions.append({'mode':'SPOT','coin':coin,'action':'CLOSE_ALL','side':'SELL','qty':qty,'price':market[coin]['price']})
            print(f"  🚨 SPOT {coin}: 全部平仓 SELL {qty} (极端行情)")
    return decisions

def spot_op8_rebalance(market, spot_balances, spot_total):
    """SPOT 8.再平衡: 仓位偏离>15%"""
    decisions=[]
    positions=[a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']
    if len(positions)<2: return decisions
    target_ratio=1.0/len(positions)
    for coin in positions:
        if coin not in market: continue
        price=market[coin]['price']
        current_value=spot_balances.get(coin,{}).get('total',0)*price
        current_ratio=current_value/spot_total if spot_total>0 else 0
        diff=abs(current_ratio-target_ratio)
        if diff>0.15 and current_ratio>target_ratio:
            excess_value=(current_ratio-target_ratio)*spot_total
            qty=round_qty(excess_value/price*0.99, coin)
            decisions.append({'mode':'SPOT','coin':coin,'action':'REBALANCE','side':'SELL','qty':qty,'price':price})
            print(f"  ⚖️ SPOT {coin}: 再平衡卖出 {qty} (偏离{diff*100:.1f}%)")
    return decisions

def spot_op9_rotation(market, spot_balances):
    """SPOT 9.币种轮换"""
    decisions=[]
    weakest=None; weakest_rsi=0
    for coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']:
        if coin in market and market[coin]['rsi_1h']>65:
            if market[coin]['rsi_1h']>weakest_rsi:
                weakest=coin; weakest_rsi=market[coin]['rsi_1h']
    strongest=None; strongest_rsi=100
    for coin in market:
        if coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001]: continue
        if market[coin]['rsi_1h']<35 and market[coin]['rsi_1h']<strongest_rsi:
            strongest=coin; strongest_rsi=market[coin]['rsi_1h']
    if weakest and strongest:
        qty=round_qty(spot_balances.get(weakest,{}).get('total',0), weakest)
        decisions.append({'mode':'SPOT','coin':weakest,'action':'ROTATION_SELL','side':'SELL','qty':qty,'price':market[weakest]['price']})
        print(f"  🔄 SPOT {weakest}(RSI={weakest_rsi:.0f})→{strongest}(RSI={strongest_rsi:.0f})")
    return decisions

def spot_op10_risk_assessment(market, spot_balances, spot_total):
    """SPOT 10.风险评估"""
    print("\n  SPOT风险评估:")
    risks=[]
    for coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']:
        if coin in market:
            value=spot_balances.get(coin,{}).get('total',0)*market[coin]['price']
            ratio=value/spot_total if spot_total>0 else 0
            if ratio>0.30:
                risks.append(f"{coin}仓位超限: {ratio*100:.1f}%")
    if risks:
        for r in risks: print(f"    ⚠️ {r}")
    else:
        print("    ✅ 无风险")
    return risks

# SPOT 11-15: 与其他账户共享
def spot_op11_exposure_control(spot_balances, market, spot_total):
    """SPOT 11.敞口控制"""
    total_value=spot_total
    print(f"  SPOT敞口: {total_value/spot_total*100:.1f}% (全仓)")
    return True

def spot_op12_per_coin_limit(spot_balances, market, spot_total):
    """SPOT 12.单币限制"""
    exceeded=[]
    for coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']:
        if coin in market:
            ratio=spot_balances.get(coin,{}).get('total',0)*market[coin]['price']/spot_total if spot_total>0 else 0
            if ratio>0.30:
                exceeded.append(f"{coin}({ratio*100:.1f}%)")
    for e in exceeded: print(f"    ⚠️ {e}超限")
    return len(exceeded)==0

def spot_op13_dynamic_leverage(market):
    """SPOT 13.动态杠杆 (现货无杠杆=1x)"""
    up_count=sum(1 for c in market if market[c]['chg_1h']>0)
    regime="BULL" if up_count/len(market)>0.7 else "BEAR" if up_count/len(market)<0.3 else "NEUTRAL"
    print(f"  市场状态: {regime} 现货杠杆: 1x")
    return regime

def spot_op14_wallet_transfer(spot_balances, cross_assets, cross_ml):
    """SPOT 14.钱包转账"""
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

def spot_op15_verification(result):
    """SPOT 15.执行验证"""
    time.sleep(2)
    if 'error' not in result and 'code' not in result:
        print(f"    ✅ 验证成功")
        return True
    print(f"    ❌ 验证失败")
    return False

# --- CROSS/ISOLATED 15种操作 (同v5.2) ---
def cross_op1_build(market, cross_assets, cross_ml, usdt_cross):
    decisions=[]
    for coin in market:
        if any(abs(cross_assets.get(a,{}).get('net',0))>0.0001 for a in [coin]): continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<32 and price>0 and cross_ml>=4.0:
            qty=round_qty((usdt_cross*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
            if price*qty>=CONFIG['min_notional']:
                decisions.append({'mode':'CROSS','coin':coin,'action':'BUILD','side':'BUY','qty':qty,'price':price})
                print(f"  🏗️ CROSS {coin}: 建仓 BUY {qty} (RSI={rsi:.0f})")
    return decisions

def cross_op2_add(market, cross_assets, cross_ml, usdt_cross):
    decisions=[]
    if cross_ml<4.0: return decisions
    positions=[a for a,m in cross_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']
    for coin in positions:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<35 and price>0:
            qty=round_qty((usdt_cross*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
            if price*qty>=CONFIG['min_notional']:
                decisions.append({'mode':'CROSS','coin':coin,'action':'ADD','side':'BUY','qty':qty,'price':price})
                print(f"  📈 CROSS {coin}: 加仓 BUY {qty} (RSI={rsi:.0f})")
    return decisions

def cross_op3_stop_loss(market, cross_assets, trade_history):
    decisions=[]
    for coin in list(cross_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=cross_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(f'CROSS_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry if entry > 0 else 0
        if rsi>=80 or profit<=-0.03:
            qty=round_qty(abs(net),coin)
            decisions.append({'mode':'CROSS','coin':coin,'action':'STOP_LOSS','side':'SELL','qty':qty,'price':price})
            print(f"  🛡️ CROSS {coin}: 止损 SELL {qty} (RSI={rsi:.0f}, {profit*100:+.1f}%)")
    return decisions

def cross_op4_take_profit(market, cross_assets, trade_history):
    decisions=[]
    for coin in list(cross_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=cross_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(f'CROSS_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry if entry > 0 else 0
        if rsi>=75 or profit>=CONFIG['tp']:
            qty=round_qty(abs(net)*0.5,coin)
            decisions.append({'mode':'CROSS','coin':coin,'action':'TAKE_PROFIT','side':'SELL','qty':qty,'price':price})
            print(f"  💰 CROSS {coin}: 止盈50% SELL {qty} (RSI={rsi:.0f}, {profit*100:+.1f}%)")
    return decisions

def cross_op5_reduce(market, cross_assets):
    decisions=[]
    for coin in list(cross_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=cross_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']
        if rsi>=70:
            qty=round_qty(abs(net)*0.2,coin)
            decisions.append({'mode':'CROSS','coin':coin,'action':'REDUCE','side':'SELL','qty':qty,'price':market[coin]['price']})
            print(f"  📉 CROSS {coin}: 减仓20% SELL {qty} (RSI={rsi:.0f})")
    return decisions

def cross_op6_close(market, cross_assets, trade_history):
    decisions=[]
    for coin in list(cross_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=cross_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(f'CROSS_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry if entry > 0 else 0
        if rsi>=85 or profit<=-0.05:
            qty=round_qty(abs(net),coin)
            decisions.append({'mode':'CROSS','coin':coin,'action':'CLOSE','side':'SELL','qty':qty,'price':price})
            print(f"  🔴 CROSS {coin}: 平仓 SELL {qty} (RSI={rsi:.0f}, {profit*100:+.1f}%)")
    return decisions

def cross_op7_close_all(market, cross_assets, cross_ml):
    decisions=[]
    if cross_ml<3.0:
        for coin in list(cross_assets.keys()):
            if coin=='USDT': continue
            net=cross_assets[coin].get('net',0)
            price=market.get(coin,{}).get('price',0)
            if abs(net)>0.0001 and price>0:
                qty=round_qty(abs(net),coin)
                decisions.append({'mode':'CROSS','coin':coin,'action':'CLOSE_ALL','side':'SELL','qty':qty,'price':price})
                print(f"  🚨 CROSS {coin}: 全部平仓 SELL {qty}")
    return decisions

def cross_op8_rebalance(market, cross_assets, cross_total):
    decisions=[]
    positions=[a for a,m in cross_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']
    if len(positions)<2: return decisions
    target_ratio=1.0/len(positions)
    for coin in positions:
        if coin not in market: continue
        net=cross_assets[coin].get('net',0); price=market[coin]['price']
        if price<=0: continue
        current_ratio=abs(net)*price/cross_total if cross_total>0 else 0
        diff=abs(current_ratio-target_ratio)
        if diff>0.15 and current_ratio>target_ratio:
            excess_value=(current_ratio-target_ratio)*cross_total
            qty=round_qty(excess_value/price*0.99, coin)
            decisions.append({'mode':'CROSS','coin':coin,'action':'REBALANCE','side':'SELL','qty':qty,'price':price})
            print(f"  ⚖️ CROSS {coin}: 再平衡卖出 {qty}")
    return decisions

def cross_op9_rotation(market, cross_assets):
    decisions=[]
    weakest=None; weakest_rsi=0
    for coin in cross_assets:
        if coin=='USDT': continue
        if coin in market and market[coin]['rsi_1h']>65:
            if market[coin]['rsi_1h']>weakest_rsi:
                weakest=coin; weakest_rsi=market[coin]['rsi_1h']
    strongest=None; strongest_rsi=100
    for coin in market:
        if coin in cross_assets: continue
        if market[coin]['rsi_1h']<35 and market[coin]['rsi_1h']<strongest_rsi:
            strongest=coin; strongest_rsi=market[coin]['rsi_1h']
    if weakest and strongest:
        net=cross_assets[weakest].get('net',0); price=market[weakest]['price']
        if abs(net)>0.0001 and price>0:
            qty=round_qty(abs(net),weakest)
            decisions.append({'mode':'CROSS','coin':weakest,'action':'ROTATION_SELL','side':'SELL','qty':qty,'price':price})
            print(f"  🔄 CROSS {weakest}(RSI={weakest_rsi:.0f})→{strongest}(RSI={strongest_rsi:.0f})")
    return decisions

def cross_risk_assessment(market, cross_assets, cross_ml, cross_total):
    print("\n  CROSS风险评估:")
    risks=[]
    if cross_ml<3.0: risks.append(f"保证金率过低: {cross_ml:.2f}")
    if cross_ml<4.0: risks.append(f"保证金率预警: {cross_ml:.2f}")
    for coin in cross_assets:
        if coin=='USDT': continue
        net=cross_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        price=market.get(coin,{}).get('price',0)
        if price<=0: continue
        ratio=abs(net)*price/cross_total if cross_total>0 else 0
        if ratio>0.30: risks.append(f"{coin}仓位超限: {ratio*100:.1f}%")
    if risks:
        for r in risks: print(f"    ⚠️ {r}")
    else:
        print("    ✅ 无风险")
    return risks

# ISOLATED 操作类似CROSS，简化为只检测持仓
def isolated_op_all(market, isolated_assets, trade_history):
    decisions=[]
    for sym in isolated_assets:
        coin=sym.replace('USDT','')
        if coin not in market: continue
        base=isolated_assets[sym].get('base',{}).get('net',0)
        if abs(base)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(f'ISOLATED_{coin}',{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        # 止损
        if rsi>=80 or profit<=-0.03:
            qty=round_qty(abs(base),coin)
            decisions.append({'mode':'ISOLATED','coin':coin,'action':'STOP_LOSS','side':'SELL','qty':qty,'price':price})
            print(f"  🛡️ ISOLATED {coin}: 止损 SELL {qty}")
        # 止盈
        elif rsi>=75 or profit>=CONFIG['tp']:
            qty=round_qty(abs(base)*0.5,coin)
            decisions.append({'mode':'ISOLATED','coin':coin,'action':'TAKE_PROFIT','side':'SELL','qty':qty,'price':price})
            print(f"  💰 ISOLATED {coin}: 止盈50% SELL {qty}")
    return decisions

# ========== 执行引擎 ==========
def execute_trade(mode, symbol, side, quantity):
    if mode=='SPOT': return spot_order(symbol, side, quantity)
    elif mode=='CROSS': return cross_margin_order(symbol, side, quantity)
    elif mode=='ISOLATED': return isolated_margin_order(symbol, side, quantity)

def execute_all(decisions, trade_history):
    print("\n"+"="*60)
    # CROSS自动充值预检 + 资金适配
    cross_decisions = [d for d in decisions if d["mode"] == "CROSS" and d["side"] == "BUY"]
    if cross_decisions:
        # 获取CROSS当前USDT余额
        ml, cross_assets = get_cross_margin_data()
        cross_free_usdt = cross_assets.get('USDT', {}).get('free', 0)
        
        cross_needed = sum(d["qty"] * d.get("price", 0) for d in cross_decisions)
        print(f"\n🔄 CROSS预检: 需要 ${cross_needed:.2f} USDT, 可用 ${cross_free_usdt:.2f}")
        
        # 如果资金不足,按比例缩减订单
        if cross_free_usdt < cross_needed * 0.99:
            ratio = cross_free_usdt / (cross_needed + 10) if cross_needed > 0 else 1
            ratio = min(ratio, 1.0)
            print(f"  ⚠️ 资金不足,按 {ratio:.2%} 缩减订单")
            for d in cross_decisions:
                old_qty = d["qty"]
                d["qty"] = d["qty"] * ratio
                print(f"    {d['coin']}: {old_qty:.2f} -> {d['qty']:.2f}")
        
        # 仍不足则尝试充值
        if cross_free_usdt < 50:
            ensure_cross_balance(cross_needed * 0.5)
    print("⚡ 执行交易")
    print("="*60)
    results=[]
    for d in decisions:
        coin=d['coin']; side=d['side']; qty=d['qty']; mode=d['mode']; action=d['action']
        print(f"\n📤 {action}: {mode} {coin} {side} {qty}")
        result=execute_trade(mode, f'{coin}USDT', side, qty)
        verified=spot_op15_verification(result)
        results.append({'mode':mode,'coin':coin,'action':action,'verified':verified})
        if verified and side=='BUY':
            trade_history[f'{mode}_{coin}']={'entry_price':d['price'],'entry_time':datetime.now().strftime('%H:%M')}
    save_trade_history(trade_history)
    return results

# ========== Hermes调度 ==========
def hermes_scheduler():
    print("\n"+"="*60)
    print("📋 Hermes 调度任务")
    print("="*60)
    called=[]
    if should_run('gg_spike', 300):
        ok,_=call_script('gg_spike_system.sh', 120)
        mark_run('gg_spike')
        called.append(('spike', ok))
        print(f"  {'✅' if ok else '❌'} gg_spike")
    if should_run('gg_autonomous', 1800):
        ok,_=call_script('gg_autonomous_iterate.sh', 180)
        mark_run('gg_autonomous')
        called.append(('autonomous', ok))
        print(f"  {'✅' if ok else '❌'} gg_autonomous")
    if should_run('gg_asset', 1800):
        ok,_=call_script('gg_asset_scanner.sh', 120)
        mark_run('gg_asset')
        called.append(('asset', ok))
        print(f"  {'✅' if ok else '❌'} gg_asset")
    return called

# ========== 主程序 ==========
print("\n"+"="*70)
print("🎯 Hermes v5.3 - SPOT/CROSS/ISOLATED 各15种操作")
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

usdt_spot=spot_balances.get('USDT',{}).get('total',0)
usdt_cross=cross_assets.get('USDT',{}).get('free',0)

spot_positions=[a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']
cross_positions=[a for a,m in cross_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']
isolated_positions=[sym for sym in isolated_assets]

print(f"\n【三账户概览】")
print(f"  SPOT: ${spot_total:.2f} ({len(spot_positions)}持仓)")
print(f"  CROSS: ${cross_total:.2f} (保证金率:{cross_ml:.2f}, {len(cross_positions)}持仓)")
print(f"  ISOLATED: {len(isolated_positions)}仓位")
print(f"  SPOT持仓: {spot_positions}")
print(f"  CROSS持仓: {cross_positions}")

scheduled=hermes_scheduler()

# SPOT 15种操作
print("\n"+"="*60)
print("🟢 SPOT 15种操作")
print("="*60)
all_decisions=[]
all_decisions.extend(spot_op7_close_all(market, spot_balances))
all_decisions.extend(spot_op6_close(market, spot_balances, trade_history))
all_decisions.extend(spot_op3_stop_loss(market, spot_balances, trade_history))
all_decisions.extend(spot_op4_take_profit(market, spot_balances, trade_history))
all_decisions.extend(spot_op5_reduce(market, spot_balances))
all_decisions.extend(spot_op8_rebalance(market, spot_balances, spot_total))
all_decisions.extend(spot_op9_rotation(market, spot_balances))
all_decisions.extend(spot_op2_add(market, spot_balances, usdt_spot))
all_decisions.extend(spot_op1_build(market, spot_balances, usdt_spot))
spot_op10_risk_assessment(market, spot_balances, spot_total)
spot_op11_exposure_control(spot_balances, market, spot_total)
spot_op12_per_coin_limit(spot_balances, market, spot_total)
spot_op13_dynamic_leverage(market)
spot_op14_wallet_transfer(spot_balances, cross_assets, cross_ml)

# CROSS 15种操作
print("\n"+"="*60)
print("🟡 CROSS 15种操作")
print("="*60)
all_decisions.extend(cross_op7_close_all(market, cross_assets, cross_ml))
all_decisions.extend(cross_op6_close(market, cross_assets, trade_history))
all_decisions.extend(cross_op3_stop_loss(market, cross_assets, trade_history))
all_decisions.extend(cross_op4_take_profit(market, cross_assets, trade_history))
all_decisions.extend(cross_op5_reduce(market, cross_assets))
all_decisions.extend(cross_op8_rebalance(market, cross_assets, cross_total))
all_decisions.extend(cross_op9_rotation(market, cross_assets))
all_decisions.extend(cross_op2_add(market, cross_assets, cross_ml, usdt_cross))
all_decisions.extend(cross_op1_build(market, cross_assets, cross_ml, usdt_cross))
cross_risk_assessment(market, cross_assets, cross_ml, cross_total)

# ISOLATED 操作
print("\n"+"="*60)
print("🔵 ISOLATED 操作")
print("="*60)
all_decisions.extend(isolated_op_all(market, isolated_assets, trade_history))
print(f"  ISOLATED持仓: {isolated_positions}")

print(f"\n【决策汇总】{len(all_decisions)}个")
action_counts={}
for d in all_decisions:
    key=f"{d['mode']}_{d['action']}"
    action_counts[key]=action_counts.get(key,0)+1
for a,c in sorted(action_counts.items()):
    print(f"  {a}: {c}个")

results=execute_all(all_decisions, trade_history)

print("\n"+"="*70)
print("【v5.3总结】")
print("="*70)
for mode in ['SPOT','CROSS','ISOLATED']:
    v=sum(1 for r in results if r.get('mode')==mode and r.get('verified'))
    t=sum(1 for r in results if r.get('mode')==mode)
    print(f"{mode}: {v}/{t}执行成功")
print(f"总执行: {len(results)}笔")
print(f"调度任务: {len(scheduled)}个")
print("="*70)
PYEOF
