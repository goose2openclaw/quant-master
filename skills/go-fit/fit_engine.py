#!/usr/bin/env python3
"""
go-fit - 趋势模型拟合引擎
对历史K线数据进行多维度模式匹配，拟合最优趋势模型组合
"""
import requests, json, time, random, math, urllib.request, statistics
from datetime import datetime, timedelta
from collections import defaultdict
import hmac, hashlib

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','DOT','LINK','UNI','AVAX','MATIC','ATOM','LTC','ETC']
MEME_COINS = ['PEPE','SHIB','FLOKI','WIF','BABYDOGE','COOKIE','AI','NEIRO','BOME','TURBO','PUMP','BONK']

# ============================================
# Data Utilities
# ============================================
def api_get(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())

def get_klines(symbol, interval='1h', limit=500):
    try:
        return api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    except: return []

def get_fitting_data(coin, interval='1h', limit=500):
    """获取用于拟合的数据"""
    klines = get_klines(f"{coin}USDT", interval, limit)
    data = []
    for k in klines:
        data.append({
            'time': k[0] // 1000,
            'open': float(k[1]),
            'high': float(k[2]),
            'low': float(k[3]),
            'close': float(k[4]),
            'volume': float(k[5])
        })
    return data

# ============================================
# Technical Indicators
# ============================================
def sma(values, period):
    if len(values) < period: return None
    return sum(values[-period:]) / period

def ema(values, period):
    if len(values) < period: return None
    k = 2 / (period + 1)
    ema_val = values[0]
    for v in values[1:]:
        ema_val = v * k + ema_val * (1 - k)
    return ema_val

def atr(data, period=14):
    if len(data) < period + 1: return None
    trs = []
    for i in range(1, len(data)):
        tr = max(
            data[i]['high'] - data[i]['low'],
            abs(data[i]['high'] - data[i-1]['close']),
            abs(data[i]['low'] - data[i-1]['close'])
        )
        trs.append(tr)
    return sum(trs[-period:]) / period

def rsi(closes, period=14):
    if len(closes) < period + 1: return 50
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def stoch(highs, lows, closes, k_period=14, d_period=3):
    if len(closes) < k_period: return 50, 50
    lowest_low = min(lows[-k_period:])
    highest_high = max(highs[-k_period:])
    if highest_high == lowest_low: return 50, 50
    k = 100 * (closes[-1] - lowest_low) / (highest_high - lowest_low)
    k_values = []
    for i in range(k_period-1, len(closes)):
        ll = min(lows[i-k_period+1:i+1])
        hh = max(highs[i-k_period+1:i+1])
        if hh != ll:
            k_values.append(100 * (closes[i] - ll) / (hh - ll))
        else:
            k_values.append(50)
    d = sum(k_values[-d_period:]) / d_period if len(k_values) >= d_period else 50
    return k, d

def macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow: return 0, 0, 0
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    if ema_fast is None or ema_slow is None: return 0, 0, 0
    macd_line = ema_fast - ema_slow
    # Signal line approximation
    macd_line_ema = ema(closes[-signal*2:] if len(closes) >= signal*2 else closes, signal)
    signal_line = macd_line_ema if macd_line_ema else 0
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def bollinger_bands(closes, period=20, std_dev=2):
    if len(closes) < period: return None, None, None
    recent = closes[-period:]
    middle = sum(recent) / period
    variance = sum((c - middle) ** 2 for c in recent) / period
    std = math.sqrt(variance)
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    position = (closes[-1] - lower) / (upper - lower) if upper != lower else 0.5
    return upper, middle, lower, position

def donchian(highs, lows, period=20):
    if len(highs) < period: return None, None, None
    upper = max(highs[-period:])
    lower = min(lows[-period:])
    middle = (upper + lower) / 2
    return upper, middle, lower

def supertrend(data, period=10, multiplier=3):
    if len(data) < period + 1: return 0, 0
    atr_val = atr(data, period)
    if atr_val is None: return 0, 0
    
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    closes = [d['close'] for d in data]
    
    hl2 = (highs[-1] + lows[-1]) / 2
    upper = hl2 + multiplier * atr_val
    lower = hl2 - multiplier * atr_val
    
    # Simple trend detection
    if len(closes) >= 2:
        trend = 1 if closes[-1] > closes[-2] else -1
    else:
        trend = 0
    
    return upper, lower, trend

