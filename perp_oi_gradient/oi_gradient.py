"""
Perp OI Gradient - 永续合约OI梯度分析
"""
from typing import Dict

class PerpOIGradient:
    """
    永续OI梯度
    OI变化率与价格关系
    """
    def __init__(self):
        self.gradient_data = {}
    
    def calculate_gradient(self, symbol: str) -> Dict:
        """计算OI梯度"""
        oi_1h_ago = 1_450_000_000
        oi_now = 1_520_000_000
        price_change = 1.5  # %
        
        gradient = (oi_now - oi_1h_ago) / oi_1h_ago * 100
        price_gradient = price_change
        
        return {
            'symbol': symbol,
            'oi_gradient': gradient,
            'price_gradient': price_gradient,
            'gradient_ratio': gradient / price_gradient if price_gradient != 0 else 0,
            'interpretation': 'OI_LEADING_PRICE' if gradient > price_gradient else 'PRICE_LEADING_OI'
        }
    
    def detect_gradient_anomaly(self, symbol: str) -> Dict:
        """检测梯度异常"""
        grad = self.calculate_gradient(symbol)
        
        return {
            'symbol': symbol,
            'anomaly': abs(grad['gradient_ratio']) > 3,
            'divergence_strength': abs(grad['gradient_ratio']) - 1,
            'signal': 'TREND_REVERSAL' if abs(grad['gradient_ratio']) > 3 else 'NORMAL'
        }
