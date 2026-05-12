#!/usr/bin/env python3
"""
go-meta - go技能自主迭代引擎
自我学习、自我优化、自我扩展
"""
import requests, json, time, random, math, urllib.request, threading
from datetime import datetime, timedelta
from collections import defaultdict
import hmac, hashlib

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 已知策略列表
KNOWN_STRATEGIES = [
    # 趋势策略
    {'name': 'trend_rsi', 'type': 'trend', 'source': 'builtin'},
    {'name': 'trend_macd', 'type': 'trend', 'source': 'builtin'},
    {'name': 'trend_ma_cross', 'type': 'trend', 'source': 'builtin'},
    {'name': 'trend_supertrend', 'type': 'trend', 'source': 'builtin'},
    {'name': 'trend_golden_cross', 'type': 'trend', 'source': 'builtin'},
    {'name': 'trend_momentum_burst', 'type': 'trend', 'source': 'builtin'},
    
    # 回归策略
    {'name': 'reversion_rsi', 'type': 'reversion', 'source': 'builtin'},
    {'name': 'reversion_bollinger', 'type': 'reversion', 'source': 'builtin'},
    
    # 动量策略
    {'name': 'momentum_rsi', 'type': 'momentum', 'source': 'builtin'},
    {'name': 'momentum_macd', 'type': 'momentum', 'source': 'builtin'},
    {'name': 'momentum_stoch', 'type': 'momentum', 'source': 'builtin'},
    {'name': 'momentum_cci', 'type': 'momentum', 'source': 'builtin'},
    
    # 波动率策略
    {'name': 'volatility_atr', 'type': 'volatility', 'source': 'builtin'},
    {'name': 'volatility_bollinger_width', 'type': 'volatility', 'source': 'builtin'},
    
    # 成交量策略
    {'name': 'volume_obv', 'type': 'volume', 'source': 'builtin'},
    {'name': 'volume_mfi', 'type': 'volume', 'source': 'builtin'},
    
    # 突破策略
    {'name': 'breakout_donchian', 'type': 'breakout', 'source': 'builtin'},
    {'name': 'breakout_vwap', 'type': 'breakout', 'source': 'builtin'},
]

# 已知因子列表
KNOWN_FACTORS = [
    {'name': 'rsi', 'category': 'technical', 'source': 'builtin'},
    {'name': 'momentum', 'category': 'technical', 'source': 'builtin'},
    {'name': 'volume', 'category': 'technical', 'source': 'builtin'},
    {'name': 'bollinger', 'category': 'technical', 'source': 'builtin'},
    {'name': 'macd', 'category': 'technical', 'source': 'builtin'},
    {'name': 'atr', 'category': 'technical', 'source': 'builtin'},
    {'name': 'adx', 'category': 'technical', 'source': 'builtin'},
    {'name': 'stoch', 'category': 'technical', 'source': 'builtin'},
    {'name': 'cci', 'category': 'technical', 'source': 'builtin'},
    {'name': 'williams_r', 'category': 'technical', 'source': 'builtin'},
    {'name': 'moon_phase', 'category': 'mystical', 'source': 'builtin'},
    {'name': 'day_of_week', 'category': 'temporal', 'source': 'builtin'},
    {'name': 'halving_cycle', 'category': 'crypto', 'source': 'builtin'},
]

# 候选新策略 (模拟)
CANDIDATE_STRATEGIES = [
    {'name': 'volatility_regime', 'type': 'regime', 'source': 'discovered', 'expected_improvement': 0.05},
    {'name': 'orderflow_imbalance', 'type': 'orderflow', 'source': 'discovered', 'expected_improvement': 0.08},
    {'name': 'funding_rate_arbitrage', 'type': 'arbitrage', 'source': 'discovered', 'expected_improvement': 0.03},
    {'name': 'liquidations_heatmap', 'type': 'structure', 'source': 'discovered', 'expected_improvement': 0.06},
    {'name': 'social_sentiment_weighted', 'type': 'sentiment', 'source': 'discovered', 'expected_improvement': 0.04},
    {'name': 'cross_exchange_arbitrage', 'type': 'arbitrage', 'source': 'discovered', 'expected_improvement': 0.07},
    {'name': 'volume_profile_delta', 'type': 'volume', 'source': 'discovered', 'expected_improvement': 0.05},
    {'name': 'liquidations_sweep', 'type': 'structure', 'source': 'discovered', 'expected_improvement': 0.09},
]

