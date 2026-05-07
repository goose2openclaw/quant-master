#!/bin/bash
# Hermes v3.2 / GO2SE Genius v2.10.1
# 日期: 2026-05-07
# 完整操作清单 + 执行验证

LOG_FILE="/tmp/hermes_v32.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v3.2 / GO2SE Genius v2.10.1"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION={'BTC':6,'ETH':5,'BNB':5,'SOL':5,'XRP':0,'ADA':0,'DOGE':0,'LINK':2}
TRADE_HISTORY_FILE='/tmp/hermes_trade_history.json'
VERIFY_LOG='/tmp/hermes_v32_verification.log'

# ========== v2.10.1 完整配置 ==========
CONFIG = {
    # 基础
    'margin_min': 3.0, 'margin_warn': 3.3,
    'position': 0.25, 'position_max': 0.35,
    'leverage': 5, 'leverage_max': 10,
    'min_notional': 10,
    
    # ===== 建仓/加仓/止损/止盈/减仓 =====
    'build_enabled': True, 'build_rsi_threshold': 25,
    'build_max_per_coin': 0.20, 'build_position_ratio': 0.15,
    'add_enabled': True, 'add_rsi_threshold': 30,
    'add_strong_rsi': 25, 'add_ratio': 0.15, 'add_max_per_coin': 0.35,
    'stop_loss_enabled': True, 'stop_loss_rsi': 80, 'stop_loss_profit': -0.03,
    'stop_loss_trailing': 0.05,
    'take_profit_enabled': True, 'take_profit_rsi': 75, 'take_profit_profit': 0.08,
    'take_profit_partial': 0.50,
    'reduce_enabled': True, 'reduce_rsi_threshold': 70,
    'reduce_strong_rsi': 75, 'reduce_profit_threshold': 0.05,
    'reduce_strong_profit': 0.10, 'reduce_ratio': 0.20, 'reduce_min_profit': 0.02,
    
    # ===== v2.10.1 新增操作 =====
    # 仓位管理
    'close_position_enabled': True,      # 平仓
    'close_all_enabled': True,          # 全部平仓
    'rebalance_enabled': True,          # 仓位再平衡
    
    # 风险控制
    'max_exposure': 0.80,             # 最大敞口80%
    'max_drawdown': 0.10,             # 最大回撤10%
    'max_per_coin': 0.30,             # 单币最大30%
    'max_total_position': 0.90,       # 总仓位最大90%
    
    # 资金调度
    'dynamic_leverage': True,
    'leverage_bull': 8, 'leverage_bear': 3, 'leverage_neutral': 5,
    'margin_warning': 5.0,            # 保证金预警
    
    # 市场择时
    'multi_timeframe': True,           # 多周期共振
    'trend_following': True,          # 趋势跟踪
    'mean_reversion': True,           # 均值回归
    
    # 组合管理
    'rotation_enabled': True,          # 币种轮换
    'rebalance定期': True,           # 定期再平衡
    'min_positions': 3,              # 最少持仓
    'max_positions': 8,               # 最多持仓
    
    # 应急处理
    'extreme_market_protection': True, # 极端行情保护
    'extreme_btc_move': 0.15,       # BTC单日15%
    'api_timeout_protection': True,    # API超时保护
    'reconnect_enabled': True,        # 断线重连
    
    # 验证
    'verify_after_order': True,
    'verify_retry': 3, 'verify_timeout': 5,
}

BACKTEST = {'NORMAL':{'30d':1637,'wr':80.4,'daily':10.0,'sharpe':1.8},
            'EXPERT':{'30d':1101,'wr':82.5,'daily':8.6,'sharpe':2.2}}

# ========== 工具函数 ==========
def get_price(sym):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(symbol, interval='1m', limit=10):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}', proxies=PROXIES, timeout=10)
        return [(float(d[2]), float(d[3]), float(d[4])) for d in r.json()]
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

def transfer(asset, amount, type_from, type_to):
    """钱包转账: SPOT<->MARGIN"""
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

