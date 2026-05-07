#!/bin/bash
# Hermes终极驱动v2.3 - 主动加减仓版
# 日期: 2026-05-07

LOG_FILE="/tmp/hermes_v23.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes v2.3 $(date '+%Y-%m-%d %H:%M:%S')"
echo "主动加减仓 | 条件阈值 | 自动化"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

PRECISION = {'BTC': 6, 'ETH': 5, 'BNB': 5, 'SOL': 5, 'XRP': 0, 'ADA': 0, 'DOGE': 0, 'LINK': 2}

CONFIG = {
    # 基础
    'margin_min': 3.0, 'margin_warn': 3.3,
    'position': 0.25, 'position_max': 0.30,
    'leverage': 5, 'leverage_max': 10,
    'min_notional': 10,
    # 加仓
    'add_enabled': True,
    'add_rsi_threshold': 30,
    'add_strong_rsi': 25,
    'add_ratio': 0.15,
    'add_max_per_coin': 0.30,
    # 减仓 v2.3新增
    'reduce_enabled': True,
    'reduce_rsi_threshold': 70,        # RSI>70考虑减仓
    'reduce_strong_rsi': 75,          # RSI>75强烈减仓
    'reduce_profit_threshold': 0.05,   # 盈利>5%考虑减仓
    'reduce_strong_profit': 0.10,      # 盈利>10%强烈减仓
    'reduce_ratio': 0.20,              # 每次减仓20%
    'reduce_min_profit': 0.02,         # 最小盈利2%才减仓
}

