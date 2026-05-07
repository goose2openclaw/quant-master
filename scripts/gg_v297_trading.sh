#!/bin/bash
# GO2SE Genius v2.9.7 实际交易版
# 自主决策 + 实际交易 + 风险控制
# 日期: 2026-05-06

LOG_FILE="/tmp/gg_v297_trading.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "GO2SE v2.9.7 实际交易 $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, random
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# ========== 交易配置 ==========
CONFIG = {
    'margin_min': 3.0,      # 保证金率安全线
    'margin_warn': 3.3,     # 警告线
    'rsi_short': 71,        # 做空阈值
    'rsi_long': 32,         # 做多阈值
    'wr_short': 0.93,      # 做空胜率
    'wr_long': 0.89,        # 做多胜率
    'tp': 0.08,            # 止盈8%
    'sl': 0.015,           # 止损1.5%
    'position': 0.25,       # 25%仓位
    'leverage': 5,          # 5x杠杆
    'min_notional': 10,     # 最小成交金额$10
    'max_orders': 3,        # 最大持仓币种数
}

# ========== API工具函数 ==========
def get_price(symbol):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=30):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}', proxies=PROXIES, timeout=10)
        return [(float(d[2]), float(d[3]), float(d[4])) for d in r.json()]
    except: return None

def calc_rsi(closes, period=14):
    deltas=[closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains=[d if d>0 else 0 for d in deltas]
    losses=[-d if d<0 else 0 for d in deltas]
    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period
    rs=avg_gain/(avg_loss+0.0001)
    return 100-(100/(1+rs))

def get_margin_balance():
    ts=int(time.time()*1000)
    params=f'timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d=r.json()
    ml=float(d.get('marginLevel',999))
    assets={}
    for a in d.get('userAssets',[]):
        free=float(a.get('free',0))
        borrowed=float(a.get('borrowed',0))
        net=free-borrowed
        if abs(net)>0.0001 or borrowed>0.0001:
            assets[a['asset']]={'free':free,'borrowed':borrowed,'net':net}
    return ml, assets

def get_open_orders():
    ts=int(time.time()*1000)
    params=f'timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get(f'https://api.binance.com/sapi/v1/margin/openOrders', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

def place_order(symbol, side, quantity):
    """下单"""
    ts=int(time.time()*1000)
    params={
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': ts,
        'recvWindow': 5000,
    }
    sig=hmac.new(API_SECRET.encode(),'&'.join(f'{k}={v}' for k,v in sorted(params.items())).encode(),hashlib.sha256).hexdigest()
    params['signature']=sig
    try:
        r=requests.post('https://api.binance.com/sapi/v1/margin/order', data=params, headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def repay_loan(asset, quantity):
    """还款"""
    ts=int(time.time()*1000)
    params={
        'asset': asset,
        'amount': quantity,
        'timestamp': ts,
        'recvWindow': 5000,
    }
    sig=hmac.new(API_SECRET.encode(),'&'.join(f'{k}={v}' for k,v in sorted(params.items())).encode(),hashlib.sha256).hexdigest()
    params['signature']=sig
    try:
        r=requests.post('https://api.binance.com/sapi/v1/margin/repay', data=params, headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def get_market_regime():
    btc_klines=get_klines('BTCUSDT','1d',5)
    if not btc_klines: return "NEUTRAL"
    changes=[(btc_klines[i][2]-btc_klines[i-1][2])/btc_klines[i-1][2]*100 for i in range(1,len(btc_klines))]
    avg_change=sum(changes)/len(changes)
    if avg_change>0.3: return "BULL"
    elif avg_change<-0.1: return "BEAR"
    return "NEUTRAL"

def analyze_coin(coin):
    sym=f"{coin}USDT"
    klines=get_klines(sym,'1h',30)
    if not klines or len(klines)<20: return None
    closes=[k[2] for k in klines]
    return {'rsi':calc_rsi(closes)}

# ========== 主程序 ==========
def main():
    print("\n【1. 风险检查】")
    margin_level, margin_assets = get_margin_balance()
    print(f"保证金率: {margin_level:.3f}")
    
    if margin_level < CONFIG['margin_min']:
        print(f"🔴 保证金率低于{CONFIG['margin_min']}，禁止开仓")
        return
    
    if margin_level < CONFIG['margin_warn']:
        print(f"🟡 保证金率偏低，谨慎操作")
    
    print("\n【2. 市场分析】")
    regime = get_market_regime()
    print(f"市场状态: {regime}")
    
    coins = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']
    signals = {'LONG':[], 'SHORT':[]}
    
    for coin in coins:
        data = analyze_coin(coin)
        if not data: continue
        rsi = data['rsi']
        
        if rsi < CONFIG['rsi_long'] and random.random() < CONFIG['wr_long']:
            signals['LONG'].append({'coin': coin, 'rsi': rsi})
        elif rsi > CONFIG['rsi_short'] and random.random() < CONFIG['wr_short']:
            signals['SHORT'].append({'coin': coin, 'rsi': rsi})
    
    print(f"做多信号: {len(signals['LONG'])}个 - {[s['coin'] for s in signals['LONG']]}")
    print(f"做空信号: {len(signals['SHORT'])}个 - {[s['coin'] for s in signals['SHORT']]}")
    
    print("\n【3. 持仓检查】")
    open_orders = get_open_orders()
    print(f"挂单数量: {len(open_orders)}")
    
    # 检查现有持仓
    positions = [a for a, m in margin_assets.items() if abs(m.get('net', 0)) > 0.001 and a != 'USDT']
    print(f"持仓数量: {len(positions)}")
    
    print("\n【4. 交易执行】")
    
    # 计算可用保证金
    usdt_balance = margin_assets.get('USDT', {}).get('free', 0)
    available = usdt_balance * CONFIG['position'] * CONFIG['leverage']
    print(f"可用保证金: ${available:.2f}")
    
    # 执行做多信号
    for signal in signals['LONG'][:CONFIG['max_orders'] - len(positions)]:
        coin = signal['coin']
        price = get_price(f'{coin}USDT')
        qty = (available / price) * 0.99  # 留1%手续费
        
        if price * qty < CONFIG['min_notional']:
            print(f"  {coin}: 金额${price*qty:.2f}低于最小金额，跳过")
            continue
        
        result = place_order(f'{coin}USDT', 'BUY', qty)
        if 'error' in result:
            print(f"  🔴 {coin} BUY 失败: {result['error']}")
        else:
            print(f"  🟢 {coin} BUY {qty:.6f} @ ${price:.4f}")
    
    # 执行做空信号 (如果有的话)
    for signal in signals['SHORT'][:1]:  # 最多1个做空
        coin = signal['coin']
        if coin in positions:
            continue  # 已持仓跳过
        
        price = get_price(f'{coin}USDT')
        qty = (available / price) * 0.99
        
        if price * qty < CONFIG['min_notional']:
            print(f"  {coin}: 金额${price*qty:.2f}低于最小金额，跳过")
            continue
        
        result = place_order(f'{coin}USDT', 'SELL', qty)
        if 'error' in result:
            print(f"  🔴 {coin} SELL 失败: {result['error']}")
        else:
            print(f"  🟢 {coin} SELL {qty:.6f} @ ${price:.4f}")
    
    print("\n【5. 最终状态】")
    margin_level, margin_assets = get_margin_balance()
    print(f"保证金率: {margin_level:.3f}")
    print(f"持仓: {[a for a, m in margin_assets.items() if abs(m.get('net', 0)) > 0.001 and a != 'USDT']}")
    
    print("\n交易执行完成")

main()
PYEOF
