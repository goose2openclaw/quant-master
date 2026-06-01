"""
Enhanced Risk Analytics
"""
import sys
import random
import math
from typing import List, Dict, Optional

class EnhancedRiskAnalytics:
    """
    增强版风险分析
    - VaR计算
    - CVaR/ES计算
    - 夏普比率
    - 索提诺比率
    - 最大回撤
    - 风险平价
    - 压力测试
    """
    
    def __init__(self):
        self.name = "Enhanced Risk Analytics"
        self.risk_free_rate = 0.02  # 2%无风险利率
        
    def calculate_var(self, returns: List[float], confidence: float = 0.95) -> float:
        """计算VaR"""
        if not returns:
            return 0.0
        
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        var = -sorted_returns[max(0, index)]
        
        return var
    
    def calculate_cvar(self, returns: List[float], confidence: float = 0.95) -> float:
        """计算CVaR/Expected Shortfall"""
        if not returns:
            return 0.0
        
        var = self.calculate_var(returns, confidence)
        tail_returns = [r for r in returns if r <= -var]
        
        if not tail_returns:
            return var
        
        return -sum(tail_returns) / len(tail_returns)
    
    def calculate_baeim(self, returns: List[float], positions: List[float]) -> float:
        """计算BAEIM"""
        if not returns or not positions:
            return 0.0
        
        position_values = [p * r for p, r in zip(positions, returns)]
        total_exposure = sum(abs(p) for p in position_values)
        
        if total_exposure == 0:
            return 0.0
        
        # 简化BAEIM
        return min(1.0, abs(sum(position_values) / total_exposure))
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """计算最大回撤"""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd * 100
    
    def calculate_sharpe(self, returns: List[float], risk_free: float = None) -> float:
        """计算夏普比率"""
        if not returns or len(returns) < 2:
            return 0.0
        
        rf = risk_free if risk_free is not None else self.risk_free_rate
        avg_return = sum(returns) / len(returns)
        
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return 0.0
        
        excess_return = avg_return - rf / 365  # 日化
        sharpe = excess_return / std_dev * math.sqrt(365)
        
        return sharpe
    
    def calculate_sortino(self, returns: List[float], risk_free: float = None) -> float:
        """计算索提诺比率"""
        if not returns or len(returns) < 2:
            return 0.0
        
        rf = risk_free if risk_free is not None else self.risk_free_rate
        avg_return = sum(returns) / len(returns)
        
        # 下行偏差
        downside_returns = [r for r in returns if r < 0]
        
        if not downside_returns:
            return 0.0
        
        downside_std = math.sqrt(sum(r ** 2 for r in downside_returns) / len(downside_returns))
        
        if downside_std == 0:
            return 0.0
        
        excess_return = avg_return - rf / 365
        sortino = excess_return / downside_std * math.sqrt(365)
        
        return sortino
    
    def calculate_calmar(self, equity_curve: List[float]) -> float:
        """计算卡尔玛比率"""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] for i in range(1, len(equity_curve))]
        
        if not returns:
            return 0.0
        
        annual_return = sum(returns) / len(returns) * 365
        max_dd = self.calculate_max_drawdown(equity_curve)
        
        if max_dd == 0:
            return 0.0
        
        return annual_return / (max_dd / 100)
    
    def stress_test(self, equity_curve: List[float], scenarios: List[str] = None) -> Dict:
        """压力测试"""
        if scenarios is None:
            scenarios = ['2008_CRASH', '2020_COVID', '2022_CRYPTO_WINTER', 'BLACK_SWANS']
        
        results = {}
        
        for scenario in scenarios:
            if scenario == '2008_CRASH':
                shock = -0.50
            elif scenario == '2020_COVID':
                shock = -0.35
            elif scenario == '2022_CRYPTO_WINTER':
                shock = -0.60
            else:  # BLACK_SWAN
                shock = -0.80
            
            results[scenario] = {
                'shock': shock * 100,
                'remaining': (1 + shock) * 100,
                'recovery_time': random.randint(6, 24),  # 月份
                'risk_level': 'EXTREME' if shock < -0.5 else 'HIGH' if shock < -0.3 else 'MEDIUM'
            }
        
        return results
    
    def calculate_risk_parity(self, positions: List[Dict]) -> List[Dict]:
        """风险平价配置"""
        if not positions:
            return []
        
        # 计算各资产波动率
        total_vol = sum(p.get('volatility', 0.02) * p.get('weight', 1) for p in positions)
        
        if total_vol == 0:
            return positions
        
        # 重新分配权重使得风险相等
        for p in positions:
            vol = p.get('volatility', 0.02)
            p['risk_parity_weight'] = (vol / total_vol) * sum(p.get('weight', 1) for p in positions)
            p['risk_contribution'] = p['risk_parity_weight'] * vol / total_vol
        
        return positions
    
    def get_full_risk_report(self, equity_curve: Optional[List[float]] = None, positions: Optional[List[Dict]] = None) -> Dict:
        """完整风险报告"""
        if equity_curve is None:
            equity_curve = [10000 + random.uniform(-500, 800) for _ in range(30)]
        
        returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] for i in range(1, len(equity_curve))] if len(equity_curve) > 1 else []
        
        var_95 = self.calculate_var(returns, 0.95)
        var_99 = self.calculate_var(returns, 0.99)
        cvar = self.calculate_cvar(returns, 0.95)
        max_dd = self.calculate_max_drawdown(equity_curve)
        sharpe = self.calculate_sharpe(returns)
        sortino = self.calculate_sortino(returns)
        calmar = self.calculate_calmar(equity_curve)
        
        # 风险等级
        risk_score = abs(var_95) * 50 + max_dd * 0.3 + max(0, -sharpe) * 10
        risk_level = 'EXTREME' if risk_score > 50 else 'HIGH' if risk_score > 30 else 'MEDIUM' if risk_score > 15 else 'LOW'
        
        return {
            'var_95': round(var_95 * 100, 2),
            'var_99': round(var_99 * 100, 2),
            'cvar': round(cvar * 100, 2),
            'max_drawdown': round(max_dd, 2),
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'calmar_ratio': round(calmar, 2),
            'risk_level': risk_level,
            'risk_score': round(risk_score, 1),
            'stress_test': self.stress_test(equity_curve),
            'final_value': equity_curve[-1] if equity_curve else 0,
            'total_return': round((equity_curve[-1] - equity_curve[0]) / equity_curve[0] * 100, 2) if len(equity_curve) > 1 else 0
        }

if __name__ == '__main__':
    ra = EnhancedRiskAnalytics()
    
    print("=" * 60)
    print("⚠️ Enhanced Risk Analytics")
    print("=" * 60)
    
    # 模拟权益曲线
    equity = [10000]
    for _ in range(30):
        equity.append(equity[-1] * (1 + random.uniform(-0.03, 0.05)))
    
    report = ra.get_full_risk_report(equity)
    
    print(f"\n📊 Risk Metrics:")
    print(f"   VaR (95%): {report['var_95']}%")
    print(f"   CVaR: {report['cvar']}%")
    print(f"   Max Drawdown: {report['max_drawdown']}%")
    print(f"   Sharpe: {report['sharpe_ratio']}")
    print(f"   Sortino: {report['sortino_ratio']}")
    print(f"   Calmar: {report['calmar_ratio']}")
    print(f"   Risk Level: {report['risk_level']}")
    
    print(f"\n📈 Performance:")
    print(f"   Return: {report['total_return']}%")
    print(f"   Final: ${report['final_value']:,.2f}")
    
    print("\n" + "=" * 60)
