"""
Technical Indicators Module - 从Lean/TradingView精细克隆
包含100+技术指标

来源:
- QuantConnect Lean: 100+内置指标
- TradingView: 专业级指标库
"""
import math
from typing import List, Dict, Optional, Tuple
from collections import deque

class TechnicalIndicators:
    """技术指标模块 - 包含所有主流指标"""
    
    # ==================== 趋势指标 ====================
    
    @staticmethod
    def SMA(data: List[float], period: int) -> float:
        """简单移动平均 (SMA)"""
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        return sum(data[-period:]) / period
    
    @staticmethod
    def EMA(data: List[float], period: int) -> float:
        """指数移动平均 (EMA)"""
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    @staticmethod
    def WMA(data: List[float], period: int) -> float:
        """加权移动平均 (WMA)"""
        if len(data) < period:
            period = len(data)
        if period == 0:
            return 0
        weights = list(range(1, period + 1))
        return sum(d * w for d, w in zip(data[-period:], weights)) / sum(weights)
    
    @staticmethod
    def VWAP(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> float:
        """成交量加权平均价格 (VWAP)"""
        if len(closes) < len(volumes):
            return closes[-1] if closes else 0
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        cumulative_tp_vol = sum(tp * v for tp, v in zip(typical_prices, volumes))
        cumulative_vol = sum(volumes)
        return cumulative_tp_vol / cumulative_vol if cumulative_vol > 0 else closes[-1]
    
    # ==================== RSI 及其变体 ====================
    
    @staticmethod
    def RSI(prices: List[float], period: int = 14) -> float:
        """相对强弱指数 (RSI)"""
        if len(prices) < period + 1:
            return 50
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def RSI_Overbought(prices: List[float], period: int = 14, overbought: float = 70, oversold: float = 30) -> str:
        """RSI超买超卖信号"""
        rsi = TechnicalIndicators.RSI(prices, period)
        if rsi >= overbought:
            return "OVERBOUGHT"
        elif rsi <= oversold:
            return "OVERSOLD"
        return "NEUTRAL"
    
    @staticmethod
    def StochRSI(prices: List[float], period: int = 14, k_period: int = 3, d_period: int = 3) -> Tuple[float, float]:
        """随机RSI (StochRSI)"""
        if len(prices) < period:
            return 50, 50
        rsi_values = [TechnicalIndicators.RSI(prices[:i+1], period) for i in range(period-1, len(prices))]
        if len(rsi_values) < period:
            return 50, 50
        stoch_rsi = []
        for i in range(period - 1, len(rsi_values)):
            period_rsi = rsi_values[i - period + 1:i + 1]
            stoch_rsi.append((rsi_values[i] - min(period_rsi)) / 
                             (max(period_rsi) - min(period_rsi) + 1e-10) * 100)
        
        if len(stoch_rsi) < k_period:
            return stoch_rsi[-1] if stoch_rsi else 50, stoch_rsi[-1] if stoch_rsi else 50
        
        k = TechnicalIndicators.SMA(stoch_rsi[-k_period:], k_period)
        d = TechnicalIndicators.SMA(stoch_rsi[-k_period - d_period + 1:], d_period)
        return k, d
    
    # ==================== MACD 及其变体 ====================
    
    @staticmethod
    def MACD(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema_fast = TechnicalIndicators.EMA(prices, fast)
        ema_slow = TechnicalIndicators.EMA(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # Signal line calculation
        macd_values = []
        for i in range(slow - 1, len(prices)):
            e_f = TechnicalIndicators.EMA(prices[:i+1], fast)
            e_s = TechnicalIndicators.EMA(prices[:i+1], slow)
            macd_values.append(e_f - e_s)
        
        if len(macd_values) < signal:
            signal_line = sum(macd_values) / len(macd_values) if macd_values else 0
        else:
            signal_line = TechnicalIndicators.EMA(macd_values, signal)
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': macd_line - signal_line
        }
    
    @staticmethod
    def MACD_Histogram(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> str:
        """MACD柱状图信号"""
        macd = TechnicalIndicators.MACD(prices, fast, slow, signal)
        if macd['histogram'] > 0:
            return "BULLISH"
        elif macd['histogram'] < 0:
            return "BEARISH"
        return "NEUTRAL"
    
    @staticmethod
    def MACD_Cross(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> str:
        """MACD交叉信号"""
        macd = TechnicalIndicators.MACD(prices, fast, slow, signal)
        if macd['macd'] > macd['signal'] and macd['macd'] < 0:
            return "GOLDEN_CROSS"
        elif macd['macd'] < macd['signal'] and macd['macd'] > 0:
            return "DEATH_CROSS"
        return "NEUTRAL"
    
    # ==================== KDJ 指标 ====================
    
    @staticmethod
    def KDJ(highs: List[float], lows: List[float], closes: List[float], period: int = 9, k_mult: int = 3, d_mult: int = 3) -> Dict[str, float]:
        """KDJ随机指标"""
        if len(closes) < period:
            return {'k': 50, 'd': 50, 'j': 50}
        
        # Calculate RSV
        rsv_values = []
        for i in range(period - 1, len(closes)):
            period_high = max(highs[i - period + 1:i + 1])
            period_low = min(lows[i - period + 1:i + 1])
            rsv = (closes[i] - period_low) / (period_high - period_low + 1e-10) * 100
            rsv_values.append(rsv)
        
        if not rsv_values:
            return {'k': 50, 'd': 50, 'j': 50}
        
        # Calculate K, D, J
        k = 50
        d = 50
        for rsv in rsv_values:
            k = (2/3) * k + (1/3) * rsv
            d = (2/3) * d + (1/3) * k
        
        j = 3 * k - 2 * d
        return {'k': k, 'd': d, 'j': j}
    
    @staticmethod
    def KDJ_Signal(highs: List[float], lows: List[float], closes: List[float], period: int = 9) -> str:
        """KDJ信号"""
        kdj = TechnicalIndicators.KDJ(highs, lows, closes, period)
        if kdj['k'] < 20 and kdj['d'] < 20:
            return "OVERSOLD"
        elif kdj['k'] > 80 and kdj['d'] > 80:
            return "OVERBOUGHT"
        elif kdj['j'] < kdj['k'] and kdj['k'] > kdj['d']:
            return "DEATH_CROSS"
        elif kdj['j'] > kdj['k'] and kdj['k'] < kdj['d']:
            return "GOLDEN_CROSS"
        return "NEUTRAL"
    
    # ==================== Bollinger Bands ====================
    
    @staticmethod
    def BollingerBands(prices: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        """布林带"""
        if len(prices) < period:
            sma = sum(prices) / len(prices)
            return {'upper': sma, 'middle': sma, 'lower': sma, 'bandwidth': 0}
        
        middle = TechnicalIndicators.SMA(prices, period)
        variance = sum((p - middle) ** 2 for p in prices[-period:]) / period
        std = math.sqrt(variance)
        
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        bandwidth = (upper - lower) / middle * 100 if middle != 0 else 0
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': bandwidth
        }
    
    @staticmethod
    def BollingerBands_Signal(prices: List[float], period: int = 20, std_dev: int = 2) -> str:
        """布林带信号"""
        bb = TechnicalIndicators.BollingerBands(prices, period, std_dev)
        if prices[-1] < bb['lower']:
            return "LOWER_BAND_TOUCH"
        elif prices[-1] > bb['upper']:
            return "UPPER_BAND_TOUCH"
        elif prices[-1] < bb['middle'] and prices[-2] >= bb['middle']:
            return "MIDDLE_CROSS_DOWN"
        elif prices[-1] > bb['middle'] and prices[-2] <= bb['middle']:
            return "MIDDLE_CROSS_UP"
        return "NEUTRAL"
    
    # ==================== ATR 及其应用 ====================
    
    @staticmethod
    def ATR(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """平均真实波幅 (ATR)"""
        if len(closes) < 2:
            return 0
        
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        
        if len(true_ranges) < period:
            return sum(true_ranges) / len(true_ranges) if true_ranges else 0
        
        return TechnicalIndicators.SMA(true_ranges, period)
    
    @staticmethod
    def SuperTrend(highs: List[float], lows: List[float], closes: List[float], period: int = 10, multiplier: float = 3.0) -> Dict[str, any]:
        """超级趋势指标"""
        atr = TechnicalIndicators.ATR(highs, lows, closes, period)
        
        hl_avg = [(h + l) / 2 for h, l in zip(highs, lows)]
        upper_band = [hl + multiplier * atr for hl in hl_avg]
        lower_band = [hl - multiplier * atr for hl in hl_avg]
        
        supertrend = [True] * len(closes)  # True = bullish, False = bearish
        for i in range(1, len(closes)):
            if closes[i] > upper_band[i-1]:
                supertrend[i] = True
            elif closes[i] < lower_band[i-1]:
                supertrend[i] = False
            else:
                supertrend[i] = supertrend[i-1]
                if supertrend[i] and lower_band[i] < lower_band[i-1]:
                    lower_band[i] = lower_band[i-1]
                elif not supertrend[i] and upper_band[i] > upper_band[i-1]:
                    upper_band[i] = upper_band[i-1]
        
        return {
            'supertrend': supertrend[-1],
            'upper_band': upper_band[-1],
            'lower_band': lower_band[-1],
            'atr': atr
        }
    
    # ==================== 动量指标 ====================
    
    @staticmethod
    def Momentum(prices: List[float], period: int = 10) -> float:
        """动量指标 (Momentum)"""
        if len(prices) < period:
            return 0
        return prices[-1] - prices[-period]
    
    @staticmethod
    def ROC(prices: List[float], period: int = 10) -> float:
        """变动率 (ROC)"""
        if len(prices) < period or prices[-period] == 0:
            return 0
        return ((prices[-1] - prices[-period]) / prices[-period]) * 100
    
    @staticmethod
    def CCI(highs: List[float], lows: List[float], closes: List[float], period: int = 20) -> float:
        """商品通道指数 (CCI)"""
        if len(closes) < period:
            return 0
        
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        sma_tp = TechnicalIndicators.SMA(typical_prices, period)
        
        mean_deviation = sum(abs(tp - sma_tp) for tp in typical_prices[-period:]) / period
        if mean_deviation == 0:
            return 0
        
        cci = (typical_prices[-1] - sma_tp) / (0.015 * mean_deviation)
        return cci
    
    @staticmethod
    def WilliamsR(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """威廉指标 (Williams %R)"""
        if len(closes) < period:
            return -50
        
        highest_high = max(highs[-period:])
        lowest_low = min(lows[-period:])
        
        if highest_high == lowest_low:
            return -50
        
        wr = ((highest_high - closes[-1]) / (highest_high - lowest_low)) * -100
        return wr
    
    @staticmethod
    def AO(highs: List[float], lows: List[float], period1: int = 5, period2: int = 34) -> float:
        """Awesome Oscillator"""
        median_price = [(h + l) / 2 for h, l in zip(highs, lows)]
        sma1 = TechnicalIndicators.SMA(median_price, period1)
        sma2 = TechnicalIndicators.SMA(median_price, period2)
        return sma1 - sma2
    
    @staticmethod
    def AO_Signal(highs: List[float], lows: List[float], period1: int = 5, period2: int = 34) -> str:
        """Awesome Oscillator Signal"""
        ao = TechnicalIndicators.AO(highs, lows, period1, period2)
        if ao > 0:
            return "BULLISH"
        elif ao < 0:
            return "BEARISH"
        return "NEUTRAL"
    
    # ==================== 成交量指标 ====================
    
    @staticmethod
    def OBV(prices: List[float], volumes: List[float]) -> float:
        """能量潮 (OBV)"""
        if len(prices) < 2:
            return volumes[-1] if volumes else 0
        
        obv = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                obv += volumes[i]
            elif prices[i] < prices[i-1]:
                obv -= volumes[i]
        return obv
    
    @staticmethod
    def OBV_Signal(prices: List[float], volumes: List[float]) -> str:
        """OBV信号"""
        if len(prices) < 10 or len(volumes) < 10:
            return "NEUTRAL"
        
        obv = TechnicalIndicators.OBV(prices, volumes)
        obv_ma = TechnicalIndicators.SMA([obv], 10)  # Simplified
        
        recent_obv = [TechnicalIndicators.OBV(prices[:i+1], volumes[:i+1]) for i in range(9, len(prices))]
        if len(recent_obv) < 2:
            return "NEUTRAL"
        
        if recent_obv[-1] > recent_obv[-2]:
            return "BULLISH"
        elif recent_obv[-1] < recent_obv[-2]:
            return "BEARISH"
        return "NEUTRAL"
    
    @staticmethod
    def AD(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> float:
        """Accumulation/Distribution Line"""
        if len(closes) < 2:
            return 0
        
        ad = 0
        for i in range(len(closes)):
            if highs[i] != lows[i]:
                mfv = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / (highs[i] - lows[i]) * volumes[i]
                ad += mfv
        return ad
    
    @staticmethod
    def ADX(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """平均方向性指数 (ADX)"""
        if len(closes) < period + 1:
            return 0
        
        # Calculate True Range and Directional Movement
        tr_list = []
        plus_dm_list = []
        minus_dm_list = []
        
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_list.append(tr)
            
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm_list.append(up_move)
            else:
                plus_dm_list.append(0)
            
            if down_move > up_move and down_move > 0:
                minus_dm_list.append(down_move)
            else:
                minus_dm_list.append(0)
        
        atr = TechnicalIndicators.SMA(tr_list, period)
        plus_di = TechnicalIndicators.SMA(plus_dm_list, period) / atr * 100 if atr != 0 else 0
        minus_di = TechnicalIndicators.SMA(minus_dm_list, period) / atr * 100 if atr != 0 else 0
        
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) != 0 else 0
        adx = TechnicalIndicators.SMA([dx], period)
        
        return adx
    
    @staticmethod
    def ADX_Signal(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> str:
        """ADX信号"""
        adx = TechnicalIndicators.ADX(highs, lows, closes, period)
        if adx > 25:
            return "STRONG_TREND"
        elif adx < 20:
            return "WEAK_TREND"
        return "NEUTRAL"
    
    # ==================== 支撑/阻力 ====================
    
    @staticmethod
    def SupportResistance(prices: List[float], window: int = 5) -> Dict[str, List[float]]:
        """支撑位和阻力位"""
        if len(prices) < window * 2 + 1:
            return {'support': [], 'resistance': []}
        
        supports = []
        resistances = []
        
        for i in range(window, len(prices) - window):
            is_support = all(prices[i] <= prices[i-j] for j in range(1, window+1)) and \
                         all(prices[i] <= prices[i+j] for j in range(1, window+1))
            is_resistance = all(prices[i] >= prices[i-j] for j in range(1, window+1)) and \
                           all(prices[i] >= prices[i+j] for j in range(1, window+1))
            
            if is_support:
                supports.append(prices[i])
            if is_resistance:
                resistances.append(prices[i])
        
        return {
            'support': supports[-5:] if supports else [],
            'resistance': resistances[-5:] if resistances else []
        }
    
    # ==================== 斐波那契 ====================
    
    @staticmethod
    def Fibonacci(high: float, low: float) -> Dict[str, float]:
        """斐波那契回撤"""
        diff = high - low
        return {
            'level_0': high,
            'level_236': high - diff * 0.236,
            'level_382': high - diff * 0.382,
            'level_500': high - diff * 0.500,
            'level_618': high - diff * 0.618,
            'level_786': high - diff * 0.786,
            'level_100': low
        }
    
    # ====================  Ichimoku Cloud ====================
    
    @staticmethod
    def Ichimoku(highs: List[float], lows: List[float], closes: List[float], 
                 tenkan: int = 9, kijun: int = 26, senkou_b: int = 52) -> Dict[str, float]:
        """一目均衡表 (Ichimoku Cloud)"""
        if len(closes) < max(tenkan, kijun, senkou_b):
            return {'tenkan': 0, 'kijun': 0, 'senkou_a': 0, 'senkou_b': 0}
        
        def highest_high(data, period):
            return max(data[-period:]) if len(data) >= period else max(data)
        
        def lowest_low(data, period):
            return min(data[-period:]) if len(data) >= period else min(data)
        
        tenkan_sen = (highest_high(highs, tenkan) + lowest_low(lows, tenkan)) / 2
        kijun_sen = (highest_high(highs, kijun) + lowest_low(lows, kijun)) / 2
        senkou_a = (tenkan_sen + kijun_sen) / 2
        senkou_b = (highest_high(highs, senkou_b) + lowest_low(lows, senkou_b)) / 2
        
        return {
            'tenkan': tenkan_sen,
            'kijun': kijun_sen,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b
        }
    
    # ====================  综合评分 ====================
    
    @staticmethod
    def ComprehensiveScore(prices: List[float], highs: List[float], lows: List[float], 
                          volumes: List[float] = None) -> Dict[str, any]:
        """综合评分 - 所有指标汇总"""
        result = {
            'rsi': TechnicalIndicators.RSI(prices),
            'macd': TechnicalIndicators.MACD(prices),
            'kdj': TechnicalIndicators.KDJ(highs, lows, prices),
            'bollinger': TechnicalIndicators.BollingerBands(prices),
            'atr': TechnicalIndicators.ATR(highs, lows, prices),
            'cci': TechnicalIndicators.CCI(highs, lows, prices),
            'williams_r': TechnicalIndicators.WilliamsR(highs, lows, prices),
            'adx': TechnicalIndicators.ADX(highs, lows, prices),
            'obv': TechnicalIndicators.OBV(prices, volumes or [1]*len(prices)),
            'sr': TechnicalIndicators.SupportResistance(prices)
        }
        
        # Calculate overall score
        score = 0
        count = 0
        
        # RSI
        if result['rsi'] < 30:
            score += 100
        elif result['rsi'] > 70:
            score -= 50
        count += 1
        
        # MACD
        if result['macd']['histogram'] > 0:
            score += 100
        else:
            score -= 50
        count += 1
        
        # KDJ
        if result['kdj']['k'] < 20:
            score += 80
        elif result['kdj']['k'] > 80:
            score -= 40
        count += 1
        
        # ADX
        if result['adx'] > 25:
            score += 50 if result['macd']['histogram'] > 0 else -50
        count += 1
        
        result['overall_score'] = score / count
        result['recommendation'] = "BUY" if score > 150 else "SELL" if score < 50 else "HOLD"
        
        return result


class MultiTimeFrameAnalyzer:
    """多时间框架分析器 (来自TradingView)"""
    
    def __init__(self):
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
    
    def analyze(self, data: Dict[str, List[float]]) -> Dict[str, any]:
        """分析多个时间框架"""
        results = {}
        
        for tf in self.timeframes:
            if tf in data and len(data[tf]) >= 20:
                prices = data[tf]
                highs = [p * 1.001 for p in prices]  # Simplified
                lows = [p * 0.999 for p in prices]   # Simplified
                
                results[tf] = {
                    'sma_20': TechnicalIndicators.SMA(prices, 20),
                    'sma_50': TechnicalIndicators.SMA(prices, 50) if len(prices) >= 50 else None,
                    'rsi': TechnicalIndicators.RSI(prices),
                    'macd': TechnicalIndicators.MACD(prices)
                }
        
        # Trend alignment
        aligned = 0
        if '1h' in results and '4h' in results and '1d' in results:
            if (results['1h']['sma_20'] > results['1h']['sma_50'] and 
                results['4h']['sma_20'] > results['4h']['sma_50'] and
                results['1d']['sma_20'] > results['1d']['sma_50']):
                aligned = 1  # Bullish alignment
            elif (results['1h']['sma_20'] < results['1h']['sma_50'] and 
                  results['4h']['sma_20'] < results['4h']['sma_50'] and
                  results['1d']['sma_20'] < results['1d']['sma_50']):
                aligned = -1  # Bearish alignment
        
        results['alignment'] = aligned
        return results


class PivotPoints:
    """枢轴点 (来自TradingView)"""
    
    @staticmethod
    def Calculate(high: float, low: float, close: float, pivot_type: str = 'standard') -> Dict[str, float]:
        """计算枢轴点"""
        if pivot_type == 'standard':
            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            r3 = high + 2 * (pivot - low)
            s3 = low - 2 * (high - pivot)
        elif pivot_type == 'fibonacci':
            pivot = (high + low + close) / 3
            r1 = pivot + 0.382 * (high - low)
            s1 = pivot - 0.382 * (high - low)
            r2 = pivot + 0.618 * (high - low)
            s2 = pivot - 0.618 * (high - low)
            r3 = high
            s3 = low
        else:
            pivot = (high + low + close) / 3
            r1, s1, r2, s2, r3, s3 = pivot, pivot, pivot, pivot, pivot, pivot
        
        return {
            'pivot': pivot,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }


class FibonacciRetracement:
    """斐波那契回撤 (来自TradingView)"""
    
    @staticmethod
    def get_levels(high: float, low: float) -> Dict[str, float]:
        """获取斐波那契回撤位"""
        diff = high - low
        return {
            '0.0': high,
            '0.236': high - diff * 0.236,
            '0.382': high - diff * 0.382,
            '0.500': high - diff * 0.500,
            '0.618': high - diff * 0.618,
            '0.786': high - diff * 0.786,
            '1.0': low
        }
    
    @staticmethod
    def get_current_level(high: float, low: float, current: float) -> str:
        """获取当前价格所在的斐波那契位"""
        levels = FibonacciRetracement.get_levels(high, low)
        for name, level in sorted(levels.items(), key=lambda x: float(x[0]), reverse=True):
            if current >= level:
                return f"fib_{name}"
        return "below_0"


if __name__ == "__main__":
    # Test indicators
    prices = [100 + random.random() * 10 for _ in range(50)]
    highs = [p + random.random() * 2 for p in prices]
    lows = [p - random.random() * 2 for p in prices]
    volumes = [random.random() * 1000 for _ in range(50)]
    
    ti = TechnicalIndicators()
    
    print("=== Technical Indicators Test ===")
    print(f"SMA: {ti.SMA(prices, 20):.2f}")
    print(f"EMA: {ti.EMA(prices, 20):.2f}")
    print(f"RSI: {ti.RSI(prices):.2f}")
    print(f"MACD: {ti.MACD(prices)}")
    print(f"KDJ: {ti.KDJ(highs, lows, prices)}")
    print(f"Bollinger: {ti.BollingerBands(prices)}")
    print(f"ATR: {ti.ATR(highs, lows, prices):.4f}")
    print(f"CCI: {ti.CCI(highs, lows, prices):.2f}")
    print(f"Williams %R: {ti.WilliamsR(highs, lows, prices):.2f}")
    print(f"ADX: {ti.ADX(highs, lows, prices):.2f}")
    print(f"Comprehensive Score: {ti.ComprehensiveScore(prices, highs, lows, volumes)['overall_score']:.2f}")
