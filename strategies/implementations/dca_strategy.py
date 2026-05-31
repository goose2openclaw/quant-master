"""
定投策略 (DCA) - 定额定时买入
原理: 定期买入固定金额,降低择时风险
"""
from ..base_strategy import BaseStrategy
from datetime import datetime

class DCAStrategy(BaseStrategy):
    def __init__(self, symbol, amount=100, interval_hours=24):
        super().__init__(name="DCA")
        self.symbol = symbol
        self.amount = amount  # 每期金额 USDT
        self.interval_hours = interval_hours
        self.last_invest_time = 0
        self.total_invested = 0
        self.total_qty = 0
    
    def on_bar(self, bar):
        price = bar['close']
        now = datetime.now().timestamp()
        
        # 检查是否到定投时间
        if now - self.last_invest_time >= self.interval_hours * 3600:
            self.last_invest_time = now
            
            # 计算买入数量
            qty = self.amount / price
            
            # 更新持仓成本
            new_total = self.total_invested + self.amount
            new_qty = self.total_qty + qty
            self.budget = self.budget - self.amount  # 减少可用资金
            self.total_invested = new_total
            self.total_qty = new_qty
            
            return {'action': 'BUY', 'qty': qty, 
                    'reason': f'DCA: ${self.amount} @ ${price:.2f}'}
        
        return None
    
    def get_avg_price(self):
        if self.total_qty > 0:
            return self.total_invested / self.total_qty
        return 0
