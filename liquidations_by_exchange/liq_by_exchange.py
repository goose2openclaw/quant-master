"""
Liquidations by Exchange - 交易所强平分布
"""
from typing import Dict, List

class LiquidationsByExchange:
    """
    各交易所强平分布
    Binance/Bybit/OKX/Deribit分项
    """
    def __init__(self):
        self.exchanges = ['binance', 'bybit', 'okx', 'deribit', 'ftx']
    
    def get_breakdown(self, symbol: str) -> Dict:
        """获取各交易所强平分布"""
        return {
            'symbol': symbol,
            'binance': {'long': 50_000_000, 'short': 35_000_000},
            'bybit': {'long': 40_000_000, 'short': 30_000_000},
            'okx': {'long': 25_000_000, 'short': 20_000_000},
            'deribit': {'long': 15_000_000, 'short': 10_000_000},
            'total_long': 130_000_000,
            'total_short': 95_000_000,
            'dominant_exchange': 'binance'
        }
    
    def find_liquidation_concentration(self, symbol: str) -> Dict:
        """找强平集中度"""
        breakdown = self.get_breakdown(symbol)
        
        binance_share = (breakdown['binance']['long'] + breakdown['binance']['short']) / (breakdown['total_long'] + breakdown['total_short'])
        
        return {
            'symbol': symbol,
            'binance_concentration': binance_share,
            'concentration_risk': 'HIGH' if binance_share > 0.5 else 'MEDIUM' if binance_share > 0.3 else 'LOW',
            'recommendation': 'WATCH_BINANCE_LIQS'
        }