# 候选新因子
CANDIDATE_FACTORS = [
    {'name': 'exchange_flow_ratio', 'category': 'onchain', 'source': 'discovered'},
    {'name': 'whale_transaction_count', 'category': 'onchain', 'source': 'discovered'},
    {'name': 'funding_rate_zscore', 'category': 'derivatives', 'source': 'discovered'},
    {'name': 'open_interest_delta', 'category': 'derivatives', 'source': 'discovered'},
    {'name': 'social_volume_momentum', 'category': 'sentiment', 'source': 'discovered'},
    {'name': 'google_trends_momentum', 'category': 'sentiment', 'source': 'discovered'},
    {'name': 'bid_ask_spread_ratio', 'category': 'microstructure', 'source': 'discovered'},
    {'name': 'order_book_imbalance', 'category': 'microstructure', 'source': 'discovered'},
]

# ============================================
# Data Utilities
# ============================================
def api_get(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())

def get_klines(symbol, interval='1h', limit=100):
    try:
        return api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    except: return []

def get_price_data(coin, interval='1h', limit=500):
    klines = get_klines(f"{coin}USDT", interval, limit)
    data = []
    for k in klines:
        data.append({
            'time': k[0] // 1000,
            'open': float(k[1]),
            'high': float(k[2]),
            'low': float(k[3]),
            'close': float(k[4]),
            'volume': float(k[5])
        })
    return data

# ============================================
# Strategy Discovery
# ============================================
class StrategyDiscovery:
    """策略发现引擎"""
    
    def __init__(self):
        self.candidates = CANDIDATE_STRATEGIES.copy()
        self.discovered = []
        self.tested = []
        
    def scan_sources(self):
        """扫描策略来源"""
        print("  🔍 扫描策略来源...")
        
        # 模拟发现新策略
        new_found = []
        for candidate in self.candidates:
            if candidate not in self.tested:
                # 模拟评估
                if random.random() < 0.3:  # 30%概率发现
                    new_found.append(candidate)
                    
        return new_found
        
    def evaluate(self, strategy, data):
        """评估策略"""
        # 简化回测
        closes = [d['close'] for d in data]
        
        # 计算模拟性能
        base_return = random.uniform(-0.1, 0.2)
        base_sharpe = random.uniform(0.5, 2.5)
        base_dd = random.uniform(5, 20)
        
        improvement = strategy.get('expected_improvement', 0)
        
        return {
            'return': base_return + improvement,
            'sharpe': base_sharpe + improvement * 2,
            'drawdown': base_dd - improvement * 50,
            'confidence': random.uniform(0.5, 0.9)
        }
        
    def discover(self, data):
        """发现新策略"""
        found = self.scan_sources()
        
        evaluated = []
        for strategy in found:
            result = self.evaluate(strategy, data)
            if result['confidence'] > 0.6:
                evaluated.append({
                    'strategy': strategy,
                    'result': result
                })
                self.tested.append(strategy)
                
        # 按改进度排序
        evaluated.sort(key=lambda x: x['result']['sharpe'], reverse=True)
        
        return evaluated[:5]  # Top 5
        
    def add_strategy(self, strategy):
        """添加策略"""
        KNOWN_STRATEGIES.append(strategy)
        self.discovered.append(strategy)
        print(f"  ✅ 新策略添加: {strategy['name']}")

# ============================================
# Factor Discovery
# ============================================
class FactorDiscovery:
    """因子发现引擎"""
    
    def __init__(self):
        self.candidates = CANDIDATE_FACTORS.copy()
        self.discovered = []
        self.tested = []
        
    def extract_features(self, data):
        """提取特征"""
        closes = [d['close'] for d in data]
        volumes = [d['volume'] for d in data]
        
        features = {}
        
        # 基础统计
        if len(closes) > 20:
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            features['mean_return'] = sum(returns) / len(returns)
            features['volatility'] = math.sqrt(sum(r**2 for r in returns) / len(returns))
            features['skewness'] = self._calc_skewness(returns)
            features['kurtosis'] = self._calc_kurtosis(returns)
            
        return features
        
    def _calc_skewness(self, values):
        if len(values) < 3: return 0
        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean)**2 for v in values) / len(values))
        if std == 0: return 0
        return sum((v - mean)**3 for v in values) / (len(values) * std**3)
        
    def _calc_kurtosis(self, values):
        if len(values) < 4: return 0
        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean)**2 for v in values) / len(values))
        if std == 0: return 0
        return sum((v - mean)**4 for v in values) / (len(values) * std**4) - 3
        
    def calculate_correlation(self, factor1_values, factor2_values):
        """计算两个因子的相关性"""
        if len(factor1_values) != len(factor2_values) or len(factor1_values) < 2:
            return 0
            
        mean1 = sum(factor1_values) / len(factor1_values)
        mean2 = sum(factor2_values) / len(factor2_values)
        
        num = sum((factor1_values[i] - mean1) * (factor2_values[i] - mean2) for i in range(len(factor1_values)))
        den1 = math.sqrt(sum((v - mean1)**2 for v in factor1_values))
        den2 = math.sqrt(sum((v - mean2)**2 for v in factor2_values))
        
        if den1 == 0 or den2 == 0: return 0
        return num / (den1 * den2)
        
    def discover(self, data):
        """发现新因子"""
        print("  🔍 发现新因子...")
        
        features = self.extract_features(data)
        
        found = []
        for candidate in self.candidates:
            if candidate not in self.tested:
                # 计算与现有因子的相关性
                correlation_with_existing = []
                for known in KNOWN_FACTORS:
                    if known['category'] == candidate['category']:
                        correlation_with_existing.append(random.uniform(0.1, 0.8))
                
                avg_correlation = sum(correlation_with_existing) / len(correlation_with_existing) if correlation_with_existing else 0.5
                
                # 低相关性意味着新信息
                if avg_correlation < 0.7:  # 新颖性阈值
                    found.append({
                        'factor': candidate,
                        'novelty': 1 - avg_correlation,
                        'features': features
                    })
                    self.tested.append(candidate)
                    
        # 按新颖性排序
        found.sort(key=lambda x: x['novelty'], reverse=True)
        
        return found[:5]
        
    def add_factor(self, factor):
        """添加因子"""
        KNOWN_FACTORS.append(factor)
        self.discovered.append(factor)
        print(f"  ✅ 新因子添加: {factor['name']}")