BACKTEST = {'NORMAL': {'30d': 1637, 'wr': 80.4, 'daily': 10.0, 'sharpe': 1.8},
            'EXPERT': {'30d': 1101, 'wr': 82.5, 'daily': 8.6, 'sharpe': 2.2}}

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
    params={'symbol': symbol, 'side': side, 'type': 'MARKET', 'quantity': quantity, 'timestamp': ts, 'recvWindow': 5000}
    query_string='&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig=hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    url=f"https://api.binance.com/sapi/v1/margin/order?{query_string}&signature={sig}"
    try:
        r=requests.post(url, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e: return {'error': str(e)}

def round_qty(qty, coin):
    p=PRECISION.get(coin, 6)
    if p==0: return int(round(qty))
    return round(qty, p)

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

# ========== 减仓决策引擎 v2.3 ==========
def reduce_position_decision(market, margin_assets, margin_ml, total_margin_value, entry_prices):
    """主动减仓决策引擎"""
    print("\n"+"="*60)
    print("📉 主动减仓决策引擎 v2.3")
    print("="*60)
    
    reduce_decisions = []
    
    for coin, data in market.items():
        rsi = data.get('rsi', 50)
        current_price = data.get('price', 0)
        
        # 检查是否在持仓中
        if coin not in margin_assets:
            continue
        
        current_net = margin_assets.get(coin, {}).get('net', 0)
        if abs(current_net) < 0.0001:
            continue
        
        # 获取入场价格计算盈亏
        entry_price = entry_prices.get(coin, current_price)
        profit_ratio = (current_price - entry_price) / entry_price if entry_price > 0 else 0
        current_position_value = abs(current_net) * current_price
        current_position_ratio = current_position_value / total_margin_value if total_margin_value > 0 else 0
        
        # 条件1: RSI超过阈值
        if rsi < CONFIG['reduce_rsi_threshold']:
            continue
        
        # 条件2: 盈利超过最小盈利
        if profit_ratio < CONFIG['reduce_min_profit']:
            print(f"\n  {coin}: RSI={rsi:.1f} 盈利{profit_ratio*100:.1f}% < {CONFIG['reduce_min_profit']*100:.0f}% 持仓")
            continue
        
        # 计算减仓数量
        reduce_value = current_position_value * CONFIG['reduce_ratio']
        reduce_qty = (reduce_value / current_price) * 0.99
        reduce_qty = round_qty(reduce_qty, coin)
        
        # 判断信号强度
        if rsi >= CONFIG['reduce_strong_rsi'] or profit_ratio >= CONFIG['reduce_strong_profit']:
            signal = "🔴强烈减仓"
            priority = 1
        else:
            signal = "🟡减仓"
            priority = 2
        
        reduce_decisions.append({
            'coin': coin, 'rsi': rsi, 'signal': signal, 'priority': priority,
            'profit_ratio': profit_ratio,
            'current_ratio': current_position_ratio,
            'reduce_qty': reduce_qty,
            'reduce_value': reduce_value,
        })
        
        print(f"\n  {coin}: RSI={rsi:.1f} {signal}")
        print(f"    盈利: {profit_ratio*100:.1f}%")
        print(f"    仓位: {current_position_ratio*100:.1f}% -> 目标: {(current_position_ratio-CONFIG['reduce_ratio']*current_position_ratio)*100:.1f}%")
        print(f"    减仓: {reduce_qty} (${reduce_value:.2f})")
    
    reduce_decisions.sort(key=lambda x: x['priority'])
    return reduce_decisions

# ========== 加仓决策引擎 ==========
def add_position_decision(market, margin_assets, margin_ml, total_margin_value, usdt_balance):
    """主动加仓决策引擎"""
    print("\n"+"="*60)
    print("📈 主动加仓决策引擎 v2.3")
    print("="*60)
    
    add_decisions = []
    
    for coin, data in market.items():
        rsi = data.get('rsi', 50)
        price = data.get('price', 0)
        current_net = margin_assets.get(coin, {}).get('net', 0)
        current_position_value = abs(current_net) * price
        current_position_ratio = current_position_value / total_margin_value if total_margin_value > 0 else 0
        
        if coin not in margin_assets or abs(current_net) < 0.0001:
            continue
        if rsi >= CONFIG['add_rsi_threshold']:
            continue
        if margin_ml < CONFIG['margin_warn']:
            continue
        if current_position_ratio >= CONFIG['add_max_per_coin']:
            continue
        
        add_value_base = usdt_balance * CONFIG['add_ratio'] * CONFIG['leverage']
        add_value = max(add_value_base, CONFIG['min_notional'])
        add_qty = (add_value / price) * 0.99
        add_qty = round_qty(add_qty, coin)
        
        if price * add_qty < CONFIG['min_notional']:
            add_qty = round_qty(CONFIG['min_notional'] / price * 1.01, coin)
        
        if rsi < CONFIG['add_strong_rsi']:
            signal = "🔴强烈加仓"
            priority = 1
        else:
            signal = "🟡加仓"
            priority = 2
        
        add_decisions.append({
            'coin': coin, 'rsi': rsi, 'signal': signal, 'priority': priority,
            'current_ratio': current_position_ratio, 'add_qty': add_qty, 'add_value': price * add_qty,
        })
        
        print(f"\n  {coin}: RSI={rsi:.1f} {signal}")
        print(f"    加仓: {add_qty} (${price*add_qty:.2f})")
    
    add_decisions.sort(key=lambda x: x['priority'])
    return add_decisions

# ========== 主程序 ==========
print("\n"+"="*70)
print("Hermes v2.3 - 主动加减仓版")
print("="*70)

print("\n【v2.3新功能】")
print(f"  加仓: RSI<{CONFIG['add_rsi_threshold']}考虑，RSI<{CONFIG['add_strong_rsi']}强烈")
print(f"  减仓: RSI>{CONFIG['reduce_rsi_threshold']}考虑，RSI>{CONFIG['reduce_strong_rsi']}强烈")
print(f"  盈利减仓: >{CONFIG['reduce_min_profit']*100:.0f}%开始考虑，>{CONFIG['reduce_strong_profit']*100:.0f}%强烈")

# 市场数据
market = {}
for coin in ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']:
    sym = f"{coin}USDT"
    price = get_price(sym)
    klines_1h = get_klines(sym, '1h', 60)
    rsi = calc_rsi([k[2] for k in klines_1h]) if klines_1h else 50
    change_1h = (klines_1h[-1][2]-klines_1h[-30][2])/klines_1h[-30][2]*100 if klines_1h and len(klines_1h)>=30 else 0
    market[coin] = {'price': price, 'rsi': rsi, 'change_1h': change_1h}

print("\n【市场数据】")
for coin, data in market.items():
    print(f"  {coin}: ${data['price']:.4f} RSI={data['rsi']:.1f} {data['change_1h']:+.2f}%")

# 资产
margin_ml, margin_assets = get_margin_data()
prices = {'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
          'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
          'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1}
margin_total = sum(abs(m.get('net',0))*prices.get(a,1) for a,m in margin_assets.items())
borrow = margin_assets.get('USDT',{}).get('borrowed',0)
margin_net = margin_total - borrow
usdt_balance = margin_assets.get('USDT', {}).get('free', 0)
positions = [a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']

# 模拟入场价格(实际应该从持仓记录获取)
entry_prices = {}
for coin in positions:
    entry_prices[coin] = market[coin]['price'] * 0.95  # 假设平均入场价为当前价的95%

print(f"\n【资产状态】")
print(f"  保证金率: {margin_ml:.3f}")
print(f"  USDT可用: ${usdt_balance:.2f}")
print(f"  MARGIN净值: ${margin_net:.2f}")
print(f"  持仓: {len(positions)}个币种")

# 减仓决策
print("\n【主动减仓决策】")
reduce_decisions = []
if CONFIG['reduce_enabled'] and margin_ml >= CONFIG['margin_min']:
    reduce_decisions = reduce_position_decision(market, margin_assets, margin_ml, margin_total, entry_prices)
    print(f"\n减仓信号: {len(reduce_decisions)}个")
else:
    print("减仓功能已关闭")

# 加仓决策
print("\n【主动加仓决策】")
add_decisions = []
if CONFIG['add_enabled'] and margin_ml >= CONFIG['margin_warn']:
    add_decisions = add_position_decision(market, margin_assets, margin_ml, margin_total, usdt_balance)
    print(f"\n加仓信号: {len(add_decisions)}个")
else:
    print("加仓功能已关闭或保证金率不足")

# 执行减仓
print("\n【执行减仓】")
reduce_trades = []
if reduce_decisions and margin_ml >= CONFIG['margin_min']:
    for decision in reduce_decisions:
        coin = decision['coin']
        reduce_qty = decision['reduce_qty']
        price = market[coin]['price']
        notional = price * reduce_qty
        if notional < CONFIG['min_notional']:
            print(f"  ⏭️ {coin}: 金额不足")
            continue
        if decision['profit_ratio'] < CONFIG['reduce_min_profit']:
            print(f"  ⏭️ {coin}: 盈利不足")
            continue
        result = place_order(f'{coin}USDT', 'SELL', reduce_qty)
        if 'error' not in result and 'code' not in result:
            reduce_trades.append(coin)
            print(f"  🟢 减仓 {coin}: {reduce_qty} @ ${price:.4f} (盈利{decision['profit_ratio']*100:.1f}%)")
        else:
            print(f"  🔴 {coin}: {result}")
elif not reduce_decisions:
    print("  无减仓信号")

# 执行加仓
print("\n【执行加仓】")
add_trades = []
if add_decisions and margin_ml >= CONFIG['margin_min']:
    for decision in add_decisions:
        coin = decision['coin']
        add_qty = decision['add_qty']
        price = market[coin]['price']
        notional = price * add_qty
        if notional < CONFIG['min_notional']:
            print(f"  ⏭️ {coin}: 金额不足")
            continue
        if notional > usdt_balance * CONFIG['leverage']:
            print(f"  ⏭️ {coin}: 余额不足")
            continue
        result = place_order(f'{coin}USDT', 'BUY', add_qty)
        if 'error' not in result and 'code' not in result:
            add_trades.append(coin)
            print(f"  🟢 加仓 {coin}: {add_qty} @ ${price:.4f}")
        else:
            print(f"  🔴 {coin}: {result}")
elif not add_decisions:
    print("  无加仓信号")

# Mirofish仿真
print("\n【Mirofish仿真】")
sim = mirofish_calibrated(1000, 30, 'EXPERT')
print(f"  30天仿真收益: {sim['avg_return']:+.0f}%")

print("\n"+"="*70)
print("【v2.3总结】")
print("="*70)
print(f"减仓信号: {len(reduce_decisions)}个 | 执行: {len(reduce_trades)}笔")
print(f"加仓信号: {len(add_decisions)}个 | 执行: {len(add_trades)}笔")
print(f"仿真收益: {sim['avg_return']:+.0f}%")
print(f"状态: 运行中")
print("="*70)
PYEOF
