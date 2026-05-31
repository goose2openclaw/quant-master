"""
MACD趋势策略
原理: MACD金叉买入, 死叉卖出
"""
from ..base_strategy import BaseStrategy

class MACDStrategy(BaseStrategy):
    def __init__(self, symbol, fast=12, slow=26, signal=9):
        super().__init__(name="MACD")
        self.symbol = symbol
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.prices = []
        self.last_macd = 0
        self.last_signal = 0
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        if len(self.prices) < self.slow:
            return None
        
        macd, signal = self._calc_macd()
        
        # 金叉
        if self.last_signal < self.last_macd and signal > macd:
            return {'action': 'BUY', 'qty': self._calc_qty(), 'reason': 'MACD Golden Cross'}
        # 死叉
        elif self.last_signal > self.last_macd and signal < macd:
            return {'action': 'SELL', 'qty': self.position, 'reason': 'MACD Death Cross'}
        
        self.last_macd = macd
        self.last_signal = signal
        return None
    
    def _calc_macd(self):
        """计算MACD"""
        ema_fast = self._ema(self.prices, self.fast)
        ema_slow = self._ema(self.prices, self.slow)
        macd = ema_fast - ema_slow
        
        # Signal line (simplified)
        signal = macd * 0.9
        return macd, signal
    
    def _ema(self, prices, period):
        """计算EMA"""
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    def _calc_qty(self):
        return self.budget / self.prices[-1] * 0.95
