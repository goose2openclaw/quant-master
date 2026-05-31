"""
FX Hedging - 外汇对冲
跨境资产对冲
"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class FXPosition:
    currency: str
    amount: float
    hedge_ratio: float  # 0-1
    hedge_type: str  # forward, option, swap

class FXHedgeManager:
    """
    外汇对冲管理器
    """
    def __init__(self):
        self.positions = {}  # {currency: FXPosition}
        self.hedge_types = ['forward', 'option', 'swap', 'none']
        self.default_hedge_ratio = 0.8
    
    def set_hedge_ratio(self, currency: str, ratio: float):
        """设置对冲比例"""
        if currency in self.positions:
            self.positions[currency].hedge_ratio = ratio
    
    def calculate_hedge(self, currency: str, amount: float) -> Dict:
        """计算对冲需求"""
        position = self.positions.get(currency, FXPosition(currency, 0, self.default_hedge_ratio, 'forward'))
        
        hedge_amount = amount * position.hedge_ratio
        
        return {
            'currency': currency,
            'total_exposure': amount,
            'hedge_amount': hedge_amount,
            'hedge_ratio': position.hedge_ratio,
            'unhedged_amount': amount - hedge_amount,
            'recommended_hedge_type': position.hedge_type
        }
    
    def execute_hedge(self, currency: str, amount: float, 
                     hedge_type: str = 'forward') -> Dict:
        """执行对冲"""
        hedge = self.calculate_hedge(currency, amount)
        
        if hedge_type == 'forward':
            return self._execute_forward_hedge(currency, hedge['hedge_amount'])
        elif hedge_type == 'option':
            return self._execute_option_hedge(currency, hedge['hedge_amount'])
        elif hedge_type == 'swap':
            return self._execute_swap_hedge(currency, hedge['hedge_amount'])
        
        return {'success': False, 'error': 'Invalid hedge type'}
    
    def _execute_forward_hedge(self, currency: str, amount: float) -> Dict:
        """远期对冲"""
        # 简化: 生成对冲合约
        return {
            'success': True,
            'hedge_id': f"FWD_{currency}_{amount}",
            'type': 'forward',
            'currency': currency,
            'amount': amount,
            'rate': self._get_fx_rate(currency),
            'settlement_date': 'T+2'
        }
    
    def _execute_option_hedge(self, currency: str, amount: float) -> Dict:
        """期权对冲"""
        return {
            'success': True,
            'hedge_id': f"OPT_{currency}_{amount}",
            'type': 'option',
            'currency': currency,
            'amount': amount,
            'strike': self._get_fx_rate(currency)
        }
    
    def _execute_swap_hedge(self, currency: str, amount: float) -> Dict:
        """互换对冲"""
        return {
            'success': True,
            'hedge_id': f"SWP_{currency}_{amount}",
            'type': 'swap',
            'currency': currency,
            'amount': amount
        }
    
    def _get_fx_rate(self, currency: str) -> float:
        """获取汇率"""
        rates = {
            'EUR': 0.92, 'GBP': 0.79, 'JPY': 149.5, 
            'CHF': 0.88, 'AUD': 1.53, 'CAD': 1.36
        }
        return rates.get(currency, 1.0)
    
    def get_hedge_status(self) -> Dict:
        """获取对冲状态"""
        total_exposure = sum(p.amount for p in self.positions.values())
        hedged_amount = sum(p.amount * p.hedge_ratio for p in self.positions.values())
        
        return {
            'total_exposure': total_exposure,
            'hedged_amount': hedged_amount,
            'hedged_ratio': hedged_amount / total_exposure if total_exposure > 0 else 0,
            'positions': {c: {'amount': p.amount, 'hedge_ratio': p.hedge_ratio} 
                          for c, p in self.positions.items()}
        }

class CrossBorderPortfolio:
    """跨境组合"""
    def __init__(self, fx_manager: FXHedgeManager):
        self.fx_manager = fx_manager
        self.domestic_holdings = {}
        self.foreign_holdings = {}
    
    def add_foreign_holding(self, currency: str, symbol: str, qty: float, price: float):
        """添加外国持仓"""
        if currency not in self.foreign_holdings:
            self.foreign_holdings[currency] = []
        
        value = qty * price
        self.foreign_holdings[currency].append({
            'symbol': symbol,
            'qty': qty,
            'value': value
        })
        
        # 自动对冲
        self.fx_manager.execute_hedge(currency, value)
    
    def calculate_currency_exposure(self) -> Dict:
        """计算货币敞口"""
        exposure = {}
        
        for currency, holdings in self.foreign_holdings.items():
            total_value = sum(h['value'] for h in holdings)
            hedge_status = self.fx_manager.calculate_hedge(currency, total_value)
            
            exposure[currency] = {
                'total_value': total_value,
                'hedged_value': hedge_status['hedge_amount'],
                'unhedged_value': hedge_status['unhedged_amount'],
                'hedge_ratio': hedge_status['hedge_ratio']
            }
        
        return exposure
