#!/usr/bin/env python3
"""
XIAMI Polymarket Integration - 预测市场交易系统
"""

import requests
import json
from datetime import datetime

class PolymarketClient:
    def __init__(self, api_key=None):
        self.base_url = "https://clob.polymarket.com"
        self.markets_url = "https://gamma-api.polymarket.com"
        self.api_key = api_key
        
    def get_markets(self, limit=20):
        """获取活跃市场"""
        try:
            url = f"{self.markets_url}/markets"
            params = {
                "limit": limit,
                "closed": "false",
                "orderBy": "volume24hr"
            }
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            markets = []
            for m in data[:limit]:
                markets.append({
                    'id': m.get('id'),
                    'question': m.get('question'),
                    'volume': m.get('volume24hr', 0),
                    'liquidity': m.get('liquidity', 0),
                    'endDate': m.get('endDate'),
                    'outcomePrices': m.get('outcomePrices', [])
                })
            return markets
        except Exception as e:
            return {'error': str(e)}
    
    def get_market_details(self, condition_id):
        """获取市场详情"""
        try:
            url = f"{self.markets_url}/markets/{condition_id}"
            resp = requests.get(url, timeout=10)
            return resp.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_order_book(self, condition_id):
        """获取订单簿"""
        try:
            url = f"{self.base_url}/orderbook"
            params = {"conditionId": condition_id}
            resp = requests.get(url, params=params, timeout=10)
            return resp.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_price(self, condition_id):
        """获取当前价格"""
        try:
            book = self.get_order_book(condition_id)
            if 'error' in book:
                return None
            
            bids = book.get('bids', [])
            asks = book.get('asks', [])
            
            best_bid = float(bids[0]['price']) if bids else None
            best_ask = float(asks[0]['price']) if asks else None
            
            if best_bid and best_ask:
                mid_price = (best_bid + best_ask) / 2
                return {
                    'bid': best_bid,
                    'ask': best_ask,
                    'mid': mid_price,
                    'spread': (best_ask - best_bid) / mid_price * 100
                }
            return None
        except:
            return None
    
    def get_trending_markets(self, limit=10):
        """获取热门市场"""
        markets = self.get_markets(limit=50)
        
        if isinstance(markets, dict) and 'error' in markets:
            return markets
        
        # 按成交量排序
        markets.sort(key=lambda x: x.get('volume', 0), reverse=True)
        
        return markets[:limit]
    
    def analyze_market(self, market):
        """分析市场机会"""
        question = market.get('question', '')
        prices = market.get('outcomePrices', [])
        
        if not prices:
            return None
        
        try:
            prices = [float(p) for p in prices]
            max_price = max(prices)
            min_price = min(prices)
            
            # 检测套利机会
            if max_price + min_price < 0.95:
                return {
                    'type': 'arbitrage',
                    'probability': max_price,
                    'gap': 1 - (max_price + min_price),
                    'question': question
                }
            
            # 检测高置信度
            if max_price > 0.8:
                return {
                    'type': 'high_confidence',
                    'outcome': 'YES' if prices.index(max_price) == 0 else 'NO',
                    'probability': max_price,
                    'question': question
                }
            
            return None
        except:
            return None


