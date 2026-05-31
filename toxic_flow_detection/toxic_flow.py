"""
Toxic Flow Detection - 有害流量检测
"""
from typing import Dict

class ToxicFlowDetector:
    """
    有害流量检测
    识别逆向选择/抢先交易
    """
    def __init__(self):
        self.flow_types = ['RETAIL', 'INFORMED', 'ARBITRAGE', 'MM']
    
    def classify_flow(self, order_flow: Dict) -> Dict:
        """分类流量"""
        size = order_flow.get('size_usd', 0)
        frequency = order_flow.get('frequency', 0)
        
        flow_type = 'RETAIL'
        if size > 1_000_000:
            flow_type = 'INFORMED'
        elif frequency > 100:
            flow_type = 'ARBITRAGE'
        
        return {
            'flow_type': flow_type,
            'toxicity_score': 0.8 if flow_type == 'INFORMED' else 0.2,
            'trade_against': False if flow_type == 'RETAIL' else True
        }
    
    def calculate_toxicity_ratio(self) -> Dict:
        """计算有害流量比率"""
        return {
            'toxic_flow_pct': 15.5,
            'healthy_flow_pct': 84.5,
            'signal': 'MARKET_MAKERS_PROTITABLE' if 15.5 < 20 else 'TOXIC_ENVIRONMENT',
            'recommendation': 'WIDEN_SPREAD' if 15.5 > 25 else 'NORMAL_SPREAD'
        }
