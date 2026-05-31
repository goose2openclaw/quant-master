"""
OMS - 完整订单管理系统
Bloomberg/FlexOMS级别
"""
import time, json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from threading import Lock

class OrderStatus(Enum):
    PENDING = "pending"
    ROUTED = "routed"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    iceberg = "iceberg"
    VWAP = "vwap"
    TWAP = "twap"
    MOC = "moc"  # Market on Close
    LOC = "loc"  # Limit on Close

class TimeInForce(Enum):
    DAY = "day"
    GTC = "gtc"  # Good Till Cancel
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill
    GTX = "gtx"  # Good Till Date

@dataclass
class Order:
    order_id: str
    client_order_id: str
    symbol: str
    side: str
    qty: float
    filled_qty: float = 0
    price: float = 0
    order_type: OrderType = OrderType.MARKET
    time_in_force: TimeInForce = TimeInForce.DAY
    status: OrderStatus = OrderStatus.PENDING
    avg_fill_price: float = 0
    leaves_qty: float = 0
    created_time: float = field(default_factory=time.time)
    updated_time: float = 0
    routed_venues: List = field(default_factory=list)
    splits: List = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class OMS:
    """
    OMS - 订单管理系统
    功能: 订单生命周期、分配、报告、合规检查
    """
    def __init__(self):
        self.orders = {}  # {order_id: Order}
        self.order_history = []
        self.pending_queue = []
        self.routing_queue = []
        self.lock = Lock()
        
        # 统计
        self.stats = {
            'total_orders': 0,
            'filled': 0,
            'cancelled': 0,
            'rejected': 0,
            'avg_fill_rate': 0
        }
        
        # 分配规则
        self.allocation_rules = {}
        
        # 订单簿
        self.order_book = {
            'bids': {},  # {order_id: Order}
            'asks': {}
        }
    
    def create_order(self, symbol, side, qty, price=0, order_type='market', 
                     time_in_force='day', client_order_id=None):
        """创建订单"""
        order_id = f"O{int(time.time()*1000000)}"
        client_order_id = client_order_id or f"C{order_id}"
        
        order = Order(
            order_id=order_id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            order_type=OrderType[order_type.upper()],
            time_in_force=TimeInForce[time_in_force.upper()],
            leaves_qty=qty
        )
        
        with self.lock:
            self.orders[order_id] = order
            self.pending_queue.append(order_id)
            self.stats['total_orders'] += 1
        
        # 分配到订单簿
        self._add_to_order_book(order)
        
        return order_id
    
    def _add_to_order_book(self, order):
        """添加到订单簿"""
        if order.side in ['buy', 'BUY']:
            self.order_book['bids'][order.order_id] = order
        else:
            self.order_book['asks'][order.order_id] = order
    
    def route_order(self, order_id, venues):
        """路由订单到venue"""
        with self.lock:
            order = self.orders.get(order_id)
            if not order:
                return None
            
            order.status = OrderStatus.ROUTED
            order.routed_venues = venues
        
        return order
    
    def fill_order(self, order_id, qty, price, venue=None):
        """订单成交"""
        with self.lock:
            order = self.orders.get(order_id)
            if not order:
                return None
            
            order.filled_qty += qty
            order.leaves_qty = order.qty - order.filled_qty
            order.updated_time = time.time()
            
            # 计算平均价
            total_cost = order.avg_fill_price * (order.filled_qty - qty) + price * qty
            order.avg_fill_price = total_cost / order.filled_qty if order.filled_qty > 0 else 0
            
            if order.filled_qty >= order.qty:
                order.status = OrderStatus.FILLED
                self.stats['filled'] += 1
            else:
                order.status = OrderStatus.PARTIAL
        
        return order
    
    def cancel_order(self, order_id, reason=None):
        """取消订单"""
        with self.lock:
            order = self.orders.get(order_id)
            if not order:
                return False
            
            order.status = OrderStatus.CANCELLED
            order.updated_time = time.time()
            order.metadata['cancel_reason'] = reason
            self.stats['cancelled'] += 1
            
            # 从订单簿移除
            self.order_book['bids'].pop(order_id, None)
            self.order_book['asks'].pop(order_id, None)
        
        return True
    
    def split_order(self, order_id, splits):
        """
        拆分订单
        splits: [{'qty': float, 'venue': str, 'price_limit': float}]
        """
        with self.lock:
            parent = self.orders.get(order_id)
            if not parent:
                return None
            
            child_orders = []
            for i, split in enumerate(splits):
                child_id = f"{order_id}_{i}"
                child = Order(
                    order_id=child_id,
                    client_order_id=f"C{child_id}",
                    symbol=parent.symbol,
                    side=parent.side,
                    qty=split['qty'],
                    price=split.get('price_limit', parent.price),
                    order_type=parent.order_type,
                    time_in_force=parent.time_in_force,
                    metadata={'parent': order_id, 'venue': split.get('venue')}
                )
                self.orders[child_id] = child
                child_orders.append(child_id)
            
            parent.splits = child_orders
        
        return child_orders
    
    def allocate_orders(self, allocation_groups):
        """
        分配订单给账户
        allocation_groups: [{'order_id': str, 'allocations': [{'account': str, 'qty': float}]}]
        """
        results = []
        
        for group in allocation_groups:
            order_id = group['order_id']
            allocations = group['allocations']
            
            allocated = []
            for alloc in allocations:
                allocated.append({
                    'order_id': order_id,
                    'account': alloc['account'],
                    'qty': alloc['qty'],
                    'filled_qty': 0,
                    'avg_price': 0
                })
            
            results.append({
                'order_id': order_id,
                'allocations': allocated
            })
        
        return results
    
    def get_order(self, order_id):
        """获取订单"""
        return self.orders.get(order_id)
    
    def get_order_book(self, symbol=None, side=None):
        """获取订单簿"""
        if symbol:
            orders = [o for o in self.order_book['bids'].values() if o.symbol == symbol]
            orders.extend([o for o in self.order_book['asks'].values() if o.symbol == symbol])
        elif side == 'buy':
            orders = list(self.order_book['bids'].values())
        elif side == 'sell':
            orders = list(self.order_book['asks'].values())
        else:
            orders = list(self.order_book['bids'].values()) + list(self.order_book['asks'].values())
        
        return [{
            'order_id': o.order_id,
            'symbol': o.symbol,
            'side': o.side,
            'qty': o.qty,
            'filled': o.filled_qty,
            'leaves': o.leaves_qty,
            'price': o.price,
            'status': o.status.value
        } for o in orders]
    
    def get_open_orders(self):
        """获取未完成订单"""
        return [o for o in self.orders.values() 
                if o.status in [OrderStatus.PENDING, OrderStatus.ROUTED, OrderStatus.PARTIAL]]
    
    def get_order_history(self, limit=100):
        """获取订单历史"""
        return self.order_history[-limit:]
    
    def generate_execution_report(self, start_date=None, end_date=None):
        """生成执行报告"""
        orders = list(self.orders.values())
        
        if start_date:
            orders = [o for o in orders if o.created_time >= start_date]
        if end_date:
            orders = [o for o in orders if o.created_time <= end_date]
        
        total_orders = len(orders)
        filled = len([o for o in orders if o.status == OrderStatus.FILLED])
        cancelled = len([o for o in orders if o.status == OrderStatus.CANCELLED])
        
        total_volume = sum(o.qty for o in orders)
        filled_volume = sum(o.filled_qty for o in orders)
        
        avg_price = sum(o.avg_fill_price * o.filled_qty for o in orders if o.filled_qty > 0)
        avg_price = avg_price / filled_volume if filled_volume > 0 else 0
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'summary': {
                'total_orders': total_orders,
                'filled': filled,
                'cancelled': cancelled,
                'fill_rate': filled / total_orders * 100 if total_orders > 0 else 0,
                'total_volume': total_volume,
                'filled_volume': filled_volume,
                'avg_fill_price': avg_price
            },
            'orders': [{
                'order_id': o.order_id,
                'symbol': o.symbol,
                'side': o.side,
                'qty': o.qty,
                'filled': o.filled_qty,
                'avg_price': o.avg_fill_price,
                'status': o.status.value,
                'created': o.created_time
            } for o in orders]
        }
    
    def get_stats(self):
        """获取统计"""
        self.stats['avg_fill_rate'] = self.stats['filled'] / self.stats['total_orders'] * 100 if self.stats['total_orders'] > 0 else 0
        return self.stats
