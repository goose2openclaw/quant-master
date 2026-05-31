"""
Whale Concentration Index - 鲸鱼集中度指数
"""
from typing import Dict

class WhaleConcentrationIndex:
    """
    鲸鱼集中度指数
    持币集中度与价格风险
    """
    def __init__(self):
        self.concentration_data = {}
    
    def calculate_index(self, symbol: str) -> Dict:
        """计算集中度指数"""
        top10_pct = 45.2
        top100_pct = 62.8
        
        return {
            'symbol': symbol,
            'top10_concentration_pct': top10_pct,
            'top100_concentration_pct': top100_pct,
            'whale_count': 150,
            'concentration_index': (top10_pct + top100_pct) / 2,
            'risk_level': 'HIGH' if top10_pct > 40 else 'MEDIUM'
        }
    
    def detect_dump_risk(self, symbol: str) -> Dict:
        """检测砸盘风险"""
        conc = self.calculate_index(symbol)
        
        dump_risk = conc['top10_concentration_pct'] * 0.1  # 假设top10持有量的10%可能卖出
        
        return {
            'symbol': symbol,
            'dump_risk_pct': dump_risk,
            'risk_level': 'HIGH' if dump_risk > 10 else 'MEDIUM' if dump_risk > 5 else 'LOW',
            'whale_count': conc['whale_count'],
            'recommendation': 'WATCH_WHALE_MOVES'
        }
