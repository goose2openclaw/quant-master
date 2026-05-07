#!/bin/bash
# GG 插针捕获器 v1.0
# 机制: 监测剧烈波动，反向操作
# 做多: 插针下跌后反弹
# 做空: 插针上涨后回落
# 日期: 2026-05-06

LOG_FILE="/tmp/gg_spike_catcher.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "📌 GG插针捕获器 $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# 配置
SPIKE_THRESHOLD = 0.02  # 2%波动视为插针
REBOUND_THRESHOLD = 0.01  # 1%反弹确认
TRADE_AMOUNT = 10  # 每次交易10 USDT

def get_margin():
    ts=int(time.time()*1000)
    params='timestamp=%d&recvWindow=5000' % ts
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get('https://api.binance.com/sapi/v1/margin/account?%s&signature=%s' % (params,sig), headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10).json()
    return float(r.get('marginLevel',999)), r

def get_price(symbol):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines_1m(symbol, limit=5):
    """获取1分钟K线"""
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit={limit}', proxies=PROXIES, timeout=8)
        data=r.json()
        return [(float(d[2]), float(d[3]), float(d[4])) for d in data]  # high, low, close
    except: return None

def place_margin_order(symbol, side, quantity):
    """开杠杆仓位"""
    ts=int(time.time()*1000)
    params=f'symbol={symbol}&side={side}&type=MARKET&quantity={quantity:.4f}&timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    try:
        r=requests.post(f'https://api.binance.com/sapi/v1/margin/order?{params}&signature={sig}', 
                       headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e:
        print(f"下单失败: {e}")
        return None

def repay_and_close(coin):
    """还款并平仓"""
    ts=int(time.time()*1000)
    # 先还款
    params=f'asset={coin}&amount=ALL&timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    try:
        r=requests.post(f'https://api.binance.com/sapi/v1/margin/repay?{params}&signature={sig}',
                       headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        print(f"还款结果: {r.json()}")
    except: pass

print("\n【插针扫描】")

coins = ['LINK','BTC','ETH','BNB','SOL','XRP','DOGE']
spike_opportunities = []

for coin in coins:
    klines = get_klines_1m(f"{coin}USDT", 5)
    if not klines: continue
    
    current_price = get_price(f"{coin}USDT")
    if current_price == 0: continue
    
    # 计算1分钟内波动
    highs = [k[0] for k in klines]
    lows = [k[1] for k in klines]
    closes = [k[2] for k in klines]
    
    # 1分钟最高最低
    high_1m = max(highs)
    low_1m = min(lows)
    
    # 从最低到最高涨幅
    rise = (high_1m - low_1m) / low_1m if low_1m > 0 else 0
    # 从最高回落
    drop = (high_1m - closes[-1]) / high_1m if high_1m > 0 else 0
    
    # 从低点反弹
    rebound = (closes[-1] - low_1m) / low_1m if low_1m > 0 else 0
    
    print(f"{coin}: 现价${current_price:.4f} 波动{rise*100:.2f}% 回落{drop*100:.2f}% 反弹{rebound*100:.2f}%")
    
    # 做空信号: 插针上涨后回落 > 1%
    if rise > SPIKE_THRESHOLD and drop > REBOUND_THRESHOLD:
        spike_opportunities.append({
            'coin': coin,
            'type': 'SHORT',
            'rise': rise,
            'drop': drop,
            'price': current_price,
            'signal': f"插针上涨{rise*100:.1f}%后回落{drop*100:.1f}%"
        })
        print(f"  ⚠️ 做空信号: 插针上涨后回落")
    
    # 做多信号: 插针下跌后反弹 > 0.5%
    if rise > SPIKE_THRESHOLD and rebound > 0.005:
        spike_opportunities.append({
            'coin': coin,
            'type': 'LONG',
            'rise': rise,
            'drop': rebound,
            'price': current_price,
            'signal': f"插针下跌后反弹{rebound*100:.1f}%"
        })
        print(f"  ✅ 做多信号: 插针下跌后反弹")

# 获取保证金率
ml, account = get_margin()
print(f"\n保证金率: {ml:.3f}")

# 执行交易
if spike_opportunities and ml > 3.0:
    # 按波动幅度排序
    spike_opportunities.sort(key=lambda x: x['rise'], reverse=True)
    best = spike_opportunities[0]
    
    print(f"\n【执行决策】")
    print(f"币种: {best['coin']}")
    print(f"类型: {best['type']}")
    print(f"信号: {best['signal']}")
    
    if best['type'] == 'SHORT':
        print(f"⚠️ 做空信号强烈，但做空需要借币")
        print(f"建议: 观望或手动操作")
    else:
        print(f"✅ 做多信号: 考虑买入")
        print(f"建议: 现价 ${best['price']:.4f} 买入")
else:
    print(f"\n【决策】无插针机会或保证金率不足")
    if ml < 3.0:
        print(f"保证金率 {ml:.2f} < 3.0，安全优先")

print(f"\n执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
PYEOF
