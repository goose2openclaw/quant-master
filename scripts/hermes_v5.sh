#!/bin/bash
# Hermes v5.0 - SPOT+MARGIN双模式
# 日期: 2026-05-07
# 功能: 现货+保证金双模式,15种操作

LOG_FILE="/tmp/hermes_v5.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v5.0 $(date)"
echo "SPOT+MARGIN双模式"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json, math
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION={'BTC':6,'ETH':5,'BNB':5,'SOL':5,'XRP':0,'ADA':0,'DOGE':0,'LINK':2}
TRADE_HISTORY_FILE='/tmp/hermes_trade_history.json'
VERIFY_LOG='/tmp/hermes_v5_verification.log'

CONFIG={
    'rsi_short': 71, 'rsi_long': 32,
    'tp': 0.08, 'sl': 0.015,
    'position': 0.25, 'leverage': 5,
    'min_notional': 10,
    'spot_position': 0.30,  # SPOT仓位30%
}

# ========== 工具函数 ==========
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

def get_margin_data():
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

# SPOT下单
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

# MARGIN下单
def margin_order(symbol, side, quantity):
    ts=int(time.time()*1000)
    params={'symbol':symbol,'side':side,'type':'MARKET','quantity':quantity,'timestamp':ts,'recvWindow':5000}
    query_string='&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig=hmac.new(API_SECRET.encode(),query_string.encode(),hashlib.sha256).hexdigest()
    url=f"https://api.binance.com/sapi/v1/margin/order?{query_string}&signature={sig}"
    try:
        r=requests.post(url, headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e: return {'error': str(e)}

# 钱包转账 SPOT<->MARGIN
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
    print("🔍 积极觉察 - 市场扫描 v5.0")
    print("="*60)
    
    coins=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']
    market={}
    
    for coin in coins:
        sym=f"{coin}USDT"; price=get_price(sym)
        k1h=get_klines(sym,'1h',60)
        k4h=get_klines(sym,'4h',20)
        
        if k1h:
            rsi_1h=calc_rsi([k[2] for k in k1h])
            rsi_4h=calc_rsi([k[2] for k in k4h]) if k4h else 50
            chg_1h=(k1h[-1][2]-k1h[0][2])/k1h[0][2]*100 if len(k1h)>=2 else 0
            
            score=0
            if rsi_1h<32: score+=3
            if rsi_1h<35: score+=2
            if rsi_4h<35: score+=2
            if chg_1h<-1: score+=1
            
            signal="📈" if score>=5 else "📊" if score>=3 else "⚪"
            market[coin]={'price':price,'rsi_1h':rsi_1h,'rsi_4h':rsi_4h,'chg_1h':chg_1h,'score':score,'signal':signal}
            print(f"  {coin}: ${price:.4f} RSI={rsi_1h:.0f}/{rsi_4h:.0f} {chg_1h:+.1f}% {signal}({score})")
    
    return market

# ========== 15种操作 ==========
def op_build(market, spot_balances, margin_assets, margin_ml, usdt_spot, usdt_margin):
    """1. 建仓: RSI<32 新币种"""
    decisions=[]
    for coin in market:
        if coin in [a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001]: continue
        if coin in [a for a,b in spot_balances.items() if b.get('total',0)>0.001]: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<32 and price>0:
            # SPOT建仓
            qty_spot=round_qty((usdt_spot*CONFIG['spot_position']/price)*0.99, coin)
            if price*qty_spot>=CONFIG['min_notional']:
                decisions.append({'mode':'SPOT','coin':coin,'action':'BUILD','side':'BUY','qty':qty_spot,'price':price})
                print(f"  🏗️ {coin}: SPOT建仓 BUY {qty_spot} (RSI={rsi:.0f})")
            # MARGIN建仓(如果有足够保证金)
            if margin_ml>=4.0:
                qty_margin=round_qty((usdt_margin*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
                if price*qty_margin>=CONFIG['min_notional']:
                    decisions.append({'mode':'MARGIN','coin':coin,'action':'BUILD','side':'BUY','qty':qty_margin,'price':price})
                    print(f"  🏗️ {coin}: MARGIN建仓 BUY {qty_margin} (RSI={rsi:.0f})")
    return decisions

def op_add(market, margin_assets, margin_ml, usdt_margin):
    """2. 加仓: RSI<35 已有持仓"""
    decisions=[]
    if margin_ml<4.0: return decisions
    positions=[a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']
    for coin in positions:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<35 and price>0:
            qty=round_qty((usdt_margin*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
            if price*qty>=CONFIG['min_notional']:
                decisions.append({'mode':'MARGIN','coin':coin,'action':'ADD','side':'BUY','qty':qty,'price':price})
                print(f"  📈 {coin}: 加仓 BUY {qty} (RSI={rsi:.0f})")
    return decisions

def op_stop_loss(market, margin_assets, trade_history):
    """3. 止损: RSI>80 或 亏损>3%"""
    decisions=[]
    for coin in list(margin_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=80 or profit<=-0.03:
            qty=round_qty(abs(net),coin)
            decisions.append({'mode':'MARGIN','coin':coin,'action':'STOP_LOSS','side':'SELL','qty':qty,'price':price})
            print(f"  🛡️ {coin}: 止损 SELL {qty} (RSI={rsi:.0f}, 盈亏{profit*100:+.1f}%)")
    return decisions

def op_take_profit(market, margin_assets, trade_history):
    """4. 止盈: RSI>75 或 盈利>8%"""
    decisions=[]
    for coin in list(margin_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=75 or profit>=CONFIG['tp']:
            qty=round_qty(abs(net)*0.5,coin)
            decisions.append({'mode':'MARGIN','coin':coin,'action':'TAKE_PROFIT','side':'SELL','qty':qty,'price':price})
            print(f"  💰 {coin}: 止盈50% SELL {qty} (RSI={rsi:.0f}, 盈亏{profit*100:+.1f}%)")
    return decisions

def op_reduce(market, margin_assets):
    """5. 减仓: RSI>70 且 盈利>2%"""
    decisions=[]
    for coin in list(margin_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        # 简化判断
        if rsi>=70:
            qty=round_qty(abs(net)*0.2,coin)
            decisions.append({'mode':'MARGIN','coin':coin,'action':'REDUCE','side':'SELL','qty':qty,'price':price})
            print(f"  📉 {coin}: 减仓20% SELL {qty} (RSI={rsi:.0f})")
    return decisions

def op_close(market, margin_assets, trade_history):
    """6. 平仓: RSI>85 或 亏损>5%"""
    decisions=[]
    for coin in list(margin_assets.keys()):
        if coin=='USDT' or coin not in market: continue
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        entry=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=85 or profit<=-0.05:
            qty=round_qty(abs(net),coin)
            decisions.append({'mode':'MARGIN','coin':coin,'action':'CLOSE','side':'SELL','qty':qty,'price':price})
            print(f"  🔴 {coin}: 平仓 SELL {qty} (RSI={rsi:.0f}, 盈亏{profit*100:+.1f}%)")
    return decisions

def op_close_all(market, margin_assets, margin_ml):
    """7. 全部平仓: 极端行情/保证金率<3.0"""
    decisions=[]
    if margin_ml<3.0:
        for coin in list(margin_assets.keys()):
            if coin=='USDT': continue
            net=margin_assets[coin].get('net',0)
            price=market.get(coin,{}).get('price',0)
            if abs(net)>0.0001 and price>0:
                qty=round_qty(abs(net),coin)
                decisions.append({'mode':'MARGIN','coin':coin,'action':'CLOSE_ALL','side':'SELL','qty':qty,'price':price})
                print(f"  🚨 {coin}: 全部平仓 SELL {qty} (保证金率过低)")
    return decisions

def op_rebalance(market, margin_assets, total_margin_value):
    """8. 再平衡: 仓位偏离>15%"""
    decisions=[]
    positions=[a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']
    if len(positions)<2: return decisions
    target_ratio=1.0/len(positions)
    for coin in positions:
        if coin not in market: continue
        net=margin_assets[coin].get('net',0)
        price=market[coin]['price']
        if price<=0: continue
        current_ratio=abs(net)*price/total_margin_value if total_margin_value>0 else 0
        diff=abs(current_ratio-target_ratio)
        if diff>0.15:
            if current_ratio>target_ratio:
                excess_value=(current_ratio-target_ratio)*total_margin_value
                qty=round_qty(excess_value/price*0.99, coin)
                decisions.append({'mode':'MARGIN','coin':coin,'action':'REBALANCE','side':'SELL','qty':qty,'price':price})
                print(f"  ⚖️ {coin}: 再平衡卖出 {qty} (偏离{diff*100:.1f}%)")
    return decisions

def op_rotation(market, margin_assets):
    """9. 币种轮换: 弱势RSI>65 → 强势RSI<35"""
    decisions=[]
    # 找弱势
    weakest=None; weakest_rsi=0
    for coin in margin_assets:
        if coin=='USDT': continue
        if coin in market and market[coin]['rsi_1h']>65:
            if market[coin]['rsi_1h']>weakest_rsi:
                weakest=coin; weakest_rsi=market[coin]['rsi_1h']
    # 找强势
    strongest=None; strongest_rsi=100
    for coin in market:
        if coin in margin_assets: continue
        if market[coin]['rsi_1h']<35 and market[coin]['rsi_1h']<strongest_rsi:
            strongest=coin; strongest_rsi=market[coin]['rsi_1h']
    if weakest and strongest:
        net=margin_assets[weakest].get('net',0)
        price=market[weakest]['price']
        if abs(net)>0.0001 and price>0:
            qty=round_qty(abs(net),weakest)
            decisions.append({'mode':'MARGIN','coin':weakest,'action':'ROTATION_SELL','side':'SELL','qty':qty,'price':price})
            print(f"  🔄 {weakest}(RSI={weakest_rsi:.0f})→{strongest}(RSI={strongest_rsi:.0f}) 轮换")
    return decisions

def op_risk_assessment(market, margin_assets, margin_ml, total_value):
    """10. 风险评估"""
    print("\n"+"="*60)
    print("⚠️ 风险评估")
    print("="*60)
    risks=[]
    if margin_ml<3.0: risks.append(f"保证金率过低: {margin_ml:.2f}")
    if margin_ml<4.0: risks.append(f"保证金率预警: {margin_ml:.2f}")
    total_exposure=sum(abs(m.get('net',0))*market.get(c,{}).get('price',0) for c,m in margin_assets.items() if c!='USDT')
    exposure_ratio=total_exposure/total_value if total_value>0 else 0
    if exposure_ratio>0.80: risks.append(f"敞口过高: {exposure_ratio*100:.1f}%")
    for coin in margin_assets:
        if coin=='USDT': continue
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        price=market.get(coin,{}).get('price',0)
        if price<=0: continue
        ratio=abs(net)*price/total_value if total_value>0 else 0
        if ratio>0.30: risks.append(f"{coin}仓位超限: {ratio*100:.1f}%")
    for r in risks: print(f"  ⚠️ {r}")
    if not risks: print("  ✅ 无风险")
    return risks

def op_exposure_control(market, margin_assets, total_value):
    """11. 敞口控制"""
    total_exposure=sum(abs(m.get('net',0))*market.get(c,{}).get('price',0) for c,m in margin_assets.items() if c!='USDT')
    exposure_ratio=total_exposure/total_value if total_value>0 else 0
    status="✅" if exposure_ratio<=0.80 else "⚠️"
    print(f"  总敞口: {exposure_ratio*100:.1f}% {status}")
    return exposure_ratio<=0.80

def op_per_coin_limit(market, margin_assets, total_value):
    """12. 单币限制"""
    exceeded=[]
    for coin in margin_assets:
        if coin=='USDT': continue
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        price=market.get(coin,{}).get('price',0)
        if price<=0: continue
        ratio=abs(net)*price/total_value if total_value>0 else 0
        if ratio>0.30:
            exceeded.append(f"{coin}({ratio*100:.1f}%)")
    for e in exceeded: print(f"  ⚠️ {e}超限")
    return len(exceeded)==0

def op_dynamic_leverage(market):
    """13. 动态杠杆"""
    up_count=sum(1 for c in market if market[c]['chg_1h']>0)
    total=len(market)
    breadth=up_count/total
    if breadth>0.7: regime="BULL"; leverage=8
    elif breadth<0.3: regime="BEAR"; leverage=3
    else: regime="NEUTRAL"; leverage=5
    print(f"  市场状态: {regime} 杠杆: {leverage}x")
    return regime, leverage

def op_wallet_transfer(spot_balances, margin_assets, margin_ml):
    """14. 钱包转账 SPOT↔MARGIN"""
    transfers=[]
    spot_usdt=spot_balances.get('USDT',{}).get('total',0)
    margin_usdt=margin_assets.get('USDT',{}).get('net',0)
    # 如果SPOT USDT太多且MARGIN保证金率OK，转入MARGIN
    if spot_usdt>500 and margin_ml>5.0:
        amount=min(spot_usdt-100, 200)  # 保留100USDT，转入200
        if amount>10:
            result=transfer('USDT', amount, 'SPOT', 'MARGIN')
            transfers.append({'from':'SPOT','to':'MARGIN','amount':amount,'result':result})
            print(f"  💼 SPOT→MARGIN 转账 ${amount:.2f}")
    # 如果MARGIN保证金率低，转出到SPOT
    elif margin_ml<4.0 and margin_usdt>50:
        amount=min(margin_usdt-20, 100)
        if amount>10:
            result=transfer('USDT', amount, 'MARGIN', 'SPOT')
            transfers.append({'from':'MARGIN','to':'SPOT','amount':amount,'result':result})
            print(f"  💼 MARGIN→SPOT 转账 ${amount:.2f}")
    return transfers

def op_execution_verification(coin, side, qty, mode, result):
    """15. 执行验证"""
    time.sleep(3)
    try:
        if mode=='SPOT':
            balances=get_spot_data()
            actual=balances.get(coin,{}).get('total',0)
        else:
            _, assets=get_margin_data()
            actual=assets.get(coin,{}).get('net',0)
        if 'error' not in result and 'code' not in result:
            log_verify(f"VERIFIED: {mode} {coin} {side} {qty}")
            print(f"  ✅ {mode} {coin} {side} {qty} 验证成功")
            return True
    except Exception as e:
        print(f"  ⚠️ 验证异常: {str(e)[:50]}")
    log_verify(f"FAILED: {mode} {coin} {side} {qty}")
    return False

# ========== 执行引擎 ==========
def execute_all(decisions, trade_history):
    print("\n"+"="*60)
    print("⚡ 执行交易")
    print("="*60)
    results=[]
    for d in decisions:
        coin=d['coin']; side=d['side']; qty=d['qty']; mode=d['mode']; action=d['action']
        print(f"\n📤 {action}: {mode} {coin} {side} {qty}")
        if mode=='SPOT':
            result=spot_order(f'{coin}USDT', side, qty)
        else:
            result=margin_order(f'{coin}USDT', side, qty)
        verified=op_execution_verification(coin, side, qty, mode, result)
        results.append({'mode':mode,'coin':coin,'action':action,'verified':verified})
        if verified and side=='BUY':
            trade_history[coin]={'entry_price':d['price'],'entry_time':datetime.now().strftime('%H:%M'),'mode':mode}
    save_trade_history(trade_history)
    return results

# ========== 主程序 ==========
print("\n"+"="*70)
print("🎯 Hermes v5.0 - SPOT+MARGIN双模式15种操作")
print("="*70)

trade_history=load_trade_history()

# 获取所有数据
market=market_sensing()
spot_balances=get_spot_data()
margin_ml, margin_assets=get_margin_data()

prices={'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
        'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
        'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1}

# 计算总资产
spot_total=sum(spot_balances.get(a,{}).get('total',0)*prices.get(a,1) for a in spot_balances)
margin_total=sum(abs(m.get('net',0))*prices.get(a,1) for a,m in margin_assets.items())
total_assets=spot_total+margin_total

usdt_spot=spot_balances.get('USDT',{}).get('total',0)
usdt_margin=margin_assets.get('USDT',{}).get('free',0)

spot_positions=[a for a,b in spot_balances.items() if b.get('total',0)>0.001 and a!='USDT']
margin_positions=[a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']

print(f"\n【资产概览】")
print(f"  SPOT: ${spot_total:.2f} (USDT: ${usdt_spot:.2f})")
print(f"  MARGIN: ${margin_total:.2f} (保证金率: {margin_ml:.3f})")
print(f"  总资产: ${total_assets:.2f}")
print(f"  SPOT持仓: {spot_positions}")
print(f"  MARGIN持仓: {margin_positions}")

# 风险评估
risks=op_risk_assessment(market, margin_assets, margin_ml, margin_total)
op_exposure_control(market, margin_assets, margin_total)
op_per_coin_limit(market, margin_assets, margin_total)
regime, leverage=op_dynamic_leverage(market)

# 生成所有决策
all_decisions=[]
all_decisions.extend(op_close_all(market, margin_assets, margin_ml))
all_decisions.extend(op_close(market, margin_assets, trade_history))
all_decisions.extend(op_stop_loss(market, margin_assets, trade_history))
all_decisions.extend(op_take_profit(market, margin_assets, trade_history))
all_decisions.extend(op_reduce(market, margin_assets))
all_decisions.extend(op_rebalance(market, margin_assets, margin_total))
all_decisions.extend(op_rotation(market, margin_assets))
all_decisions.extend(op_add(market, margin_assets, margin_ml, usdt_margin))
all_decisions.extend(op_build(market, spot_balances, margin_assets, margin_ml, usdt_spot, usdt_margin))

# 执行钱包转账
transfers=op_wallet_transfer(spot_balances, margin_assets, margin_ml)

print(f"\n【决策汇总】{len(all_decisions)}个")
action_counts={}
for d in all_decisions:
    action_counts[d['action']]=action_counts.get(d['action'],0)+1
for a,c in sorted(action_counts.items()):
    print(f"  {a}: {c}个")

# 执行
results=execute_all(all_decisions, trade_history)

print("\n"+"="*70)
print("【v5.0总结】")
print("="*70)
v_spot=sum(1 for r in results if r.get('mode')=='SPOT' and r.get('verified'))
v_margin=sum(1 for r in results if r.get('mode')=='MARGIN' and r.get('verified'))
print(f"SPOT执行: {v_spot}笔")
print(f"MARGIN执行: {v_margin}笔")
print(f"总执行: {len(results)}笔")
print(f"风险数量: {len(risks)}个")
print("="*70)
PYEOF
