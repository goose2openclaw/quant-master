#!/usr/bin/env python3
"""G12 Dashboard Server with API"""
import http.server
import socketserver
import json
import os
import urllib.request
import hmac
import hashlib
import time

API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"
PROXY = "http://172.29.144.1:7897"

def api_request(url):
    headers = {"X-MBX-APIKEY": API_KEY}
    req = urllib.request.Request(url, headers=headers)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_spot():
    ts = int(time.time() * 1000)
    q = "timestamp=" + str(ts)
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = "https://api.binance.com/api/v3/account?" + q + "&signature=" + sig
    data = api_request(url)
    if "error" in data: return {}
    return {b["asset"]: {"free": float(b["free"]), "locked": float(b["locked"]), "total": float(b["free"])+float(b["locked"])} for b in data.get("balances", []) if float(b["free"])+float(b["locked"]) > 0}

def get_margin():
    ts = int(time.time() * 1000)
    q = "timestamp=" + str(ts)
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = "https://api.binance.com/api/v3/margin/account?" + q + "&signature=" + sig
    data = api_request(url)
    if "error" in data: return {}
    return {"totalCollateralValue": data.get("totalCollateralValue", "0"), "marginLevel": data.get("marginLevel", "0")}

def get_futures():
    ts = int(time.time() * 1000)
    q = "timestamp=" + str(ts)
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = "https://fapi.binance.com/fapi/v2/balance?" + q + "&signature=" + sig
    data = api_request(url)
    if "error" in data: return {}
    return {b["asset"]: {"balance": float(b["balance"]), "availableBalance": float(b["availableBalance"])} for b in data if float(b["balance"]) > 0}

def get_trades():
    """从交易日志读取真实交易记录"""
    try:
        with open('/tmp/g12_plus_trades.json', 'r') as f:
            trades = json.load(f)
        # 只返回最近20条
        return trades[-20:] if len(trades) > 20 else trades
    except:
        return []

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/g12_data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            result = {
                "spot": get_spot(), 
                "margin": get_margin(), 
                "futures": get_futures(),
                "trades": get_trades()
            }
            self.wfile.write(json.dumps(result).encode())
        else:
            super().do_GET()

PORT = 8081
os.chdir('/home/goose/.openclaw/workspace/g12_webui')
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server running at http://localhost:{PORT}")
    httpd.serve_forever()
