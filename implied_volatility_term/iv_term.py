"""
Implied Volatility Term Structure - IV期限结构
"""
from typing import Dict, List

class IVTermStructure:
    """
    IV期限结构
    短期/中期/长期波动率
    """
    def __init__(self):
        self.term_data = {}
    
    def get_term_structure(self, symbol: str) -> Dict:
        """获取期限结构"""
        return {
            'symbol': symbol,
            '1w_iv': 0.80,
            '1m_iv': 0.72,
            '3m_iv': 0.65,
            '6m_iv': 0.60,
            '1y_iv': 0.55,
            'shape': 'DOWNWARD' if True else 'UPWARD',
            'contango_ratio': 0.88
        }
    
    def detect_term_premium(self, symbol: str) -> Dict:
        """检测期限溢价"""
        term = self.get_term_structure(symbol)
        
        premium_1y_vs_1m = term['1y_iv'] - term['1m_iv']
        
        return {
            'symbol': symbol,
            'term_premium': premium_1y_vs_1m,
            'premium_interpretation': 'HIGH_TERM_PREMIUM' if premium_1y_vs_1m > 0.15 else 'NORMAL',
            'roll_yield_opportunity': premium_1y_vs_1m if premium_1y_vs_1m > 0 else 0
        }
    
    def predict_iv crush(self, symbol: str) -> Dict:
        """预测IV crush效应"""
        term = self.get_term_structure(symbol)
        
        return {
            'symbol': symbol,
            'iv_crush_risk': 'HIGH' if term['1w_iv'] > term['1m_iv'] * 1.2 else 'MEDIUM' if term['1w_iv'] > term['1m_iv'] * 1.1 else 'LOW',
            'estimated_iv_drop_pct': 15 if term['1w_iv'] > term['1m_iv'] * 1.2 else 5,
            'before_event': term['1w_iv'],
            'after_event': term['1m_iv']
        }
