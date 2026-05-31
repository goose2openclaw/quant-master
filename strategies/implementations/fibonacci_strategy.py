"""
斐波那契策略
原理: 利用斐波那契回撤位判断支撑阻力
"""
from ..base_strategy import BaseStrategy

class FibonacciStrategy(BaseStrategy):
    FIB_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    
    def __init__(self, symbol, lookback=100):
        super().__init__(name="Fibonacci")
        self.symbol = symbol
        self.lookback = lookback
        self.prices = []
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        
        if len(self.prices) < self.lookback:
            return None
        
        # 找到周期高低点
        window = self.prices[-self.lookback:]
        swing_high = max(window)
        swing_low = min(window)
        
        # 计算斐波那契位
        fib_levels = {}
        for level in self.FIB_LEVELS:
            fib_levels[level] = swing_high - (swing_high - swing_low) * level
        
        current_price = bar['close']
        
        # 买入: 价格触及斐波那契支撑
        if self.position == 0:
            for level in [0.618, 0.786, 0.5]:
                if abs(current_price - fib_levels[level]) / fib_levels[level] < 0.01:
                    return {'action': 'BUY', 'qty': self._calc_qty(),
                            'reason': f'Fib support {level*100:.1f}%: ${fib_levels[level]:.2f}'}
        
        # 卖出: 价格触及阻力
        elif self.position > 0:
            for level in [0.382, 0.236]:
                if abs(current_price - fib_levels[level]) / fib_levels[level] < 0.01:
                    return {'action': 'SELL', 'qty': self.position,
                            'reason': f'Fib resistance {level*100:.1f}%: ${fib_levels[level]:.2f}'}
        
        return None
