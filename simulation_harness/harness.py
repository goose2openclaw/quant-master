"""
Simulation Harness - 蒙特卡洛模拟与压力测试
"""
import sys, random, math, time
from typing import Dict, List, Tuple
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class SimulationResult:
    name: str
    iterations: int
    mean: float
    std: float
    median: float
    percentile_5: float
    percentile_95: float
    min: float
    max: float
    outcomes: List[float]

class MonteCarloSimulator:
    """
    蒙特卡洛模拟引擎
    用于组合预测/风险评估
    """
    
    def __init__(self):
        self.results = {}
    
    def simulate_portfolio_return(self, initial: float, monthly_return: float,
                                  monthly_vol: float, months: int,
                                  iterations: int = 10000) -> SimulationResult:
        """模拟组合收益"""
        outcomes = []
        
        for _ in range(iterations):
            value = initial
            for _ in range(months):
                ret = random.gauss(monthly_return, monthly_vol)
                value *= (1 + ret)
            outcomes.append(value)
        
        outcomes.sort()
        n = len(outcomes)
        
        return SimulationResult(
            name='Portfolio Value',
            iterations=iterations,
            mean=sum(outcomes) / n,
            std=self._std(outcomes),
            median=outcomes[n // 2],
            percentile_5=outcomes[int(n * 0.05)],
            percentile_95=outcomes[int(n * 0.95)],
            min=outcomes[0],
            max=outcomes[-1],
            outcomes=outcomes
        )
    
    def simulate_trading_strategy(self, win_rate: float, avg_win: float,
                                 avg_loss: float, trades: int,
                                 position_size: float,
                                 iterations: int = 10000) -> SimulationResult:
        """模拟交易策略"""
        outcomes = []
        
        for _ in range(iterations):
            balance = 10000  # 初始1万
            for _ in range(trades):
                if random.random() < win_rate:
                    balance *= (1 + avg_win * position_size)
                else:
                    balance *= (1 - avg_loss * position_size)
            outcomes.append(balance)
        
        outcomes.sort()
        n = len(outcomes)
        
        pnl = [(o - 10000) / 10000 * 100 for o in outcomes]
        
        return SimulationResult(
            name='Strategy P&L %',
            iterations=iterations,
            mean=sum(pnl) / n,
            std=self._std(pnl),
            median=pnl[n // 2],
            percentile_5=pnl[int(n * 0.05)],
            percentile_95=pnl[int(n * 0.95)],
            min=pnl[0],
            max=pnl[-1],
            outcomes=pnl
        )
    
    def simulate_market_crash(self, portfolio_value: float,
                             crash_probability: float,
                             avg_crash_pct: float,
                             iterations: int = 10000) -> SimulationResult:
        """模拟市场崩盘"""
        outcomes = []
        
        for _ in range(iterations):
            value = portfolio_value
            if random.random() < crash_probability:
                crash_loss = random.uniform(0.2, avg_crash_pct)
                value *= (1 - crash_loss)
            outcomes.append(value)
        
        outcomes.sort()
        n = len(outcomes)
        
        return SimulationResult(
            name='Portfolio with Crash',
            iterations=iterations,
            mean=sum(outcomes) / n,
            std=self._std(outcomes),
            median=outcomes[n // 2],
            percentile_5=outcomes[int(n * 0.05)],
            percentile_95=outcomes[int(n * 0.95)],
            min=outcomes[0],
            max=outcomes[-1],
            outcomes=outcomes
        )
    
    def stress_test(self, portfolio: Dict) -> Dict:
        """压力测试"""
        results = {}
        
        # 场景
        scenarios = {
            '2008_CRISIS': -0.50,
            '2020_COVID': -0.35,
            '2022_CRYPTO': -0.70,
            'BULL_MARKET': 0.50,
            'SIDEWAYS': 0.05
        }
        
        for scenario, shock in scenarios.items():
            stressed_value = portfolio['total_value'] * (1 + shock)
            drawdown = (1 - stressed_value / portfolio['total_value']) * 100
            
            results[scenario] = {
                'shock_pct': shock * 100,
                'stressed_value': stressed_value,
                'drawdown_pct': drawdown,
                'recovery_time': self._estimate_recovery(shock)
            }
        
        return results
    
    def _estimate_recovery(self, shock: float) -> str:
        """估算恢复时间"""
        if shock >= 0:
            return "N/A (positive)"
        
        shock_abs = abs(shock)
        if shock_abs < 0.2:
            return "3-6 months"
        elif shock_abs < 0.4:
            return "6-12 months"
        elif shock_abs < 0.6:
            return "1-2 years"
        else:
            return "2+ years"
    
    def _std(self, values: List[float]) -> float:
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((v - mean)**2 for v in values) / len(values)
        return math.sqrt(variance)

class ScenarioAnalyzer:
    """
    场景分析器
    多维度市场情景测试
    """
    
    def __init__(self):
        self.scenarios = {}
    
    def add_scenario(self, name: str, conditions: Dict):
        """添加场景"""
        self.scenarios[name] = conditions
    
    def run_scenario_analysis(self, strategy_fn, initial_params: Dict) -> Dict:
        """运行场景分析"""
        results = {}
        
        for name, conditions in self.scenarios.items():
            # 应用场景条件
            params = initial_params.copy()
            params.update(conditions)
            
            # 运行策略
            try:
                result = strategy_fn(params)
                results[name] = {
                    'conditions': conditions,
                    'result': result,
                    'success': True
                }
            except Exception as e:
                results[name] = {
                    'conditions': conditions,
                    'error': str(e),
                    'success': False
                }
        
        return results
    
    def get_worst_case(self, results: Dict) -> Tuple[str, Dict]:
        """最坏情况"""
        worst = min(
            [(k, v) for k, v in results.items() if v.get('success')],
            key=lambda x: x[1].get('result', {}).get('pnl', 0)
        )
        return worst[0], worst[1]
    
    def get_best_case(self, results: Dict) -> Tuple[str, Dict]:
        """最好情况"""
        best = max(
            [(k, v) for k, v in results.items() if v.get('success')],
            key=lambda x: x[1].get('result', {}).get('pnl', 0)
        )
        return best[0], best[1]

# ============================================================================
# DEMO
# ============================================================================

if __name__ == '__main__':
    mc = MonteCarloSimulator()
    
    print("\n=== Monte Carlo Simulation ===")
    print("\n1. Trading Strategy Simulation:")
    print("   Win Rate: 55%, Avg Win: 2%, Avg Loss: 1.5%, 100 trades, 10% position")
    
    result = mc.simulate_trading_strategy(
        win_rate=0.55,
        avg_win=0.02,
        avg_loss=0.015,
        trades=100,
        position_size=0.10,
        iterations=10000
    )
    
    print(f"\n   Results (10,000 iterations):")
    print(f"   Mean: {result.mean:+.2f}%")
    print(f"   Median: {result.median:+.2f}%")
    print(f"   Std Dev: {result.std:.2f}%")
    print(f"   5th Percentile: {result.percentile_5:+.2f}%")
    print(f"   95th Percentile: {result.percentile_95:+.2f}%")
    print(f"   Best Case: {result.max:+.2f}%")
    print(f"   Worst Case: {result.min:+.2f}%")
    
    print("\n2. Portfolio Stress Test:")
    portfolio = {'total_value': 10000}
    stress = mc.stress_test(portfolio)
    
    for scenario, data in stress.items():
        print(f"\n   {scenario}:")
        print(f"     Shock: {data['shock_pct']:+.1f}%")
        print(f"     Stressed Value: ${data['stressed_value']:,.2f}")
        print(f"     Recovery: {data['recovery_time']}")
    
    print("\n=== Simulation Complete ===")