def parabolic_sar(highs, lows, af=0.02, max_af=0.2):
    if len(highs) < 2: return 0
    # Simplified SAR calculation
    sar = lows[0]
    ep = highs[0]
    af_val = af
    trend = 1
    
    for i in range(1, len(highs)):
        sar = sar + af_val * (ep - sar)
        if trend == 1:
            if lows[i] < sar:
                trend = -1
                sar = ep
                ep = lows[i]
                af_val = af
            else:
                if highs[i] > ep:
                    ep = highs[i]
                    af_val = min(af_val + af, max_af)
        else:
            if highs[i] > sar:
                trend = 1
                sar = ep
                ep = lows[i]
                af_val = af
            else:
                if lows[i] < ep:
                    ep = lows[i]
                    af_val = min(af_val + af, max_af)
    return sar

# ============================================
# Fitting Utilities
# ============================================
def calculate_rsq(y_true, y_pred):
    """计算R²决定系数"""
    n = len(y_true)
    if n < 2: return 0
    mean_y = sum(y_true) / n
    ss_tot = sum((y - mean_y) ** 2 for y in y_true)
    ss_res = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n))
    return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

def calculate_rmse(y_true, y_pred):
    """计算RMSE"""
    n = len(y_true)
    if n < 2: return 0
    mse = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n)) / n
    return math.sqrt(mse)

def calculate_mae(y_true, y_pred):
    """计算MAE"""
    n = len(y_true)
    if n < 2: return 0
    return sum(abs(y_true[i] - y_pred[i]) for i in range(n)) / n

def linear_regression(x, y):
    """简单线性回归"""
    n = len(x)
    if n < 2: return 0, 0
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(x[i] * y[i] for i in range(n))
    sum_x2 = sum(xi ** 2 for xi in x)
    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0: return 0, sum_y / n
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept

# ============================================
# Trend Models
# ============================================
class TrendModel:
    """趋势模型基类"""
    def __init__(self, model_id, name):
        self.model_id = model_id
        self.name = name
        self.fitness = 0.0
        self.weight = 0.0
        self.signal = 'HOLD'
        self.confidence = 0.5
        self.parameters = {}
        self.history = []
        
    def fit(self, data):
        """拟合模型"""
        raise NotImplementedError
        
    def predict(self):
        """预测信号"""
        return self.signal
        
    def get_fitness_metrics(self):
        """获取拟合度指标"""
        return {
            'r_squared': self.fitness,
            'weight': self.weight,
            'confidence': self.confidence
        }

class MACrossModel(TrendModel):
    """MA交叉模型"""
    def __init__(self, fast=20, slow=50):
        super().__init__('trend_ma_cross', f'MA{fast}/{slow}交叉')
        self.fast = fast
        self.slow = slow
        
    def fit(self, closes):
        if len(closes) < self.slow + 10: return
        ma_fast_values = [sma(closes[:i], self.fast) for i in range(self.fast, len(closes))]
        ma_slow_values = [sma(closes[:i], self.slow) for i in range(self.slow, len(closes))]
        
        if len(ma_fast_values) < 2 or len(ma_slow_values) < 2: return
        
        # Calculate alignment (how often does fast MA stay above slow MA)
        aligned = sum(1 for i in range(min(len(ma_fast_values), len(ma_slow_values))) 
                      if ma_fast_values[-(i+1)] > ma_slow_values[-(i+1)])
        alignment_ratio = aligned / min(len(ma_fast_values), len(ma_slow_values))
        
        # Current trend
        current_fast = ma_fast_values[-1]
        current_slow = ma_slow_values[-1]
        prev_fast = ma_fast_values[-2] if len(ma_fast_values) >= 2 else current_fast
        prev_slow = ma_slow_values[-2] if len(ma_slow_values) >= 2 else current_slow
        
        # Signal
        if current_fast > current_slow and prev_fast <= prev_slow:
            self.signal = 'BUY'
            self.confidence = 0.7 + alignment_ratio * 0.2
        elif current_fast < current_slow and prev_fast >= prev_slow:
            self.signal = 'SELL'
            self.confidence = 0.7 + alignment_ratio * 0.2
        elif current_fast > current_slow:
            self.signal = 'BUY'
            self.confidence = 0.5 + alignment_ratio * 0.3
        else:
            self.signal = 'SELL'
            self.confidence = 0.5 + alignment_ratio * 0.3
            
        self.fitness = alignment_ratio
        self.parameters = {'fast': self.fast, 'slow': self.slow, 'alignment': alignment_ratio}

