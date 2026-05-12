#!/usr/bin/env python3
"""
go-noise - 高级噪音分析与降噪引擎
噪音矩阵构建、噪音特征提取、加权噪音模型组合
"""
import math, json, time, urllib.request, statistics
from datetime import datetime, timedelta
from collections import defaultdict
import hmac, hashlib

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

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

def get_price_data(coin, interval='1h', limit=500):
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
# Statistical Functions
# ============================================
def mean(values):
    return sum(values) / len(values) if values else 0

def std(values):
    if len(values) < 2: return 0
    m = mean(values)
    variance = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)

def skewness(values):
    if len(values) < 3: return 0
    m = mean(values)
    s = std(values)
    if s == 0: return 0
    return sum((v - m) ** 3 for v in values) / (len(values) * s ** 3)

def kurtosis(values):
    if len(values) < 4: return 0
    m = mean(values)
    s = std(values)
    if s == 0: return 0
    return sum((v - m) ** 4 for v in values) / (len(values) * s ** 4) - 3

def entropy(values, bins=10):
    """计算香农熵"""
    if not values: return 0
    hist = defaultdict(int)
    v_min, v_max = min(values), max(values)
    if v_min == v_max: return 0
    for v in values:
        bin_idx = int((v - v_min) / (v_max - v_min) * bins)
        bin_idx = min(bin_idx, bins - 1)
        hist[bin_idx] += 1
    total = len(values)
    ent = 0
    for count in hist.values():
        p = count / total
        if p > 0:
            ent -= p * math.log2(p)
    return ent

def autocorr(values, lag=1):
    """自相关"""
    if len(values) < lag + 2: return 0
    n = len(values)
    mean_val = mean(values)
    c0 = sum((v - mean_val) ** 2 for v in values) / n
    if c0 == 0: return 0
    clag = sum((values[i] - mean_val) * (values[i-lag] - mean_val) for i in range(lag, n)) / n
    return clag / c0

# ============================================
# Time Series Functions
# ============================================
def sma(values, period):
    if len(values) < period: return None
    return mean(values[-period:])

def ema(values, period):
    if len(values) < period: return None
    k = 2 / (period + 1)
    ema_val = mean(values[:period])
    for v in values[period:]:
        ema_val = v * k + ema_val * (1 - k)
    return ema_val

def linear_regression(x, y):
    n = len(x)
    if n < 2: return 0, mean(y)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(x[i] * y[i] for i in range(n))
    sum_x2 = sum(xi ** 2 for xi in x)
    denom = n * sum_x2 - sum_x ** 2
    if denom == 0: return 0, sum_y / n
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept

