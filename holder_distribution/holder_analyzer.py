"""
Holder Distribution - 持币分布分析
"""
from typing import Dict, List

class HolderDistributionAnalyzer:
    """
    持币分布分析
    巨鲸/散户比例追踪
    """
    def __init__(self):
        self.distribution_data = {}
    
    def get_holder_distribution(self, symbol: str) -> Dict:
        """获取持币分布"""
        return {
            'symbol': symbol,
            'top10_pct': 45.2,      # 前10地址占比
            'top100_pct': 62.8,     # 前100地址占比
            'top1000_pct': 78.5,    # 前1000地址占比
            'retail_pct': 21.5,     # 散户占比
            'whale_count': 150,      # 鲸鱼地址数
            'total_holders': 500_000
        }
    
    def calculate_concentration_index(self, symbol: str) -> Dict:
        """计算集中度指数"""
        dist = self.get_holder_distribution(symbol)
        
        return {
            'symbol': symbol,
            'gini_coefficient': 0.75,  # 0=平等, 1=极端不平等
            'concentration_score': dist['top10_pct'],
            'risk_level': 'HIGH' if dist['top10_pct'] > 50 else 'MEDIUM' if dist['top10_pct'] > 30 else 'LOW',
            'interpretation': 'HIGHLY_CONCENTRATED' if dist['top10_pct'] > 50 else 'MODERATELY_CONCENTRATED'
        }
    
    def detect_distribution_shift(self, symbol: str) -> Dict:
        """检测分布变化"""
        return {
            'symbol': symbol,
            'whale_change_7d': 2.5,      # 鲸鱼增加2.5%
            'retail_change_7d': -2.5,     # 散户减少
            'new_whale_addresses': 15,
            'distribution_trend': 'WHALE_ACCUMULATION',
            'signal': 'BULLISH'
        }
    
    def predict_sell_pressure(self, symbol: str) -> Dict:
        """预测卖压"""
        dist = self.get_holder_distribution(symbol)
        
        # 假设鲸鱼卖出会造成大波动
        estimated_sell_pressure = dist['top10_pct'] * 0.1  # 10%的top10持有量可能卖出
        
        return {
            'symbol': symbol,
            'potential_sell_pressure_pct': estimated_sell_pressure,
            'risk_level': 'HIGH' if estimated_sell_pressure > 10 else 'MEDIUM' if estimated_sell_pressure > 5 else 'LOW',
            'recommendation': 'WATCH_WHALE_MOVES'
        }
