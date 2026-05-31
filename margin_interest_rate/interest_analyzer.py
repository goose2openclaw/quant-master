"""
Margin Interest Rate - 保证金利率分析
"""
from typing import Dict

class MarginInterestAnalyzer:
    """
    保证金利率分析
    全市场保证金借贷成本
    """
    def __init__(self):
        self.interest_data = {}
    
    def get_margin_interest(self, exchange: str = 'binance') -> Dict:
        """获取保证金利率"""
        return {
            'exchange': exchange,
            'btc_long': 0.0004,
            'btc_short': 0.0005,
            'eth_long': 0.0005,
            'eth_short': 0.0006,
            'usdt_borrow': 0.001
        }
    
    def calculate_cost_to_short(self, symbol: str, days: int) -> Dict:
        """计算做空成本"""
        interest = self.get_margin_interest()
        borrow_rate = interest.get(f'{symbol.lower()}_short', 0.0005)
        
        total_cost = borrow_rate * days * 100  # 年化百分比
        
        return {
            'symbol': symbol,
            'days': days,
            'daily_rate': borrow_rate,
            'total_cost_pct': total_cost,
            'annualized_cost': borrow_rate * 365 * 100,
            'cost_verdict': 'CHEAP' if borrow_rate < 0.0005 else 'EXPENSIVE'
        }
    
    def compare_exchange_rates(self, symbol: str) -> List[Dict]:
        """对比交易所利率"""
        exchanges = ['binance', 'bybit', 'okx', 'deribit']
        comparison = []
        
        for ex in exchanges:
            rates = self.get_margin_interest(ex)
            comparison.append({
                'exchange': ex,
                'rate': rates.get(f'{symbol.lower()}_short', 0),
                'annualized': rates.get(f'{symbol.lower()}_short', 0) * 365 * 100
            })
        
        return sorted(comparison, key=lambda x: x['annualized'])