def decompose(closes, period=24):
    """简单季节性分解"""
    if len(closes) < period * 2: return closes, [0] * len(closes), [0] * len(closes)
    
    trend = []
    for i in range(len(closes)):
        start = max(0, i - period // 2)
        end = min(len(closes), i + period // 2 + 1)
        trend.append(mean(closes[start:end]))
    
    detrended = [closes[i] - trend[i] for i in range(len(closes))]
    
    seasonal = [0] * len(closes)
    for i in range(period):
        vals = [detrended[j] for j in range(i, len(closes), period) if j < len(detrended)]
        if vals:
            seasonal[i::period] = [mean(vals)] * (len(closes) // period + 1)
    seasonal = seasonal[:len(closes)]
    
    residual = [detrended[i] - seasonal[i] for i in range(len(closes))]
    
    return trend, seasonal, residual

# ============================================
# FFT Functions
# ============================================
def fft_denoise(values, cutoff_ratio=0.1):
    """简单的FFT降噪"""
    n = len(values)
    if n < 10: return values
    
    # Compute FFT
    fft_vals = []
    for k in range(n):
        real = sum(values[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        imag = -sum(values[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        fft_vals.append(complex(real, imag))
    
    # Apply low-pass filter
    cutoff = int(n * cutoff_ratio)
    filtered = [0] * n
    for k in range(n):
        if k < cutoff or k > n - cutoff:
            filtered[k] = fft_vals[k]
    
    # Inverse FFT (simplified)
    result = []
    for i in range(n):
        real = sum(filtered[k].real * math.cos(2 * math.pi * k * i / n) for k in range(n)) / n
        result.append(real)
    
    return result

# ============================================
# Noise Models
# ============================================
class NoiseModel:
    """噪音模型基类"""
    def __init__(self, model_id, name):
        self.model_id = model_id
        self.name = name
        self.fit_quality = 0.0
        self.stability = 0.0
        self.weight = 0.0
        self.parameters = {}
        
    def fit(self, noise_series):
        """拟合噪音模型"""
        raise NotImplementedError
        
    def get_noise(self, price_series, signal):
        """获取噪音成分"""
        raise NotImplementedError

class WhiteNoiseModel(NoiseModel):
    """白噪音模型"""
    def __init__(self):
        super().__init__('noise_white', '白噪音')
        
    def fit(self, noise_series):
        if len(noise_series) < 10:
            self.fit_quality = 0
            return
        # 白噪音检验: 残差应该无自相关
        ac1 = autocorr(noise_series, 1)
        self.fit_quality = 1 - abs(ac1)
        self.stability = 1 - std(noise_series) / (abs(mean(noise_series)) + 1e-10)
        self.parameters = {'mean': mean(noise_series), 'std': std(noise_series)}
        
    def get_noise(self, price_series, signal):
        return signal * 0.05  # 简单白噪音估计

class GaussianNoiseModel(NoiseModel):
    """高斯噪音模型"""
    def __init__(self):
        super().__init__('noise_gauss', '高斯噪音')
        
    def fit(self, noise_series):
        if len(noise_series) < 10: return
        self.fit_quality = max(0, 1 - abs(skewness(noise_series)))
        self.stability = 1 - abs(kurtosis(noise_series) / 10)
        self.parameters = {'mean': mean(noise_series), 'std': std(noise_series), 'skew': skewness(noise_series), 'kurt': kurtosis(noise_series)}
        
    def get_noise(self, price_series, signal):
        return signal * 0.03

class LaplacianNoiseModel(NoiseModel):
    """拉普拉斯噪音模型"""
    def __init__(self):
        super().__init__('noise_laplace', '拉普拉斯噪音')
        
    def fit(self, noise_series):
        if len(noise_series) < 10: return
        self.fit_quality = 1 / (1 + abs(skewness(noise_series)))
        self.stability = 0.7
        self.parameters = {'b': std(noise_series) * 0.5}
        
    def get_noise(self, price_series, signal):
        return signal * 0.04

class ARCHNoiseModel(NoiseModel):
    """ARCH/GARCH噪音模型 (简化版)"""
    def __init__(self):
        super().__init__('noise_garch', 'GARCH波动噪音')
        
    def fit(self, noise_series):
        if len(noise_series) < 20: return
        returns = [noise_series[i+1] - noise_series[i] for i in range(len(noise_series)-1)]
        self.fit_quality = 1 / (1 + abs(std(returns) - std(noise_series)))
        self.stability = abs(autocorr([abs(r) for r in returns], 1))
        self.parameters = {'vol_clustering': autocorr([abs(r) for r in returns], 1)}
        
    def get_noise(self, price_series, signal):
        return signal * 0.06

class TrendLagNoiseModel(NoiseModel):
    """均线滞后噪音"""
    def __init__(self, ma_period=20):
        super().__init__('noise_ma_lag', f'MA{ma_period}滞后噪音')
        self.ma_period = ma_period
        
    def fit(self, closes):
        if len(closes) < self.ma_period + 5: return
        ma_values = [sma(closes[:i+1], self.ma_period) for i in range(self.ma_period-1, len(closes))]
        lag = (len(closes) - len(ma_values))
        noise = [closes[lag + i] - ma_values[i] for i in range(len(ma_values))]
        self.fit_quality = 1 - min(abs(mean(noise)) / (std(noise) + 1e-10), 1)
        self.stability = 1 - abs(autocorr(noise, 1))
        self.parameters = {'lag': lag, 'ma_period': self.ma_period, 'noise_std': std(noise)}
        
    def get_noise(self, price_series, signal):
        return signal * 0.05

class IntradayNoiseModel(NoiseModel):
    """日内噪音模型"""
    def __init__(self):
        super().__init__('noise_intraday', '日内噪音')
        
    def fit(self, noise_series):
        if len(noise_series) < 50: return
        # 检测日内模式噪音
        daily = [noise_series[i] for i in range(0, min(len(noise_series), 100), 24)]
        self.fit_quality = 1 - abs(skewness(daily))
        self.stability = 0.6
        self.parameters = {'intraday_pattern': std(daily) / (abs(mean(daily)) + 1e-10)}
        
    def get_noise(self, price_series, signal):
        return signal * 0.04

class VolatilityClusterNoiseModel(NoiseModel):
    """波动聚集噪音"""
    def __init__(self):
        super().__init__('noise_vol_cluster', '波动聚集噪音')
        
    def fit(self, noise_series):
        if len(noise_series) < 20: return
        abs_noise = [abs(n) for n in noise_series]
        ac1 = autocorr(abs_noise, 1)
        self.fit_quality = max(0, min(1, ac1 + 0.5))
        self.stability = abs(ac1)
        self.parameters = {'clustering': ac1}
        
    def get_noise(self, price_series, signal):
        return signal * 0.07

class WeekendNoiseModel(NoiseModel):
    """周末噪音模型"""
    def __init__(self):
        super().__init__('noise_weekend', '周末噪音')
        
    def fit(self, noise_series):
        if len(noise_series) < 50: return
        # 周末vs工作日噪音差异
        weekend = [noise_series[i] for i in range(5, min(len(noise_series), 168), 7)]
        weekday = [noise_series[i] for i in range(min(len(noise_series), 168)) if i % 7 not in [5, 6]]
        if weekday and weekend:
            ratio = std(weekend) / (std(weekday) + 1e-10)
            self.fit_quality = min(1, ratio)
            self.stability = 0.7
            self.parameters = {'weekend_std': std(weekend), 'weekday_std': std(weekday), 'ratio': ratio}
        
    def get_noise(self, price_series, signal):
        return signal * 0.03

class FalseBreakNoiseModel(NoiseModel):
    """假突破噪音"""
    def __init__(self):
        super().__init__('noise_false_break', '假突破噪音')
        
    def fit(self, highs, lows, closes):
        if len(closes) < 30: return
        # 检测假突破模式
        false_breaks = 0
        for i in range(1, len(closes)-1):
            # 假突破上破
            if highs[i] > highs[i-1] and closes[i] < closes[i-1] and closes[i] < highs[i-1]:
                false_breaks += 1
            # 假突破下破
            if lows[i] < lows[i-1] and closes[i] > closes[i-1] and closes[i] > lows[i-1]:
                false_breaks += 1
        self.fit_quality = false_breaks / (len(closes) - 2)
        self.stability = 0.5
        self.parameters = {'false_break_ratio': self.fit_quality}
        
    def get_noise(self, price_series, signal):
        return signal * self.fit_quality * 0.5

class BidAskBounceNoiseModel(NoiseModel):
    """买卖价差噪音"""
    def __init__(self, spread=0.001):
        super().__init__('noise_bid_ask', '买卖价差噪音')
        self.spread = spread
        
    def fit(self, highs, lows, closes):
        if len(closes) < 20: return
        bounces = sum(1 for i in range(1, len(closes)) 
                     if (closes[i] - closes[i-1]) * (closes[i-1] - closes[i-2]) < 0)
        bounce_ratio = bounces / (len(closes) - 2)
        self.fit_quality = bounce_ratio
        self.stability = 0.6
        self.parameters = {'spread': self.spread, 'bounce_ratio': bounce_ratio}
        
    def get_noise(self, price_series, signal):
        return signal * 0.02 + self.spread * price_series[-1] * 0.5

class FFTDenoiseModel(NoiseModel):
    """FFT降噪模型"""
    def __init__(self, cutoff=0.1):
        super().__init__('noise_fft', 'FFT降噪')
        self.cutoff = cutoff
        
    def fit(self, noise_series):
        if len(noise_series) < 20: return
        fft_noise = fft_denoise(noise_series, self.cutoff)
        original_var = std(noise_series) ** 2
        denoised_var = std([noise_series[i] - fft_noise[i] for i in range(len(noise_series))]) ** 2
        self.fit_quality = 1 - (denoised_var / (original_var + 1e-10))
        self.stability = 0.8
        self.parameters = {'cutoff': self.cutoff, 'noise_ratio': self.fit_quality}
        
    def get_noise(self, price_series, signal):
        return signal * 0.1

class KalmanDenoiseModel(NoiseModel):
    """卡尔曼滤波降噪"""
    def __init__(self, q=0.001, r=0.1):
        super().__init__('noise_kalman', '卡尔曼滤波')
        self.q = q  # 过程噪声
        self.r = r  # 测量噪声
        
    def fit(self, closes):
        if len(closes) < 10: return
        # 简化卡尔曼滤波
        x = closes[0]
        p = 1
        filtered = [x]
        for z in closes[1:]:
            # 预测
            x_pred = x
            p_pred = p + self.q
            # 更新
            k = p_pred / (p_pred + self.r)
            x = x_pred + k * (z - x_pred)
            p = (1 - k) * p_pred
            filtered.append(x)
        
        noise = [closes[i] - filtered[i] for i in range(len(closes))]
        self.fit_quality = 1 - std(noise) / (std(closes) + 1e-10)
        self.stability = 0.75
        self.parameters = {'q': self.q, 'r': self.r, 'noise_std': std(noise)}
        
    def get_noise(self, price_series, signal):
        return signal * 0.05

class MedianFilterModel(NoiseModel):
    """中值滤波噪音"""
    def __init__(self, window=5):
        super().__init__('noise_median', '中值滤波')
        self.window = window
        
    def fit(self, closes):
        if len(closes) < self.window: return
        # 简化中值滤波
        filtered = []
        for i in range(len(closes)):
            start = max(0, i - self.window // 2)
            end = min(len(closes), i + self.window // 2 + 1)
            window_vals = sorted(closes[start:end])
            filtered.append(window_vals[len(window_vals) // 2])
        
        noise = [closes[i] - filtered[i] for i in range(len(closes))]
        self.fit_quality = 1 - abs(mean(noise)) / (std(noise) + 1e-10)
        self.stability = 0.7
        self.parameters = {'window': self.window}
        
    def get_noise(self, price_series, signal):
        return signal * 0.03

# ============================================
# Noise Engine
# ============================================
class NoiseEngine:
    """噪音分析引擎"""
    
    def __init__(self):
        self.models = []
        self.noise_matrix = None
        self.features = {}
        self.data = None
        
    def analyze(self, coin, interval='1h', period='30d'):
        """分析噪音"""
        period_map = {'7d': 168, '30d': 720, '90d': 2160, '180d': 4320}
        limit = period_map.get(period, 720)
        
        self.data = get_price_data(coin, interval, min(limit, 500))
        if not self.data:
            return None
            
        closes = [d['close'] for d in self.data]
        highs = [d['high'] for d in self.data]
        lows = [d['low'] for d in self.data]
        volumes = [d['volume'] for d in self.data]
        
        # 构建噪音矩阵: noise = price - trend
        trend = []
        for i in range(len(closes)):
            start = max(0, i - 20)
            end = min(len(closes), i + 21)
            trend.append(mean(closes[start:end]))
        
        self.noise_matrix = [closes[i] - trend[i] for i in range(len(closes))]
        
        # 拟合噪音模型
        self._fit_models(closes, highs, lows, volumes)
        
        # 提取噪音特征
        self._extract_features()
        
        return self
        
    def _fit_models(self, closes, highs, lows, volumes):
        """拟合噪音模型"""
        self.models = []
        
        models_to_fit = [
            WhiteNoiseModel(),
            GaussianNoiseModel(),
            LaplacianNoiseModel(),
            ARCHNoiseModel(),
            TrendLagNoiseModel(20),
            IntradayNoiseModel(),
            VolatilityClusterNoiseModel(),
            WeekendNoiseModel(),
            FalseBreakNoiseModel(),
            BidAskBounceNoiseModel(),
            FFTDenoiseModel(),
            KalmanDenoiseModel(),
            MedianFilterModel(),
        ]
        
        for model in models_to_fit:
            try:
                if 'highs' in str(type(model).fit.__code__.co_varnames):
                    model.fit(highs, lows, closes)
                elif 'closes' in str(type(model).fit.__code__.co_varnames):
                    model.fit(closes)
                elif hasattr(self, 'noise_matrix'):
                    model.fit(self.noise_matrix)
            except:
                pass
            self.models.append(model)
        
        # 计算权重
        self._calculate_weights()
        
    def _calculate_weights(self):
        """计算噪音模型权重"""
        total = sum(m.fit_quality * 0.5 + m.stability * 0.5 for m in self.models)
        if total == 0: return
        for m in self.models:
            m.weight = (m.fit_quality * 0.5 + m.stability * 0.5) / total
            
    def _extract_features(self):
        """提取噪音特征"""
        if self.noise_matrix is None: return
        
        nm = self.noise_matrix
        self.features = {
            'noise_level': std(nm),
            'noise_mean': mean(nm),
            'noise_skewness': skewness(nm),
            'noise_kurtosis': kurtosis(nm),
            'noise_entropy': entropy(nm),
            'noise_persistence': autocorr(nm, 1),
            'noise_volatility': std([nm[i+1]-nm[i] for i in range(len(nm)-1)]) if len(nm) > 1 else 0,
            'noise_burst_freq': sum(1 for i in range(1, len(nm)) if abs(nm[i]) > 2 * std(nm)) / len(nm),
        }
        
    def get_noise_features(self):
        """获取噪音特征"""
        return self.features
        
    def get_noise_matrix(self):
        """获取噪音矩阵"""
        return self.noise_matrix
        
    def get_top_noise_models(self, n=5):
        """获取权重最高的噪音模型"""
        sorted_models = sorted(self.models, key=lambda m: m.weight, reverse=True)
        return sorted_models[:n]
        
    def denoise(self, signal, confidence=0.8):
        """降噪处理信号"""
        if not self.models or self.noise_matrix is None:
            return {'signal': signal, 'confidence': confidence, 'noise_reduction': 0}
            
        # 计算加权噪音
        total_noise = 0
        for model in self.models:
            total_noise += model.weight * model.fit_quality
            
        # 噪音水平
        noise_level = self.features.get('noise_level', 0)
        
        # 降噪因子
        if noise_level < 0.01:
            noise_factor = 0.1
        elif noise_level < 0.05:
            noise_factor = 0.3
        elif noise_level < 0.1:
            noise_factor = 0.5
        else:
            noise_factor = 0.7
            
        # 调整后的信号
        adjusted_signal = signal * (1 - total_noise * noise_factor * 0.3)
        adjusted_confidence = confidence * (1 - total_noise * 0.5)
        
        return {
            'signal': adjusted_signal,
            'confidence': max(0.1, min(1.0, adjusted_confidence)),
            'noise_reduction': total_noise * noise_factor,
            'noise_level': noise_level,
            'noise_models_used': len([m for m in self.models if m.weight > 0.05])
        }
        
    def summary(self):
        """获取摘要"""
        return {
            'features': self.features,
            'top_models': [
                {
                    'id': m.model_id,
                    'name': m.name,
                    'weight': m.weight,
                    'fit_quality': m.fit_quality,
                    'stability': m.stability
                }
                for m in self.get_top_noise_models(5)
            ]
        }

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-noise - 噪音分析与降噪引擎")
        print("Usage: python noise_engine.py <coin> [interval] [period]")
        sys.exit(1)
        
    coin = sys.argv[1].upper()
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    period = sys.argv[3] if len(sys.argv) > 3 else '30d'
    
    print(f"\n🔊 噪音分析: {coin} ({interval}, {period})")
    print("="*60)
    
    engine = NoiseEngine()
    result = engine.analyze(coin, interval, period)
    
    if result:
        summary = result.summary()
        features = summary['features']
        
        print(f"\n📊 噪音特征:")
        print(f"   噪音水平: {features['noise_level']:.6f}")
        print(f"   噪音均值: {features['noise_mean']:.6f}")
        print(f"   噪音偏度: {features['noise_skewness']:.4f}")
        print(f"   噪音峰度: {features['noise_kurtosis']:.4f}")
        print(f"   噪音熵: {features['noise_entropy']:.4f}")
        print(f"   噪音持续性: {features['noise_persistence']:.4f}")
        print(f"   噪音波动率: {features['noise_volatility']:.6f}")
        print(f"   爆发频率: {features['noise_burst_freq']:.2%}")
        
        print(f"\n🏆 TOP 噪音模型:")
        for m in summary['top_models']:
            print(f"   {m['name']}: 权重={m['weight']:.2%}, 拟合度={m['fit_quality']:.2%}")
        
        # 测试降噪
        test_signal = 65
        denoised = result.denoise(test_signal, 0.8)
        print(f"\n🔧 降噪测试:")
        print(f"   原始信号: {test_signal}")
        print(f"   降噪信号: {denoised['signal']:.2f}")
        print(f"   降噪置信度: {denoised['confidence']:.2%}")
        print(f"   噪音降低: {denoised['noise_reduction']:.2%}")
    else:
        print("数据获取失败")
