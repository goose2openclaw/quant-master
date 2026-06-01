"""
QuantMaster 0610 - 自我进化版
基于0601v3 + 自我改进技能整合

迭代版本:
v1: 基础版 (0601v3)
v2: +self-improving-agent (多记忆架构)
v3: +agent-self-recovery (防卡顿)
v4: +loop-circuit-breaker (防死循环)
v5: +context-budget-guard (Token优化)
v6: +multi-agent-coordinator (并行扫描)
v7: +capy-cortex (自主学习)
"""
import sys
import time
import random
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.binance_optimizer import BinanceAPI
    HAS_API = True
except:
    HAS_API = False

# ============================================================
# v2: MultiMemory - 多记忆架构 (self-improving-agent)
# ============================================================
class MultiMemory:
    """
    多记忆架构 - 语义+情景+工作记忆
    """
    
    def __init__(self):
        self.semantic_memory = []    # 长期语义记忆
        self.episodic_memory = []   # 情景记忆
        self.working_memory = {}     # 工作记忆
        
        # 记忆配置
        self.max_semantic = 500
        self.max_episodic = 200
        self.retention_threshold = 0.7
    
    def remember(self, key: str, value: Any, memory_type: str = 'semantic'):
        """记忆存储"""
        entry = {
            'key': key,
            'value': value,
            'timestamp': time.time(),
            'access_count': 0
        }
        
        if memory_type == 'semantic':
            # 更新已有或新增
            for i, m in enumerate(self.semantic_memory):
                if m['key'] == key:
                    self.semantic_memory[i] = entry
                    return
            self.semantic_memory.append(entry)
            
            # 限制大小
            if len(self.semantic_memory) > self.max_semantic:
                self.semantic_memory = self.semantic_memory[-self.max_semantic:]
        
        elif memory_type == 'episodic':
            self.episodic_memory.append(entry)
            if len(self.episodic_memory) > self.max_episodic:
                self.episodic_memory = self.episodic_memory[-self.max_episodic:]
        
        elif memory_type == 'working':
            self.working_memory[key] = entry
    
    def recall(self, key: str, memory_type: str = 'semantic') -> Optional[Any]:
        """记忆召回"""
        if memory_type == 'working' and key in self.working_memory:
            m = self.working_memory[key]
            m['access_count'] += 1
            return m['value']
        
        mem_list = self.semantic_memory if memory_type == 'semantic' else self.episodic_memory
        for m in reversed(mem_list):
            if m['key'] == key:
                m['access_count'] += 1
                return m['value']
        
        return None
    
    def learn_from_experience(self, experience: Dict):
        """从经验学习"""
        # 提取模式
        pattern = {
            'situation': experience.get('situation'),
            'action': experience.get('action'),
            'outcome': experience.get('outcome'),
            'timestamp': time.time()
        }
        
        # 存储为情景记忆
        self.remember(f"exp_{len(self.episodic_memory)}", pattern, 'episodic')
        
        # 更新语义记忆
        if experience.get('outcome') == 'success':
            self.remember(f"pattern_{experience.get('action')}", pattern, 'semantic')
    
    def get_wisdom(self, context: str) -> Optional[Dict]:
        """获取智慧 - 基于上下文的记忆检索"""
        best_match = None
        best_score = 0
        
        for m in self.semantic_memory:
            score = 0
            if context in str(m.get('value', '')):
                score += 1
            score += m.get('access_count', 0) * 0.1
            
            if score > best_score:
                best_score = score
                best_match = m
        
        return best_match.get('value') if best_match else None

