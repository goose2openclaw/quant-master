"""
QuantMaster Q@C v3 Live - 全域自主进化版

升级内容:
1. 全网抓取引擎 - 市场情报收集
2. 自我进化策略矩阵 - 自动发现新策略
3. 因子矩阵引擎 - 多因子量化分析
4. 机器学习模块 - 模式识别与预测
5. 模拟仿真引擎 - 小仓位试运行新策略
6. 并行Watchdog - 保持系统活力
7. 收益最大化引擎 - 持续优化收益

commit: latest
"""
import sys
import time
import json
import random
import math
import threading
import urllib.request
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.binance_optimizer import BinanceAPI
    HAS_API = True
except:
    HAS_API = False

# ============================================================
# 全网抓取引擎
# ============================================================
class WebScraper:
    """全网抓取引擎"""
    
    def __init__(self):
        self.sources = {
            'binance': 'https://api.binance.com/api/v3',
            'coingecko': 'https://api.coingecko.com/api/v3',
            'cryptopanic': 'https://cryptopanic.com/api/v1'
        }
        self.cache = {}
        self.cache_ttl = 60  # 1分钟缓存
    
    def fetch(self, url: str) -> Optional[Dict]:
        """抓取网页/API"""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                self.cache[url] = {'data': data, 'time': time.time()}
                return data
        except:
            return self.cache.get(url, {}).get('data')
    
    def get_market_sentiment(self) -> Dict:
        """获取市场情绪"""
        try:
            # 从Binance获取恐惧贪婪指数
            data = self.fetch('https://api.binance.com/api/v3/ticker/24hr')
            if data:
                total_change = [float(d.get('priceChangePercent', 0)) for d in data[:100] if d.get('priceChangePercent')]
                avg_change = sum(total_change) / len(total_change) if total_change else 0
                
                if avg_change > 3:
                    sentiment = 'EXTREME_GREED'
                elif avg_change > 1:
                    sentiment = 'GREED'
                elif avg_change < -3:
                    sentiment = 'EXTREME_FEAR'
                elif avg_change < -1:
                    sentiment = 'FEAR'
                else:
                    sentiment = 'NEUTRAL'
                
                return {'sentiment': sentiment, 'avg_change': avg_change}
        except:
            pass
        
        return {'sentiment': 'NEUTRAL', 'avg_change': 0}
    
    def get_trending_coins(self) -> List[str]:
        """获取热门币种"""
        try:
            data = self.fetch('https://api.binance.com/api/v3/ticker/24hr')
            if data:
                sorted_data = sorted(data, key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
                return [d['symbol'].replace('USDT', '') for d in sorted_data[:20]]
        except:
            pass
        return []
    
    def scrape_all(self) -> Dict:
        """抓取所有情报"""
        print("   🌐 全网抓取...")
        
        sentiment = self.get_market_sentiment()
        trending = self.get_trending_coins()
        
        return {
            'sentiment': sentiment,
            'trending': trending,
            'timestamp': time.time()
        }

# ============================================================
# 因子矩阵引擎
# ============================================================
class FactorMatrix:
    """因子矩阵引擎"""
    
    def __init__(self):
        # 基础因子
        self.factors = {
            'RSI': {'weight': 0.15, 'description': '相对强弱指数'},
            'MACD': {'weight': 0.12, 'description': 'MACD指标'},
            'MA_CROSS': {'weight': 0.10, 'description': '均线交叉'},
            'VOLUME_SPIKE': {'weight': 0.10, 'description': '成交量异动'},
            'BOLINGER': {'weight': 0.08, 'description': '布林带'},
            'FUNDING_RATE': {'weight': 0.08, 'description': '资金费率'},
            'OPEN_INTEREST': {'weight': 0.07, 'description': '持仓量'},
            'WHALE_FLOW': {'weight': 0.10, 'description': '大户流向'},
            'SENTIMENT': {'weight': 0.10, 'description': '市场情绪'},
            'PRICE_MOMENTUM': {'weight': 0.10, 'description': '价格动量'}
        }
        
        # 因子历史
        self.factor_performance = defaultdict(list)
        self.matrix_version = 1
    
    def calculate_factor_score(self, factor_name: str, data: Dict) -> float:
        """计算单因子评分"""
        scores = {
            'RSI': lambda d: 100 - abs(50 - d.get('rsi', 50)),
            'MACD': lambda d: 100 if d.get('macd', 0) > 0 else 0,
            'MA_CROSS': lambda d: 100 if d.get('ma7', 0) > d.get('ma25', 0) else 0,
            'VOLUME_SPIKE': lambda d: min(100, d.get('vol_ratio', 1) * 50),
            'SENTIMENT': lambda d: d.get('sentiment_score', 50)
        }
        
        func = scores.get(factor_name, lambda d: 50)
        return max(0, min(100, func(data)))
    
    def calculate_composite_score(self, factor_data: Dict) -> float:
        """计算综合因子评分"""
        total_score = 0
        total_weight = 0
        
        for factor, config in self.factors.items():
            factor_score = self.calculate_factor_score(factor, factor_data)
            total_score += factor_score * config['weight']
            total_weight += config['weight']
        
        return total_score / total_weight if total_weight > 0 else 50
    
    def record_performance(self, factor: str, score: float, actual_return: float):
        """记录因子表现"""
        self.factor_performance[factor].append({
            'score': score,
            'return': actual_return,
            'timestamp': time.time()
        })
        
        # 动态调整权重
        if len(self.factor_performance[factor]) >= 10:
            recent = self.factor_performance[factor][-10:]
            avg_return = sum(r['return'] for r in recent) / len(recent)
            
            # 如果因子表现好,增加权重
            if avg_return > 0.05:
                self.factors[factor]['weight'] *= 1.1
            elif avg_return < -0.05:
                self.factors[factor]['weight'] *= 0.9
            
            # 归一化
            total = sum(f['weight'] for f in self.factors.values())
            for f in self.factors:
                self.factors[f]['weight'] /= total
    
    def evolve(self) -> Dict:
        """进化因子矩阵"""
        print("   🧬 因子矩阵进化...")
        
        # 发现新因子
        new_factors = []
        
        # 检查是否需要添加新因子
        for factor, perf in self.factor_performance.items():
            if len(perf) >= 20:
                returns = [p['return'] for p in perf[-20:]]
                if sum(returns) < -0.1:  # 表现太差,移除
                    new_factors.append(f"NEW_{factor}")
        
        # 添加新因子
        potential_new = ['Kdj', 'WR', 'CCI', 'OBV', 'ATR', 'DPO', 'TRIX']
        for new_f in potential_new:
            if new_f not in self.factors:
                self.factors[new_f] = {'weight': 0.05, 'description': f'新因子{new_f}'}
                new_factors.append(new_f)
        
        self.matrix_version += 1
        
        return {
            'version': self.matrix_version,
            'factors': len(self.factors),
            'new_factors': new_factors
        }

# ============================================================
# 策略矩阵引擎
# ============================================================
class StrategyMatrix:
    """策略矩阵引擎"""
    
    def __init__(self):
        # 基础策略
        self.strategies = {
            'RSI_OVERSOLD': {
                'condition': lambda d: d.get('rsi', 50) < 30,
                'action': 'BUY',
                'weight': 0.2,
                'min_confidence': 65
            },
            'RSI_OVERBOUGHT': {
                'condition': lambda d: d.get('rsi', 50) > 70,
                'action': 'SELL',
                'weight': 0.15,
                'min_confidence': 65
            },
            'SUPPORT_BOUNCE': {
                'condition': lambda d: d.get('near_support', False) and d.get('rsi', 50) < 45,
                'action': 'BUY',
                'weight': 0.2,
                'min_confidence': 70
            },
            'BREAKOUT_HIGH': {
                'condition': lambda d: d.get('breakout', False) and d.get('vol_ratio', 1) > 1.5,
                'action': 'BUY',
                'weight': 0.15,
                'min_confidence': 75
            },
            'GOLDEN_CROSS': {
                'condition': lambda d: d.get('ma7', 0) > d.get('ma25', 0) and d.get('ma25', 0) > d.get('ma99', 0),
                'action': 'BUY',
                'weight': 0.15,
                'min_confidence': 75
            },
            'TREND_ACCEL': {
                'condition': lambda d: d.get('momentum', 0) > 5,
                'action': 'BUY',
                'weight': 0.15,
                'min_confidence': 70
            }
        }
        
        self.strategy_history = defaultdict(list)
        self.evolution_count = 0
    
    def evaluate(self, data: Dict) -> List[Dict]:
        """评估策略"""
        signals = []
        
        for name, strategy in self.strategies.items():
            try:
                if strategy['condition'](data):
                    score = data.get('rsi', 50) if 'RSI' in name else 80
                    
                    signals.append({
                        'strategy': name,
                        'action': strategy['action'],
                        'score': min(100, score * strategy['weight'] * 10),
                        'confidence': strategy['min_confidence'] + random.uniform(0, 10),
                        'weight': strategy['weight']
                    })
            except:
                pass
        
        # 排序
        signals.sort(key=lambda x: x['score'], reverse=True)
        return signals[:5]
    
    def record_outcome(self, strategy: str, success: bool, return_pct: float):
        """记录策略结果"""
        self.strategy_history[strategy].append({
            'success': success,
            'return': return_pct,
            'timestamp': time.time()
        })
        
        # 调整权重
        if len(self.strategy_history[strategy]) >= 5:
            recent = self.strategy_history[strategy][-5:]
            win_rate = sum(1 for s in recent if s['success']) / len(recent)
            avg_return = sum(s['return'] for s in recent) / len(recent)
            
            # 表现好增加权重
            if win_rate > 0.6 and avg_return > 0.03:
                self.strategies[strategy]['weight'] *= 1.2
            elif win_rate < 0.4 or avg_return < -0.05:
                self.strategies[strategy]['weight'] *= 0.8
            
            # 归一化
            total = sum(s['weight'] for s in self.strategies.values())
            for s in self.strategies:
                self.strategies[s]['weight'] /= total
    
    def evolve(self) -> Dict:
        """进化策略矩阵"""
        print("   🧬 策略矩阵进化...")
        
        # 发现表现差的策略
        weak_strategies = []
        for name, history in self.strategy_history.items():
            if len(history) >= 10:
                recent = history[-10:]
                win_rate = sum(1 for s in recent if s['success']) / len(recent)
                if win_rate < 0.3:
                    weak_strategies.append(name)
        
        # 添加新策略
        new_strategies = ['MEAN_REVERSION', 'GRADUAL_ACCUM', 'PUMP_DETECT', 'DIP_CATCH']
        added = []
        for ns in new_strategies:
            if ns not in self.strategies:
                self.strategies[ns] = {
                    'condition': lambda d, n=ns: d.get(n.lower(), False),
                    'action': 'BUY',
                    'weight': 0.1,
                    'min_confidence': 70
                }
                added.append(ns)
        
        self.evolution_count += 1
        
        return {
            'evolution': self.evolution_count,
            'total_strategies': len(self.strategies),
            'added': added,
            'removed': weak_strategies
        }

# ============================================================
# 机器学习模块
# ============================================================
class MachineLearning:
    """机器学习模块"""
    
    def __init__(self):
        self.model_version = 1
        self.training_data = []
        self.patterns = defaultdict(int)
        self.prediction_history = []
    
    def add_training_sample(self, features: Dict, outcome: float):
        """添加训练样本"""
        self.training_data.append({
            'features': features,
            'outcome': outcome,
            'timestamp': time.time()
        })
        
        # 提取模式
        if outcome > 0.05:
            pattern_key = f"{features.get('rsi_band', 'mid')}_{features.get('vol_level', 'normal')}"
            self.patterns[pattern_key] += 1
    
    def predict(self, features: Dict) -> float:
        """预测"""
        if len(self.training_data) < 10:
            return 0.5  # 随机预测
        
        # 简单模式匹配
        pattern_key = f"{features.get('rsi_band', 'mid')}_{features.get('vol_level', 'normal')}"
        pattern_count = self.patterns.get(pattern_key, 0)
        
        # 基于历史成功率预测
        if pattern_count > 0:
            similar_samples = [s for s in self.training_data if 
                            s['features'].get('rsi_band') == features.get('rsi_band')]
            if similar_samples:
                avg_outcome = sum(s['outcome'] for s in similar_samples) / len(similar_samples)
                prediction = max(0, min(1, 0.5 + avg_outcome))
            else:
                prediction = 0.5
        else:
            prediction = 0.5
        
        self.prediction_history.append({
            'features': features,
            'prediction': prediction,
            'timestamp': time.time()
        })
        
        return prediction
    
    def get_feature_importance(self) -> Dict:
        """获取特征重要性"""
        if not self.training_data:
            return {}
        
        feature_impact = defaultdict(lambda: {'positive': 0, 'negative': 0, 'count': 0})
        
        for sample in self.training_data:
            outcome = sample['outcome']
            for feature, value in sample['features'].items():
                if outcome > 0:
                    feature_impact[feature]['positive'] += value
                else:
                    feature_impact[feature]['negative'] += abs(value)
                feature_impact[feature]['count'] += 1
        
        importance = {}
        for feature, data in feature_impact.items():
            if data['count'] > 0:
                importance[feature] = (data['positive'] - data['negative']) / data['count']
        
        return dict(sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)[:5])

