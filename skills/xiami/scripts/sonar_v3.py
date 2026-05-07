#!/usr/bin/env python3
"""
🦐 XIAMI 声纳系统 v3 - 观测与执行分离
- 500ms 观测点
- 执行需对照趋势模型
- 多市场支持
"""

import json
import ccxt
import time
from datetime import datetime

class XiamiSonarV3:
    """声纳系统 v3"""
    
    def __init__(self):
        with open('skills/xiami/data/trend_database.json', 'r') as f:
            self.db = json.load(f)
        
        self.observe_matrix = self.db.get('observe_matrix', {})
        self.execution_rules = self.db.get('execution_rules', {})
        
        # 观测缓存
        self.observe_cache = {}
        
    def get_trends(self, market):
        return self.db.get(f'{market}_trends', {})
    
    def should_execute(self, trend_info, confidence_score):
        """判断是否执行"""
        # 获取时间框架配置
        tfs = trend_info.get('timeframes', {})
        if not tfs:
            return False, "无时间框架"
        
        # 获取最佳时间框架
        best_tf = list(tfs.keys())[0]
        tf_config = tfs[best_tf]
        
        # 检查是否仅观测
        if tf_config.get('execute', False) == False:
            return False, f"{best_tf} 仅观测不执行"
        
        # 检查最小置信度
        min_conf = tf_config.get('min_confidence', 
                                 self.execution_rules.get('min_confidence_to_execute', 4))
        
        if confidence_score < min_conf:
            return False, f"置信度{confidence_score}<{min_conf}"
        
        # 检查风险
        risk = tf_config.get('risk', '中')
        max_positions = self.execution_rules.get('max_position_size_by_risk', {}).get(risk, 0.1)
        
        return True, f"可执行 | 置信度:{confidence_score} | 风险:{risk} | 仓位:{max_positions}"
    
    def match_indicators(self, indicators, trend_info):
        """匹配指标"""
        score = 0
        matched = []
        
        # RSI
        if 'RSI' in indicators and 'RSI' in str(trend_info.get('indicators', [])):
            rsi = indicators['RSI']
            if rsi < 30:
                score += 3
                matched.append('RSI超卖')
            elif rsi > 70:
                score += 3
                matched.append('RSI超买')
        
        # MACD
        if 'MACD' in indicators:
            macd = indicators['MACD']
            if 'MACD' in str(trend_info.get('indicators', [])):
                if macd > 0:
                    score += 2
                    matched.append('MACD金叉')
        
        # Volume
        if 'Volume_Ratio' in indicators and 'Volume' in str(trend_info.get('indicators', [])):
            vr = indicators['Volume_Ratio']
            if vr > 2:
                score += 3
                matched.append('成交量放大')
        
        return score, matched
    
    def observe_cycle(self, market='crypto'):
        """观测周期 - 500ms"""
        trends = self.get_trends(market)
        
        try:
            e = ccxt.binance()
            e.load_markets()
            
            symbols = {
                'crypto': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT'],
                'stock': [],
                'forex': [],
                'futures': [],
                'commodity': []
            }.get(market, ['BTC/USDT'])
            
            observations = []
            
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
                    
                    # 匹配趋势
                    for trend_name, trend_info in trends.items():
                        conf, matched = self.match_indicators(indicators, trend_info)
                        
                        if conf > 0:
                            # 检查是否执行
                            can_exec, reason = self.should_execute(trend_info, conf)
                            
                            observations.append({
                                'symbol': symbol,
                                'trend': trend_name,
                                'name': trend_info.get('name', trend_name),
                                'confidence': conf,
                                'matched': matched,
                                'change': change,
                                'can_execute': can_exec,
                                'execute_reason': reason
                            })
                            
                except:
                    continue
            
            return sorted(observations, key=lambda x: x['confidence'], reverse=True)
            
        except Exception as e:
            print(f"❌ 观测错误: {e}")
            return []
    
    def run(self):
        """运行声纳"""
        print("="*60)
        print("🔊 XIAMI 声纳系统 v3")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 500ms 观测周期
        print("\n📡 500ms 观测点...")
        
        observations = self.observe_cycle('crypto')
        
        if not observations:
            print("⚪ 无观测信号")
            return
        
        # 分类显示
        print(f"\n📊 共 {len(observations)} 个观测信号:")
        
        execute_signals = [o for o in observations if o['can_execute']]
        observe_only = [o for o in observations if not o['can_execute']]
        
        # 可执行信号
        if execute_signals:
            print(f"\n✅ 可执行信号 ({len(execute_signals)}个):")
            for o in execute_signals[:3]:
                emoji = "📈" if o['change'] > 0 else "📉"
                print(f"   {emoji} {o['symbol']} | {o['name']}")
                print(f"      置信度: {o['confidence']} | 涨跌: {o['change']:+.1f}%")
                print(f"      原因: {', '.join(o['matched'])}")
                print(f"      → {o['execute_reason']}")
        
        # 仅观测
        if observe_only:
            print(f"\n🔭 仅观测 ({len(observe_only)}个):")
            for o in observe_only[:3]:
                print(f"   ⚪ {o['symbol']} | {o['name']} | {o['execute_reason']}")
        
        return observations

if __name__ == "__main__":
    sonar = XiamiSonarV3()
    sonar.run()