class PredictionTrader:
    """预测交易员"""
    
    def __init__(self, client):
        self.client = client
        
    def scan_opportunities(self, limit=20):
        """扫描交易机会"""
        markets = self.client.get_trending_markets(limit)
        
        if isinstance(markets, dict) and 'error' in markets:
            return markets
        
        opportunities = []
        
        for market in markets:
            analysis = self.client.analyze_market(market)
            if analysis:
                analysis['volume'] = market.get('volume', 0)
                analysis['liquidity'] = market.get('liquidity', 0)
                opportunities.append(analysis)
        
        return opportunities
    
    def get_prediction_signals(self):
        """获取预测信号"""
        markets = self.client.get_trending_markets(limit=15)
        
        if isinstance(markets, dict) and 'error' in markets:
            return markets
        
        signals = []
        
        for m in markets:
            question = m.get('question', '')
            prices = m.get('outcomePrices', [])
            volume = m.get('volume', 0)
            
            if prices and len(prices) >= 2:
                try:
                    yes_price = float(prices[0])
                    no_price = float(prices[1]) if len(prices) > 1 else 1 - yes_price
                    
                    # 生成信号
                    if yes_price > 0.7:
                        signals.append({
                            'question': question,
                            'signal': 'YES',
                            'probability': yes_price,
                            'volume': volume,
                            'confidence': 'high' if yes_price > 0.85 else 'medium'
                        })
                    elif no_price > 0.7:
                        signals.append({
                            'question': question,
                            'signal': 'NO',
                            'probability': no_price,
                            'volume': volume,
                            'confidence': 'high' if no_price > 0.85 else 'medium'
                        })
                except:
                    continue
        
        return signals


def main():
    import sys
    
    client = PolymarketClient()
    trader = PredictionTrader(client)
    
    if len(sys.argv) < 2:
        print("""
🔮 XIAMI Polymarket Integration

用法:
  python polymarket.py markets [limit]
  python polymarket.py trending [limit]
  python polymarket.py scan
  python polymarket.py signals

示例:
  python polymarket.py markets 10
  python polymarket.py trending
  python polymarket.py scan
  python polymarket.py signals
""")
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'markets':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        markets = client.get_markets(limit)
        
        if isinstance(markets, dict) and 'error' in markets:
            print(f"错误: {markets['error']}")
            return
        
        print(f"\n📊 Polymarket 活跃市场 (Top {len(markets)})")
        for i, m in enumerate(markets[:10], 1):
            print(f"\n{i}. {m.get('question')[:60]}...")
            print(f"   成交量: ${m.get('volume', 0):,.0f}")
            print(f"   流动性: ${m.get('liquidity', 0):,.0f}")
    
    elif cmd == 'trending':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        markets = client.get_trending_markets(limit)
        
        if isinstance(markets, dict) and 'error' in markets:
            print(f"错误: {markets['error']}")
            return
        
        print(f"\n🔥 热门市场 (Top {len(markets)})")
        for i, m in enumerate(markets, 1):
            print(f"{i}. {m.get('question')[:50]}...")
            print(f"   成交量: ${m.get('volume', 0):,.0f}")
    
    elif cmd == 'scan':
        opportunities = trader.scan_opportunities()
        
        if isinstance(opportunities, dict) and 'error' in opportunities:
            print(f"错误: {opportunities['error']}")
            return
        
        print(f"\n🎯 扫描到 {len(opportunities)} 个机会")
        
        for o in opportunities:
            if o['type'] == 'arbitrage':
                print(f"\n⚡ 套利机会")
                print(f"   问题: {o['question'][:50]}...")
                print(f"   概率差: {o['gap']*100:.2f}%")
            
            elif o['type'] == 'high_confidence':
                print(f"\n🎯 高置信度信号")
                print(f"   问题: {o['question'][:50]}...")
                print(f"   信号: {o['outcome']} ({o['probability']*100:.0f}%)")
    
    elif cmd == 'signals':
        signals = trader.get_prediction_signals()
        
        if isinstance(signals, dict) and 'error' in signals:
            print(f"错误: {signals['error']}")
            return
        
        print(f"\n📡 预测信号 ({len(signals)}个)")
        
        for s in signals:
            emoji = "🟢" if s['signal'] == 'YES' else "🔴"
            print(f"\n{emoji} {s['question'][:50]}...")
            print(f"   信号: {s['signal']} ({s['probability']*100:.0f}%)")
            print(f"   置信度: {s['confidence']} | 成交量: ${s['volume']:,.0f}")


if __name__ == '__main__':
    main()