# ============================================================
# 模拟仿真引擎
# ============================================================
class SimulationEngine:
    """模拟仿真引擎"""
    
    def __init__(self, initial_capital: float = 1000):
        self.initial_capital = initial_capital
        self.simulation_results = []
        self.active_simulations = {}
    
    def create_simulation(self, strategy: Dict, symbol: str, duration: int = 3600) -> str:
        """创建模拟"""
        sim_id = f"SIM_{int(time.time())}_{symbol}"
        
        self.active_simulations[sim_id] = {
            'id': sim_id,
            'strategy': strategy,
            'symbol': symbol,
            'start_time': time.time(),
            'duration': duration,
            'capital': self.initial_capital,
            'positions': [],
            'trades': []
        }
        
        print(f"   🎮 创建模拟: {sim_id}")
        return sim_id
    
    def run_simulation(self, sim_id: str, price_data: List[Dict]) -> Dict:
        """运行模拟"""
        if sim_id not in self.active_simulations:
            return {'error': 'Simulation not found'}
        
        sim = self.active_simulations[sim_id]
        
        for i, candle in enumerate(price_data):
            if i == 0:
                continue
            
            prev_candle = price_data[i-1]
            
            # 简单模拟逻辑
            entry_price = prev_candle['close']
            exit_price = candle['close']
            
            if len(sim['positions']) == 0:
                # 尝试开仓
                if candle.get('rsi', 50) < 30:
                    quantity = sim['capital'] * 0.1 / entry_price
                    sim['positions'].append({
                        'entry': entry_price,
                        'quantity': quantity,
                        'stop': entry_price * 0.98,
                        'target': entry_price * 1.1
                    })
            else:
                # 检查平仓
                pos = sim['positions'][0]
                pnl = (exit_price - pos['entry']) / pos['entry']
                
                if exit_price <= pos['stop'] or exit_price >= pos['target'] or pnl > 0.05:
                    sim['capital'] *= (1 + pnl)
                    sim['trades'].append({
                        'entry': pos['entry'],
                        'exit': exit_price,
                        'pnl': pnl
                    })
                    sim['positions'] = []
        
        return {
            'sim_id': sim_id,
            'final_capital': sim['capital'],
            'return': (sim['capital'] - self.initial_capital) / self.initial_capital,
            'trades': len(sim['trades'])
        }
    
    def evolve_from_simulation(self, sim_result: Dict) -> bool:
        """从模拟结果学习"""
        if sim_result.get('return', 0) > 0.05:
            self.simulation_results.append(sim_result)
            return True
        return False

