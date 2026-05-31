"""
网格策略 - 震荡行情套利
原理: 在价格区间设置网格,低买高卖
"""
from ..base_strategy import BaseStrategy

class GridStrategy(BaseStrategy):
    def __init__(self, symbol, grid_num=10, profit_pct=1):
        super().__init__(name="Grid")
        self.symbol = symbol
        self.grid_num = grid_num
        self.profit_pct = profit_pct
        self.grid_prices = []
        self.last_grid_price = 0
    
    def on_bar(self, bar):
        price = bar['close']
        
        # 初始化网格
        if not self.grid_prices:
            self.grid_prices = [price * (1 + (i - self.grid_num/2) * 0.01) for i in range(self.grid_num)]
            self.last_grid_price = price
            return None
        
        # 网格交易
        for grid_price in self.grid_prices:
            # 价格触及网格,买入
            if price <= grid_price and self.last_grid_price > grid_price and self.position == 0:
                return {'action': 'BUY', 'qty': self._calc_qty(), 
                        'reason': f'Grid hit: ${grid_price:.2f}'}
            
            # 价格触及网格,卖出
            elif price >= grid_price and self.last_grid_price < grid_price and self.position > 0:
                return {'action': 'SELL', 'qty': self.position,
                        'reason': f'Grid hit: ${grid_price:.2f}'}
        
        self.last_grid_price = price
        return None
