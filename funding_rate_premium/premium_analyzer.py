"""
Funding Rate Premium - 资金费率溢价分析
"""
from typing import Dict

class FundingRatePremiumAnalyzer:
    """
    资金费率溢价分析
    费率偏离公平价值检测
    """
    def __init__(self):
        self.premium_data = {}
    
    def calculate_premium(self, symbol: str) -> Dict:
        """计算溢价"""
        fair_rate = 0.0001  # 公平资金费率
        current_rate = 0.00025  # 当前费率
        
        premium = current_rate - fair_rate
        premium_pct = premium / fair_rate * 100 if fair_rate > 0 else 0
        
        return {
            'symbol': symbol,
            'current_rate': current_rate,
            'fair_rate': fair_rate,
            'premium': premium,
            'premium_pct': premium_pct,
            'interpretation': 'OVERPRICED' if premium_pct > 50 else 'FAIR' if premium_pct > -50 else 'UNDERPRICED'
        }
    
    def find_premium_opportunities(self) -> List[Dict]:
        """找溢价机会"""
        symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP']
        opportunities = []
        
        for sym in symbols:
            prem = self.calculate_premium(sym)
            if prem['interpretation'] != 'FAIR':
                opportunities.append({
                    'symbol': sym,
                    'premium_pct': prem['premium_pct'],
                    'strategy': 'SHORT' if prem['premium_pct'] > 50 else 'LONG'
                })
        
        return sorted(opportunities, key=lambda x: abs(x['premium_pct']), reverse=True)
