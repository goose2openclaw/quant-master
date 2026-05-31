"""
Open Interest Tracking - 未平仓合约追踪
"""
from typing import Dict, List
import time

class OpenInterestTracker:
    """
    未平仓合约追踪
    检测合约资金流入/流出
    """
    def __init__(self):
        self.oi_data = {}  # {symbol: {'oi': float, 'change_24h': float}}
        self.price_data = {}  # {symbol: price}
        self.alerts = []
    
    def fetch_oi(self, symbol: str) -> Dict:
        """获取OI数据"""
        # 简化
        return {
            'symbol': symbol,
            'open_interest': 1_000_000_000,  # 10亿 USD
            'change_24h_pct': 5.2,
            'long_short_ratio': 1.15
        }
    
    def detect_oi_divergence(self, symbol: str) -> Dict:
        """检测OI背离"""
        oi = self.fetch_oi(symbol)
        price_change = 2.5  # 简化
        
        return {
            'symbol': symbol,
            'oi_change': oi['change_24h_pct'],
            'price_change': price_change,
            'divergence': oi['change_24h_pct'] - price_change,
            'signal': 'BULLISH' if oi['change_24h_pct'] > 0 and price_change < 0 else
                     'BEARISH' if oi['change_24h_pct'] < 0 and price_change > 0 else 'NEUTRAL'
        }
    
    def detect_squeeze(self, symbol: str) -> Dict:
        """检测OI收缩 (突破前兆)"""
        oi_trend = -15.5  # 简化: OI持续收缩
        
        return {
            'symbol': symbol,
            'oi_trend_pct': oi_trend,
            'squeeze_detected': oi_trend < -10,
            'confidence': 'HIGH' if oi_trend < -20 else 'MEDIUM' if oi_trend < -10 else 'LOW',
            'interpretation': 'Large positions being closed before potential move'
        }
    
    def get_oi_sentiment(self, symbol: str) -> str:
        """获取OI情绪"""
        oi = self.fetch_oi(symbol)
        
        if oi['change_24h_pct'] > 10:
            return 'EXTREME_LONG'
        elif oi['change_24h_pct'] < -10:
            return 'EXTREME_SHORT'
        elif oi['long_short_ratio'] > 1.3:
            return 'BULLISH'
        elif oi['long_short_ratio'] < 0.7:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
