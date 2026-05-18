#!/usr/bin/env python3
"""
G41 - Polymarket增强版
======================
G40策略 + Polymarket预测市场信号

版本: 1.0
日期: 2026-05-18
"""

import json, time, urllib.request, hmac, hashlib, os
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g41.log'

# Polymarket信号 (模拟)
POLYMARKET_SIGNALS = {
    'BTC': 0.42,
    'ETH': 0.35,
    'SOL': 0.28,
    'DOGE': 0.22,
    'XRP': 0.15,
    'ADA': 0.12,
    'DOT': 0.10,
    'LINK': 0.08
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

def get_account():
    try:
        account = api_signed('/api/v3/account')
        prices = {s: get_price(s) for s in ['BTC','ETH','BNB','XRP','ADA','SOL','DOT','LINK','DOGE','SHIB','NEIRO','BOME']}
        usdt = 0
        total = 0
        holdings = {}
        for b in account.get('balances', []):
            free = float(b.get('free', 0))
            asset = b['asset']
            if asset == 'USDT':
                usdt = free
                total += free
            else:
                price = prices.get(asset, 0)
                value = free * price
                total += value
                if value > 0.1:
                    holdings[asset] = {'amount': free, 'price': price, 'value': value}
        return holdings, usdt, total
    except: return {}, 0, 0

def log(msg):
    ts = datetime.now().strftime('%m-%d %H:%M:%S')
    line = '[{}] {}'.format(ts, msg)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + chr(10))
            f.flush()
    except: pass
    print(line, flush=True)

def analyze_symbol(symbol):
    klines = get_klines(symbol)
    if not klines or len(klines) < 50:
        return None
    
    closes = [float(k[4]) for k in klines]
    
    # 技术信号
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
    
    # Polymarket信号
    pm_signal = POLYMARKET_SIGNALS.get(symbol, 0)
    
    # 综合信号 = 技术60% + PM40%
    combined = tech_signal * 0.6 + pm_signal * 0.4
    
    return {
        'symbol': symbol,
        'tech': tech_signal,
        'pm': pm_signal,
        'combined': combined,
        'action': 'buy' if combined > 0.2 else 'sell' if combined < -0.1 else 'hold',
        'price': closes[-1]
    }

def run():
    log('=' * 60)
    log('G41 Polymarket增强版 启动')
    log('=' * 60)
    
    holdings, usdt, total = get_account()
    log('总资产: ${:.2f} USDT: ${:.2f}'.format(total, usdt))
    
    log('
Polymarket信号:')
    for sym, sig in POLYMARKET_SIGNALS.items():
        log('  {}: {:+.2f}'.format(sym, sig))
    
    log('
综合分析:')
    symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'DOGE', 'NEIRO', 'BOME']
    
    for sym in symbols:
        result = analyze_symbol(sym)
        if result:
            log('  {}: 技术{:+.2f} PM{:+.2f} 综合{:+.2f} {}'.format(
                sym, result['tech'], result['pm'], result['combined'], result['action']))

if __name__ == '__main__':
    run()