class EMACrossModel(TrendModel):
    """EMA交叉模型"""
    def __init__(self, fast=12, slow=26):
        super().__init__('trend_ema_cross', f'EMA{fast}/{slow}交叉')
        self.fast = fast
        self.slow = slow
        
    def fit(self, closes):
        if len(closes) < self.slow + 10: return
        
        ema_fast_values = [ema(closes[:i+1], self.fast) for i in range(self.fast-1, len(closes))]
        ema_slow_values = [ema(closes[:i+1], self.slow) for i in range(self.slow-1, len(closes))]
        
        if len(ema_fast_values) < 2 or len(ema_slow_values) < 2: return
        
        offset = len(closes) - len(ema_fast_values)
        aligned = 0
        for i in range(min(len(ema_fast_values), len(ema_slow_values))):
            if ema_fast_values[-(i+1)] > ema_slow_values[-(i+1)]:
                aligned += 1
        alignment_ratio = aligned / min(len(ema_fast_values), len(ema_slow_values))
        
        current_fast = ema_fast_values[-1]
        current_slow = ema_slow_values[-1]
        prev_fast = ema_fast_values[-2] if len(ema_fast_values) >= 2 else current_fast
        prev_slow = ema_slow_values[-2] if len(ema_slow_values) >= 2 else current_slow
        
        if current_fast > current_slow and prev_fast <= prev_slow:
            self.signal = 'BUY'
            self.confidence = 0.75
        elif current_fast < current_slow and prev_fast >= prev_slow:
            self.signal = 'SELL'
            self.confidence = 0.75
        elif current_fast > current_slow:
            self.signal = 'BUY'
            self.confidence = 0.55
        else:
            self.signal = 'SELL'
            self.confidence = 0.55
            
        self.fitness = alignment_ratio
        self.parameters = {'fast': self.fast, 'slow': self.slow}

class RSIModel(TrendModel):
    """RSI动量模型"""
    def __init__(self, period=14):
        super().__init__('momentum_rsi', f'RSI({period})')
        self.period = period
        
    def fit(self, closes):
        if len(closes) < self.period + 5: return
        
        rsi_val = rsi(closes, self.period)
        
        if rsi_val < 30:
            self.signal = 'BUY'
            self.confidence = (30 - rsi_val) / 30
        elif rsi_val > 70:
            self.signal = 'SELL'
            self.confidence = (rsi_val - 70) / 30
        else:
            self.signal = 'HOLD'
            self.confidence = 0.5
            
        self.fitness = 0.6 + (1 - abs(rsi_val - 50) / 50) * 0.3
        self.parameters = {'rsi': rsi_val, 'period': self.period}

class BollingerModel(TrendModel):
    """布林带回归模型"""
    def __init__(self, period=20, std_dev=2):
        super().__init__('reversion_bollinger', f'布林带({period},{std_dev})')
        self.period = period
        self.std_dev = std_dev
        
    def fit(self, closes):
        if len(closes) < self.period + 5: return
        
        upper, middle, lower, position = bollinger_bands(closes, self.period, self.std_dev)
        
        if position < 0.2:  # Near lower band
            self.signal = 'BUY'
            self.confidence = 0.6 + (0.2 - position) * 1.5
        elif position > 0.8:  # Near upper band
            self.signal = 'SELL'
            self.confidence = 0.6 + (position - 0.8) * 1.5
        elif position < 0.5:
            self.signal = 'BUY'
            self.confidence = 0.5
        else:
            self.signal = 'SELL'
            self.confidence = 0.5
            
        self.fitness = 0.65
        self.parameters = {'position': position, 'upper': upper, 'lower': lower}

