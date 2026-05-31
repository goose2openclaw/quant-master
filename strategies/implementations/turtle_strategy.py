"""
海龟策略 - 经典趋势跟随
原理: 唐奇安通道突破, Nautral Days Entry/Exit
"""
from ..base_strategy import BaseStrategy

class TurtleStrategy(BaseStrategy):
    def __init__(self, symbol, entry_period=20, exit_period=10, atr_period=20):
        super().__init__(name="Turtle")
        self.symbol = symbol
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period
        self.prices = []
        self.highs = []
        self.lows = []
        self.entry_price = 0
        self.stop_price = 0
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        self.highs.append(bar['high'])
        self.lows.append(bar['low'])
        
        if len(self.highs) < max(self.entry_period, self.exit_period, self.atr_period) + 1:
            return None
        
        # 唐奇安通道
        entry_high = max(self.highs[-self.entry_period:-1])
        entry_low = min(self.lows[-self.entry_period:-1])
        exit_high = max(self.highs[-self.exit_period:-1])
        exit_low = min(self.lows[-self.exit_period:-1])
        
        # ATR计算
        atr = self._calc_atr()
        
        current_price = bar['close']
        
        # 买入信号: 突破20日高点
        if self.position == 0:
            if current_price > entry_high:
                self.entry_price = current_price
                self.stop_price = current_price - 2 * atr
                return {'action': 'BUY', 'qty': self._calc_qty(),
                        'reason': f'Channel breakout: ${entry_high:.2f}'}
        
        # 卖出信号: 跌破10日低点或ATR止损
        elif self.position > 0:
            if current_price < exit_low:
                return {'action': 'SELL', 'qty': self.position, 'reason': f'Channel breakdown: ${exit_low:.2f}'}
            if current_price < self.stop_price:
                return {'action': 'SELL', 'qty': self.position, 'reason': 'ATR stop'}
        
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
