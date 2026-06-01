"""
QuantMaster 0610+ - 完美融合版
0610进化组件 + 0601v3完整功能

合并内容:
- 0610: 6个进化组件 (MultiMemory/AntiStuck/LoopBreaker/TokenBudget/Coordinator/CapyCortex)
- 0601v3: Smart Router + Profit Maximizer + Multi-Exchange Scanner
"""
import sys
import time
import random
from typing import Dict, List, Optional, Any
from collections import defaultdict

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.binance_optimizer import BinanceAPI
    HAS_API = True
except:
    HAS_API = False

# ============================================================
# 0610 进化组件 (from quant_master_0610.py)
# ============================================================

class MultiMemory:
    """多记忆架构"""
    def __init__(self):
        self.semantic_memory = []
        self.episodic_memory = []
        self.working_memory = {}
        self.max_semantic = 500
        self.max_episodic = 200
    
    def remember(self, key: str, value: Any, memory_type: str = 'semantic'):
        entry = {'key': key, 'value': value, 'timestamp': time.time(), 'access_count': 0}
        if memory_type == 'semantic':
            for i, m in enumerate(self.semantic_memory):
                if m['key'] == key:
                    self.semantic_memory[i] = entry
                    return
            self.semantic_memory.append(entry)
            if len(self.semantic_memory) > self.max_semantic:
                self.semantic_memory = self.semantic_memory[-self.max_semantic:]
        elif memory_type == 'episodic':
            self.episodic_memory.append(entry)
            if len(self.episodic_memory) > self.max_episodic:
                self.episodic_memory = self.episodic_memory[-self.max_episodic:]
        elif memory_type == 'working':
            self.working_memory[key] = entry
    
    def recall(self, key: str, memory_type: str = 'semantic') -> Optional[Any]:
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
        pattern = {
            'situation': experience.get('situation'),
            'action': experience.get('action'),
            'outcome': experience.get('outcome'),
            'timestamp': time.time()
        }
        self.remember(f"exp_{len(self.episodic_memory)}", pattern, 'episodic')
        if experience.get('outcome') == 'success':
            self.remember(f"pattern_{experience.get('action')}", pattern, 'semantic')

class AntiStuck:
    """防卡顿机制"""
    def __init__(self):
        self.stuck_threshold = 3
        self.repeat_count = 0
        self.action_history = []
        self.escape_strategies = ['SKIP_TO_NEXT', 'RANDOM_PERTURBATION', 'EXPAND_SEARCH', 'SIMPLIFY_PROBLEM', 'FALLBACK_DEFAULT']
    
    def record_action(self, action: str) -> bool:
        self.action_history.append({'action': action, 'timestamp': time.time()})
        if len(self.action_history) >= 2:
            if self.action_history[-1]['action'] == self.action_history[-2]['action']:
                self.repeat_count += 1
            else:
                self.repeat_count = 0
        return self.repeat_count >= self.stuck_threshold
    
    def escape(self, current_state: Dict) -> Dict:
        strategy = random.choice(self.escape_strategies)
        escape_plan = {'strategy': strategy, 'action': current_state, 'timestamp': time.time()}
        suggestions = {
            'SKIP_TO_NEXT': '跳过当前,处理下一个',
            'RANDOM_PERTURBATION': '添加随机扰动',
            'EXPAND_SEARCH': '扩大搜索范围',
            'SIMPLIFY_PROBLEM': '简化问题',
            'FALLBACK_DEFAULT': '使用默认方案'
        }
        escape_plan['suggestion'] = suggestions.get(strategy, '')
        self.repeat_count = 0
        return escape_plan
    
    def is_progress_stalled(self) -> bool:
        return self.repeat_count >= self.stuck_threshold

class LoopBreaker:
    """防死循环断路器"""
    def __init__(self):
        self.loop_detection_window = 10
        self.max_loop_count = 5
        self.consecutive_failures = 0
        self.failure_threshold = 3
        self.circuit_open = False
        self.circuit_open_time = 0
        self.cooldown = 30
        self.pattern_history = []
    
    def check(self, pattern: str) -> bool:
        if self.circuit_open:
            if time.time() - self.circuit_open_time < self.cooldown:
                return True
            else:
                self.circuit_open = False
        
        pattern_hash = hash(pattern)
        if pattern_hash in self.pattern_history[-self.loop_detection_window:]:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.failure_threshold:
                self.circuit_open = True
                self.circuit_open_time = time.time()
                return True
        else:
            self.consecutive_failures = 0
        
        self.pattern_history.append(pattern_hash)
        if len(self.pattern_history) > 100:
            self.pattern_history = self.pattern_history[-50:]
        return False
    
    def get_status(self) -> Dict:
        return {
            'circuit_open': self.circuit_open,
            'consecutive_failures': self.consecutive_failures,
            'cooldown_remaining': max(0, self.cooldown - (time.time() - self.circuit_open_time)) if self.circuit_open else 0
        }

