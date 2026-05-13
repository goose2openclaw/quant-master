#!/usr/bin/env python3
import requests, hmac, hashlib, time

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def sign(params):
    params['recvWindow'] = 5000
    params['timestamp'] = int(time.time()*1000)
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + '&signature=' + sig

def get_positions():
    url = 'https://fapi.binance.com/fapi/v2/positionRisk'
    r = requests.get(url + '?' + sign({}), 
                    headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

def get_account():
    url = 'https://fapi.binance.com/fapi/v2/account'
    r = requests.get(url + '?' + sign({}), 
                    headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

print("持仓检查:")
positions = get_positions()
active = [p for p in positions if float(p.get('positionAmt', 0)) != 0]
if active:
    for p in active:
        print(f"  {p['symbol']}: {p['positionAmt']} 浮亏:{p['unrealizedProfit']}")
else:
    print("  无持仓")

print("\n账户:")
acc = get_account()
print(f"  总资产: ${float(acc.get('totalMarginBalance', 0)):.2f}")
print(f"  可用: ${float(acc.get('availableBalance', 0)):.2f}")
