#!/bin/bash
# GG 自主决策系统 v2.9.4
# 资产盘点 + 仿真 + 自主决策 + 操作
# 日期: 2026-05-06

LOG_FILE="/tmp/gg_autonomous_decision.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "GG 自主决策 $(date '+%Y-%m-%d %H:%M:%S')"
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

def get_margin_data():
    ts=int(time.time()*1000)
    params=f'timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d=r.json()
    ml=float(d.get('marginLevel',0))
    assets={}
    for a in d.get('userAssets',[]):
        free=float(a.get('free',0))
        borrowed=float(a.get('borrowed',0))
        net=free-borrowed
        if abs(net)>0.0001 or borrowed>0.0001:
            assets[a['asset']]={'free':free,'borrowed':borrowed,'net':net}
    return ml,assets

def get_spot_data():
    ts=int(time.time()*1000)
    params=f'timestamp={ts}&recvWindow=5000'
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    d=r.json()
    balances={}
    for b in d.get('balances',[]):
        free=float(b.get('free',0))
        locked=float(b.get('locked',0))
        total=free+locked
        if total>0.0001:
            balances[b['asset']]={'free':free,'locked':locked,'total':total}
    return balances

def simulate_return(config, n=1000):
    """仿真收益"""
    results=[]
    for _ in range(n):
        capital=1000
        for _ in range(90):
            rsi=random.uniform(22,82)
            if rsi<config['rsi_long']:
                capital*=1.07 if random.random()<config['wr_long'] else 0.982
            elif rsi>config['rsi_short']:
                capital*=1.07 if random.random()<config['wr_short'] else 0.982
            else:
                capital*=1.045 if random.random()<0.78 else 0.988
        results.append((capital-1000)/1000*100)
    return sum(results)/len(results)

def main():
    print("\n【1. 资产盘点】")
    prices={'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
            'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
            'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1.0}
    
    spot=get_spot_data()
    margin_ml,margin_assets=get_margin_data()
    
    spot_total=sum(spot.get(a,{}).get('total',0)*prices.get(a,0) for a in spot)
    margin_total=sum(abs(m.get('net',0))*prices.get(a,1) for a,m in margin_assets.items())
    borrow_usdt=margin_assets.get('USDT',{}).get('borrowed',0)
    margin_net=margin_total-borrow_usdt
    total_assets=spot_total+margin_net
    
    print(f"现货: ${spot_total:.2f}")
    print(f"全仓净资产: ${margin_net:.2f}")
    print(f"合并总资产: ${total_assets:.2f}")
    print(f"保证金率: {margin_ml:.3f}")
    
    print("\n【2. 仿真分析】")
    config={'rsi_short':RSI_SHORT,'rsi_long':RSI_LONG,'wr_short':RSI_SHORT_WR,'wr_long':RSI_LONG_WR}
    expected_return=simulate_return(config,500)
    print(f"预期月收益: {expected_return:.0f}%")
    
    print("\n【3. 自主决策】")
    decisions=[]
    
    # 风险判断
    if margin_ml<MARGIN_MIN:
        decisions.append(('STOP','保证金率低于安全线，禁止开仓'))
    elif margin_ml<3.5:
        decisions.append(('CAUTION','保证金率偏低，谨慎操作'))
    else:
        decisions.append(('NORMAL','保证金率正常，可交易'))
    
    # 资金判断
    if total_assets<1000:
        decisions.append(('ADD','资金不足，建议增加本金'))
    elif total_assets<2000:
        decisions.append(('STEADY','资金偏少，稳健操作'))
    else:
        decisions.append(('FULL','资金充足，全力操作'))
    
    for action,msg in decisions:
        print(f"  [{action}] {msg}")
    
    print("\n【4. 执行结果】")
    result={
        'timestamp':datetime.now().isoformat(),
        'spot_total':spot_total,
        'margin_total':margin_total,
        'margin_net':margin_net,
        'total_assets':total_assets,
        'margin_level':margin_ml,
        'expected_return':expected_return,
        'decisions':decisions,
    }
    
    with open('/tmp/gg_decision_result.json','w') as f:
        json.dump(result,f,indent=2)
    
    print("决策完成")
    return result

main()
PYEOF