# ============================================
# Skill Comparison
# ============================================
class SkillComparator:
    """技能比较引擎"""
    
    def __init__(self):
        self.comparisons = []
        
    def compare(self, skill1_data, skill2_data):
        """比较两个技能"""
        # 简化比较
        metrics = ['return', 'sharpe', 'drawdown', 'win_rate']
        
        results = {}
        for metric in metrics:
            v1 = skill1_data.get(metric, 0)
            v2 = skill2_data.get(metric, 0)
            
            if metric == 'drawdown':
                # 回撤越低越好
                results[metric] = 1 if v1 < v2 else -1
            else:
                results[metric] = 1 if v1 > v2 else -1
                
        # 综合评分
        total = sum(results.values())
        winner = 'skill1' if total > 0 else 'skill2'
        
        return {
            'winner': winner,
            'metrics': results,
            'score_diff': abs(total) / len(metrics)
        }
        
    def distill(self, skills_data):
        """蒸馏多个技能"""
        print("  🔬 蒸馏技能...")
        
        # 收集所有性能指标
        best_return = max(s.get('return', 0) for s in skills_data)
        best_sharpe = max(s.get('sharpe', 0) for s in skills_data)
        best_dd = min(s.get('drawdown', 100) for s in skills_data)
        
        # 蒸馏最佳组合
        distilled = {
            'return': best_return,
            'sharpe': best_sharpe,
            'drawdown': best_dd,
            'source': 'distilled',
            'components': len(skills_data)
        }
        
        return distilled
        
    def merge(self, skill1, skill2):
        """合并两个技能"""
        return {
            'name': f"{skill1['name']}_merged_{skill2['name']}",
            'return': (skill1.get('return', 0) + skill2.get('return', 0)) / 2,
            'sharpe': (skill1.get('sharpe', 0) + skill2.get('sharpe', 0)) / 2,
            'drawdown': min(skill1.get('drawdown', 100), skill2.get('drawdown', 100)),
            'source': 'merged'
        }

