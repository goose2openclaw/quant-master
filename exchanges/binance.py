"""
Binance 交易所
"""
import hashlib, hmac, time, requests
from .exchange import Exchange

class BinanceExchange(Exchange):
    """Binance现货交易所"""
    def __init__(self, api_key, api_secret, proxy):
        super().__init__('Binance', api_key, api_secret, proxy)
        self.base_url = "https://api.binance.com"
        self.precision = {}  # 精度缓存
    
    def connect(self):
        print(f"[{self.name}] 连接中...")
        self.connected = True
        print(f"[{self.name}] 连接成功")
        return True
    
    def disconnect(self):
        self.connected = False
        print(f"[{self.name}] 已断开")
    
    def _sign(self, params):
        """签名"""
        params['timestamp'] = int(time.time() * 1000)
        params['recvWindow'] = 5000
        q_str = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
        sig = hmac.new(self.api_secret.encode(), q_str.encode(), hashlib.sha256).hexdigest()
        return f"{q_str}&signature={sig}"
    
    def _get_precision(self, symbol):
        """获取精度"""
        if symbol not in self.precision:
            try:
                r = requests.get(
                    f"{self.base_url}/api/v3/exchangeInfo",
                    proxies=self.proxy, timeout=10
                )
                for s in r.json().get('symbols', []):
                    if s['symbol'] == symbol:
                        for f in s['filters']:
                            if f['filterType'] == 'LOT_SIZE':
                                self.precision[symbol] = f['stepSize']
                        break
            except:
                self.precision[symbol] = '0.00001'
        return float(self.precision.get(symbol, '0.00001'))
    
    def get_balance(self):
        """获取余额"""
        try:
            signed = self._sign({})
            r = requests.get(
                f"{self.base_url}/api/v3/account?{signed}",
                headers={"X-MBX-APIKEY": self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                balances = {b['asset']: float(b['free']) + float(b['locked']) 
                          for b in data['balances']}
                return balances
        except Exception as e:
            print(f"[{self.name}] Balance error: {e}")
        return {}
    
    def get_positions(self):
        """获取持仓"""
        positions = {}
        balances = self.get_balance()
        for asset, qty in balances.items():
            if qty > 0 and asset != 'USDT':
                ticker = self.get_ticker(asset + 'USDT')
                if ticker:
                    price = ticker.get('last', 0)
                    positions[asset] = {
                        'symbol': asset,
                        'qty': qty,
                        'value': qty * price,
                        'avg_price': price
                    }
        return positions
    
    def get_ticker(self, symbol):
        """获取Ticker"""
        try:
            symbol = self.normalize_symbol(symbol)
            r = requests.get(
                f"{self.base_url}/api/v3/ticker/24hr",
                params={"symbol": symbol},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                d = r.json()
                return {
                    'symbol': symbol,
                    'last': float(d['lastPrice']),
                    'bid': float(d['bidPrice']),
                    'ask': float(d['askPrice']),
                    'volume': float(d['volume']),
                    'quote_volume': float(d['quoteVolume']),
                    'change_24h': float(d['priceChange']),
                    'change_pct_24h': float(d['priceChangePercent'])
                }
        except Exception as e:
            print(f"[{self.name}] Ticker error: {e}")
        return None
    
    def get_klines(self, symbol, interval='1m', limit=100):
        """获取K线"""
        try:
            symbol = self.normalize_symbol(symbol)
            r = requests.get(
                f"{self.base_url}/api/v3/klines",
                params={"symbol": symbol, "interval": interval, "limit": limit},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                return [{
                    'time': datetime.fromtimestamp(k[0]/1000),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                } for k in r.json()]
        except Exception as e:
            print(f"[{self.name}] Klines error: {e}")
        return []
    
    def send_order(self, symbol, side, qty, price=None, order_type='MARKET'):
        """下单"""
        try:
            symbol = self.normalize_symbol(symbol)
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': str(round(qty, 8))
            }
            if order_type.upper() == 'LIMIT' and price:
                params['price'] = str(price)
                params['timeInForce'] = 'GTC'
            
            signed = self._sign(params)
            r = requests.post(
                f"{self.base_url}/api/v3/order?{signed}",
                headers={"X-MBX-APIKEY": self.api_key},
                proxies=self.proxy, timeout=10
            )
            data = r.json()
            if 'orderId' in data:
                return {
                    'success': True,
                    'order_id': str(data['orderId']),
                    'symbol': symbol,
                    'side': side,
                    'qty': float(data['executedQty']),
                    'price': float(data.get('price', 0))
                }
            return {'success': False, 'msg': data.get('msg', 'Unknown')}
        except Exception as e:
            return {'success': False, 'msg': str(e)}
    
    def cancel_order(self, order_id, symbol):
        """取消订单"""
        try:
            symbol = self.normalize_symbol(symbol)
            params = {'symbol': symbol, 'orderId': order_id}
            signed = self._sign(params)
            r = requests.delete(
                f"{self.base_url}/api/v3/order?{signed}",
                headers={"X-MBX-APIKEY": self.api_key},
                proxies=self.proxy, timeout=10
            )
            return r.status_code == 200
        except:
            return False
    
    def get_order(self, order_id, symbol):
        """查询订单"""
        try:
            symbol = self.normalize_symbol(symbol)
            params = {'symbol': symbol, 'orderId': order_id}
            signed = self._sign(params)
            r = requests.get(
                f"{self.base_url}/api/v3/order?{signed}",
                headers={"X-MBX-APIKEY": self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                d = r.json()
                return {
                    'order_id': str(d['orderId']),
                    'symbol': d['symbol'],
                    'side': d['side'],
                    'qty': float(d['origQty']),
                    'filled': float(d['executedQty']),
                    'status': d['status'],
                    'price': float(d.get('price', 0))
                }
        except:
            pass
        return None

from datetime import datetime
