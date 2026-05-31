"""
蒙特卡洛回测 - 概率模拟
"""
import numpy as np
import random
from datetime import datetime

class MonteCarloSimulator:
    """
    蒙特卡洛模拟器
    功能: 路径模拟、概率分布、风险评估
    """
    def __init__(self, initial_capital=10000, num_simulations=1000):
        self.initial_capital = initial_capital
        self.num_simulations = num_simulations
        self.price_paths = []
        self.final_values = []
        self.max_drawdowns = []
        self.sharpe_ratios = []
    
    def simulate_gbm(self, initial_price, mu=0, sigma=0.3, days=252, steps_per_day=1):
        """
        几何布朗运动模拟
        dS = mu*S*dt + sigma*S*dW
        """
        dt = 1 / steps_per_day
        total_steps = days * steps_per_day
        
        paths = np.zeros((self.num_simulations, total_steps + 1))
        paths[:, 0] = initial_price
        
        for t in range(1, total_steps + 1):
            z = np.random.standard_normal(self.num_simulations)
            paths[:, t] = paths[:, t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)
        
        return paths
    
    def simulate_strategy(self, strategy_func, price_paths):
        """
        模拟策略在路径上的表现
        """
        results = []
        
        for path in price_paths:
            equity = self.initial_capital
            peak = equity
            max_dd = 0
            trades = 0
            wins = 0
            
            for i, price in enumerate(path):
                signal = strategy_func(price, i)
                if signal:
                    trades += 1
                    # 简化: 假设每笔交易收益服从正态分布
                    pnl_pct = np.random.normal(0.001, 0.02)
                    equity *= (1 + pnl_pct)
                    if pnl_pct > 0:
                        wins += 1
                    
                    peak = max(peak, equity)
                    dd = (peak - equity) / peak * 100
                    max_dd = max(max_dd, dd)
            
            final_return = (equity - self.initial_capital) / self.initial_capital * 100
            results.append({
                'final_value': equity,
                'return': final_return,
                'max_drawdown': max_dd,
                'trades': trades,
                'win_rate': wins / trades * 100 if trades > 0 else 0
            })
        
        return results
    
    def run_simulation(self, initial_price, mu=0.0002, sigma=0.03, days=30):
        """运行完整模拟"""
        print(f"[MonteCarlo] 运行 {self.num_simulations} 次模拟...")
        
        # 生成价格路径
        price_paths = self.simulate_gbm(
            initial_price=initial_price,
            mu=mu,  # 日均收益率
            sigma=sigma,  # 日波动率
            days=days
        )
        
        # 模拟策略
        def simple_strategy(price, day):
            # 简化: 随机交易
            return random.random() < 0.1
        
        results = self.simulate_strategy(simple_strategy, price_paths)
        
        self.final_values = [r['final_value'] for r in results]
        self.max_drawdowns = [r['max_drawdown'] for r in results]
        
        return self.get_statistics()
    
    def get_statistics(self):
        """获取统计信息"""
        final_arr = np.array(self.final_values)
        dd_arr = np.array(self.max_drawdowns)
        
        return {
            'initial_capital': self.initial_capital,
            'num_simulations': self.num_simulations,
            'final_value': {
                'mean': np.mean(final_arr),
                'median': np.median(final_arr),
                'std': np.std(final_arr),
                'min': np.min(final_arr),
                'max': np.max(final_arr),
                'percentile_5': np.percentile(final_arr, 5),
                'percentile_95': np.percentile(final_arr, 95),
                'percentile_99': np.percentile(final_arr, 99)
            },
            'max_drawdown': {
                'mean': np.mean(dd_arr),
                'median': np.median(dd_arr),
                'max': np.max(dd_arr),
                'percentile_95': np.percentile(dd_arr, 95)
            },
            'probability_of_profit': np.sum(final_arr > self.initial_capital) / len(final_arr) * 100,
            'probability_of_loss': np.sum(final_arr < self.initial_capital) / len(final_arr) * 100,
            'var_95': np.percentile(final_arr, 5) - self.initial_capital,  # 95% VaR
            'cvar_95': np.mean(final_arr[final_arr <= np.percentile(final_arr, 5)]) - self.initial_capital
        }
    
    def get_distribution(self, bins=50):
        """获取分布"""
        return {
            'final_values': np.histogram(self.final_values, bins=bins)[0].tolist(),
            'bin_edges': np.histogram(self.final_values, bins=bins)[1].tolist()
        }
    
    def generate_report(self):
        """生成报告"""
        stats = self.get_statistics()
        dist = self.get_distribution()
        
        return {
            'summary': stats,
            'distribution': dist,
            'recommendation': self._get_recommendation(stats)
        }
    
    def _get_recommendation(self, stats):
        """基于模拟结果给出建议"""
        prob_profit = stats['probability_of_profit']
        var = stats['var_95']
        
        if prob_profit >= 70 and var >= 0:
            return "策略表现优秀,建议实盘"
        elif prob_profit >= 50:
            return "策略中性,建议优化"
        else:
            return "策略风险较高,谨慎使用"