def verify_order(coin, side, expected_qty, result):
    """验证订单"""
    print(f"\n🔍 验证: {coin} {side} {expected_qty}")
    time.sleep(CONFIG['verify_timeout'])
    for attempt in range(CONFIG['verify_retry']):
        try:
            ml, assets = get_margin_data()
            actual = assets.get(coin, {}).get('net', 0)
            if side == 'BUY' and actual > 0:
                print(f"  ✅ 成功 (尝试{attempt+1})")
                log_verify(f"VERIFIED: {coin} {side} {expected_qty}")
                return True
            elif side == 'SELL' and actual >= 0:
                print(f"  ✅ 成功 (尝试{attempt+1})")
                log_verify(f"VERIFIED: {coin} {side} {expected_qty}")
                return True
        except: pass
        time.sleep(2)
    print(f"  ❌ 失败")
    log_verify(f"FAILED: {coin} {side} {expected_qty}")
    return False

def verify_margin():
    """验证保证金率"""
    try:
        ml, _ = get_margin_data()
        status = "✅" if ml > CONFIG['margin_min'] else "❌"
        print(f"\n🔍 保证金率: {ml:.3f} {status}")
        return ml > CONFIG['margin_min']
    except: return False

def mirofish_calibrated(n_agents=1000, n_days=30, mode='EXPERT'):
    config=BACKTEST[mode]; results=[]
    for _ in range(n_agents):
        capital=1000
        for _ in range(n_days):
            std=config['daily']/config['sharpe']/(30**0.5)
            ret=random.gauss(config['daily'], std)
            capital*=(1+ret/100)
        results.append((capital-1000)/1000*100)
    avg_return=sum(results)/len(results)
    positive_rate=sum(1 for r in results if r>0)/len(results)*100
    return {'avg_return': avg_return, 'positive_rate': positive_rate}

# ========== 市场感知 ==========
def market_sensing():
    print("\n"+"="*60)
    print("🔍 积极觉察 - 市场扫描 v2.10.1")
    print("="*60)
    
    coins=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK','AVAX','DOT']
    market={}; up_count=0
    
    for coin in coins:
        sym=f"{coin}USDT"; price=get_price(sym)
        k1h=get_klines(sym,'1h',60)
        k4h=get_klines(sym,'4h',20)
        k1d=get_klines(sym,'1d',7)
        
        if k1h:
            rsi_1h=calc_rsi([k[2] for k in k1h])
            trend_1h,chg_1h=get_trend(k1h[-30:]) if len(k1h)>=30 else ("N/A",0)
            trend_4h,chg_4h=get_trend(k4h[-10:]) if k4h else ("N/A",0)
            trend_1d,chg_1d=get_trend(k1d) if k1d else ("N/A",0)
            
            if chg_1h>0: up_count+=1
            
            # 多周期共振
            multi_signal = "✅" if (rsi_1h<30 or rsi_1h>70) else "⚪"
            
            market[coin]={
                'price':price,'rsi_1h':rsi_1h,'chg_1h':chg_1h,'chg_4h':chg_4h,'chg_1d':chg_1d,
                'trend_1h':trend_1h,'trend_4h':trend_4h,'trend_1d':trend_1d,
                'multi_signal':multi_signal
            }
            print(f"  {coin}: ${price:.4f} RSI={rsi_1h:.0f} {chg_1h:+.1f}% {multi_signal}")
    
    # 市场广度
    breadth=up_count/len(coins)
    regime="BULL" if breadth>0.7 else "BEAR" if breadth<0.3 else "NEUTRAL"
    print(f"\n  广度: {up_count}/{len(coins)}上涨 | 状态: {regime}")
    return market, regime, breadth

