#!/bin/bash
# GG 自主交易脚本 v1.0
# 规则: 信号强烈时自主决策，自主操作，不询问
# 触发条件: D>0.6 + RSI在40-70 + 成交量放大
# 日期: 2026-05-06

LOG_FILE="/tmp/gg_autonomous_trade.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "🎯 GG自主交易 $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# 账户状态
ts=int(time.time()*1000)
params='timestamp=%d&recvWindow=5000' % ts
sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
r=requests.get('https://api.binance.com/sapi/v1/margin/account?%s&signature=%s' % (params,sig), headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10).json()
ml=float(r.get('marginLevel',999))

print(f"保证金率: {ml:.3f}")

# 获取持仓
cross={}
for a in r.get('userAssets',[]):
    free=float(a.get('free',0))
    borrowed=float(a.get('borrowed',0))
    if free>0.0001 or borrowed>0.0001:
        cross[a['asset']]={'free':free,'borrowed':borrowed}

# 获取K线
def get_klines(symbol, limit=24):
    try:
        rr=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit={limit}', proxies=PROXIES, timeout=10)
        data=rr.json()
        return [(float(d[1]), float(d[2]), float(d[3]), float(d[4]), float(d[5])) for d in data]
    except: return None

# 计算声纳指标
def calc_sonar(closes, volumes):
    n=len(closes)
    deltas=[closes[i]-closes[i-1] for i in range(1,n)]
    gains=[d if d>0 else 0 for d in deltas]
    losses=[-d if d<0 else 0 for d in deltas]
    avg_gain=sum(gains[-14:])/14
    avg_loss=sum(losses[-14:])/14
    rsi=100-(100/(1+avg_gain/(avg_loss+0.0001)))
    
    ema12=sum(closes[-12:])/12
    ema26=sum(closes[-26:])/26
    macd=ema12-ema26
    signal=macd*0.8
    
    ma20=sum(closes[-20:])/20
    std=(sum((c-ma20)**2 for c in closes[-20:])/20)**0.5
    bb_upper=ma20+2*std
    bb_lower=ma20-2*std
    
    ma5=sum(closes[-5:])/5
    ma20_arr=sum(closes[-20:])/20
    trend=1 if ma5>ma20_arr else(-1 if ma5<ma20_arr else 0)
    change=(closes[-1]-closes[-24])/closes[-24]*100 if n>=24 else 0
    returns=[(closes[i]-closes[i-1])/closes[i-1] for i in range(1,n)]
    vol_m=sum(abs(r) for r in returns[-24:])/24*100
    D=0.35*trend+0.3*(change/10)-0.1*vol_m
    D=max(-1,min(1,D))
    
    avg_vol=sum(volumes[-20:])/20
    vol_ratio=volumes[-1]/avg_vol if avg_vol>0 else 1
    
    score=0
    if rsi<40: score+=1
    if rsi>70: score+=1
    if macd>signal: score+=1
    if vol_ratio>1.5: score+=1
    if D>0.3: score+=1
    if closes[-1]>bb_upper: score+=1
    if closes[-1]<bb_lower: score+=1
    
    return {'rsi':rsi,'macd':macd,'signal':signal,'bb_upper':bb_upper,'bb_lower':bb_lower,
            'ma20':ma20,'vol_ratio':vol_ratio,'D':D,'score':score,'price':closes[-1],'change':change}

# 检查所有币种
coins=['LINK','BTC','ETH','BNB','SOL','XRP','ADA','DOGE']
print("\n【扫描信号】")
signals=[]

for coin in coins:
    sym=f"{coin}USDT"
    klines=get_klines(sym,24)
    if not klines: continue
    
    closes=[k[3] for k in klines]
    volumes=[k[4] for k in klines]
    sonar=calc_sonar(closes,volumes)
    
    print(f"{coin}: D={sonar['D']:.2f} RSI={sonar['rsi']:.0f} Vol={sonar['vol_ratio']:.1f}x Score={sonar['score']}/6")
    
    # 强烈买入信号: D>0.6 + RSI在40-70 + 成交量放大
    if sonar['D']>0.6 and 40<sonar['rsi']<70 and sonar['vol_ratio']>1.2:
        signals.append((coin,sonar))
    
    # 卖出信号: D<-0.3 或 RSI>85 或跌破MA20
    if coin in cross:
        if sonar['D']<-0.3 or sonar['rsi']>85 or closes[-1]<sonar['ma20']:
            print(f"  ⚠️ 警告: {coin} 触发卖出条件!")

# 执行交易
print("\n【自主决策】")
if not signals:
    print("无强烈信号，继续持有当前仓位")
elif ml<2.5:
    print("保证金率过低({:.2f})，跳过开新仓位".format(ml))
elif ml<3.0:
    print("保证金率预警({:.2f})，谨慎操作".format(ml))
else:
    # 按D分数排序，选最强信号
    signals.sort(key=lambda x: x[1]['D'], reverse=True)
    best=singals[0]
    coin=best[0]
    sonar=best[1]
    print(f"✅ 强烈信号: {coin}")
    print(f"   D={sonar['D']:.2f} RSI={sonar['rsi']:.0f} Vol={sonar['vol_ratio']:.1f}x")
    print(f"   建议: 买入{coin}")
    print(f"   原因: 趋势强劲，成交量放大")

print(f"\n执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
PYEOF
