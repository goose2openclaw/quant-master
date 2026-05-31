"""
Bybit 交易所
"""
import hashlib, hmac, time, requests, json
from .exchange import Exchange

class BybitExchange(Exchange):
    """Bybit交易所"""
    def __init__(self, api_key, api_secret, proxy):
        super().__init__('Bybit', api_key, api_secret, proxy)
        self.base_url = "https://api.bybit.com"
    
    def _sign(self, params):
        param_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
        return hmac.new(self.api_secret.encode(), param_str.encode(), hashlib.sha256).hexdigest()
    
    def connect(self):
        print(f"[{self.name}] 连接中...")
        self.connected = True
        print(f"[{self.name}] 连接成功")
        return True
    
    def disconnect(self):
        self.connected = False
    
    def get_balance(self):
        try:
            params = {'category': 'spot', 'timestamp': int(time.time()*1000)}
            params['sign'] = self._sign(params)
            r = requests.get(f"{self.base_url}/v5/account/wallet-balance", 
                           params=params, headers={'X-BAPI-API-KEY': self.api_key}, 
                           proxies=self.proxy, timeout=10)
            if r.status_code == 200:
                data = r.json().get('result', {}).get('list', [{}])[0]
                coins = data.get('coin', [])
                return {c['coin']: float(c.get('availableToWithdraw', 0)) for c in coins}
        except:
            pass
        return {}
    
    def get_positions(self):
        return {}  # 简化
    
    def get_ticker(self, symbol):
        try:
            r = requests.get(f"{self.base_url}/v5/market/ticker",
                           params={'category': 'spot', 'symbol': symbol.upper()},
                           proxies=self.proxy, timeout=10)
            if r.status_code == 200:
                d = r.json().get('result', {}).get('list', [{}])[0]
                return {'last': float(d.get('lastPrice', 0)), 'volume': float(d.get('volume24h', 0))}
        except:
            pass
        return None
    
    def get_klines(self, symbol, interval='1', limit=100):
        try:
            interval_map = {'1m': '1', '5m': '5', '15m': '15', '1h': '60', '1d': 'D'}
            r = requests.get(f"{self.base_url}/v5/market/kline",
                           params={'category': 'spot', 'symbol': symbol.upper(), 
                                  'interval': interval_map.get(interval, '1'), 'limit': limit},
                           proxies=self.proxy, timeout=10)
            if r.status_code == 200:
                return [{'time': datetime.fromtimestamp(int(k[0])/1000),
                        'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]),
                        'close': float(k[4]), 'volume': float(k[5])} 
                       for k in r.json().get('result', {}).get('list', [])]
        except:
            pass
        return []
    
    def send_order(self, symbol, side, qty, price=None, order_type='MARKET'):
        return {'success': False, 'msg': 'Not implemented'}
    
    def cancel_order(self, order_id, symbol):
        return False
    
    def get_order(self, order_id, symbol):
        return None

from datetime import datetime