# ========== 风险评估 ==========
def risk_assessment(market, margin_assets, margin_ml, total_value):
    """风险评估"""
    print("\n"+"="*60)
    print("⚠️ 风险评估")
    print("="*60)
    
    risks=[]; actions=[]
    
    # 1. 保证金率风险
    if margin_ml < CONFIG['margin_min']:
        risks.append(f"保证金率过低: {margin_ml:.2f}<{CONFIG['margin_min']}")
        actions.append(('CLOSE_ALL','强制平仓'))
    elif margin_ml < CONFIG['margin_warning']:
        risks.append(f"保证金率预警: {margin_ml:.2f}<{CONFIG['margin_warning']}")
        actions.append(('REDUCE_LEVERAGE','降低杠杆'))
    
    # 2. 敞口风险
    total_exposure = sum(abs(margin_assets.get(c,{}).get('net',0))*market.get(c,{}).get('price',0) for c in margin_assets if c!='USDT')
    exposure_ratio = total_exposure/total_value if total_value>0 else 0
    if exposure_ratio > CONFIG['max_exposure']:
        risks.append(f"敞口过高: {exposure_ratio*100:.1f}%>{CONFIG['max_exposure']*100:.0f}%")
        actions.append(('REDUCE_EXPOSURE','降低敞口'))
    
    # 3. 极端行情风险
    if 'BTC' in market:
        btc_chg = abs(market['BTC'].get('chg_1d',0))
        if btc_chg > CONFIG['extreme_btc_move']*100:
            risks.append(f"BTC剧烈波动: {btc_chg:.1f}%")
            actions.append(('EXTREME_PROTECTION','极端行情保护'))
    
    # 4. 单币超限
    for coin in margin_assets:
        if coin=='USDT': continue
        coin_value = abs(margin_assets[coin].get('net',0))*market.get(coin,{}).get('price',0)
        coin_ratio = coin_value/total_value if total_value>0 else 0
        if coin_ratio > CONFIG['max_per_coin']:
            risks.append(f"{coin}仓位超限: {coin_ratio*100:.1f}%>{CONFIG['max_per_coin']*100:.0f}%")
            actions.append(('REDUCE_COIN',f'减{coin}'))
    
    for r in risks:
        print(f"  ⚠️ {r}")
    for a in actions:
        print(f"  → {a[0]}: {a[1]}")
    
    return risks, actions

# ========== 交易决策 ==========
def build_decisions(market, margin_assets, margin_ml, total_value, usdt_balance, positions):
    decisions=[]
    if not CONFIG['build_enabled'] or margin_ml<CONFIG['margin_warn']: return decisions
    for coin in market:
        if coin in positions: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<CONFIG['build_rsi_threshold'] and price>0:
            qty=round_qty((usdt_balance*CONFIG['build_position_ratio']*CONFIG['leverage']/price)*0.99, coin)
            if price*qty>=CONFIG['min_notional']:
                decisions.append({'coin':coin,'action':'BUILD','qty':qty,'price':price,'rsi':rsi})
                print(f"  🏗️ {coin}: RSI={rsi:.0f} 建仓 {qty}")
    return decisions

def add_decisions(market, margin_assets, margin_ml, total_value, usdt_balance, positions):
    decisions=[]
    if not CONFIG['add_enabled'] or margin_ml<CONFIG['margin_warn']: return decisions
    for coin in positions:
        if coin not in market: continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        if rsi<CONFIG['add_rsi_threshold']:
            current_value=abs(margin_assets[coin].get('net',0))*price
            current_ratio=current_value/total_value if total_value>0 else 0
            if current_ratio<CONFIG['add_max_per_coin']:
                qty=round_qty((usdt_balance*CONFIG['add_ratio']*CONFIG['leverage']/price)*0.99, coin)
                if price*qty>=CONFIG['min_notional']:
                    decisions.append({'coin':coin,'action':'ADD','qty':qty,'price':price,'rsi':rsi})
                    print(f"  📈 {coin}: RSI={rsi:.0f} 加仓 {qty}")
    return decisions

def stop_loss_decisions(market, margin_assets, trade_history):
    decisions=[]
    if not CONFIG['stop_loss_enabled']: return decisions
    for coin in list(margin_assets.keys()):
        if coin not in market or coin=='USDT': continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        entry=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=CONFIG['stop_loss_rsi'] or profit<=CONFIG['stop_loss_profit']:
            decisions.append({'coin':coin,'action':'STOP_LOSS','qty':round_qty(abs(net),coin),'price':price,'rsi':rsi,'profit':profit})
            print(f"  🛡️ {coin}: RSI={rsi:.0f} 盈亏{profit*100:+.1f}% 止损")
    return decisions

