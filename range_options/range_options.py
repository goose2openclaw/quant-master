"""
Range Options - 预测市场区间期权
"""
from typing import Dict

class RangeOptions:
    """
    区间期权
    价格区间预测合约
    """
    def __init__(self):
        self.ranges = {}
    
    def create_range_contract(self, asset: str, high: float, low: float) -> Dict:
        """创建区间合约"""
        return {
            'contract_id': f"RANGE_{asset}_{high}",
            'asset': asset,
            'range_high': high,
            'range_low': low,
            'mid_point': (high + low) / 2,
            'range_width': high - low
        }
    
    def price_range_contract(self, contract: Dict, current_price: float, 
                           volatility: float, time_days: int) -> Dict:
        """定价区间合约"""
        width = contract['range_width']
        mid = contract['mid_point']
        
        # 简化: 区间越宽越便宜
        moneyness = abs(current_price - mid) / width
        time_value = time_days / 365 * volatility
        
        price = 0.50 * (1 - moneyness) * (1 - time_value)
        
        return {
            'contract_id': contract['contract_id'],
            'current_price': current_price,
            'fair_price': max(0.05, min(0.95, price)),
            'in_range': 'YES' if low < current_price < high else 'NO'
        }
