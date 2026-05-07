#!/usr/bin/env python3
"""
🦐 XIAMI 完整交易系统 v4
- 多数据源
- 智能执行
- 风险管理
"""

import json
import ccxt
import time
from datetime import datetime

class XiamiV4:
    """XIAMI v4"""
    
    def __init__(self):
        with open('skills/xiami/data/trend_database.json', 'r') as f:
            self.trends = json.load(f)
        
        with open('skills/xiami/data/config.json', 'r') as f:
            self.config = json.load(f)
        
        self.api_priority = self.config['api_priority']
        self.risk = self.config['risk_management']
        
    def get_best_api(self):
        """获取最快API"""
        for ex in self.api_priority['tier1']:
            try:
                e = getattr(ccxt, ex)()
                start = time.time()
                e.fetch_time()
                latency = (time.time() - start) * 1000
                if latency < 1000:
                    return ex, latency
            except:
                continue
        return 'binance', 999
    
    def calculate_position(self, confidence):
        """根据置信度计算仓位"""
        sizes = self.risk['position_size_by_confidence']
        return sizes.get(str(confidence), 0.05)
    
    def get_stop_loss(self, timeframe):
        """获取止损"""
        return self.risk['stop_loss'].get(timeframe, 0.02)
    
    def get_take_profit(self, timeframe):
        """获取止盈"""
        return self.risk['take_profit'].get(timeframe, 0.05)
    
    def run_scan(self):
        """运行扫描"""
        print("="*60)
        print("🦐 XIAMI v4 - 完整交易系统")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # API测速
        best_api, latency = self.get_best_api()
        print(f"\n🌐 最佳API: {best_api} ({latency:.0f}ms)")
        
        # 扫描
        try:
            e = getattr(ccxt, best_api)()
            e.load_markets()
            
            tickers = e.fetch_tickers(['BTC/USDT', 'ETH/USDT', 'SOL/USDT'])
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage', 0)
                volume = ticker.get('quoteVolume', 0)
                
                print(f"\n📡 {symbol}:")
                print(f"   价格: ${ticker.get('last', 0):.2f}")
                print(f"   涨跌: {change:+.2f}%")
                print(f"   成交量: ${volume/1e6:.1f}M")
                
                # 匹配趋势
                matched = self.match_trends(change, volume)
                
                if matched:
                    for m in matched[:2]:
                        print(f"   🎯 {m['name']} (置信度: {m['confidence']})")
                        
                        # 计算交易参数
                        position = self.calculate_position(m['confidence'])
                        sl = self.get_stop_loss(m['timeframe'])
                        tp = self.get_take_profit(m['timeframe'])
                        
                        print(f"   💰 建议仓位: {position*100:.0f}%")
                        print(f"   🛡️ 止损: {sl*100:.1f}% | 止盈: {tp*100:.1f}%")
                        
        except Exception as ex:
            print(f"❌ 错误: {ex}")
    
    def match_trends(self, change, volume):
        """匹配趋势"""
        # 简化匹配逻辑
        if abs(change) > 5 and volume > 1000000:
            return [{'name': '动量突破', 'confidence': 6, 'timeframe': '15m'}]
        elif abs(change) > 3:
            return [{'name': '趋势', 'confidence': 5, 'timeframe': '1h'}]
        return []

if __name__ == "__main__":
    xiami = XiamiV4()
    xiami.run_scan()
