"""
剥头皮策略 - 超短线快进快出
原理: 利用极短期波动,快速小额盈利
"""
from ..base_strategy import BaseStrategy

class ScalpingStrategy(BaseStrategy):
    def __init__(self, symbol, profit_pct=0.1, stop_pct=0.05, fast_ema=5, slow_ema=13):
        super().__init__(name="Scalping")
        self.symbol = symbol
        self.profit_pct = profit_pct  # 盈利目标 %
        self.stop_pct = stop_pct      # 止损 %
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.prices = []
        self.entry_price = 0
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        if len(self.prices) < self.slow_ema:
            return None
        
        # 计算EMA
        fast_ema = self._ema(self.prices[-self.fast_ema:])
        slow_ema = self._ema(self.prices[-self.slow_ema:])
        
        # 金叉买入
        if self.position == 0:
            if self._ema(self.prices[-self.fast_ema-1:-1]) < slow_ema and fast_ema > slow_ema:
                self.entry_price = bar['close']
                return {'action': 'BUY', 'qty': self._calc_qty(), 'reason': 'EMA Golden Cross'}
        
        # 死叉卖出
        elif self.position > 0:
            if self._ema(self.prices[-self.fast_ema-1:-1]) > slow_ema and fast_ema < slow_ema:
                return {'action': 'SELL', 'qty': self.position, 'reason': 'EMA Death Cross'}
            
            # 止盈止损
            price = bar['close']
            pnl_pct = (price - self.entry_price) / self.entry_price * 100
            
            if pnl_pct >= self.profit_pct:
                return {'action': 'SELL', 'qty': self.position, 'reason': f'Take profit: {pnl_pct:.2f}%'}
            if pnl_pct <= -self.stop_pct:
                return {'action': 'SELL', 'qty': self.position, 'reason': f'Stop loss: {pnl_pct:.2f}%'}
        
        return None
    
    def _ema(self, prices):
        if len(prices) < 2:
            return prices[0] if prices else 0
        multiplier = 2 / (len(prices) + 1)
        ema = sum(prices[:len(prices)]) / len(prices)
        for price in prices[len(prices):]:
            ema = (price - ema) * multiplier + ema
        return ema
