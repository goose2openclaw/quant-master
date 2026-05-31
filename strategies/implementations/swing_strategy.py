"""
波段策略 - 捕捉中线波动
原理: 趋势确认后买入,趋势反转卖出
"""
from ..base_strategy import BaseStrategy

class SwingStrategy(BaseStrategy):
    def __init__(self, symbol, lookback=20, atr_period=14, atr_multiplier=2):
        super().__init__(name="Swing")
        self.symbol = symbol
        self.lookback = lookback
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.prices = []
        self.highs = []
        self.lows = []
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        self.highs.append(bar['high'])
        self.lows.append(bar['low'])
        
        if len(self.prices) < self.lookback + 1:
            return None
        
        # 趋势判断
        swing_high = max(self.highs[-self.lookback:-1])
        swing_low = min(self.lows[-self.lookback:-1])
        
        # ATR止损
        atr = self._calc_atr()
        
        # 买入: 价格突破波段高点
        if self.position == 0:
            if bar['close'] > swing_high:
                return {'action': 'BUY', 'qty': self._calc_qty(), 
                        'reason': f'Breakout: ${swing_high:.2f}'}
        
        # 卖出: 价格跌破波段低点或ATR止损
        elif self.position > 0:
            if bar['close'] < swing_low:
                return {'action': 'SELL', 'qty': self.position, 'reason': f'Breakdown: ${swing_low:.2f}'}
            
            # ATR移动止损
            stop_price = self.strategy.entry_price - atr * self.atr_multiplier if hasattr(self, 'strategy') else 0
            if stop_price > 0 and bar['close'] < stop_price:
                return {'action': 'SELL', 'qty': self.position, 'reason': f'ATR trail stop'}
        
        return None
    
    def _calc_atr(self):
        if len(self.prices) < self.atr_period + 1:
            return 0
        trs = []
        for i in range(-self.atr_period, 0):
            tr = max(
                self.highs[i] - self.lows[i],
                abs(self.highs[i] - self.prices[i-1]),
                abs(self.lows[i] - self.prices[i-1])
            )
            trs.append(tr)
        return sum(trs) / self.atr_period if trs else 0
