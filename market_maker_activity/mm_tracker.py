"""
Market Maker Activity - 做市商活动监控
"""
from typing import Dict, List

class MarketMakerTracker:
    """
    做市商活动监控
    追踪Citadel/Jump/Wintermute等
    """
    def __init__(self):
        self.market_makers = {
            'citadel': {'active_pairs': ['BTC', 'ETH'], 'volume_24h': 500_000_000},
            'jump_trading': {'active_pairs': ['SOL', 'AVAX'], 'volume_24h': 200_000_000},
            'wintermute': {'active_pairs': ['LINK', 'UNI'], 'volume_24h': 100_000_000},
            'delphi': {'active_pairs': ['AAVE', 'CRV'], 'volume_24h': 50_000_000}
        }
    
    def get_mm_activity(self, symbol: str) -> Dict:
        """获取做市商活动"""
        active_mm = [mm for mm, data in self.market_makers.items() if symbol in data['active_pairs']]
        
        return {
            'symbol': symbol,
            'active_market_makers': active_mm,
            'total_mm_volume': sum(self.market_makers[mm]['volume_24h'] for mm in active_mm) if active_mm else 0,
            'spread_estimate': 0.01 if len(active_mm) > 2 else 0.02,  # 更多MM=更窄价差
            'liquidity_score': 'HIGH' if len(active_mm) >= 3 else 'MEDIUM' if len(active_mm) >= 1 else 'LOW'
        }
    
    def detect_mm_withdrawal(self, symbol: str) -> Dict:
        """检测做市商撤退"""
        current = self.get_mm_activity(symbol)
        
        return {
            'symbol': symbol,
            'mm_count': len(current['active_market_makers']),
            'withdrawal_detected': current['liquidity_score'] == 'LOW',
            'spread_impact': 'WIDER' if current['liquidity_score'] == 'LOW' else 'STABLE',
            'signal': 'BEARISH_LIQUIDITY' if current['liquidity_score'] == 'LOW' else 'NEUTRAL'
        }
    
    def estimate_price_impact(self, symbol: str, trade_size: float) -> Dict:
        """估算价格影响"""
        activity = self.get_mm_activity(symbol)
        
        # 简化: 基于流动性的价格影响
        depth_score = activity['liquidity_score']
        impact_multiplier = {'HIGH': 0.5, 'MEDIUM': 1.0, 'LOW': 2.0}
        
        base_impact = trade_size / 1_000_000 * 0.1  # 基础影响
        final_impact = base_impact * impact_multiplier.get(depth_score, 1.0)
        
        return {
            'symbol': symbol,
            'trade_size': trade_size,
            'estimated_price_impact_pct': final_impact,
            'liquidity_depth': depth_score,
            'recommendation': 'SPLIT_ORDER' if final_impact > 1.0 else 'PROCEED'
        }
