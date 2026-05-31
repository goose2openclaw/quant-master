"""
RSI均值回归策略
原理: RSI超卖时买入, RSI超买时卖出
"""
from ..base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    def __init__(self, symbol, rsi_period=14, buy_threshold=30, sell_threshold=70):
        super().__init__(name="RSI")
        self.symbol = symbol
        self.rsi_period = rsi_period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.prices = []
    
    def on_bar(self, bar):
        """K线回调"""
        self.prices.append(bar['close'])
        if len(self.prices) < self.rsi_period:
            return None
        
        # 计算RSI
        rsi = self._calc_rsi()
        
        # 交易信号
        if rsi < self.buy_threshold:
            return {'action': 'BUY', 'qty': self._calc_qty(), 'reason': f'RSI={rsi:.1f}<{self.buy_threshold}'}
        elif rsi > self.sell_threshold:
            return {'action': 'SELL', 'qty': self.position, 'reason': f'RSI={rsi:.1f}>{self.sell_threshold}'}
        return None
    
    def _calc_rsi(self):
        """计算RSI"""
        deltas = [self.prices[i] - self.prices[i-1] for i in range(1, len(self.prices))]
        gains = [d if d > 0 else 0 for d in deltas[-self.rsi_period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-self.rsi_period:]]
        
        avg_gain = sum(gains) / self.rsi_period
        avg_loss = sum(losses) / self.rsi_period
        
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calc_qty(self):
        """计算仓位"""
        return self.budget / self.prices[-1] * 0.95