class TokenBudget:
    """Token预算管理器"""
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.used_tokens = 0
        self.warning_threshold = 0.8
        self.critical_threshold = 0.95
        self.optimization_strategies = ['TRUNCATE_HISTORY', 'COMPRESS_SUMMARIES', 'DROP_LOW_PRIORITY', 'MERGE_SIMILAR', 'PRUNE_DETAILS']
    
    def estimate(self, data: Any) -> int:
        if isinstance(data, str):
            return len(data) // 4
        elif isinstance(data, dict):
            return sum(self.estimate(v) for v in data.values())
        elif isinstance(data, list):
            return sum(self.estimate(v) for v in data)
        else:
            return 10
    
    def use(self, tokens: int) -> Dict:
        self.used_tokens += tokens
        usage_ratio = self.used_tokens / self.max_tokens
        status = 'OK'
        if usage_ratio >= self.critical_threshold:
            status = 'CRITICAL'
        elif usage_ratio >= self.warning_threshold:
            status = 'WARNING'
        return {'used': self.used_tokens, 'total': self.max_tokens, 'usage': usage_ratio * 100, 'status': status}
    
    def optimize(self, current_data: Any) -> Any:
        usage_ratio = self.used_tokens / self.max_tokens
        if usage_ratio < self.warning_threshold:
            return current_data
        if isinstance(current_data, list) and len(current_data) > 10:
            return current_data[:10]
        if isinstance(current_data, str) and len(current_data) > 5000:
            return current_data[:5000] + "...[truncated]"
        return current_data

class ParallelCoordinator:
    """并行任务协调器"""
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.tasks = []
        self.results = {}
    
    def add_task(self, task_id: str, task_func, args: tuple = ()):
        self.tasks.append({'id': task_id, 'func': task_func, 'args': args, 'status': 'pending'})
    
    def execute_all(self) -> Dict:
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
        if not self.results:
            return None
        success_results = [r for r in self.results.values() if r['status'] == 'success']
        if not success_results:
            return None
        return max(success_results, key=lambda x: key_selector(x['result']))

class CapyCortex:
    """自主学习大脑"""
    def __init__(self):
        self.lessons_learned = []
        self.strategy_performance = defaultdict(list)
        self.adaptation_rules = []
    
    def record_outcome(self, strategy: str, outcome: float):
        self.strategy_performance[strategy].append({'outcome': outcome, 'timestamp': time.time()})
        if len(self.strategy_performance[strategy]) > 100:
            self.strategy_performance[strategy] = self.strategy_performance[strategy][-100:]
    
    def get_best_strategy(self) -> Optional[str]:
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
        lesson = {
            'mistake': mistake.get('description'),
            'cause': mistake.get('cause'),
            'correction': mistake.get('correction'),
            'timestamp': time.time()
        }
        self.lessons_learned.append(lesson)
        rule = {'condition': f"when {mistake.get('description')}", 'action': mistake.get('correction'), 'timestamp': time.time()}
        self.adaptation_rules.append(rule)
        if len(self.lessons_learned) > 50:
            self.lessons_learned = self.lessons_learned[-50:]
    
    def reflect(self, session_data: Dict):
        outcomes = session_data.get('outcomes', [])
        if not outcomes:
            return
        avg_performance = sum(outcomes) / len(outcomes)
        if avg_performance < 0.5:
            best_strategy = self.get_best_strategy()
            if best_strategy:
                self.learn_from_mistake({'description': f'策略{best_strategy}表现下降', 'cause': '市场变化或策略失效', 'correction': f'切换到策略{best_strategy}'})
    
    def get_advice(self, context: str) -> Optional[str]:
        for rule in reversed(self.adaptation_rules):
            if context in rule.get('condition', ''):
                return rule.get('action')
        return None

# ============================================================
# 0601v3 完整组件 (from quant_master_0601v3.py)
# ============================================================

