"""
Smart Order Routing - 智能订单路由
最优执行venue选择
"""
import time, random
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class VenueQuote:
    venue: str
    price: float
    quantity: float
    fee: float
    latency_ms: float
    net_price: float  # 扣除费用后的净价格

class SmartOrderRouter:
    """
    SOR - 智能订单路由
    功能: 多交易所比价、最优venue选择、执行优化
    """
    def __init__(self):
        self.venues = {}  # 可用交易场所
        self.last_quotes = {}  # 最新报价缓存
    
    def add_venue(self, name, venue):
        """添加交易场所"""
        self.venues[name] = venue
    
    def get_best_route(self, symbol, side, quantity):
        """
        获取最优路由
        选择净价格最优的venue
        """
        quotes = self._collect_quotes(symbol, side, quantity)
        
        if not quotes:
            return None
        
        # 按净价格排序
        quotes.sort(key=lambda x: x.net_price if side == 'BUY' else -x.net_price)
        
        return quotes[0]
    
    def get_split_route(self, symbol, side, quantity, max_venue_fills=3):
        """
        分割订单路由
        将大单分割到多个venue执行
        """
        quotes = self._collect_quotes(symbol, side, quantity)
        
        if not quotes:
            return []
        
        # 按净价格排序
        quotes.sort(key=lambda x: x.net_price if side == 'BUY' else -x.net_price)
        
        # 分配订单
        fills = []
        remaining = quantity
        
        for quote in quotes[:max_venue_fills]:
            fill_qty = min(remaining, quote.quantity)
            fills.append({
                'venue': quote.venue,
                'price': quote.price,
                'quantity': fill_qty,
                'fee': quote.fee,
                'net_cost': fill_qty * quote.net_price
            })
            remaining -= fill_qty
            if remaining <= 0:
                break
        
        return fills
    
    def _collect_quotes(self, symbol, side, quantity):
        """收集各venue报价"""
        quotes = []
        
        for name, venue in self.venues.items():
            try:
                # 模拟获取报价
                quote = self._get_venue_quote(name, symbol, side, quantity)
                if quote:
                    quotes.append(quote)
            except Exception as e:
                print(f"[SOR] {name} quote error: {e}")
        
        return quotes
    
    def _get_venue_quote(self, venue_name, symbol, side, quantity):
        """模拟获取venue报价"""
        # 简化: 基于venue特性生成模拟报价
        base_price = 100000 + random.uniform(-100, 100)
        fee_rates = {
            'binance': 0.001,
            'coinbase': 0.005,
            'kraken': 0.002,
            'bybit': 0.001
        }
        fee_rate = fee_rates.get(venue_name, 0.001)
        latency = random.uniform(10, 100)
        
        # 模拟滑点
        slippage = quantity / 1000 * 0.0001
        price = base_price * (1 + slippage) if side == 'BUY' else base_price * (1 - slippage)
        
        net_price = price * (1 - fee_rate) if side == 'BUY' else price * (1 + fee_rate)
        
        return VenueQuote(
            venue=venue_name,
            price=price,
            quantity=quantity * random.uniform(0.5, 2),
            fee=fee_rate * quantity * price,
            latency_ms=latency,
            net_price=net_price
        )
    
    def execute_order(self, route, symbol, side):
        """执行路由订单"""
        executed = []
        for fill in route:
            # 实际执行逻辑
            executed.append({
                'venue': fill['venue'],
                'quantity': fill['quantity'],
                'price': fill['price'],
                'status': 'filled',
                'time': time.time()
            })
        return executed
    
    def get_venue_performance(self):
        """获取各venue表现"""
        return {
            'binance': {'avg_latency': 15, 'fill_rate': 99.5, 'avg_slippage': 0.0005},
            'coinbase': {'avg_latency': 25, 'fill_rate': 98.0, 'avg_slippage': 0.001},
            'kraken': {'avg_latency': 30, 'fill_rate': 97.5, 'avg_slippage': 0.0008},
            'bybit': {'avg_latency': 20, 'fill_rate': 99.0, 'avg_slippage': 0.0006}
        }