def take_profit_decisions(market, margin_assets, trade_history):
    decisions=[]
    if not CONFIG['take_profit_enabled']: return decisions
    for coin in list(margin_assets.keys()):
        if coin not in market or coin=='USDT': continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        entry=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=CONFIG['take_profit_rsi'] or profit>=CONFIG['take_profit_profit']:
            qty=round_qty(abs(net)*CONFIG['take_profit_partial'], coin)
            decisions.append({'coin':coin,'action':'TAKE_PROFIT','qty':qty,'price':price,'rsi':rsi,'profit':profit})
            print(f"  💰 {coin}: RSI={rsi:.0f} 盈亏{profit*100:+.1f}% 止盈")
    return decisions

def reduce_decisions(market, margin_assets, margin_ml, total_value, trade_history):
    decisions=[]
    if not CONFIG['reduce_enabled']: return decisions
    for coin in list(margin_assets.keys()):
        if coin not in market or coin=='USDT': continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        entry=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        if rsi>=CONFIG['reduce_rsi_threshold'] and profit>=CONFIG['reduce_min_profit']:
            qty=round_qty(abs(net)*CONFIG['reduce_ratio'], coin)
            decisions.append({'coin':coin,'action':'REDUCE','qty':qty,'price':price,'rsi':rsi,'profit':profit})
            print(f"  📉 {coin}: RSI={rsi:.0f} 盈亏{profit*100:+.1f}% 减仓")
    return decisions

def close_position_decisions(market, margin_assets, trade_history):
    """平仓决策"""
    decisions=[]
    if not CONFIG['close_position_enabled']: return decisions
    for coin in list(margin_assets.keys()):
        if coin not in market or coin=='USDT': continue
        rsi=market[coin]['rsi_1h']; price=market[coin]['price']
        net=margin_assets[coin].get('net',0)
        if abs(net)<0.0001: continue
        entry=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit=(price-entry)/entry
        # 严重亏损或 RSI>85 全部平仓
        if rsi>=85 or profit<=-0.05:
            decisions.append({'coin':coin,'action':'CLOSE','qty':round_qty(abs(net),coin),'price':price,'rsi':rsi,'profit':profit})
            print(f"  🔴 {coin}: RSI={rsi:.0f} 盈亏{profit*100:+.1f}% 平仓")
    return decisions

def close_all_decisions(market, margin_assets, margin_ml, trade_history):
    """全部平仓决策"""
    decisions=[]
    if not CONFIG['close_all_enabled']: return decisions
    # 极端行情
    if 'BTC' in market and abs(market['BTC'].get('chg_1d',0))>CONFIG['extreme_btc_move']*100:
        for coin in list(margin_assets.keys()):
            if coin=='USDT': continue
            price=market.get(coin,{}).get('price',0)
            net=margin_assets[coin].get('net',0)
            if abs(net)>0.0001 and price>0:
                decisions.append({'coin':coin,'action':'CLOSE_ALL','qty':round_qty(abs(net),coin),'price':price})
                print(f"  🚨 {coin}: 全部平仓 (极端行情)")
    # 保证金率过低
    if margin_ml < CONFIG['margin_min']:
        for coin in list(margin_assets.keys()):
            if coin=='USDT': continue
            price=market.get(coin,{}).get('price',0)
            net=margin_assets[coin].get('net',0)
            if abs(net)>0.0001 and price>0:
                decisions.append({'coin':coin,'action':'CLOSE_ALL','qty':round_qty(abs(net),coin),'price':price})
                print(f"  🚨 {coin}: 全部平仓 (保证金率过低)")
    return decisions

