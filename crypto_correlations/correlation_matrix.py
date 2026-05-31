"""
Crypto Correlations - 相关性矩阵
"""
from typing import Dict, List
import numpy as np

class CorrelationMatrix:
    """
    相关性分析
    发现跨资产关联
    """
    def __init__(self):
        self.assets = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX']
        self.prices = {}
    
    def calculate_correlation(self, asset1: str, asset2: str, days: int = 30) -> float:
        """计算两个资产的相关性"""
        # 简化: 返回模拟相关性
        correlations = {
            ('BTC', 'ETH'): 0.85,
            ('BTC', 'DOGE'): 0.72,
            ('ETH', 'SOL'): 0.78,
            ('BTC', 'XRP'): 0.45,
            ('ETH', 'ADA'): 0.68
        }
        return correlations.get((asset1, asset2), correlations.get((asset2, asset1), 0.5))
    
    def build_matrix(self) -> Dict:
        """构建相关性矩阵"""
        matrix = {}
        for a1 in self.assets:
            matrix[a1] = {}
            for a2 in self.assets:
                if a1 == a2:
                    matrix[a1][a2] = 1.0
                else:
                    matrix[a1][a2] = self.calculate_correlation(a1, a2)
        return matrix
    
    def find_high_correlations(self, threshold: float = 0.8) -> List[Dict]:
        """找高相关对"""
        pairs = []
        for i, a1 in enumerate(self.assets):
            for a2 in self.assets[i+1:]:
                corr = self.calculate_correlation(a1, a2)
                if abs(corr) >= threshold:
                    pairs.append({'pair': (a1, a2), 'correlation': corr})
        return sorted(pairs, key=lambda x: abs(x['correlation']), reverse=True)
    
    def find_uncorrelated(self, threshold: float = 0.3) -> List[Dict]:
        """找低相关资产 (分散化好选择)"""
        pairs = []
        for i, a1 in enumerate(self.assets):
            for a2 in self.assets[i+1:]:
                corr = self.calculate_correlation(a1, a2)
                if abs(corr) < threshold:
                    pairs.append({'pair': (a1, a2), 'correlation': corr})
        return sorted(pairs, key=lambda x: abs(x['correlation']))
    
    def generate_pair_trading_signals(self) -> List[Dict]:
        """生成配对交易信号"""
        signals = []
        for pair_data in self.find_high_correlations(0.7):
            pair = pair_data['pair']
            corr = pair_data['correlation']
            
            # 简化配对交易逻辑
            signals.append({
                'pair': pair,
                'correlation': corr,
                'strategy': 'MEAN_REVERSION',
                'signal': 'WATCH' if corr > 0.8 else 'NEUTRAL'
            })
        return signals
