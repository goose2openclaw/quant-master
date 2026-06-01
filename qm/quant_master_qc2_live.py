"""
QuantMaster Q@C v2 Live - 实盘版本带审批机制
在Q@C v2基础上增加:
1. 实盘交易模式
2. 前10笔交易需要审批
3. 审批后自动执行
"""
import sys
import time
import json
from typing import Dict, List, Optional
from collections import defaultdict

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.binance_optimizer import BinanceAPI
    HAS_API = True
except:
    HAS_API = False

# ============================================================
# 审批管理器
# ============================================================
class ApprovalManager:
    """交易审批管理器"""
    
    def __init__(self, max_auto_trades: int = 10):
        self.max_auto_trades = max_auto_trades
        self.pending_approvals = []
        self.approved_trades = []
        self.rejected_trades = []
        self.auto_trade_count = 0
        self.approval_file = '/home/goose/.openclaw/workspace/pending_approvals.json'
        
        self.load_state()
    
    def load_state(self):
        """加载状态"""
        try:
            with open(self.approval_file, 'r') as f:
                data = json.load(f)
                self.pending_approvals = data.get('pending', [])
                self.approved_trades = data.get('approved', [])
                self.rejected_trades = data.get('rejected', [])
                self.auto_trade_count = len(self.approved_trades)
        except:
            pass
    
    def save_state(self):
        """保存状态"""
        try:
            with open(self.approval_file, 'w') as f:
                json.dump({
                    'pending': self.pending_approvals,
                    'approved': self.approved_trades,
                    'rejected': self.rejected_trades
                }, f, indent=2, default=str)
        except:
            pass
    
    def needs_approval(self) -> bool:
        """是否需要审批"""
        return self.auto_trade_count < self.max_auto_trades
    
    def request_approval(self, trade: Dict) -> str:
        """申请审批"""
        approval_id = f"APR_{int(time.time())}_{trade['symbol']}"
        
        approval_request = {
            'id': approval_id,
            'trade': trade,
            'timestamp': time.time(),
            'status': 'PENDING'
        }
        
        self.pending_approvals.append(approval_request)
        self.save_state()
        
        return approval_id
    
    def approve(self, approval_id: str) -> bool:
        """批准交易"""
        for req in self.pending_approvals:
            if req['id'] == approval_id:
                req['status'] = 'APPROVED'
                self.approved_trades.append(req)
                self.pending_approvals.remove(req)
                self.auto_trade_count += 1
                self.save_state()
                return True
        return False
    
    def reject(self, approval_id: str) -> bool:
        """拒绝交易"""
        for req in self.pending_approvals:
            if req['id'] == approval_id:
                req['status'] = 'REJECTED'
                self.rejected_trades.append(req)
                self.pending_approvals.remove(req)
                self.save_state()
                return True
        return False
    
    def get_pending(self) -> List[Dict]:
        """获取待审批列表"""
        return self.pending_approvals
    
    def is_auto_mode(self) -> bool:
        """是否自动模式"""
        return self.auto_trade_count >= self.max_auto_trades
    
    def get_status(self) -> Dict:
        return {
            'auto_trade_count': self.auto_trade_count,
            'max_auto_trades': self.max_auto_trades,
            'pending_count': len(self.pending_approvals),
            'is_auto_mode': self.is_auto_mode()
        }

# ============================================================
# 带审批的执行器
# ============================================================
class ApprovalExecutor:
    """带审批的交易执行器"""
    
    def __init__(self, api: BinanceAPI, approval_manager: ApprovalManager):
        self.api = api
        self.approval_manager = approval_manager
        self.execution_history = []
    
    def execute(self, signal: Dict, require_approval: bool = True) -> Dict:
        """执行交易"""
        trade_info = {
            'symbol': signal.get('symbol', ''),
            'action': signal.get('action', ''),
            'type': signal.get('type', ''),
            'entry': signal.get('entry', 0),
            'target': signal.get('target', 0),
            'stop': signal.get('stop', 0),
            'score': signal.get('score', 0),
            'confidence': signal.get('confidence', 0),
            'timestamp': time.time()
        }
        
        # 检查是否需要审批
        if require_approval and self.approval_manager.needs_approval():
            approval_id = self.approval_manager.request_approval(trade_info)
            
            return {
                'status': 'PENDING_APPROVAL',
                'approval_id': approval_id,
                'trade': trade_info,
                'message': f'交易已提交审批 (ID: {approval_id}), 请在OpenClaw中批准'
            }
        
        # 直接执行
        return self.execute_now(trade_info)
    
    def execute_now(self, trade_info: Dict) -> Dict:
        """立即执行"""
        try:
            # 模拟下单
            result = {
                'status': 'FILLED',
                'trade': trade_info,
                'filled_price': trade_info['entry'],
                'filled_time': time.time()
            }
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            return {
                'status': 'FAILED',
                'trade': trade_info,
                'error': str(e)
            }
    
    def approve_and_execute(self, approval_id: str) -> Dict:
        """批准并执行"""
        if self.approval_manager.approve(approval_id):
            for req in self.approval_manager.approved_trades:
                if req['id'] == approval_id:
                    return self.execute_now(req['trade'])
        
        return {'status': 'FAILED', 'error': 'Approval not found'}

