"""
Liquidations Heatmap - 强平热力图
"""
from typing import Dict, List

class LiquidationsHeatmap:
    """
    强平热力图
    全市场强平分布可视化
    """
    def __init__(self):
        self.price_levels = {}
    
    def build_liquidation_levels(self, symbol: str) -> List[Dict]:
        """构建强平水平"""
        levels = []
        base_price = 65000
        
        for i in range(1, 21):
            levels.append({
                'distance_pct': i * 2,
                'up_price': base_price * (1 + i * 0.02),
                'down_price': base_price * (1 - i * 0.02),
                'up_liquidation_size': 50_000_000 * i,
                'down_liquidation_size': 50_000_000 * i,
                'heat': 'EXTREME' if i <= 3 else 'HIGH' if i <= 7 else 'MEDIUM' if i <= 15 else 'LOW'
            })
        
        return levels
    
    def find_liquidation_walls(self, symbol: str) -> Dict:
        """找强平墙"""
        levels = self.build_liquidation_levels(symbol)
        
        walls = []
        for lvl in levels:
            if lvl['up_liquidation_size'] > 200_000_000 or lvl['down_liquidation_size'] > 200_000_000:
                walls.append(lvl)
        
        return {
            'symbol': symbol,
            'total_walls': len(walls),
            'strongest_wall': max(walls, key=lambda x: x['up_liquidation_size'] + x['down_liquidation_size']) if walls else None,
            'walls': walls
        }
    
    def predict_liquidation Cascade(self, symbol: str) -> Dict:
        """预测强平瀑布"""
        levels = self.build_liquidation_levels(symbol)
        
        return {
            'symbol': symbol,
            'cascade_risk': 'HIGH' if levels[0]['up_liquidation_size'] > 500_000_000 else 'MEDIUM',
            'chain_reaction': [
                {'trigger': 66000, 'cascade_size': 500_000_000},
                {'trigger': 68000, 'cascade_size': 800_000_000},
                {'trigger': 70000, 'cascade_size': 1_200_000_000}
            ],
            'downside_target': 64000,
            'recommendation': 'WATCH_LIQUIDATION_WALLS'
        }
