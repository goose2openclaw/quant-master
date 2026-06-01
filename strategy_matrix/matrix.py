"""
Strategy Matrix - 策略矩阵系统
所有策略统一矩阵化管理
"""
import sys
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

class StrategyType(Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    ARBITRAGE = "arbitrage"
    SCALPING = "scalping"
    SWING = "swing"

class StrategyStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    OPTIMIZING = "optimizing"
    DEPRECATED = "deprecated"

@dataclass
class StrategyConfig:
    strategy_id: str
    name: str
    type: StrategyType
    params: Dict[str, float]
    status: StrategyStatus
    performance: Dict[str, float]
    weight: float
    enabled: bool
    created_at: float
    updated_at: float
    tags: List[str] = field(default_factory=list)

@dataclass
class StrategySignal:
    strategy_id: str
    strategy_name: str
    signal_type: str  # BUY/SELL/HOLD
    confidence: float
    score: float
    reasons: List[str]
    timestamp: float

class StrategyMatrix:
    """
    策略矩阵
    - 网格化管理所有策略
    - 性能追踪
    - 动态权重
    - 信号聚合
    """
    
    def __init__(self):
        self.name = "Strategy Matrix"
        self.strategies: Dict[str, StrategyConfig] = {}
        self.signal_history: List[StrategySignal] = []
        self.performance_history: Dict[str, List[float]] = {}
        
        # 矩阵配置
        self.matrix_config = {
            'max_active_strategies': 10,
            'min_confidence': 0.5,
            'weight_update_interval': 3600,  # 1小时
            'auto_optimize': True
        }
        
        # 初始化内置策略
        self._init_builtin_strategies()
    
    def _init_builtin_strategies(self):
        """初始化内置策略"""
        builtins = [
            ('RSI', StrategyType.MEAN_REVERSION, {'rsi_period': 14, 'oversold': 30, 'overbought': 70}),
            ('MACD', StrategyType.MOMENTUM, {'fast': 12, 'slow': 26, 'signal': 9}),
            ('Bollinger', StrategyType.MEAN_REVERSION, {'period': 20, 'std_dev': 2}),
            ('Momentum', StrategyType.MOMENTUM, {'period': 10, 'threshold': 0.02}),
            ('Breakout', StrategyType.BREAKOUT, {'period': 20, 'atr_period': 14}),
            ('Scalping', StrategyType.SCALPING, {'ema_fast': 5, 'ema_slow': 13}),
            ('Swing', StrategyType.SWING, {'smas': [10, 20, 50]}),
            ('Grid', StrategyType.ARBITRAGE, {'grid_size': 10, 'width_pct': 0.01}),
        ]
        
        for name, stype, params in builtins:
            sid = f"STRAT_{name.upper()}"
            self.strategies[sid] = StrategyConfig(
                strategy_id=sid,
                name=name,
                type=stype,
                params=params,
                status=StrategyStatus.ACTIVE,
                performance={'win_rate': 0.55, 'sharpe': 1.2, 'mdd': 10},
                weight=0.1,
                enabled=True,
                created_at=time.time(),
                updated_at=time.time(),
                tags=['builtin']
            )
    
    def add_strategy(self, strategy: StrategyConfig) -> bool:
        """添加策略到矩阵"""
        if strategy.strategy_id in self.strategies:
            return False
        self.strategies[strategy.strategy_id] = strategy
        return True
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """从矩阵移除策略"""
        if strategy_id in self.strategies:
            del self.strategies[strategy_id]
            return True
        return False
    
    def enable_strategy(self, strategy_id: str) -> bool:
        """启用策略"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].enabled = True
            self.strategies[strategy_id].updated_at = time.time()
            return True
        return False
    
    def disable_strategy(self, strategy_id: str) -> bool:
        """禁用策略"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].enabled = False
            self.strategies[strategy_id].status = StrategyStatus.PAUSED
            self.strategies[strategy_id].updated_at = time.time()
            return True
        return False
    
    def update_performance(self, strategy_id: str, perf: Dict[str, float]):
        """更新策略性能"""
        if strategy_id not in self.strategies:
            return
        
        strat = self.strategies[strategy_id]
        strat.performance = perf
        strat.updated_at = time.time()
        
        # 记录历史
        if strategy_id not in self.performance_history:
            self.performance_history[strategy_id] = []
        self.performance_history[strategy_id].append(perf.get('sharpe', 0))
    
    def calculate_weights(self):
        """基于性能计算策略权重"""
        total_score = 0
        scores = {}
        
        for sid, strat in self.strategies.items():
            if not strat.enabled:
                continue
            
            # 综合评分: Sharpe * WinRate * (1 - MDD/100)
            perf = strat.performance
            sharpe = perf.get('sharpe', 0)
            win_rate = perf.get('win_rate', 0) / 100
            mdd = perf.get('mdd', 10) / 100
            
            score = sharpe * 2 + win_rate * 3 - mdd * 2
            scores[sid] = max(0, score)
            total_score += max(0, score)
        
        # 归一化权重
        if total_score > 0:
            for sid in scores:
                self.strategies[sid].weight = scores[sid] / total_score
    
    def generate_signal(self, symbol: str, market_data: Dict) -> List[StrategySignal]:
        """所有策略生成信号"""
        signals = []
        
        for sid, strat in self.strategies.items():
            if not strat.enabled:
                continue
            
            # 模拟信号生成
            score = self._calculate_strategy_score(strat, market_data)
            confidence = strat.performance.get('win_rate', 0.5)
            
            if score > 60:
                signal_type = 'BUY'
                reasons = [f"{strat.name} 信号强烈"]
            elif score < 40:
                signal_type = 'SELL'
                reasons = [f"{strat.name} 建议离场"]
            else:
                signal_type = 'HOLD'
                reasons = [f"{strat.name} 观望"]
            
            signal = StrategySignal(
                strategy_id=sid,
                strategy_name=strat.name,
                signal_type=signal_type,
                confidence=confidence,
                score=score,
                reasons=reasons,
                timestamp=time.time()
            )
            
            signals.append(signal)
            self.signal_history.append(signal)
        
        return signals
    
    def _calculate_strategy_score(self, strat: StrategyConfig, data: Dict) -> float:
        """计算策略评分"""
        import random
        base = 50
        
        # 根据类型调整
        if strat.type == StrategyType.MOMENTUM:
            base += random.uniform(-10, 20)
        elif strat.type == StrategyType.MEAN_REVERSION:
            base += random.uniform(-5, 15)
        elif strat.type == StrategyType.BREAKOUT:
            base += random.uniform(0, 20)
        elif strat.type == StrategyType.ARBITRAGE:
            base += random.uniform(5, 25)
        
        # 权重影响
        base += strat.weight * 20
        
        return max(0, min(100, base))
    
    def aggregate_signals(self, signals: List[StrategySignal]) -> Dict:
        """聚合信号"""
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        sell_signals = [s for s in signals if s.signal_type == 'SELL']
        
        # 加权评分
        total_score = 0
        for s in signals:
            total_score += s.score * self.strategies[s.strategy_id].weight
        
        # 最终决策
        if len(buy_signals) > len(sell_signals) and len(buy_signals) >= 3:
            decision = 'BUY'
        elif len(sell_signals) > len(buy_signals) and len(sell_signals) >= 3:
            decision = 'SELL'
        else:
            decision = 'HOLD'
        
        return {
            'decision': decision,
            'buy_count': len(buy_signals),
            'sell_count': len(sell_signals),
            'hold_count': len(signals) - len(buy_signals) - len(sell_signals),
            'weighted_score': total_score,
            'signals': signals,
            'timestamp': time.time()
        }
    
    def get_matrix_view(self) -> Dict:
        """获取矩阵视图"""
        active = [s for s in self.strategies.values() if s.enabled]
        
        return {
            'total_strategies': len(self.strategies),
            'active_count': len(active),
            'total_weight': sum(s.weight for s in active),
            'strategies': [{
                'id': s.strategy_id,
                'name': s.name,
                'type': s.type.value,
                'status': s.status.value,
                'weight': s.weight,
                'enabled': s.enabled,
                'performance': s.performance
            } for s in self.strategies.values()]
        }

if __name__ == '__main__':
    matrix = StrategyMatrix()
    
    print("=== Strategy Matrix ===\n")
    
    # 矩阵视图
    view = matrix.get_matrix_view()
    print(f"Total Strategies: {view['total_strategies']}")
    print(f"Active: {view['active_count']}")
    
    # 计算权重
    matrix.calculate_weights()
    
    # 生成信号
    signals = matrix.generate_signal('BTC', {'price': 67000})
    
    print(f"\nSignals Generated: {len(signals)}")
    for s in signals[:5]:
        print(f"  {s.strategy_name}: {s.signal_type} ({s.score:.1f})")
    
    # 聚合
    agg = matrix.aggregate_signals(signals)
    print(f"\nAggregated: {agg['decision']}")
    print(f"  BUY: {agg['buy_count']}, SELL: {agg['sell_count']}, HOLD: {agg['hold_count']}")
    print(f"  Weighted Score: {agg['weighted_score']:.1f}")
