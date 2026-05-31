"""
Signal Aggregation - 多源信号聚合引擎
"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Signal:
    source: str
    symbol: str
    direction: str  # BUY/SELL/NEUTRAL
    strength: float  # 0-100
    timestamp: float

class SignalAggregator:
    """
    多源信号聚合
    整合技术/量化/情绪/链上信号
    """
    def __init__(self):
        self.signals = []
        self.weights = {
            'technical': 0.25,
            'onchain': 0.25,
            'sentiment': 0.20,
            'funding': 0.15,
            'whale': 0.15
        }
    
    def add_signal(self, source: str, symbol: str, direction: str, strength: float):
        """添加信号"""
        signal = Signal(
            source=source,
            symbol=symbol,
            direction=direction,
            strength=strength,
            timestamp=__import__('time').time()
        )
        self.signals.append(signal)
    
    def get_aggregated_signal(self, symbol: str) -> Dict:
        """获取聚合信号"""
        symbol_signals = [s for s in self.signals if s.symbol == symbol]
        
        if not symbol_signals:
            return {'signal': 'NEUTRAL', 'confidence': 0}
        
        buy_signals = [s for s in symbol_signals if s.direction == 'BUY']
        sell_signals = [s for s in symbol_signals if s.direction == 'SELL']
        
        buy_strength = sum(s.strength * self.weights.get(s.source, 0.1) for s in buy_signals)
        sell_strength = sum(s.strength * self.weights.get(s.source, 0.1) for s in sell_signals)
        
        total = buy_strength + sell_strength
        if total == 0:
            return {'signal': 'NEUTRAL', 'confidence': 0}
        
        net = (buy_strength - sell_strength) / total
        
        if net > 0.2:
            return {'signal': 'BUY', 'confidence': abs(net) * 100, 'net': net}
        elif net < -0.2:
            return {'signal': 'SELL', 'confidence': abs(net) * 100, 'net': net}
        else:
            return {'signal': 'NEUTRAL', 'confidence': 100 - abs(net) * 100, 'net': net}
    
    def get_signal_summary(self, symbol: str) -> Dict:
        """获取信号摘要"""
        agg = self.get_aggregated_signal(symbol)
        symbol_signals = [s for s in self.signals if s.symbol == symbol]
        
        return {
            'symbol': symbol,
            'aggregated_signal': agg['signal'],
            'confidence': round(agg['confidence'], 1),
            'signal_count': len(symbol_signals),
            'buy_signals': len([s for s in symbol_signals if s.direction == 'BUY']),
            'sell_signals': len([s for s in symbol_signals if s.direction == 'SELL']),
            'sources': list(set(s.source for s in symbol_signals))
        }
