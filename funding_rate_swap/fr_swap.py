"""
Funding Rate Swap - 资金费率互换
"""
from typing import Dict

class FundingRateSwap:
    """
    资金费率互换
    锁定资金费率/对冲费率风险
    """
    def __init__(self):
        self.swaps = {}
    
    def create_swap(self, symbol: str, notional: float, direction: str) -> Dict:
        """创建互换"""
        return {
            'swap_id': f"SWAP_{symbol}_{notional}",
            'symbol': symbol,
            'notional': notional,
            'direction': direction,
            'fixed_rate': 0.00015,
            'current_floating_rate': 0.00018,
            'counterparty': 'Binance',
            'settlement_date': 'T+1'
        }
    
    def calculate_swap_value(self, swap: Dict, current_rate: float) -> Dict:
        """计算互换价值"""
        fixed = swap['fixed_rate']
        floating = current_rate
        
        pv_fixed = fixed * swap['notional'] / 365
        pv_floating = floating * swap['notional'] / 365
        
        return {
            'swap_id': swap['swap_id'],
            'fixed_leg_pv': pv_fixed,
            'floating_leg_pv': pv_floating,
            'mark_to_market': pv_fixed - pv_floating,
            'm2m_pct': (pv_fixed - pv_floating) / swap['notional'] * 100
        }
    
    def find_swap_opportunities(self) -> List[Dict]:
        """找互换机会"""
        return [
            {'symbol': 'BTC', 'fixed_rate': 0.00015, 'float_rate': 0.00022, 'edge': 0.00007},
            {'symbol': 'ETH', 'fixed_rate': 0.00018, 'float_rate': 0.00025, 'edge': 0.00007}
        ]
