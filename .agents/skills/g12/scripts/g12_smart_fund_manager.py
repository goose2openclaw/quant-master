#!/usr/bin/env python3
import json, hmac, hashlib, time, subprocess
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
PRICES = {'BTC':95000,'ETH':2800,'SOL':95,'XRP':1.5,'ADA':0.35,'DOGE':0.12,'LINK':12,'USDT':1}

def sign(p): return hmac.new(API_SECRET.encode(), p.encode(), hashlib.sha256).hexdigest()
def curl(url):
    r = subprocess.run(['curl','-s','--proxy',PROXY,'-H','X-MBX-APIKEY: '+API_KEY,url], capture_output=True, text=True, timeout=10)
    return json.loads(r.stdout)

def get_all():
    ts = int(time.time()*1000)
    spot = curl('https://api.binance.com/api/v3/account?timestamp='+str(ts)+'&signature='+sign('timestamp='+str(ts)))
    fut = curl('https://fapi.binance.com/fapi/v2/balance?timestamp='+str(ts)+'&signature='+sign('timestamp='+str(ts)))
    marg = curl('https://api.binance.com/sapi/v1/margin/account?timestamp='+str(ts)+'&signature='+sign('timestamp='+str(ts)))
    spot_usdt = 0
    spot_total = 0
    for b in spot['balances']:
        total = float(b['free'])+float(b['locked'])
        if total > 0:
            spot_total += total * PRICES.get(b['asset'],0)
            if b['asset'] == 'USDT': spot_usdt = total
    contract = 0
    for b in fut:
        if b['asset'] == 'USDT': contract = float(b.get('balance',0))
    margin = float(marg.get('totalCollateralValueInUSDT',0))
    total = spot_total + contract + margin
    return {'spot_total':spot_total,'spot_usdt':spot_usdt,'contract':contract,'margin':margin,'total':total}

def transfer(amount):
    ts = int(time.time()*1000)
    params = 'asset=USDT&amount='+str(amount)+'&type=1&timestamp='+str(ts)+'&recvWindow=5000'
    sig = sign(params)
    return curl('https://api.binance.com/sapi/v1/futures/transfer?'+params+'&signature='+sig)

def manage():
    print('='*50)
    bal = get_all()
    print('Total: $'+str(round(bal['total'],2)))
    print('  Spot USDT: $'+str(round(bal['spot_usdt'],2)))
    print('  Contract: $'+str(round(bal['contract'],2)))
    print('  Margin: $'+str(round(bal['margin'],2)))
    trading = bal['total'] * 0.5
    target = trading * 0.6
    print('Trading capital: $'+str(round(target,2)))
    if bal['contract'] < 30:
        if bal['spot_usdt'] >= 30:
            amt = min(bal['spot_usdt']*0.8, target)
            print('Transfer to contract: $'+str(round(amt,2)))
            r = transfer(round(amt,2))
            if 'tranId' in r: print('Success! TX:'+str(r['tranId']))
            else: print('Failed: '+str(r))
        else:
            print('Need to sell assets for trading')
    else:
        print('Balance OK for trading')
    print('='*50)

if __name__ == '__main__':
    manage()
