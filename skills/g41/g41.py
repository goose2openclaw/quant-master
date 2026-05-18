#!/usr/bin/env python3
"""
G41 - Polymarket增强版
G40策略 + Polymarket预测市场信号
"""

import json, time, urllib.request, hmac, hashlib
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g41.log'

POLYMARKET_SIGNALS = {
    'BTC': 0.42, 'ETH': 0.35, 'SOL': 0.28, 'DOGE': 0.22,
    'XRP': 0.15, 'ADA': 0.12, 'DOT': 0.10, 'LINK': 0.08
}

def api_signed(endpoint, params=None, method='GET'):
    ts = int(time.time() * 1000)
    base = {'timestamp': ts, 'recvWindow': 5000}
    if params: base.update(params)
    q = '&'.join('{}={}'.format(k, v) for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com{}?{}&signature={}'.format(endpoint, q, sig)
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=15).read().decode())

def get_price(symbol):
    try:
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=' + symbol + 'USDT'
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        d = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        return float(d['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=100):
    try:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + symbol + 'USDT&interval=' + interval + '&limit=' + str(limit)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return []

def place_order(symbol, side, quantity):
    try:
        ts = int(time.time() * 1000)
        qty_str = str(int(quantity)) if quantity >= 1 else '{:.6f}'.format(quantity)
        params = {'symbol': symbol + 'USDT', 'side': side, 'type': 'MARKET', 'quantity': qty_str, 'timestamp': ts, 'recvWindow': 5000}
        q = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
        sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = 'https://api.binance.com/api/v3/order?' + q + '&signature=' + sig
        req = urllib.request.Request(url, method='POST')
        req.add_header('X-MBX-APIKEY', API_KEY)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        resp = json.loads(opener.open(req, timeout=10).read().decode())
        if 'code' in resp: return {'success': False, 'error': resp['msg']}
        return {'success': True, 'symbol': symbol}
    except Exception as e: return {'success': False, 'error': str(e)}

def log(msg):
    ts = datetime.now().strftime('%m-%d %H:%M:%S')
    line = '[' + ts + '] ' + msg
    try:
        with open(LOG_FILE, 'a') as f: f.write(line + chr(10))
    except: pass
    print(line, flush=True)

def get_account():
    try:
        ts = int(time.time() * 1000)
        params = {'timestamp': ts, 'recvWindow': 5000}
        q = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
        sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = 'https://api.binance.com/api/v3/account?' + q + '&signature=' + sig
        req = urllib.request.Request(url)
        req.add_header('X-MBX-APIKEY', API_KEY)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(req, timeout=15).read().decode())
    except: return {}

def analyze_symbol(symbol):
    klines = get_klines(symbol)
    if not klines or len(klines) < 50: return None
    closes = [float(k[4]) for k in klines]
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    rs = avg_gain / avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100 / (1 + rs))
    tech_signal = trend * 10 + (rsi - 50) / 50
    pm_signal = POLYMARKET_SIGNALS.get(symbol, 0)
    combined = tech_signal * 0.6 + pm_signal * 0.4
    return {'symbol': symbol, 'tech': tech_signal, 'pm': pm_signal, 'combined': combined,
            'action': 'buy' if combined > 0.2 else 'sell' if combined < -0.1 else 'hold', 'price': closes[-1]}

def main():
    log('=' * 60)
    log('G41 Polymarket增强版启动')
    log('=' * 60)
    
    account = get_account()
    prices = {s: get_price(s) for s in ['BTC','ETH','BNB','XRP','ADA','SOL','DOT','LINK','DOGE','SHIB','NEIRO','BOME']}
    holdings = {}
    for b in account.get('balances', []):
        free = float(b.get('free', 0))
        asset = b['asset']
        if asset != 'USDT' and free > 0:
            price = prices.get(asset, 0)
            value = free * price
            if value > 0.1: holdings[asset] = {'amount': free, 'price': price, 'value': value}
    
    total = sum(h['value'] for h in holdings.values())
    usdt_bal = float([b for b in account.get('balances', []) if b['asset'] == 'USDT'][0]['free'])
    total += usdt_bal
    
    log('总资产: $' + str(round(total, 2)))
    log('USDT: $' + str(round(usdt_bal, 2)))
    log('')
    log('Polymarket信号:')
    for sym, sig in sorted(POLYMARKET_SIGNALS.items()): log('  ' + sym + ': ' + ('+' if sig > 0 else '') + str(round(sig, 2)))
    log('')
    log('综合分析:')
    
    decisions = []
    for sym in ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','DOGE','NEIRO','BOME']:
        result = analyze_symbol(sym)
        if result:
            log('  ' + sym + ': 技术' + str(round(result['tech'],2)) + ' PM' + str(round(result['pm'],2)) + ' 综合' + str(round(result['combined'],2)) + ' => ' + result['action'])
            if result['action'] == 'sell' and sym in holdings and holdings[sym]['value'] > 1:
                decisions.append({'action': 'sell', 'symbol': sym, 'amount': holdings[sym]['amount'] * 0.5})
            elif result['action'] == 'buy' and sym not in holdings and usdt_bal > 5:
                decisions.append({'action': 'buy', 'symbol': sym, 'budget': usdt_bal * 0.1})
    
    log('')
    log('执行决策:')
    for d in decisions[:3]:
        log('  ' + d['action'].upper() + ' ' + d['symbol'])
        if d['action'] == 'sell':
            qty = d['amount']
            result = place_order(d['symbol'], 'SELL', qty)
            log('    结果: ' + ('成功' if result.get('success') else '失败:' + str(result.get('error', ''))))
        elif d['action'] == 'buy':
            price = prices.get(d['symbol'], 0)
            if price > 0:
                qty = d['budget'] / price
                if qty > 0.0001:
                    result = place_order(d['symbol'], 'BUY', qty)
                    log('    结果: ' + ('成功' if result.get('success') else '失败:' + str(result.get('error', ''))))
    
    log('')
    log('G41 启动完成!')

if __name__ == '__main__': main()
