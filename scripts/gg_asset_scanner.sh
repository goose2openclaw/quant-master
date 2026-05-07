#!/bin/bash
# GG 资产扫描器 v2.9.4
# 自主资产盘点、复盘、仿真、决策
# 日期: 2026-05-06

LOG_FILE="/tmp/gg_asset_scanner.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "GG 资产扫描 $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, random
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def get_price(sym):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_spot_balance():
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

def get_margin_balance():
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
    return ml, assets

def analyze_and_decide():
    """自主分析和决策"""
    prices={'BTC':get_price('BTCUSDT'),'ETH':get_price('ETHUSDT'),'BNB':get_price('BNBUSDT'),
            'SOL':get_price('SOLUSDT'),'XRP':get_price('XRPUSDT'),'ADA':get_price('ADAUSDT'),
            'DOGE':get_price('DOGEUSDT'),'LINK':get_price('LINKUSDT'),'USDT':1.0,'ORDI':get_price('ORDIUSDT')}
    
    spot=get_spot_balance()
    margin_ml,margin_assets=get_margin_balance()
    
    # 计算现货总值
    spot_total=sum(spot.get(a,{}).get('total',0)*prices.get(a,0) for a in spot)
    margin_total=sum(abs(m.get('net',0))*prices.get(a,1) for a,m in margin_assets.items())
    borrow_usdt=margin_assets.get('USDT',{}).get('borrowed',0)
    margin_net=margin_total-borrow_usdt
    
    total_assets=spot_total+margin_net
    
    result={
        'timestamp':datetime.now().isoformat(),
        'spot_wallet':spot_total,
        'margin_wallet':margin_total,
        'margin_net':margin_net,
        'borrow':borrow_usdt,
        'total_assets':total_assets,
        'margin_level':margin_ml,
        'decisions':[],
        'alerts':[],
    }
    
    # 风险分析
    if margin_ml<3.0:
        result['alerts'].append({'type':'danger','msg':f'保证金率{margin_ml:.3f}低于安全线3.0'})
    elif margin_ml<3.5:
        result['alerts'].append({'type':'warning','msg':f'保证金率{margin_ml:.3f}偏低'})
    
    # 收益分析
    if total_assets<1000:
        result['decisions'].append({'action':'warning','msg':'资金不足，建议增加本金'})
    elif total_assets<2000:
        result['decisions'].append({'action':'caution','msg':'资金偏少，稳健操作'})
    else:
        result['decisions'].append({'action':'normal','msg':'资金充足，可正常交易'})
    
    # 仓位分析
    if margin_total/total_assets>0.5:
        result['alerts'].append({'type':'warning','msg':'杠杆仓位过重'})
    
    return result

# 执行扫描
result=analyze_and_decide()

print(f"\n【资产扫描结果】")
print(f"时间: {result['timestamp']}")
print(f"现货钱包: ${result['spot_wallet']:.2f}")
print(f"全仓总额: ${result['margin_wallet']:.2f}")
print(f"全仓借款: ${result['borrow']:.2f}")
print(f"全仓净资产: ${result['margin_net']:.2f}")
print(f"合并总资产: ${result['total_assets']:.2f}")
print(f"保证金率: {result['margin_level']:.3f}")

if result['alerts']:
    print(f"\n【预警】")
    for a in result['alerts']:
        print(f"  {a['type']}: {a['msg']}")

if result['decisions']:
    print(f"\n【决策】")
    for d in result['decisions']:
        print(f"  {d['action']}: {d['msg']}")

# 保存结果
with open('/tmp/gg_asset_scan_result.json','w') as f:
    json.dump(result,f,indent=2)

print(f"\n扫描完成")
PYEOF
