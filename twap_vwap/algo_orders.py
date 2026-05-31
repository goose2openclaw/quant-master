"""
TWAP/VWAP 算法订单
时间加权/成交量加权下单
"""
import time
from enum import Enum

class AlgoType(Enum):
    TWAP = "TWAP"
    VWAP = "VWAP"
    POV = "POV"  # Percentage of Volume

class AlgoOrder:
    """算法订单"""
    def __init__(self, symbol, side, total_qty, algo_type, duration_sec, params=None):
        self.symbol = symbol
        self.side = side
        self.total_qty = total_qty
        self.algo_type = algo_type
        self.duration_sec = duration_sec
        self.params = params or {}
        self.executed_qty = 0
        self.remaining_qty = total_qty
        self.start_time = 0
        self.end_time = 0
        self.slices = []
        self.status = 'pending'

class TWAPExecutor:
    """
    TWAP - 时间加权平均执行
    将订单均匀分布在时间区间内
    """
    def __init__(self, order_manager):
        self.order_manager = order_manager
        self.active_orders = {}
    
    def create_order(self, symbol, side, total_qty, duration_min=30, slice_interval_sec=60):
        """创建TWAP订单"""
        order_id = f"TWAP_{int(time.time()*1000)}"
        
        order = AlgoOrder(
            symbol=symbol,
            side=side,
            total_qty=total_qty,
            algo_type=AlgoType.TWAP,
            duration_sec=duration_min * 60
        )
        order.start_time = time.time()
        order.end_time = order.start_time + duration_min * 60
        
        # 计算切片
        num_slices = (duration_min * 60) // slice_interval_sec
        qty_per_slice = total_qty / num_slices
        
        for i in range(num_slices):
            schedule_time = order.start_time + i * slice_interval_sec
            order.slices.append({
                'time': schedule_time,
                'qty': qty_per_slice,
                'executed': False
            })
        
        self.active_orders[order_id] = order
        print(f"[TWAP] Created {order_id}: {total_qty} {symbol} over {duration_min}min")
        return order_id
    
    def execute_slice(self, order_id):
        """执行切片"""
        order = self.active_orders.get(order_id)
        if not order:
            return None
        
        now = time.time()
        
        for slice in order.slices:
            if not slice['executed'] and now >= slice['time']:
                # 执行切片
                result = self.order_manager.send_order(
                    symbol=order.symbol,
                    side=order.side,
                    qty=slice['qty']
                )
                slice['executed'] = True
                slice['executed_at'] = now
                order.executed_qty += slice['qty']
                order.remaining_qty -= slice['qty']
                print(f"[TWAP] {order_id} slice filled: {slice['qty']}")
        
        # 检查完成
        if all(s['executed'] for s in order.slices):
            order.status = 'completed'
        
        return order

class VWAPExecutor:
    """
    VWAP - 成交量加权平均执行
    根据历史成交量分布执行订单
    """
    def __init__(self, order_manager, market_data):
        self.order_manager = order_manager
        self.market_data = market_data
        self.active_orders = {}
    
    def create_order(self, symbol, side, total_qty, duration_min=30, participation_rate=0.1):
        """创建VWAP订单"""
        order_id = f"VWAP_{int(time.time()*1000)}"
        
        order = AlgoOrder(
            symbol=symbol,
            side=side,
            total_qty=total_qty,
            algo_type=AlgoType.VWAP,
            duration_sec=duration_min * 60,
            params={'participation_rate': participation_rate}
        )
        order.start_time = time.time()
        order.end_time = order.start_time + duration_min * 60
        
        # 获取历史成交量分布
        vol_profile = self._get_volume_profile(symbol, duration_min)
        order.volume_profile = vol_profile
        
        self.active_orders[order_id] = order
        print(f"[VWAP] Created {order_id}: {total_qty} {symbol} @ {participation_rate*100}% participation")
        return order_id
    
    def _get_volume_profile(self, symbol, periods):
        """获取成交量分布"""
        # 简化: 假设成交量服从正态分布,高峰在开盘和收盘
        # 实际应从历史数据计算
        import random
        profile = []
        for i in range(periods):
            # 模拟U型分布
            t = i / periods
            weight = 1 - abs(t - 0.5) * 0.5
            profile.append(weight + random.uniform(-0.1, 0.1))
        total = sum(profile)
        return [p/total for p in profile]  # 归一化
    
    def execute_period(self, order_id):
        """每个周期执行"""
        order = self.active_orders.get(order_id)
        if not order or order.status == 'completed':
            return None
        
        now = time.time()
        elapsed = now - order.start_time
        periods = int(elapsed / 60)  # 每分钟检查
        
        if periods < len(order.volume_profile):
            target_qty = order.total_qty * order.volume_profile[periods]
            target_qty = min(target_qty, order.remaining_qty)
            
            if target_qty > 0:
                result = self.order_manager.send_order(
                    symbol=order.symbol,
                    side=order.side,
                    qty=target_qty
                )
                order.executed_qty += target_qty
                order.remaining_qty -= target_qty
        
        # 检查完成
        if order.remaining_qty <= 0:
            order.status = 'completed'
        
        return order
    
    def get_vwap_price(self, order_id):
        """获取VWAP执行价格"""
        order = self.active_orders.get(order_id)
        if not order or order.executed_qty == 0:
            return 0
        
        # 简化: 基于执行记录计算
        return 100000  # mock

class POVExecutor:
    """
    POV - 成交量比例执行
    按市场成交量的一定比例执行
    """
    def __init__(self, order_manager, market_data):
        self.order_manager = order_manager
        self.market_data = market_data
        self.active_orders = {}
    
    def create_order(self, symbol, side, total_qty, pov_rate=0.1, duration_min=60):
        """创建POV订单"""
        order_id = f"POV_{int(time.time()*1000)}"
        
        order = AlgoOrder(
            symbol=symbol,
            side=side,
            total_qty=total_qty,
            algo_type=AlgoType.POV,
            duration_sec=duration_min * 60,
            params={'pov_rate': pov_rate}
        )
        order.start_time = time.time()
        order.pov_rate = pov_rate
        
        self.active_orders[order_id] = order
        return order_id
    
    def on_market_volume(self, order_id, market_volume):
        """根据市场成交量执行"""
        order = self.active_orders.get(order_id)
        if not order:
            return None
        
        # 按比例执行
        target_qty = market_volume * order.pov_rate
        target_qty = min(target_qty, order.remaining_qty, order.total_qty * 0.25)  # 单次上限25%
        
        if target_qty > 0.0001:
            result = self.order_manager.send_order(
                symbol=order.symbol,
                side=order.side,
                qty=target_qty
            )
            order.executed_qty += target_qty
            order.remaining_qty -= target_qty
        
        if order.remaining_qty <= 0:
            order.status = 'completed'
        
        return order
