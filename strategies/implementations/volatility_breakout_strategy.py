"""
波动率突破策略
原理: 波动率收缩后放大时突破买入
"""
from ..base_strategy import BaseStrategy
import math

class VolatilityBreakoutStrategy(BaseStrategy):
    def __init__(self, symbol, lookback=20, atr_multiplier=3):
        super().__init__(name="VolBreakout")
        self.symbol = symbol
        self.lookback = lookback
        self.atr_multiplier = atr_multiplier
        self.prices = []
        self.ranges = []  # 当日振幅
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        
        # 计算当日振幅
        day_range = bar['high'] - bar['low']
        self.ranges.append(day_range)
        
        if len(self.ranges) < self.lookback:
            return None
        
        # 计算平均振幅
        avg_range = sum(self.ranges[-self.lookback:]) / self.lookback
        
        # 突破信号: 当日振幅超过均值的一定倍数
        if self.position == 0:
            if day_range > avg_range * self.atr_multiplier:
                # 突破上涨
                if bar['close'] > bar['open']:  # 阳线
                    return {'action': 'BUY', 'qty': self._calc_qty(),
                            'reason': f'Vol breakout: {day_range/avg_range:.1f}x avg'}
                # 突破下跌
                else:
                    return {'action': 'SELL', 'qty': self.position, 'reason': 'Vol breakdown'}
        
        return None
