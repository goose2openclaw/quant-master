"""
VWAP策略 - 成交量加权平均价
原理: 价格在VWAP上方做多,下方做空
"""
from ..base_strategy import BaseStrategy

class VWAPStrategy(BaseStrategy):
    def __init__(self, symbol, std_dev=1.5):
        super().__init__(name="VWAP")
        self.symbol = symbol
        self.std_dev = std_dev
        self.prices = []
        self.volumes = []
    
    def on_bar(self, bar):
        self.prices.append(bar['close'])
        self.volumes.append(bar.get('volume', 1))
        
        if len(self.prices) < 50:
            return None
        
        # 计算VWAP
        cum_pv = sum(p * v for p, v in zip(self.prices[-50:], self.volumes[-50:]))
        cum_v = sum(self.volumes[-50:])
        vwap = cum_pv / cum_v if cum_v > 0 else self.prices[-1]
        
        # 计算标准差
        import math
        variance = sum((p - vwap) ** 2 for p in self.prices[-50:]) / 50
        std = math.sqrt(variance)
        
        current_price = bar['close']
        upper_band = vwap + std * self.std_dev
        lower_band = vwap - std * self.std_dev
        
        # 买入: 价格下穿下轨
        if self.position == 0:
            if current_price < lower_band:
                return {'action': 'BUY', 'qty': self._calc_qty(), 'reason': f'Below VWAP-{self.std_dev}σ'}
        
        # 卖出: 价格上穿上轨
        elif self.position > 0:
            if current_price > upper_band:
                return {'action': 'SELL', 'qty': self.position, 'reason': f'Above VWAP+{self.std_dev}σ'}
            # 或价格回到VWAP
            elif current_price > vwap and self.prices[-2] <= vwap:
                return {'action': 'SELL', 'qty': self.position, 'reason': 'Crossed VWAP'}
        
        return None
