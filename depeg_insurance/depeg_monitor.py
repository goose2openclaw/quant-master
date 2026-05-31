"""Depeg Insurance - 稳定币脱锚监控与保险"""
class DepegInsurance:
    def check_peg_status(self, stablecoin: str = 'USDT') -> dict:
        peg_ratio = 0.9998
        return {
            'stablecoin': stablecoin,
            'peg_ratio': peg_ratio,
            'deviation_bps': (1 - peg_ratio) * 10000,
            'status': 'PEGGED' if abs(1 - peg_ratio) < 0.001 else 'WARNING',
            'confidence': 95
        }
    
    def calculate_depeg_probability(self, stablecoin: str = 'USDT') -> dict:
        peg = self.check_peg_status(stablecoin)
        dev_bps = peg['deviation_bps']
        probability_30d = min(dev_bps / 100, 0.3) if dev_bps > 0 else 0.01
        probability_1y = min(dev_bps / 50, 0.6) if dev_bps > 0 else 0.05
        return {
            'stablecoin': stablecoin,
            'depeg_prob_30d': probability_30d,
            'depeg_prob_1y': probability_1y,
            'risk_level': 'HIGH' if probability_30d > 0.2 else 'MEDIUM' if probability_30d > 0.1 else 'LOW'
        }
    
    def get_insurance_premium(self, stablecoin: str, coverage: float) -> dict:
        prob = self.calculate_depeg_probability(stablecoin)
        expected_loss = prob['depeg_prob_1y'] * 0.1
        premium = coverage * expected_loss * 1.5
        return {
            'stablecoin': stablecoin,
            'coverage': coverage,
            'annual_premium': premium,
            'premium_pct': premium / coverage * 100
        }
