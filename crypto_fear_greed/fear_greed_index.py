"""
Crypto Fear & Greed Index - 加密恐惧贪婪指数
"""
from typing import Dict
import time

class FearGreedIndex:
    """
    恐惧贪婪指数
    综合多个指标计算市场情绪
    """
    def __init__(self):
        self.history = []
        self.weights = {
            'volatility': 0.25,
            'market_momentum': 0.25,
            'social_volume': 0.15,
            'dominant': 0.15,
            '趋势': 0.20
        }
    
    def calculate(self) -> Dict:
        """计算当前指数"""
        # 各维度得分 (0-100)
        volatility_score = 30  # 波动率得分
        momentum_score = 65    # 动量得分
        social_score = 70      # 社交媒体得分
        dominance_score = 55   # 主导地位得分
        trend_score = 60       # 趋势得分
        
        # 加权平均
        index = (
            volatility_score * self.weights['volatility'] +
            momentum_score * self.weights['market_momentum'] +
            social_score * self.weights['social_volume'] +
            dominance_score * self.weights['dominant'] +
            trend_score * self.weights['趋势']
        )
        
        classification = self._classify(index)
        
        return {
            'index': round(index),
            'classification': classification,
            'timestamp': time.time(),
            'components': {
                'volatility': volatility_score,
                'momentum': momentum_score,
                'social_volume': social_score,
                'dominance': dominance_score,
                'trend': trend_score
            }
        }
    
    def _classify(self, index: float) -> str:
        """分类"""
        if index <= 25:
            return 'EXTREME_FEAR'
        elif index <= 45:
            return 'FEAR'
        elif index <= 55:
            return 'NEUTRAL'
        elif index <= 75:
            return 'GREED'
        else:
            return 'EXTREME_GREED'
    
    def get_historical_extremes(self, days: int = 30) -> Dict:
        """获取历史极端值"""
        # 简化
        return {
            'period_days': days,
            'extreme_fear_days': 5,
            'extreme_greed_days': 3,
            'avg_index': 52,
            'current_vs_avg': '+8'
        }
    
    def generate_trade_signal(self) -> Dict:
        """生成交易信号"""
        current = self.calculate()
        
        signal = 'NEUTRAL'
        action = 'HOLD'
        
        if current['index'] <= 20:
            signal = 'EXTREME_FEAR'
            action = 'BUY'
        elif current['index'] <= 40:
            signal = 'FEAR'
            action = 'ACCUMULATE'
        elif current['index'] >= 80:
            signal = 'EXTREME_GREED'
            action = 'SELL'
        elif current['index'] >= 60:
            signal = 'GREED'
            action = 'TAKE_PROFIT'
        
        return {
            'index': current['index'],
            'signal': signal,
            'action': action,
            'rationale': f"Index at {current['index']} indicates {signal.lower().replace('_', ' ')}"
        }
