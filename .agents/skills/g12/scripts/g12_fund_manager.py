#!/usr/bin/env python3
import os, hmac, hashlib, time
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
MIN_CONTRACT = 10
MIN_SPOT_RESERVE = 10

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('[' + ts + '] ' + msg)

def get_spot_usdt():
    ts = int(time.time() * 1000)
    q = 'timestamp=' + str(ts)
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com/api/v3/account?' + q + '&signature=' + sig
    cmd = 'curl -s --proxy ' + PROXY + ' -H "X-MBX-APIKEY: ' + API_KEY + '" "' + url + '"'
    result = os.popen(cmd).read()
    try:
        data = json.loads(result)
        for b in data.get('balances', []):
            if b['asset'] == 'USDT':
                return float(b['free']) + float(b['locked'])
    except:
        pass
    return 0

def get_contract_usdt():
    ts = int(time.time() * 1000)
    q = 'timestamp=' + str(ts)
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://fapi.binance.com/fapi/v2/balance?' + q + '&signature=' + sig
    cmd = 'curl -s --proxy ' + PROXY + ' -H "X-MBX-APIKEY: ' + API_KEY + '" "' + url + '"'
    result = os.popen(cmd).read()
    try:
        data = json.loads(result)
        if isinstance(data, list):
            for b in data:
                if b['asset'] == 'USDT':
                    return float(b.get('balance', 0))
    except:
        pass
    return 0

def transfer(asset, amount, typ):
    ts = int(time.time() * 1000)
    q = 'asset=' + asset + '&amount=' + str(amount) + '&type=' + str(typ) + '&timestamp=' + str(ts) + '&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com/sapi/v1/asset/transfer?' + q + '&signature=' + sig
    cmd = 'curl -s --proxy ' + PROXY + ' -X POST -H "X-MBX-APIKEY: ' + API_KEY + '" "' + url + '"'
    result = os.popen(cmd).read()
    log('Transfer response: ' + result[:200])
    return result

def manage():
    import json
    log('=== Fund Manager ===')
    spot = get_spot_usdt()
    contract = get_contract_usdt()
    log('Spot USDT: ' + str(round(spot, 2)))
    log('Contract USDT: ' + str(round(contract, 2)))
    total = spot + contract
    log('Total: ' + str(round(total, 2)))
    
    if contract < MIN_CONTRACT:
        available = spot - MIN_SPOT_RESERVE
        if available > 20:
            amount = min(available, total * 0.5)
            log('Need transfer to contract: ' + str(round(amount, 2)))
            transfer('USDT', round(amount, 2), 3)
    elif contract > MIN_CONTRACT * 5:
        excess = contract - MIN_CONTRACT * 2
        if excess > 20:
            log('Excess in contract, transfer back: ' + str(round(excess, 2)))
            transfer('USDT', round(excess, 2), 4)
    log('=== Done ===')

if __name__ == '__main__':
    import json
    manage()
