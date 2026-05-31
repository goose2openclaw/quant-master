"""
Quant Prediction Bridge - 量化策略与预测市场桥接
"""
from typing import Dict

class QuantPredictionBridge:
    """
    量化预测桥接
    将量化信号转为预测市场头寸
    """
    def __init__(self):
        self.signals = {}
        self.positions = {}
    
    def convert_signal_to_bet(self, signal: Dict, market_id: str) -> Dict:
        """转换信号为投注"""
        confidence = signal.get('confidence', 0.5)
        direction = signal.get('direction', 'NEUTRAL')
        
        if direction == 'BUY':
            prediction = confidence
            size = min(confidence * 1000, 10000)
        elif direction == 'SELL':
            prediction = 1 - confidence
            size = min((1 - confidence) * 1000, 10000)
        else:
            return {'action': 'NO_BET'}
        
        return {
            'market_id': market_id,
            'prediction': prediction,
            'recommended_size': size,
            'kelly_fraction': confidence * 2 - 1 if confidence > 0.5 else 0,
            'expected_value': (prediction * 2 - 1) * size
        }
    
    def hedge_prediction_with_quant(self, prediction_market_pos: Dict, 
                                  quant_signal: Dict) -> Dict:
        """用量化信号对冲预测市场头寸"""
        pred_size = prediction_market_pos.get('size', 0)
        quant_conf = quant_signal.get('confidence', 0.5)
        
        hedge_ratio = abs(quant_conf - 0.5) * 0.5
        
        return {
            'original_position': prediction_market_pos,
            'hedge_ratio': hedge_ratio,
            'hedge_size': pred_size * hedge_ratio,
            'net_exposure': pred_size * (1 - hedge_ratio),
            'risk_reduction_pct': hedge_ratio * 100
        }
    
    def aggregate_quant_signals(self, signals: List[Dict]) -> Dict:
        """聚合量化信号"""
        if not signals:
            return {'direction': 'NEUTRAL', 'confidence': 0.5}
        
        buy_signals = [s for s in signals if s.get('direction') == 'BUY']
        sell_signals = [s for s in signals if s.get('direction') == 'SELL']
        
        avg_buy_conf = sum(s['confidence'] for s in buy_signals) / len(buy_signals) if buy_signals else 0
        avg_sell_conf = sum(s['confidence'] for s in sell_signals) / len(sell_signals) if sell_signals else 0
        
        net = (len(buy_signals) * avg_buy_conf - len(sell_signals) * avg_sell_conf) / len(signals) if signals else 0
        
        return {
            'total_signals': len(signals),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'aggregate_direction': 'BUY' if net > 0.1 else 'SELL' if net < -0.1 else 'NEUTRAL',
            'aggregate_confidence': abs(net)
        }
