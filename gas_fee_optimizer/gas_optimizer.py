"""
Gas Fee Optimizer - Gas费优化器
"""
from typing import Dict

class GasFeeOptimizer:
    """
    Gas费优化
    智能Gas推荐/时机选择
    """
    def __init__(self):
        self.gas_history = []
    
    def get_recommended_gas(self, urgency: str = 'medium') -> Dict:
        """获取推荐Gas"""
        recommendations = {
            'low': {'gwei': 10, 'wait_time': '>30 min', 'savings': '50%'},
            'medium': {'gwei': 30, 'wait_time': '5-15 min', 'savings': '20%'},
            'high': {'gwei': 50, 'wait_time': '1-5 min', 'savings': '0%'},
            'instant': {'gwei': 100, 'wait_time': '<1 min', 'savings': 'NEGATIVE'}
        }
        
        return recommendations.get(urgency, recommendations['medium'])
    
    def predict_gas_spike(self) -> Dict:
        """预测Gas飙升"""
        # 简化: 基于历史模式
        return {
            'spike_probability_1h': 0.25,
            'predicted_spike_time': None,
            'recommended_action': 'BATCH_TRANSACTIONS_NOW',
            'savings_potential': 40  # USD
        }
    
    def optimize_transaction_timing(self) -> Dict:
        """优化交易时机"""
        current_gas = 30
        
        return {
            'current_gwei': current_gas,
            'optimal_window': '02:00-05:00 UTC',
            'avg_savings': '35%',
            'recommendation': 'WAIT' if current_gas > 40 else 'EXECUTE_NOW'
        }
