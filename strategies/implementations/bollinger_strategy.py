"""
布林带均值回归策略
原理: 价格触及下轨买入, 触及上轨卖出
"""
from ..base_strategy import BaseStrategy
import math

class BollingerStrategy(BaseStrategy):
    def __init__(self, symbol, period=20, std_dev=2):
        super().__init__(name="Bollinger")
        self.symbol = symbol
        self.period = period
        self.std_dev = std_dev
        self.prices = []
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        if len(self.prices) < self.period:
            return None
        
        upper, middle, lower = self._calc_bands()
        price = self.prices[-1]
        
        if price <= lower:
            return {'action': 'BUY', 'qty': self._calc_qty(), 'reason': f'Price={price:.2f}<Lower={lower:.2f}'}
        elif price >= upper:
            return {'action': 'SELL', 'qty': self.position, 'reason': f'Price={price:.2f}>Upper={upper:.2f}'}
        return None
    
    def _calc_bands(self):
        """计算布林带"""
        window = self.prices[-self.period:]
        middle = sum(window) / self.period
        variance = sum((p - middle) ** 2 for p in window) / self.period
        std = math.sqrt(variance)
        upper = middle + std * self.std_dev
        lower = middle - std * self.std_dev
        return upper, middle, lower
    
    def _calc_qty(self):
        return self.budget / self.prices[-1] * 0.95
