#!/usr/bin/env python3
"""
趋势数据库管理器
- 加载趋势模型
- 匹配当前市场
- 生成交易信号
"""

import json
from datetime import datetime

class TrendDatabase:
    """趋势数据库"""
    
    def __init__(self, db_path='data/trend_database.json'):
        self.db_path = db_path
        self.data = self.load()
    
    def load(self):
        """加载数据库"""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def get_trends(self, market_type='crypto'):
        """获取趋势类型"""
        return self.data.get(f'{market_type}_trends', {})
    
    def match_indicators(self, indicators, trend_type, market_type='crypto'):
        """匹配指标"""
        trends = self.get_trends(market_type)
        
        if trend_type not in trends:
            return None
        
        trend = trends[trend_type]
        
        # 简单匹配
        matched = []
        
        if 'RSI' in indicators:
            rsi = indicators['RSI']
            if 'RSI' in str(trend.get('indicators', [])):
                if rsi < 30:
                    matched.append('RSI超卖')
                elif rsi > 70:
                    matched.append('RSI超买')
        
        if 'MACD' in indicators:
            macd = indicators.get('MACD', 0)
            if 'MACD' in str(trend.get('indicators', [])):
                if macd > 0:
                    matched.append('MACD金叉')
                else:
                    matched.append('MACD死叉')
        
        if 'Volume' in indicators:
            vol = indicators.get('Volume', 0)
            vol_ma = indicators.get('Volume_MA', 1)
            if vol > vol_ma * 2:
                matched.append('成交量激增')
        
        return matched
    
    def get_signal(self, market_type, indicators):
        """获取交易信号"""
        trends = self.get_trends(market_type)
        
        signals = []
        
        for trend_name, trend_info in trends.items():
            matched = self.match_indicators(indicators, trend_name, market_type)
            
            if matched:
                signals.append({
                    'type': trend_name,
                    'name': trend_info.get('name', trend_name),
                    'matched_indicators': matched,
                    'timeframes': trend_info.get('timeframes', {}),
                    'reliability': trend_info.get('reliability', '中')
                })
        
        return signals
    
    def get_best_timeframe(self, trend_type, market_type='crypto'):
        """获取最佳时间框架"""
        trends = self.get_trends(market_type)
        
        if trend_type not in trends:
            return None
        
        trend = trends[trend_type]
        timeframes = trend.get('timeframes', {})
        
        # 返回最短时间框架
        if timeframes:
            tf = list(timeframes.keys())[0]
            return {
                'timeframe': tf,
                'duration': timeframes[tf].get('duration', ''),
                'profit_target': timeframes[tf].get('profit_target', '')
            }
        
        return None
    
    def analyze(self, market_type, indicators):
        """综合分析"""
        print("="*60)
        print(f"📊 趋势分析 - {market_type.upper()}")
        print("="*60)
        
        print(f"\n📈 当前指标:")
        for k, v in indicators.items():
            print(f"   {k}: {v}")
        
        signals = self.get_signal(market_type, indicators)
        
        if signals:
            print(f"\n🎯 匹配到 {len(signals)} 个趋势:")
            
            for s in signals:
                print(f"\n   📌 {s['name']} ({s['type']})")
                print(f"      匹配指标: {', '.join(s['matched_indicators'])}")
                print(f"      可靠性: {s['reliability']}")
                
                if s['timeframes']:
                    tf = s['timeframes']
                    for t, info in tf.items():
                        print(f"      {t}: {info.get('profit_target', '')}")
        
        return signals

def main():
    db = TrendDatabase()
    
    # 测试
    indicators = {
        'RSI': 25,
        'MACD': 50,
        'MACross': 'Golden',
        'Volume': 5000000,
        'Volume_MA': 2000000,
        'Price_Change': 5.5
    }
    
    db.analyze('crypto', indicators)

if __name__ == "__main__":
    main()
