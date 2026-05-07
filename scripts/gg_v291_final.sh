#!/bin/bash
# GG v2.9.1 Final MVP
# 市场不佳应对 + 替代机会拓展
# 日期: 2026-05-06

LOG_FILE="/tmp/gg_v291_final.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "GG v2.9.1 Final MVP $(date '+%Y-%m-%d %H:%M:%S')"
echo "市场不佳应对 + 替代机会拓展"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, random
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# v2.9.1 Final配置
MARGIN_MIN = 3.0

# 主策略RSI
RSI_SHORT = 73
RSI_LONG = 30
RSI_SHORT_WR = 0.90
RSI_LONG_WR = 0.86

# 替代策略RSI (更宽松)
ALT_RSI_SHORT = 70
ALT_RSI_LONG = 35

# 市场判定
BULL_THRESHOLD = 0.3
BEAR_THRESHOLD = -0.1

def get_margin():
    ts=int(time.time()*1000)
    params='timestamp=%d&recvWindow=5000' % ts
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get('https://api.binance.com/sapi/v1/margin/account?%s&signature=%s' % (params,sig), headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10).json()
    return float(r.get('marginLevel',999))

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

def calc_d(closes):
    if len(closes)<20: return 0
    ma5=sum(closes[-5:])/5
    ma20=sum(closes[-20:])/20
    trend=1 if ma5>ma20 else(-1 if ma5<ma20 else 0)
    change=(closes[-1]-closes[-24])/closes[-24]*100 if len(closes)>=24 else 0
    returns=[(closes[i]-closes[i-1])/closes[i-1] for i in range(1,len(closes))]
    vol=sum(abs(r) for r in returns[-24:])/24*100
    D=0.35*trend+0.3*(change/10)-0.1*vol
    return max(-1,min(1,D))

def get_market_regime():
    btc_klines=get_klines('BTCUSDT','1d',2)
    eth_klines=get_klines('ETHUSDT','1d',2)
    if not btc_klines: return "NEUTRAL"
    btc_change=(btc_klines[-1][2]-btc_klines[0][2])/btc_klines[0][2]*100
    eth_change=0
    if eth_klines:
        eth_change=(eth_klines[-1][2]-eth_klines[0][2])/eth_klines[0][2]*100
    if btc_change>BULL_THRESHOLD and eth_change>0:
        return "BULL"
    elif btc_change<BEAR_THRESHOLD and eth_change<0:
        return "BEAR"
    return "NEUTRAL"

def detect_bad_market():
    """检测市场不佳条件"""
    btc_price=get_price('BTCUSDT')
    btc_klines=get_klines('BTCUSDT','1h',24)
    
    conditions = {
        'low_liquidity': False,
        'sideways': False,
        'high_volatility': False,
    }
    
    if btc_klines and len(btc_klines) >= 24:
        vols=[abs(btc_klines[i][2]-btc_klines[i][1])/btc_klines[i][2] for i in range(len(btc_klines))]
        avg_vol=sum(vols)/len(vols)
        recent_vol=sum(vols[-5:])/5
        if recent_vol < avg_vol * 0.5:
            conditions['low_liquidity'] = True
        
        closes=[k[2] for k in btc_klines]
        rsi=calc_rsi(closes)
        if 40 < rsi < 60:
            conditions['sideways'] = True
        
        if recent_vol > avg_vol * 2:
            conditions['high_volatility'] = True
    
    return conditions

def analyze_coin(coin):
    sym=f"{coin}USDT"
    klines=get_klines(sym,'1h',30)
    if not klines or len(klines)<20: return None
    closes=[k[2] for k in klines]
    return {'rsi':calc_rsi(closes),'d':calc_d(closes)}

def find_alt_opportunities(coins, regime, bad_conditions):
    """寻找替代机会"""
    opps={'LONG':[],'SHORT':[],'RANGE':[],'HOLD':[]}
    
    for coin in coins:
        data=analyze_coin(coin)
        if not data: continue
        rsi=data['rsi']
        D=data['d']
        
        # 替代策略: 更宽松的RSI阈值
        if bad_conditions['sideways']:
            # 横盘: 区间策略
            if 40 < rsi < 60:
                opps['RANGE'].append({'coin':coin,'rsi':rsi,'d':D})
            elif rsi < 40:
                opps['LONG'].append({'coin':coin,'rsi':rsi,'d':D})
            elif rsi > 60:
                opps['SHORT'].append({'coin':coin,'rsi':rsi,'d':D})
            else:
                opps['HOLD'].append({'coin':coin,'rsi':rsi,'d':D})
        elif bad_conditions['low_liquidity']:
            # 低流动性: 更保守
            if rsi < 35:
                opps['LONG'].append({'coin':coin,'rsi':rsi,'d':D})
            elif rsi > 70:
                opps['SHORT'].append({'coin':coin,'rsi':rsi,'d':D})
            else:
                opps['HOLD'].append({'coin':coin,'rsi':rsi,'d':D})
        else:
            # 主策略
            if rsi > RSI_SHORT:
                if random.random()<RSI_SHORT_WR:
                    opps['SHORT'].append({'coin':coin,'rsi':rsi,'d':D})
            elif rsi < RSI_LONG:
                if random.random()<RSI_LONG_WR:
                    opps['LONG'].append({'coin':coin,'rsi':rsi,'d':D})
            elif regime=="BULL" and D>0.25:
                opps['LONG'].append({'coin':coin,'rsi':rsi,'d':D})
            elif regime=="BEAR" and D<-0.15:
                opps['SHORT'].append({'coin':coin,'rsi':rsi,'d':D})
            else:
                opps['HOLD'].append({'coin':coin,'rsi':rsi,'d':D})
    
    return opps

# ================== 主程序 ==================
margin=get_margin()
print(f"保证金率: {margin:.3f}")

if margin<MARGIN_MIN:
    print(f"禁止开仓")
    exit()

regime=get_market_regime()
bad_conditions=detect_bad_market()

print(f"市场状态: {regime}")
print(f"不佳条件: {bad_conditions}")

coins=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']
opps=find_alt_opportunities(coins, regime, bad_conditions)

print(f"\n做多信号: {len(opps['LONG'])}个")
for s in opps['LONG'][:3]:
    print(f"  {s['coin']}: RSI={s['rsi']:.1f}")
print(f"做空信号: {len(opps['SHORT'])}个")
for s in opps['SHORT'][:3]:
    print(f"  {s['coin']}: RSI={s['rsi']:.1f}")
print(f"区间信号: {len(opps['RANGE'])}个")
print(f"观望: {len(opps['HOLD'])}个")
print(f"\n检测完成")
PYEOF

echo "v2.9.1 Final MVP执行完成 $(date)"
