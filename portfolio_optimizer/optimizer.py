"""
组合优化器 - Mean-Variance, Risk-Parity, Kelly Criterion
"""
import numpy as np
from scipy.optimize import minimize

class PortfolioOptimizer:
    """
    组合优化器
    方法: 马科维茨、风险平价、凯利公式、最大夏普
    """
    def __init__(self, returns, cov_matrix, risk_free_rate=0.02):
        self.returns = np.array(returns)
        self.cov_matrix = np.array(cov_matrix)
        self.risk_free_rate = risk_free_rate
        self.n_assets = len(returns)
    
    def mean_variance(self, target_return=None):
        """
        马科维茨均值方差优化
        目标: 最小化组合方差
        """
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(self.cov_matrix, weights))
        
        def portfolio_return(weights):
            return np.sum(weights * self.returns)
        
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # 权重和=1
        ]
        
        if target_return:
            constraints.append({
                'type': 'eq',
                'fun': lambda w: portfolio_return(w) - target_return
            })
        
        bounds = [(0, 1) for _ in range(self.n_assets)]
        initial_weights = np.array([1/self.n_assets] * self.n_assets)
        
        result = minimize(
            portfolio_variance,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        return {
            'weights': result.x,
            'expected_return': portfolio_return(result.x),
            'variance': portfolio_variance(result.x),
            'volatility': np.sqrt(portfolio_variance(result.x))
        }
    
    def max_sharpe(self):
        """
        最大夏普比率组合
        """
        def neg_sharpe(weights):
            port_return = np.sum(weights * self.returns)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
            return -sharpe
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(0, 1) for _ in range(self.n_assets)]
        initial_weights = np.array([1/self.n_assets] * self.n_assets)
        
        result = minimize(
            neg_sharpe,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        weights = result.x
        port_return = np.sum(weights * self.returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        
        return {
            'weights': weights,
            'expected_return': port_return,
            'volatility': port_vol,
            'sharpe_ratio': (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
        }
    
    def risk_parity(self):
        """
        风险平价组合
        每个资产对组合风险的贡献相等
        """
        def risk_contribution(weights):
            port_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            marginal_contrib = np.dot(self.cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / port_vol if port_vol > 0 else weights
            target_rc = port_vol / self.n_assets
            return np.sum((risk_contrib - target_rc)**2)
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(0, 1) for _ in range(self.n_assets)]
        initial_weights = np.array([1/self.n_assets] * self.n_assets)
        
        result = minimize(
            risk_contribution,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        return {
            'weights': result.x,
            'expected_return': np.sum(result.x * self.returns),
            'volatility': np.sqrt(np.dot(result.x.T, np.dot(self.cov_matrix, result.x)))
        }
    
    def kelly_criterion(self):
        """
        凯利公式
        f* = (bp - q) / b
        """
        # 简化: 基于历史收益计算凯利权重
        mean_return = np.mean(self.returns)
        variance = np.var(self.returns)
        
        if variance == 0:
            return {'weights': np.array([1/self.n_assets] * self.n_assets)}
        
        # 简化的凯利公式
        kelly_weights = self.returns / variance
        kelly_weights = np.maximum(kelly_weights, 0)  # 只做多
        
        # 归一化
        if np.sum(kelly_weights) > 0:
            kelly_weights = kelly_weights / np.sum(kelly_weights)
        else:
            kelly_weights = np.array([1/self.n_assets] * self.n_assets)
        
        # 凯利建议仓位可能过大,使用半凯利
        kelly_weights *= 0.5
        
        return {
            'weights': kelly_weights,
            'expected_return': np.sum(kelly_weights * self.returns),
            'note': '使用半凯利 (50%) 降低风险'
        }
    
    def efficient_frontier(self, points=50):
        """
        有效前沿
        """
        min_return = np.min(self.returns)
        max_return = np.max(self.returns)
        
        frontier = []
        for target in np.linspace(min_return, max_return, points):
            try:
                result = self.mean_variance(target_return=target)
                if result['variance'] < float('inf'):
                    frontier.append({
                        'return': result['expected_return'],
                        'volatility': np.sqrt(result['variance']),
                        'weights': result['weights']
                    })
            except:
                continue
        
        return frontier
    
    def min_variance(self):
        """最小方差组合"""
        return self.mean_variance()
    
    def max_return(self):
        """最大收益组合"""
        max_return = np.max(self.returns)
        return self.mean_variance(target_return=max_return)
