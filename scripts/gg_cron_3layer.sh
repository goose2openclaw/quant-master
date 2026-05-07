#!/bin/bash
# GG 三层Cron监控系统
# Layer 1: 风险监控 (每1分钟)
# Layer 2: 自主交易 (每5分钟)
# Layer 3: 日终报告 (每天一次)
# 日期: 2026-05-06

MODE=${1:-all}

python3 << 'PYEOF'
import requests, hmac, hashlib, time
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

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

def calc_D(closes):
    if len(closes)<20: return 0
    ma5=sum(closes[-5:])/5
    ma20=sum(closes[-20:])/20
    trend=1 if ma5>ma20 else(-1 if ma5<ma20 else 0)
    change=(closes[-1]-closes[-24])/closes[-24]*100 if len(closes)>=24 else 0
    returns=[(closes[i]-closes[i-1])/closes[i-1] for i in range(1,len(closes))]
    vol=sum(abs(r) for r in returns[-24:])/24*100
    D=0.35*trend+0.3*(change/10)-0.1*vol
    return max(-1,min(1,D))

def get_klines(symbol, limit=24):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit={limit}', proxies=PROXIES, timeout=10)
        return [float(d[4]) for d in r.json()]
    except: return None

# === LAYER 1: 风险监控 (每分钟) ===
def layer1_risk_monitor():
    ml, account = get_margin()
    now = datetime.now().strftime('%H:%M:%S')
    
    if ml < 2.5:
        status = "🚨强制平仓风险!"
        action = "立即减仓!"
    elif ml < 3.0:
        status = "⚠️预警"
        action = "准备减仓"
    else:
        status = "✅安全"
        action = "正常"
    
    print(f"[{now}] Layer1 风险监控: 保证金率={ml:.3f} {status}")
    
    if ml < 2.5:
        print(f"  🚨 {action} - 执行强制减仓!")
        # 这里可以加自动减仓逻辑
    
    return ml, status

# === LAYER 2: 自主交易 (每5分钟) ===
def layer2_autonomous_trade():
    ml, _ = get_margin()
    if ml < 3.0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Layer2 自主交易: 保证金率低，跳过")
        return
    
    coins=['LINK','BTC','ETH','BNB','SOL','XRP','ADA','DOGE']
    signals=[]
    
    for coin in coins:
        closes=get_klines(f"{coin}USDT",24)
        if not closes: continue
        D=calc_D(closes)
        
        deltas=[closes[i]-closes[i-1] for i in range(1,len(closes))]
        gains=[d if d>0 else 0 for d in deltas]
        losses=[-d if d<0 else 0 for d in deltas]
        avg_gain=sum(gains[-14:])/14
        avg_loss=sum(losses[-14:])/14
        rsi=100-(100/(1+avg_gain/(avg_loss+0.0001)))
        
        if D>0.6 and 40<rsi<70:
            signals.append((coin,D,rsi))
    
    now=datetime.now().strftime('%H:%M:%S')
    if signals:
        signals.sort(key=lambda x:x[1],reverse=True)
        best=signals[0]
        print(f"[{now}] Layer2 自主交易: 信号={best[0]} D={best[1]:.2f} RSI={best[2]:.0f} ✅买入")
    else:
        print(f"[{now}] Layer2 自主交易: 无信号，继续持有")

# === LAYER 3: 日终报告 (每天21:00) ===
def layer3_daily_report():
    ml, account = get_margin()
    total_btc=float(account['totalAssetOfBtc'])
    liab_btc=float(account['totalLiabilityOfBtc'])
    rb=requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', proxies=PROXIES, timeout=8)
    btc_price=float(rb.json()['price'])
    
    cross={}
    for a in account.get('userAssets',[]):
        free=float(a.get('free',0))
        borrowed=float(a.get('borrowed',0))
        if free>0.0001 or borrowed>0.0001:
            cross[a['asset']]={'free':free,'borrowed':borrowed}
    
    print(f"\n{'='*60}")
    print(f"📊 GG 日终报告 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"保证金率: {ml:.3f}")
    print(f"总资产: ${total_btc*btc_price:.2f}")
    print(f"负债: ${liab_btc*btc_price:.2f}")
    print(f"净收益: ${(total_btc-liab_btc)*btc_price:.2f}")
    print(f"\n持仓:")
    for c,v in cross.items():
        price=get_price(f"{c}USDT")
        val=v['free']*price if price else 0
        print(f"  {c}: {v['free']:.4f}个 ${val:.2f}")

# 主程序
import sys
mode = sys.argv[1] if len(sys.argv)>1 else 'all'

if mode in ['all','layer1']:
    layer1_risk_monitor()
if mode in ['all','layer2']:
    layer2_autonomous_trade()
if mode in ['all','layer3']:
    hour = datetime.now().hour
    if hour == 21:
        layer3_daily_report()
PYEOF
