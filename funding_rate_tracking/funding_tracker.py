"""
Funding Rate Tracking - 永续合约资金费率追踪
"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class FundingRate:
    symbol: str
    rate: float  # e.g., 0.0001 = 0.01%
    next_funding_time: float
    exchange: str

class FundingRateTracker:
    """
    资金费率追踪
    发现资金费率套利机会
    """
    def __init__(self):
        self.rates = {}  # {symbol: FundingRate}
        self.history = []
        self.alerts = []
    
    def fetch_funding_rates(self, exchange: str = 'binance') -> Dict[str, float]:
        """获取资金费率"""
        # 简化: 模拟数据
        rates = {
            'BTCUSDT': 0.0001,
            'ETHUSDT': 0.0002,
            'BNBUSDT': -0.0003,  # 负费率表示多头支付空头
            'SOLUSDT': 0.0005,
            'DOGEUSDT': 0.001,
            'XRPUSDT': -0.0001,
        }
        return rates
    
    def find_arbitrage_opportunities(self, threshold: float = 0.0005) -> List[Dict]:
        """找套利机会"""
        opportunities = []
        rates = self.fetch_funding_rates()
        
        for symbol, rate in rates.items():
            if abs(rate) > threshold:
                opportunity = {
                    'symbol': symbol,
                    'funding_rate': rate,
                    'annualized_rate': rate * 3 * 365,  # 每8小时一次
                    'direction': 'SHORT' if rate > 0 else 'LONG',
                    'exchange': 'binance'
                }
                opportunities.append(opportunity)
        
        return sorted(opportunities, key=lambda x: abs(x['annualized_rate']), reverse=True)
    
    def track_funding_convergence(self, symbol: str) -> Dict:
        """追踪资金费率收敛"""
        hist = [r for r in self.history if r['symbol'] == symbol]
        
        if len(hist) < 10:
            return {'status': 'insufficient_data'}
        
        recent_avg = sum(h['rate'] for h in hist[-10:]) / 10
        current = self.rates.get(symbol, FundingRate(symbol, 0, 0, ''))
        
        return {
            'symbol': symbol,
            'current_rate': current.rate,
            'recent_avg': recent_avg,
            'deviation': abs(current.rate - recent_avg),
            'converging': abs(current.rate) < abs(recent_avg)
        }
    
    def generate_funding_report(self) -> Dict:
        """生成资金费率报告"""
        opportunities = self.find_arbitrage_opportunities()
        
        return {
            'timestamp': __import__('time').time(),
            'total_pairs': len(self.rates),
            'high_funding_pairs': len(opportunities),
            'opportunities': opportunities[:10],
            'long_pay': [o for o in opportunities if o['direction'] == 'LONG'],
            'short_pay': [o for o in opportunities if o['direction'] == 'SHORT']
        }
