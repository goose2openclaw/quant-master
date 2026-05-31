"""绩效分析 - 归因+风险指标"""
import json
from datetime import datetime, timedelta

class PerformanceAnalyzer:
    def __init__(self, trade_logger):
        self.logger = trade_logger
    
    def analyze(self):
        """分析绩效"""
        trades = self.logger.get_trades(1000)
        if not trades:
            return {'error': 'No trades'}
        
        # 计算指标
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) <= 0]
        
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        avg_win = sum(t.get('pnl', 0) for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.get('pnl', 0) for t in losses) / len(losses) if losses else 0
        
        # 最大回撤 (简化)
        equity_file = self.logger.equity_file
        max_drawdown = 0
        if os.path.exists(equity_file):
            equity = []
            with open(equity_file) as f:
                next(f)  # skip header
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        equity.append(float(parts[1]))
            peak = equity[0] if equity else 0
            for e in equity:
                if e > peak:
                    peak = e
                dd = (peak - e) / peak * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, dd)
        
        return {
            'total_trades': len(trades),
            'win_rate': f"{win_rate:.1f}%",
            'avg_win': f"${avg_win:.2f}",
            'avg_loss': f"${avg_loss:.2f}",
            'total_pnl': f"${total_pnl:.2f}",
            'max_drawdown': f"{max_drawdown:.1f}%",
            'sharpe_ratio': 'N/A',  # 需要更多数据
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 'N/A'
        }
    
    def get_equity_curve(self):
        """获取权益曲线数据"""
        equity_file = self.logger.equity_file
        data = []
        if os.path.exists(equity_file):
            with open(equity_file) as f:
                next(f)
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        data.append({'time': parts[0], 'equity': float(parts[1])})
        return data

import os  # for max_drawdown calc
