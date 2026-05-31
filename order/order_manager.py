"""订单管理器"""
import hashlib, hmac, time, requests
from enum import Enum
from threading import Lock

class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class Order:
    def __init__(self, symbol, side, qty, price=None, order_type='MARKET'):
        self.order_id = None
        self.client_id = f"QM{int(time.time()*1000)}"
        self.symbol = symbol
        self.side = side
        self.qty = qty
        self.price = price
        self.type = order_type
        self.status = OrderStatus.PENDING
        self.filled_qty = 0
        self.avg_price = 0
        self.create_time = time.time()
        self.update_time = time.time()
        self.error = None

class OrderManager:
    def __init__(self, api_key, api_secret, proxy):
        self.api_key = api_key
        self.api_secret = api_secret
        self.proxy = proxy
        self.orders = {}
        self.lock = Lock()
        self.max_retry = 3
    
    def send_order(self, symbol, side, qty, price=None, order_type='MARKET'):
        order = Order(symbol, side, qty, price, order_type)
        for attempt in range(self.max_retry):
            try:
                result = self._submit_order(order)
                if result['success']:
                    order.order_id = result['order_id']
                    order.status = OrderStatus.SUBMITTED
                    with self.lock:
                        self.orders[order.order_id] = order
                    return order
                time.sleep(1)
            except Exception as e:
                order.error = str(e)
                time.sleep(1)
        order.status = OrderStatus.REJECTED
        return order
    
    def _submit_order(self, order):
        ts = int(time.time() * 1000)
        params = {
            'symbol': order.symbol + 'USDT',
            'side': order.side,
            'type': order.type,
            'quantity': str(order.qty),
            'timestamp': ts,
            'recvWindow': 5000
        }
        q_str = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
        sig = hmac.new(self.api_secret.encode(), q_str.encode(), hashlib.sha256).hexdigest()
        url = f"https://api.binance.com/api/v3/order?{q_str}&signature={sig}"
        r = requests.post(url, headers={'X-MBX-APIKEY': self.api_key}, proxies=self.proxy, timeout=10)
        data = r.json()
        if 'orderId' in data:
            return {'success': True, 'order_id': str(data['orderId'])}
        return {'success': False, 'msg': data.get('msg', 'Error')}
    
    def cancel_order(self, order_id):
        ts = int(time.time() * 1000)
        params = f"symbol=BTCUSDT&orderId={order_id}&timestamp={ts}&recvWindow=5000"
        sig = hmac.new(self.api_secret.encode(), params.encode(), hashlib.sha256).hexdigest()
        url = f"https://api.binance.com/api/v3/order?{params}&signature={sig}"
        r = requests.delete(url, headers={'X-MBX-APIKEY': self.api_key}, proxies=self.proxy, timeout=10)
        if r.status_code == 200:
            with self.lock:
                if order_id in self.orders:
                    self.orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False
    
    def get_all_orders(self):
        with self.lock:
            return list(self.orders.values())
