#!/bin/bash
# GG v2.9.1 专家模式
# 日期: 2026-05-06

LOG_FILE="/tmp/gg_v291_expert.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "GG v2.9.1 $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, random

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# v2.9.1配置
MARGIN_MIN = 3.0
RSI_SHORT = 73
RSI_LONG = 30
RSI_SHORT_WR = 0.90
RSI_LONG_WR = 0.86
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

def analyze_coin(coin):
    sym=f"{coin}USDT"
    klines=get_klines(sym,'1h',30)
    if not klines or len(klines)<20: return None
    closes=[k[2] for k in klines]
    return {'rsi':calc_rsi(closes),'d':calc_d(closes)}

margin=get_margin()
print(f"保证金率: {margin:.3f}")

if margin<MARGIN_MIN:
    print(f"禁止开仓")
    exit()

regime=get_market_regime()
print(f"市场: {regime}")

coins=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']
signals={'LONG':[],'SHORT':[],'HOLD':[]}

for coin in coins:
    data=analyze_coin(coin)
    if not data: continue
    rsi=data['rsi']
    D=data['d']
    
    if rsi>RSI_SHORT:
        if random.random()<RSI_SHORT_WR:
            signals['SHORT'].append({'coin':coin,'rsi':rsi,'d':D})
    elif rsi<RSI_LONG:
        if random.random()<RSI_LONG_WR:
            signals['LONG'].append({'coin':coin,'rsi':rsi,'d':D})
    elif regime=="BULL" and D>0.25:
        signals['LONG'].append({'coin':coin,'rsi':rsi,'d':D})
    elif regime=="BEAR" and D<-0.15:
        signals['SHORT'].append({'coin':coin,'rsi':rsi,'d':D})
    else:
        signals['HOLD'].append({'coin':coin,'rsi':rsi,'d':D})

print(f"\n做多: {len(signals['LONG'])}个")
for s in signals['LONG']:
    print(f"  {s['coin']}: RSI={s['rsi']:.1f}")
print(f"做空: {len(signals['SHORT'])}个")
for s in signals['SHORT']:
    print(f"  {s['coin']}: RSI={s['rsi']:.1f}")
print(f"观望: {len(signals['HOLD'])}个")
PYEOF

echo "v2.9.1完成"
