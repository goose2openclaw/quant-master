"""
Order UUID Tracking - 全局唯一订单追踪
"""
from typing import Dict
import uuid

class OrderUUIDTracker:
    """
    全交易所订单唯一ID追踪
    跨交易所/跨链订单状态追踪
    """
    def __init__(self):
        self.orders = {}
    
    def generate_uuid(self, symbol: str, exchange: str) -> str:
        """生成唯一订单ID"""
        prefix = f"QM-{exchange[:3].upper()}"
        unique = str(uuid.uuid4())[:8]
        return f"{prefix}-{symbol}-{unique}"
    
    def track_order(self, exchange: str, local_order_id: str, symbol: str,
                   side: str, amount: float, price: float) -> Dict:
        """追踪订单"""
        order_uuid = self.generate_uuid(symbol, exchange)
        
        order_record = {
            'order_uuid': order_uuid,
            'exchange': exchange,
            'local_order_id': local_order_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'status': 'SUBMITTED',
            'created_at': __import__('time').time(),
            'updated_at': __import__('time').time()
        }
        
        self.orders[order_uuid] = order_record
        return order_record
    
    def update_status(self, order_uuid: str, status: str, fill_amount: float = 0):
        """更新状态"""
        if order_uuid in self.orders:
            self.orders[order_uuid]['status'] = status
            self.orders[order_uuid]['fill_amount'] = fill_amount
            self.orders[order_uuid]['updated_at'] = __import__('time').time()
    
    def get_order_status(self, order_uuid: str) -> Dict:
        """获取订单状态"""
        return self.orders.get(order_uuid, {'status': 'NOT_FOUND'})
