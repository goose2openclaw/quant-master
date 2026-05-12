#!/usr/bin/env python3
"""
go-ensemble - 加权组合矫正引擎
通过反向预测和仿真迭代，持续优化加权系数矩阵
"""
import math, json, time, random, urllib.request, copy
from datetime import datetime, timedelta
from collections import defaultdict
import hmac, hashlib

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 默认因子权重
DEFAULT_FACTOR_WEIGHTS = {
    'technical': 0.15,
    'quantum': 0.10,
    'thermo': 0.10,
    'human': 0.10,
    'contrarian': 0.15,
    'institutional': 0.15,
    'reverse': 0.10,
    'meta': 0.05,
    'volume': 0.05,
    'momentum': 0.05,
}

# 默认策略权重
DEFAULT_STRATEGY_WEIGHTS = {
    'mirofish': 0.20,
    'oracle': 0.25,
    'momentum': 0.15,
    'reversion': 0.15,
    'breakout': 0.10,
    'quantum': 0.05,
    'thermo': 0.05,
    'contrarian': 0.05,
}

# 默认时间框架权重
DEFAULT_TIMEFRAME_WEIGHTS = {
    '1m': 0.05,
    '5m': 0.10,
    '15m': 0.15,
    '1h': 0.30,
    '4h': 0.25,
    '1d': 0.15,
}

# 优化参数
OPTIMIZATION_PARAMS = {
    'learning_rate': 0.01,
    'momentum': 0.9,
    'decay': 0.95,
    'iterations': 100,
    'population_size': 50,
    'mutation_rate': 0.1,
    'convergence_threshold': 0.001,
}

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
# Statistical Utilities
# ============================================
def mean(values):
    return sum(values) / len(values) if values else 0

def std(values):
    if len(values) < 2: return 0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))

def normalize(values):
    if not values: return []
    s = sum(values)
    if s == 0: return [1/len(values)] * len(values) if values else []
    return [v / s for v in values]

# ============================================
# Component Base
# ============================================
class Component:
    """组件基类"""
    def __init__(self, name, weight=0.1):
        self.name = name
        self.weight = weight
        self.predictions = []
        self.accuracy = 0.5
        self.last_error = 0
        
    def predict(self, data):
        """子类实现"""
        raise NotImplementedError
        
    def update(self, new_data, actual):
        """更新组件"""
        pass

# ============================================
# Indicator Components
# ============================================
class TechnicalIndicator(Component):
    """技术指标组件"""
    
    def __init__(self, name, weight=0.1):
        super().__init__(name, weight)
        
    def predict(self, data):
        """技术指标预测"""
        if len(data) < 20:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        closes = [d['close'] for d in data]
        
        if self.name == 'rsi':
            return self._rsi_signal(closes)
        elif self.name == 'macd':
            return self._macd_signal(closes)
        elif self.name == 'bollinger':
            return self._bollinger_signal(closes)
        elif self.name == 'ma_cross':
            return self._ma_cross_signal(closes)
        elif self.name == 'atr':
            return self._atr_signal(data)
        else:
            return {'signal': 'neutral', 'confidence': 0.5}
            
    def _rsi_signal(self, closes, period=14):
        if len(closes) < period + 1:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return {'signal': 'strong_buy', 'confidence': 0.9}
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        if rsi < 30:
            return {'signal': 'buy', 'confidence': (30 - rsi) / 30}
        elif rsi > 70:
            return {'signal': 'sell', 'confidence': (rsi - 70) / 30}
        else:
            return {'signal': 'neutral', 'confidence': 0.5}
            
    def _macd_signal(self, closes, fast=12, slow=26, signal=9):
        if len(closes) < slow + signal:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        # 简化MACD
        ema_fast = mean(closes[-fast:])
        ema_slow = mean(closes[-slow:])
        
        macd = ema_fast - ema_slow
        signal_line = macd * 0.9  # 简化
        
        if macd > signal_line:
            return {'signal': 'buy', 'confidence': min(0.9, abs(macd - signal_line) / macd * 10 + 0.5)}
        else:
            return {'signal': 'sell', 'confidence': min(0.9, abs(macd - signal_line) / abs(macd) * 10 + 0.5)}
            
    def _bollinger_signal(self, closes, period=20, std_dev=2):
        if len(closes) < period:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        recent = closes[-period:]
        mid = mean(recent)
        s = std(recent)
        
        upper = mid + std_dev * s
        lower = mid - std_dev * s
        
        current = closes[-1]
        
        if current < lower:
            return {'signal': 'buy', 'confidence': 0.7}
        elif current > upper:
            return {'signal': 'sell', 'confidence': 0.7}
        else:
            return {'signal': 'neutral', 'confidence': 0.5}
            
    def _ma_cross_signal(self, closes, short=5, long=20):
        if len(closes) < long + 1:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        ma_short = mean(closes[-short:])
        ma_long = mean(closes[-long:])
        
        ma_short_prev = mean(closes[-short-1:-1])
        ma_long_prev = mean(closes[-long-1:-1])
        
        # 金叉/死叉
        if ma_short > ma_long and ma_short_prev <= ma_long_prev:
            return {'signal': 'buy', 'confidence': 0.7}
        elif ma_short < ma_long and ma_short_prev >= ma_long_prev:
            return {'signal': 'sell', 'confidence': 0.7}
        else:
            return {'signal': 'neutral', 'confidence': 0.5}
            
    def _atr_signal(self, data, period=14):
        if len(data) < period + 1:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        trs = []
        for i in range(1, min(len(data), period + 1)):
            tr = max(
                data[i]['high'] - data[i]['low'],
                abs(data[i]['high'] - data[i-1]['close']),
                abs(data[i]['low'] - data[i-1]['close'])
            )
            trs.append(tr)
            
        atr = mean(trs)
        current_range = data[-1]['high'] - data[-1]['low']
        
        if current_range > atr * 1.5:
            return {'signal': 'volatility', 'confidence': 0.6}
        else:
            return {'signal': 'neutral', 'confidence': 0.5}

