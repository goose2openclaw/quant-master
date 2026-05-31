"""
配对交易策略 - 价差回归
原理: 两个相关资产价差偏离均值时,空强多弱,等待回归
"""
from ..base_strategy import BaseStrategy
import math

class PairTradingStrategy(BaseStrategy):
    def __init__(self, symbol1, symbol2, lookback=30, entry_threshold=2.0, exit_threshold=0.5):
        super().__init__(name="PairTrading")
        self.symbol1 = symbol1  # 多头
        self.symbol2 = symbol2  # 空头
        self.lookback = lookback
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.spread_history = []
    
    def on_bar(self, bar1, bar2):
        """需要两个标的的数据"""
        price1 = bar1['close']
        price2 = bar2['close']
        
        if price2 == 0:
            return None
        
        spread = price1 / price2
        self.spread_history.append(spread)
        
        if len(self.spread_history) < self.lookback:
            return None
        
        # 计算均值和标准差
        window = self.spread_history[-self.lookback:]
        mean = sum(window) / self.lookback
        variance = sum((s - mean) ** 2 for s in window) / self.lookback
        std = math.sqrt(variance)
        
        if std == 0:
            return None
        
        zscore = (spread - mean) / std
        
        # 配对交易信号
        if self.position == 0:
            if zscore > self.entry_threshold:
                # spread过高,应该回归,空symbol1多symbol2 (简化)
                return {'action': 'SELL', 'symbol': self.symbol1, 'qty': self._calc_qty(), 
                        'reason': f'Spread high: {zscore:.2f}'}
            elif zscore < -self.entry_threshold:
                # spread过低,空symbol2多symbol1
                return {'action': 'BUY', 'symbol': self.symbol1, 'qty': self._calc_qty(),
                        'reason': f'Spread low: {zscore:.2f}'}
        
        # 回归平仓
        elif self.position > 0:
            if abs(zscore) < self.exit_threshold:
                return {'action': 'CLOSE', 'qty': self.position,
                        'reason': f'Spread converged: {zscore:.2f}'}
        
        return None