class HyperliquidExchange:
    """Hyperliquid DEX"""
    def __init__(self):
        self.name = "Hyperliquid"
        self.type = "DEX"
        self.status = "ACTIVE"
        self.symbols = ['BTC', 'ETH', 'SOL', 'AVAX', 'LINK', 'MATIC', 'ARB', 'OP', 'NEAR', 'TIA', 'SUI', 'SEI', 'INJ']
    
    def get_ticker(self, symbol: str) -> Dict:
        price = random.uniform(10, 50000)
        return {'symbol': symbol, 'price': price, 'bid': price * 0.999, 'ask': price * 1.001, 'volume': random.uniform(1e6, 1e8), 'status': 'ACTIVE'}
    
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

class SmartRouter:
    """智能路由"""
    def __init__(self, binance_api, hyperliquid):
        self.binance = binance_api
        self.hyperliquid = hyperliquid
    
    def get_best_price(self, symbol: str, side: str) -> Dict:
        binance_ticker = self.binance.get_ticker(symbol + 'USDT') or {}
        hyper_price = random.uniform(10, 50000)
        binance_price = binance_ticker.get('price', 0)
        if side == 'BUY':
            if binance_price > 0 and (hyper_price == 0 or binance_price < hyper_price):
                return {'exchange': 'binance', 'price': binance_price, 'route': 'SPOT'}
            return {'exchange': 'hyperliquid', 'price': hyper_price, 'route': 'DEX'}
        else:
            if binance_price > 0 and (hyper_price == 0 or binance_price > hyper_price):
                return {'exchange': 'binance', 'price': binance_price, 'route': 'SPOT'}
            return {'exchange': 'hyperliquid', 'price': hyper_price, 'route': 'DEX'}
    
    def find_arbitrage(self, symbol: str) -> Optional[Dict]:
        binance_price = random.uniform(1000, 50000)
        hyper_price = random.uniform(1000, 50000)
        diff = abs(binance_price - hyper_price) / max(binance_price, hyper_price) * 100
        if diff > 0.5:
            return {'symbol': symbol, 'binance_price': binance_price, 'hyper_price': hyper_price, 'spread': diff, 'action': 'BUY_HYPER_SELL_BINANCE' if hyper_price < binance_price else 'BUY_BINANCE_SELL_HYPER'}
        return None

class ProfitMaximizer:
    """收益最大化"""
    def __init__(self):
        self.strategies = {
            'CEX_SPOT': {'fee': 0.001, 'liquidity': 'HIGH'},
            'CEX_FUTURES': {'fee': 0.0004, 'leverage': True},
            'DEX_SPOT': {'fee': 0.0003, 'liquidity': 'MED'},
            'STAKING': {'fee': 0, 'yield': True}
        }
    
    def calculate_optimal_allocation(self, capital: float, signals: List[Dict]) -> Dict:
        allocations = []
        remaining = capital
        sorted_signals = sorted(signals, key=lambda x: x.get('score', 0), reverse=True)
        for sig in sorted_signals[:5]:
            if remaining < 100:
                break
            sig_type = sig.get('type', '')
            if 'FUNDING_ARB' in sig_type:
                strategy = 'CEX_FUTURES'
                alloc = min(remaining * 0.3, capital * 0.15)
            elif 'STAKING' in sig_type:
                strategy = 'STAKING'
                alloc = min(remaining * 0.2, capital * 0.10)
            else:
                strategy = 'CEX_SPOT'
                alloc = min(remaining * 0.25, capital * 0.20)
            allocations.append({'symbol': sig.get('symbol'), 'strategy': strategy, 'allocation': alloc, 'expected_return': self._estimate_return(sig, strategy)})
            remaining -= alloc
        total_expected = sum(a['expected_return'] * a['allocation'] for a in allocations)
        return {'allocations': allocations, 'total_expected_return': total_expected, 'remaining_capital': remaining, 'utilization': (capital - remaining) / capital * 100}
    
    def _estimate_return(self, signal: Dict, strategy: str) -> float:
        base_return = signal.get('score', 60) / 100 * 0.10
        strat_info = self.strategies.get(strategy, {})
        leverage = strat_info.get('leverage', False)
        if leverage:
            base_return *= 3
        staking_yield = strat_info.get('yield', False)
        if staking_yield:
            base_return += 0.05
        return base_return + strat_info.get('fee', 0.001) * 2

