"""
动量策略
原理: 24h涨幅超过阈值且RSI强势时买入, 回落到阈值时卖出
"""
from ..base_strategy import BaseStrategy

class MomentumStrategy(BaseStrategy):
    def __init__(self, symbol, momentum_threshold=5, rsi_period=14, rsi_min=55):
        super().__init__(name="Momentum")
        self.symbol = symbol
        self.momentum_threshold = momentum_threshold  # %
        self.rsi_period = rsi_period
        self.rsi_min = rsi_min
        self.prices = []
        self.price_24h = 0
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        if len(self.prices) < 2:
            return None
        
        if self.price_24h == 0:
            self.price_24h = self.prices[-(2880 if len(self.prices) > 2880 else len(self.prices))]
            return None
        
        current = self.prices[-1]
        change_24h = (current - self.price_24h) / self.price_24h * 100
        
        if change_24h > self.momentum_threshold:
            rsi = self._calc_rsi()
            if rsi > self.rsi_min:
                return {'action': 'BUY', 'qty': self._calc_qty(), 
                        'reason': f'Momentum={change_24h:.1f}%, RSI={rsi:.1f}'}
        elif change_24h < -self.momentum_threshold:
            return {'action': 'SELL', 'qty': self.position, 
                    'reason': f'Reversal={change_24h:.1f}%'}
        return None
    
    def _calc_rsi(self):
        if len(self.prices) < self.rsi_period + 1:
            return 50
        deltas = [self.prices[i] - self.prices[i-1] for i in range(-self.rsi_period, 0)]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains) / self.rsi_period
        avg_loss = sum(losses) / self.rsi_period
        if avg_loss == 0:
            return 100
        return 100 - (100 / (1 + avg_gain / avg_loss))
    
    def _calc_qty(self):
        return self.budget / self.prices[-1] * 0.95