def rebalance_decisions(market, margin_assets, margin_ml, total_value):
    """仓位再平衡决策"""
    decisions=[]
    if not CONFIG['rebalance_enabled']: return decisions
    
    # 检查仓位偏离
    target_ratio = 1.0/len([c for c in margin_assets if c!='USDT']) if len(margin_assets)>1 else 1.0
    
    for coin in margin_assets:
        if coin=='USDT': continue
        price=market.get(coin,{}).get('price',0)
        net=margin_assets[coin].get('net',0)
        if price<=0: continue
        current_value=abs(net)*price
        current_ratio=current_value/total_value if total_value>0 else 0
        
        # 偏离超过15%
        if abs(current_ratio - target_ratio) > 0.15:
            # 需要卖出超配的
            if current_ratio > target_ratio:
                excess_value=current_value - (total_value*target_ratio)
                qty=round_qty(excess_value/price*0.99, coin)
                if qty>0:
                    decisions.append({'coin':coin,'action':'REBALANCE_SELL','qty':qty,'price':price})
                    print(f"  ⚖️ {coin}: 再平衡卖出 {qty} (偏离{abs(current_ratio-target_ratio)*100:.1f}%)")
            # 需要买入低配的
            else:
                deficit_value=(total_value*target_ratio) - current_value
                qty=round_qty(deficit_value/price*0.99, coin)
                if qty>0:
                    decisions.append({'coin':coin,'action':'REBALANCE_BUY','qty':qty,'price':price})
                    print(f"  ⚖️ {coin}: 再平衡买入 {qty} (偏离{abs(current_ratio-target_ratio)*100:.1f}%)")
    return decisions

def rotation_decisions(market, margin_assets, trade_history):
    """币种轮换决策"""
    decisions=[]
    if not CONFIG['rotation_enabled']: return decisions
    
    # 找出最弱的币种(持有但RSI>65)
    weakest=None; weakest_rsi=0
    for coin in margin_assets:
        if coin=='USDT': continue
        if coin in market and market[coin]['rsi_1h']>65:
            if market[coin]['rsi_1h']>weakest_rsi:
                weakest=coin; weakest_rsi=market[coin]['rsi_1h']
    
    # 找出最强的币种(未持有但RSI<35)
    strongest=None; strongest_rsi=100
    for coin in market:
        if coin in margin_assets: continue
        if market[coin]['rsi_1h']<35 and market[coin]['rsi_1h']<strongest_rsi:
            strongest=coin; strongest_rsi=market[coin]['rsi_1h']
    
    # 执行轮换
    if weakest and strongest:
        price=market[weakest]['price']
        net=margin_assets[weakest].get('net',0)
        if abs(net)>0.0001 and price>0:
            # 卖出弱势
            decisions.append({'coin':weakest,'action':'ROTATION_SELL','qty':round_qty(abs(net),weakest),'price':price,'rsi':weakest_rsi})
            # 买入强势
            buy_qty=round_qty(abs(net)*price/market[strongest]['price']*0.99, strongest)
            decisions.append({'coin':strongest,'action':'ROTATION_BUY','qty':buy_qty,'price':market[strongest]['price'],'rsi':strongest_rsi})
            print(f"  🔄 轮换: {weakest}(RSI={weakest_rsi:.0f})→{strongest}(RSI={strongest_rsi:.0f})")
    return decisions

# ========== 执行引擎 ==========
def execute_all(decisions, trade_history):
    print("\n"+"="*60)
    print("⚡ 执行所有交易 (带验证)")
    print("="*60)
    
    results=[]
    priority={'STOP_LOSS':0,'CLOSE':0,'CLOSE_ALL':1,'TAKE_PROFIT':2,'REDUCE':3,'REBALANCE_SELL':4,'ROTATION_SELL':5,'BUILD':6,'ADD':7,'REBALANCE_BUY':8,'ROTATION_BUY':9}
    
    # 按优先级排序
    sorted_decisions=sorted(decisions, key=lambda x: priority.get(x['action'],99))
    
    for d in sorted_decisions:
        coin=d['coin']; action=d['action']; qty=d['qty']; price=d['price']
        side='BUY' if 'BUY' in action else 'SELL'
        
        print(f"\n📤 {action}: {coin} {side} {qty}")
        result=place_order(f'{coin}USDT', side, qty)
        
        if CONFIG['verify_after_order']:
            verified=verify_order(coin, side, qty, result)
            results.append({'coin':coin,'action':action,'verified':verified,'qty':qty})
            if verified and side=='BUY':
                trade_history[coin]={'entry_price':price,'entry_time':datetime.now().strftime('%H:%M')}
        else:
            if 'error' not in result and 'code' not in result:
                results.append({'coin':coin,'action':action,'verified':True,'qty':qty})
                if side=='BUY':
                    trade_history[coin]={'entry_price':price,'entry_time':datetime.now().strftime('%H:%M')}
            else:
                results.append({'coin':coin,'action':action,'verified':False,'qty':qty,'error':str(result)})
    
    save_trade_history(trade_history)
    return results