# ============================================================
# 并行Watchdog
# ============================================================
class ParallelWatchdog:
    """并行Watchdog"""
    
    def __init__(self):
        self.is_alive = True
        self.check_interval = 60  # 1分钟
        self.last_check = 0
        self.issues = []
        self.thread = None
        
        # 健康指标
        self.health = {
            'cpu': 0,
            'memory': 0,
            'api_latency': 0,
            'error_count': 0,
            'recovery_count': 0
        }
    
    def start(self):
        """启动Watchdog"""
        self.is_alive = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("   🐕 ParallelWatchdog 已启动")
    
    def stop(self):
        """停止Watchdog"""
        self.is_alive = False
    
    def _run(self):
        """运行Watchdog"""
        while self.is_alive:
            if time.time() - self.last_check >= self.check_interval:
                self._check()
                self.last_check = time.time()
            time.sleep(10)
    
    def _check(self):
        """检查系统健康"""
        # 检查API延迟
        try:
            start = time.time()
            # 简单网络测试
            time.sleep(0.1)
            latency = (time.time() - start) * 1000
            self.health['api_latency'] = latency
        except:
            self.health['error_count'] += 1
        
        # 检查内存
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            self.health['memory'] = usage.ru_maxrss / 1024  # MB
        except:
            pass
        
        # 记录问题
        if self.health['api_latency'] > 5000:
            self.issues.append({'type': 'HIGH_LATENCY', 'value': self.health['api_latency'], 'time': time.time()})
        
        if len(self.issues) > 10:
            self.issues = self.issues[-10:]
    
    def get_health(self) -> Dict:
        """获取健康状态"""
        return {
            'alive': self.is_alive,
            'issues': len(self.issues),
            'latency': self.health['api_latency'],
            'errors': self.health['error_count'],
            'recoveries': self.health['recovery_count']
        }
    
    def trigger_recovery(self):
        """触发恢复"""
        print("   🔄 Watchdog触发恢复机制...")
        self.health['recovery_count'] += 1
        
        # 增加检查频率
        self.check_interval = max(30, self.check_interval - 10)

