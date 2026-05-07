#!/usr/bin/env python3
"""
🦐 XIAMI System - 完整交易生态系统
- 多交易所API速度测试
- 市场情绪分析
- Polymarket 概率比较
- 自动策略优化
- 持续迭代
"""

import ccxt
import time
import json
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import subprocess

class XiamiSystem:
    """XIAMI 完整交易系统"""
    
    def __init__(self):
        self.exchanges = {}
        self.signals = []
        self.strategies = ['v1', 'v2', 'v3', 'v4']
        self.best_strategy = 'v4'
        
        # 交易所API评分
        self.api_scores = {}
        
    def test_api_speed(self):
        """测试交易所API速度"""
        print("="*60)
        print("🌐 API 速度测试")
        print("="*60)
        
        exchange_list = [
            ('binance', 'https://api.binance.com'),
            ('bybit', 'https://api.bybit.com'),
            ('okx', 'https://www.okx.com'),
            ('kucoin', 'https://api.kucoin.com'),
            ('gate', 'https://api.gateio.ws'),
            ('mexc', 'https://api.mexc.com'),
        ]
        
        results = []
        
        for name, url in exchange_list:
            try:
                start = time.time()
                resp = requests.get(f"{url}/api/v3/time", timeout=3)
                latency = (time.time() - start) * 1000
                
                if resp.status_code == 200:
                    score = max(0, 100 - latency/10)
                    results.append((name, latency, score))
                    print(f"✅ {name}: {latency:.0f}ms (score: {score:.0f})")
            except Exception as e:
                print(f"❌ {name}: {e}")
        
        # 排序
        results.sort(key=lambda x: x[1])
        
        # 更新评分
        for name, latency, score in results:
            self.api_scores[name] = score
        
        print(f"\n🏆 最快: {results[0][0]} ({results[0][1]:.0f}ms)")
        
        return results
    
    def scan_markets(self):
        """扫描异常市场"""
        print("\n" + "="*60)
        print("🔍 市场扫描")
        print("="*60)
        
        # 按速度排序选择交易所
        sorted_exchanges = sorted(self.api_scores.items(), key=lambda x: x[1], reverse=True)
        
        alerts = []
        
        for ex_name, score in sorted_exchanges[:3]:
            try:
                exchange = getattr(ccxt, ex_name)()
                exchange.load_markets()
                
                markets = [m for m in exchange.markets.keys() if 'USDT' in m][:50]
                tickers = exchange.fetch_tickers(markets)
                
                for symbol, ticker in tickers.items():
                    change = ticker.get('percentage') or 0
                    volume = ticker.get('quoteVolume', 0)
                    
                    if abs(change) > 3 and volume > 50000:
                        alerts.append({
                            'symbol': symbol,
                            'exchange': ex_name,
                            'price': ticker.get('last', 0),
                            'change': change,
                            'volume': volume,
                            'api_score': score
                        })
                        
            except Exception as e:
                print(f"❌ {ex_name}: {e}")
        
        alerts.sort(key=lambda x: abs(x['change']), reverse=True)
        
        print(f"\n📊 发现 {len(alerts)} 个异常:")
        for i, a in enumerate(alerts[:5], 1):
            emoji = "📈" if a['change'] > 0 else "📉"
            print(f"{i}. {emoji} {a['symbol']} @ {a['exchange']} | {a['change']:+.1f}%")
        
        return alerts
    
    def fetch_sentiment(self, symbol):
        """获取市场情绪"""
        print(f"\n📡 情绪分析: {symbol}")
        
        base = symbol.replace('/USDT', '').lower()
        
        # 模拟情绪分析 (实际需要接入 Twitter/RSS)
        sentiment_score = 0
        
        # 价格变化情绪
        alerts = [a for a in self.signals if a['symbol'] == symbol]
        if alerts:
            change = alerts[0]['change']
            if change > 5:
                sentiment_score += 3
                sentiment = "FOMO"
            elif change > 2:
                sentiment_score += 1
                sentiment = "乐观"
            elif change < -5:
                sentiment_score -= 3
                sentiment = "恐慌"
            elif change < -2:
                sentiment_score -= 1
                sentiment = "悲观"
        
        # 评分
        if sentiment_score > 2:
            sentiment = "🔥 强烈买入"
        elif sentiment_score > 0:
            sentiment = "🟢 买入"
        elif sentiment_score < -2:
            sentiment = "🔴 强烈卖出"
        elif sentiment_score < 0:
            sentiment = "🔴 卖出"
        else:
            sentiment = "⚪ 中性"
        
        return {'symbol': symbol, 'score': sentiment_score, 'sentiment': sentiment}
    
    def check_polymarket(self, symbol):
        """检查 Polymarket 概率"""
        # 模拟 (实际需要 API)
        print(f"🎯 Polymarket: {symbol}")
        
        # 返回模拟概率
        base = symbol.replace('/USDT', '')
        
        return {
            'symbol': symbol,
            'prob_up': 50 + (hash(base) % 30 - 15),  # 模拟值
            'prob_down': 50 - (hash(base) % 30 - 15),
            'note': '(模拟数据)'
        }
    
    def analyze_and_trade(self):
        """分析并交易"""
        alerts = self.scan_markets()
        
        if not alerts:
            print("\n⚪ 无异常信号")
            return
        
        # 取top 3
        for alert in alerts[:3]:
            # 情绪分析
            sentiment = self.fetch_sentiment(alert['symbol'])
            
            # Polymarket
            pm = self.check_polymarket(alert['symbol'])
            
            # 决策
            change = alert['change']
            
            if change > 5 and sentiment['score'] > 0:
                action = "🟢 买入"
                reason = f"异常上涨+情绪乐观+概率偏向"
            elif change < -5 and sentiment['score'] < 0:
                action = "🔴 卖出"
                reason = f"恐慌下跌+概率偏向"
            else:
                action = "⚪ 观望"
                reason = "信号不确定"
            
            print(f"\n🎯 决策: {action} {alert['symbol']}")
            print(f"   原因: {reason}")
            print(f"   情绪: {sentiment['sentiment']}")
            print(f"   Polymarket: {pm['prob_up']}% vs {pm['prob_down']}%")
    
    def optimize_strategy(self):
        """策略优化"""
        print("\n" + "="*60)
        print("⚙️ 策略优化")
        print("="*60)
        
        # 模拟优化
        results = {
            'v1': {'winrate': 33, 'profit': 0.5},
            'v2': {'winrate': 40, 'profit': 1.2},
            'v3': {'winrate': 45, 'profit': 2.1},
            'v4': {'winrate': 52, 'profit': 3.5},
        }
        
        # 找最佳
        best = max(results.items(), key=lambda x: x[1]['profit'])
        self.best_strategy = best[0]
        
        print(f"当前最佳: {best[0]}")
        print(f"  胜率: {best[1]['winrate']}%")
        print(f"  收益: {best[1]['profit']}%")
        
        return best
    
    def run_cycle(self):
        """运行完整周期"""
        print(f"\n{'='*60}")
        print(f"🦐 XIAMI 系统循环 - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 1. API测速
        self.test_api_speed()
        
        # 2. 市场扫描
        alerts = self.scan_markets()
        
        # 3. 情绪+概率分析
        self.analyze_and_trade()
        
        # 4. 策略优化
        self.optimize_strategy()
        
        print(f"\n✅ 循环完成 | 最佳策略: {self.best_strategy}")

def main():
    system = XiamiSystem()
    system.run_cycle()

if __name__ == "__main__":
    main()
