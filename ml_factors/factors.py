"""
机器学习因子库
"""
import numpy as np
from collections import deque

class MLFactor:
    """机器学习因子基类"""
    def __init__(self, name):
        self.name = name
        self.values = []
        self._window = []
    
    def update(self, value):
        self._window.append(value)
        self.values.append(value)
    
    def reset(self):
        self.values = []
        self._window = []


class RollingStatFactor(MLFactor):
    """滚动统计因子"""
    def __init__(self, name, window=20):
        super().__init__(name)
        self.window = window
        self._deque = deque(maxlen=window)
    
    def update(self, value):
        self._deque.append(value)
        self.values.append(value)
    
    def mean(self):
        return np.mean(self._deque) if len(self._deque) == self.window else None
    
    def std(self):
        return np.std(self._deque) if len(self._deque) == self.window else None
    
    def zscore(self):
        if len(self._deque) < self.window:
            return None
        m = np.mean(self._deque)
        s = np.std(self._deque)
        if s == 0:
            return 0
        return (list(self._deque)[-1] - m) / s


class MomentumFactor(MLFactor):
    """动量因子"""
    def __init__(self, name, periods=[5, 10, 20]):
        super().__init__(name)
        self.periods = periods
        self.price_history = deque(maxlen=max(periods)+1)
    
    def update(self, price):
        self.price_history.append(price)
        self.values.append(price)
    
    def momentum(self, period):
        if len(self.price_history) < period + 1:
            return None
        return (list(self.price_history)[-1] - list(self.price_history)[-(period+1)]) / list(self.price_history)[-(period+1)]
    
    def all_momentums(self):
        return {f'mom_{p}': self.momentum(p) for p in self.periods if self.momentum(p) is not None}


class MeanReversionFactor(MLFactor):
    """均值回归因子"""
    def __init__(self, name, window=20):
        super().__init__(name)
        self.window = window
        self.prices = deque(maxlen=window)
    
    def update(self, price):
        self.prices.append(price)
        self.values.append(price)
    
    def zscore(self):
        if len(self.prices) < self.window:
            return None
        arr = np.array(self.prices)
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return 0
        return (arr[-1] - mean) / std
    
    def forecast(self):
        """预测价格回归方向"""
        z = self.zscore()
        if z is None:
            return 0
        return -z  # zscore为正时预计下跌，为负时预计上涨


class VolatilityFactor(MLFactor):
    """波动率因子"""
    def __init__(self, name, window=20):
        super().__init__(name)
        self.window = window
        self.returns = deque(maxlen=window)
        self.last_price = None
    
    def update(self, price):
        if self.last_price is not None:
            ret = (price - self.last_price) / self.last_price
            self.returns.append(ret)
        self.last_price = price
        self.values.append(price)
    
    def volatility(self):
        if len(self.returns) < self.window:
            return None
        return np.std(self.returns) * np.sqrt(252)  # 年化波动率
    
    def relative_volatility(self, market_vol):
        vol = self.volatility()
        if vol is None:
            return None
        return vol / market_vol if market_vol > 0 else None


class VolumeFactor(MLFactor):
    """成交量因子"""
    def __init__(self, name, window=20):
        super().__init__(name)
        self.window = window
        self.volumes = deque(maxlen=window)
        self.prices = deque(maxlen=window)
    
    def update(self, price, volume):
        self.prices.append(price)
        self.volumes.append(volume)
        self.values.append(volume)
    
    def VWAP(self):
        if len(self.volumes) < self.window:
            return None
        return np.sum(np.array(self.prices) * np.array(self.volumes)) / np.sum(self.volumes)
    
    def volume_ratio(self):
        """当前成交量/平均成交量"""
        if len(self.volumes) < self.window:
            return None
        return self.volumes[-1] / np.mean(self.volumes)
    
    def OBV_direction(self):
        """OBV方向"""
        if len(self.prices) < 2:
            return 0
        obv = 0
        for i in range(1, len(self.prices)):
            if self.prices[i] > self.prices[i-1]:
                obv += self.volumes[i]
            elif self.prices[i] < self.prices[i-1]:
                obv -= self.volumes[i]
        return 1 if obv > 0 else -1


class CorrelationFactor(MLFactor):
    """相关性因子"""
    def __init__(self, name, window=20):
        super().__init__(name)
        self.window = window
        self.asset_returns = deque(maxlen=window)
        self.market_returns = deque(maxlen=window)
    
    def update(self, asset_return, market_return):
        self.asset_returns.append(asset_return)
        self.market_returns.append(market_return)
        self.values.append(asset_return)
    
    def correlation(self):
        if len(self.asset_returns) < self.window:
            return None
        a = np.array(self.asset_returns)
        m = np.array(self.market_returns)
        if np.std(a) == 0 or np.std(m) == 0:
            return 0
        return np.corrcoef(a, m)[0, 1]
    
    def beta(self):
        """Beta = Cov(asset, market) / Var(market)"""
        if len(self.asset_returns) < self.window:
            return None
        a = np.array(self.asset_returns)
        m = np.array(self.market_returns)
        if np.var(m) == 0:
            return 1
        return np.cov(a, m)[0, 1] / np.var(m)


class TrendStrengthFactor(MLFactor):
    """趋势强度因子"""
    def __init__(self, name, window=20):
        super().__init__(name)
        self.window = window
        self.prices = deque(maxlen=window)
    
    def update(self, price):
        self.prices.append(price)
        self.values.append(price)
    
    def adx_style(self):
        """类似ADX的趋势强度"""
        if len(self.prices) < self.window + 1:
            return None
        arr = list(self.prices)
        plus_dm = max(arr[-1] - arr[-2], 0)
        minus_dm = max(arr[-2] - arr[-1], 0)
        
        tr = max(arr[-1], arr[-2]) - min(arr[-1], arr[-2])
        
        if tr == 0:
            return 0
        return 100 * abs(plus_dm - minus_dm) / tr
    
    def trend_score(self):
        """趋势评分 - 0到100"""
        if len(self.prices) < self.window:
            return 50
        arr = list(self.prices)
        # 简单线性回归斜率
        x = np.arange(len(arr))
        slope = np.polyfit(x, arr, 1)[0]
        # 归一化
        avg_price = np.mean(arr)
        return 50 + 50 * (slope / avg_price * 100) if avg_price > 0 else 50