class StochasticModel(TrendModel):
    """随机指标模型"""
    def __init__(self, k_period=14, d_period=3):
        super().__init__('momentum_stoch', f'随机({k_period},{d_period})')
        self.k_period = k_period
        self.d_period = d_period
        
    def fit(self, data):
        if len(data) < self.k_period + 5: return
        
        highs = [d['high'] for d in data]
        lows = [d['low'] for d in data]
        closes = [d['close'] for d in data]
        
        k, d = stoch(highs, lows, closes, self.k_period, self.d_period)
        
        if k < 20:
            self.signal = 'BUY'
            self.confidence = (20 - k) / 20
        elif k > 80:
            self.signal = 'SELL'
            self.confidence = (k - 80) / 20
        elif k > d and k < 50:
            self.signal = 'BUY'
            self.confidence = 0.55
        elif k < d and k > 50:
            self.signal = 'SELL'
            self.confidence = 0.55
        else:
            self.signal = 'HOLD'
            self.confidence = 0.5
            
        self.fitness = 0.6
        self.parameters = {'k': k, 'd': d}

class MACDModel(TrendModel):
    """MACD动量模型"""
    def __init__(self, fast=12, slow=26, signal=9):
        super().__init__('momentum_macd', f'MACD({fast},{slow},{signal})')
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
        
    def fit(self, closes):
        if len(closes) < self.slow + 20: return
        
        macd_line, signal_line, histogram = macd(closes, self.fast, self.slow, self.signal_period)
        
        if histogram > 0 and histogram > -signal_line * 0.1:
            self.signal = 'BUY'
            self.confidence = 0.55 + min(abs(histogram) / signal_line * 0.3, 0.3) if signal_line != 0 else 0.6
        elif histogram < 0 and histogram < signal_line * 0.1:
            self.signal = 'SELL'
            self.confidence = 0.55 + min(abs(histogram) / abs(signal_line) * 0.3, 0.3) if signal_line != 0 else 0.6
        else:
            self.signal = 'HOLD'
            self.confidence = 0.5
            
        self.fitness = 0.6
        self.parameters = {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}

class SupertrendModel(TrendModel):
    """超级趋势模型"""
    def __init__(self, period=10, multiplier=3):
        super().__init__('trend_supertrend', f'超级趋势({period},{multiplier})')
        self.period = period
        self.multiplier = multiplier
        
    def fit(self, data):
        if len(data) < self.period + 5: return
        
        upper, lower, trend = supertrend(data, self.period, self.multiplier)
        
        if trend == 1:
            self.signal = 'BUY'
            self.confidence = 0.65
        else:
            self.signal = 'SELL'
            self.confidence = 0.65
            
        self.fitness = 0.7
        self.parameters = {'upper': upper, 'lower': lower, 'trend': trend}

class DonchianModel(TrendModel):
    """唐奇安突破模型"""
    def __init__(self, period=20):
        super().__init__('breakout_donchian', f'唐奇安({period})')
        self.period = period
        
    def fit(self, data):
        if len(data) < self.period + 5: return
        
        highs = [d['high'] for d in data]
        lows = [d['low'] for d in data]
        closes = [d['close'] for d in data]
        
        upper, middle, lower = donchian(highs, lows, self.period)
        
        # Breakout detection
        if closes[-1] > upper:
            self.signal = 'BUY'
            self.confidence = 0.7
        elif closes[-1] < lower:
            self.signal = 'SELL'
            self.confidence = 0.7
        elif closes[-1] > middle:
            self.signal = 'BUY'
            self.confidence = 0.55
        else:
            self.signal = 'SELL'
            self.confidence = 0.55
            
        self.fitness = 0.65
        self.parameters = {'upper': upper, 'middle': middle, 'lower': lower}

class MomentumBurstModel(TrendModel):
    """动量爆发模型"""
    def __init__(self, lookback=10, threshold=0.05):
        super().__init__('trend_momentum_burst', f'动量爆发({lookback})')
        self.lookback = lookback
        self.threshold = threshold
        
    def fit(self, closes):
        if len(closes) < self.lookback + 2: return
        
        momentum = (closes[-1] - closes[-self.lookback]) / closes[-self.lookback]
        
        if momentum > self.threshold:
            self.signal = 'BUY'
            self.confidence = min(0.5 + momentum * 5, 0.9)
        elif momentum < -self.threshold:
            self.signal = 'SELL'
            self.confidence = min(0.5 + abs(momentum) * 5, 0.9)
        else:
            self.signal = 'HOLD'
            self.confidence = 0.5
            
        self.fitness = 0.6
        self.parameters = {'momentum': momentum}

