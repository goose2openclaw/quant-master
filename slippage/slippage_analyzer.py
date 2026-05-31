"""
Slippage分析 - 成交质量分析
"""
import numpy as np
from datetime import datetime
from collections import deque

class TradeAnalysis:
    """交易分析"""
    def __init__(self):
        self.trades = []
        self.slippage_records = []
        self.execution_times = []
    
    def add_trade(self, order_price, execution_price, quantity, side, symbol):
        """添加交易记录"""
        slippage = (execution_price - order_price) / order_price * 100 if order_price > 0 else 0
        if side == 'SELL':
            slippage = -slippage
        
        self.trades.append({
            'time': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'order_price': order_price,
            'execution_price': execution_price,
            'quantity': quantity,
            'slippage_bps': slippage * 100  # 基点
        })
        
        self.slippage_records.append(slippage * 100)
    
    def add_execution_time(self, ms):
        self.execution_times.append(ms)
    
    def get_slippage_stats(self):
        """获取滑点统计"""
        if not self.slippage_records:
            return {}
        
        arr = np.array(self.slippage_records)
        return {
            'mean_slippage_bps': np.mean(arr),
            'median_slippage_bps': np.median(arr),
            'std_slippage_bps': np.std(arr),
            'max_slippage_bps': np.max(arr),
            'min_slippage_bps': np.min(arr),
            'p95_slippage_bps': np.percentile(arr, 95),
            'p99_slippage_bps': np.percentile(arr, 99)
        }
    
    def get_execution_stats(self):
        """获取执行统计"""
        if not self.execution_times:
            return {}
        
        arr = np.array(self.execution_times)
        return {
            'mean_exec_time_ms': np.mean(arr),
            'median_exec_time_ms': np.median(arr),
            'max_exec_time_ms': np.max(arr),
            'min_exec_time_ms': np.min(arr),
            'p95_exec_time_ms': np.percentile(arr, 95)
        }
    
    def get_fill_rate(self, total_orders):
        """获取成交率"""
        if total_orders == 0:
            return 0
        return len(self.trades) / total_orders * 100
    
    def get_recent_trades(self, limit=20):
        return self.trades[-limit:]
    
    def get_quality_score(self):
        """计算执行质量分数 (0-100)"""
        slip = self.get_slippage_stats()
        exec_t = self.get_execution_stats()
        
        score = 100
        
        # 滑点扣分
        if slip.get('mean_slippage_bps', 0) > 10:
            score -= 20
        elif slip.get('mean_slippage_bps', 0) > 5:
            score -= 10
        
        # 执行时间扣分
        if exec_t.get('mean_exec_time_ms', 0) > 1000:
            score -= 20
        elif exec_t.get('mean_exec_time_ms', 0) > 500:
            score -= 10
        
        return max(0, min(100, score))
    
    def generate_report(self):
        """生成执行报告"""
        slip = self.get_slippage_stats()
        exec_t = self.get_execution_stats()
        
        return {
            'trade_count': len(self.trades),
            'slippage': slip,
            'execution': exec_t,
            'quality_score': self.get_quality_score(),
            'recent_trades': self.get_recent_trades(10)
        }
