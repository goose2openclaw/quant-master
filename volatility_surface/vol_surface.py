"""
Volatility Surface - 波动率曲面构建
"""
from typing import Dict, List
import numpy as np

class VolatilitySurface:
    """
    波动率曲面
    IV曲面/微笑/skew分析
    """
    def __init__(self):
        self.surface_cache = {}
    
    def build_smile(self, symbol: str, expiry: str) -> Dict:
        """构建波动率微笑"""
        strikes = [0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2]  # Moneyness
        strikes_usd = [k * 65000 for k in strikes]  # 基于BTC
        
        ivs = []
        for k in strikes:
            # 模拟: 两端高IV，中间低 (vol smile)
            iv = 0.5 + abs(k - 1.0) * 0.3
            ivs.append(iv)
        
        return {
            'symbol': symbol,
            'expiry': expiry,
            'strikes': strikes_usd,
            'implied_vols': ivs,
            'skew': ivs[0] - ivs[-1],  # 25d skew
            'atm_vol': ivs[3],  # ATM vol
            'rr_25d': ivs[0] - ivs[4],  # 25d risk reversal
            'strangle': (ivs[0] + ivs[-1]) / 2 - ivs[3]  # Strangle
        }
    
    def term_structure(self, symbol: str) -> Dict:
        """波动率期限结构"""
        expiries = ['1W', '2W', '1M', '3M', '6M', '1Y']
        vols = [0.6, 0.55, 0.50, 0.45, 0.42, 0.40]  # 简化
        
        return {
            'symbol': symbol,
            'expiries': expiries,
            'vols': vols,
            'structure': 'DOWNWARD' if vols[0] > vols[-1] else 'UPWARD' if vols[0] < vols[-1] else 'FLAT',
            'contango_ratio': vols[1] / vols[0] if vols[0] > 0 else 1
        }
    
    def predict_vol_regime(self, symbol: str) -> Dict:
        """预测波动率区间"""
        term = self.term_structure(symbol)
        
        return {
            'current_vol': term['vols'][0],
            'regime': 'HIGH' if term['vols'][0] > 0.6 else 'NORMAL' if term['vols'][0] > 0.3 else 'LOW',
            'expected_move_1d': term['vols'][0] * 65_000 * 1.28 / np.sqrt(365),  # 1 std dev
            'recommendation': 'HEDGE_VOL' if term['vols'][0] > 0.7 else 'COLLECT_VOL' if term['vols'][0] < 0.4 else 'NEUTRAL'
        }
