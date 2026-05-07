#!/usr/bin/env python3
"""
XIAMI Polymarket Arbitrage Module - 预测市场套利检测
集成 polymarket-arbitrage 技能功能
"""

import requests
import json
import os
from datetime import datetime

class PolymarketArbitrageScanner:
    """Polymarket 套利扫描器"""
    
    def __init__(self, data_dir=None):
        self.base_url = "https://gamma-api.polymarket.com"
        self.data_dir = data_dir or "/root/.openclaw/workspace/skills/polymarket-arbitrage/polymarket_data"
        self.fee_assumption = 2.0  # 2% taker fee
        
    def fetch_markets(self, limit=100):
        """抓取市场数据"""
        try:
            url = f"{self.base_url}/markets"
            params = {
                "limit": limit,
                "closed": "false",
                "orderBy": "volume24hr"
            }
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            
            markets = []
            for m in data:
                try:
                    outcomes = m.get('outcomes', [])
                    prices = m.get('outcomePrices', [])
                    
                    if not outcomes or not prices:
                        continue
                    
                    # 解析概率 - outcomePrices 是 JSON 字符串格式
                    probabilities = []
                    try:
                        # 解析外层字符串
                        if isinstance(prices, str):
                            prices = json.loads(prices)
                        
                        # 转换为浮点数 (概率是 0-1 范围)
                        for p in prices:
                            try:
                                prob = float(p)
                                probabilities.append(prob)
                            except:
                                continue
                    except Exception as e:
                        continue
                    
                    # 只处理二元市场 (Yes/No) 且概率和接近100%
                    if len(probabilities) != 2:
                        continue
                    
                    # 检查是否是有效的二元市场
                    prob_sum = sum(probabilities)
                    if prob_sum < 0.95 or prob_sum > 1.05:
                        continue
                    
                    market = {
                        'market_id': m.get('id', ''),
                        'title': m.get('question', ''),
                        'url': f"https://polymarket.com/market/{m.get('slug', m.get('id', ''))}",
                        'probabilities': probabilities,
                        'volume': float(m.get('volume24hr', 0)),
                        'volume_str': m.get('volume24hr', ''),
                        'outcome_count': len(probabilities),
                        'prob_sum': prob_sum,
                        'outcomes': outcomes,
                        'fetched_at': datetime.now().isoformat()
                    }
                    markets.append(market)
                except:
                    continue
            
            return markets
        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []
    
    def detect_arbitrage(self, markets, min_edge=2.0):
        """检测套利机会"""
        arbs = []
        
        for m in markets:
            probs = m['probabilities']
            prob_sum = m['prob_sum']
            
            if len(probs) < 2:
                continue
            
            # 计算费用 (概率是0-1范围)
            fee_multiplier = len(probs)
            # 转换为百分比: (1.0 - prob_sum) * 100
            gross_edge = (1.0 - prob_sum) * 100  # 百分比
            # 费用也是百分比
            net_edge = gross_edge - (self.fee_assumption * fee_multiplier)
            
            if net_edge >= min_edge:
                # 买入套利 (概率和 < 100%)
                arb = {
                    'type': 'math_arb_buy',
                    'market_id': m['market_id'],
                    'title': m['title'],
                    'url': m['url'],
                    'probabilities': probs,
                    'prob_sum': prob_sum,
                    'gross_edge_pct': gross_edge,
                    'net_profit_pct': net_edge,
                    'volume': m['volume'],
                    'outcome_count': len(probs),
                    'outcomes': m['outcomes'],
                    'risk_score': self._calculate_risk(m),
                    'action': 'buy_all_outcomes',
                    'allocation': self._calculate_allocation(probs)
                }
                arbs.append(arb)
            
            # 检测卖出套利 (概率和 > 100%)
            elif prob_sum > (1.0 + (self.fee_assumption / 100) * fee_multiplier):
                gross_edge = (prob_sum - 1.0) * 100
                net_edge = gross_edge - (self.fee_assumption * fee_multiplier)
                
                if net_edge >= min_edge:
                    arb = {
                        'type': 'math_arb_sell',
                        'market_id': m['market_id'],
                        'title': m['title'],
                        'url': m['url'],
                        'probabilities': probs,
                        'prob_sum': prob_sum,
                        'gross_edge_pct': gross_edge,
                        'net_profit_pct': net_edge,
                        'volume': m['volume'],
                        'outcome_count': len(probs),
                        'outcomes': m['outcomes'],
                        'risk_score': self._calculate_risk(m),
                        'action': 'sell_all_outcomes',
                        'warning': 'Requires liquidity and capital to collateralize'
                    }
                    arbs.append(arb)
        
        # 按净收益率排序
        arbs.sort(key=lambda x: x['net_profit_pct'], reverse=True)
        return arbs
    
    def _calculate_risk(self, market):
        """计算风险分数"""
        risk = 50  # 基础风险
        
        volume = market.get('volume', 0)
        if volume < 100000:
            risk += 20
        elif volume < 500000:
            risk += 10
            
        outcome_count = market.get('outcome_count', 2)
        if outcome_count > 2:
            risk += outcome_count * 5
            
        return min(risk, 100)
    
    def _calculate_allocation(self, probabilities):
        """计算最优分配"""
        inverse_probs = []
        for p in probabilities:
            if p > 0:
                inverse_probs.append(100 / p)
            else:
                inverse_probs.append(0)
        
        total = sum(inverse_probs)
        if total == 0:
            return [1/len(probabilities)] * len(probabilities)
        
        allocation = [ip / total for ip in inverse_probs]
        return allocation
    
    def scan(self, min_edge=2.0, limit=100):
        """完整扫描"""
        print(f"📡 Fetching markets...")
        markets = self.fetch_markets(limit=limit)
        
        if not markets:
            return {'error': 'No markets fetched', 'arbitrages': []}
        
        print(f"   Found {len(markets)} binary markets")
        print(f"🎯 Detecting arbitrage (min edge: {min_edge}%)...")
        
        arbs = self.detect_arbitrage(markets, min_edge)
        
        result = {
            'detected_at': datetime.now().isoformat(),
            'min_edge': min_edge,
            'fee_assumption': self.fee_assumption,
            'market_count': len(markets),
            'arbitrage_count': len(arbs),
            'arbitrages': arbs
        }
        
        return result
    
    def save_result(self, result, filename='xiami_arbs.json'):
        """保存结果"""
        os.makedirs(self.data_dir, exist_ok=True)
        path = os.path.join(self.data_dir, filename)
        with open(path, 'w') as f:
            json.dump(result, f, indent=2)
        return path


