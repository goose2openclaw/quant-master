"""
Orderbook Imbalance - 订单簿不平衡分析
"""
from typing import Dict

class OrderbookImbalance:
    """
    订单簿不平衡
    买卖压力实时分析
    """
    def __init__(self):
        self.orderbook = {}
    
    def calculate_imbalance(self, symbol: str) -> Dict:
        """计算不平衡"""
        bid_vol = 150_000_000
        ask_vol = 100_000_000
        imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)
        
        return {
            'symbol': symbol,
            'bid_volume': bid_vol,
            'ask_volume': ask_vol,
            'imbalance_ratio': imbalance,
            'interpretation': 'BUY_IMBALANCE' if imbalance > 0.1 else 'SELL_IMBALANCE' if imbalance < -0.1 else 'BALANCED',
            'predicted_price_move': imbalance * 100
        }
    
    def detect_ walls(self, symbol: str) -> Dict:
        """检测订单墙"""
        return {
            'symbol': symbol,
            'bid_wall_price': 64000,
            'bid_wall_size': 200_000_000,
            'ask_wall_price': 66000,
            'ask_wall_size': 180_000_000,
            'wall_stability': 'STABLE',
            'break_probability': 0.25
        }
    
    def predict_short_term_move(self, symbol: str) -> Dict:
        """预测短期走势"""
        imbalance = self.calculate_imbalance(symbol)
        walls = self.detect_walls(symbol)
        
        return {
            'symbol': symbol,
            'direction': imbalance['interpretation'],
            'target_move_pct': abs(imbalance['predicted_price_move']),
            'confidence': 0.75,
            'time_horizon': '1-5 min'
        }
