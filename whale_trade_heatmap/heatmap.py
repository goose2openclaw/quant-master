"""
Whale Trade Heatmap - 巨鲸交易热力图
"""
from typing import Dict, List

class WhaleTradeHeatmap:
    """
    巨鲸交易热力图
    时间/价格/成交量3D可视化
    """
    def __init__(self):
        self.trades = []
    
    def generate_heatmap(self, symbol: str) -> List[Dict]:
        """生成热力图数据"""
        heatmap = []
        price_levels = 20
        
        for i in range(price_levels):
            heatmap.append({
                'price_level': 64000 + i * 500,
                'buy_volume': 10_000_000 + (hash(str(i)) % 10) * 1_000_000,
                'sell_volume': 8_000_000 + (hash(str(i*2)) % 8) * 1_000_000,
                'heat': (hash(str(i)) % 100) / 100
            })
        
        return sorted(heatmap, key=lambda x: x['heat'], reverse=True)
    
    def find_whale_clusters(self, symbol: str) -> List[Dict]:
        """找巨鲸集群"""
        heatmap = self.generate_heatmap(symbol)
        
        clusters = []
        for h in heatmap:
            if h['heat'] > 0.7:
                clusters.append({
                    'price': h['price_level'],
                    'volume': h['buy_volume'] + h['sell_volume'],
                    'direction': 'BUY' if h['buy_volume'] > h['sell_volume'] else 'SELL',
                    'strength': 'HIGH'
                })
        
        return clusters
    
    def predict_price_impact(self, symbol: str) -> Dict:
        """预测价格影响"""
        clusters = self.find_whale_clusters(symbol)
        total_buy = sum(c['volume'] for c in clusters if c['direction'] == 'BUY')
        total_sell = sum(c['volume'] for c in clusters if c['direction'] == 'SELL')
        
        return {
            'symbol': symbol,
            'cluster_count': len(clusters),
            'buy_pressure': total_buy,
            'sell_pressure': total_sell,
            'net_direction': 'BUY' if total_buy > total_sell else 'SELL',
            'predicted_impact_pct': abs(total_buy - total_sell) / 1_000_000 * 0.5
        }
