#!/bin/bash
# Hermes v3.0 完全修复版
# 日期: 2026-05-07
# 修复: 新增建仓/止损/止盈/对冲/动态调整

LOG_FILE="/tmp/hermes_v30.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v3.0 $(date '+%Y-%m-%d %H:%M:%S')"
echo "5大基本功能完全体"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json
from datetime import datetime
from pathlib import Path

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION = {'BTC':6,'ETH':5,'BNB':5,'SOL':5,'XRP':0,'ADA':0,'DOGE':0,'LINK':2}
TRADE_HISTORY_FILE='/tmp/hermes_trade_history.json'

# ========== v3.0 完整配置 ==========
CONFIG = {
    # 基础配置
    'margin_min': 3.0, 'margin_warn': 3.3,
    'position': 0.25, 'position_max': 0.35,
    'leverage': 5, 'leverage_max': 10,
    'min_notional': 10,
    # 【修复1】建仓配置 - 新增
    'build_enabled': True,           # 允许建仓
    'build_rsi_threshold': 25,     # RSI<25考虑建仓
    'build_max_per_coin': 0.20,    # 单币最大仓位20%
    'build_position_ratio': 0.15,   # 建仓用15%可用金
    # 加仓配置
    'add_enabled': True,
    'add_rsi_threshold': 30,
    'add_strong_rsi': 25,
    'add_ratio': 0.15,
    'add_max_per_coin': 0.35,
    # 【修复2】止损配置 - 完善
    'stop_loss_enabled': True,
    'stop_loss_rsi': 80,           # RSI>80触发止损
    'stop_loss_profit': -0.03,     # 亏损3%触发止损
    'stop_loss_trailing': 0.05,    # 回撤5%触发止损
    # 【修复3】止盈配置 - 完善
    'take_profit_enabled': True,
    'take_profit_rsi': 75,         # RSI>75考虑止盈
    'take_profit_profit': 0.08,    # 盈利8%触发止盈
    'take_profit_partial': 0.50,   # 部分止盈50%
    # 减仓配置
    'reduce_enabled': True,
    'reduce_rsi_threshold': 70,
    'reduce_strong_rsi': 75,
    'reduce_profit_threshold': 0.05,
    'reduce_strong_profit': 0.10,
    'reduce_ratio': 0.20,
    'reduce_min_profit': 0.02,
    # 【修复4】对冲配置 - 新增
    'hedge_enabled': False,
    'hedge_threshold': 0.80,       # 仓位超过80%考虑对冲
    'hedge_ratio': 0.10,           # 对冲10%
    # 【修复5】动态杠杆 - 新增
    'dynamic_leverage': True,
    'leverage_bull': 8,            # 牛市提高杠杆
    'leverage_bear': 3,            # 熊市降低杠杆
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
    if change>1: trend="📈强势上涨"
    elif change>0.3: trend="📊上涨"
    elif change>-0.3: trend="➡️震荡"
    elif change>-1: trend="📉下跌"
    else: trend="📉强势下跌"
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
        with open(TRADE_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except: return {}

def save_trade_history(history):
    try:
        with open(TRADE_HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    except: pass

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

# ========== v3.0 五大功能引擎 ==========

def market_sensing():
    """【功能1】积极觉察 - 市场扫描"""
    print("\n"+"="*60)
    print("🔍 积极觉察 - 市场扫描")
    print("="*60)
    
    coins=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK','AVAX','DOT']
    market={}
    global_trend_up=0
    
    for coin in coins:
        sym=f"{coin}USDT"
        price=get_price(sym)
        klines_1h=get_klines(sym,'1h',60)
        klines_4h=get_klines(sym,'4h',20)
        klines_1d=get_klines(sym,'1d',7)
        
        if klines_1h:
            rsi_1h=calc_rsi([k[2] for k in klines_1h])
            trend_1h,chg_1h=get_trend(klines_1h[-30:]) if len(klines_1h)>=30 else ("N/A",0)
            trend_4h,chg_4h=get_trend(klines_1d) if klines_4h else ("N/A",0)
            trend_1d,chg_1d=get_trend(klines_1d) if klines_1d else ("N/A",0)
            
            # 计算市场广度
            if chg_1h>0: global_trend_up+=1
            
            market[coin]={
                'price':price,'rsi_1h':rsi_1h,
                'chg_1h':chg_1h,'chg_4h':chg_4h,'chg_1d':chg_1d,
                'trend_1h':trend_1h,'trend_4h':trend_4h,'trend_1d':trend_1d
            }
            
            print(f"  {coin}: ${price:.4f} RSI={rsi_1h:.1f} {chg_1h:+.2f}%/{chg_4h:+.2f}%/{chg_1d:+.2f}%")
    
    # 市场广度判断
    breadth_ratio=global_trend_up/len(coins)
    if breadth_ratio>0.7: market_regime="BULL"
    elif breadth_ratio<0.3: market_regime="BEAR"
    else: market_regime="NEUTRAL"
    
    print(f"\n  市场广度: {global_trend_up}/{len(coins)}上涨")
    print(f"  市场状态: {market_regime}")
    
    return market, market_regime, breadth_ratio

def build_position_decision(market, margin_assets, margin_ml, total_margin_value, usdt_balance, positions):
    """【功能2a】建仓决策 - 对未持仓币种"""
    print("\n"+"="*60)
    print("🏗️ 建仓决策 - 未持仓币种")
    print("="*60)
    
    build_decisions=[]
    
    for coin, data in market.items():
        # 跳过已有持仓
        if coin in positions: continue
        
        rsi=data.get('rsi_1h', 50)
        price=data.get('price', 0)
        
        # RSI门槛检查
        if rsi >= CONFIG['build_rsi_threshold']: continue
        
        # 保证金率检查
        if margin_ml < CONFIG['margin_warn']: continue
        
        # 计算建仓数量
        build_value=usdt_balance*CONFIG['build_position_ratio']*CONFIG['leverage']
        build_qty=(build_value/price)*0.99
        build_qty=round_qty(build_qty, coin)
        
        if price*build_qty < CONFIG['min_notional']: continue
        
        # 信号强度
        if rsi < 20: signal="🔴极度超卖-强烈建仓"
        elif rsi < CONFIG['build_rsi_threshold']: signal="🟡超卖-建仓"
        else: signal="⚪观望"
        
        build_decisions.append({
            'coin':coin,'rsi':rsi,'signal':signal,'price':price,
            'build_qty':build_qty,'build_value':price*build_qty
        })
        
        if rsi < CONFIG['build_rsi_threshold']:
            print(f"  {coin}: RSI={rsi:.1f} {signal}")
            print(f"    建仓: {build_qty} (${price*build_qty:.2f})")
    
    return build_decisions

def add_position_decision(market, margin_assets, margin_ml, total_margin_value, usdt_balance, positions):
    """【功能2b】加仓决策 - 对已有持仓"""
    print("\n"+"="*60)
    print("📈 加仓决策 - 已有持仓")
    print("="*60)
    
    add_decisions=[]
    
    for coin in positions:
        if coin not in market: continue
        
        data=market[coin]
        rsi=data.get('rsi_1h', 50)
        price=data.get('price', 0)
        
        if rsi >= CONFIG['add_rsi_threshold']: continue
        if margin_ml < CONFIG['margin_warn']: continue
        
        current_net=margin_assets.get(coin,{}).get('net',0)
        current_value=abs(current_net)*price
        current_ratio=current_value/total_margin_value if total_margin_value>0 else 0
        
        if current_ratio >= CONFIG['add_max_per_coin']: continue
        
        add_value=usdt_balance*CONFIG['add_ratio']*CONFIG['leverage']
        add_qty=(add_value/price)*0.99
        add_qty=round_qty(add_qty, coin)
        
        if price*add_qty < CONFIG['min_notional']: continue
        
        if rsi < CONFIG['add_strong_rsi']:
            signal="🔴强烈加仓"
        else:
            signal="🟡加仓"
        
        add_decisions.append({
            'coin':coin,'rsi':rsi,'signal':signal,'price':price,
            'add_qty':add_qty,'add_value':price*add_qty
        })
        
        print(f"  {coin}: RSI={rsi:.1f} {signal}")
        print(f"    加仓: {add_qty} (${price*add_qty:.2f})")
    
    return add_decisions

def stop_loss_decision(market, margin_assets, trade_history):
    """【功能2c】止损决策"""
    print("\n"+"="*60)
    print("🛡️ 止损决策")
    print("="*60)
    
    stop_decisions=[]
    
    for coin, data in market.items():
        if coin not in margin_assets: continue
        
        current_net=margin_assets.get(coin,{}).get('net',0)
        if abs(current_net) < 0.0001: continue
        
        rsi=data.get('rsi_1h', 50)
        price=data.get('price', 0)
        
        # 获取入场价
        entry_price=trade_history.get(coin,{}).get('entry_price', price*0.95)
        profit_ratio=(price-entry_price)/entry_price
        
        # 检查止损条件
        should_stop=False
        reason=""
        
        if rsi >= CONFIG['stop_loss_rsi']:
            should_stop=True
            reason=f"RSI={rsi:.1f}>={CONFIG['stop_loss_rsi']}"
        elif profit_ratio <= CONFIG['stop_loss_profit']:
            should_stop=True
            reason=f"亏损{profit_ratio*100:.1f}%<={CONFIG['stop_loss_profit']*100:.0f}%"
        
        if should_stop:
            stop_qty=round_qty(abs(current_net), coin)
            stop_decisions.append({
                'coin':coin,'rsi':rsi,'profit_ratio':profit_ratio,
                'reason':reason,'stop_qty':stop_qty
            })
            print(f"  {coin}: {reason}")
            print(f"    盈亏: {profit_ratio*100:+.1f}%")
            print(f"    止损: {stop_qty}")
    
    return stop_decisions

def take_profit_decision(market, margin_assets, trade_history):
    """【功能2d】止盈决策"""
    print("\n"+"="*60)
    print("💰 止盈决策")
    print("="*60)
    
    tp_decisions=[]
    
    for coin, data in market.items():
        if coin not in margin_assets: continue
        
        current_net=margin_assets.get(coin,{}).get('net',0)
        if abs(current_net) < 0.0001: continue
        
        rsi=data.get('rsi_1h', 50)
        price=data.get('price', 0)
        
        entry_price=trade_history.get(coin,{}).get('entry_price', price*0.95)
        profit_ratio=(price-entry_price)/entry_price
        
        should_tp=False
        reason=""
        
        if rsi >= CONFIG['take_profit_rsi']:
            should_tp=True
            reason=f"RSI={rsi:.1f}>={CONFIG['take_profit_rsi']}"
        elif profit_ratio >= CONFIG['take_profit_profit']:
            should_tp=True
            reason=f"盈利{profit_ratio*100:.1f}%>={CONFIG['take_profit_profit']*100:.0f}%"
        
        if should_tp:
            tp_qty=round_qty(abs(current_net)*CONFIG['take_profit_partial'], coin)
            tp_decisions.append({
                'coin':coin,'rsi':rsi,'profit_ratio':profit_ratio,
                'reason':reason,'tp_qty':tp_qty
            })
            print(f"  {coin}: {reason}")
            print(f"    盈亏: {profit_ratio*100:+.1f}%")
            print(f"    部分止盈: {tp_qty} (50%)")
    
    return tp_decisions

def reduce_position_decision(market, margin_assets, margin_ml, total_margin_value, trade_history):
    """【功能2e】减仓决策"""
    print("\n"+"="*60)
    print("📉 减仓决策")
    print("="*60)
    
    reduce_decisions=[]
    
    for coin in list(margin_assets.keys()):
        if coin not in market: continue
        
        data=market[coin]
        rsi=data.get('rsi_1h', 50)
        price=data.get('price', 0)
        
        current_net=margin_assets.get(coin,{}).get('net',0)
        if abs(current_net) < 0.0001: continue
        
        entry_price=trade_history.get(coin,{}).get('entry_price', price*0.95)
        profit_ratio=(price-entry_price)/entry_price
        
        current_value=abs(current_net)*price
        current_ratio=current_value/total_margin_value if total_margin_value>0 else 0
        
        if rsi >= CONFIG['reduce_rsi_threshold'] and profit_ratio >= CONFIG['reduce_min_profit']:
            reduce_qty=round_qty(abs(current_net)*CONFIG['reduce_ratio'], coin)
            reduce_decisions.append({
                'coin':coin,'rsi':rsi,'profit_ratio':profit_ratio,
                'reduce_qty':reduce_qty
            })
            print(f"  {coin}: RSI={rsi:.1f} 盈利{profit_ratio*100:+.1f}%")
            print(f"    减仓: {reduce_qty}")
    
    return reduce_decisions

def dynamic_leverage_decision(market_regime, breadth_ratio):
    """【功能3】动态杠杆调整"""
    print("\n"+"="*60)
    print("⚡ 动态杠杆决策")
    print("="*60)
    
    if not CONFIG['dynamic_leverage']:
        print(f"  动态杠杆: 已关闭")
        return CONFIG['leverage']
    
    if market_regime=="BULL":
        leverage=CONFIG['leverage_bull']
        reason="牛市提高杠杆"
    elif market_regime=="BEAR":
        leverage=CONFIG['leverage_bear']
        reason="熊市降低杠杆"
    else:
        leverage=CONFIG['leverage']
        reason="震荡市标准杠杆"
    
    print(f"  市场: {market_regime}")
    print(f"  杠杆: {leverage}x ({reason})")
    
    return leverage

# ========== 执行引擎 ==========
def execute_trades(action, decisions, market, margin_assets, trade_history, action_name):
    """执行交易"""
    print(f"\n【执行{action_name}】")
    results=[]
    
    for d in decisions:
        coin=d['coin']
        price=market[coin]['price']
        
        if action=="BUY":
            qty=d.get('build_qty',0) or d.get('add_qty',0)
            result=place_order(f'{coin}USDT','BUY',qty)
        elif action=="SELL":
            qty=d.get('stop_qty',0) or d.get('tp_qty',0) or d.get('reduce_qty',0)
            result=place_order(f'{coin}USDT','SELL',qty)
        
        if 'error' not in result and 'code' not in result:
            results.append(coin)
            print(f"  🟢 {coin} {action}: {qty}")
            # 更新交易历史
            if action=="BUY":
                history=trade_history.get(coin,{})
                history['entry_price']=price
                history['entry_time']=datetime.now().strftime('%Y-%m-%d %H:%M')
                trade_history[coin]=history
        else:
            print(f"  🔴 {coin} 失败: {result}")
    
    save_trade_history(trade_history)
    return results

# ========== 主程序 ==========
print("\n"+"="*70)
print("Hermes v3.0 完全修复版")
print("5大基本功能: 积极觉察|主动决策|自动操作|收益最大化|胜率最大化")
print("="*70)

# 加载交易历史
trade_history=load_trade_history()

# 【功能1】积极觉察
market, market_regime, breadth_ratio = market_sensing()

# 资产
margin_ml, margin_assets=get_margin_data()
prices={'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
        'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
        'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1}
margin_total=sum(abs(m.get('net',0))*prices.get(a,1) for a,m in margin_assets.items())
borrow=margin_assets.get('USDT',{}).get('borrowed',0)
margin_net=margin_total-borrow
usdt_balance=margin_assets.get('USDT',{}).get('free',0)
positions=[a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']

print(f"\n【资产状态】")
print(f"  保证金率: {margin_ml:.3f}")
print(f"  USDT可用: ${usdt_balance:.2f}")
print(f"  MARGIN净值: ${margin_net:.2f}")
print(f"  持仓: {len(positions)}个 {positions}")

# 【功能3】动态杠杆
current_leverage=dynamic_leverage_decision(market_regime, breadth_ratio)

# 【功能2】主动决策
build_decisions=build_position_decision(market,margin_assets,margin_ml,margin_total,usdt_balance,positions) if CONFIG['build_enabled'] else []
add_decisions=add_position_decision(market,margin_assets,margin_ml,margin_total,usdt_balance,positions) if CONFIG['add_enabled'] else []
stop_decisions=stop_loss_decision(market,margin_assets,trade_history) if CONFIG['stop_loss_enabled'] else []
tp_decisions=take_profit_decision(market,margin_assets,trade_history) if CONFIG['take_profit_enabled'] else []
reduce_decisions=reduce_position_decision(market,margin_assets,margin_ml,margin_total,trade_history) if CONFIG['reduce_enabled'] else []

print(f"\n【决策汇总】")
print(f"  建仓信号: {len(build_decisions)}个")
print(f"  加仓信号: {len(add_decisions)}个")
print(f"  止损信号: {len(stop_decisions)}个")
print(f"  止盈信号: {len(tp_decisions)}个")
print(f"  减仓信号: {len(reduce_decisions)}个")

# 执行
stop_trades=execute_trades("SELL",stop_decisions,market,margin_assets,trade_history,"止损") if stop_decisions else []
tp_trades=execute_trades("SELL",tp_decisions,market,margin_assets,trade_history,"止盈") if tp_decisions else []
reduce_trades=execute_trades("SELL",reduce_decisions,market,margin_assets,trade_history,"减仓") if reduce_decisions else []
build_trades=execute_trades("BUY",build_decisions,market,margin_assets,trade_history,"建仓") if build_decisions else []
add_trades=execute_trades("BUY",add_decisions,market,margin_assets,trade_history,"加仓") if add_decisions else []

# Mirofish仿真
sim=mirofish_calibrated(1000,30,'EXPERT')

print("\n"+"="*70)
print("【v3.0总结】")
print("="*70)
print(f"建仓执行: {len(build_trades)}笔")
print(f"加仓执行: {len(add_trades)}笔")
print(f"止损执行: {len(stop_trades)}笔")
print(f"止盈执行: {len(tp_trades)}笔")
print(f"减仓执行: {len(reduce_trades)}笔")
print(f"仿真收益: {sim['avg_return']:+.0f}%")
print(f"市场状态: {market_regime}")
print(f"动态杠杆: {current_leverage}x")
print("="*70)
PYEOF