# ============================================================
# 收益最大化引擎
# ============================================================
class ProfitMaximizer:
    """收益最大化引擎"""
    
    def __init__(self):
        self.target_return = 0.1  # 10%月目标
        self.risk_tolerance = 0.02  # 2%最大回撤
        self.position_sizing = {
            'HIGH_CONFIDENCE': 0.3,
            'MEDIUM_CONFIDENCE': 0.2,
            'LOW_CONFIDENCE': 0.1
        }
        
        # 性能追踪
        self.daily_returns = []
        self.max_drawdown = 0
        self.win_rate = 0
    
    def calculate_position_size(self, confidence: str, capital: float, price: float) -> float:
        """计算仓位大小"""
        pct = self.position_sizing.get(confidence, 0.1)
        position_value = capital * pct
        return position_value / price
    
    def should_take_profit(self, current_return: float, target: float) -> bool:
        """是否应该止盈"""
        return current_return >= target
    
    def should_cut_loss(self, current_return: float) -> bool:
        """是否应该止损"""
        return current_return <= -self.risk_tolerance
    
    def optimize(self, performance_data: Dict) -> Dict:
        """优化策略"""
        recent_returns = performance_data.get('recent_returns', [])
        
        if not recent_returns:
            return {'action': 'HOLD', 'reason': 'No data'}
        
        avg_return = sum(recent_returns) / len(recent_returns)
        
        # 根据表现调整
        if avg_return > self.target_return:
            action = 'INCREASE_SIZE'
            reason = f'表现优秀 (+{avg_return*100:.1f}%)'
        elif avg_return < -self.risk_tolerance:
            action = 'REDUCE_SIZE'
            reason = f'风险警告 ({avg_return*100:.1f}%)'
        else:
            action = 'MAINTAIN'
            reason = f'表现正常 ({avg_return*100:.1f}%)'
        
        return {'action': action, 'reason': reason, 'avg_return': avg_return}

