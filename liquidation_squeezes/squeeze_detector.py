"""
Liquidation Squeezes - 多空挤压检测
"""
from typing import Dict, List

class LiquidationSqueezeDetector:
    def detect_long_squeeze(self, symbol: str) -> Dict:
        short_interest_ratio = 0.15
        cost_to_borrow = 0.10
        days_to_cover = 5
        return {
            'symbol': symbol,
            'squeeze_type': 'LONG_SQUEEZE',
            'short_interest': short_interest_ratio,
            'borrow_rate_annual': cost_to_borrow,
            'days_to_cover': days_to_cover,
            'imminent': short_interest_ratio > 0.10 and days_to_cover < 10,
            'risk_level': 'HIGH' if short_interest_ratio > 0.20 else 'MEDIUM'
        }
    
    def detect_short_squeeze(self, symbol: str) -> Dict:
        return {
            'symbol': symbol,
            'squeeze_type': 'SHORT_SQUEEZE',
            'long_interest': 0.12,
            'downside_target': -15.0,
            'risk_level': 'HIGH'
        }
    
    def generate_squeeze_alert(self, symbol: str) -> Dict:
        long_sq = self.detect_long_squeeze(symbol)
        return {
            'symbol': symbol,
            'long_squeeze': long_sq,
            'short_squeeze': self.detect_short_squeeze(symbol),
            'primary_threat': 'LONG_SQUEEZE' if long_sq['imminent'] else 'NONE'
        }
