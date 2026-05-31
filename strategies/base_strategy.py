"""
策略基类
"""
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """策略基类"""
    def __init__(self, name):
        self.name = name
        self.position = 0
        self.budget = 10000
        self.trades = []
        self.equity_curve = []
    
    @abstractmethod
    def on_bar(self, bar):
        """K线回调 - 返回交易信号"""
        pass
    
    def on_fill(self, fill):
        """成交回调"""
        self.trades.append(fill)
        if fill['side'] == 'BUY':
            self.position += fill['qty']
        else:
            self.position -= fill['qty']
        self.equity_curve.append(self._calc_equity(fill['price']))
    
    def _calc_equity(self, price):
        """计算权益"""
        return self.position * price + (self.budget - sum(t['qty'] * t['price'] for t in self.trades if t['side'] == 'BUY'))
    
    def get_stats(self):
        """获取统计"""
        if not self.trades:
            return {}
        pnl = [t['pnl'] for t in self.trades if 'pnl' in t]
        wins = [p for p in pnl if p > 0]
        losses = [p for p in pnl if p <= 0]
        return {
            'total_trades': len(self.trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': len(wins)/len(pnl)*100 if pnl else 0,
            'avg_win': sum(wins)/len(wins) if wins else 0,
            'avg_loss': sum(losses)/len(losses) if losses else 0,
        }
