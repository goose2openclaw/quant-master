"""
Binary Betting - 二元预测投注
"""
from typing import Dict

class BinaryBetting:
    """
    二元投注
    是/否结果预测
    """
    def __init__(self):
        self.bets = {}
    
    def place_binary_bet(self, event_id: str, prediction: bool, stake: float, 
                        odds: float = 2.0) -> Dict:
        """下注"""
        return {
            'bet_id': f"BET_{event_id}_{prediction}",
            'event_id': event_id,
            'prediction': prediction,
            'stake': stake,
            'odds': odds,
            'potential_payout': stake * odds,
            'fee': stake * 0.02,
            'status': 'OPEN'
        }
    
    def settle_bet(self, bet_id: str, outcome: bool) -> Dict:
        """结算"""
        return {
            'bet_id': bet_id,
            'outcome': outcome,
            'result': 'WON' if outcome else 'LOST',
            'payout': 0,  # 如果输了
            'settled_at': __import__('time').time()
        }
    
    def calculate_kelly_criterion(self, odds: float, probability: float) -> float:
        """计算Kelly公式"""
        b = odds - 1  # 赔率净值
        p = probability  # 胜率
        q = 1 - p  # 败率
        
        kelly = (b * p - q) / b if b > 0 else 0
        return max(0, kelly)
    
    def get_bet_recommendation(self, odds: float, probability: float) -> Dict:
        """获取投注建议"""
        kelly = self.calculate_kelly_criterion(odds, probability)
        kelly_fraction = kelly * 0.25  # 半凯利
        
        edge = odds * probability - 1
        
        return {
            'odds': odds,
            'probability': probability,
            'edge': edge,
            'edge_pct': edge * 100,
            'kelly_fraction': kelly_fraction,
            'recommended_stake_pct': kelly_fraction * 100,
            'bet': 'YES' if edge > 0 else 'NO'
        }
