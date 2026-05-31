"""
Prediction Market Maker - 预测市场做市商
"""
from typing import Dict

class PredictionMarketMaker:
    """
    预测市场做市
    赔率报价/库存管理
    """
    def __init__(self):
        self.inventory = {}
        self.position_limits = {'YES': 10000, 'NO': 10000}
    
    def calculate_quote(self, market_id: str, side: str, size: float) -> Dict:
        """计算报价"""
        base_price = 0.50
        spread = 0.04
        inventory_bias = self._get_inventory_bias(market_id, side)
        
        price = base_price + spread / 2 + inventory_bias
        
        return {
            'market_id': market_id,
            'side': side,
            'size': size,
            'price': price,
            'spread': spread,
            'inventory_bias': inventory_bias
        }
    
    def _get_inventory_bias(self, market_id: str, side: str) -> float:
        """获取库存偏差"""
        yes_pos = self.inventory.get(f'{market_id}_YES', 0)
        no_pos = self.inventory.get(f'{market_id}_NO', 0)
        
        if side == 'YES':
            return yes_pos / self.position_limits['YES'] * 0.05
        else:
            return no_pos / self.position_limits['NO'] * 0.05
    
    def update_inventory(self, market_id: str, side: str, size: float):
        """更新库存"""
        key = f'{market_id}_{side}'
        self.inventory[key] = self.inventory.get(key, 0) + size
    
    def calculate_pnl(self, market_id: str) -> Dict:
        """计算盈亏"""
        yes_pos = self.inventory.get(f'{market_id}_YES', 0)
        no_pos = self.inventory.get(f'{market_id}_NO', 0)
        
        return {
            'market_id': market_id,
            'yes_position': yes_pos,
            'no_position': no_pos,
            'realized_pnl': 0,
            'unrealized_pnl': (yes_pos - no_pos) * 0.50,
            'net_exposure': yes_pos + no_pos
        }
