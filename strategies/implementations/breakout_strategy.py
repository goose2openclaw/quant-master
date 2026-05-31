"""
突破策略 - 追涨杀跌
原理: 价格突破关键位后追入,趋势延续时持有
"""
from ..base_strategy import BaseStrategy

class BreakoutStrategy(BaseStrategy):
    def __init__(self, symbol, lookback=20, volume_multiplier=1.5):
        super().__init__(name="Breakout")
        self.symbol = symbol
        self.lookback = lookback
        self.volume_multiplier = volume_multiplier
        self.prices = []
        self.volumes = []
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        self.volumes.append(bar.get('volume', 0))
        
        if len(self.prices) < self.lookback:
            return None
        
        # 计算关键位
        recent_prices = self.prices[-self.lookback:]
        resistance = max(recent_prices[:-1])
        support = min(recent_prices[:-1])
        
        # 计算平均成交量
        avg_volume = sum(self.volumes[-self.lookback:-1]) / self.lookback
        
        # 突破阻力位 + 放量
        if self.position == 0:
            if bar['close'] > resistance and bar.get('volume', 0) > avg_volume * self.volume_multiplier:
                return {'action': 'BUY', 'qty': self._calc_qty(),
                        'reason': f'Breakout: ${resistance:.2f}, Vol x{bar.get("volume",0)/avg_volume:.1f}'}
        
        # 跌破支撑位
        elif self.position > 0:
            if bar['close'] < support:
                return {'action': 'SELL', 'qty': self.position, 'reason': f'Breakdown: ${support:.2f}'}
        
        return None