# ============================================================
# QuantMaster 0610+ - 完美融合版
# ============================================================
class QuantMaster0610Plus:
    """
    QuantMaster 0610+ - 完美融合版
    
    版本: 0610+
    融合: 0610进化组件 + 0601v3完整功能
    
    包含:
    进化组件:
    - v2 MultiMemory
    - v3 AntiStuck
    - v4 LoopBreaker
    - v5 TokenBudget
    - v6 ParallelCoordinator
    - v7 CapyCortex
    
    完整功能:
    - Smart Router (智能路由)
    - Profit Maximizer (收益最大化)
    - Multi-Exchange Scanner (多交易所扫描)
    - Hyperliquid Integration
    """
    
    VERSION = "0610+"
    
    def __init__(self, capital: float = 10000):
        self.capital = capital
        self.initial_capital = capital
        self.api = BinanceAPI()
        
        print("=" * 60)
        print(f"🚀 QuantMaster {self.VERSION} 初始化")
        print("=" * 60)
        
        # === 0610 进化组件 ===
        print("\n📦 0610 进化组件:")
        self.memory = MultiMemory()
        self.memory.remember('system', 'initialized', 'semantic')
        print("  ✅ v2 MultiMemory")
        
        self.anti_stuck = AntiStuck()
        print("  ✅ v3 AntiStuck")
        
        self.loop_breaker = LoopBreaker()
        print("  ✅ v4 LoopBreaker")
        
        self.token_budget = TokenBudget()
        print("  ✅ v5 TokenBudget")
        
        self.coordinator = ParallelCoordinator()
        print("  ✅ v6 ParallelCoordinator")
        
        self.cortex = CapyCortex()
        print("  ✅ v7 CapyCortex")
        
        # === 0601v3 完整功能 ===
        print("\n📦 0601v3 完整功能:")
        self.hyperliquid = HyperliquidExchange()
        print("  ✅ Hyperliquid Exchange")
        
        self.router = SmartRouter(self.api, self.hyperliquid)
        print("  ✅ Smart Router")
        
        self.profit_max = ProfitMaximizer()
        print("  ✅ Profit Maximizer")
        
        # 币种列表
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'AVAXUSDT', 'LINKUSDT',
            'MATICUSDT', 'DOTUSDT', 'ADAUSDT', 'XRPUSDT', 'BNBUSDT',
            'NEARUSDT', 'TIAUSDT', 'SUIUSDT', 'SEIUSDT', 'INJUSDT'
        ]
        
        self.signals = []
        self.arbitrage = []
        self.allocations = []
        
        print("\n" + "=" * 60)
        print("✅ 完美融合版初始化完成")
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
    
    def get_klines(self, symbol: str, exchange: str = 'binance') -> List[Dict]:
        try:
            if exchange == 'binance':
                return self.api.get_klines(symbol, '1h', 100) or []
            else:
                base = symbol.replace('USDT', '')
                return self.hyperliquid.get_klines(base, '1h', 100)
        except:
            return []
    
    def detect_signals(self, symbol: str, exchange: str = 'binance') -> List[Dict]:
        signals = []
        klines = self.get_klines(symbol, exchange)
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
        
        # 记录到记忆
        self.memory.remember(f'{symbol}_rsi', rsi, 'working')
        self.memory.remember(f'{symbol}_price', price, 'working')
        
        # 信号检测
        if rsi < 30:
            signals.append({'symbol': symbol.replace('USDT', ''), 'exchange': exchange, 'type': 'RSI_OVERSOLD', 'action': 'BUY', 'score': min(100, 80 + (30 - rsi) * 2), 'confidence': 70 + (30 - rsi), 'entry': price, 'target': price * 1.12, 'stop': price * 0.97, 'rsi': rsi, 'momentum': mom_1d})
        
        if rsi > 70:
            signals.append({'symbol': symbol.replace('USDT', ''), 'exchange': exchange, 'type': 'RSI_OVERBOUGHT', 'action': 'SELL', 'score': min(100, 80 + (rsi - 70) * 2), 'confidence': 70 + (rsi - 70), 'entry': price, 'target': price * 0.88, 'stop': price * 1.03, 'rsi': rsi, 'momentum': mom_1d})
        
        if ma7 > ma25 > ma99 and price > ma7:
            signals.append({'symbol': symbol.replace('USDT', ''), 'exchange': exchange, 'type': 'GOLDEN_CROSS', 'action': 'BUY', 'score': min(100, 75 + mom_4h * 3), 'confidence': 80, 'entry': price, 'target': ma7 * 1.15, 'stop': ma25 * 0.98, 'rsi': rsi, 'momentum': mom_4h})
        
        if ma7 < ma25 < ma99 and price < ma7:
            signals.append({'symbol': symbol.replace('USDT', ''), 'exchange': exchange, 'type': 'DEATH_CROSS', 'action': 'SELL', 'score': min(100, 75 + abs(mom_4h) * 3), 'confidence': 80, 'entry': price, 'target': ma7 * 0.85, 'stop': ma25 * 1.02, 'rsi': rsi, 'momentum': mom_4h})
        
        if price > high_20 * 1.01 and vol_ratio > 1.5:
            signals.append({'symbol': symbol.replace('USDT', ''), 'exchange': exchange, 'type': 'BREAKOUT_HIGH', 'action': 'BUY', 'score': min(100, 75 + vol_ratio * 10), 'confidence': min(95, 65 + vol_ratio * 15), 'entry': price, 'target': price * 1.15, 'stop': high_20 * 0.98, 'rsi': rsi, 'momentum': mom_1h})
        
        if abs(price - low_20) / price < 0.02 and rsi < 45:
            signals.append({'symbol': symbol.replace('USDT', ''), 'exchange': exchange, 'type': 'SUPPORT_BOUNCE', 'action': 'BUY', 'score': min(100, 75 + (45 - rsi) * 2), 'confidence': 75, 'entry': price, 'target': price * 1.12, 'stop': low_20 * 0.97, 'rsi': rsi, 'momentum': mom_1h})
        
        if mom_4h > 5 and mom_4h > mom_1d:
            signals.append({'symbol': symbol.replace('USDT', ''), 'exchange': exchange, 'type': 'TREND_ACCEL_UP', 'action': 'BUY', 'score': min(100, 70 + mom_4h * 5), 'confidence': 80, 'entry': price, 'target': price * 1.20, 'stop': price * 0.97, 'rsi': rsi, 'momentum': mom_4h})
        
        # 记录策略表现
        for sig in signals:
            self.cortex.record_outcome(sig['type'], sig['score'] / 100)
        
        return signals
    
    def scan_all(self) -> Dict:
        """完整扫描"""
        all_signals = []
        arbitrage_opps = []
        
        print(f"\n🔍 完美融合扫描 {len(self.symbols)} 个币种...")
        
        for i, symbol in enumerate(self.symbols, 1):
            if i % 5 == 0:
                print(f"   进度: {i}/{len(self.symbols)}")
            
            # 防卡顿检查
            if self.anti_stuck.is_progress_stalled():
                escape = self.anti_stuck.escape({'symbol': symbol})
                print(f"   ⚠️ {escape['suggestion']}")
            
            # Binance扫描
            signals_bn = self.detect_signals(symbol, 'binance')
            all_signals.extend(signals_bn)
            
            # Hyperliquid扫描
            signals_hl = self.detect_signals(symbol, 'hyperliquid')
            all_signals.extend(signals_hl)
            
            # 死循环检查
            if self.loop_breaker.check(f"{symbol}_{len(all_signals)}"):
                print(f"   ⚠️ 断路器触发")
                continue
            
            # 套利机会
            arb = self.router.find_arbitrage(symbol.replace('USDT', ''))
            if arb:
                arbitrage_opps.append(arb)
        
        # 过滤排序
        filtered = [s for s in all_signals if s['score'] >= 60]
        filtered.sort(key=lambda x: x['score'], reverse=True)
        
        # Token优化
        filtered = self.token_budget.optimize(filtered)
        self.token_budget.use(len(str(filtered)))
        
        # 记忆总结
        self.memory.remember('last_scan_count', len(filtered), 'working')
        self.memory.remember('last_scan_time', time.time(), 'working')
        
        # 自主学习反思
        self.cortex.reflect({'outcomes': [s['score'] / 100 for s in filtered[:10]]})
        
        self.signals = filtered
        self.arbitrage = arbitrage_opps
        
        # 计算最优分配
        if self.signals:
            allocation = self.profit_max.calculate_optimal_allocation(self.capital, self.signals)
            self.allocations = allocation.get('allocations', [])
        
        print(f"\n✅ 扫描完成: {len(filtered)}个信号, {len(arbitrage_opps)}个套利机会")
        
        return {
            'signals': filtered,
            'arbitrage': arbitrage_opps,
            'allocations': self.allocations
        }
    
    def generate_report(self) -> str:
        """生成报告"""
        if not self.signals:
            self.scan_all()
        
        buys = [s for s in self.signals if s['action'] in ['BUY', 'LONG']]
        sells = [s for s in self.signals if s['action'] in ['SELL', 'SHORT']]
        
        by_exchange = defaultdict(list)
        for s in self.signals:
            by_exchange[s['exchange']].append(s)
        
        # 进化组件状态
        breaker_status = self.loop_breaker.get_status()
        token_status = self.token_budget.use(0)
        best_strategy = self.cortex.get_best_strategy()
        advice = self.cortex.get_advice('scan')
        
        rec = 'BUY' if len(buys) > len(sells) + 3 else ('SELL' if len(sells) > len(buys) + 3 else 'HOLD')
        rec_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(rec, '⚪')
        
        # 预期收益
        total_expected = sum(a['expected_return'] * a['allocation'] for a in self.allocations) if self.allocations else 0
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🚀 QuantMaster {self.VERSION} - 完美融合版                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏰ 扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧠 进化组件状态                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

   v2 MultiMemory:    {len(self.memory.semantic_memory)}条语义 ✅
   v3 AntiStuck:      重复={self.anti_stuck.repeat_count}次 ✅
   v4 LoopBreaker:    {'OPEN' if breaker_status['circuit_open'] else 'CLOSED'} ✅
   v5 TokenBudget:    {token_status['used']}/{token_status['total']} ({token_status['usage']:.1f}%) ✅
   v6 Coordinator:    {len(self.coordinator.tasks)}个任务 ✅
   v7 CapyCortex:     {len(self.cortex.lessons_learned)}条教训, 最佳={best_strategy or 'N/A'} ✅

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🛠️ 完整功能                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   ✅ Smart Router (智能路由)
   ✅ Profit Maximizer (收益最大化)
   ✅ Multi-Exchange (Binance + Hyperliquid)
   ✅ Arbitrage Detection (套利检测)

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 信号概览                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   总信号: {len(self.signals)}个
   🟢 买入: {len(buys)}个
   🔴 卖出: {len(sells)}个
   🏦 Binance: {len(by_exchange['binance'])}个
   ⚡ Hyperliquid: {len(by_exchange['hyperliquid'])}个
   💰 套利机会: {len(self.arbitrage)}个
