"""
回测引擎
"""
from datetime import datetime, timedelta
from ..data import HistoryData

class BacktestEngine:
    """
    回测引擎 - 事件驱动回测
    """
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.strategy = None
        self.data_source = None
        self.trades = []
        self.equity_curve = []
        self.stats = {}
    
    def set_strategy(self, strategy):
        """设置策略"""
        self.strategy = strategy
        strategy.budget = self.initial_capital
    
    def set_data_source(self, data_source):
        """设置数据源"""
        self.data_source = data_source
    
    def run(self, symbol, start_date, end_date, interval='1m'):
        """运行回测"""
        print(f"[Backtest] 运行回测: {symbol} {start_date} - {end_date}")
        
        # 获取历史数据
        history = HistoryData(proxy={'http':'','https':''})
        bars = history.get_klines(symbol, interval, 1000)
        
        if not bars:
            print("[Backtest] 无数据")
            return
        
        # 逐K线回测
        for bar in bars:
            # 策略信号
            signal = self.strategy.on_bar(bar)
            
            if signal:
                self._execute(signal, bar)
            
            # 更新权益
            equity = self.capital + self.position * bar['close']
            self.equity_curve.append({
                'time': bar['time'],
                'equity': equity,
                'position': self.position
            })
        
        self._calc_stats()
        print(f"[Backtest] 完成: 总交易 {len(self.trades)}")
        return self.stats
    
    def _execute(self, signal, bar):
        """执行信号"""
        action = signal['action']
        qty = signal.get('qty', 0)
        price = bar['close']
        
        if action == 'BUY' and self.capital >= price * qty:
            cost = price * qty
            self.capital -= cost
            self.position += qty
            self.trades.append({
                'time': bar['time'],
                'side': 'BUY',
                'qty': qty,
                'price': price,
                'value': cost
            })
        elif action == 'SELL' and self.position >= qty:
            proceeds = price * qty
            self.capital += proceeds
            self.position -= qty
            self.trades.append({
                'time': bar['time'],
                'side': 'SELL',
                'qty': qty,
                'price': price,
                'value': proceeds,
                'pnl': (price - self.trades[-1]['price']) * qty if self.trades and self.trades[-1]['side'] == 'BUY' else 0
            })
    
    def _calc_stats(self):
        """计算统计"""
        if not self.trades:
            return
        
        pnl = [t.get('pnl', 0) for t in self.trades]
        wins = [p for p in pnl if p > 0]
        losses = [p for p in pnl if p <= 0]
        
        final_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.initial_capital
        
        # 计算最大回撤
        peak = self.initial_capital
        max_dd = 0
        for e in self.equity_curve:
            if e['equity'] > peak:
                peak = e['equity']
            dd = (peak - e['equity']) / peak * 100
            max_dd = max(max_dd, dd)
        
        self.stats = {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': (final_equity - self.initial_capital) / self.initial_capital * 100,
            'total_trades': len(self.trades),
            'win_rate': len(wins) / len(pnl) * 100 if pnl else 0,
            'avg_win': sum(wins) / len(wins) if wins else 0,
            'avg_loss': sum(losses) / len(losses) if losses else 0,
            'max_drawdown': max_dd,
            'profit_factor': abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0
        }
    
    def get_equity_curve(self):
        return self.equity_curve
    
    def get_trades(self):
        return self.trades