class XIAMIPolymarketArbitrage:
    """XIAMI 预测市场套利模块"""
    
    def __init__(self):
        self.scanner = PolymarketArbitrageScanner()
        
    def run(self, min_edge=2.0, save=True):
        """运行套利扫描"""
        print("\n" + "="*60)
        print("🔮 XIAMI Polymarket Arbitrage Scanner")
        print("="*60)
        
        result = self.scanner.scan(min_edge=min_edge)
        
        if save:
            path = self.scanner.save_result(result)
            print(f"\n💾 Results saved to: {path}")
        
        # 打印摘要
        print(f"\n📊 Scan Results:")
        print(f"   Markets scanned: {result.get('market_count', 0)}")
        print(f"   Arbitrage found: {result.get('arbitrage_count', 0)}")
        
        arbs = result.get('arbitrages', [])
        if arbs:
            print(f"\n⚡ Top Opportunities:")
            for i, arb in enumerate(arbs[:5], 1):
                print(f"\n{i}. {arb['title'][:60]}...")
                print(f"   Type: {arb['type']}")
                print(f"   Net profit: {arb['net_profit_pct']:.2f}%")
                print(f"   Volume: ${arb['volume']:,.0f}")
                print(f"   Risk: {arb['risk_score']}/100")
                print(f"   Action: {arb['action']}")
        
        return result


def main():
    import sys
    
    module = XIAMIPolymarketArbitrage()
    
    # 参数
    min_edge = 2.0
    if len(sys.argv) > 1:
        try:
            min_edge = float(sys.argv[1])
        except:
            pass
    
    result = module.run(min_edge=min_edge)
    
    # 返回状态码
    if result.get('arbitrage_count', 0) > 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
