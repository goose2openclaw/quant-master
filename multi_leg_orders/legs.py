"""
Multi-leg Orders - 组合单/价差单
支持: 跨式组合/价差组合/比率组合
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class LegSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class LegType(Enum):
    LONG = "LONG"  # 做多腿
    SHORT = "SHORT"  # 做空腿

@dataclass
class OrderLeg:
    symbol: str
    side: LegSide
    qty: float
    leg_type: LegType  # 相对于组合
    ratio: float = 1.0  # 数量比率

class MultiLegOrder:
    """组合单"""
    def __init__(self, order_id, legs, order_type='SPREAD'):
        self.order_id = order_id
        self.legs = legs  # List[OrderLeg]
        self.order_type = order_type
        self.status = 'pending'
        self.filled_legs = []
        self.avg_prices = {}
    
    def get_net_delta(self):
        """净Delta"""
        delta = 0
        for leg in self.legs:
            qty = leg.qty * leg.ratio
            if leg.leg_type == LegType.LONG:
                delta += qty
            else:
                delta -= qty
        return delta

class SpreadOrderManager:
    """
    组合单管理器
    支持: 跨式/价差/比率/箱式
    """
    def __init__(self, order_manager):
        self.order_manager = order_manager
        self.active_orders = {}
    
    def create_straddle(self, symbol, qty, strike_price=None):
        """
        创建跨式组合
        同时买入/卖出 同执行价Call和Put
        """
        order_id = f"STRADDLE_{int(time.time()*1000)}"
        
        legs = [
            OrderLeg(symbol, LegSide.BUY, qty, LegType.LONG, 1.0),  # Call
            OrderLeg(symbol, LegSide.BUY, qty, LegType.SHORT, 1.0)  # Put
        ]
        
        order = MultiLegOrder(order_id, legs, 'STRADDLE')
        self.active_orders[order_id] = order
        return order_id
    
    def create_strangle(self, symbol, call_qty, put_qty, call_strike, put_strike):
        """
        创建宽跨式组合
        买入不同执行价的Call和Put
        """
        order_id = f"STRANGLE_{int(time.time()*1000)}"
        
        legs = [
            OrderLeg(symbol, LegSide.BUY, call_qty, LegType.LONG, 1.0),
            OrderLeg(symbol, LegSide.BUY, put_qty, LegType.SHORT, 1.0)
        ]
        
        order = MultiLegOrder(order_id, legs, 'STRANGLE')
        self.active_orders[order_id] = order
        return order_id
    
    def create_vertical_spread(self, symbol, qty, leg1_side, leg2_side, strike1, strike2):
        """
        创建垂直价差
        同标的不同执行价
        """
        order_id = f"VERTICAL_{int(time.time()*1000)}"
        
        legs = [
            OrderLeg(symbol, leg1_side, qty, LegType.LONG if leg1_side == LegSide.BUY else LegType.SHORT, 1.0),
            OrderLeg(symbol, leg2_side, qty, LegType.SHORT if leg2_side == LegSide.BUY else LegType.LONG, 1.0)
        ]
        
        order = MultiLegOrder(order_id, legs, 'VERTICAL_SPREAD')
        self.active_orders[order_id] = order
        return order_id
    
    def create_ratio_spread(self, symbol, qty1, qty2, leg1_side, leg2_side, ratio=2):
        """
        创建比率价差
        腿之间数量比率不同
        """
        order_id = f"RATIO_{int(time.time()*1000)}"
        
        legs = [
            OrderLeg(symbol, leg1_side, qty1, LegType.LONG if leg1_side == LegSide.BUY else LegType.SHORT, 1.0),
            OrderLeg(symbol, leg2_side, qty2, LegType.SHORT if leg2_side == LegSide.BUY else LegType.LONG, ratio)
        ]
        
        order = MultiLegOrder(order_id, legs, 'RATIO_SPREAD')
        self.active_orders[order_id] = order
        return order_id
    
    def create_butterfly(self, symbol, qty, strikes=[95, 100, 105], ratio=1):
        """
        创建蝶式价差
        3个执行价,外侧卖出中间买入
        """
        order_id = f"BUTTERFLY_{int(time.time()*1000)}"
        
        legs = [
            OrderLeg(symbol, LegSide.SELL, qty, LegType.SHORT, ratio),
            OrderLeg(symbol, LegSide.BUY, qty * 2, LegType.LONG, 1.0),
            OrderLeg(symbol, LegSide.SELL, qty, LegType.SHORT, ratio)
        ]
        
        order = MultiLegOrder(order_id, legs, 'BUTTERFLY')
        self.active_orders[order_id] = order
        return order_id
    
    def execute_order(self, order_id):
        """执行组合单"""
        order = self.active_orders.get(order_id)
        if not order:
            return {'success': False, 'error': 'Order not found'}
        
        results = []
        
        for leg in order.legs:
            result = self.order_manager.send_order(
                symbol=leg.symbol,
                side=leg.side.value,
                qty=leg.qty * leg.ratio
            )
            results.append(result)
            
            if result.get('success'):
                order.filled_legs.append(leg)
                order.avg_prices[leg.symbol] = result.get('price', 0)
        
        if len(order.filled_legs) == len(order.legs):
            order.status = 'filled'
        elif len(order.filled_legs) > 0:
            order.status = 'partial'
        else:
            order.status = 'rejected'
        
        return {
            'success': order.status == 'filled',
            'order_id': order_id,
            'status': order.status,
            'results': results
        }
    
    def cancel_order(self, order_id):
        """取消组合单"""
        order = self.active_orders.get(order_id)
        if not order:
            return False
        
        # 取消所有腿
        for leg in order.legs:
            if leg in order.filled_legs:
                self.order_manager.cancel_order(leg.symbol)
        
        order.status = 'cancelled'
        return True
    
    def get_order_status(self, order_id):
        """获取订单状态"""
        order = self.active_orders.get(order_id)
        if not order:
            return None
        
        return {
            'order_id': order_id,
            'type': order.order_type,
            'status': order.status,
            'legs': [{
                'symbol': leg.symbol,
                'side': leg.side.value,
                'qty': leg.qty,
                'filled': leg in order.filled_legs
            } for leg in order.legs],
            'net_delta': order.get_net_delta()
        }

import time
