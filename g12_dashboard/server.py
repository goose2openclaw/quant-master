#!/usr/bin/env python3
"""G12 Dashboard API Server"""
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"

def sign_params(params):
    import time, hmac, hashlib
    ts = int(time.time() * 1000)
    params['timestamp'] = ts
    params['recvWindow'] = 5000
    query = '&'.join(f"{k}={params[k]}" for k in sorted(params) if k != 'signature')
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query, sig

def get_price(symbol):
    import requests
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(symbol, limit=100):
    import requests, time
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'t':int(k[0]),'o':float(k[1]),'h':float(k[2]),'l':float(k[3]),'c':float(k[4])} for k in r.json()]
    except: return []

class G12Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = {'totalAsset': 1323, 'usdtBalance': 15, 'positions': [], 'signals': []}
            self.wfile.write(json.dumps(data).encode())
        else:
            super().do_GET()

PORT = 8080
server = HTTPServer(('', PORT), G12Handler)
print(f"🚀 G12 Dashboard: http://localhost:{PORT}")
server.serve_forever()