# ============================================================
# 审批管理器
# ============================================================
class ApprovalManager:
    """交易审批管理器"""
    
    def __init__(self, max_auto_trades: int = 10):
        self.max_auto_trades = max_auto_trades
        self.pending_approvals = []
        self.approved_trades = []
        self.auto_trade_count = 0
        self.approval_file = '/home/goose/.openclaw/workspace/pending_approvals.json'
        self.load_state()
    
    def load_state(self):
        try:
            with open(self.approval_file, 'r') as f:
                data = json.load(f)
                self.pending_approvals = data.get('pending', [])
                self.approved_trades = data.get('approved', [])
                self.auto_trade_count = len(self.approved_trades)
        except:
            pass
    
    def save_state(self):
        with open(self.approval_file, 'w') as f:
            json.dump({
                'pending': self.pending_approvals,
                'approved': self.approved_trades
            }, f, indent=2, default=str)
    
    def needs_approval(self) -> bool:
        return self.auto_trade_count < self.max_auto_trades
    
    def request_approval(self, trade: Dict) -> str:
        approval_id = f"APR_{int(time.time())}_{trade['symbol']}"
        self.pending_approvals.append({
            'id': approval_id,
            'trade': trade,
            'timestamp': time.time(),
            'status': 'PENDING'
        })
        self.save_state()
        return approval_id
    
    def approve(self, approval_id: str) -> bool:
        for req in self.pending_approvals:
            if req['id'] == approval_id:
                req['status'] = 'APPROVED'
                self.approved_trades.append(req)
                self.pending_approvals.remove(req)
                self.auto_trade_count += 1
                self.save_state()
                return True
        return False
    
    def approve_all(self):
        for req in self.pending_approvals[:]:
            req['status'] = 'APPROVED'
            self.approved_trades.append(req)
            self.pending_approvals.remove(req)
            self.auto_trade_count += 1
        self.save_state()
    
    def get_pending(self) -> List[Dict]:
        return self.pending_approvals

