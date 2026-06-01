"""
Risk Analytics - VaR & BAEIM
风险价值 / 回撤风险 / 风险敞口
"""
import sys
import random
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class RiskMetrics:
    var_95: float
    var_99: float
    baeim: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    volatility: float

class RiskAnalytics:
    """
    风险分析引擎
    - VaR (Value at Risk)
    - BAEIM (Backtested Expected Shortfall)
    - 风险敞口监控
    """
    
    def __init__(self):
        self.name = "Risk Analytics"
        self.confidence_levels = [0.90, 0.95, 0.99]
    
    def calculate_var(self, returns: List[float], confidence: float = 0.95) -> float:
        """计算VaR"""
        if not returns:
            return 0
        sorted_returns = sorted(returns)
        index = int(len(sorted_returns) * (1 - confidence))
        return abs(sorted_returns[max(0, index)])
    
    def calculate_cvar(self, returns: List[float], confidence: float = 0.95) -> float:
        """计算CVaR (Expected Shortfall)"""
        if not returns:
            return 0
        var = self.calculate_var(returns, confidence)
        tail_returns = [r for r in returns if r <= -var]
        return abs(sum(tail_returns) / len(tail_returns)) if tail_returns else var
    
    def calculate_baeim(self, returns: List[float], positions: List[float]) -> float:
        """计算BAEIM (Backtested Adverse Excursion Impact Measure)"""
        if not returns or not positions:
            return 0
        
        # 模拟持仓期间的极端损失
        max_adverse = 0
        for i, ret in enumerate(returns):
            if i < len(positions):
                position = positions[i]
                adverse = abs(ret) * position
                if adverse > max_adverse:
                    max_adverse = adverse
        
        return max_adverse
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
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
    
    def calculate_sharpe(self, returns: List[float], risk_free: float = 0.02) -> float:
        """计算夏普比率"""
        if not returns or len(returns) < 2:
            return 0
        
        avg_return = sum(returns) / len(returns)
        std = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        
        if std == 0:
            return 0
        
        return (avg_return - risk_free) / std * (252 ** 0.5)
    
    def calculate_sortino(self, returns: List[float], risk_free: float = 0.02) -> float:
        """计算索提诺比率"""
        if not returns:
            return 0
        
        avg_return = sum(returns) / len(returns)
        downside_returns = [r for r in returns if r < 0]
        
        if not downside_returns:
            return 0
        
        downside_std = (sum(r ** 2 for r in downside_returns) / len(downside_returns)) ** 0.5
        
        if downside_std == 0:
            return 0
        
        return (avg_return - risk_free) / downside_std * (252 ** 0.5)
    
    def get_full_risk_report(self, equity_curve: List[float] = None,
                           returns: List[float] = None,
                           positions: List[float] = None) -> Dict:
        """完整风险报告"""
        # 生成模拟数据
        if returns is None:
            returns = [random.gauss(0.001, 0.02) for _ in range(100)]
        
        if equity_curve is None:
            equity = [10000]
            for r in returns:
                equity.append(equity[-1] * (1 + r))
        
        if positions is None:
            positions = [1.0] * len(returns)
        
        var_95 = self.calculate_var(returns, 0.95)
        var_99 = self.calculate_var(returns, 0.99)
        cvar = self.calculate_cvar(returns, 0.95)
        baeim = self.calculate_baeim(returns, positions)
        mdd = self.calculate_max_drawdown(equity)
        sharpe = self.calculate_sharpe(returns)
        sortino = self.calculate_sortino(returns)
        
        # 总资产
        total_assets = equity[-1] if equity else 10000
        
        return {
            'total_assets': total_assets,
            'var_95': var_95 * total_assets,
            'var_99': var_99 * total_assets,
            'cvar_95': cvar * total_assets,
            'baeim': baeim,
            'max_drawdown_pct': mdd,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'volatility': (sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns)) ** 0.5 * (252 ** 0.5),
            'risk_level': 'HIGH' if mdd > 20 or sharpe < 0.5 else 'MEDIUM' if mdd > 10 else 'LOW'
        }
    
    def check_risk_limits(self, metrics: Dict) -> List[str]:
        """检查风险限制"""
        violations = []
        
        if metrics.get('var_95', 0) > metrics.get('total_assets', 0) * 0.1:
            violations.append('VaR_95: 超过资产10%')
        
        if metrics.get('max_drawdown_pct', 0) > 20:
            violations.append('MDD: 超过20%')
        
        if metrics.get('sharpe_ratio', 0) < 1.0:
            violations.append('Sharpe: 低于1.0')
        
        if metrics.get('baeim', 0) > metrics.get('total_assets', 0) * 0.15:
            violations.append('BAEIM: 超过资产15%')
        
        return violations

if __name__ == '__main__':
    ra = RiskAnalytics()
    
    print("=== Risk Analytics ===\n")
    
    report = ra.get_full_risk_report()
    
    print(f"Total Assets: ${report['total_assets']:,.2f}")
    print(f"\nRisk Metrics:")
    print(f"  VaR (95%): ${report['var_95']:,.2f}")
    print(f"  VaR (99%): ${report['var_99']:,.2f}")
    print(f"  CVaR (95%): ${report['cvar_95']:,.2f}")
    print(f"  BAEIM: ${report['baeim']:,.2f}")
    print(f"  Max Drawdown: {report['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe: {report['sharpe_ratio']:.2f}")
    print(f"  Sortino: {report['sortino_ratio']:.2f}")
    print(f"  Volatility: {report['volatility']:.2f}%")
    print(f"\n  Risk Level: {report['risk_level']}")
    
    violations = ra.check_risk_limits(report)
    if violations:
        print(f"\n⚠️ Violations:")
        for v in violations:
            print(f"  - {v}")
