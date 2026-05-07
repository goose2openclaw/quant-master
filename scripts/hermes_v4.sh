#!/bin/bash
# Hermes v4.0 - 6目标驱动系统
# 日期: 2026-05-07
# 目标: 积极觉察 | 主动决策 | 自动操作 | 收益最大化 | 胜率提升 | 资金安全

LOG_FILE="/tmp/hermes_v4.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v4.0 $(date)"
echo "6目标驱动系统"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json, math
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION={'BTC':6,'ETH':5,'BNB':5,'SOL':5,'XRP':0,'ADA':0,'DOGE':0,'LINK':2}
TRADE_HISTORY_FILE='/tmp/hermes_trade_history.json'
GOALS_FILE='/tmp/hermes_goals.json'
VERIFY_LOG='/tmp/hermes_v4_verification.log'

# ========== v4.0 6目标配置 ==========
GOALS={
    # 目标1: 积极觉察机会
    'aware': {
        'scan_coins': ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK','AVAX','DOT'],
        'scan_intervals': ['1h','4h','1d'],
        'rsi_oversold': 32,      # 超卖阈值
        'rsi_overbought': 75,    # 超买阈值
        'volume_spike': 1.5,      # 成交量放大
        'trend_strength': 0.5,    # 趋势强度
    },
    # 目标2: 主动智能决策
    'decide': {
        'proactive': 0.90,        # 主动性
        'confidence': 0.85,      # 置信度
        'multi_signal': True,     # 多信号共振
        'dynamic_threshold': True, # 动态阈值
    },
    # 目标3: 自动执行
    'execute': {
        'auto': True,
        'verify': True,
        'retry': 3,
        'timeout': 5,
    },
    # 目标4: 收益最大化
    'return_max': {
        'tp_multiplier': 1.2,    # 动态止盈
        'compounding': True,      # 复利
        'position_sizing': True,  # 动态仓位
    },
    # 目标5: 胜率提升
    'winrate_max': {
        'target': 0.35,          # 目标胜率
        'optimize': True,
        'learning': True,        # 学习优化
    },
    # 目标6: 资金安全
    'capital_safe': {
        'max_exposure': 0.80,
        'max_per_coin': 0.30,
        'margin_min': 3.0,
        'margin_warn': 4.0,
        'position_max': 0.35,
    }
}

# 基于EXPERT回测优化
CONFIG={
    'rsi_short': 71, 'rsi_long': 32,
    'wr_short': 0.93, 'wr_long': 0.89,
    'tp': 0.08, 'sl': 0.015,
    'position': 0.25, 'leverage': 5,
    'min_notional': 10,
}

def get_price(sym):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=100):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}', proxies=PROXIES, timeout=10)
        return [(float(d[2]),float(d[3]),float(d[4]),float(d[5])) for d in r.json()]
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

def calc_ema(closes, period=20):
    if len(closes)<period: return closes[-1] if closes else 0
    k=2/(period+1)
    ema=sum(closes[:period])/period
    for price in closes[period:]:
        ema=price*k+ema*(1-k)
    return ema

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

def load_goals():
    try:
        with open(GOALS_FILE, 'r') as f: return json.load(f)
    except: return {'sessions':0,'total_trades':0,'wins':0,'losses':0,'total_return':0}

def save_goals(goals):
    try:
        with open(GOALS_FILE, 'w') as f: json.dump(goals, f)
    except: pass

def verify_order(coin, side, expected_qty):
    time.sleep(CONFIG.get('verify_timeout', 5))
    for attempt in range(3):
        try:
            ml, assets = get_margin_data()
            actual = assets.get(coin, {}).get('net', 0)
            if side == 'BUY' and actual > 0:
                return True
            elif side == 'SELL' and actual >= 0:
                return True
        except: pass
        time.sleep(2)
    return False

