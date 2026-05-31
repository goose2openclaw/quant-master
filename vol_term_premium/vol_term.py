"""
Vol Term Premium - 波动率期限溢价分析
"""
from typing import Dict

class VolTermPremium:
    """
    波动率期限溢价
    期限结构溢价交易
    """
    def __init__(self):
        self.term_data = {}
    
    def calculate_term_premium(self, symbol: str) -> Dict:
        """计算期限溢价"""
        short_vol = 0.80
        long_vol = 0.60
        
        term_premium = short_vol - long_vol
        
        return {
            'symbol': symbol,
            'short_term_vol': short_vol,
            'long_term_vol': long_vol,
            'term_premium': term_premium,
            'annualized_term_premium': term_premium * 100,
            'interpretation': 'CONTANGO_PREMIUM' if term_premium > 0 else 'BACKWARDATION_DISCOUNT'
        }
    
    def find_term_trades(self) -> List[Dict]:
        """找期限交易"""
        symbols = ['BTC', 'ETH', 'SOL']
        trades = []
        
        for sym in symbols:
            term = self.calculate_term_premium(sym)
            if abs(term['term_premium']) > 0.05:
                trades.append({
                    'symbol': sym,
                    'strategy': 'SELL_SHORT_TERM_VOL' if term['term_premium'] > 0 else 'BUY_SHORT_TERM_VOL',
                    'edge_pct': abs(term['annualized_term_premium']) - 5
                })
        
        return sorted(trades, key=lambda x: x['edge_pct'], reverse=True)
