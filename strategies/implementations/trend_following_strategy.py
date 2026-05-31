"""
趋势跟随策略 - ADX确认趋势
原理: ADX确认趋势强度,顺势而为
"""
from ..base_strategy import BaseStrategy

class TrendFollowingStrategy(BaseStrategy):
    def __init__(self, symbol, adx_period=14, adx_threshold=25):
        super().__init__(name="TrendFollow")
        self.symbol = symbol
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.prices = []
        self.highs = []
        self.lows = []
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        self.highs.append(bar['high'])
        self.lows.append(bar['low'])
        
        if len(self.prices) < self.adx_period * 2:
            return None
        
        # 计算ADX
        adx = self._calc_adx()
        
        # 无趋势时不交易
        if adx < self.adx_threshold:
            return None
        
        # 计算趋势方向
        ema_fast = self._ema(self.prices[-10:])
        ema_slow = self._ema(self.prices[-30:]) if len(self.prices) >= 30 else ema_fast
        
        # 上涨趋势
        if self.position == 0 and ema_fast > ema_slow:
            return {'action': 'BUY', 'qty': self._calc_qty(), 'reason': f'Trend up, ADX={adx:.1f}'}
        
        # 下跌趋势
        elif self.position > 0 and ema_fast < ema_slow:
            return {'action': 'SELL', 'qty': self.position, 'reason': f'Trend down, ADX={adx:.1f}'}
        
        return None
    
    def _ema(self, prices):
        if len(prices) < 2:
            return prices[0] if prices else 0
        multiplier = 2 / (len(prices) + 1)
        ema = sum(prices[:len(prices)]) / len(prices)
        for price in prices[len(prices):]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    def _calc_adx(self):
        # 简化ADX计算
        if len(self.prices) < self.adx_period * 2:
            return 0
        
        # 计算 +DI 和 -DI
        plus_dm = []
        minus_dm = []
        trs = []
        
        for i in range(-self.adx_period, 0):
            high_diff = self.highs[i] - self.highs[i-1]
            low_diff = self.lows[i-1] - self.lows[i]
            
            plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
            minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)
            
            tr = max(
                self.highs[i] - self.lows[i],
                abs(self.highs[i] - self.prices[i-1]),
                abs(self.lows[i] - self.prices[i-1])
            )
            trs.append(tr)
        
        atr = sum(trs) / self.adx_period
        if atr == 0:
            return 0
        
        plus_di = sum(plus_dm) / self.adx_period / atr * 100
        minus_di = sum(minus_dm) / self.adx_period / atr * 100
        
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        return dx  # 简化版ADX
