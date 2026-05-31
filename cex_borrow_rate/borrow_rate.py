"""
CEX Borrow Rate - 交易所借贷利率追踪
"""
from typing import Dict, List

class CEXBorrowRate:
    """
    交易所借贷利率
    逐交易所/逐币种费率追踪
    """
    def __init__(self):
        self.rates = {}
    
    def get_borrow_rates(self, exchange: str = 'binance') -> Dict:
        """获取借贷利率"""
        return {
            'BTC': {'borrow_rate': 0.0005, 'available': 100_000_000},
            'ETH': {'borrow_rate': 0.0006, 'available': 80_000_000},
            'USDT': {'borrow_rate': 0.001, 'available': 500_000_000},
            'SOL': {'borrow_rate': 0.0008, 'available': 20_000_000}
        }
    
    def find_borrow_rate_arb(self) -> List[Dict]:
        """找借贷利率套利"""
        opportunities = []
        exchanges = ['binance', 'bybit', 'okx']
        
        for ex in exchanges:
            rates = self.get_borrow_rates(ex)
            for sym, data in rates.items():
                if data['borrow_rate'] > 0.001:
                    opportunities.append({
                        'symbol': sym,
                        'exchange': ex,
                        'borrow_rate': data['borrow_rate'],
                        'annual_rate': data['borrow_rate'] * 365 * 100,
                        'opportunity': 'HIGH_BORROW_COST'
                    })
        
        return sorted(opportunities, key=lambda x: x['annual_rate'], reverse=True)
    
    def detect_rate_anomaly(self) -> List[Dict]:
        """检测利率异常"""
        rates = self.get_borrow_rates()
        anomalies = []
        
        for sym, data in rates.items():
            if data['borrow_rate'] > 0.002:  # 高于0.2%日利率
                anomalies.append({
                    'symbol': sym,
                    'rate': data['borrow_rate'],
                    'annual_rate': data['borrow_rate'] * 365 * 100,
                    'reason': 'SUPPLY_DEMAND_IMBALANCE'
                })
        
        return anomalies