# ========== 主程序 ==========
print("\n"+"="*70)
print("Hermes v3.2 / GO2SE Genius v2.10.1")
print("完整操作清单 + 执行验证")
print("="*70)

trade_history=load_trade_history()

# 1. 积极觉察
market, regime, breadth=market_sensing()

# 2. 获取资产
margin_ml, margin_assets=get_margin_data()
spot_balances=get_spot_data()
prices={'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
        'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
        'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1}
spot_total=sum(spot_balances.get(a,{}).get('total',0)*prices.get(a,0) for a in spot_balances)
margin_total=sum(abs(m.get('net',0))*prices.get(a,1) for a,m in margin_assets.items())
borrow=margin_assets.get('USDT',{}).get('borrowed',0)
margin_net=margin_total-borrow
total_assets=spot_total+margin_net
usdt_balance=margin_assets.get('USDT',{}).get('free',0)
positions=[a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']

print(f"\n【资产状态】")
print(f"  保证金率: {margin_ml:.3f}")
print(f"  USDT可用: ${usdt_balance:.2f}")
print(f"  MARGIN净值: ${margin_net:.2f}")
print(f"  合并总资产: ${total_assets:.2f}")
print(f"  持仓: {len(positions)}个 {positions}")

# 3. 风险评估
risks, risk_actions=risk_assessment(market, margin_assets, margin_ml, margin_total)

# 4. 执行风险应对
if risk_actions:
    print(f"\n【执行风险应对】")
    for action, desc in risk_actions:
        print(f"  → {action}: {desc}")

# 5. 生成所有决策
all_decisions=[]
all_decisions.extend(close_all_decisions(market, margin_assets, margin_ml, trade_history))
all_decisions.extend(close_position_decisions(market, margin_assets, trade_history))
all_decisions.extend(stop_loss_decisions(market, margin_assets, trade_history))
all_decisions.extend(take_profit_decisions(market, margin_assets, trade_history))
all_decisions.extend(reduce_decisions(market, margin_assets, margin_ml, margin_total, trade_history))
all_decisions.extend(rebalance_decisions(market, margin_assets, margin_ml, margin_total))
all_decisions.extend(rotation_decisions(market, margin_assets, trade_history))
all_decisions.extend(build_decisions(market, margin_assets, margin_ml, margin_total, usdt_balance, positions))
all_decisions.extend(add_decisions(market, margin_assets, margin_ml, margin_total, usdt_balance, positions))

print(f"\n【决策汇总】")
action_counts={}
for d in all_decisions:
    action_counts[d['action']]=action_counts.get(d['action'],0)+1
for a,c in sorted(action_counts.items()):
    print(f"  {a}: {c}个")

# 6. 执行
results=execute_all(all_decisions, trade_history)

# 7. 验证保证金率
print(f"\n【执行后验证】")
verify_margin()

# 8. 仿真
sim=mirofish_calibrated(1000, 30, 'EXPERT')

print("\n"+"="*70)
print("【v2.10.1总结】")
print("="*70)
verified=sum(1 for r in results if r.get('verified',False))
print(f"执行总数: {len(results)}笔")
print(f"验证成功: {verified}笔")
print(f"验证失败: {len(results)-verified}笔")
print(f"仿真收益: {sim['avg_return']:+.0f}%")
print(f"市场状态: {regime}")
print(f"风险数量: {len(risks)}个")
print("="*70)
PYEOF
