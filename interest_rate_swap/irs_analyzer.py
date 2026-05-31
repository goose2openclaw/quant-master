"""
Interest Rate Swap - 利率互换分析
"""
from typing import Dict

class InterestRateSwapAnalyzer:
    """
    利率互换
    浮动固浮动利率交换
    """
    def __init__(self):
        self.swaps = {}
    
    def price_swap(self, notional: float, fixed_rate: float, term_days: int) -> Dict:
        """定价互换"""
        floating_rate = 0.00018  # 当前浮动利率
        
        return {
            'notional': notional,
            'fixed_rate': fixed_rate,
            'floating_rate': floating_rate,
            'term_days': term_days,
            'fixed_leg_pv': notional * fixed_rate * term_days / 365,
            'floating_leg_pv': notional * floating_rate * term_days / 365,
            'swap_value': notional * (fixed_rate - floating_rate) * term_days / 365,
            'receive_fixed': True
        }
    
    def find_swap_counterparties(self) -> List[Dict]:
        """找互换对手"""
        return [
            {'counterparty': 'Binance', 'fixed_rate': 0.00015, 'available': True},
            {'counterparty': 'Bybit', 'fixed_rate': 0.00016, 'available': True},
            {'counterparty': 'OKX', 'fixed_rate': 0.00014, 'available': False}
        ]