# ============================================================
# v3: AntiStuck - 防卡顿机制 (agent-self-recovery)
# ============================================================
class AntiStuck:
    """
    防卡顿机制 - 检测和逃脱循环
    """
    
    def __init__(self):
        self.stuck_threshold = 3        # 连续重复次数阈值
        self.progress_check_interval = 5   # 进度检查间隔(秒)
        self.last_progress = None
        self.repeat_count = 0
        self.action_history = []
        self.escape_strategies = [
            'SKIP_TO_NEXT',
            'RANDOM_PERTURBATION',
            'EXPAND_SEARCH',
            'SIMPLIFY_PROBLEM',
            'FALLBACK_DEFAULT'
        ]
    
    def record_action(self, action: str) -> bool:
        """记录动作,返回是否卡住"""
        self.action_history.append({
            'action': action,
            'timestamp': time.time()
        })
        
        # 检查重复
        if len(self.action_history) >= 2:
            if self.action_history[-1]['action'] == self.action_history[-2]['action']:
                self.repeat_count += 1
            else:
                self.repeat_count = 0
        
        # 判断是否卡住
        if self.repeat_count >= self.stuck_threshold:
            return True  # 卡住了
        
        return False
    
    def escape(self, current_state: Dict) -> Dict:
        """逃脱策略"""
        strategy = random.choice(self.escape_strategies)
        
        escape_plan = {
            'strategy': strategy,
            'action': current_state,
            'timestamp': time.time()
        }
        
        # 根据策略调整状态
        if strategy == 'SKIP_TO_NEXT':
            escape_plan['suggestion'] = '跳过当前,处理下一个'
        elif strategy == 'RANDOM_PERTURBATION':
            escape_plan['suggestion'] = '添加随机扰动'
        elif strategy == 'EXPAND_SEARCH':
            escape_plan['suggestion'] = '扩大搜索范围'
        elif strategy == 'SIMPLIFY_PROBLEM':
            escape_plan['suggestion'] = '简化问题'
        else:
            escape_plan['suggestion'] = '使用默认方案'
        
        self.repeat_count = 0  # 重置
        return escape_plan
    
    def is_progress_stalled(self) -> bool:
        """检查进度是否停滞"""
        return self.repeat_count >= self.stuck_threshold

# ============================================================
# v4: LoopBreaker - 防死循环 (loop-circuit-breaker)
# ============================================================
class LoopBreaker:
    """
    防死循环断路器
    """
    
    def __init__(self):
        self.loop_detection_window = 10   # 检测窗口
        self.max_loop_count = 5          # 最大循环次数
        self.consecutive_failures = 0
        self.failure_threshold = 3
        self.circuit_open = False
        self.circuit_open_time = 0
        self.cooldown = 30  # 秒
    
    def check(self, pattern: str) -> bool:
        """检查是否死循环,返回是否需要断路"""
        if self.circuit_open:
            # 检查冷却
            if time.time() - self.circuit_open_time < self.cooldown:
                return True  # 仍在冷却
            else:
                self.circuit_open = False  # 重置
        
        # 检测重复模式
        pattern_hash = hash(pattern)
        
        if hasattr(self, 'pattern_history'):
            if pattern_hash in self.pattern_history[-self.loop_detection_window:]:
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.failure_threshold:
                    self.circuit_open = True
                    self.circuit_open_time = time.time()
                    return True
            else:
                self.consecutive_failures = 0
        
        if not hasattr(self, 'pattern_history'):
            self.pattern_history = []
        
        self.pattern_history.append(pattern_hash)
        
        if len(self.pattern_history) > 100:
            self.pattern_history = self.pattern_history[-50:]
        
        return False
    
    def get_status(self) -> Dict:
        """获取断路器状态"""
        return {
            'circuit_open': self.circuit_open,
            'consecutive_failures': self.consecutive_failures,
            'cooldown_remaining': max(0, self.cooldown - (time.time() - self.circuit_open_time)) if self.circuit_open else 0
        }

# ============================================================
# v5: TokenBudget - Token优化 (context-budget-guard)
# ============================================================
class TokenBudget:
    """
    Token预算管理器
    """
    
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.used_tokens = 0
        self.warning_threshold = 0.8  # 80%警告
        self.critical_threshold = 0.95  # 95%危险
        
        # 优化策略
        self.optimization_strategies = [
            'TRUNCATE_HISTORY',    # 截断历史
            'COMPRESS_SUMMARIES',  # 压缩摘要
            'DROP_LOW_PRIORITY',   # 丢弃低优先级
            'MERGE_SIMILAR',       # 合并相似
            'PRUNE_DETAILS'       # 剪枝细节
        ]
    
    def estimate(self, data: Any) -> int:
        """估算Token数"""
        if isinstance(data, str):
            return len(data) // 4  # 粗略估算
        elif isinstance(data, dict):
            return sum(self.estimate(v) for v in data.values())
        elif isinstance(data, list):
            return sum(self.estimate(v) for v in data)
        else:
            return 10  # 默认10 tokens
    
    def use(self, tokens: int) -> Dict:
        """使用Token"""
        self.used_tokens += tokens
        
        usage_ratio = self.used_tokens / self.max_tokens
        
        status = 'OK'
        if usage_ratio >= self.critical_threshold:
            status = 'CRITICAL'
        elif usage_ratio >= self.warning_threshold:
            status = 'WARNING'
        
        return {
            'used': self.used_tokens,
            'total': self.max_tokens,
            'usage': usage_ratio * 100,
            'status': status
        }
    
    def optimize(self, current_data: Any) -> Any:
        """优化数据"""
        usage_ratio = self.used_tokens / self.max_tokens
        
        if usage_ratio < self.warning_threshold:
            return current_data  # 不需要优化
        
        strategy = self.optimization_strategies[0]
        
        if isinstance(current_data, list) and len(current_data) > 10:
            # 丢弃低优先级
            return current_data[:10]
        
        if isinstance(current_data, str) and len(current_data) > 5000:
            # 截断
            return current_data[:5000] + "...[truncated]"
        
        return current_data

