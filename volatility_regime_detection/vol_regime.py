"""
Volatility Regime Detection - 波动率状态检测
"""
from typing import Dict

class VolatilityRegimeDetector:
    """
    波动率状态检测
    LOW/HIGH/CRISIS状态识别
    """
    def __init__(self):
        self.regimes = ['LOW', 'NORMAL', 'HIGH', 'CRISIS']
    
    def detect_regime(self, symbol: str = 'BTC') -> Dict:
        """检测当前状态"""
        vol = 0.65  # 简化: 65%年化
        
        regime = 'NORMAL'
        if vol > 1.0:
            regime = 'CRISIS'
        elif vol > 0.8:
            regime = 'HIGH'
        elif vol < 0.4:
            regime = 'LOW'
        
        return {
            'symbol': symbol,
            'current_vol': vol,
            'regime': regime,
            'transition_probability': self._get_transition_probs(regime),
            'expected_regime_duration': '5-10 days'
        }
    
    def _get_transition_probs(self, current: str) -> Dict:
        """获取转移概率"""
        probs = {
            'LOW': {'LOW': 0.6, 'NORMAL': 0.3, 'HIGH': 0.1, 'CRISIS': 0.0},
            'NORMAL': {'LOW': 0.1, 'NORMAL': 0.7, 'HIGH': 0.15, 'CRISIS': 0.05},
            'HIGH': {'LOW': 0.0, 'NORMAL': 0.3, 'HIGH': 0.5, 'CRISIS': 0.2},
            'CRISIS': {'LOW': 0.0, 'NORMAL': 0.2, 'HIGH': 0.4, 'CRISIS': 0.4}
        }
        return probs.get(current, probs['NORMAL'])
    
    def predict_regime_change(self) -> Dict:
        """预测状态变化"""
        current = self.detect_regime('BTC')
        
        return {
            'current_regime': current['regime'],
            'next_regime_prediction': 'HIGH',
            'probability': 0.30,
            'time_horizon': '7-14 days',
            'trigger_indicators': ['MACD_NEG', 'RSI_EXTREME', 'FLOW_NEGATIVE']
        }
