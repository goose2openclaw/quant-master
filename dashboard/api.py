#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, json, time, hmac, hashlib

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
MEME_COINS = {'BOME', 'PUMP', 'NEIRO', 'TURBO', 'DOGE', 'SHIB', 'PEPE'}

def proxy_get(url, timeout=5):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    return json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=timeout).read().decode())

def signed_get(endpoint, timeout=5):
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    return json.loads(urllib.request.build_opener(proxy_handler).open(req, timeout=timeout).read().decode())

def futures_get(timeout=5):
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v2/balance?{q}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    return json.loads(urllib.request.build_opener(proxy_handler).open(req, timeout=timeout).read().decode())

def get_all_account_data():
    holdings = []
    total_spot = 0
    total_cross = 0
    total_isolated = 0
    total_futures = 0
    
    # 现货账户
    try:
        account = signed_get("/api/v3/account", timeout=8)
        for b in account.get('balances', []):
            free = float(b.get('free', 0))
            if free > 0.0001:
                if b['asset'] == 'USDT':
                    holdings.append({'coin': 'USDT', 'amount': free, 'price': 1, 'value': free, 'type': 'cash', 'account': 'spot'})
                    total_spot += free
                else:
                    try:
                        p = float(proxy_get(f'https://api.binance.com/api/v3/ticker/price?symbol={b["asset"]}USDT', timeout=5)['price'])
                        v = free * p
                        holdings.append({'coin': b['asset'], 'amount': free, 'price': p, 'value': v, 'type': 'meme' if b['asset'] in MEME_COINS else 'major', 'account': 'spot'})
                        total_spot += v
                    except: pass
    except Exception as e:
        pass
    
    # 全仓杠杆
    try:
        cross = signed_get("/sapi/v1/margin/account", timeout=8)
        for b in cross.get('userAssets', []):
            free = float(b.get('free', 0))
            net = free - float(b.get('borrowed', 0)) - float(b.get('interest', 0))
            if abs(net) > 0.0001:
                try:
                    p = float(proxy_get(f'https://api.binance.com/api/v3/ticker/price?symbol={b["asset"]}USDT', timeout=5)['price'])
                    v = abs(net) * p
                    holdings.append({'coin': b['asset'], 'amount': abs(net), 'price': p, 'value': v, 'type': 'meme' if b['asset'] in MEME_COINS else 'major', 'account': 'cross'})
                    total_cross += v
                except: pass
    except: pass
    
    # 逐仓
    try:
        isolated = signed_get("/sapi/v1/margin/isolated/account", timeout=8)
        for pair in isolated.get('assets', []):
            for b in pair.get('assets', []):
                free = float(b.get('free', 0))
                if free > 0.0001:
                    try:
                        p = float(proxy_get(f'https://api.binance.com/api/v3/ticker/price?symbol={b["asset"]}USDT', timeout=5)['price'])
                        v = free * p
                        holdings.append({'coin': b['asset'], 'amount': free, 'price': p, 'value': v, 'type': 'meme' if b['asset'] in MEME_COINS else 'major', 'account': 'isolated'})
                        total_isolated += v
                    except: pass
    except: pass
    
    # 合约
    try:
        fut = futures_get(timeout=8)
        for b in fut:
            if float(b.get('availableBalance', 0)) > 0.01:
                if b['asset'] == 'USDT':
                    total_futures += float(b['availableBalance'])
    except: pass
    
    grand_total = total_spot + total_cross + total_isolated + total_futures
    
    return {
        'spot': total_spot,
        'cross': total_cross,
        'isolated': total_isolated,
        'futures': total_futures,
        'total': grand_total,
        'holdings': sorted(holdings, key=lambda x: x['value'], reverse=True)[:20]
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/data':
            try:
                data = get_all_account_data()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8091), Handler)
    print('API running on 8091')
    server.serve_forever()