class GoldenCrossModel(TrendModel):
    """金叉模型"""
    def __init__(self, fast=50, slow=200):
        super().__init__('trend_golden_cross', f'金叉({fast}/{slow})')
        self.fast = fast
        self.slow = slow
        
    def fit(self, closes):
        if len(closes) < self.slow + 10: return
        
        ma_fast = sma(closes[-self.fast:], self.fast)
        ma_slow = sma(closes[-self.slow:], self.slow)
        ma_fast_prev = sma(closes[-self.fast-1:-1], self.fast)
        ma_slow_prev = sma(closes[-self.slow-1:-1], self.slow)
        
        if ma_fast is None or ma_slow is None: return
        
        # Golden cross: fast crosses above slow
        if ma_fast > ma_slow and ma_fast_prev <= ma_slow_prev:
            self.signal = 'BUY'
            self.confidence = 0.8
        # Death cross: fast crosses below slow
        elif ma_fast < ma_slow and ma_fast_prev >= ma_slow_prev:
            self.signal = 'SELL'
            self.confidence = 0.8
        elif ma_fast > ma_slow:
            self.signal = 'BUY'
            self.confidence = 0.6
        else:
            self.signal = 'SELL'
            self.confidence = 0.6
            
        self.fitness = 0.75
        self.parameters = {'ma_fast': ma_fast, 'ma_slow': ma_slow}

class GannAngleModel(TrendModel):
    """江恩角度线模型 (简化版)"""
    def __init__(self):
        super().__init__('mystic_gann', '江恩角度')
        
    def fit(self, closes):
        if len(closes) < 50: return
        
        # Simplified Gann angle calculation
        # 1x1 angle = price change equals time change
        x = list(range(len(closes)))
        slope, intercept = linear_regression(x, closes)
        
        current_price = closes[-1]
        # Gann angles: 1x1, 2x1, 3x1, 4x1, 8x1
        angles = {
            '1x1': slope,
            '2x1': slope * 2,
            '3x1': slope * 3,
            '4x1': slope * 4,
            '8x1': slope * 8
        }
        
        # Price relative to 1x1 line
        expected = intercept + slope * len(closes)
        deviation = (current_price - expected) / expected if expected != 0 else 0
        
        if deviation < -0.05:  # Price below Gann line
            self.signal = 'BUY'
            self.confidence = min(0.5 + abs(deviation) * 10, 0.85)
        elif deviation > 0.05:  # Price above Gann line
            self.signal = 'SELL'
            self.confidence = min(0.5 + deviation * 10, 0.85)
        else:
            self.signal = 'HOLD'
            self.confidence = 0.5
            
        self.fitness = 0.55
        self.parameters = {'angles': angles, 'deviation': deviation, 'slope': slope}

# ============================================
# Model Registry
# ============================================
MODEL_REGISTRY = {
    'trend_ma_cross': lambda: MACrossModel(20, 50),
    'trend_ema_cross': lambda: EMACrossModel(12, 26),
    'trend_golden_cross': lambda: GoldenCrossModel(50, 200),
    'momentum_rsi': lambda: RSIModel(14),
    'reversion_bollinger': lambda: BollingerModel(20, 2),
    'momentum_stoch': lambda: StochasticModel(14, 3),
    'momentum_macd': lambda: MACDModel(12, 26, 9),
    'trend_supertrend': lambda: SupertrendModel(10, 3),
    'breakout_donchian': lambda: DonchianModel(20),
    'trend_momentum_burst': lambda: MomentumBurstModel(10, 0.05),
    'mystic_gann': lambda: GannAngleModel(),
}

