"""
Cross-Exchange Liquidations - 跨交易所强平聚合
"""
from typing import Dict, List

class CrossExchangeLiquidations:
    """
    跨交易所强平聚合
    Binance/Bybit/OKX等全网强平监控
    """
    def __init__(self):
        self.exchanges = ['binance', 'bybit', 'okx', 'deribit', 'ftx']
        self.liquidations = {}
    
    def get_liquidations_by_exchange(self, exchange: str) -> Dict:
        """获取交易所强平数据"""
        return {
            'exchange': exchange,
            'total_24h': 100_000_000,  # 简化
            'long_liquidations': 60_000_000,
            'short_liquidations': 40_000_000,
            'largest_single': 5_000_000
        }
    
    def aggregate_all_exchanges(self) -> Dict:
        """聚合所有交易所"""
        total_long = 0
        total_short = 0
        by_symbol = {}
        
        for ex in self.exchanges:
            data = self.get_liquidations_by_exchange(ex)
            total_long += data['long_liquidations']
            total_short += data['short_liquidations']
        
        return {
            'total_exchanges': len(self.exchanges),
            'total_24h': total_long + total_short,
            'long_liquidations': total_long,
            'short_liquidations': total_short,
            'long_short_ratio': total_long / total_short if total_short > 0 else 0,
            'dominant_side': 'LONG' if total_long > total_short * 1.5 else 'SHORT' if total_short > total_long * 1.5 else 'BALANCED'
        }
    
    def detect_liquidation_cluster(self, symbol: str) -> Dict:
        """检测强平集群"""
        return {
            'symbol': symbol,
            'clusters': [
                {'price': 65000, 'size': 200_000_000, 'side': 'LONG'},
                {'price': 64000, 'size': 350_000_000, 'side': 'LONG'},
                {'price': 66000, 'size': 150_000_000, 'side': 'SHORT'}
            ],
            'total_cluster_size': 700_000_000,
            'risk_level': 'HIGH'
        }
