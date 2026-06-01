"""
Strategic Watchdog - 战略看门狗
收益最大化 + 全局思考 + 风险把控 + 自我升级
"""
import sys
import time
import random
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class GlobalState:
    """全局状态"""
    total_equity: float
    daily_pnl: float
    total_pnl: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    risk_level: str
    cycle_count: int
    stuck_probability: float

@dataclass
class IterationRecord:
    """迭代记录"""
    iteration: int
    timestamp: float
    global_state: GlobalState
    decisions_made: List[str]
    outcomes: List[str]
    learnings: List[str]

@dataclass
class WatchdogDecision:
    """看门狗决策"""
    decision_type: str
    reason: str
    confidence: float
    action: str
    target: str

class StrategicWatchdog:
    """
    战略看门狗
    
    核心职责:
    1. 收益最大化 - 全局最优而非局部最优
    2. 跳出循环 - 检测局部最优陷阱
    3. 风险把控 - 动态风险调整
    4. 自我升级 - 从历史中学习迭代
    """
    
    def __init__(self, initial_capital: float = 10000):
        self.name = "Strategic Watchdog"
        self.version = "16.6.0"
        
        # 状态
        self.initial_capital = initial_capital
        self.global_state = GlobalState(
            total_equity=initial_capital,
            daily_pnl=0,
            total_pnl=0,
            win_rate=0,
            sharpe_ratio=0,
            max_drawdown=0,
            risk_level="MODERATE",
            cycle_count=0,
            stuck_probability=0
        )
        
        # 迭代历史
        self.iteration_history: List[IterationRecord] = []
        self.current_iteration = 0
        
        # 循环检测
        self.action_history: List[str] = []
        self.repeat_threshold = 5
        self.stuck_counter = 0
        
        # 风险配置
        self.risk_config = {
            'max_drawdown_limit': 0.15,  # 15%
            'daily_loss_limit': 0.05,     # 5%
            'position_limit': 0.25,        # 25%
            'auto_reduce_risk': True
        }
        
        # 学习配置
        self.learning_config = {
            'pattern_window': 20,
            'adaptation_rate': 0.1,
            'min_confidence': 0.6
        }
        
        # 模式
        self.modes = {
            'NORMAL': {'risk_multiplier': 1.0, 'position_size': 0.1},
            'CAUTIOUS': {'risk_multiplier': 0.5, 'position_size': 0.05},
            'AGGRESSIVE': {'risk_multiplier': 1.5, 'position_size': 0.15},
            'SURVIVAL': {'risk_multiplier': 0.2, 'position_size': 0.02}
        }
        self.current_mode = 'NORMAL'
        
        print(f"🧙 Strategic Watchdog v{self.version} initialized")
        print(f"   Initial Capital: ${initial_capital:,.2f}")
        print(f"   Mode: {self.current_mode}")
    
    # =========================================================================
    # CORE LOOP - 全局状态更新
    # =========================================================================
    
    def update_global_state(self, portfolio_state: Dict):
        """更新全局状态"""
        prev_state = self.global_state
        
        # 计算新状态
        current_equity = portfolio_state.get('equity', self.initial_capital)
        daily_pnl = portfolio_state.get('daily_pnl', 0)
        total_pnl = current_equity - self.initial_capital
        
        # 计算指标
        win_rate = portfolio_state.get('win_rate', 0)
        trades = portfolio_state.get('total_trades', 0)
        
        # 权益曲线计算
        equity_curve = portfolio_state.get('equity_curve', [current_equity])
        max_dd = self._calculate_max_drawdown(equity_curve)
        sharpe = self._calculate_sharpe(equity_curve)
        
        # 检测循环
        self.stuck_probability = self._detect_stuck_pattern()
        
        # 更新状态
        self.global_state = GlobalState(
            total_equity=current_equity,
            daily_pnl=daily_pnl,
            total_pnl=total_pnl,
            win_rate=win_rate,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            risk_level=self._assess_risk_level(),
            cycle_count=self.global_state.cycle_count + 1,
            stuck_probability=self.stuck_probability
        )
        
        return self.global_state
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """计算最大回撤"""
        if not equity_curve:
            return 0
        
        peak = equity_curve[0]
        max_dd = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd * 100
    
    def _calculate_sharpe(self, equity_curve: List[float]) -> float:
        """计算夏普比率"""
        if len(equity_curve) < 2:
            return 0
        
        returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] 
                   for i in range(1, len(equity_curve))]
        
        if not returns:
            return 0
        
        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        
        if std_return == 0:
            return 0
        
        return avg_return / std_return * (252 ** 0.5)
    
    # =========================================================================
    # LOOP DETECTION - 跳出循环
    # =========================================================================
    
    def _detect_stuck_pattern(self) -> float:
        """检测是否陷入局部最优"""
        if len(self.action_history) < self.repeat_threshold:
            return 0
        
        # 检查最近动作是否重复
        recent = self.action_history[-self.repeat_threshold:]
        
        # 找最长的重复模式
        for pattern_len in range(1, len(recent) // 2):
            pattern = recent[-pattern_len:]
            prev_pattern = recent[-pattern_len*2:-pattern_len]
            
            if pattern == prev_pattern:
                self.stuck_counter += 1
                return min(1.0, self.stuck_counter / 10)
        
        self.stuck_counter = max(0, self.stuck_counter - 1)
        return self.stuck_counter / 10
    
    def should_break_loop(self) -> bool:
        """判断是否应该跳出循环"""
        if self.stuck_probability > 0.7:
            return True
        
        # 检测收益停滞
        if len(self.iteration_history) >= 10:
            recent_pnl = [r.global_state.total_pnl for r in self.iteration_history[-10:]]
            if max(recent_pnl) == min(recent_pnl):
                return True
        
        return False
    
    # =========================================================================
    # RISK MANAGEMENT - 风险把控
    # =========================================================================
    
    def _assess_risk_level(self) -> str:
        """评估风险等级"""
        state = self.global_state
        
        if state.max_drawdown > 20:
            return "EXTREME"
        elif state.max_drawdown > 15:
            return "HIGH"
        elif state.max_drawdown > 10:
            return "MODERATE"
        elif state.max_drawdown > 5:
            return "LOW"
        else:
            return "SAFE"
    
    def adjust_risk_mode(self) -> str:
        """根据全局状态调整风险模式"""
        state = self.global_state
        prev_mode = self.current_mode
        
        # 风险评估
        if state.risk_level == "EXTREME":
            self.current_mode = "SURVIVAL"
        elif state.risk_level == "HIGH":
            self.current_mode = "CAUTIOUS"
        elif state.risk_level == "SAFE" and state.sharpe_ratio > 1.5:
            self.current_mode = "AGGRESSIVE"
        elif state.daily_pnl < -self.initial_capital * 0.03:
            self.current_mode = "SURVIVAL"
        else:
            self.current_mode = "NORMAL"
        
        if prev_mode != self.current_mode:
            print(f"⚠️ Mode changed: {prev_mode} → {self.current_mode}")
        
        return self.current_mode
    
    def get_risk_adjusted_position_size(self) -> float:
        """获取风险调整后的仓位大小"""
        base = self.modes[self.current_mode]['position_size']
        multiplier = self.modes[self.current_mode]['risk_multiplier']
        
        # 根据回撤调整
        if self.global_state.max_drawdown > 10:
            base *= 0.5
        
        return base * multiplier
    
    def check_risk_limits(self) -> List[str]:
        """检查风险限制"""
        violations = []
        state = self.global_state
        cfg = self.risk_config
        
        if state.max_drawdown > cfg['max_drawdown_limit'] * 100:
            violations.append(f"Max Drawdown {state.max_drawdown:.1f}% exceeds {cfg['max_drawdown_limit']*100}%")
        
        if abs(state.daily_pnl) > cfg['daily_loss_limit'] * self.initial_capital:
            violations.append(f"Daily loss ${abs(state.daily_pnl):.2f} exceeds limit")
        
        return violations
    
    # =========================================================================
    # RETURN MAXIMIZATION - 收益最大化
    # =========================================================================
    
    def find_global_opportunity(self, all_signals: List[Dict]) -> List[Dict]:
        """从全局角度找机会"""
        if not all_signals:
            return []
        
        # 按评分排序
        sorted_signals = sorted(all_signals, key=lambda x: x.get('score', 0), reverse=True)
        
        # 筛选高置信度
        high_conf = [s for s in sorted_signals if s.get('confidence', 0) > 0.6]
        
        # 找不同类型的最佳机会
        opportunities = []
        seen_types = set()
        
        for signal in high_conf:
            signal_type = signal.get('type', 'UNKNOWN')
            
            # 避免同类型重复
            if signal_type in seen_types and len(opportunities) >= 3:
                continue
            
            opportunities.append(signal)
            seen_types.add(signal_type)
            
            if len(opportunities) >= 5:
                break
        
        return opportunities
    
    def calculate_optimal_allocation(self, opportunities: List[Dict]) -> Dict[str, float]:
        """计算最优配置"""
        if not opportunities:
            return {}
        
        position_size = self.get_risk_adjusted_position_size()
        total_equity = self.global_state.total_equity
        
        # Kelly Criterion 简单版
        allocations = {}
        kelly_factor = 0.25  # 降低Kelly波动
        
        for opp in opportunities:
            symbol = opp.get('symbol', 'UNKNOWN')
            win_rate = opp.get('win_rate', 0.5)
            odds = opp.get('odds', 1.5)
            
            # Kelly = W - (1-W)/R
            kelly = (win_rate * odds - (1 - win_rate)) / odds
            kelly = max(0, min(kelly, 0.3)) * kelly_factor
            
            allocation = total_equity * position_size * kelly * 4
            
            allocations[symbol] = min(allocation, total_equity * position_size)
        
        return allocations
    
    # =========================================================================
    # SELF-IMPROVEMENT - 自我升级
    # =========================================================================
    
    def learn_from_iteration(self) -> List[str]:
        """从当前迭代中学习"""
        if len(self.iteration_history) < 5:
            return []
        
        learnings = []
        
        # 分析最近10次迭代
        recent = self.iteration_history[-10:]
        
        # 模式识别
        outcomes = []
        for record in recent:
            outcomes.extend(record.outcomes)
        
        # 检测盈利模式
        wins = [o for o in outcomes if 'WIN' in o or 'PROFIT' in o]
        losses = [o for o in outcomes if 'LOSS' in o or 'STOP' in o]
        
        if len(wins) > len(losses) * 2:
            learnings.append("当前策略盈利能力强,保持配置")
        
        if len(losses) > len(wins):
            learnings.append("亏损增多,考虑降低风险敞口")
        
        # 检测循环
        if self.stuck_probability > 0.5:
            learnings.append("检测到循环模式,需要策略调整")
        
        # 检测回撤
        if self.global_state.max_drawdown > 10:
            learnings.append("回撤过大,应启动保本机制")
        
        return learnings
    
    def adapt_strategy(self) -> Dict[str, Any]:
        """自适应策略调整"""
        learnings = self.learn_from_iteration()
        
        adaptations = {
            'mode_change': self.adjust_risk_mode(),
            'learnings': learnings,
            'position_adjustment': self.get_risk_adjusted_position_size(),
            'stuck_escape': self.should_break_loop(),
            'timestamp': time.time()
        }
        
        return adaptations
    
    # =========================================================================
    # MAIN DECISION ENGINE
    # =========================================================================
    
    def make_decision(self, portfolio_state: Dict, 
                     all_signals: List[Dict]) -> WatchdogDecision:
        """主要决策引擎"""
        # 1. 更新全局状态
        self.update_global_state(portfolio_state)
        
        # 2. 检查风险
        violations = self.check_risk_limits()
        if violations:
            return WatchdogDecision(
                decision_type="RISK_ALERT",
                reason=f"风险限制突破: {violations[0]}",
                confidence=0.9,
                action="REDUCE_EXPOSURE",
                target="PORTFOLIO"
            )
        
        # 3. 检测循环
        if self.should_break_loop():
            adaptations = self.adapt_strategy()
            return WatchdogDecision(
                decision_type="LOOP_ESCAPE",
                reason=f"跳出局部最优,概率={self.stuck_probability:.1%}",
                confidence=0.8,
                action="STRATEGY_ROTATION",
                target="ALL"
            )
        
        # 4. 找全局最优机会
        opportunities = self.find_global_opportunity(all_signals)
        
        if opportunities:
            # 计算最优配置
            allocations = self.calculate_optimal_allocation(opportunities)
            
            return WatchdogDecision(
                decision_type="OPPORTUNITY",
                reason=f"发现{len(opportunities)}个高置信度机会",
                confidence=0.85,
                action="ALLOCATE",
                target=str(list(allocations.keys())[:3])
            )
        
        # 5. 自适应调整
        adaptations = self.adapt_strategy()
        
        if adaptations['learnings']:
            return WatchdogDecision(
                decision_type="SELF_IMPROVE",
                reason=f"学习到: {adaptations['learnings'][0]}",
                confidence=0.7,
                action="ADAPT",
                target="STRATEGY"
            )
        
        # 6. 默认持有
        return WatchdogDecision(
            decision_type="HOLD",
            reason="全局状态正常,无特殊操作",
            confidence=0.6,
            action="MAINTAIN",
            target="CURRENT"
        )
    
    # =========================================================================
    # RECORD & STATUS
    # =========================================================================
    
    def record_iteration(self, decisions: List[str], outcomes: List[str]):
        """记录迭代"""
        record = IterationRecord(
            iteration=self.current_iteration,
            timestamp=time.time(),
            global_state=self.global_state,
            decisions_made=decisions,
            outcomes=outcomes,
            learnings=self.learn_from_iteration()
        )
        
        self.iteration_history.append(record)
        self.action_history.extend(decisions)
        self.current_iteration += 1
        
        # 限制历史大小
        if len(self.iteration_history) > 1000:
            self.iteration_history = self.iteration_history[-500:]
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'name': self.name,
            'version': self.version,
            'mode': self.current_mode,
            'iteration': self.current_iteration,
            'global_state': {
                'equity': self.global_state.total_equity,
                'daily_pnl': self.global_state.daily_pnl,
                'total_pnl': self.global_state.total_pnl,
                'win_rate': self.global_state.win_rate,
                'sharpe': self.global_state.sharpe_ratio,
                'max_drawdown': self.global_state.max_drawdown,
                'risk_level': self.global_state.risk_level,
                'stuck_prob': self.stuck_probability
            },
            'position_size': self.get_risk_adjusted_position_size(),
            'stuck_escape': self.should_break_loop()
        }