# ============================================
# Fitting Engine
# ============================================
class FitEngine:
    """趋势模型拟合引擎"""
    
    def __init__(self, min_fitness=0.5):
        self.min_fitness = min_fitness
        self.models = []
        self.data = None
        self.results = []
        
    def fit(self, coin, interval='1h', period='30d', models=None):
        """拟合模型"""
        # Parse period
        period_map = {'7d': 168, '30d': 720, '90d': 2160, '180d': 4320, '365d': 8760}
        limit = period_map.get(period, 720)
        
        # Get data
        self.data = get_fitting_data(coin, interval, min(limit, 500))
        if not self.data:
            return None
            
        closes = [d['close'] for d in self.data]
        highs = [d['high'] for d in self.data]
        lows = [d['low'] for d in self.data]
        
        # Initialize models
        if models is None:
            models = list(MODEL_REGISTRY.keys())
            
        self.results = []
        
        for model_id in models:
            if model_id in MODEL_REGISTRY:
                model = MODEL_REGISTRY[model_id]()
                
                try:
                    # Fit based on model type
                    if 'stoch' in model_id or 'donchian' in model_id or 'supertrend' in model_id:
                        model.fit(self.data)
                    else:
                        model.fit(closes)
                        
                    if model.fitness >= self.min_fitness or model.fitness == 0:
                        self.results.append(model)
                except Exception as e:
                    print(f"Model {model_id} error: {e}")
        
        # Calculate weights
        self._calculate_weights()
        
        return self
        
    def _calculate_weights(self):
        """计算模型权重"""
        if not self.results:
            return
            
        # Weight by fitness and confidence
        total_score = sum(m.fitness * 0.6 + m.confidence * 0.4 for m in self.results)
        
        for model in self.results:
            score = model.fitness * 0.6 + model.confidence * 0.4
            model.weight = score / total_score if total_score > 0 else 1 / len(self.results)
            
    def combined_signal(self):
        """组合信号"""
        if not self.results:
            return {'signal': 'HOLD', 'confidence': 0, 'weighted_score': 0}
            
        buy_votes = 0
        sell_votes = 0
        hold_votes = 0
        total_weight = 0
        weighted_score = 0
        
        for model in self.results:
            total_weight += model.weight
            if model.signal == 'BUY':
                buy_votes += model.weight
                weighted_score += model.weight * model.confidence
            elif model.signal == 'SELL':
                sell_votes += model.weight
                weighted_score -= model.weight * model.confidence
            else:
                hold_votes += model.weight
                
        buy_ratio = buy_votes / total_weight if total_weight > 0 else 0
        sell_ratio = sell_votes / total_weight if total_weight > 0 else 0
        
        if buy_ratio > 0.5:
            signal = 'BUY'
            confidence = buy_ratio * 0.6 + (1 - sell_ratio) * 0.4
        elif sell_ratio > 0.5:
            signal = 'SELL'
            confidence = sell_ratio * 0.6 + (1 - buy_ratio) * 0.4
        else:
            signal = 'HOLD'
            confidence = 1 - abs(weighted_score)
            
        return {
            'signal': signal,
            'confidence': min(confidence, 1.0),
            'weighted_score': weighted_score,
            'buy_ratio': buy_ratio,
            'sell_ratio': sell_ratio
        }
        
    def get_top_models(self, n=5):
        """获取权重最高的N个模型"""
        sorted_models = sorted(self.results, key=lambda m: m.weight, reverse=True)
        return sorted_models[:n]
        
    def summary(self):
        """获取摘要"""
        combined = self.combined_signal()
        top_models = self.get_top_models(5)
        
        return {
            'total_models': len(self.results),
            'combined': combined,
            'top_models': [
                {
                    'id': m.model_id,
                    'name': m.name,
                    'fitness': m.fitness,
                    'weight': m.weight,
                    'signal': m.signal,
                    'confidence': m.confidence
                }
                for m in top_models
            ]
        }

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("go-fit - 趋势模型拟合引擎")
        print("Usage: python fit_engine.py <coin> [interval] [period]")
        print("Example: python fit_engine.py BTC 1h 30d")
        sys.exit(1)
        
    coin = sys.argv[1].upper()
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    period = sys.argv[3] if len(sys.argv) > 3 else '30d'
    
    print(f"\n🔍 拟合分析: {coin} ({interval}, {period})")
    print("="*60)
    
    engine = FitEngine()
    result = engine.fit(coin, interval, period)
    
    if result:
        summary = result.summary()
        combined = summary['combined']
        
        print(f"\n📊 拟合 {summary['total_models']} 个模型")
        print(f"\n🎯 组合信号: {combined['signal']}")
        print(f"   置信度: {combined['confidence']*100:.1f}%")
        print(f"   加权评分: {combined['weighted_score']:.3f}")
        print(f"   买入权重: {combined['buy_ratio']*100:.1f}%")
        print(f"   卖出权重: {combined['sell_ratio']*100:.1f}%")
        
        print(f"\n🏆 TOP 模型:")
        for m in summary['top_models']:
            print(f"   {m['name']}: {m['signal']} (权重:{m['weight']:.2%}, 拟合度:{m['fitness']:.2%})")
    else:
        print("数据获取失败")
