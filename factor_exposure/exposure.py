"""
Factor Exposure Analysis - 因子敞口分析
"""
import numpy as np
from typing import Dict, List

class FactorExposure:
    """因子敞口"""
    def __init__(self, factor_name, exposure_value, contribution):
        self.factor_name = factor_name
        self.exposure = exposure_value  # 敞口值
        self.contribution = contribution  # 收益贡献

class FactorExposureAnalyzer:
    """
    因子敞口分析
    分析组合在各因子上的暴露
    """
    def __init__(self):
        self.factors = {
            'market': {'beta': 0, 'description': '市场因子'},
            'size': {'description': '大小盘因子'},
            'value': {'description': '价值因子'},
            'momentum': {'description': '动量因子'},
            'quality': {'description': '质量因子'},
            'volatility': {'description': '波动率因子'},
            'yield': {'description': '收益率因子'},
            'growth': {'description': '成长因子'}
        }
        self.exposures = {}  # {factor: exposure_value}
    
    def calculate_portfolio_exposure(self, holdings, factor_values):
        """
        计算组合因子敞口
        holdings: {symbol: {'weight': 0.x, 'factor_values': {...}}}
        factor_values: {symbol: {factor: value}}
        """
        portfolio_exposure = {}
        
        for factor in self.factors:
            weighted_exposure = 0
            total_weight = 0
            
            for symbol, data in holdings.items():
                weight = data.get('weight', 0)
                symbol_factors = factor_values.get(symbol, {})
                factor_value = symbol_factors.get(factor, 0)
                
                weighted_exposure += weight * factor_value
                total_weight += abs(weight)
            
            # 归一化
            portfolio_exposure[factor] = weighted_exposure / total_weight if total_weight > 0 else 0
        
        self.exposures = portfolio_exposure
        return portfolio_exposure
    
    def get_risk_contribution(self, factor_cov_matrix):
        """
        计算因子风险贡献
        factor_cov_matrix: 因子协方差矩阵
        """
        risk_contrib = {}
        total_risk = 0
        
        for factor, exposure in self.exposures.items():
            factor_var = exposure ** 2 * factor_cov_matrix.get(factor, {}).get(factor, 1)
            risk_contrib[factor] = factor_var
            total_risk += factor_var
        
        # 归一化为百分比
        if total_risk > 0:
            risk_contrib = {k: v/total_risk*100 for k, v in risk_contrib.items()}
        
        return risk_contrib
    
    def calculate_factor_return_contribution(self, factor_returns):
        """
        计算因子收益贡献
        factor_returns: {factor: return}
        """
        contributions = {}
        
        for factor, exposure in self.exposures.items():
            ret = factor_returns.get(factor, 0)
            contrib = exposure * ret
            contributions[factor] = {
                'exposure': exposure,
                'return': ret,
                'contribution': contrib,
                'contribution_pct': contrib * 100
            }
        
        return contributions
    
    def detect_factor_overexposure(self, limit=0.3):
        """检测因子过度暴露"""
        overexposed = []
        
        for factor, exposure in self.exposures.items():
            if abs(exposure) > limit:
                overexposed.append({
                    'factor': factor,
                    'exposure': exposure,
                    'severity': 'high' if abs(exposure) > 0.5 else 'medium'
                })
        
        return overexposed
    
    def rebalance_to_target_exposure(self, current_holdings, target_exposure, factor_values):
        """
        调仓到目标因子敞口
        """
        # 简化: 线性规划求解
        # 实际需要优化器
        
        adjustments = {}
        
        for symbol, data in current_holdings.items():
            current_weight = data.get('weight', 0)
            
            # 计算当前因子敞口
            symbol_factors = factor_values.get(symbol, {})
            
            # 简化: 计算需要的权重调整
            adjustments[symbol] = {
                'current_weight': current_weight,
                'target_weight': current_weight,  # 需要优化器计算
                'change': 0
            }
        
        return adjustments
    
    def generate_report(self):
        """生成报告"""
        total_exposure = sum(abs(v) for v in self.exposures.values())
        
        return {
            'exposures': self.exposures,
            'total_exposure': total_exposure,
            'concentration': max(abs(v) for v in self.exposures.values()) if self.exposures else 0,
            'factors': self.factors
        }