# ============================================
# Signal Components
# ============================================
class SignalComponent(Component):
    """信号组件 (基于简单规则)"""
    
    def __init__(self, name, weight=0.1):
        super().__init__(name, weight)
        
    def predict(self, data):
        """信号预测"""
        if len(data) < 20:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        closes = [d['close'] for d in data]
        volumes = [d['volume'] for d in data]
        
        if self.name == 'momentum':
            return self._momentum_signal(closes)
        elif self.name == 'volume':
            return self._volume_signal(closes, volumes)
        elif self.name == 'trend':
            return self._trend_signal(closes)
        elif self.name == 'reversion':
            return self._reversion_signal(closes)
        else:
            return {'signal': 'neutral', 'confidence': 0.5}
            
    def _momentum_signal(self, closes):
        if len(closes) < 20:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        recent_return = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] > 0 else 0
        
        if recent_return > 0.05:
            return {'signal': 'buy', 'confidence': min(0.9, recent_return * 10)}
        elif recent_return < -0.05:
            return {'signal': 'sell', 'confidence': min(0.9, abs(recent_return) * 10)}
        else:
            return {'signal': 'neutral', 'confidence': 0.5}
            
    def _volume_signal(self, closes, volumes):
        if len(volumes) < 20:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        recent_vol = mean(volumes[-10:])
        avg_vol = mean(volumes[-30:-10]) if len(volumes) >= 30 else mean(volumes)
        
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        if vol_ratio > 1.5:
            price_change = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] > 0 else 0
            if price_change > 0:
                return {'signal': 'sell', 'confidence': 0.7}  # 放量上涨=派发
            else:
                return {'signal': 'buy', 'confidence': 0.7}  # 放量下跌=吸筹
        else:
            return {'signal': 'neutral', 'confidence': 0.5}
            
    def _trend_signal(self, closes):
        if len(closes) < 20:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        # 简单趋势: 20日均线方向
        ma20 = mean(closes[-20:])
        ma10 = mean(closes[-10:])
        
        if ma10 > ma20 * 1.02:
            return {'signal': 'buy', 'confidence': 0.6}
        elif ma10 < ma20 * 0.98:
            return {'signal': 'sell', 'confidence': 0.6}
        else:
            return {'signal': 'neutral', 'confidence': 0.5}
            
    def _reversion_signal(self, closes):
        if len(closes) < 50:
            return {'signal': 'neutral', 'confidence': 0.5}
            
        # 均值回归: 价格偏离均值过大时反向
        ma50 = mean(closes[-50:])
        current = closes[-1]
        
        deviation = (current - ma50) / ma50 if ma50 > 0 else 0
        
        if deviation > 0.1:
            return {'signal': 'sell', 'confidence': min(0.9, deviation * 5)}
        elif deviation < -0.1:
            return {'signal': 'buy', 'confidence': min(0.9, abs(deviation) * 5)}
        else:
            return {'signal': 'neutral', 'confidence': 0.5}