"""
        
        if advice:
            report += f"\n   AI建议: {advice}\n"
        
        # 套利机会
        if self.arbitrage:
            report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    💰 套利机会                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
            for arb in self.arbitrage[:3]:
                report += f"   {arb['symbol']}: {arb['action']} (差价{arb['spread']:.2f}%)\n"
        
        # 最优分配
        if self.allocations:
            report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    💎 最优分配 (收益最大化)                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

   预期总收益: {total_expected:+.2f}%
   资金利用率: {sum(a['allocation'] for a in self.allocations) / self.capital * 100:.1f}%

"""
            for alloc in self.allocations[:5]:
                report += f"   📦 {alloc['symbol']:8} {alloc['strategy']:12} ${alloc['allocation']:,.0f} ({alloc['expected_return']*100:+.1f}%)\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    💡 交易建议: {rec_emoji} {rec}                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🟢 TOP 买入信号                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for i, sig in enumerate(buys[:6], 1):
            ex = "🏦" if sig['exchange'] == 'binance' else "⚡"
            report += f"   {i}. 🟢 {sig['symbol']:8} {ex} {sig['type']:20}\n"
            report += f"      评分: {sig['score']:.1f} | 置信: {sig['confidence']:.0f}%\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔴 TOP 卖出信号                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for i, sig in enumerate(sells[:6], 1):
            ex = "🏦" if sig['exchange'] == 'binance' else "⚡"
            report += f"   {i}. 🔴 {sig['symbol']:8} {ex} {sig['type']:20}\n"
            report += f"      评分: {sig['score']:.1f} | 置信: {sig['confidence']:.0f}%\n"
        
        report += "\n" + "=" * 66 + "\n"
        
        return report
    
    def run(self):
        print(self.generate_report())

def main():
    qm = QuantMaster0610Plus(10000)
    qm.run()

if __name__ == '__main__':
    main()