# ============================================================
# Q@C v2 Live (复用之前的代码)
# ============================================================
# 导入Q@C v2的核心组件
import threading
from datetime import datetime

class FullSymbolList:
    def __init__(self):
        self.binance_spot = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT', 
            'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT',
            'MATICUSDT', 'ATOMUSDT', 'LTCUSDT', 'UNIUSDT', 'XLMUSDT',
            'ETCUSDT', 'NEARUSDT', 'APTUSDT', 'SUIUSDT', 'SEIUSDT',
            'TIAUSDT', 'INJUSDT', 'JUPUSDT', 'WLDUSDT', 'STRKUSDT',
            'PEPEUSDT', 'SHIBUSDT', 'BONKUSDT', 'CRVUSDT', 'AAVEUSDT'
        ]
        self.hyperliquid = [
            'BTC', 'ETH', 'SOL', 'AVAX', 'LINK', 'MATIC',
            'ARB', 'OP', 'NEAR', 'TIA', 'SUI', 'SEI', 'INJ'
        ]
        self.total = len(self.binance_spot) + len(self.hyperliquid)
    
    def get_all_symbols(self):
        return self.binance_spot

class MultiMemory:
    def __init__(self):
        self.semantic_memory = []
        self.episodic_memory = []
        self.working_memory = {}
    
    def remember(self, key, value, memory_type='semantic'):
        entry = {'key': key, 'value': value, 'timestamp': time.time()}
        if memory_type == 'working':
            self.working_memory[key] = entry
        elif memory_type == 'semantic':
            self.semantic_memory.append(entry)
        else:
            self.episodic_memory.append(entry)
    
    def recall(self, key, memory_type='semantic'):
        if memory_type == 'working' and key in self.working_memory:
            return self.working_memory[key]['value']
        for m in reversed(self.semantic_memory if memory_type == 'semantic' else self.episodic_memory):
            if m['key'] == key:
                return m['value']
        return None

class CapyCortex:
    def __init__(self):
        self.strategy_performance = defaultdict(list)
    
    def record_outcome(self, strategy, outcome):
        self.strategy_performance[strategy].append({'outcome': outcome, 'timestamp': time.time()})
    
    def get_best_strategy(self):
        if not self.strategy_performance:
            return None
        best, best_avg = None, float('-inf')
        for s, outcomes in self.strategy_performance.items():
            if outcomes:
                avg = sum(o['outcome'] for o in outcomes) / len(outcomes)
                if avg > best_avg:
                    best_avg, best = avg, s
        return best

class LoopBreaker:
    def __init__(self):
        self.pattern_history = []
    
    def check(self, pattern):
        h = hash(pattern)
        if h in self.pattern_history[-10:]:
            return True
        self.pattern_history.append(h)
        if len(self.pattern_history) > 50:
            self.pattern_history = self.pattern_history[-30:]
        return False

class ActiveProbe:
    def __init__(self):
        self.probe_types = ['PRICE_ALERT', 'VOLUME_SPIKE', 'TREND_CHANGE']
    
    def probe_all(self, data):
        results = []
        change = (data.get('price', 0) - data.get('prev_price', 0)) / max(1, data.get('prev_price', 1))
        if abs(change) > 0.02:
            results.append({'type': 'PRICE_ALERT', 'change': change * 100})
        if data.get('volume_ratio', 1) > 2:
            results.append({'type': 'VOLUME_SPIKE', 'ratio': data['volume_ratio']})
        return results

