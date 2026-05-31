"""
马丁策略 - 亏损加倍
原理: 亏损后加倍下单,回本后退出
警告: 风险极高,需严格止损
"""
from ..base_strategy import BaseStrategy
import math

class MartingaleStrategy(BaseStrategy):
    def __init__(self, symbol, initial_qty=0.01, multiplier=2.0, max_loss_pct=10):
        super().__init__(name="Martingale")
        self.symbol = symbol
        self.initial_qty = initial_qty
        self.multiplier = multiplier
        self.max_loss_pct = max_loss_pct
        self.current_qty = initial_qty
        self.loss_count = 0
        self.base_price = 0
    
    def on_bar(self, bar):
        price = bar['close']
        
        # 亏损后加倍
        if self.loss_count > 0:
            self.current_qty = self.initial_qty * (self.multiplier ** self.loss_count)
        
        # 止损检查
        if self.position > 0 and self.base_price > 0:
            loss_pct = (self.base_price - price) / self.base_price * 100
            if loss_pct >= self.max_loss_pct:
                self.loss_count += 1
                return {'action': 'SELL', 'qty': self.position, 'reason': f'Stop loss: {loss_pct:.1f}%'}
        
        # 买入信号 (简化: RSI超卖)
        if self.position == 0:
            from factors.technical import TechnicalFactors
            prices = self.strategy.prices if hasattr(self, 'strategy') else [price]
            rsi = TechnicalFactors.RSI(prices[-20:] if len(prices) >= 20 else prices)
            if rsi < 30:
                self.base_price = price
                return {'action': 'BUY', 'qty': self.current_qty, 'reason': f'RSI={rsi:.1f}'}
        
        # 回本后退出
        if self.position > 0 and self.base_price > 0 and price >= self.base_price:
            self.loss_count = 0
            self.current_qty = self.initial_qty
            return {'action': 'SELL', 'qty': self.position, 'reason': 'Breakeven exit'}
        
        return None
