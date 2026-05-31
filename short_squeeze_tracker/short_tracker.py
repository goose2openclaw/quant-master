"""
Short Squeeze Tracker - 做空挤压追踪
"""
from typing import Dict

class ShortSqueezeTracker:
    """
    做空挤压追踪
    借币余额/做空比例/挤压概率
    """
    def __init__(self):
        self.short_data = {}
    
    def get_short_interest(self, symbol: str) -> Dict:
        """获取做空利率"""
        return {
            'symbol': symbol,
            'short_interest_ratio': 0.045,
            'days_to_cover': 4.5,
            'borrow_rate_annual': 0.12,
            'utilization': 0.85,
            'signal': 'EXTREME_SHORT' if 0.045 > 0.05 else 'HIGH_SHORT' if 0.045 > 0.03 else 'NORMAL'
        }
    
    def predict_squeeze_probability(self, symbol: str) -> Dict:
        """预测挤压概率"""
        short = self.get_short_interest(symbol)
        
        squeeze_prob = min(short['short_interest_ratio'] * 5, 0.8)
        
        return {
            'symbol': symbol,
            'squeeze_probability': squeeze_prob,
            'confidence': 0.75,
            'trigger_price_move': 5.0,  # 5%上涨触发
            'estimated_short_cover_volume': 50_000_000
        }
    
    def generate_squeeze_alert(self, symbol: str) -> Dict:
        """生成挤压警报"""
        squeeze = self.predict_squeeze_probability(symbol)
        
        return {
            'symbol': symbol,
            'alert_level': 'HIGH' if squeeze['squeeze_probability'] > 0.5 else 'MEDIUM',
            'squeeze_probability': squeeze['squeeze_probability'],
            'action': 'WATCH_LONG_ENTRIES' if squeeze['squeeze_probability'] > 0.5 else 'HOLD'
        }
