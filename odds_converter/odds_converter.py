"""
Odds Converter - 赔率格式转换
"""
from typing import Dict

class OddsConverter:
    """
    赔率转换
    Decimal/American/Fractional互转
    """
    def __init__(self):
        self.formats = ['DECIMAL', 'AMERICAN', 'FRACTIONAL', 'PROBABILITY']
    
    def decimal_to_american(self, decimal: float) -> float:
        """Decimal转American"""
        if decimal >= 2.0:
            return (decimal - 1) * 100
        else:
            return -100 / (decimal - 1)
    
    def american_to_decimal(self, american: float) -> float:
        """American转Decimal"""
        if american > 0:
            return 1 + american / 100
        else:
            return 1 + 100 / abs(american)
    
    def decimal_to_probability(self, decimal: float) -> float:
        """Decimal转概率"""
        return 1 / decimal if decimal > 0 else 0
    
    def probability_to_decimal(self, prob: float) -> float:
        """概率转Decimal"""
        return 1 / prob if prob > 0 else 0
    
    def convert_odds(self, odds: float, from_format: str, to_format: str) -> float:
        """转换赔率格式"""
        prob = self.decimal_to_probability(
            self.american_to_decimal(odds) if from_format == 'AMERICAN' else odds
        )
        
        if to_format == 'PROBABILITY':
            return prob
        elif to_format == 'DECIMAL':
            return self.probability_to_decimal(prob)
        elif to_format == 'AMERICAN':
            return self.decimal_to_american(self.probability_to_decimal(prob))
        
        return odds
    
    def calculate_payout(self, stake: float, odds: float, format: str = 'DECIMAL') -> Dict:
        """计算支付"""
        decimal = self.american_to_decimal(odds) if format == 'AMERICAN' else odds
        profit = stake * (decimal - 1)
        
        return {
            'stake': stake,
            'decimal_odds': decimal,
            'profit': profit,
            'total_return': stake + profit,
            'implied_probability': 1 / decimal
        }
