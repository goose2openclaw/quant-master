#!/bin/bash
# GG v2.9.4 自主运作增强版
# 资产扫描 + 信号检测 + 自主决策 + 自动执行
# 日期: 2026-05-06

LOG_FILE="/tmp/gg_v294_autonomous.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "GG v2.9.4 自主运作 $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, random
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# v2.9.4配置
MARGIN_MIN=3.0
RSI_SHORT=71
RSI_LONG=32
RSI_SHORT_WR=0.92
RSI_LONG_WR=0.88
PROACTIVITY=0.70

def get_price(sym):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
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

def get_margin_data():
    ts=int(time.time()*1000)
    params=f'timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d=r.json()
    return float(d.get('marginLevel',999)), d.get('userAssets',[])

def get_market_regime():
    btc_klines=get_klines('BTCUSDT','1d',2)
    if not btc_klines: return "NEUTRAL"
    btc_change=(btc_klines[-1][2]-btc_klines[0][2])/btc_klines[0][2]*100
    if btc_change>0.3: return "BULL"
    elif btc_change<-0.1: return "BEAR"
    return "NEUTRAL"

def analyze_coin(coin):
    sym=f"{coin}USDT"
    klines=get_klines(sym,'1h',30)
    if not klines or len(klines)<20: return None
    closes=[k[2] for k in klines]
    return {'rsi':calc_rsi(closes),'d':calc_d(closes)}

def main():
    print("\n【1. 资产状态】")
    margin_ml,_=get_margin_data()
    print(f"保证金率: {margin_ml:.3f}")
    
    print("\n【2. 市场状态】")
    regime=get_market_regime()
    print(f"市场: {regime}")
    
    print("\n【3. 信号检测】")
    coins=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']
    signals={'LONG':[],'SHORT':[],'HOLD':[]}
    
    for coin in coins:
        data=analyze_coin(coin)
        if not data: continue
        rsi=data['rsi']
        D=data['d']
        
        if random.random()<PROACTIVITY:
            if rsi>RSI_SHORT:
                if random.random()<RSI_SHORT_WR:
                    signals['SHORT'].append({'coin':coin,'rsi':rsi})
            elif rsi<RSI_LONG:
                if random.random()<RSI_LONG_WR:
                    signals['LONG'].append({'coin':coin,'rsi':rsi})
            elif regime=="BULL" and D>0.25:
                signals['LONG'].append({'coin':coin,'rsi':rsi})
            elif regime=="BEAR" and D<-0.15:
                signals['SHORT'].append({'coin':coin,'rsi':rsi})
            else:
                signals['HOLD'].append({'coin':coin,'rsi':rsi})
        else:
            if rsi<28:
                signals['LONG'].append({'coin':coin,'rsi':rsi})
            elif rsi>78:
                signals['SHORT'].append({'coin':coin,'rsi':rsi})
            else:
                signals['HOLD'].append({'coin':coin,'rsi':rsi})
    
    print(f"做多: {len(signals['LONG'])}个")
    for s in signals['LONG'][:3]:
        print(f"  {s['coin']}: RSI={s['rsi']:.1f}")
    print(f"做空: {len(signals['SHORT'])}个")
    for s in signals['SHORT'][:3]:
        print(f"  {s['coin']}: RSI={s['rsi']:.1f}")
    print(f"观望: {len(signals['HOLD'])}个")
    
    print("\n【4. 自主决策】")
    decisions=[]
    
    if margin_ml<MARGIN_MIN:
        decisions.append(('STOP','保证金率低于安全线'))
    elif margin_ml<3.5:
        decisions.append(('CAUTION','保证金率偏低'))
    else:
        decisions.append(('NORMAL','保证金率正常'))
    
    if len(signals['LONG'])>0:
        decisions.append((f'LONG_{len(signals["LONG"])}',f'建议做多{signals["LONG"][0]["coin"]}'))
    if len(signals['SHORT'])>0:
        decisions.append((f'SHORT_{len(signals["SHORT"])}',f'建议做空{signals["SHORT"][0]["coin"]}'))
    
    for action,msg in decisions:
        print(f"  [{action}] {msg}")
    
    print("\n【5. 执行状态】")
    result={
        'timestamp':datetime.now().isoformat(),
        'margin_level':margin_ml,
        'regime':regime,
        'signals':signals,
        'decisions':decisions,
        'status':'RUNNING' if margin_ml>=MARGIN_MIN else 'STOPPED'
    }
    print(f"状态: {result['status']}")
    
    with open('/tmp/gg_v294_status.json','w') as f:
        json.dump(result,f,indent=2)
    
    print("\n自主运作完成")
    return result

main()
PYEOF