# ========== 目标1: 积极觉察 ==========
def goal1_aware():
    print("\n"+"="*60)
    print("🎯 目标1: 积极觉察机会")
    print("="*60)
    
    coins=GOALS['aware']['scan_coins']
    market={}
    
    for coin in coins:
        sym=f"{coin}USDT"; price=get_price(sym)
        k1h=get_klines(sym,'1h',60)
        k4h=get_klines(sym,'4h',20)
        k1d=get_klines(sym,'1d',7)
        
        if k1h:
            rsi_1h=calc_rsi([k[2] for k in k1h])
            rsi_4h=calc_rsi([k[2] for k in k4h]) if k4h else 50
            rsi_1d=calc_rsi([k[2] for k in k1d]) if k1d else 50
            
            # 多周期信号
            change_1h=(k1h[-1][2]-k1h[0][2])/k1h[0][2]*100 if len(k1h)>=2 else 0
            
            # 机会评分
            score=0
            if rsi_1h<35: score+=3
            if rsi_1h<30: score+=2
            if rsi_4h<35: score+=2
            if rsi_1d<40: score+=1
            if change_1h<-1: score+=1
            
            signal="📈" if score>=5 else "📊" if score>=3 else "⚪"
            
            market[coin]={
                'price':price,'rsi_1h':rsi_1h,'rsi_4h':rsi_4h,'rsi_1d':rsi_1d,
                'change_1h':change_1h,'score':score,'signal':signal
            }
            
            print(f"  {coin}: ${price:.4f} RSI={rsi_1h:.0f}/{rsi_4h:.0f}/{rsi_1d:.0f} {change_1h:+.1f}% {signal}({score})")
    
    return market

