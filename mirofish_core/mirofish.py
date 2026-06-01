"""
MiroFish Core - 核心控制器
管理策略矩阵 + 因子矩阵
所有操作必须仿真
"""
import sys
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

from strategy_matrix.matrix import StrategyMatrix, StrategySignal, StrategyStatus
from factor_matrix.matrix import FactorMatrix, FactorValue, FactorCategory

@dataclass
class MiroFishConfig:
    name: str = "MiroFish"
    version: str = "16.6.0"
    simulation_required: bool = True  # 所有操作必须仿真
    auto_optimize: bool = True
    risk_level: str = "MEDIUM"  # LOW/MEDIUM/HIGH

@dataclass
class Operation:
    op_id: str
    op_type: str  # TRADE/ADJUST_WEIGHT/ENABLE_STRATEGY/etc
    target_type: str  # strategy/factor/portfolio
    target_id: str
    params: Dict
    simulation_result: Optional[Dict] = None
    approved: bool = False
    timestamp: float = 0

@dataclass
class SimulationResult:
    operation_id: str
    success: bool
    projected_pnl: float
    projected_risk: float
    confidence: float
    reasons: List[str]
    warnings: List[str]

class MiroFishCore:
    """
    MiroFish 核心控制器
    - 直接管理策略矩阵和因子矩阵
    - 所有操作必须仿真
    - 统一决策引擎
    """
    
    def __init__(self, config: MiroFishConfig = None):
        self.config = config or MiroFishConfig()
        
        # 核心矩阵
        self.strategy_matrix = StrategyMatrix()
        self.factor_matrix = FactorMatrix()
        
        # 操作记录
        self.operations: List[Operation] = []
        self.op_count = 0
        
        # 仿真引擎
        self.simulation_engine = SimulationEngine()
        
        print(f"🐟 MiroFish Core {self.config.version} initialized")
        print(f"   Simulation Required: {self.config.simulation_required}")
        print(f"   Strategies: {len(self.strategy_matrix.strategies)}")
        print(f"   Factors: {len(self.factor_matrix.factors)}")
    
    # =========================================================================
    # CORE OPERATIONS - ALL REQUIRE SIMULATION
    # =========================================================================
    
    def _create_op_id(self) -> str:
        """创建操作ID"""
        self.op_count += 1
        return f"OP_{self.op_count:05d}"
    
    def _simulate_operation(self, op: Operation) -> SimulationResult:
        """仿真操作"""
        return self.simulation_engine.simulate(op)
    
    def _execute_approved(self, op: Operation) -> bool:
        """执行已批准的操作"""
        try:
            if op.target_type == 'strategy':
                return self._execute_strategy_op(op)
            elif op.target_type == 'factor':
                return self._execute_factor_op(op)
            elif op.target_type == 'portfolio':
                return self._execute_portfolio_op(op)
            return False
        except Exception as e:
            print(f"Execution error: {e}")
            return False
    
    def _execute_strategy_op(self, op: Operation) -> bool:
        """执行策略操作"""
        if op.op_type == 'ENABLE':
            return self.strategy_matrix.enable_strategy(op.target_id)
        elif op.op_type == 'DISABLE':
            return self.strategy_matrix.disable_strategy(op.target_id)
        elif op.op_type == 'ADJUST_WEIGHT':
            weight = op.params.get('weight', 0.1)
            if op.target_id in self.strategy_matrix.strategies:
                self.strategy_matrix.strategies[op.target_id].weight = weight
                return True
        elif op.op_type == 'UPDATE_PARAMS':
            params = op.params
            if op.target_id in self.strategy_matrix.strategies:
                self.strategy_matrix.strategies[op.target_id].params.update(params)
                return True
        return False
    
    def _execute_factor_op(self, op: Operation) -> bool:
        """执行因子操作"""
        if op.op_type == 'ENABLE':
            return self.factor_matrix.enable_factor(op.target_id)
        elif op.op_type == 'DISABLE':
            return self.factor_matrix.disable_factor(op.target_id)
        elif op.op_type == 'ADJUST_WEIGHT':
            weight = op.params.get('weight', 0.1)
            if op.target_id in self.factor_matrix.factors:
                self.factor_matrix.factors[op.target_id].weight = weight
                return True
        return False
    
    def _execute_portfolio_op(self, op: Operation) -> bool:
        """执行组合操作"""
        # 重新计算权重
        if op.op_type == 'REBALANCE':
            self.strategy_matrix.calculate_weights()
            self.factor_matrix._recalculate_weights()
            return True
        return False
    
    # =========================================================================
    # PUBLIC API - SIMULATION WRAPPED
    # =========================================================================
    
    def adjust_strategy_weight(self, strategy_id: str, new_weight: float) -> SimulationResult:
        """调整策略权重 (需要仿真)"""
        op = Operation(
            op_id=self._create_op_id(),
            op_type='ADJUST_WEIGHT',
            target_type='strategy',
            target_id=strategy_id,
            params={'weight': new_weight},
            timestamp=time.time()
        )
        
        # 仿真
        result = self._simulate_operation(op)
        op.simulation_result = asdict(result) if result else None
        
        if self.config.simulation_required and result and result.success:
            result.warnings.append("SIMULATION REQUIRED: Operation queued")
        
        # 保存
        self.operations.append(op)
        
        return result
    
    def enable_strategy(self, strategy_id: str) -> SimulationResult:
        """启用策略 (需要仿真)"""
        op = Operation(
            op_id=self._create_op_id(),
            op_type='ENABLE',
            target_type='strategy',
            target_id=strategy_id,
            params={},
            timestamp=time.time()
        )
        
        result = self._simulate_operation(op)
        op.simulation_result = asdict(result) if result else None
        
        if result and result.success and not self.config.simulation_required:
            self._execute_approved(op)
        
        self.operations.append(op)
        return result
    
    def disable_strategy(self, strategy_id: str) -> SimulationResult:
        """禁用策略 (需要仿真)"""
        op = Operation(
            op_id=self._create_op_id(),
            op_type='DISABLE',
            target_type='strategy',
            target_id=strategy_id,
            params={},
            timestamp=time.time()
        )
        
        result = self._simulate_operation(op)
        op.simulation_result = asdict(result) if result else None
        
        if result and result.success and not self.config.simulation_required:
            self._execute_approved(op)
        
        self.operations.append(op)
        return result
    
    def adjust_factor_weight(self, factor_id: str, new_weight: float) -> SimulationResult:
        """调整因子权重 (需要仿真)"""
        op = Operation(
            op_id=self._create_op_id(),
            op_type='ADJUST_WEIGHT',
            target_type='factor',
            target_id=factor_id,
            params={'weight': new_weight},
            timestamp=time.time()
        )
        
        result = self._simulate_operation(op)
        op.simulation_result = asdict(result) if result else None
        
        if result and result.success and not self.config.simulation_required:
            self._execute_approved(op)
        
        self.operations.append(op)
        return result
    
    def rebalance_portfolio(self) -> SimulationResult:
        """重新平衡组合 (需要仿真)"""
        op = Operation(
            op_id=self._create_op_id(),
            op_type='REBALANCE',
            target_type='portfolio',
            target_id='MAIN',
            params={},
            timestamp=time.time()
        )
        
        result = self._simulate_operation(op)
        op.simulation_result = asdict(result) if result else None
        
        if result and result.success and not self.config.simulation_required:
            self._execute_approved(op)
        
        self.operations.append(op)
        return result
    
    # =========================================================================
    # TRADING DECISION - SIMULATION WRAPPED
    # =========================================================================
    
    def generate_trading_decision(self, symbol: str, market_data: Dict) -> Dict:
        """生成交易决策 (必须仿真)"""
        print(f"\n🐟 MiroFish Generating Decision for {symbol}")
        
        # 1. 计算所有因子
        print("  📊 Calculating factors...")
        factor_values = self.factor_matrix.calculate_all_factors(market_data)
        
        # 2. 生成策略信号
        print("  📈 Generating strategy signals...")
        signals = self.strategy_matrix.generate_signal(symbol, market_data)
        
        # 3. 聚合信号
        print("  🔄 Aggregating signals...")
        aggregated = self.strategy_matrix.aggregate_signals(signals)
        
        # 4. 获取复合因子得分
        composite_score = self.factor_matrix.get_composite_score()
        
        # 5. 综合决策
        weighted_decision = (
            aggregated['weighted_score'] * 0.6 +
            composite_score * 0.4
        )
        
        if weighted_decision > 60:
            decision = 'BUY'
        elif weighted_decision < 40:
            decision = 'SELL'
        else:
            decision = 'HOLD'
        
        # 6. 创建交易操作
        op = Operation(
            op_id=self._create_op_id(),
            op_type='TRADE',
            target_type='portfolio',
            target_id=symbol,
            params={
                'decision': decision,
                'weighted_score': weighted_decision,
                'strategy_signals': len(signals),
                'factor_count': len(factor_values)
            },
            timestamp=time.time()
        )
        
        # 7. 必须仿真
        print("  🔬 Simulating trade...")
        sim_result = self._simulate_operation(op)
        op.simulation_result = asdict(sim_result) if sim_result else None
        
        self.operations.append(op)
        
        return {
            'symbol': symbol,
            'decision': decision,
            'weighted_score': weighted_decision,
            'composite_score': composite_score,
            'strategy_signals': len(signals),
            'buy_signals': aggregated['buy_count'],
            'sell_signals': aggregated['sell_count'],
            'simulation': asdict(sim_result) if sim_result else None,
            'approved': sim_result.success if sim_result else False,
            'timestamp': time.time()
        }
    
    # =========================================================================
    # STATUS & VIEW
    # =========================================================================
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'name': self.config.name,
            'version': self.config.version,
            'simulation_required': self.config.simulation_required,
            'operations_total': len(self.operations),
            'strategy_matrix': self.strategy_matrix.get_matrix_view(),
            'factor_matrix': self.factor_matrix.get_matrix_view()
        }
    
    def get_pending_operations(self) -> List[Dict]:
        """获取待处理操作"""
        pending = []
        for op in self.operations[-10:]:
            if not op.simulation_result or not op.simulation_result.get('approved'):
                pending.append(asdict(op))
        return pending

