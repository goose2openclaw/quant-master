#!/bin/bash
LOG_FILE="/tmp/hermes_v321.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "Hermes v3.2.1 $(date)"
echo "=========================================="
python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION={'BTC':6,'ETH':5,'BNB':5,'SOL':5,'XRP':0,'ADA':0,'DOGE':0,'LINK':2}
TRADE_HISTORY_FILE='/tmp/hermes_trade_history.json'

CONFIG={
    'margin_min':3.0,'margin_warn':3.3,'position':0.25,'leverage':5,
    'min_notional':10,'position_max':0.35,
    'rsi_short':71,'rsi_long':32,'tp':0.08,'sl':0.015,
    'proactivity':0.90,
    'build_enabled':True,'build_rsi_threshold':32,
    'add_enabled':True,'add_rsi_threshold':35,
    'stop_loss_enabled':True,'stop_loss_rsi':80,'stop_loss_profit':-0.03,
    'take_profit_enabled':True,'take_profit_rsi':75,'take_profit_profit':0.08,
    'close_position_enabled':True,
    'rebalance_enabled':True,
    'max_per_coin':0.30,
    'verify_after_order':True,'verify_retry':3,'verify_timeout':5,
}

def get_price(sym):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(symbol, interval='1m', limit=10):
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

def get_trend(klines):
    if not klines or len(klines)<2: return "N/A", 0
    change=(klines[-1][2]-klines[0][2])/klines[0][2]*100
    if change>1: trend="📈强势"
    elif change>0.3: trend="📊上涨"
    elif change>-0.3: trend="➡️震荡"
    elif change>-1: trend="📉下跌"
    else: trend="📉强势"
    return trend, change

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
        if abs(net)>0.0001 or borrowed>0.0001:
            assets[a['asset']]={'free':free,'borrowed':borrowed,'net':net}
    return ml, assets

def place_order(symbol, side, quantity):
    ts=int(time.time()*1000)
    params={'symbol':symbol,'side':side,'type':'MARKET','quantity':quantity,'timestamp':ts,'recvWindow':5000}
    query_string='&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig=hmac.new(API_SECRET.encode(),query_string.encode(),hashlib.sha256).hexdigest()
    url=f"https://api.binance.com/sapi/v1/margin/order?{query_string}&signature={sig}"
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

def verify_order(coin, side, expected_qty, result):
    print(f"\n🔍 验证: {coin} {side} {expected_qty}")
    time.sleep(CONFIG['verify_timeout'])
    for attempt in range(CONFIG['verify_retry']):
        try:
            ml, assets = get_margin_data()
            actual = assets.get(coin, {}).get('net', 0)
            if side == 'BUY' and actual > 0:
                print(f"  ✅ 成功")
                return True
            elif side == 'SELL' and actual >= 0:
                print(f"  ✅ 成功")
                return True
        except: pass
        time.sleep(2)
    print(f"  ❌ 失败")
    return False

def verify_margin():
    try:
        ml, _ = get_margin_data()
        print(f"\n🔍 保证金率: {ml:.3f} {'✅' if ml>CONFIG['margin_min'] else '❌'}")
        return ml > CONFIG['margin_min']
    except: return False

def market_sensing():
    print("\n"+"="*60)
    print("🔍 积极觉察 - 市场扫描 v3.2.1")
    print("="*60)
    coins=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']
    market={}; up_count=0
    for coin in coins:
        sym=f"{coin}USDT"; price=get_price(sym)
        k1h=get_klines(sym,'1h',60)
        if k1h:
            rsi=calc_rsi([k[2] for k in k1h])
            trend,chg=get_trend(k1h[-30:]) if len(k1h)>=30 else ("N/A",0)
            if chg>0: up_count+=1
            signal="✅" if (rsi<35 or rsi>75) else "⚪"
            market[coin]={'price':price,'rsi':rsi,'chg':chg,'trend':trend}
            print(f"  {coin}: ${price:.4f} RSI={rsi:.0f} {chg:+.1f}% {signal}")
    regime="BULL" if up_count/len(coins)>0.7 else "BEAR" if up_count/len(coins)<0.3 else "NEUTRAL"
    print(f"\n  广度: {up_count}/{len(coins)}上涨 | {regime}")
    return market, regime

