"""
交易引擎 - QMT快捷交易 + vnpy引擎
"""
from .event import EventEngine, Event

class Order:
    """订单"""
    def __init__(self, symbol, side, qty, price=None, order_type='MARKET'):
        self.symbol = symbol
        self.side = side  # BUY/SELL
        self.qty = qty
        self.price = price
        self.type = order_type
        self.order_id = None
        self.status = 'pending'
        self.filled_qty = 0
        self.avg_price = 0

class TradingEngine:
    """
    交易引擎 - QMT快捷交易功能 + vnpy架构
    """
    def __init__(self, event_engine):
        self.event_engine = event_engine
        self.positions = {}  # {symbol: {'qty': 0, 'avg_price': 0}}
        self.orders = {}    # {order_id: Order}
        self.balance = 0
        self.gateway = None
    
    def set_gateway(self, gateway):
        """设置交易通道"""
        self.gateway = gateway
    
    def send_order(self, symbol, side, qty, price=None, order_type='MARKET'):
        """快捷下单 - QMT风格"""
        order = Order(symbol, side, qty, price, order_type)
        order.order_id = self._generate_id()
        
        # 发送订单事件
        self.event_engine.put(Event('order', {
            'order': order,
            'action': 'send'
        }))
        
        # 通过网关发送
        if self.gateway:
            result = self.gateway.send_order(order)
            if result['success']:
                order.status = 'submitted'
                self.orders[order.order_id] = order
        
        return order
    
    def cancel_order(self, order_id):
        """取消订单"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if self.gateway:
                result = self.gateway.cancel_order(order_id)
                if result['success']:
                    order.status = 'cancelled'
            return True
        return False
    
    def basket_order(self, orders):
        """篮子交易 - QMT核心功能"""
        results = []
        for o in orders:
            order = self.send_order(o['symbol'], o['side'], o['qty'])
            results.append(order)
        return results
    
    def get_position(self, symbol):
        """获取持仓"""
        return self.positions.get(symbol, {'qty': 0, 'avg_price': 0})
    
    def get_all_positions(self):
        """获取所有持仓"""
        return self.positions
    
    def _generate_id(self):
        """生成订单ID"""
        import time
        return f"QM{int(time.time()*1000)}"
    
    def update_position(self, symbol, qty, avg_price):
        """更新持仓"""
        self.positions[symbol] = {'qty': qty, 'avg_price': avg_price}
