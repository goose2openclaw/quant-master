"""
Scenario Stress Testing - 危机情景压测
"""
import json
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Scenario:
    name: str
    description: str
    market_shock: float  # 市场冲击 %
    volatility_change: float  # 波动率变化倍数
    correlation_change: float  # 相关性变化
    liquidity_shock: float  # 流动性冲击

class StressTestScenario:
    """压测情景"""
    def __init__(self, name, description, params):
        self.name = name
        self.description = description
        self.market_shock = params.get('market_shock', 0)
        self.volatility_mult = params.get('volatility_mult', 1.0)
        self.correlation_change = params.get('correlation_change', 0)
        self.liquidity_shock = params.get('liquidity_shock', 0)
        self.duration = params.get('duration', 10)  # 天

class ScenarioStressTester:
    """
    情景压测
    模拟历史危机情景
    """
    def __init__(self):
        self.scenarios = {}
        self.results = {}
        self._init_default_scenarios()
    
    def _init_default_scenarios(self):
        """初始化默认情景"""
        self.add_scenario('black_monday', '1987年黑色星期一', {
            'market_shock': -0.22,
            'volatility_mult': 5.0,
            'correlation_change': 0.3,
            'liquidity_shock': -0.5,
            'duration': 5
        })
        
        self.add_scenario('dotcom_crash', '2000年互联网泡沫', {
            'market_shock': -0.78,
            'volatility_mult': 3.0,
            'correlation_change': 0.2,
            'liquidity_shock': -0.3,
            'duration': 30
        })
        
        self.add_scenario('financial_crisis', '2008金融危机', {
            'market_shock': -0.50,
            'volatility_mult': 4.0,
            'correlation_change': 0.4,
            'liquidity_shock': -0.7,
            'duration': 20
        })
        
        self.add_scenario('covid_crash', '2020新冠暴跌', {
            'market_shock': -0.34,
            'volatility_mult': 6.0,
            'correlation_change': 0.5,
            'liquidity_shock': -0.6,
            'duration': 10
        })
        
        self.add_scenario('crypto_winter', '2022加密寒冬', {
            'market_shock': -0.65,
            'volatility_mult': 4.0,
            'correlation_change': 0.3,
            'liquidity_shock': -0.8,
            'duration': 60
        })
        
        self.add_scenario('flash_crash', 'Flash Crash', {
            'market_shock': -0.10,
            'volatility_mult': 10.0,
            'correlation_change': 0.2,
            'liquidity_shock': -0.9,
            'duration': 1
        })
    
    def add_scenario(self, scenario_id, name, params):
        """添加自定义情景"""
        self.scenarios[scenario_id] = StressTestScenario(name, '', params)
    
    def run_stress_test(self, portfolio, positions):
        """
        运行压测
        portfolio: 组合价值
        positions: {symbol: {'weight': 0.x, 'beta': 1.0, 'liquidity': 0.x}}
        """
        results = {}
        
        for scenario_id, scenario in self.scenarios.items():
            # 计算情景影响
            market_loss = portfolio * scenario.market_shock
            
            # 根据持仓调整
            position_losses = {}
            total_exposure = 0
            
            for symbol, pos_data in positions.items():
                weight = pos_data.get('weight', 0)
                beta = pos_data.get('beta', 1.0)
                liquidity = pos_data.get('liquidity', 1.0)
                
                # 损失 = 组合损失 * 权重 * Beta * 流动性折扣
                loss = market_loss * weight * beta * (1 / liquidity if liquidity > 0 else 1)
                position_losses[symbol] = loss
                total_exposure += abs(loss)
            
            # 波动率影响
            vol_increase = (scenario.volatility_mult - 1) * 100
            
            # 流动性损失
            liquidity_loss = portfolio * scenario.liquidity_shock * 0.1
            
            # 总损失
            total_loss = market_loss + liquidity_loss
            
            results[scenario_id] = {
                'name': scenario.name,
                'portfolio_impact': market_loss,
                'total_loss': total_loss,
                'loss_pct': scenario.market_shock * 100,
                'position_losses': position_losses,
                'volatility_increase': vol_increase,
                'liquidity_loss': liquidity_loss,
                'recovery_days': scenario.duration,
                'severity': self._get_severity(total_loss / portfolio)
            }
        
        self.results = results
        return results
    
    def _get_severity(self, loss_pct):
        if loss_pct < -0.3:
            return 'Extreme'
        elif loss_pct < -0.15:
            return 'High'
        elif loss_pct < -0.05:
            return 'Medium'
        else:
            return 'Low'
    
    def get_worst_scenarios(self, n=3):
        """获取最差情景"""
        if not self.results:
            return []
        
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1]['loss_pct']
        )
        
        return sorted_results[:n]
    
    def get_risk_apetite(self, max_acceptable_loss=0.15):
        """评估风险偏好"""
        if not self.results:
            return None
        
        scenarios_within_limit = []
        
        for scenario_id, result in self.results.items():
            if abs(result['loss_pct']) <= max_acceptable_loss * 100:
                scenarios_within_limit.append(scenario_id)
        
        coverage = len(scenarios_within_limit) / len(self.results) * 100
        
        return {
            'scenarios_tested': len(self.results),
            'scenarios_within_limit': len(scenarios_within_limit),
            'coverage': coverage,
            'risk_rating': 'Conservative' if coverage < 30 else ('Moderate' if coverage < 60 else 'Aggressive')
        }
