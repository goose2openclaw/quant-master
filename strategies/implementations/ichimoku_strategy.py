"""
Ichimoku云图策略
原理: 利用Ichimoku指标判断趋势和支撑阻力
"""
from ..base_strategy import BaseStrategy

class IchimokuStrategy(BaseStrategy):
    def __init__(self, symbol, conversion=9, base=26, span_b=52):
        super().__init__(name="Ichimoku")
        self.symbol = symbol
        self.conversion = conversion  # Tenkan-sen
        self.base = base              # Kijun-sen
        self.span_b = span_b          # Senkou Span B
        self.highs = []
        self.lows = []
        self.closes = []
    
    def on_bar(self, bar):
        self.highs.append(bar['high'])
        self.lows.append(bar['low'])
        self.closes.append(bar['close'])
        
        if len(self.highs) < self.span_b:
            return None
        
        # Tenkan-sen (转换线)
        tenkan = (max(self.highs[-self.conversion:]) + min(self.lows[-self.conversion:])) / 2
        
        # Kijun-sen (基准线)
        kijun = (max(self.highs[-self.base:]) + min(self.lows[-self.base:])) / 2
        
        # 上行云 (Senkou Span A)
        span_a = (tenkan + kijun) / 2
        
        # 下行云 (Senkou Span B)
        span_b_val = (max(self.highs[-self.span_b:]) + min(self.lows[-self.span_b:])) / 2
        
        current_price = bar['close']
        
        # 买入: 价格在云上方
        if self.position == 0:
            if current_price > max(span_a, span_b_val):
                return {'action': 'BUY', 'qty': self._calc_qty(), 'reason': 'Above cloud'}
        
        # 卖出: 价格在云下方
        elif self.position > 0:
            if current_price < min(span_a, span_b_val):
                return {'action': 'SELL', 'qty': self.position, 'reason': 'Below cloud'}
        
        return None
