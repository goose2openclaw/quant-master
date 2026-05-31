"""
Strategy Correlation - 策略相关性分析
"""
import numpy as np
from typing import Dict, List

class StrategyCorrelationAnalyzer:
    """
    策略相关性分析
    分析多策略间的相关性,避免过度集中
    """
    def __init__(self):
        self.strategy_returns = {}  # {strategy_name: [returns]}
        self.correlation_matrix = {}
    
    def add_strategy_returns(self, strategy_name, returns):
        """添加策略收益序列"""
        self.strategy_returns[strategy_name] = returns
        self._update_correlation_matrix()
    
    def _update_correlation_matrix(self):
        """更新相关性矩阵"""
        strategies = list(self.strategy_returns.keys())
        n = len(strategies)
        
        self.correlation_matrix = np.zeros((n, n))
        
        for i, s1 in enumerate(strategies):
            for j, s2 in enumerate(strategies):
                if i == j:
                    self.correlation_matrix[i, j] = 1.0
                else:
                    corr = self._calculate_correlation(
                        self.strategy_returns[s1],
                        self.strategy_returns[s2]
                    )
                    self.correlation_matrix[i, j] = corr
    
    def _calculate_correlation(self, returns1, returns2):
        """计算相关系数"""
        if len(returns1) != len(returns2) or len(returns1) < 2:
            return 0
        
        # 皮尔逊相关
        mean1 = np.mean(returns1)
        mean2 = np.mean(returns2)
        
        numerator = sum((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(returns1, returns2))
        denom1 = sum((r - mean1)**2 for r in returns1)**0.5
        denom2 = sum((r - mean2)**2 for r in returns2)**0.5
        
        if denom1 * denom2 == 0:
            return 0
        
        return numerator / (denom1 * denom2)
    
    def get_correlation(self, strategy1, strategy2):
        """获取两个策略的相关系数"""
        strategies = list(self.strategy_returns.keys())
        if strategy1 not in strategies or strategy2 not in strategies:
            return None
        
        i = strategies.index(strategy1)
        j = strategies.index(strategy2)
        
        return self.correlation_matrix[i, j]
    
    def get_highly_correlated(self, strategy_name, threshold=0.7):
        """获取高度相关的策略"""
        strategies = list(self.strategy_returns.keys())
        if strategy_name not in strategies:
            return []
        
        i = strategies.index(strategy_name)
        
        correlated = []
        for j, s2 in enumerate(strategies):
            if i != j:
                corr = self.correlation_matrix[i, j]
                if abs(corr) >= threshold:
                    correlated.append({
                        'strategy': s2,
                        'correlation': corr,
                        'direction': 'positive' if corr > 0 else 'negative'
                    })
        
        return correlated
    
    def get_portfolio_diversification(self):
        """计算组合分散度"""
        strategies = list(self.strategy_returns.keys())
        n = len(strategies)
        
        if n < 2:
            return 1.0
        
        # 平均相关度
        total_corr = 0
        count = 0
        for i in range(n):
            for j in range(i+1, n):
                total_corr += abs(self.correlation_matrix[i, j])
                count += 1
        
        avg_corr = total_corr / count if count > 0 else 0
        
        # 分散度 = 1 - 平均相关度
        diversification = 1 - avg_corr
        
        return {
            'avg_correlation': avg_corr,
            'diversification_score': diversification,
            'recommendation': 'Well diversified' if diversification > 0.6 else 'Consider reducing correlation'
        }
    
    def find_optimal_subset(self, max_correlation=0.5):
        """找到低相关性子集"""
        strategies = list(self.strategy_returns.keys())
        n = len(strategies)
        
        best_subset = []
        
        for i in range(n):
            subset = [strategies[i]]
            valid = True
            
            for s in subset:
                idx1 = strategies.index(s)
                for j in range(len(subset)):
                    s2 = subset[j]
                    idx2 = strategies.index(s2)
                    if abs(self.correlation_matrix[idx1, idx2]) > max_correlation:
                        valid = False
                        break
                
                if valid:
                    for j in range(i+1, n):
                        s2 = strategies[j]
                        can_add = True
                        idx2 = strategies.index(s2)
                        for s3 in subset:
                            idx3 = strategies.index(s3)
                            if abs(self.correlation_matrix[idx2, idx3]) > max_correlation:
                                can_add = False
                                break
                        if can_add:
                            subset.append(s2)
                
                if not valid:
                    break
            
            if len(subset) > len(best_subset):
                best_subset = subset
        
        return best_subset
    
    def generate_matrix_html(self):
        """生成相关性矩阵HTML"""
        strategies = list(self.strategy_returns.keys())
        
        html = '<table border="1"><tr><th></th>'
        for s in strategies:
            html += f'<th>{s[:10]}</th>'
        html += '</tr>'
        
        for i, s1 in enumerate(strategies):
            html += f'<tr><td>{s1[:10]}</td>'
            for j in range(len(strategies)):
                corr = self.correlation_matrix[i, j]
                color = 'green' if corr > 0.7 else 'yellow' if corr > 0.3 else 'red'
                html += f'<td style="background:{color}">{corr:.2f}</td>'
            html += '</tr>'
        
        html += '</table>'
        return html