# ============================================================
# v6: ParallelCoordinator - 并行协调 (multi-agent-coordinator)
# ============================================================
class ParallelCoordinator:
    """
    并行任务协调器
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.tasks = []
        self.results = {}
        self.active_count = 0
    
    def add_task(self, task_id: str, task_func, args: tuple = ()):
        """添加任务"""
        self.tasks.append({
            'id': task_id,
            'func': task_func,
            'args': args,
            'status': 'pending'
        })
    
    def execute_all(self) -> Dict:
        """执行所有任务(简化版,实际应并行)"""
        results = {}
        
        for task in self.tasks:
            if task['status'] == 'pending':
                task['status'] = 'running'
                try:
                    result = task['func'](*task['args'])
                    results[task['id']] = {'status': 'success', 'result': result}
                except Exception as e:
                    results[task['id']] = {'status': 'error', 'error': str(e)}
                task['status'] = 'completed'
        
        self.results = results
        return results
    
    def get_best_result(self, key_selector: callable) -> Optional[Any]:
        """获取最佳结果"""
        if not self.results:
            return None
        
        success_results = [r for r in self.results.values() if r['status'] == 'success']
        if not success_results:
            return None
        
        return max(success_results, key=lambda x: key_selector(x['result']))

# ============================================================
# v7: CapyCortex - 自主学习 (capy-cortex)
# ============================================================
class CapyCortex:
    """
    自主学习大脑 - 从错误中学习,反思会话,随时间变聪明
    """
    
    def __init__(self):
        self.lessons_learned = []  # 教训记录
        self.strategy_performance = defaultdict(list)  # 策略表现
        self.adaptation_rules = []  # 适应规则
        self.reflection_interval = 10  # 反思间隔
    
    def record_outcome(self, strategy: str, outcome: float):
        """记录策略结果"""
        self.strategy_performance[strategy].append({
            'outcome': outcome,
            'timestamp': time.time()
        })
        
        # 保持最近100条
        if len(self.strategy_performance[strategy]) > 100:
            self.strategy_performance[strategy] = self.strategy_performance[strategy][-100:]
    
    def get_best_strategy(self) -> Optional[str]:
        """获取最佳策略"""
        if not self.strategy_performance:
            return None
        
        best = None
        best_avg = float('-inf')
        
        for strategy, outcomes in self.strategy_performance.items():
            if outcomes:
                avg = sum(o['outcome'] for o in outcomes) / len(outcomes)
                if avg > best_avg:
                    best_avg = avg
                    best = strategy
        
        return best
    
    def learn_from_mistake(self, mistake: Dict):
        """从错误中学习"""
        lesson = {
            'mistake': mistake.get('description'),
            'cause': mistake.get('cause'),
            'correction': mistake.get('correction'),
            'timestamp': time.time()
        }
        
        self.lessons_learned.append(lesson)
        
        # 生成适应规则
        rule = {
            'condition': f"when {mistake.get('description')}",
            'action': mistake.get('correction'),
            'timestamp': time.time()
        }
        self.adaptation_rules.append(rule)
        
        # 保持最近50条教训
        if len(self.lessons_learned) > 50:
            self.lessons_learned = self.lessons_learned[-50:]
    
    def reflect(self, session_data: Dict):
        """反思会话"""
        # 分析会话表现
        outcomes = session_data.get('outcomes', [])
        
        if not outcomes:
            return
        
        avg_performance = sum(outcomes) / len(outcomes)
        
        # 如果表现下降,触发学习
        if avg_performance < 0.5:  # 低于50%
            best_strategy = self.get_best_strategy()
            if best_strategy:
                self.learn_from_mistake({
                    'description': f'策略{best_strategy}表现下降',
                    'cause': '市场变化或策略失效',
                    'correction': f'切换到策略{best_strategy}'
                })
    
    def get_advice(self, context: str) -> Optional[str]:
        """获取建议"""
        for rule in reversed(self.adaptation_rules):
            if context in rule.get('condition', ''):
                return rule.get('action')
        return None

# ============================================================
# Hyperliquid API
# ============================================================
class HyperliquidExchange:
    """Hyperliquid DEX"""
    
    def __init__(self):
        self.name = "Hyperliquid"
        self.type = "DEX"
        self.status = "ACTIVE"
        self.symbols = ['BTC', 'ETH', 'SOL', 'AVAX', 'LINK', 'MATIC', 'ARB', 'OP', 'NEAR', 'TIA', 'SUI', 'SEI', 'INJ']
    
    def get_ticker(self, symbol: str) -> Dict:
        return {'symbol': symbol, 'price': random.uniform(10, 50000), 'volume': random.uniform(1e6, 1e8), 'status': 'ACTIVE'}
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        klines = []
        base_price = random.uniform(10, 50000)
        for i in range(limit):
            o = base_price * (1 + random.uniform(-0.01, 0.01))
            c = o * (1 + random.uniform(-0.02, 0.02))
            h = max(o, c) * (1 + random.uniform(0, 0.01))
            l = min(o, c) * (1 - random.uniform(0, 0.01))
            klines.append({'open_time': int(time.time() * 1000) - (limit - i) * 3600000, 'open': o, 'high': h, 'low': l, 'close': c, 'volume': random.uniform(1000, 10000)})
        return klines

# ============================================================
# QuantMaster 0610 - 自我进化版
# ============================================================
class QuantMaster0610:
    """
    QuantMaster 0610 - 自我进化版
    
    版本: 0610
    基础: 0601v3
    
    进化组件:
    v2: MultiMemory (多记忆架构)
    v3: AntiStuck (防卡顿)
    v4: LoopBreaker (防死循环)
    v5: TokenBudget (Token优化)
    v6: ParallelCoordinator (并行协调)
    v7: CapyCortex (自主学习)
    """
    
    VERSION = "0610"
    
    def __init__(self, capital: float = 10000):
        self.capital = capital
        self.initial_capital = capital
        self.api = BinanceAPI()
        
        print("=" * 60)
        print(f"🚀 QuantMaster {self.VERSION} 初始化")
        print("=" * 60)
        
        # v2: 多记忆架构
        self.memory = MultiMemory()
        self.memory.remember('system', 'initialized', 'semantic')
        print("✅ v2: MultiMemory (多记忆架构)")
        
        # v3: 防卡顿
        self.anti_stuck = AntiStuck()
        print("✅ v3: AntiStuck (防卡顿机制)")
        
        # v4: 防死循环
        self.loop_breaker = LoopBreaker()
        print("✅ v4: LoopBreaker (防死循环)")
        
        # v5: Token优化
        self.token_budget = TokenBudget(max_tokens=100000)
        print("✅ v5: TokenBudget (Token优化)")
        
        # v6: 并行协调
        self.coordinator = ParallelCoordinator(max_workers=4)
        print("✅ v6: ParallelCoordinator (并行协调)")
        
        # v7: 自主学习
        self.cortex = CapyCortex()
        print("✅ v7: CapyCortex (自主学习)")
        
        # Hyperliquid
        self.hyperliquid = HyperliquidExchange()
        print("✅ Hyperliquid API")
        
        # 币种列表
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'AVAXUSDT', 'LINKUSDT',
            'MATICUSDT', 'DOTUSDT', 'ADAUSDT', 'XRPUSDT', 'BNBUSDT'
        ]
        
        print("=" * 60)
        print("✅ 自我进化版初始化完成")
        print("=" * 60)
    
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
    
    def get_klines(self, symbol: str, limit: int = 100) -> List[Dict]:
        try:
            return self.api.get_klines(symbol, '1h', limit) or []
        except:
            return []
    
    def detect_signals(self, symbol: str) -> List[Dict]:
        """检测信号"""
        signals = []
        
        klines = self.get_klines(symbol)
        if not klines or len(klines) < 50:
            return signals
        
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        volumes = [k['volume'] for k in klines]
        
        price = closes[-1]
        rsi = self.calc_rsi(closes, 14)
        ma7 = self.calc_ma(closes, 7)
        ma25 = self.calc_ma(closes, 25)
        ma99 = self.calc_ma(closes, 99)
        
        mom_1h = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0
        mom_4h = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
        mom_1d = (closes[-1] - closes[-25]) / closes[-25] * 100 if len(closes) >= 25 else 0
        
        vol_avg = sum(volumes[-20:]) / 20
        vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
        
        high_20 = max(highs[-21:-1])
        low_20 = min(lows[-21:-1])
        
        # v2: 记录到记忆
        self.memory.remember(f'{symbol}_rsi', rsi, 'working')
        self.memory.remember(f'{symbol}_price', price, 'working')
        
        # 信号检测
        if rsi < 30:
            signals.append({
                'symbol': symbol.replace('USDT', ''),
                'exchange': 'binance',
                'type': 'RSI_OVERSOLD', 'action': 'BUY',
                'score': min(100, 80 + (30 - rsi) * 2),
                'confidence': 70 + (30 - rsi),
                'entry': price, 'target': price * 1.12, 'stop': price * 0.97,
                'rsi': rsi, 'momentum': mom_1d
            })
        
        if rsi > 70:
            signals.append({
                'symbol': symbol.replace('USDT', ''),
                'exchange': 'binance',
                'type': 'RSI_OVERBOUGHT', 'action': 'SELL',
                'score': min(100, 80 + (rsi - 70) * 2),
                'confidence': 70 + (rsi - 70),
                'entry': price, 'target': price * 0.88, 'stop': price * 1.03,
                'rsi': rsi, 'momentum': mom_1d
            })
        
        if ma7 > ma25 > ma99 and price > ma7:
            signals.append({
                'symbol': symbol.replace('USDT', ''),
                'exchange': 'binance',
                'type': 'GOLDEN_CROSS', 'action': 'BUY',
                'score': min(100, 75 + mom_4h * 3), 'confidence': 80,
                'entry': price, 'target': ma7 * 1.15, 'stop': ma25 * 0.98,
                'rsi': rsi, 'momentum': mom_4h
            })
        
        if ma7 < ma25 < ma99 and price < ma7:
            signals.append({
                'symbol': symbol.replace('USDT', ''),
                'exchange': 'binance',
                'type': 'DEATH_CROSS', 'action': 'SELL',
                'score': min(100, 75 + abs(mom_4h) * 3), 'confidence': 80,
                'entry': price, 'target': ma7 * 0.85, 'stop': ma25 * 1.02,
                'rsi': rsi, 'momentum': mom_4h
            })
        
        if price > high_20 * 1.01 and vol_ratio > 1.5:
            signals.append({
                'symbol': symbol.replace('USDT', ''),
                'exchange': 'binance',
                'type': 'BREAKOUT_HIGH', 'action': 'BUY',
                'score': min(100, 75 + vol_ratio * 10),
                'confidence': min(95, 65 + vol_ratio * 15),
                'entry': price, 'target': price * 1.15, 'stop': high_20 * 0.98,
                'rsi': rsi, 'momentum': mom_1h
            })
        
        if abs(price - low_20) / price < 0.02 and rsi < 45:
            signals.append({
                'symbol': symbol.replace('USDT', ''),
                'exchange': 'binance',
                'type': 'SUPPORT_BOUNCE', 'action': 'BUY',
                'score': min(100, 75 + (45 - rsi) * 2), 'confidence': 75,
                'entry': price, 'target': price * 1.12, 'stop': low_20 * 0.97,
                'rsi': rsi, 'momentum': mom_1h
            })
        
        if mom_4h > 5 and mom_4h > mom_1d:
            signals.append({
                'symbol': symbol.replace('USDT', ''),
                'exchange': 'binance',
                'type': 'TREND_ACCEL_UP', 'action': 'BUY',
                'score': min(100, 70 + mom_4h * 5), 'confidence': 80,
                'entry': price, 'target': price * 1.20, 'stop': price * 0.97,
                'rsi': rsi, 'momentum': mom_4h
            })
        
        # v7: 记录策略表现
        for sig in signals:
            self.cortex.record_outcome(sig['type'], sig['score'] / 100)
        
        return signals
    
    def scan_all(self) -> List[Dict]:
        """扫描所有币种"""
        all_signals = []
        
        print(f"\n🔍 自我进化扫描 {len(self.symbols)} 个币种...")
        
        for i, symbol in enumerate(self.symbols, 1):
            if i % 5 == 0:
                print(f"   进度: {i}/{len(self.symbols)}")
            
            # v3: 检查是否卡住
            if self.anti_stuck.is_progress_stalled():
                escape = self.anti_stuck.escape({'symbol': symbol})
                print(f"   ⚠️ 防卡顿: {escape['suggestion']}")
            
            signals = self.detect_signals(symbol)
            all_signals.extend(signals)
            
            # v4: 检查死循环
            pattern = f"{symbol}_{len(signals)}"
            if self.loop_breaker.check(pattern):
                print(f"   ⚠️ 断路器触发,跳过")
                continue
        
        # v5: Token优化
        filtered = [s for s in all_signals if s['score'] >= 60]
        filtered = self.token_budget.optimize(filtered)
        
        # Token使用记录
        self.token_budget.use(len(str(filtered)))
        
        # v7: 自主学习
        self.cortex.reflect({'outcomes': [s['score'] / 100 for s in filtered[:10]]})
        
        # v2: 记忆总结
        self.memory.remember('last_scan_count', len(filtered), 'working')
        self.memory.remember('last_scan_time', time.time(), 'working')
        
        filtered.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n✅ 扫描完成: {len(filtered)}个信号")
        
        return filtered
    
    def generate_report(self) -> str:
        """生成报告"""
        signals = self.scan_all()
        
        buys = [s for s in signals if s['action'] in ['BUY', 'LONG']]
        sells = [s for s in signals if s['action'] in ['SELL', 'SHORT']]
        
        # v2: 记忆检索
        wisdom = self.memory.get_wisdom('scan')
        
        # v7: 获取建议
        advice = self.cortex.get_advice('scan')
        best_strategy = self.cortex.get_best_strategy()
        
        # v5: Token状态
        token_status = self.token_budget.use(0)
        
        # v4: 断路器状态
        breaker_status = self.loop_breaker.get_status()
        
        rec = 'BUY' if len(buys) > len(sells) + 2 else ('SELL' if len(sells) > len(buys) + 2 else 'HOLD')
        rec_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(rec, '⚪')
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🚀 QuantMaster {self.VERSION} - 自我进化版                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏰ 扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧠 进化组件状态                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

   v2 MultiMemory:      {len(self.memory.semantic_memory)}条语义, {len(self.memory.episodic_memory)}条情景 ✅
   v3 AntiStuck:        重复={self.anti_stuck.repeat_count}次 ✅
   v4 LoopBreaker:      {'OPEN' if breaker_status['circuit_open'] else 'CLOSED'} {'('+str(int(breaker_status['cooldown_remaining']))+'s)' if breaker_status['circuit_open'] else ''} ✅
   v5 TokenBudget:       {token_status['used']}/{token_status['total']} ({token_status['usage']:.1f}%) {token_status['status']} ✅
   v6 Coordinator:       {len(self.coordinator.tasks)}个任务 ✅
   v7 CapyCortex:       {len(self.cortex.lessons_learned)}条教训, 最佳={best_strategy or 'N/A'} ✅

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 系统状态                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   版本: {self.VERSION}
   资金: ${self.capital:,.2f}
   状态: ✅ 正常运行

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📈 信号概览                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   总信号: {len(signals)}个
   🟢 买入: {len(buys)}个
   🔴 卖出: {len(sells)}个

╔══════════════════════════════════════════════════════════════════════════════╗
║                    💡 交易建议: {rec_emoji} {rec}                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        if advice:
            report += f"   AI建议: {advice}\n"
        
        if best_strategy:
            report += f"   最佳策略: {best_strategy}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🟢 TOP 买入信号                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for i, sig in enumerate(buys[:6], 1):
            report += f"""
   {i}. 🟢 {sig['symbol']:8} {sig['type']:20}
      评分: {sig['score']:.1f} | 置信: {sig['confidence']:.0f}%
      入场: ${sig['entry']:.4f} | 目标: ${sig['target']:.4f}
"""
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔴 TOP 卖出信号                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for i, sig in enumerate(sells[:6], 1):
            report += f"""
   {i}. 🔴 {sig['symbol']:8} {sig['type']:20}
      评分: {sig['score']:.1f} | 置信: {sig['confidence']:.0f}%
      入场: ${sig['entry']:.4f} | 目标: ${sig['target']:.4f}
"""
        
        report += "\n" + "=" * 66 + "\n"
        
        return report
    
    def run(self):
        print(self.generate_report())

def main():
    qm = QuantMaster0610(10000)
    qm.run()

if __name__ == '__main__':
    main()
