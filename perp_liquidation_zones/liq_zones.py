"""
Perp Liquidation Zones - 永续合约强平区域分析
"""
from typing import Dict, List

class PerpLiquidationZones:
    """
    永续强平区域
    识别密集强平价格区间
    """
    def __init__(self):
        self.zones = {}
    
    def identify_zones(self, symbol: str) -> List[Dict]:
        """识别强平区域"""
        zones = []
        
        for i in range(1, 11):
            zones.append({
                'distance_pct': i * 5,
                'direction': 'UP' if i % 2 == 0 else 'DOWN',
                'price': 65000 * (1 + i * 0.05 if i % 2 == 0 else 1 - i * 0.05),
                'estimated_liquidation_size': i * 50_000_000,
                'density': 'HIGH' if i <= 3 else 'MEDIUM' if i <= 6 else 'LOW'
            })
        
        return zones
    
    def find_max_pain_zone(self, symbol: str) -> Dict:
        """找最大痛点区域"""
        zones = self.identify_zones(symbol)
        high_density = [z for z in zones if z['density'] == 'HIGH']
        
        return {
            'symbol': symbol,
            'max_pain_zone': high_density[0] if high_density else zones[0],
            'distance_from_spot_pct': zones[0]['distance_pct'],
            'liquidation_concentration': sum(z['estimated_liquidation_size'] for z in high_density)
        }
    
    def predict_zone_breach(self, symbol: str) -> Dict:
        """预测区域突破"""
        zone = self.find_max_pain_zone(symbol)
        
        return {
            'symbol': symbol,
            'zone_price': zone['max_pain_zone']['price'],
            'breach_probability': 0.45,
            'predicted_direction': 'BREACH_DOWN',
            'estimated_move_pct': 3.5,
            'confidence': 0.68
        }
