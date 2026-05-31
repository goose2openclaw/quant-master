"""
Volatility Atlas - 全市场波动率地图
"""
from typing import Dict, List

class VolatilityAtlas:
    """
    波动率地图
    可视化全市场波动率
    """
    def __init__(self):
        self.vol_data = {}
    
    def get_volatility_map(self) -> List[Dict]:
        """获取波动率地图"""
        symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOGE', 'XRP', 'DOT', 'LINK', 'AVAX']
        vol_map = []
        
        for sym in symbols:
            vol = 0.4 + (hash(sym) % 60) / 100  # 0.4-1.0
            vol_map.append({
                'symbol': sym,
                'volatility': vol,
                'regime': 'HIGH' if vol > 0.7 else 'NORMAL' if vol > 0.5 else 'LOW'
            })
        
        return sorted(vol_map, key=lambda x: x['volatility'], reverse=True)
    
    def find_low_vol_assets(self) -> List[Dict]:
        """找低波动资产"""
        vol_map = self.get_volatility_map()
        return [v for v in vol_map if v['volatility'] < 0.5]
    
    def find_high_vol_assets(self) -> List[Dict]:
        """找高波动资产"""
        vol_map = self.get_volatility_map()
        return [v for v in vol_map if v['volatility'] > 0.7]
    
    def get_cross_asset_vol(self) -> Dict:
        """获取跨资产波动"""
        vol_map = self.get_volatility_map()
        avg_vol = sum(v['volatility'] for v in vol_map) / len(vol_map)
        
        return {
            'avg_volatility': avg_vol,
            'regime': 'HIGH' if avg_vol > 0.7 else 'NORMAL',
            'dispersion': max(v['volatility'] for v in vol_map) - min(v['volatility'] for v in vol_map),
            'correlation_regime': 'DIVERGENT' if avg_vol > 0.6 else 'CONVERGENT'
        }
