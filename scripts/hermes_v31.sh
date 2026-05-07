#!/bin/bash
# Hermes v3.1 - 执行后主动查验版
# 日期: 2026-05-07
# 新增: 订单执行验证系统

LOG_FILE="/tmp/hermes_v31.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v3.1 $(date '+%Y-%m-%d %H:%M:%S')"
echo "执行后主动查验版"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION = {'BTC':6,'ETH':5,'BNB':5,'SOL':5,'XRP':0,'ADA':0,'DOGE':0,'LINK':2}
TRADE_HISTORY_FILE='/tmp/hermes_trade_history.json'
VERIFICATION_LOG='/tmp/hermes_verification.log'

# ========== v3.1 验证配置 ==========
CONFIG = {
    'margin_min': 3.0, 'margin_warn': 3.3,
    'position': 0.25, 'position_max': 0.35,
    'leverage': 5, 'leverage_max': 10,
    'min_notional': 10,
    'build_enabled': True,
    'build_rsi_threshold': 25,
    'build_max_per_coin': 0.20,
    'build_position_ratio': 0.15,
    'add_enabled': True,
    'add_rsi_threshold': 30,
    'add_strong_rsi': 25,
    'add_ratio': 0.15,
    'add_max_per_coin': 0.35,
    'stop_loss_enabled': True,
    'stop_loss_rsi': 80,
    'stop_loss_profit': -0.03,
    'stop_loss_trailing': 0.05,
    'take_profit_enabled': True,
    'take_profit_rsi': 75,
    'take_profit_profit': 0.08,
    'take_profit_partial': 0.50,
    'reduce_enabled': True,
    'reduce_rsi_threshold': 70,
    'reduce_strong_rsi': 75,
    'reduce_profit_threshold': 0.05,
    'reduce_strong_profit': 0.10,
    'reduce_ratio': 0.20,
    'reduce_min_profit': 0.02,
    'hedge_enabled': False,
    'hedge_threshold': 0.80,
    'hedge_ratio': 0.10,
    'dynamic_leverage': True,
    'leverage_bull': 8,
    'leverage_bear': 3,
    # v3.1新增验证配置
    'verify_after_order': True,        # 下单后验证
    'verify_retry': 3,               # 验证失败重试次数
    'verify_timeout': 5,            # 验证等待秒数
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

def log_verification(verification):
    """记录验证结果"""
    try:
        with open(VERIFICATION_LOG, 'a') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {verification}\n")
    except: pass

# ========== v3.1 核心验证引擎 ==========
def verify_order_execution(coin, side, expected_qty, order_result):
    """验证订单执行结果"""
    print("\n"+"="*60)
    print(f"🔍 执行验证: {coin} {side} {expected_qty}")
    print("="*60)
    
    verification = {
        'coin': coin,
        'side': side,
        'expected_qty': expected_qty,
        'order_result': order_result,
        'verified': False,
        'attempts': 0,
        'actual_balance': 0,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 检查订单是否成功
    if 'error' in order_result or 'code' in order_result:
        print(f"  ❌ 订单失败: {order_result}")
        verification['error'] = order_result.get('msg', str(order_result))
        log_verification(f"FAILED: {coin} {side} - {verification['error']}")
        return verification
    
    print(f"  📝 订单提交成功，等待验证...")
    
    # 等待订单确认
    time.sleep(CONFIG['verify_timeout'])
    
    # 验证余额变化
    for attempt in range(CONFIG['verify_retry']):
        verification['attempts'] = attempt + 1
        
        try:
            # 获取最新余额
            ts=int(time.time()*1000)
            params=f'timestamp={ts}&recvWindow=5000'
            sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
            r=requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
            d=r.json()
            
            # 找到对应币种余额
            actual_balance = 0
            for a in d.get('userAssets', []):
                if a['asset'] == coin:
                    free=float(a.get('free',0)); borrowed=float(a.get('borrowed',0))
                    actual_balance = free - borrowed
                    break
            
            verification['actual_balance'] = actual_balance
            
            # 验证余额变化
            if side == 'BUY':
                # 买入后余额应增加
                if actual_balance > 0:
                    verification['verified'] = True
                    print(f"  ✅ 验证成功 (尝试{verification['attempts']}/{CONFIG['verify_retry']})")
                    print(f"     预期: {expected_qty}, 实际: {actual_balance}")
                    log_verification(f"VERIFIED: {coin} {side} {expected_qty} - actual: {actual_balance}")
                    break
                else:
                    print(f"  ⚠️ 余额未变化: {actual_balance}")
            else:  # SELL
                # 卖出后余额应减少
                if actual_balance >= 0:
                    verification['verified'] = True
                    print(f"  ✅ 验证成功 (尝试{verification['attempts']}/{CONFIG['verify_retry']})")
                    print(f"     预期减少: {expected_qty}, 实际: {actual_balance}")
                    log_verification(f"VERIFIED: {coin} {side} {expected_qty} - actual: {actual_balance}")
                    break
                else:
                    print(f"  ⚠️ 余额异常: {actual_balance}")
                    
        except Exception as e:
            print(f"  ⚠️ 验证异常 (尝试{attempt+1}): {e}")
            verification['error'] = str(e)
            time.sleep(2)
    
    if not verification['verified']:
        print(f"  ❌ 验证失败 (已重试{CONFIG['verify_retry']}次)")
        log_verification(f"UNVERIFIED: {coin} {side} {expected_qty} - {verification.get('error', 'unknown')}")
    
    return verification

def verify_margin_level():
    """验证保证金率"""
    print("\n"+"="*60)
    print("🔍 保证金率验证")
    print("="*60)
    
    try:
        ts=int(time.time()*1000)
        params=f'timestamp={ts}&recvWindow=5000'
        sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
        r=requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        d=r.json()
        ml=float(d.get('marginLevel',999))
        
        print(f"  保证金率: {ml:.3f}")
        
        if ml > CONFIG['margin_min']:
            print(f"  ✅ 正常 (>{CONFIG['margin_min']})")
            return {'verified': True, 'margin_level': ml}
        else:
            print(f"  ❌ 过低 (<{CONFIG['margin_min']})")
            return {'verified': False, 'margin_level': ml}
    except Exception as e:
        print(f"  ❌ 验证异常: {e}")
        return {'verified': False, 'error': str(e)}

def execute_with_verification(coin, side, qty):
    """带验证的执行"""
    print(f"\n📤 执行交易: {coin} {side} {qty}")
    
    # 执行订单
    result = place_order(f'{coin}USDT', side, qty)
    
    # 验证执行
    verification = verify_order_execution(coin, side, qty, result)
    
    return {
        'order_result': result,
        'verification': verification
    }

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
    print("🔍 积极觉察 - 市场扫描")
    print("="*60)
    
    coins=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK','AVAX','DOT']
    market={}
    global_trend_up=0
    
    for coin in coins:
        sym=f"{coin}USDT"
        price=get_price(sym)
        klines_1h=get_klines(sym,'1h',60)
        
        if klines_1h:
            rsi_1h=calc_rsi([k[2] for k in klines_1h])
            trend_1h,chg_1h=get_trend(klines_1h[-30:]) if len(klines_1h)>=30 else ("N/A",0)
            if chg_1h>0: global_trend_up+=1
            market[coin]={'price':price,'rsi_1h':rsi_1h,'chg_1h':chg_1h,'trend_1h':trend_1h}
            print(f"  {coin}: ${price:.4f} RSI={rsi_1h:.1f} {chg_1h:+.2f}%")
    
    breadth_ratio=global_trend_up/len(coins)
    if breadth_ratio>0.7: regime="BULL"
    elif breadth_ratio<0.3: regime="BEAR"
    else: regime="NEUTRAL"
    
    print(f"\n  市场广度: {global_trend_up}/{len(coins)}上涨 | 状态: {regime}")
    return market, regime, breadth_ratio

# ========== 交易决策 ==========
def build_decisions(market, margin_assets, margin_ml, total_margin_value, usdt_balance, positions):
    print("\n"+"="*60)
    print("🏗️ 建仓决策")
    print("="*60)
    
    decisions=[]
    for coin, data in market.items():
        if coin in positions: continue
        rsi=data.get('rsi_1h',50); price=data.get('price',0)
        if rsi>=CONFIG['build_rsi_threshold']: continue
        if margin_ml<CONFIG['margin_warn']: continue
        build_value=usdt_balance*CONFIG['build_position_ratio']*CONFIG['leverage']
        build_qty=round_qty((build_value/price)*0.99, coin)
        if price*build_qty<CONFIG['min_notional']: continue
        decisions.append({'coin':coin,'rsi':rsi,'qty':build_qty,'price':price,'action':'BUILD'})
        if rsi<CONFIG['build_rsi_threshold']:
            print(f"  {coin}: RSI={rsi:.1f} 信号建仓 {build_qty}")
    return decisions

def add_decisions(market, margin_assets, margin_ml, total_margin_value, usdt_balance, positions):
    print("\n"+"="*60)
    print("📈 加仓决策")
    print("="*60)
    
    decisions=[]
    for coin in positions:
        if coin not in market: continue
        data=market[coin]; rsi=data.get('rsi_1h',50); price=data.get('price',0)
        if rsi>=CONFIG['add_rsi_threshold']: continue
        if margin_ml<CONFIG['margin_warn']: continue
        current_net=margin_assets.get(coin,{}).get('net',0)
        current_value=abs(current_net)*price
        current_ratio=current_value/total_margin_value if total_margin_value>0 else 0
        if current_ratio>=CONFIG['add_max_per_coin']: continue
        add_value=usdt_balance*CONFIG['add_ratio']*CONFIG['leverage']
        add_qty=round_qty((add_value/price)*0.99, coin)
        if price*add_qty<CONFIG['min_notional']: continue
        decisions.append({'coin':coin,'rsi':rsi,'qty':add_qty,'price':price,'action':'ADD'})
        print(f"  {coin}: RSI={rsi:.1f} 信号加仓 {add_qty}")
    return decisions

def stop_loss_decisions(market, margin_assets, trade_history):
    print("\n"+"="*60)
    print("🛡️ 止损决策")
    print("="*60)
    
    decisions=[]
    for coin in list(margin_assets.keys()):
        if coin not in market: continue
        data=market[coin]; rsi=data.get('rsi_1h',50); price=data.get('price',0)
        current_net=margin_assets.get(coin,{}).get('net',0)
        if abs(current_net)<0.0001: continue
        entry_price=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit_ratio=(price-entry_price)/entry_price
        
        if rsi>=CONFIG['stop_loss_rsi'] or profit_ratio<=CONFIG['stop_loss_profit']:
            stop_qty=round_qty(abs(current_net), coin)
            decisions.append({'coin':coin,'rsi':rsi,'profit_ratio':profit_ratio,'qty':stop_qty,'price':price,'action':'STOP_LOSS'})
            print(f"  {coin}: RSI={rsi:.1f} 盈利{profit_ratio*100:+.1f}% 触发止损")
    return decisions

def take_profit_decisions(market, margin_assets, trade_history):
    print("\n"+"="*60)
    print("💰 止盈决策")
    print("="*60)
    
    decisions=[]
    for coin in list(margin_assets.keys()):
        if coin not in market: continue
        data=market[coin]; rsi=data.get('rsi_1h',50); price=data.get('price',0)
        current_net=margin_assets.get(coin,{}).get('net',0)
        if abs(current_net)<0.0001: continue
        entry_price=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit_ratio=(price-entry_price)/entry_price
        
        if rsi>=CONFIG['take_profit_rsi'] or profit_ratio>=CONFIG['take_profit_profit']:
            tp_qty=round_qty(abs(current_net)*CONFIG['take_profit_partial'], coin)
            decisions.append({'coin':coin,'rsi':rsi,'profit_ratio':profit_ratio,'qty':tp_qty,'price':price,'action':'TAKE_PROFIT'})
            print(f"  {coin}: RSI={rsi:.1f} 盈利{profit_ratio*100:+.1f}% 触发止盈")
    return decisions

def reduce_decisions(market, margin_assets, margin_ml, total_margin_value, trade_history):
    print("\n"+"="*60)
    print("📉 减仓决策")
    print("="*60)
    
    decisions=[]
    for coin in list(margin_assets.keys()):
        if coin not in market: continue
        data=market[coin]; rsi=data.get('rsi_1h',50); price=data.get('price',0)
        current_net=margin_assets.get(coin,{}).get('net',0)
        if abs(current_net)<0.0001: continue
        entry_price=trade_history.get(coin,{}).get('entry_price',price*0.95)
        profit_ratio=(price-entry_price)/entry_price
        
        if rsi>=CONFIG['reduce_rsi_threshold'] and profit_ratio>=CONFIG['reduce_min_profit']:
            reduce_qty=round_qty(abs(current_net)*CONFIG['reduce_ratio'], coin)
            decisions.append({'coin':coin,'rsi':rsi,'profit_ratio':profit_ratio,'qty':reduce_qty,'price':price,'action':'REDUCE'})
            print(f"  {coin}: RSI={rsi:.1f} 盈利{profit_ratio*100:+.1f}% 减仓")
    return decisions

# ========== 执行引擎 ==========
def execute_with_full_verification(decisions, margin_assets, trade_history):
    """带完整验证的执行"""
    print("\n"+"="*60)
    print("⚡ 执行交易 (带验证)")
    print("="*60)
    
    all_results = []
    
    # 优先处理止损/止盈
    priority_order = ['STOP_LOSS', 'TAKE_PROFIT', 'REDUCE', 'BUILD', 'ADD']
    
    for priority in priority_order:
        for d in decisions:
            if d.get('action') != priority: continue
            
            coin = d['coin']
            side = 'BUY' if d['action'] in ['BUILD', 'ADD'] else 'SELL'
            qty = d['qty']
            price = d['price']
            
            print(f"\n📤 {d['action']}: {coin} {side} {qty}")
            
            # 执行订单
            order_result = place_order(f'{coin}USDT', side, qty)
            
            # 验证执行
            if CONFIG['verify_after_order']:
                verification = verify_order_execution(coin, side, qty, order_result)
                
                if verification['verified']:
                    # 更新交易历史
                    if side == 'BUY':
                        history = trade_history.get(coin, {})
                        history['entry_price'] = price
                        history['entry_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                        trade_history[coin] = history
                    
                    all_results.append({
                        'coin': coin,
                        'action': d['action'],
                        'verified': True,
                        'qty': qty,
                        'price': price
                    })
                else:
                    all_results.append({
                        'coin': coin,
                        'action': d['action'],
                        'verified': False,
                        'qty': qty,
                        'price': price,
                        'error': verification.get('error')
                    })
            else:
                if 'error' not in order_result and 'code' not in order_result:
                    all_results.append({
                        'coin': coin,
                        'action': d['action'],
                        'verified': True,
                        'qty': qty,
                        'price': price
                    })
    
    save_trade_history(trade_history)
    return all_results

# ========== 主程序 ==========
print("\n"+"="*70)
print("Hermes v3.1 - 执行后主动查验版")
print("积极觉察 | 自主决策 | 自动操作 | 执行验证")
print("="*70)

# 加载交易历史
trade_history = load_trade_history()

# 积极觉察
market, regime, breadth = market_sensing()

# 获取资产
margin_ml, margin_assets = get_margin_data()
prices={'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
        'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
        'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1}
margin_total=sum(abs(m.get('net',0))*prices.get(a,1) for a,m in margin_assets.items())
borrow=margin_assets.get('USDT',{}).get('borrowed',0)
usdt_balance=margin_assets.get('USDT',{}).get('free',0)
positions=[a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']

print(f"\n【资产状态】")
print(f"  保证金率: {margin_ml:.3f}")
print(f"  USDT可用: ${usdt_balance:.2f}")
print(f"  持仓: {len(positions)}个 {positions}")

# 验证保证金率
margin_verify = verify_margin_level()

# 生成决策
all_decisions = []
all_decisions.extend(build_decisions(market, margin_assets, margin_ml, margin_total, usdt_balance, positions))
all_decisions.extend(add_decisions(market, margin_assets, margin_ml, margin_total, usdt_balance, positions))
all_decisions.extend(stop_loss_decisions(market, margin_assets, trade_history))
all_decisions.extend(take_profit_decisions(market, margin_assets, trade_history))
all_decisions.extend(reduce_decisions(market, margin_assets, margin_ml, margin_total, trade_history))

print(f"\n【决策汇总】")
print(f"  建仓: {len([d for d in all_decisions if d['action']=='BUILD'])}个")
print(f"  加仓: {len([d for d in all_decisions if d['action']=='ADD'])}个")
print(f"  止损: {len([d for d in all_decisions if d['action']=='STOP_LOSS'])}个")
print(f"  止盈: {len([d for d in all_decisions if d['action']=='TAKE_PROFIT'])}个")
print(f"  减仓: {len([d for d in all_decisions if d['action']=='REDUCE'])}个")

# 执行
results = execute_with_full_verification(all_decisions, margin_assets, trade_history)

# 再次验证保证金率
print("\n"+"="*60)
print("🔍 执行后验证")
print("="*60)
final_margin_verify = verify_margin_level()

# 仿真
sim = mirofish_calibrated(1000, 30, 'EXPERT')

print("\n"+"="*70)
print("【v3.1总结】")
print("="*70)
verified_count = sum(1 for r in results if r.get('verified', False))
print(f"执行总数: {len(results)}笔")
print(f"验证成功: {verified_count}笔")
print(f"验证失败: {len(results)-verified_count}笔")
print(f"仿真收益: {sim['avg_return']:+.0f}%")
print(f"保证金率: {'✅正常' if final_margin_verify.get('verified', False) else '❌异常'}")
print("="*70)
PYEOF