class AutonomousDecision:
    def __init__(self):
        self.decision_history = []
        self.position_limit = 5
    
    def make_decision(self, signals, current_positions):
        decisions = []
        sorted_signals = sorted(signals, key=lambda x: x.get('score', 0), reverse=True)
        available = self.position_limit - current_positions
        
        for sig in sorted_signals:
            if len(decisions) >= available:
                break
            score = sig.get('score', 0)
            confidence = sig.get('confidence', 0)
            combined = confidence * 0.4 + score * 0.6
            
            if combined >= 65:
                entry = {
                    'signal': sig,
                    'decision': 'HIGH' if combined >= 80 else 'MEDIUM',
                    'action': 'EXECUTE',
                    'combined_score': combined
                }
                decisions.append(entry)
                self.decision_history.append(entry)
        
        return decisions
    
    def get_recommendation(self):
        if not self.decision_history:
            return 'NO_SIGNAL'
        high = sum(1 for d in self.decision_history[-10:] if d['decision'] == 'HIGH')
        return 'STRONG_BUY' if high >= 3 else 'BUY' if high >= 1 else 'HOLD'

class PeriodicScanner:
    def __init__(self, interval=300):
        self.interval = interval
        self.last_scan = 0
    
    def should_scan(self):
        return time.time() - self.last_scan >= self.interval
    
    def update_last_scan(self):
        self.last_scan = time.time()

