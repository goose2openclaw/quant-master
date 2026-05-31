"""
NVT Signal - NVT信号
Network Value to Transaction Ratio
"""
from typing import Dict

class NTVSignal:
    """
    NVT信号
    类似P/E比率的链上估值
    """
    def __init__(self):
        self.nvt_data = {}
    
    def calculate_nvt(self, symbol: str = 'BTC') -> Dict:
        """计算NVT"""
        market_cap = 1_200_000_000_000
        daily_tx_volume = 30_000_000_000
        
        nvt = market_cap / daily_tx_volume if daily_tx_volume > 0 else 0
        
        return {
            'symbol': symbol,
            'nvt': nvt,
            'nvt_signal': 40,  # 移动平均
            'interpretation': 'OVERVALUED' if nvt > 45 else 'UNDERVALUED' if nvt < 25 else 'FAIR',
            'historical_avg': 35
        }
    
    def detect_nvt_divergence(self, symbol: str) -> Dict:
        """检测NVT背离"""
        nvt = self.calculate_nvt(symbol)
        price_change = 10.5
        
        return {
            'symbol': symbol,
            'nvt': nvt['nvt'],
            'nvt_signal': nvt['nvt_signal'],
            'divergence': (nvt['nvt'] > nvt['nvt_signal'] and price_change > 0) or (nvt['nvt'] < nvt['nvt_signal'] and price_change < 0),
            'signal': 'BEARISH' if nvt['nvt'] > 50 and price_change > 5 else 'NEUTRAL'
        }
    
    def get_nvt_recommendation(self, symbol: str) -> Dict:
        """获取NVT建议"""
        nvt = self.calculate_nvt(symbol)
        
        return {
            'symbol': symbol,
            'action': 'SELL' if nvt['interpretation'] == 'OVERVALUED' else 'BUY' if nvt['interpretation'] == 'UNDERVALUED' else 'HOLD',
            'nvt': nvt['nvt'],
            'confidence': 0.72
        }