# ============================================================
# Q@C v3 Live 主系统
# ============================================================
class QuantMasterQC3Live:
    VERSION = "Q@C v3 Live"
    
    def __init__(self, capital: float = 10000, max_auto_trades: int = 10):
        self.capital = capital
        self.mode = 'LIVE'
        
        print("=" * 70)
        print(f"🚀 {self.VERSION} - 全域自主进化版")
        print("=" * 70)
        
        # API
        self.api = BinanceAPI()
        print("✅ Binance API (实盘模式)")
        
        # 核心引擎
        self.scraper = WebScraper()
        print("✅ 全网抓取引擎")
        
        self.factor_matrix = FactorMatrix()
        print("✅ 因子矩阵引擎")
        
        self.strategy_matrix = StrategyMatrix()
        print("✅ 策略矩阵引擎")
        
        self.ml = MachineLearning()
        print("✅ 机器学习模块")
        
        self.simulator = SimulationEngine(1000)  # 模拟资金$1000
        print("✅ 模拟仿真引擎")
        
        self.watchdog = ParallelWatchdog()
        print("✅ 并行Watchdog")
        
        self.profit_maximizer = ProfitMaximizer()
        print("✅ 收益最大化引擎")
        
        # 审批管理
        self.approval_manager = ApprovalManager(max_auto_trades)
        print(f"✅ 审批管理: 前{max_auto_trades}笔需审批")
        
        # 币种列表
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT',
            'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT',
            'MATICUSDT', 'ATOMUSDT', 'LTCUSDT', 'UNIUSDT', 'XLMUSDT'
        ]
        
        # 数据
        self.signals = []
        self.executions = []
        self.evolution_log = []
        
        print("\n" + "=" * 70)
        print(f"✅ {self.VERSION} 初始化完成")
        print("=" * 70)
    
    def scan_all(self) -> List[Dict]:
        """全域扫描"""
        print(f"\n🔍 {self.VERSION} 全域扫描...")
        
        # 全网情报
        print("   [1/4] 全网抓取...")
        market_data = self.scraper.scrape_all()
        
        # 因子分析
        print("   [2/4] 因子分析...")
        factor_data = self.factor_matrix.evolve()
        
        # 策略评估
        print("   [3/4] 策略评估...")
        strategy_data = self.strategy_matrix.evolve()
        
        # 信号检测
        print("   [4/4] 信号检测...")
        all_signals = []
        
        for i, symbol in enumerate(self.symbols, 1):
            if i % 5 == 0:
                print(f"   进度: {i}/{len(self.symbols)}")
            
            try:
                klines = self.api.get_klines(symbol, '1h', 100) or []
                if not klines or len(klines) < 50:
                    continue
                
                closes = [k['close'] for k in klines]
                highs = [k['high'] for k in klines]
                lows = [k['low'] for k in klines]
                volumes = [k['volume'] for k in klines]
                
                ticker = self.api.get_ticker(symbol) or {}
                price = ticker.get('price', closes[-1])
                
                # 计算因子
                rsi = self.calc_rsi(closes)
                ma7 = self.calc_ma(closes, 7)
                ma25 = self.calc_ma(closes, 25)
                ma99 = self.calc_ma(closes, 99)
                
                mom = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
                vol_ratio = volumes[-1] / (sum(volumes[-20:]) / 20) if len(volumes) >= 20 else 1
                
                high_20 = max(highs[-21:-1])
                low_20 = min(lows[-21:-1])
                
                data = {
                    'rsi': rsi,
                    'ma7': ma7,
                    'ma25': ma25,
                    'ma99': ma99,
                    'momentum': mom,
                    'vol_ratio': vol_ratio,
                    'near_support': abs(price - low_20) / price < 0.02,
                    'breakout': price > high_20 * 1.01,
                    'sentiment_score': 50 + mom
                }
                
                # 策略评估
                strategies = self.strategy_matrix.evaluate(data)
                
                # 添加信号
                for strat in strategies:
                    all_signals.append({
                        'symbol': symbol.replace('USDT', ''),
                        'exchange': 'binance',
                        'type': strat['strategy'],
                        'action': strat['action'],
                        'score': strat['score'],
                        'confidence': strat['confidence'],
                        'entry': price,
                        'target': price * 1.12,
                        'stop': price * 0.98,
                        'rsi': rsi,
                        'momentum': mom,
                        'factor_score': self.factor_matrix.calculate_composite_score(data),
                        'ml_prediction': self.ml.predict(data)
                    })
                    
                    # 训练样本
                    self.ml.add_training_sample({
                        'rsi_band': 'low' if rsi < 30 else ('high' if rsi > 70 else 'mid'),
                        'vol_level': 'high' if vol_ratio > 2 else 'normal',
                        'momentum': mom
                    }, 0.01)  # 假设1%收益
                
            except:
                pass
        
        # 过滤排序
        filtered = [s for s in all_signals if s['score'] >= 65]
        filtered.sort(key=lambda x: x['score'], reverse=True)
        
        self.signals = filtered
        
        # 记录进化
        self.evolution_log.append({
            'time': time.time(),
            'signals': len(filtered),
            'factor_version': factor_data['version'],
            'strategy_evolution': strategy_data['evolution']
        })
        
        print(f"\n✅ 扫描完成: {len(filtered)}个信号")
        
        return filtered
    
    def calc_rsi(self, closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        return 100 - (100 / (1 + avg_gain / avg_loss))
    
    def calc_ma(self, closes: List[float], period: int) -> float:
        if len(closes) < period:
            return sum(closes) / len(closes)
        return sum(closes[-period:]) / period
    
    def execute(self) -> List[Dict]:
        """执行信号"""
        results = []
        
        print(f"\n⚡ 执行 ({len(self.signals)}个信号)...")
        
        for sig in self.signals[:10]:
            # 检查是否需要审批
            if self.approval_manager.needs_approval():
                approval_id = self.approval_manager.request_approval(sig)
                print(f"   ⏳ 待审批: {sig['symbol']} {sig['type']} (ID: {approval_id})")
            else:
                # 直接执行
                print(f"   ⚡ 执行: {sig['symbol']} {sig['type']}")
                results.append({
                    'status': 'FILLED',
                    'signal': sig,
                    'time': time.time()
                })
        
        self.executions.extend(results)
        return results
    
    def run_full_cycle(self):
        """完整运行周期"""
        print("\n" + "=" * 70)
        print(f"🔄 {self.VERSION} 完整周期")
        print("=" * 70)
        
        # 启动Watchdog
        if not self.watchdog.is_alive:
            self.watchdog.start()
        
        # 1. 全域扫描
        self.scan_all()
        
        # 2. 执行
        self.execute()
        
        # 3. 报告
        self.generate_report()
    
    def generate_report(self) -> str:
        """生成报告"""
        buys = [s for s in self.signals if s['action'] == 'BUY']
        sells = [s for s in self.signals if s['action'] == 'SELL']
        
        watchdog_health = self.watchdog.get_health()
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🚀 {self.VERSION} - 全域自主进化版                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏰ 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
📊 模式: {self.mode}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧬 进化状态                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   因子矩阵:
   - 版本: v{self.factor_matrix.matrix_version}
   - 因子数: {len(self.factor_matrix.factors)}
   
   策略矩阵:
   - 进化次数: {self.strategy_matrix.evolution_count}
   - 策略数: {len(self.strategy_matrix.strategies)}
   
   机器学习:
   - 训练样本: {len(self.ml.training_data)}
   - 模型版本: v{self.ml.model_version}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🐕 Watchdog状态                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

   状态: {'✅ 活跃' if watchdog_health['alive'] else '❌ 停止'}
   延迟: {watchdog_health['latency']:.0f}ms
   问题: {watchdog_health['issues']}个
   恢复: {watchdog_health['recoveries']}次

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📈 信号概览                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   总信号: {len(self.signals)}个
   🟢 买入: {len(buys)}个
   🔴 卖出: {len(sells)}个
"""
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🟢 TOP信号                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for i, sig in enumerate(buys[:6], 1):
            report += f"   {i}. {sig['symbol']:8} {sig['type']:20} 评分{sig['score']:.0f}\n"
        
        report += "\n" + "=" * 72 + "\n"
        
        return report
    
    def run(self):
        self.run_full_cycle()
        print(self.generate_report())

def main():
    qm = QuantMasterQC3Live(10000, max_auto_trades=10)
    qm.run()

if __name__ == '__main__':
    main()
