"""
技术因子库
"""
import math

class TechnicalFactors:
    """技术指标因子"""
    
    @staticmethod
    def RSI(prices, period=14):
        """RSI"""
        if len(prices) < period + 1:
            return 50
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        return 100 - (100 / (1 + avg_gain / avg_loss))
    
    @staticmethod
    def MACD(prices, fast=12, slow=26, signal=9):
        """MACD"""
        ema_fast = TechnicalFactors.EMA(prices, fast)
        ema_slow = TechnicalFactors.EMA(prices, slow)
        macd = ema_fast - ema_slow
        signal_line = macd * 0.9  # simplified
        return {'macd': macd, 'signal': signal_line, 'histogram': macd - signal_line}
    
    @staticmethod
    def BollingerBands(prices, period=20, std_dev=2):
        """布林带"""
        window = prices[-period:]
        middle = sum(window) / period
        variance = sum((p - middle) ** 2 for p in window) / period
        std = math.sqrt(variance)
        return {
            'upper': middle + std * std_dev,
            'middle': middle,
            'lower': middle - std * std_dev,
            'bandwidth': (middle + std * std_dev) - (middle - std * std_dev)
        }
    
    @staticmethod
    def EMA(prices, period):
        """EMA"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    @staticmethod
    def ATR(high, low, close, period=14):
        """ATR"""
        if len(high) < 2:
            return 0
        trs = [max(high[i] - low[i], 
                   abs(high[i] - close[i-1]),
                   abs(low[i] - close[i-1])) for i in range(1, len(high))]
        return sum(trs[-period:]) / period if len(trs) >= period else sum(trs) / len(trs)
    
    @staticmethod
    def ADX(high, low, close, period=14):
        """ADX趋势强度"""
        if len(high) < period + 1:
            return 0
        plus_dm = [max(high[i] - high[i-1], 0) if high[i] - high[i-1] > low[i-1] - low[i] else 0 for i in range(1, len(high))]
        minus_dm = [max(low[i-1] - low[i], 0) if low[i-1] - low[i] > high[i] - high[i-1] else 0 for i in range(1, len(high))]
        atr = TechnicalFactors.ATR(high, low, close, period)
        if atr == 0:
            return 0
        plus_di = sum(plus_dm[-period:]) / period / atr * 100
        minus_di = sum(minus_dm[-period:]) / period / atr * 100
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        return dx  # Simplified ADX
    
    @staticmethod
    def Stochastic(high, low, close, period=14):
        """随机指标"""
        if len(high) < period:
            return 50, 50
        window = list(zip(high[-period:], low[-period:], close[-period:]))
        highest = max(h[0] for h in window)
        lowest = min(h[1] for h in window)
        current = close[-1]
        if highest == lowest:
            return 50, 50
        k = (current - lowest) / (highest - lowest) * 100
        d = k * 0.9 + 50 * 0.1  # smoothed
        return k, d
    
    @staticmethod
    def OBV(close, volume):
        """OBV能量潮"""
        if len(close) < 2:
            return volume[0] if volume else 0
        obv = volume[0]
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv += volume[i]
            elif close[i] < close[i-1]:
                obv -= volume[i]
        return obv
    
    @staticmethod
    def VWAP(close, volume):
        """VWAP成交量加权"""
        if not volume or sum(volume) == 0:
            return close[-1] if close else 0
        return sum(c * v for c, v in zip(close, volume)) / sum(volume)
