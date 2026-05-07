#!/usr/bin/python3
"""
🦐 XIAMI 声纳趋势匹配系统
- 如同潜艇声纳快速匹配
- 根据趋势模型动态调整执行频率
- 自动选择最佳时间框架
"""

import json
import ccxt
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class XiamiSonar:
    """声纳趋势匹配系统"""
    
    def __init__(self):
        # 加载趋势数据库
        with open('skills/xiami/data/trend_database.json', 'r') as f:
            self.trend_db = json.load(f)
        
        # 动态执行参数
        self.execution_params = {
            'quant': {
                'interval_ms': 500,
                'duration_sec': 60,
                'min_change': 2.0,
                'max_positions': 3,
            },
            'mole': {
                'interval_sec': 900,
                'min_change': 5.0,
            },
            'mainstream': {
                'interval_sec': 1800,
            }
        }
        
        # API速度缓存
        self.api_speed = {}
        
    def load_trend_models(self, market='crypto'):
        """加载趋势模型"""
        return self.trend_db.get(f'{market}_trends', {})
    
    def match_trend(self, indicators):
        """匹配趋势模型 - 声纳扫描"""
        matched = []
        trends = self.load_trend_models()
        
        for trend_name, trend_info in trends.items():
            score = 0
            matched_indicators = []
            
            # RSI匹配
            if 'RSI' in indicators and 'RSI' in str(trend_info.get('indicators', [])):
                rsi = indicators['RSI']
                if rsi < 30:
                    score += 3
                    matched_indicators.append('RSI超卖')
                elif rsi > 70:
                    score += 3
                    matched_indicators.append('RSI超买')
                elif 40 < rsi < 60:
                    score += 1
            
            # MACD匹配
            if 'MACD' in indicators and 'MACD' in str(trend_info.get('indicators', [])):
                macd = indicators.get('MACD', 0)
                if macd > 0:
                    score += 2
                    matched_indicators.append('MACD金叉')
                else:
                    score += 2
                    matched_indicators.append('MACD死叉')
            
            # 成交量匹配
            if 'Volume_Ratio' in indicators and 'Volume' in str(trend_info.get('indicators', [])):
                vol_ratio = indicators['Volume_Ratio']
                if vol_ratio > 2:
                    score += 3
                    matched_indicators.append('成交量激增')
            
            if score > 0:
                matched.append({
                    'trend': trend_name,
                    'name': trend_info.get('name', trend_name),
                    'score': score,
                    'indicators': matched_indicators,
                    'timeframes': trend_info.get('timeframes', {}),
                    'reliability': trend_info.get('reliability', '中')
                })
        
        # 按分数排序
        matched.sort(key=lambda x: x['score'], reverse=True)
        return matched
    
    def get_execution_params(self, matched_trend):
        """根据匹配到的趋势获取执行参数 - 声纳响应"""
        if not matched_trend:
            # 无匹配，使用默认
            return self.execution_params
        
        trend = matched_trend[0]
        timeframes = trend.get('timeframes', {})
        
        # 获取最短时间框架
        if timeframes:
            # 按时间长度排序
            tf_map = {
                '1m': 1,
                '5m': 5,
                '15m': 15,
                '30m': 30,
                '1h': 60,
                '4h': 240,
                '1d': 1440,
                '1w': 10080
            }
            
            sorted_tf = sorted(timeframes.items(), 
                            key=lambda x: tf_map.get(x[0], 999))
            
            best_tf = sorted_tf[0]
            tf_name = best_tf[0]
            tf_info = best_tf[1]
            
            # 根据时间框架调整执行频率
            duration_min = tf_info.get('duration', '30分钟')
            
            # 解析duration
            if '分钟' in duration_min:
                mins = int(duration_min.replace('分钟', '').replace('-', '').split('-')[0])
            elif '小时' in duration_min:
                mins = int(duration_min.replace('小时', '').replace('-', '').split('-')[0]) * 60
            elif '天' in duration_min:
                mins = int(duration_min.replace('天', '').replace('-', '').split('-')[0]) * 1440
            else:
                mins = 30
            
            # 动态调整参数
            if mins <= 5:
                # 超短期 - 高频
                params = {
                    'interval_ms': 200,
                    'duration_sec': 30,
                    'min_change': 1.0,
                    'max_positions': 5,
                }
            elif mins <= 30:
                # 短期 - 中频
                params = {
                    'interval_ms': 500,
                    'duration_sec': 60,
                    'min_change': 2.0,
                    'max_positions': 3,
                }
            elif mins <= 240:
                # 中期 - 低频
                params = {
                    'interval_ms': 1000,
                    'duration_sec': 120,
                    'min_change': 3.0,
                    'max_positions': 2,
                }
            else:
                # 长期 - 常规
                params = self.execution_params['quant']
            
            return params
        
        return self.execution_params['quant']
    
    def sonar_scan(self):
        """声纳扫描 - 快速匹配"""
        print("="*60)
        print("🔊 XIAMI 声纳扫描")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 1. 获取市场数据
        try:
            e = ccxt.binance()
            e.load_markets()
            
            # 采样关键币种
            symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
            tickers = e.fetch_tickers(symbols)
            
            # 计算指标
            indicators = {}
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage', 0)
                volume = ticker.get('quoteVolume', 0)
                
                indicators[symbol] = {
                    'change': change,
                    'volume': volume,
                    'RSI': 50 + (change * 2),  # 简化模拟
                    'MACD': change * 10,
                    'Volume_Ratio': volume / 1000000,
                }
                
                # 匹配趋势
                matched = self.match_trend(indicators[symbol])
                
                if matched:
                    print(f"\n📡 {symbol}:")
                    print(f"   涨跌: {change:+.1f}%")
                    
                    for m in matched[:2]:
                        print(f"   🎯 {m['name']} (匹配度: {m['score']})")
                        
                        # 获取执行参数
                        params = self.get_execution_params([m])
                        
                        print(f"   ⚡ 执行: 每{params['interval_ms']}ms, 持续{params['duration_sec']}s")
                        print(f"   📊 目标: {m['timeframes']}")
        
        except Exception as e:
            print(f"❌ 扫描错误: {e}")

def main():
    sonar = XiamiSonar()
    sonar.sonar_scan()

if __name__ == "__main__":
    main()
