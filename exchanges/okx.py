"""
OKX 交易所
"""
import hashlib, hmac, base64, time, requests, json
from .exchange import Exchange

class OKXExchange(Exchange):
    """OKX交易所"""
    def __init__(self, api_key, api_secret, passphrase, proxy):
        super().__init__('OKX', api_key, api_secret, proxy)
        self.passphrase = passphrase
        self.base_url = "https://www.okx.com"
    
    def _sign(self, timestamp, method, path, body=''):
        message = timestamp + method + path + body
        mac = hmac.new(self.api_secret.encode(), message.encode(), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()
    
    def _headers(self, path, body=''):
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        sign = self._sign(timestamp, 'GET', path, body)
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': sign,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    def connect(self):
        print(f"[{self.name}] 连接中...")
        self.connected = True
        print(f"[{self.name}] 连接成功")
        return True
    
    def disconnect(self):
        self.connected = False
    
    def get_balance(self):
        """获取余额"""
        try:
            path = '/api/v5/account/balance'
            headers = self._headers(path)
            r = requests.get(f"{self.base_url}{path}", headers=headers, proxies=self.proxy, timeout=10)
            if r.status_code == 200:
                data = r.json().get('data', [{}])[0]
                details = data.get('details', [])
                return {d['ccy']: float(d.get('availBal', 0)) for d in details}
        except Exception as e:
            print(f"[{self.name}] Balance error: {e}")
        return {}
    
    def get_positions(self):
        """获取持仓"""
        positions = {}
        try:
            path = '/api/v5/account/positions'
            headers = self._headers(path)
            r = requests.get(f"{self.base_url}{path}", headers=headers, proxies=self.proxy, timeout=10)
            if r.status_code == 200:
                for p in r.json().get('data', []):
                    sym = p['instId']
                    qty = float(p.get('availPos', 0))
                    if qty > 0:
                        positions[sym] = {'symbol': sym, 'qty': qty}
        except:
            pass
        return positions
    
    def get_ticker(self, symbol):
        """获取Ticker"""
        try:
            symbol = self.normalize_symbol(symbol)
            path = f"/api/v5/market/ticker?instId={symbol}"
            r = requests.get(f"{self.base_url}{path}", proxies=self.proxy, timeout=10)
            if r.status_code == 200:
                d = r.json().get('data', [{}])[0]
                return {
                    'last': float(d.get('last', 0)),
                    'bid': float(d.get('bidPx', 0)),
                    'ask': float(d.get('askPx', 0)),
                    'volume': float(d.get('vol24h', 0))
                }
        except:
            pass
        return None
    
    def get_klines(self, symbol, interval='1m', limit=100):
        """获取K线"""
        try:
            symbol = self.normalize_symbol(symbol)
            path = f"/api/v5/market/candles?instId={symbol}&bar={interval}&limit={limit}"
            r = requests.get(f"{self.base_url}{path}", proxies=self.proxy, timeout=10)
            if r.status_code == 200:
                return [{
                    'time': datetime.fromtimestamp(int(k[0])/1000),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                } for k in r.json().get('data', [])]
        except:
            pass
        return []
    
    def send_order(self, symbol, side, qty, price=None, order_type='MARKET'):
        """下单"""
        try:
            symbol = self.normalize_symbol(symbol)
            path = '/api/v5/trade/order'
            body = json.dumps({
                'instId': symbol,
                'tdMode': 'cash',
                'side': side.lower(),
                'ordType': order_type.lower(),
                'sz': str(qty)
            })
            if price:
                body = json.dumps({
                    'instId': symbol,
                    'tdMode': 'cash',
                    'side': side.lower(),
                    'ordType': 'limit',
                    'sz': str(qty),
                    'px': str(price)
                })
            headers = self._headers(path, body)
            headers['Content-Type'] = 'application/json'
            r = requests.post(f"{self.base_url}{path}", headers=headers, data=body, proxies=self.proxy, timeout=10)
            if r.status_code == 200:
                d = r.json()
                if d.get('code') == '0':
                    return {'success': True, 'order_id': d['data'][0]['ordId']}
            return {'success': False, 'msg': r.text}
        except Exception as e:
            return {'success': False, 'msg': str(e)}
    
    def cancel_order(self, order_id, symbol):
        try:
            path = '/api/v5/trade/cancel-order'
            body = json.dumps({'instId': symbol, 'ordId': order_id})
            headers = self._headers(path, body)
            headers['Content-Type'] = 'application/json'
            r = requests.post(f"{self.base_url}{path}", headers=headers, data=body, proxies=self.proxy, timeout=10)
            return r.status_code == 200
        except:
            return False
    
    def get_order(self, order_id, symbol):
        return None  # 简化实现

from datetime import datetime
