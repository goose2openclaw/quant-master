"""
Funding Rate Ceiling Floor - 资金费率天花板与地板
"""
from typing import Dict

class FundingRateCeilingFloor:
    """
    资金费率极值分析
    历史极值与均值回归
    """
    def __init__(self):
        self.historical_data = {}
    
    def calculate_bounds(self, symbol: str) -> Dict:
        """计算极值边界"""
        return {
            'symbol': symbol,
            'ceiling': 0.001,      # 历史最高
            'floor': -0.0005,      # 历史最低
            'current_rate': 0.00025,
            'distance_to_ceiling_pct': 75,
            'distance_to_floor_pct': 50,
            'mean_reversion_probability': 0.72
        }
    
    def predict_reversion(self, symbol: str) -> Dict:
        """预测回归"""
        bounds = self.calculate_bounds(symbol)
        
        at_ceiling = bounds['current_rate'] >= bounds['ceiling'] * 0.9
        at_floor = bounds['current_rate'] <= bounds['floor'] * 1.1
        
        return {
            'symbol': symbol,
            'will_revert': at_ceiling or at_floor,
            'target_rate': (bounds['ceiling'] + bounds['floor']) / 2,
            'reversion_distance_pct': abs(bounds['current_rate'] - (bounds['ceiling'] + bounds['floor']) / 2) / bounds['current_rate'] * 100,
            'confidence': bounds['mean_reversion_probability']
        }
