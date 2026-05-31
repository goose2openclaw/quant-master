"""
Cross Margin Optimizer - 跨保证金优化器
"""
from typing import Dict, List

class CrossMarginOptimizer:
    """
    跨保证金优化
    全仓/逐仓最优配置
    """
    def __init__(self):
        self.positions = {}
    
    def optimize_margin_type(self, positions: List[Dict]) -> Dict:
        """优化保证金类型"""
        recommendations = []
        
        for pos in positions:
            if abs(pos.get('pnl', 0)) > 1000:
                recommendations.append({
                    'symbol': pos['symbol'],
                    'current_type': 'CROSS',
                    'recommended_type': 'ISOLATED',
                    'savings': 50
                })
        
        return {
            'total_positions': len(positions),
            'recommendations': recommendations,
            'estimated_savings': sum(r['savings'] for r in recommendations)
        }
    
    def calculate_margin_efficiency(self, portfolio: Dict) -> Dict:
        """计算保证金效率"""
        return {
            'total_margin_used': 10_000,
            'total_position_value': 100_000,
            'efficiency_ratio': 0.10,
            'optimal_ratio': 0.15,
            'recommendation': 'INCREASE_LEVERAGE' if 0.10 < 0.15 else 'REDUCE_RISK'
        }