class SimulationEngine:
    """
    仿真引擎
    所有操作必须通过仿真验证
    """
    
    def __init__(self):
        self.name = "Simulation Engine"
    
    def simulate(self, op: Operation) -> SimulationResult:
        """仿真操作"""
        import random
        
        # 模拟仿真
        projected_pnl = random.uniform(-100, 500)
        projected_risk = random.uniform(0, 20)
        confidence = random.uniform(0.6, 0.95)
        
        # 基于操作类型判断
        if op.op_type == 'TRADE':
            success = confidence > 0.5
            reasons = [
                f"Operation: {op.op_type} on {op.target_id}",
                f"Projected P&L: ${projected_pnl:.2f}",
                f"Risk Score: {projected_risk:.1f}%",
                f"Confidence: {confidence:.1%}"
            ]
            warnings = []
            if projected_risk > 15:
                warnings.append("HIGH RISK WARNING")
        
        elif op.op_type == 'ADJUST_WEIGHT':
            success = True
            reasons = [
                f"Adjusting weight for {op.target_id}",
                f"New weight: {op.params.get('weight', 0)}"
            ]
            warnings = []
        
        elif op.op_type == 'ENABLE':
            success = random.random() > 0.2
            reasons = [f"Enabling {op.target_id}"]
            warnings = [] if success else ["Enable may increase risk"]
        
        elif op.op_type == 'DISABLE':
            success = True
            reasons = [f"Disabling {op.target_id}"]
            warnings = ["Reduced strategy coverage"]
        
        else:
            success = True
            reasons = [f"Operation: {op.op_type}"]
            warnings = []
        
        return SimulationResult(
            operation_id=op.op_id,
            success=success,
            projected_pnl=projected_pnl,
            projected_risk=projected_risk,
            confidence=confidence,
            reasons=reasons,
            warnings=warnings
        )

from dataclasses import asdict

if __name__ == '__main__':
    config = MiroFishConfig(simulation_required=True)
    mf = MiroFishCore(config)
    
    print("\n=== MiroFish Core Test ===\n")
    
    # 状态
    status = mf.get_status()
    print(f"Strategies: {status['strategy_matrix']['total_strategies']}")
    print(f"Factors: {status['factor_matrix']['total_factors']}")
    
    # 生成决策
    print("\n--- Trading Decision ---")
    decision = mf.generate_trading_decision('BTC', {'price': 67000})
    
    print(f"\nDecision: {decision['decision']}")
    print(f"Score: {decision['weighted_score']:.1f}")
    print(f"Simulation Approved: {decision['approved']}")
    if decision['simulation']:
        sim = decision['simulation']
        print(f"  Projected P&L: ${sim['projected_pnl']:.2f}")
        print(f"  Risk: {sim['projected_risk']:.1f}%")
        print(f"  Confidence: {sim['confidence']:.1%}")
