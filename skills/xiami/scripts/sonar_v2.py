#!/usr/bin/env python3
"""
🦐 XIAMI 声纳系统 v2
- 完整趋势匹配
- 执行矩阵自动调整
- 多市场支持
"""

import json
import ccxt
import time
from datetime import datetime

class XiamiSonarV2:
    """声纳系统 v2"""
    
    def __init__(self):
        with open('skills/xiami/data/trend_database.json', 'r') as f:
            self.db = json.load(f)
        
        self.execution_matrix = self.db.get('execution_matrix', {})
    
    def get_trends(self, market='crypto'):
        return self.db.get(f'{market}_trends', {})
    
    def get_execution_params(self, timeframe):
        """根据时间框架获取执行参数"""
        matrix = self.execution_matrix.get(timeframe, {
            'quant_interval_ms': 500,
            'duration_sec': 60,
            'risk': '中'
        })
        
        return {
            'interval_ms': matrix.get('quant_interval_ms', 500),
            'duration_sec': matrix.get('duration_sec', 60),
            'risk': matrix.get('risk', '中'),
            'timeframe': timeframe
        }
    
    def match_trends(self, indicators, market='crypto'):
        """匹配趋势"""
        trends = self.get_trends(market)
        matched = []
        
        for name, info in trends.items():
            score = 0
            matched_indicators = []
            
            # RSI
            if 'RSI' in indicators and 'RSI' in str(info.get('indicators', [])):
                rsi = indicators['RSI']
                if rsi < 30:
                    score += 3
                    matched_indicators.append('RSI超卖')
                elif rsi > 70:
                    score += 3
                    matched_indicators.append('RSI超买')
            
            # MACD
            if 'MACD' in indicators:
                macd = indicators['MACD']
                if 'MACD' in str(info.get('indicators', [])):
                    if macd > 0:
                        score += 2
                        matched_indicators.append('MACD金叉')
            
            # Volume
            if 'Volume_Ratio' in indicators and 'Volume' in str(info.get('indicators', [])):
                vr = indicators['Volume_Ratio']
                if vr > 2:
                    score += 3
                    matched_indicators.append('成交量激增')
            
            if score > 0:
                # 获取最佳时间框架
                tfs = info.get('timeframes', {})
                if tfs:
                    best_tf = list(tfs.keys())[0]
                    exec_params = self.get_execution_params(best_tf)
                    
                    matched.append({
                        'name': name,
                        'display_name': info.get('name', name),
                        'score': score,
                        'indicators': matched_indicators,
                        'timeframe': best_tf,
                        'profit_target': tfs[best_tf].get('profit_target', ''),
                        'reliability': info.get('reliability', '中'),
                        'execution': exec_params
                    })
        
        return sorted(matched, key=lambda x: x['score'], reverse=True)
    
    def scan_market(self, market='crypto'):
        """扫描市场"""
        print(f"\n{'='*60}")
        print(f"🔊 XIAMI 声纳扫描 - {market.upper()}")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        try:
            e = ccxt.binance()
            e.load_markets()
            
            symbols = {
                'crypto': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
                'stock': ['AAPL', 'MSFT', 'GOOGL'],
            }.get(market, ['BTC/USDT'])
            
            for symbol in symbols:
                try:
                    ticker = e.fetch_ticker(symbol)
                    
                    change = ticker.get('percentage', 0)
                    volume = ticker.get('quoteVolume', 0)
                    
                    indicators = {
                        'RSI': 50 + (change * 0.5),
                        'MACD': change * 5,
                        'Volume_Ratio': volume / 1000000
                    }
                    
                    matched = self.match_trends(indicators, market)
                    
                    if matched:
                        print(f"\n📡 {symbol}:")
                        print(f"   涨跌: {change:+.1f}% | 成交量: ${volume/1e6:.1f}M")
                        
                        for m in matched[:2]:
                            print(f"   🎯 {m['display_name']} (匹配度: {m['score']})")
                            print(f"      目标: {m['profit_target']}")
                            print(f"      执行: 每{m['execution']['interval_ms']}ms, {m['execution']['duration_sec']}s")
                            print(f"      风险: {m['execution']['risk']}")
                
                except Exception as ex:
                    print(f"❌ {symbol}: {ex}")
        
        except Exception as e:
            print(f"❌ 扫描错误: {e}")
        
        print(f"\n{'='*60}")

def main():
    sonar = XiamiSonarV2()
    
    # 扫描各市场
    sonar.scan_market('crypto')
    sonar.scan_market('stock')

if __name__ == "__main__":
    main()
