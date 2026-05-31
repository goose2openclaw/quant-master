"""
Options Greeks Stream - 期权希腊值实时计算
Delta, Gamma, Theta, Vega, Rho
"""
import math
from scipy.stats import norm
from threading import Thread
from typing import Dict, List

class GreeksCalculator:
    """希腊值计算器"""
    def __init__(self):
        self.cache = {}  # {option_key: greeks}
    
    def calculate_greeks(self, S, K, T, r, sigma, option_type='call'):
        """
        计算期权希腊值
        S: 标的资产价格
        K: 执行价
        T: 到期时间 (年)
        r: 无风险利率
        sigma: 波动率
        """
        if T <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
        
        # d1, d2
        d1 = (math.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Delta
        if option_type == 'call':
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        
        # Gamma (call和put相同)
        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
        
        # Theta
        if option_type == 'call':
            theta = - (S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm.cdf(d2)
        else:
            theta = - (S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm.cdf(-d2)
        theta = theta / 365  # 转为每日
        
        # Vega (call和put相同)
        vega = S * norm.pdf(d1) * math.sqrt(T) / 100  # 每1%波动率
        
        # Rho
        if option_type == 'call':
            rho = K * T * math.exp(-r * T) * norm.cdf(d2) / 100
        else:
            rho = -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho,
            'd1': d1,
            'd2': d2
        }
    
    def calculate_portfolio_greeks(self, positions):
        """
        计算组合希腊值
        positions: [{'type': 'call/put', 'qty': int, 'S': float, 'K': float, 'T': float, 'r': float, 'sigma': float}]
        """
        total_greeks = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
        
        for pos in positions:
            greeks = self.calculate_greeks(
                pos['S'], pos['K'], pos['T'], pos['r'], pos['sigma'], pos.get('type', 'call')
            )
            
            qty = pos.get('qty', 1)
            for key in total_greeks:
                total_greeks[key] += greeks[key] * qty
        
        return total_greeks

class GreeksStreamMonitor:
    """
    希腊值实时监控
    """
    def __init__(self, data_feed):
        self.data_feed = data_feed  # 价格数据源
        self.calculator = GreeksCalculator()
        self.positions = {}
        self.streaming = False
        self.callbacks = []
    
    def add_position(self, symbol, option_type, qty, K, T, r=0.02, sigma=0.5):
        """添加持仓"""
        self.positions[symbol] = {
            'type': option_type,
            'qty': qty,
            'K': K,
            'T': T,
            'r': r,
            'sigma': sigma,
            'S': 0  # 标的当前价
        }
    
    def update_price(self, symbol, spot_price):
        """更新价格"""
        if symbol in self.positions:
            self.positions[symbol]['S'] = spot_price
            self._recalculate(symbol)
    
    def _recalculate(self, symbol):
        """重新计算希腊值"""
        pos = self.positions[symbol]
        
        if pos['S'] == 0:
            return
        
        greeks = self.calculator.calculate_greeks(
            pos['S'], pos['K'], pos['T'], pos['r'], pos['sigma'], pos['type']
        )
        
        # 应用数量
        for key in greeks:
            greeks[key] *= pos['qty']
        
        greeks['symbol'] = symbol
        self.positions[symbol]['greeks'] = greeks
        
        # 触发回调
        for callback in self.callbacks:
            try:
                callback(symbol, greeks)
            except:
                pass
    
    def subscribe(self, callback):
        """订阅希腊值更新"""
        self.callbacks.append(callback)
    
    def get_portfolio_greeks(self):
        """获取组合希腊值"""
        return self.calculator.calculate_portfolio_greeks([
            {**pos, 'type': pos['type']} for pos in self.positions.values()
        ])
    
    def get_position_greeks(self, symbol):
        """获取单个持仓希腊值"""
        return self.positions.get(symbol, {}).get('greeks', {})
    
    def get_risk_summary(self):
        """获取风险摘要"""
        portfolio = self.get_portfolio_greeks()
        
        # Delta中性需要的交易量
        delta_neutral_qty = -portfolio['delta'] if portfolio['delta'] != 0 else 0
        
        return {
            'portfolio': portfolio,
            'delta_neutral_qty': delta_neutral_qty,
            'gamma_risk': abs(portfolio['gamma']),
            'theta_burn': portfolio['theta'],
            'vega_exposure': portfolio['vega']
        }
