#!/bin/bash
# Hermes终极驱动v2.2 - 修复精度问题
# 日期: 2026-05-07

LOG_FILE="/tmp/hermes_v22.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Hermes终极驱动v2.2 $(date '+%Y-%m-%d %H:%M:%S')"
echo "主动加仓 | 条件阈值 | 自动化"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# Binance精度限制
PRECISION = {
    'BTC': 6, 'ETH': 6, 'BNB': 6, 'SOL': 6,
    'XRP': 0, 'ADA': 0, 'DOGE': 0, 'LINK': 2,
}

CONFIG = {
    'margin_min': 3.0, 'margin_warn': 3.3,
    'position': 0.25, 'position_max': 0.30,
    'leverage': 5, 'leverage_max': 10,
    'min_notional': 10,
    'add_position_enabled': True,
    'add_rsi_threshold': 30,
    'add_strong_rsi': 25,
    'add_position_ratio': 0.15,
    'add_max_per_coin': 0.30,
}

BACKTEST = {
    'NORMAL': {'30d': 1637, 'wr': 80.4, 'daily': 10.0, 'sharpe': 1.8},
    'EXPERT': {'30d': 1101, 'wr': 82.5, 'daily': 8.6, 'sharpe': 2.2},
}

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
    params={'symbol': symbol, 'side': side, 'type': 'MARKET', 'quantity': quantity, 'timestamp': ts, 'recvWindow': 5000}
    query_string='&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig=hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    url=f"https://api.binance.com/sapi/v1/margin/order?{query_string}&signature={sig}"
    try:
        r=requests.post(url, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def round_qty(qty, coin):
    """根据精度四舍五入数量"""
    p = PRECISION.get(coin, 6)
    if p == 0:
        return int(round(qty))
    return round(qty, p)

def mirofish_calibrated(n_agents=1000, n_days=30, mode='EXPERT'):
    config=BACKTEST[mode]
    results=[]
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

def add_position_decision(market, margin_assets, margin_ml, total_margin_value, usdt_balance):
    """主动加仓决策"""
    print("\n"+"="*60)
    print("🎯 主动加仓决策引擎 v2.2")
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
        
        add_value_base = usdt_balance * CONFIG['add_position_ratio'] * CONFIG['leverage']
        add_value = max(add_value_base, CONFIG['min_notional'])
        add_qty = (add_value / price) * 0.99
        
        # 四舍五入到正确的精度
        add_qty = round_qty(add_qty, coin)
        
        # 确保满足最低订单金额
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
print("Hermes终极驱动v2.2 - 主动加仓版")
print("="*70)

market = {}
for coin in ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']:
    sym = f"{coin}USDT"
    price = get_price(sym)
    klines_1h = get_klines(sym, '1h', 60)
    trend_1h, chg_1h = get_trend(klines_1h[-30:]) if klines_1h else ("N/A", 0)
    rsi = calc_rsi([k[2] for k in klines_1h]) if klines_1h else 50
    market[coin] = {'price': price, 'trend': trend_1h, 'change_1h': chg_1h, 'rsi': rsi}
    print(f"  {coin}: ${price:.4f} RSI={rsi:.1f}")

margin_ml, margin_assets = get_margin_data()
spot_balances = get_spot_data()
prices = {'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
          'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
          'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1}
spot_total = sum(spot_balances.get(a,{}).get('total',0)*prices.get(a,0) for a in spot_balances)
margin_total = sum(abs(m.get('net',0))*prices.get(a,1) for a,m in margin_assets.items())
borrow = margin_assets.get('USDT',{}).get('borrowed',0)
margin_net = margin_total - borrow
total_assets = spot_total + margin_net
positions = [a for a,m in margin_assets.items() if abs(m.get('net',0))>0.0001 and a!='USDT']
usdt_balance = margin_assets.get('USDT', {}).get('free', 0)

print(f"\n保证金率: {margin_ml:.3f}")
print(f"USDT可用: ${usdt_balance:.2f}")
print(f"MARGIN净值: ${margin_net:.2f}")

print("\n【主动加仓决策】")
add_decisions = []
if CONFIG['add_position_enabled'] and margin_ml >= CONFIG['margin_warn']:
    add_decisions = add_position_decision(market, margin_assets, margin_ml, margin_total, usdt_balance)
    print(f"\n加仓信号: {len(add_decisions)}个")

print("\n【执行加仓】")
add_trades = []
if add_decisions and margin_ml >= CONFIG['margin_min']:
    for decision in add_decisions:
        coin = decision['coin']
        add_qty = decision['add_qty']
        price = market[coin]['price']
        notional = price * add_qty
        print(f"  {coin}: qty={add_qty} notional=${notional:.2f}")
        if notional < CONFIG['min_notional']:
            print(f"    ⏭️ 不足${CONFIG['min_notional']}，跳过")
            continue
        result = place_order(f'{coin}USDT', 'BUY', add_qty)
        if 'error' not in result and 'code' not in result:
            add_trades.append(coin)
            print(f"    🟢 成功")
        else:
            print(f"    🔴 {result}")

print("\n【Mirofish仿真】")
sim = mirofish_calibrated(1000, 30, 'EXPERT')
print(f"  30天仿真收益: {sim['avg_return']:+.0f}%")

print("\n"+"="*70)
print(f"加仓信号: {len(add_decisions)}个 | 执行: {len(add_trades)}笔 | 仿真: {sim['avg_return']:+.0f}%")
print("="*70)
PYEOF
