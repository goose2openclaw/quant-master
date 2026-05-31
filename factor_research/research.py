"""
因子研究框架 - Alpha因子库
"""
import numpy as np
from datetime import datetime

class Factor:
    """因子基类"""
    def __init__(self, name):
        self.name = name
        self.values = []
        self.ic = 0  # Information Coefficient
        self.ir = 0  # Information Ratio
    
    def calculate(self, market_data):
        raise NotImplementedError
    
    def update_ic(self, predicted, actual):
        """更新IC"""
        if len(predicted) > 10:
            correlation = np.corrcoef(predicted[-20:], actual[-20:])[0, 1]
            self.ic = correlation if not np.isnan(correlation) else 0
            self.ir = self.ic / np.std(predicted) if np.std(predicted) > 0 else 0

class FactorRegistry:
    """因子注册表"""
    def __init__(self):
        self.factors = {}
        self.factor_library = {
            'price': PriceFactor,
            'volume': VolumeFactor,
            'momentum': MomentumFactor,
            'mean_reversion': MeanReversionFactor,
            'volatility': VolatilityFactor,
            'trend': TrendFactor,
            'sentiment': SentimentFactor,
            'onchain': OnChainFactor
        }
    
    def register(self, name, factor_class):
        self.factors[name] = factor_class(name)
    
    def get_factor(self, name):
        return self.factors.get(name)
    
    def list_factors(self):
        return list(self.factors.keys())

class PriceFactor(Factor):
    def calculate(self, data):
        return {'price': data[-1] if data else 0}

class VolumeFactor(Factor):
    def calculate(self, data):
        return {'volume': data[-1] if data else 0}

class MomentumFactor(Factor):
    def calculate(self, data):
        if len(data) < 20:
            return {'momentum': 0}
        return {'momentum': (data[-1] - data[-20]) / data[-20] * 100}

class MeanReversionFactor(Factor):
    def calculate(self, data):
        if len(data) < 20:
            return {'zscore': 0}
        mean = np.mean(data[-20:])
        std = np.std(data[-20:])
        if std == 0:
            return {'zscore': 0}
        return {'zscore': (data[-1] - mean) / std}

class VolatilityFactor(Factor):
    def calculate(self, data):
        if len(data) < 20:
            return {'volatility': 0}
        returns = np.diff(data[-20:]) / data[-20:-1]
        return {'volatility': np.std(returns) * np.sqrt(252) * 100}

class TrendFactor(Factor):
    def calculate(self, data):
        if len(data) < 20:
            return {'trend': 0}
        x = np.arange(20)
        slope = np.polyfit(x, data[-20:], 1)[0]
        return {'trend': slope / np.mean(data[-20:]) * 100}

class SentimentFactor(Factor):
    def __init__(self, name):
        super().__init__(name)
        self.sentiment_score = 50
    
    def calculate(self, data):
        return {'sentiment': self.sentiment_score}

class OnChainFactor(Factor):
    def __init__(self, name):
        super().__init__(name)
        self WhaleRatio = 0
        self.ExchangeFlow = 0
    
    def calculate(self, data):
        return {'whale_ratio': self.WhaleRatio, 'exchange_flow': self.ExchangeFlow}

class FactorResearch:
    """
    因子研究框架
    """
    def __init__(self):
        self.registry = FactorRegistry()
        self.backtest_results = {}
    
    def add_factor(self, name, factor_type):
        """添加因子"""
        if factor_type in self.registry.factor_library:
            self.registry.register(name, self.registry.factor_library[factor_type])
            print(f"[FactorResearch] 添加因子: {name} ({factor_type})")
        else:
            print(f"[FactorResearch] 未知因子类型: {factor_type}")
    
    def calculate_portfolio_factors(self, symbols, market_data):
        """计算组合因子"""
        results = {}
        for symbol in symbols:
            results[symbol] = {}
            for name, factor in self.registry.factors.items():
                if symbol in market_data:
                    factor_values = market_data[symbol].get(name, [])
                    results[symbol][name] = factor.calculate(factor_values)
        return results
    
    def backtest_factor(self, factor_name, returns):
        """回测因子"""
        factor = self.registry.get_factor(factor_name)
        if not factor or len(returns) < 30:
            return None
        
        # 计算IC序列
        ic_series = []
        for i in range(30, len(returns)):
            pred = factor.values[i-30:i]
            actual = returns[i-30:i]
            if len(pred) == len(actual) and np.std(pred) > 0 and np.std(actual) > 0:
                ic = np.corrcoef(pred, actual)[0, 1]
                ic_series.append(ic if not np.isnan(ic) else 0)
        
        if not ic_series:
            return None
        
        return {
            'factor': factor_name,
            'ic_mean': np.mean(ic_series),
            'ic_std': np.std(ic_series),
            'ir': np.mean(ic_series) / np.std(ic_series) if np.std(ic_series) > 0 else 0,
            'ic_series': ic_series[-20:]
        }
    
    def get_top_factors(self, returns_dict):
        """获取最优因子"""
        results = []
        for name in self.registry.list_factors():
            bt_result = self.backtest_factor(name, returns_dict.get(name, []))
            if bt_result:
                results.append(bt_result)
        
        results.sort(key=lambda x: x['ir'], reverse=True)
        return results[:10]
