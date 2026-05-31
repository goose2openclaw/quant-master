"""
DEX Aggregator V2 - 下一代DEX聚合器
"""
from typing import Dict, List

class DEXAggregatorV2:
    """
    DEX聚合器V2
    0x/1inch/ParaSwap/LiFi聚合
    """
    def __init__(self):
        self.dexes = ['uniswap_v3', 'uniswap_v2', 'curve', 'balancer', 'sushiswap', 'dodo']
        self.algorithms = ['swap', 'split', 'merge']
    
    def quote(self, token_in: str, token_out: str, amount: float) -> List[Dict]:
        """获取报价"""
        quotes = []
        
        for dex in self.dexes:
            quotes.append({
                'dex': dex,
                'output_amount': amount * 0.995,
                'price_impact': 0.3,
                'gas_estimate': 150000
            })
        
        return sorted(quotes, key=lambda x: x['output_amount'], reverse=True)
    
    def find_optimal_route(self, token_in: str, token_out: str, amount: float) -> Dict:
        """找最优路由"""
        quotes = self.quote(token_in, token_out, amount)
        
        # 单一路由
        best_single = quotes[0] if quotes else None
        
        # 分割路由
        split_routes = []
        if len(quotes) >= 2:
            split_routes.append({
                'type': 'SPLIT',
                'routes': [
                    {'dex': quotes[0]['dex'], 'pct': 0.6, 'output': amount * 0.6 * 0.996},
                    {'dex': quotes[1]['dex'], 'pct': 0.4, 'output': amount * 0.4 * 0.994}
                ],
                'total_output': amount * 0.597,
                'savings_vs_single': amount * 0.002
            })
        
        return {
            'token_in': token_in,
            'token_out': token_out,
            'amount_in': amount,
            'best_single': best_single,
            'split_routes': split_routes,
            'recommendation': split_routes[0] if split_routes and split_routes[0]['total_output'] > best_single['output_amount'] else best_single
        }