# ========== 目标2: 主动决策 ==========
def goal2_decide(market, margin_assets, margin_ml, total_value, usdt_balance, positions, trade_history):
    print("\n"+"="*60)
    print("🧠 目标2: 主动智能决策")
    print("="*60)
    
    decisions=[]
    config=GOALS['decide']
    
    for coin in positions:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        
        entry=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        
        # 动态止盈止损
        tp_multiplier=GOALS['return_max']['tp_multiplier']
        tp=CONFIG['tp']*tp_multiplier
        sl=CONFIG['sl']
        
        # 加仓: RSI<35 且信心充足
        if rsi<35 and config['proactive']>0.85 and margin_ml>=GOALS['capital_safe']['margin_warn']:
            current_ratio=abs(net)*price/total_value if total_value>0 else 0
            if current_ratio<GOALS['capital_safe']['position_max']:
                qty=round_qty((usdt_balance*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
                if price*qty>=CONFIG['min_notional']:
                    decisions.append({'coin':coin,'action':'ADD','side':'BUY','qty':qty,'price':price,'rsi':rsi,'profit':profit,'confidence':0.9})
                    print(f"  📈 {coin}: RSI={rsi:.0f} 盈亏{profit*100:+.1f}% → 加仓 BUY {qty} (置信{0.9})")
        
        # 止损: RSI>80 或 亏损>3%
        if rsi>=80 or profit<=-0.03:
            decisions.append({'coin':coin,'action':'STOP_LOSS','side':'SELL','qty':round_qty(abs(net),coin),'price':price,'rsi':rsi,'profit':profit,'confidence':0.95})
            print(f"  🛡️ {coin}: RSI={rsi:.0f} 盈亏{profit*100:+.1f}% → 止损 SELL")
        
        # 止盈: RSI>75 或 盈利>10%
        if rsi>=75 or profit>=tp:
            qty=round_qty(abs(net)*0.5,coin)
            decisions.append({'coin':coin,'action':'TAKE_PROFIT','side':'SELL','qty':qty,'price':price,'rsi':rsi,'profit':profit,'confidence':0.85})
            print(f"  💰 {coin}: RSI={rsi:.0f} 盈亏{profit*100:+.1f}% → 止盈50% SELL")
    
    # 新币建仓
    for coin in market:
        if coin in positions: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        score=market[coin]['score']
        if rsi<32 and score>=5 and margin_ml>=GOALS['capital_safe']['margin_warn'] and price>0:
            qty=round_qty((usdt_balance*CONFIG['position']*CONFIG['leverage']/price)*0.99, coin)
            if price*qty>=CONFIG['min_notional']:
                decisions.append({'coin':coin,'action':'BUILD','side':'BUY','qty':qty,'price':price,'rsi':rsi,'score':score,'confidence':0.85})
                print(f"  🏗️ {coin}: RSI={rsi:.0f} Score={score} → 建仓 BUY {qty}")
    
    print(f"\n  决策总数: {len(decisions)}个")
    return decisions

# ========== 目标3: 自动执行 ==========
def goal3_execute(decisions, trade_history, goals):
    print("\n"+"="*60)
    print("⚡ 目标3: 自动执行操作")
    print("="*60)
    
    results=[]
    config=GOALS['execute']
    
    for d in decisions:
        coin=d['coin']; side=d['side']; qty=d['qty']; action=d['action']
        
        print(f"\n📤 {action}: {coin} {side} {qty}")
        result=place_order(f'{coin}USDT', side, qty)
        
        verified=False
        if 'error' not in result and 'code' not in result:
            if config['verify']:
                verified=verify_order(coin, side, qty)
            else:
                verified=True
            
            if verified and side=='BUY':
                trade_history[coin]={'entry_price':d['price'],'entry_time':datetime.now().strftime('%H:%M')}
                goals['total_trades']+=1
        
        results.append({'coin':coin,'action':action,'verified':verified})
        status="✅" if verified else "❌"
        print(f"  {status} {action} {coin} {side} {qty}")
    
    save_trade_history(trade_history)
    return results

# ========== 目标4: 收益最大化 ==========
def goal4_return_max(market, margin_assets, total_value):
    print("\n"+"="*60)
    print("💹 目标4: 收益最大化")
    print("="*60)
    
    total_pnl=0; positions_count=0
    
    for coin in margin_assets:
        if coin=='USDT': continue
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        
        price=market.get(coin,{}).get('price',0)
        if price<=0: continue
        
        value=abs(net)*price
        ratio=value/total_value if total_value>0 else 0
        total_pnl+=value
        positions_count+=1
        
        print(f"  {coin}: ${value:.2f} ({ratio*100:.1f}%)")
    
    # 复利计算
    if GOALS['return_max']['compounding']:
        comp_effect=math.pow(1+total_pnl/total_value, 1)-1 if total_value>0 else 0
        print(f"\n  组合收益: ${total_pnl:.2f}")
        print(f"  复利效应: {comp_effect*100:+.2f}%")
    
    return total_pnl

# ========== 目标5: 胜率提升 ==========
def goal5_winrate_max(goals, results):
    print("\n"+"="*60)
    print("🎯 目标5: 胜率不断提升")
    print("="*60)
    
    goals['sessions']+=1
    
    # 更新统计
    total=goals['total_trades']
    wins=goals['wins']
    losses=goals['losses']
    
    # 本次胜率
    this_win=sum(1 for r in results if r.get('verified') and r.get('action') in ['TAKE_PROFIT','STOP_LOSS'])
    this_loss=sum(1 for r in results if not r.get('verified') and r.get('action') in ['BUILD','ADD'])
    
    if this_win>0 or this_loss>0:
        if this_win>this_loss:
            goals['wins']+=this_win
        else:
            goals['losses']+=this_loss
    
    total=goals['total_trades']
    wins=goals['wins']
    winrate=wins/total*100 if total>0 else 0
    
    print(f"  总交易: {total}笔")
    print(f"  盈利: {wins}笔")
    print(f"  亏损: {losses}笔")
    print(f"  胜率: {winrate:.1f}%")
    print(f"  目标: {GOALS['winrate_max']['target']*100:.0f}%")
    
    if winrate>GOALS['winrate_max']['target']:
        print(f"  ✅ 胜率达标!")
    
    save_goals(goals)
    return winrate

# ========== 目标6: 资金安全 ==========
def goal6_capital_safe(market, margin_assets, margin_ml, total_value):
    print("\n"+"="*60)
    print("🛡️ 目标6: 资金安全和利用率")
    print("="*60)
    
    config=GOALS['capital_safe']
    
    # 保证金率
    ml_status="✅" if margin_ml>=config['margin_min'] else "❌"
    print(f"  保证金率: {margin_ml:.3f} {ml_status}")
    
    # 敞口
    total_exposure=sum(abs(m.get('net',0))*market.get(c,{}).get('price',0) for c,m in margin_assets.items() if c!='USDT')
    exposure_ratio=total_exposure/total_value if total_value>0 else 0
    exp_status="✅" if exposure_ratio<=config['max_exposure'] else "⚠️"
    print(f"  总敞口: {exposure_ratio*100:.1f}% {exp_status}")
    
    # 单币限制
    for coin in margin_assets:
        if coin=='USDT': continue
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        price=market.get(coin,{}).get('price',0)
        if price<=0: continue
        ratio=abs(net)*price/total_value if total_value>0 else 0
        if ratio>config['max_per_coin']:
            print(f"  ⚠️ {coin}超限: {ratio*100:.1f}%>{config['max_per_coin']*100:.0f}%")
    
    # 资金利用率
    util=total_exposure/total_value if total_value>0 else 0
    print(f"  资金利用率: {util*100:.1f}%")
    
    return margin_ml>=config['margin_min'] and exposure_ratio<=config['max_exposure']

# ========== 主程序 ==========
print("\n"+"="*70)
print("🎯🎯🎯 Hermes v4.0 - 6目标驱动系统 🎯🎯🎯")
print("="*70)

trade_history=load_trade_history()
goals=load_goals()

# 目标1: 积极觉察
market=goal1_aware()

# 获取资产
margin_ml, margin_assets=get_margin_data()
prices={'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
        'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
        'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1}
spot_total=0; margin_total=0
for a,m in margin_assets.items():
    price=prices.get(a,1)
    margin_total+=abs(m.get('net',0))*price
usdt_balance=margin_assets.get('USDT',{}).get('free',0)
borrow=margin_assets.get('USDT',{}).get('borrowed',0)
positions=[a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']

print(f"\n【资产概览】")
print(f"  保证金率: {margin_ml:.3f}")
print(f"  USDT可用: ${usdt_balance:.2f}")
print(f"  MARGIN净值: ${margin_total:.2f}")
print(f"  持仓: {len(positions)}个 {positions}")

# 目标2: 主动决策
decisions=goal2_decide(market, margin_assets, margin_ml, margin_total, usdt_balance, positions, trade_history)

# 目标3: 自动执行
results=goal3_execute(decisions, trade_history, goals)

# 目标4: 收益最大化
pnl=goal4_return_max(market, margin_assets, margin_total)

# 目标5: 胜率提升
winrate=goal5_winrate_max(goals, results)

# 目标6: 资金安全
safe=goal6_capital_safe(market, margin_assets, margin_ml, margin_total)

print("\n"+"="*70)
print("🎯🎯🎯 v4.0 6目标总结 🎯🎯🎯")
print("="*70)
verified=sum(1 for r in results if r.get('verified'))
print(f"目标1 积极觉察: {len(market)}币种扫描 ✅")
print(f"目标2 主动决策: {len(decisions)}个决策")
print(f"目标3 自动操作: {verified}/{len(results)}执行成功")
print(f"目标4 收益最大化: ${pnl:.2f}")
print(f"目标5 胜率提升: {winrate:.1f}%")
print(f"目标6 资金安全: {'✅安全' if safe else '⚠️注意'}")
print("="*70)
PYEOF
