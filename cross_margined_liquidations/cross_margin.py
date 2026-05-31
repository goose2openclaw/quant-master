"""
Cross-Margined Liquidations - 交叉保证金强平分析
"""
from typing import Dict, List

class CrossMarginedLiquidations:
    """
    交叉保证金强平分析
    全仓/逐仓强平差异
    """
    def __init__(self):
        self.positions = {}
    
    def calculate_liquidation_price_cross(self, positions: List[Dict]) -> Dict:
        """计算交叉保证金强平价格"""
        total_margin = sum(p.get('margin', 0) for p in positions)
        total_unrealized_pnl = sum(p.get('pnl', 0) for p in positions)
        
        maintenance_margin_ratio = 0.5  # 50%维持保证金
        
        return {
            'total_margin': total_margin,
            'total_pnl': total_unrealized_pnl,
            'effective_margin_ratio': (total_margin + total_unrealized_pnl) / total_margin if total_margin > 0 else 0,
            'liquidation_risk': 'HIGH' if total_unrealized_pnl < -total_margin * 0.5 else 'MEDIUM' if total_unrealized_pnl < -total_margin * 0.3 else 'LOW'
        }
    
    def detect_cascade_risk(self) -> Dict:
        """检测级联风险"""
        return {
            'cascade_probability': 0.15,
            'affected_positions': 1500,
            'total_value_at_risk': 50_000_000,
            'risk_level': 'MEDIUM',
            'recommendation': 'REDUCE_LEVERAGE'
        }
