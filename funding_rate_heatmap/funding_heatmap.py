"""
Funding Rate Heatmap - 资金费率热力图
"""
from typing import Dict, List

class FundingRateHeatmap:
    """
    资金费率热力图
    可视化全市场资金费率分布
    """
    def __init__(self):
        self.funding_data = {}
    
    def get_funding_matrix(self) -> List[Dict]:
        """获取资金费率矩阵"""
        symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOGE', 'XRP', 'DOT', 'LINK', 'AVAX']
        matrix = []
        
        for sym in symbols:
            rate = (hash(sym) % 100) / 10000  # 模拟 -0.01 到 +0.01
            matrix.append({
                'symbol': sym,
                'funding_rate': rate,
                'annualized': rate * 3 * 365 * 100,
                'heat': 'HOT_LONG' if rate > 0.005 else 'HOT_SHORT' if rate < -0.005 else 'NEUTRAL'
            })
        
        return sorted(matrix, key=lambda x: x['funding_rate'], reverse=True)
    
    def find_funding_arbitrage_pairs(self) -> List[Dict]:
        """找资金费率套利对"""
        matrix = self.get_funding_matrix()
        
        pairs = []
        for item in matrix:
            if abs(item['funding_rate']) > 0.003:
                pairs.append({
                    'symbol': item['symbol'],
                    'strategy': 'SHORT' if item['funding_rate'] > 0 else 'LONG',
                    'annualized_rate': item['annualized'],
                    'opportunity': 'HIGH' if abs(item['annualized']) > 20 else 'MEDIUM' if abs(item['annualized']) > 10 else 'LOW'
                })
        
        return sorted(pairs, key=lambda x: abs(x['annualized_rate']), reverse=True)
    
    def generate_funding_report(self) -> Dict:
        """生成资金费率报告"""
        matrix = self.get_funding_matrix()
        
        avg_funding = sum(m['funding_rate'] for m in matrix) / len(matrix)
        
        return {
            'timestamp': __import__('time').time(),
            'avg_funding_rate': avg_funding,
            'hot_long_symbols': [m['symbol'] for m in matrix if m['heat'] == 'HOT_LONG'],
            'hot_short_symbols': [m['symbol'] for m in matrix if m['heat'] == 'HOT_SHORT'],
            'arbitrage_opportunities': self.find_funding_arbitrage_pairs()[:5]
        }