def decisions(market, margin_assets, margin_ml, total_value, usdt_balance, positions, trade_history):
    all_dec=[]
    
    for coin in positions:
        if coin not in market: continue
        rsi=market[coin]['rsi']; price=market[coin]['price']
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        
        # 加仓: RSI<35
        if rsi<CONFIG['add_rsi_threshold'] and margin_ml>=CONFIG['margin_warn']:
            current_value=abs(net)*price
            current_ratio=current_value/total_value if total_value>0 else 0
            if current_ratio<CONFIG['position_max']:
                qty=round_qty((usdt_balance*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
                if price*qty>=CONFIG['min_notional']:
                    all_dec.append({'coin':coin,'action':'ADD','side':'BUY','qty':qty,'price':price,'rsi':rsi})
                    print(f"  📈 {coin}: RSI={rsi:.0f} 加仓 BUY {qty}")
        
        # 止损: RSI>80或亏损>3%
        entry=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=CONFIG['stop_loss_rsi'] or profit<=CONFIG['stop_loss_profit']:
            qty=round_qty(abs(net),coin)
            all_dec.append({'coin':coin,'action':'STOP_LOSS','side':'SELL','qty':qty,'price':price,'rsi':rsi})
            print(f"  🛡️ {coin}: RSI={rsi:.0f} 盈亏{profit*100:+.1f}% 止损 SELL")
        
        # 止盈: RSI>75或盈利>8%
        if rsi>=CONFIG['take_profit_rsi'] or profit>=CONFIG['take_profit_profit']:
            qty=round_qty(abs(net)*0.5,coin)
            all_dec.append({'coin':coin,'action':'TAKE_PROFIT','side':'SELL','qty':qty,'price':price,'rsi':rsi})
            print(f"  💰 {coin}: RSI={rsi:.0f} 盈亏{profit*100:+.1f}% 止盈50% SELL")
    
    # 建仓: 新币 RSI<32
    for coin in market:
        if coin in positions: continue
        rsi=market[coin]['rsi']; price=market[coin]['price']
        if rsi<CONFIG['build_rsi_threshold'] and margin_ml>=CONFIG['margin_warn'] and price>0:
            qty=round_qty((usdt_balance*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
            if price*qty>=CONFIG['min_notional']:
                all_dec.append({'coin':coin,'action':'BUILD','side':'BUY','qty':qty,'price':price,'rsi':rsi})
                print(f"  🏗️ {coin}: RSI={rsi:.0f} 建仓 BUY {qty}")
    
    return all_dec

def execute_all(all_dec, trade_history):
    print("\n"+"="*60)
    print("⚡ 执行交易")
    print("="*60)
    results=[]
    for d in all_dec:
        coin=d['coin']; action=d['action']; side=d['side']; qty=d['qty']
        print(f"\n📤 {action}: {coin} {side} {qty}")
        result=place_order(f'{coin}USDT', side, qty)
        verified=False
        if 'error' not in result and 'code' not in result:
            verified=verify_order(coin, side, qty, result)
            if verified and side=='BUY':
                trade_history[coin]={'entry_price':d['price'],'entry_time':datetime.now().strftime('%H:%M')}
        results.append({'coin':coin,'action':action,'verified':verified})
    save_trade_history(trade_history)
    return results

trade_history=load_trade_history()
market, regime=market_sensing()

margin_ml, margin_assets=get_margin_data()
prices={'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
        'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
        'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1}
margin_total=sum(abs(m.get('net',0))*prices.get(a,1) for a,m in margin_assets.items())
borrow=margin_assets.get('USDT',{}).get('borrowed',0)
usdt_balance=margin_assets.get('USDT',{}).get('free',0)
positions=[a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']

print(f"\n【资产】保证金率:{margin_ml:.3f} USDT:${usdt_balance:.2f} MARGIN:${margin_total:.2f}")
print(f"【持仓】{len(positions)}个 {positions}")

all_dec=decisions(market, margin_assets, margin_ml, margin_total, usdt_balance, positions, trade_history)
print(f"\n【决策汇总】{len(all_dec)}个")
results=execute_all(all_dec, trade_history)
verify_margin()

print("\n"+"="*60)
print("【v3.2.1总结】")
print("="*60)
v=sum(1 for r in results if r.get('verified',False))
print(f"执行:{len(results)}笔 成功:{v}笔 市场:{regime}")
PYEOF