# ============================================
# Ensemble Engine
# ============================================
class EnsembleEngine:
    """加权组合引擎"""
    
    def __init__(self):
        self.factor_weights = copy.deepcopy(DEFAULT_FACTOR_WEIGHTS)
        self.strategy_weights = copy.deepcopy(DEFAULT_STRATEGY_WEIGHTS)
        self.timeframe_weights = copy.deepcopy(DEFAULT_TIMEFRAME_WEIGHTS)
        
        self.components = []
        self.prediction_history = []
        self.error_history = []
        self.iteration = 0
        
        self.learning_rate = OPTIMIZATION_PARAMS['learning_rate']
        self.momentum = OPTIMIZATION_PARAMS['momentum']
        self.velocity = {}  # 动量
        
        self._init_components()
        
    def _init_components(self):
        """初始化组件"""
        # 技术指标
        for indicator in ['rsi', 'macd', 'bollinger', 'ma_cross', 'atr']:
            self.components.append(TechnicalIndicator(indicator, 0.1))
            
        # 信号组件
        for signal in ['momentum', 'volume', 'trend', 'reversion']:
            self.components.append(SignalComponent(signal, 0.1))
            
    def set_weights(self, factor_weights=None, strategy_weights=None, timeframe_weights=None):
        """设置权重"""
        if factor_weights:
            self.factor_weights.update(factor_weights)
        if strategy_weights:
            self.strategy_weights.update(strategy_weights)
        if timeframe_weights:
            self.timeframe_weights.update(timeframe_weights)
            
        self._normalize_weights()
        
    def _normalize_weights(self):
        """归一化权重"""
        # 因子权重
        total = sum(self.factor_weights.values())
        if total > 0:
            self.factor_weights = {k: v / total for k, v in self.factor_weights.items()}
            
        # 策略权重
        total = sum(self.strategy_weights.values())
        if total > 0:
            self.strategy_weights = {k: v / total for k, v in self.strategy_weights.items()}
            
        # 时间框架权重
        total = sum(self.timeframe_weights.values())
        if total > 0:
            self.timeframe_weights = {k: v / total for k, v in self.timeframe_weights.items()}
            
    def predict(self, data):
        """综合预测"""
        if not data or len(data) < 20:
            return {'signal': 'neutral', 'confidence': 0.5, 'components': {}}
            
        # 收集各组件预测
        predictions = {}
        total_confidence = 0
        signal_scores = {'buy': 0, 'sell': 0, 'neutral': 0}
        
        for component in self.components:
            pred = component.predict(data)
            predictions[component.name] = pred
            
            # 加权投票
            weight = self._get_component_weight(component)
            confidence = pred['confidence'] * weight
            
            signal_scores[pred['signal']] += confidence
            total_confidence += confidence
            
        # 归一化
        if total_confidence > 0:
            for signal in signal_scores:
                signal_scores[signal] /= total_confidence
                
        # 最终信号
        best_signal = max(signal_scores, key=signal_scores.get)
        final_confidence = signal_scores[best_signal]
        
        return {
            'signal': best_signal,
            'confidence': final_confidence,
            'signal_scores': signal_scores,
            'components': predictions
        }
        
    def _get_component_weight(self, component):
        """获取组件权重"""
        name = component.name
        
        # 技术指标 -> technical
        if name in ['rsi', 'macd', 'bollinger', 'ma_cross', 'atr', 'adx', 'stoch', 'cci']:
            return self.factor_weights.get('technical', 0.1)
            
        # 动量 -> momentum
        if name in ['momentum', 'volume', 'trend']:
            return self.factor_weights.get('momentum', 0.05)
            
        # 成交量 -> volume
        if name == 'volume':
            return self.factor_weights.get('volume', 0.05)
            
        return 0.1
        
    def train(self, coin, period='90d', method='genetic', iterations=100):
        """训练权重"""
        period_map = {'7d': 168, '30d': 720, '90d': 2160}
        limit = min(period_map.get(period, 720), 500)
        
        data = get_price_data(coin, '1h', limit)
        
        if not data:
            print(f"无法获取 {coin} 数据")
            return None
            
        print(f"\n🔧 开始训练 {coin} 加权组合 ({method}, {iterations}次迭代)")
        print("="*60)
        
        if method == 'genetic':
            best_weights, best_error = self._genetic_optimize(data, iterations)
        elif method == 'gradient':
            best_weights, best_error = self._gradient_optimize(data, iterations)
        elif method == 'bayesian':
            best_weights, best_error = self._bayesian_optimize(data, iterations)
        else:  # simulation
            best_weights, best_error = self._simulation_optimize(data, iterations)
            
        # 应用最佳权重
        if best_weights:
            self.factor_weights.update(best_weights)
            self._normalize_weights()
            
        print(f"\n✅ 训练完成!")
        print(f"   最终误差: {best_error:.6f}")
        print(f"   迭代次数: {self.iteration}")
        
        return best_weights, best_error
        
    def _genetic_optimize(self, data, generations=100):
        """遗传算法优化"""
        best_weights = None
        best_error = float('inf')
        
        population_size = OPTIMIZATION_PARAMS['population_size']
        mutation_rate = OPTIMIZATION_PARAMS['mutation_rate']
        
        # 初始化种群
        population = []
        for _ in range(population_size):
            weights = self._random_weights()
            population.append(weights)
            
        for gen in range(generations):
            # 评估
            scored = []
            for weights in population:
                error = self._evaluate_weights(weights, data)
                scored.append((weights, error))
                
            # 排序
            scored.sort(key=lambda x: x[1])
            
            # 最佳
            if scored[0][1] < best_error:
                best_error = scored[0][1]
                best_weights = scored[0][0].copy()
                
            if gen % 20 == 0:
                print(f"  遗传迭代 {gen+1}/{generations}: 误差={best_error:.6f}")
                
            # 选择
            survivors = [w for w, _ in scored[:population_size // 2]]
            
            # 交叉
            children = []
            while len(children) < population_size - len(survivors):
                p1, p2 = random.sample(survivors, 2)
                child = self._crossover(p1, p2)
                children.append(child)
                
            # 变异
            for child in children:
                if random.random() < mutation_rate:
                    self._mutate(child)
                    
            population = survivors + children
            
        return best_weights, best_error
        
    def _gradient_optimize(self, data, iterations=100):
        """梯度下降优化"""
        best_weights = self.factor_weights.copy()
        best_error = self._evaluate_weights(best_weights, data)
        
        velocity = {k: 0 for k in best_weights}
        
        for i in range(iterations):
            # 计算梯度 (简化)
            gradient = {}
            for key in best_weights:
                epsilon = 0.001
                perturbed = best_weights.copy()
                perturbed[key] += epsilon
                
                error_plus = self._evaluate_weights(perturbed, data)
                gradient[key] = (error_plus - best_error) / epsilon
                
            # 更新
            for key in best_weights:
                velocity[key] = self.momentum * velocity[key] - self.learning_rate * gradient[key]
                best_weights[key] += velocity[key]
                
            # 确保非负
            best_weights[key] = max(0.01, best_weights[key])
            
            # 归一化
            self.factor_weights = best_weights.copy()
            self._normalize_weights()
            best_weights = self.factor_weights.copy()
            
            # 评估
            error = self._evaluate_weights(best_weights, data)
            
            if error < best_error:
                best_error = error
                
            if i % 20 == 0:
                print(f"  梯度迭代 {i+1}/{iterations}: 误差={best_error:.6f}")
                
            self.iteration = i
            
        return best_weights, best_error
        
    def _bayesian_optimize(self, data, iterations=100):
        """贝叶斯优化"""
        best_weights = self.factor_weights.copy()
        best_error = self._evaluate_weights(best_weights, data)
        
        for i in range(iterations):
            # 采样新权重
            new_weights = self._sample_weights(best_weights, exploration=0.3)
            
            # 评估
            error = self._evaluate_weights(new_weights, data)
            
            # 如果更好, 移动 towards it
            if error < best_error:
                alpha = 0.2
                for key in new_weights:
                    best_weights[key] = (1 - alpha) * best_weights[key] + alpha * new_weights[key]
                best_error = error
                
            if i % 20 == 0:
                print(f"  贝叶斯迭代 {i+1}/{iterations}: 误差={best_error:.6f}")
                
            self.iteration = i
            
        return best_weights, best_error
        
    def _simulation_optimize(self, data, iterations=100):
        """仿真优化"""
        best_weights = self.factor_weights.copy()
        best_error = self._evaluate_weights(best_weights, data)
        
        for i in range(iterations):
            # 随机扰动
            perturbed = best_weights.copy()
            for key in perturbed:
                perturbation = random.uniform(-0.1, 0.1)
                perturbed[key] = max(0.01, perturbed[key] + perturbation)
                
            # 归一化
            total = sum(perturbed.values())
            perturbed = {k: v / total for k, v in perturbed.items()}
            
            # 评估
            error = self._evaluate_weights(perturbed, data)
            
            # 模拟退火: 偶尔接受差的解
            temperature = 1.0 / (1 + i / 10)
            if error < best_error or random.random() < temperature:
                if error < best_error:
                    best_weights = perturbed
                    best_error = error
                    
            if i % 20 == 0:
                print(f"  仿真迭代 {i+1}/{iterations}: 误差={best_error:.6f}")
                
            self.iteration = i
            
        return best_weights, best_error
        
    def _evaluate_weights(self, weights, data):
        """评估权重"""
        # 保存原始权重
        original = self.factor_weights.copy()
        
        # 应用新权重
        self.factor_weights = weights.copy()
        self._normalize_weights()
        
        # 仿真预测
        total_error = 0
        predictions_made = 0
        
        # 滚动窗口回测
        window_size = 50
        step = 10
        
        for i in range(window_size, len(data) - 1, step):
            train_data = data[max(0, i - window_size):i]
            test_data = data[i]
            
            # 预测
            pred = self.predict(train_data)
            actual_return = (test_data['close'] - train_data[-1]['close']) / train_data[-1]['close']
            
            # 计算误差 (信号方向)
            if actual_return > 0.005:
                actual_signal = 'buy'
            elif actual_return < -0.005:
                actual_signal = 'sell'
            else:
                actual_signal = 'neutral'
                
            # 预测误差
            if pred['signal'] == actual_signal:
                error = 0
            elif pred['signal'] == 'neutral':
                error = 1
            else:
                error = 2  # 完全错误
                
            total_error += error
            predictions_made += 1
            
        # 恢复原始权重
        self.factor_weights = original
        
        return total_error / max(1, predictions_made) if predictions_made > 0 else 1.0
        
    def _random_weights(self):
        """生成随机权重"""
        keys = list(self.factor_weights.keys())
        weights = [random.random() for _ in keys]
        total = sum(weights)
        return {k: v / total for k, v in zip(keys, weights)}
        
    def _crossover(self, p1, p2):
        """交叉"""
        child = {}
        for key in p1:
            if random.random() < 0.5:
                child[key] = p1[key]
            else:
                child[key] = p2[key]
        return child
        
    def _mutate(self, weights):
        """变异"""
        mutation_rate = OPTIMIZATION_PARAMS['mutation_rate']
        for key in weights:
            if random.random() < mutation_rate:
                weights[key] = max(0.01, weights[key] + random.uniform(-0.1, 0.1))
                
    def _sample_weights(self, current, exploration=0.1):
        """采样新权重"""
        new_weights = {}
        for key, val in current.items():
            noise = random.gauss(0, exploration)
            new_weights[key] = max(0.01, val + noise)
            
        total = sum(new_weights.values())
        return {k: v / total for k, v in new_weights.items()}
        
    def update(self, new_data, actual_result):
        """在线更新"""
        # 预测
        pred = self.predict(new_data)
        
        # 计算误差
        if actual_result > 0.005:
            actual = 'buy'
        elif actual_result < -0.005:
            actual = 'sell'
        else:
            actual = 'neutral'
            
        error = 0 if pred['signal'] == actual else (1 if pred['signal'] == 'neutral' else 2)
        
        # 梯度下降更新
        gradient = {}
        for key in self.factor_weights:
            epsilon = 0.001
            perturbed = self.factor_weights.copy()
            perturbed[key] += epsilon
            
            # 重新评估 (简化)
            original = self.factor_weights.copy()
            self.factor_weights = perturbed
            self._normalize_weights()
            
            # 简化的误差变化
            perturbed_error = error + epsilon  # 简化
            
            gradient[key] = (perturbed_error - error) / epsilon
            self.factor_weights = original
            
        # 更新
        for key in gradient:
            delta = -self.learning_rate * gradient[key]
            self.factor_weights[key] = max(0.01, self.factor_weights[key] + delta)
            
        self._normalize_weights()
        
        self.error_history.append(error)
        self.prediction_history.append(pred)
        
    def get_weights(self):
        """获取当前权重"""
        return {
            'factors': self.factor_weights.copy(),
            'strategies': self.strategy_weights.copy(),
            'timeframes': self.timeframe_weights.copy()
        }
        
    def save_weights(self, filepath):
        """保存权重"""
        weights = self.get_weights()
        weights['history'] = {
            'iteration': self.iteration,
            'error_history': self.error_history[-100:]
        }
        with open(filepath, 'w') as f:
            json.dump(weights, f, indent=2)
        print(f"权重已保存到 {filepath}")
        
    def load_weights(self, filepath):
        """加载权重"""
        with open(filepath, 'r') as f:
            weights = json.load(f)
            
        if 'factors' in weights:
            self.factor_weights = weights['factors']
        if 'strategies' in weights:
            self.strategy_weights = weights['strategies']
        if 'timeframes' in weights:
            self.timeframe_weights = weights['timeframes']
            
        if 'history' in weights:
            self.iteration = weights['history'].get('iteration', 0)
            self.error_history = weights['history'].get('error_history', [])
            
        print(f"权重已从 {filepath} 加载")

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-ensemble - 加权组合矫正引擎")
        print("Usage:")
        print("  python ensemble_engine.py train <coin> [period] [method]")
        print("  python ensemble_engine.py predict <coin>")
        print("  python ensemble_engine.py weights")
        print("  python ensemble_engine.py update <coin>")
        sys.exit(1)
        
    cmd = sys.argv[1]
    ensemble = EnsembleEngine()
    
    if cmd == 'train' and len(sys.argv) >= 3:
        coin = sys.argv[2].upper()
        period = sys.argv[3] if len(sys.argv) > 3 else '90d'
        method = sys.argv[4] if len(sys.argv) > 4 else 'genetic'
        
        weights, error = ensemble.train(coin, period, method)
        
        if weights:
            print(f"\n📊 最优因子权重:")
            for k, v in sorted(weights.items(), key=lambda x: -x[1]):
                print(f"   {k}: {v:.4f}")
                
    elif cmd == 'predict' and len(sys.argv) >= 3:
        coin = sys.argv[2].upper()
        data = get_price_data(coin, '1h', 200)
        
        if data:
            pred = ensemble.predict(data)
            print(f"\n🎯 {coin} 预测:")
            print(f"   信号: {pred['signal']}")
            print(f"   置信度: {pred['confidence']:.1%}")
            print(f"   信号得分: buy={pred['signal_scores']['buy']:.2f}, sell={pred['signal_scores']['sell']:.2f}, neutral={pred['signal_scores']['neutral']:.2f}")
        else:
            print(f"无法获取 {coin} 数据")
            
    elif cmd == 'weights':
        weights = ensemble.get_weights()
        print(f"\n⚙️ 当前权重:")
        print(f"\n📊 因子权重:")
        for k, v in sorted(weights['factors'].items(), key=lambda x: -x[1]):
            print(f"   {k}: {v:.4f}")
            
    elif cmd == 'update' and len(sys.argv) >= 3:
        coin = sys.argv[2].upper()
        data = get_price_data(coin, '1h', 200)
        
        if data and len(data) > 1:
            actual_return = (data[-1]['close'] - data[-2]['close']) / data[-2]['close']
            ensemble.update(data[:-1], actual_return)
            print(f"权重已更新 (实际收益: {actual_return:.2%})")
        else:
            print(f"无法更新")
    else:
        print("未知命令")
