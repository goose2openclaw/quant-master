"""
Performance Attribution - 收益归因分析
"""
import numpy as np
from typing import Dict, List

class PerformanceAttribution:
    """
    收益归因分析
    将组合收益分解到各个因子/标的/策略
    """
    def __init__(self):
        self.returns = []
        self.factor_returns = {}
        self.positions = {}
    
    def add_return(self, date, portfolio_return, benchmark_return=0):
        """添加收益记录"""
        self.returns.append({
            'date': date,
            'portfolio': portfolio_return,
            'benchmark': benchmark_return,
            'excess': portfolio_return - benchmark_return
        })
    
    def add_factor_return(self, factor, date, return_value):
        """添加因子收益"""
        if factor not in self.factor_returns:
            self.factor_returns[factor] = []
        self.factor_returns[factor].append({'date': date, 'return': return_value})
    
    def get_total_return(self):
        """总收益"""
        if not self.returns:
            return 0
        total = 1
        for r in self.returns:
            total *= (1 + r['portfolio'])
        return (total - 1) * 100
    
    def get_brinson_attribution(self, positions, benchmarks):
        """
        Brinson归因模型
        分解: 配置效应 + 选择效应 + 交互效应
        """
        # 简化实现
        allocation_effect = 0
        selection_effect = 0
        interaction_effect = 0
        
        for symbol in positions:
            port_weight = positions[symbol].get('weight', 0)
            bench_weight = benchmarks.get(symbol, {}).get('weight', 0)
            port_return = positions[symbol].get('return', 0)
            bench_return = benchmarks.get(symbol, {}).get('return', 0)
            
            # 配置效应: (P_weight - B_weight) * B_return
            allocation_effect += (port_weight - bench_weight) * bench_return
            
            # 选择效应: B_weight * (P_return - B_return)
            selection_effect += bench_weight * (port_return - bench_return)
            
            # 交互效应: (P_weight - B_weight) * (P_return - B_return)
            interaction_effect += (port_weight - bench_weight) * (port_return - bench_return)
        
        return {
            'allocation_effect': allocation_effect * 100,
            'selection_effect': selection_effect * 100,
            'interaction_effect': interaction_effect * 100,
            'total_effect': (allocation_effect + selection_effect + interaction_effect) * 100
        }
    
    def get_factor_contribution(self):
        """因子收益贡献"""
        if not self.factor_returns:
            return {}
        
        contributions = {}
        for factor, values in self.factor_returns.items():
            if not values:
                continue
            # 计算因子收益
            factor_ret = sum(v['return'] for v in values) / len(values)
            contributions[factor] = {
                'avg_return': factor_ret * 100,
                'periods': len(values)
            }
        
        return contributions
    
    def get_style_attribution(self, style_factors, holdings):
        """
        风格归因
        分解到: 大小盘/价值成长/动量等
        """
        style_contrib = {}
        
        for style, exposure in style_factors.items():
            # 风格收益 = 暴露度 * 风格因子收益
            style_ret = exposure * self.factor_returns.get(style, [{'return': 0}])[-1]['return']
            style_contrib[style] = {
                'exposure': exposure,
                'return_contribution': style_ret * 100
            }
        
        return style_contrib
    
    def get_risk_contribution(self, volatility_by_position):
        """风险贡献"""
        total_vol = sum(volatility_by_position.values())
        
        risk_contrib = {}
        for pos, vol in volatility_by_position.items():
            weight = vol / total_vol if total_vol > 0 else 0
            risk_contrib[pos] = {
                'volatility': vol * 100,
                'weight': weight * 100,
                'risk_contribution': weight * 100
            }
        
        return risk_contrib
    
    def generate_report(self):
        """生成归因报告"""
        return {
            'total_return': self.get_total_return(),
            'factor_contribution': self.get_factor_contribution(),
            'brinson': self.get_brinson_attribution(
                self.positions,
                {}
            ),
            'periods': len(self.returns)
        }
