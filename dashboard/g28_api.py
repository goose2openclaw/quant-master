#!/usr/bin/env python3
"""
G28 Dashboard API Server
"""
from flask import Flask, jsonify, render_template
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

app = Flask(__name__)

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

def get_price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try: return float(json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())['price'])
    except: return 0

def get_rsi(symbol, period=14):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=50'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        closes = [float(k[4]) for k in data]
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        if avg_loss == 0: return 100
        return 100-(100/(1+avg_gain/avg_loss))
    except: return 50

def get_momentum(symbol):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=25'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        if len(data) < 24: return 0
        old = float(data[-24][4]); new = float(data[-1][4])
        return ((new - old) / old) * 100
    except: return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    holdings = [
        ('USDT', 188.22), ('ETH', 0.0034), ('BNB', 0.0116),
        ('LINK', 1.77), ('SOL', 0.0729), ('UNI', 2.25),
        ('BOME', 505265.0), ('NEIRO', 94506.0), ('TURBO', 56541.0), ('PUMP', 49317.0),
    ]
    
    prices = {c: get_price(f"{c}USDT") for c, _ in holdings}
    
    positions = []
    for coin, amount in holdings:
        if coin == 'USDT': continue
        price = prices.get(coin, 0)
        value = amount * price
        rsi = get_rsi(f"{coin}USDT")
        momentum = get_momentum(f"{coin}USDT")
        
        coin_type = 'Meme' if coin in ['BOME', 'NEIRO', 'TURBO', 'PUMP'] else 'Major'
        buy_thresh = 35 if coin_type == 'Meme' else 40
        sell_thresh = 75 if coin_type == 'Meme' else 70
        
        if rsi < buy_thresh and momentum < -2: decision = 'BUY'
        elif rsi < buy_thresh: decision = 'ADD'
        elif rsi > sell_thresh and momentum > 3: decision = 'SELL'
        elif rsi > sell_thresh - 5: decision = 'REDUCE'
        else: decision = 'HOLD'
        
        positions.append({
            'coin': coin, 'amount': amount, 'value': value,
            'price': price, 'rsi': rsi, 'momentum': momentum,
            'decision': decision, 'type': coin_type
        })
    
    spot_total = sum(a * prices.get(c, 0) for c, a in holdings)
    margin_total = 112.27 * prices.get('LINK', 0) + 0.00052 * prices.get('BTC', 0) + 0.015 * prices.get('ETH', 0)
    futures_balance = 30.0
    total = spot_total + margin_total + futures_balance
    
    signals = {'buy': 0, 'sell': 0, 'hold': 0}
    for p in positions:
        if p['decision'] in ['BUY', 'ADD']: signals['buy'] += 1
        elif p['decision'] in ['SELL', 'REDUCE']: signals['sell'] += 1
        else: signals['hold'] += 1
    
    return jsonify({
        'total': total, 'spot': spot_total, 'margin': margin_total, 'futures': futures_balance,
        'positions': positions, 'signals': signals, 'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, debug=False)
