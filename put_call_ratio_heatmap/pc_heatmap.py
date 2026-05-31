"""
Put-Call Ratio Heatmap - 看跌看涨比率热力图
"""
from typing import Dict, List

class PutCallRatioHeatmap:
    """
    Put-Call比率热力图
    全市场期权情绪可视化
    """
    def __init__(self):
        self.ratio_data = {}
    
    def get_pc_ratio(self, symbol: str) -> Dict:
        """获取Put-Call比率"""
        return {
            'symbol': symbol,
            'pc_ratio': 0.65,
            'interpretation': 'BULLISH' if 0.65 < 0.7 else 'BEARISH' if 0.65 > 1.0 else 'NEUTRAL',
            'volume_ratio': 0.70,
            'open_interest_ratio': 0.68
        }
    
    def get_pc_heatmap(self) -> List[Dict]:
        """获取全市场PC比率热力图"""
        symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'DOGE', 'XRP', 'DOT']
        heatmap = []
        
        for sym in symbols:
            pc = self.get_pc_ratio(sym)
            heatmap.append({
                'symbol': sym,
                'pc_ratio': pc['pc_ratio'],
                'sentiment': pc['interpretation'],
                'heat': 'HOT_BULLISH' if pc['pc_ratio'] < 0.5 else 'WARM_BULLISH' if pc['pc_ratio'] < 0.7 else 'COLD_BEARISH' if pc['pc_ratio'] > 1.0 else 'NEUTRAL'
            })
        
        return sorted(heatmap, key=lambda x: x['pc_ratio'])
    
    def detect_extreme_sentiment(self) -> List[Dict]:
        """检测极端情绪"""
        heatmap = self.get_pc_heatmap()
        extremes = [h for h in heatmap if h['pc_ratio'] < 0.4 or h['pc_ratio'] > 1.2]
        
        return extremes