if __name__ == '__main__':
    watchdog = StrategicWatchdog(initial_capital=10000)
    
    print("\n=== Strategic Watchdog Test ===\n")
    
    # 模拟状态
    portfolio = {
        'equity': 10500,
        'daily_pnl': 150,
        'win_rate': 0.62,
        'total_trades': 20,
        'equity_curve': [10000, 10100, 10200, 10300, 10400, 10500]
    }
    
    signals = [
        {'symbol': 'BTC', 'score': 72, 'confidence': 0.7, 'type': 'TREND'},
        {'symbol': 'ETH', 'score': 68, 'confidence': 0.65, 'type': 'MOMENTUM'},
        {'symbol': 'SOL', 'score': 65, 'confidence': 0.6, 'type': 'TREND'},
        {'symbol': 'BNB', 'score': 58, 'confidence': 0.5, 'type': 'MEAN_REV'},
    ]
    
    # 做决策
    decision = watchdog.make_decision(portfolio, signals)
    
    print(f"Decision: {decision.decision_type}")
    print(f"Reason: {decision.reason}")
    print(f"Action: {decision.action}")
    print(f"Confidence: {decision.confidence:.1%}")
    
    # 状态
    status = watchdog.get_status()
    print(f"\nStatus:")
    print(f"  Mode: {status['mode']}")
    print(f"  Equity: ${status['global_state']['equity']:,.2f}")
    print(f"  P&L: ${status['global_state']['total_pnl']:,.2f}")
    print(f"  Max DD: {status['global_state']['max_drawdown']:.1f}%")
    print(f"  Risk: {status['global_state']['risk_level']}")
    print(f"  Stuck Prob: {status['global_state']['stuck_prob']:.1%}")
    print(f"  Position Size: {status['position_size']:.1%}")
