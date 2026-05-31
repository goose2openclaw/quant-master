"""
均值回归策略 - 波动反弹
原理: 价格偏离均值后回归,高卖低买
"""
from ..base_strategy import BaseStrategy
import math

class MeanReversionStrategy(BaseStrategy):
    def __init__(self, symbol, period=20, std_dev=2, zscore_entry=2.0):
        super().__init__(name="MeanReversion")
        self.symbol = symbol
        self.period = period
        self.std_dev = std_dev
        self.zscore_entry = zscore_entry
        self.prices = []
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        
        if len(self.prices) < self.period:
            return None
        
        # 计算均值和标准差
        window = self.prices[-self.period:]
        mean = sum(window) / self.period
        variance = sum((p - mean) ** 2 for p in window) / self.period
        std = math.sqrt(variance)
        
        # 计算Z-Score
        if std == 0:
            return None
        
        zscore = (bar['close'] - mean) / std
        
        # Z-Score < -zscore_entry: 价格超跌,买入
        if self.position == 0 and zscore < -self.zscore_entry:
            return {'action': 'BUY', 'qty': self._calc_qty(), 
                    'reason': f'ZScore={zscore:.2f} < {-self.zscore_entry:.2f}'}
        
        # Z-Score > zscore_entry: 价格超涨,卖出
        elif self.position > 0 and zscore > self.zscore_entry:
            return {'action': 'SELL', 'qty': self.position,
                    'reason': f'ZScore={zscore:.2f} > {self.zscore_entry:.2f}'}
        
        # 回归均值后平仓
        elif self.position > 0 and abs(zscore) < 0.5:
            return {'action': 'SELL', 'qty': self.position,
                    'reason': f'Mean reverted: ZScore={zscore:.2f}'}
        
        return None