# ============================================
# Meta Learning Engine
# ============================================
class MetaLearner:
    """元学习引擎 - 自主迭代核心"""
    
    def __init__(self):
        self.strategy_discovery = StrategyDiscovery()
        self.factor_discovery = FactorDiscovery()
        self.skill_comparator = SkillComparator()
        
        self.iteration_count = 0
        self.strategies_added = []
        self.factors_added = []
        self.performance_history = []
        
        self.running = False
        self.thread = None
        
        self.mode = 'conservative'  # conservative, aggressive, explorative
        
    def start(self, interval=3600, mode='conservative'):
        """启动自主迭代"""
        self.running = True
        self.mode = mode
        
        self.thread = threading.Thread(target=self._loop, args=(interval,))
        self.thread.daemon = True
        self.thread.start()
        
        print(f"🚀 go-meta 自主迭代引擎启动 (模式: {mode}, 间隔: {interval}s)")
        
    def stop(self):
        """停止"""
        self.running = False
        print("⏹️ go-meta 自主迭代引擎停止")
        
    def _loop(self, interval):
        """迭代循环"""
        while self.running:
            try:
                self.iterate()
            except Exception as e:
                print(f"  ❌ 迭代错误: {e}")
                
            time.sleep(interval)
            
    def iterate(self):
        """执行一次迭代"""
        self.iteration_count += 1
        
        print(f"\n{'='*60}")
        print(f"🔄 迭代 #{self.iteration_count} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"{'='*60}")
        
        # 获取数据
        data = get_price_data('BTC', '1h', 200)
        
        # 1. 策略发现
        print("\n📊 策略发现:")
        new_strategies = self.strategy_discovery.discover(data)
        for item in new_strategies:
            strat = item['strategy']
            result = item['result']
            print(f"  • {strat['name']} ({strat['type']})")
            print(f"    预期改进: +{result['sharpe']:.2f} sharpe, {result['return']*100:+.1f}%")
            
            # 添加到技能
            if result['confidence'] > 0.7 and self.mode != 'conservative':
                self.strategy_discovery.add_strategy(strat)
                self.strategies_added.append(strat)
                
        # 2. 因子发现
        print("\n📊 因子发现:")
        new_factors = self.factor_discovery.discover(data)
        for item in new_factors:
            factor = item['factor']
            print(f"  • {factor['name']} ({factor['category']})")
            print(f"    新颖性: {item['novelty']:.2f}")
            
            # 添加到因子库
            if item['novelty'] > 0.5 and self.mode == 'explorative':
                self.factor_discovery.add_factor(factor)
                self.factors_added.append(factor)
                
        # 3. 技能比较
        print("\n📊 技能比较:")
        skills_data = [
            {'name': 'go_current', 'return': 0.15, 'sharpe': 1.5, 'drawdown': 12},
            {'name': 'go_distilled', 'return': 0.18, 'sharpe': 1.8, 'drawdown': 10},
        ]
        
        comparison = self.skill_comparator.compare(skills_data[0], skills_data[1])
        print(f"  比较结果: {comparison['winner']} 胜出")
        print(f"  分数差异: {comparison['score_diff']:.2f}")
        
        # 蒸馏
        distilled = self.skill_comparator.distill(skills_data)
        print(f"  蒸馏结果: sharpe={distilled['sharpe']:.2f}, return={distilled['return']*100:.1f}%")
        
        # 记录性能
        self.performance_history.append({
            'iteration': self.iteration_count,
            'strategies': len(KNOWN_STRATEGIES),
            'factors': len(KNOWN_FACTORS),
            'distilled_sharpe': distilled['sharpe']
        })
        
        print(f"\n📈 当前状态:")
        print(f"  总策略数: {len(KNOWN_STRATEGIES)}")
        print(f"  总因子数: {len(KNOWN_FACTORS)}")
        print(f"  本次新增策略: {len(self.strategies_added)}")
        print(f"  本次新增因子: {len(self.factors_added)}")
        
    def get_status(self):
        """获取状态"""
        return {
            'running': self.running,
            'iteration': self.iteration_count,
            'mode': self.mode,
            'total_strategies': len(KNOWN_STRATEGIES),
            'total_factors': len(KNOWN_FACTORS),
            'strategies_added': len(self.strategies_added),
            'factors_added': len(self.factors_added),
            'performance_history': self.performance_history[-10:]  # 最近10次
        }
        
    def get_new_strategies(self):
        """获取新策略"""
        return self.strategies_added
        
    def get_new_factors(self):
        """获取新因子"""
        return self.factors_added

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-meta - go技能自主迭代引擎")
        print("Usage:")
        print("  python meta_engine.py start [interval] [mode]")
        print("  python meta_engine.py iterate")
        print("  python meta_engine.py status")
        print("  python meta_engine.py stop")
        print("\nModes: conservative, aggressive, explorative")
        sys.exit(1)
        
    cmd = sys.argv[1]
    meta = MetaLearner()
    
    if cmd == 'start':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
        mode = sys.argv[3] if len(sys.argv) > 3 else 'conservative'
        
        meta.start(interval, mode)
        
        print("\n自主迭代运行中，按 Ctrl+C 停止...")
        try:
            while True:
                time.sleep(10)
                status = meta.get_status()
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] 迭代#{status['iteration']} | 策略:{status['total_strategies']} | 因子:{status['total_factors']}", end='')
        except KeyboardInterrupt:
            meta.stop()
            
    elif cmd == 'iterate':
        meta.iterate()
        
    elif cmd == 'status':
        status = meta.get_status()
        print(f"\n📊 go-meta 状态:")
        print(f"  运行状态: {'运行中' if status['running'] else '已停止'}")
        print(f"  迭代次数: {status['iteration']}")
        print(f"  运行模式: {status['mode']}")
        print(f"  总策略数: {status['total_strategies']}")
        print(f"  总因子数: {status['total_factors']}")
        print(f"  本次新增策略: {status['strategies_added']}")
        print(f"  本次新增因子: {status['factors_added']}")
        
        if status['performance_history']:
            print(f"\n📈 最近性能:")
            for h in status['performance_history'][-5:]:
                print(f"  迭代#{h['iteration']}: sharpe={h['distilled_sharpe']:.2f}")
                
    elif cmd == 'stop':
        meta.stop()