# ============================================================
# QuantMaster Q@C v2 Live 主系统
# ============================================================
class QuantMasterQC2Live:
    VERSION = "Q@C v2 Live"
    
    def __init__(self, capital=10000, max_auto_trades=10):
        self.capital = capital
        self.mode = 'LIVE'
        
        print("=" * 60)
        print(f"🚀 {self.VERSION} 初始化")
        print("=" * 60)
        
        self.api = BinanceAPI()
        print("✅ Binance API (实盘模式)")
        
        self.symbols = FullSymbolList()
        print(f"✅ 全域币种: {self.symbols.total}个")
        
        self.memory = MultiMemory()
        self.cortex = CapyCortex()
        self.loop_breaker = LoopBreaker()
        self.scanner = PeriodicScanner(300)
        self.probe = ActiveProbe()
        self.decision_engine = AutonomousDecision()
        
        # 审批管理器
        self.approval_manager = ApprovalManager(max_auto_trades)
        self.executor = ApprovalExecutor(self.api, self.approval_manager)
        
        print(f"✅ 审批模式: 前{max_auto_trades}笔需审批")
        print(f"✅ 当前自动交易: {self.approval_manager.auto_trade_count}/{max_auto_trades}")
        
        self.signals = []
        self.decisions = []
        self.executions = []
        
        print("\n" + "=" * 60)
        print(f"✅ {self.VERSION} 初始化完成")
        print("=" * 60)
    
    def calc_rsi(self, closes, period=14):
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
    
    def calc_ma(self, closes, period):
        if len(closes) < period:
            return sum(closes) / len(closes)
        return sum(closes[-period:]) / period
    
    def scan_all(self):
        all_signals = []
        
        print(f"\n🔍 全域扫描 {len(self.symbols.get_all_symbols())} 个币种...")
        
        for i, symbol in enumerate(self.symbols.get_all_symbols(), 1):
            if i % 10 == 0:
                print(f"   进度: {i}/{len(self.symbols.get_all_symbols())}")
            
            if self.loop_breaker.check(symbol):
                continue
            
            try:
                klines = self.api.get_klines(symbol, '1h', 100) or []
                if not klines or len(klines) < 50:
                    continue
                
                closes = [k['close'] for k in klines]
                highs = [k['high'] for k in klines]
                lows = [k['low'] for k in klines]
                volumes = [k['volume'] for k in klines]
                
                try:
                    ticker = self.api.get_ticker(symbol) or {}
                except:
                    ticker = {}
                
                price = ticker.get('price', closes[-1])
                rsi = self.calc_rsi(closes, 14)
                ma7 = self.calc_ma(closes, 7)
                ma25 = self.calc_ma(closes, 25)
                
                mom_1h = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0
                mom_4h = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
                
                vol_avg = sum(volumes[-20:]) / 20
                vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
                
                high_20 = max(highs[-21:-1])
                low_20 = min(lows[-21:-1])
                
                if rsi < 30:
                    all_signals.append({
                        'symbol': symbol.replace('USDT', ''),
                        'exchange': 'binance',
                        'type': 'RSI_OVERSOLD',
                        'action': 'BUY',
                        'score': min(100, 80 + (30 - rsi) * 2),
                        'confidence': 70 + (30 - rsi),
                        'entry': price,
                        'target': price * 1.12,
                        'stop': price * 0.98,
                        'rsi': rsi,
                        'momentum': mom_4h
                    })
                
                if rsi > 70:
                    all_signals.append({
                        'symbol': symbol.replace('USDT', ''),
                        'exchange': 'binance',
                        'type': 'RSI_OVERBOUGHT',
                        'action': 'SELL',
                        'score': min(100, 80 + (rsi - 70) * 2),
                        'confidence': 70 + (rsi - 70),
                        'entry': price,
                        'target': price * 0.88,
                        'stop': price * 1.03,
                        'rsi': rsi,
                        'momentum': mom_4h
                    })
                
                if ma7 > ma25 and price > ma7:
                    all_signals.append({
                        'symbol': symbol.replace('USDT', ''),
                        'exchange': 'binance',
                        'type': 'GOLDEN_CROSS',
                        'action': 'BUY',
                        'score': min(100, 75 + mom_4h * 3),
                        'confidence': 80,
                        'entry': price,
                        'target': ma7 * 1.12,
                        'stop': ma25 * 0.98,
                        'rsi': rsi,
                        'momentum': mom_4h
                    })
                
                if price > high_20 * 1.01 and vol_ratio > 1.5:
                    all_signals.append({
                        'symbol': symbol.replace('USDT', ''),
                        'exchange': 'binance',
                        'type': 'BREAKOUT_HIGH',
                        'action': 'BUY',
                        'score': min(100, 75 + vol_ratio * 10),
                        'confidence': min(95, 65 + vol_ratio * 15),
                        'entry': price,
                        'target': price * 1.15,
                        'stop': high_20 * 0.98,
                        'rsi': rsi,
                        'momentum': mom_1h
                    })
                
                if abs(price - low_20) / price < 0.02 and rsi < 45:
                    all_signals.append({
                        'symbol': symbol.replace('USDT', ''),
                        'exchange': 'binance',
                        'type': 'SUPPORT_BOUNCE',
                        'action': 'BUY',
                        'score': min(100, 75 + (45 - rsi) * 2),
                        'confidence': 75,
                        'entry': price,
                        'target': price * 1.10,
                        'stop': low_20 * 0.98,
                        'rsi': rsi,
                        'momentum': mom_1h
                    })
                
            except Exception as e:
                pass
        
        filtered = [s for s in all_signals if s['score'] >= 65]
        filtered.sort(key=lambda x: x['score'], reverse=True)
        
        self.signals = filtered
        self.scanner.update_last_scan()
        
        print(f"\n✅ 扫描完成: {len(filtered)}个信号")
        
        return filtered
    
    def make_decisions(self):
        self.decisions = self.decision_engine.make_decision(self.signals, 0)
        
        print(f"\n🤖 决策完成: {len(self.decisions)}个")
        for d in self.decisions:
            sig = d['signal']
            print(f"   {d['decision']}: {sig['symbol']} {sig['type']} ({d['combined_score']:.0f})")
        
        return self.decisions
    
    def execute_all(self):
        """执行所有决策"""
        results = []
        pending = []
        
        for decision in self.decisions:
            sig = decision['signal']
            
            result = self.executor.execute(sig, require_approval=True)
            
            if result['status'] == 'PENDING_APPROVAL':
                pending.append(result)
                print(f"   ⏳ 待审批: {sig['symbol']} {sig['type']} (ID: {result['approval_id']})")
            else:
                results.append(result)
                print(f"   ⚡ 执行: {sig['symbol']} {result.get('status', 'UNKNOWN')}")
        
        self.executions.extend(results)
        
        return results, pending
    
    def run(self):
        """完整运行周期"""
        print("\n" + "=" * 60)
        print(f"🔄 {self.VERSION} 实盘运行")
        print("=" * 60)
        
        # 1. 扫描
        self.scan_all()
        
        # 2. 决策
        self.make_decisions()
        
        # 3. 执行
        results, pending = self.execute_all()
        
        # 4. 状态
        status = self.approval_manager.get_status()
        
        print("\n" + "=" * 60)
        print("📊 执行状态")
        print("=" * 60)
        print(f"   已执行: {len(results)}笔")
        print(f"   待审批: {len(pending)}笔")
        print(f"   自动交易: {status['auto_trade_count']}/{status['max_auto_trades']}")
        print(f"   自动模式: {'✅ 是' if status['is_auto_mode'] else '❌ 否 (需审批)'}")
        
        if pending:
            print("\n" + "=" * 60)
            print("⏳ 待审批交易")
            print("=" * 60)
            for p in pending:
                t = p['trade']
                print(f"   ID: {p['approval_id']}")
                print(f"   币种: {t['symbol']}")
                print(f"   类型: {t['action']} {t['type']}")
                print(f"   入场: ${t['entry']:.4f}")
                print(f"   目标: ${t['target']:.4f}")
                print(f"   止损: ${t['stop']:.4f}")
                print()
        
        return pending

def main():
    qm = QuantMasterQC2Live(10000, max_auto_trades=10)
    qm.run()

if __name__ == '__main__':
    main()
