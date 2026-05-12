#!/usr/bin/env python3
"""
go-quantum - 量子力学交易分析引擎
应用量子力学原理分析价格运动，预测转折点、边界条件和周期
"""
import math, json, time, random, urllib.request, cmath
from datetime import datetime, timedelta
from collections import defaultdict
import hmac, hashlib

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 量子常数
QUANTUM_PARAMS = {
    'hbar': 0.0001,           # 归一化普朗克常数
    'potential_strength': 0.02,  # 势垒强度
    'tunneling_factor': 0.15,    # 隧穿因子
    'decoherence_rate': 0.10,    # 退相干率
    'boundary_width': 0.05,       # 边界宽度
    'coherence_decay': 0.95,      # 相干性衰减
}

# 能级 (n²倍的基态能量)
ENERGY_LEVELS = [0.01, 0.04, 0.09, 0.16, 0.25, 0.36, 0.49, 0.64]

# 量子态描述
QUANTUM_STATES = {
    0: {'name': '基态', 'description': '低波动盘整', 'stability': 'high'},
    1: {'name': '第一激发态', 'description': '轻微趋势', 'stability': 'medium'},
    2: {'name': '第二激发态', 'description': '明显趋势', 'stability': 'medium'},
    3: {'name': '第三激发态', 'description': '强趋势', 'stability': 'low'},
    4: {'name': '高激发态', 'description': '极端波动', 'stability': 'very_low'},
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
    """归一化到[0,1]"""
    if not values: return []
    min_v, max_v = min(values), max(values)
    if max_v == min_v: return [0.5] * len(values)
    return [(v - min_v) / (max_v - min_v) for v in values]

# ============================================
# Wave Function Analysis
# ============================================
class WaveFunction:
    """波函数分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.times = [d['time'] for d in data]
        
    def build_psi(self):
        """构建波函数 Ψ = A·e^(iθ)·φ·e^(-iEt/ℏ)"""
        if len(self.data) < 20:
            return None
            
        # 价格序列
        prices = self.closes
        
        # 振幅 (归一化价格变化)
        returns = [math.log(prices[i]/prices[i-1]) for i in range(1, len(prices))]
        amplitude = std(returns) if returns else 0.01
        
        # 相位 (价格趋势方向)
        recent_return = sum(returns[-10:]) / len(returns) if returns else 0
        phase = math.atan(recent_return)  # -π/2 到 π/2
        
        # 频率成分 (使用FFT提取)
        frequencies = self._fft_analysis(prices)
        
        # 能量 (波动率)
        energy = amplitude ** 2
        
        return {
            'amplitude': amplitude,
            'phase': phase,
            'frequencies': frequencies,
            'energy': energy,
            'psi_magnitude': abs(amplitude * math.e ** (1j * phase))
        }
        
    def _fft_analysis(self, prices):
        """FFT频率分析"""
        if len(prices) < 32:
            return []
            
        # 简化的频率分析
        n = 8  # 分析8个频率
        freq_data = []
        
        for i in range(n):
            window = 2 ** (i + 2)  # 4, 8, 16, 32, 64, 128, 256, 512
            if window > len(prices):
                break
                
            # 取最近window个点
            subset = prices[-window:]
            if len(subset) < 4:
                continue
                
            # 计算该窗口的波动率
            returns = [(subset[j]-subset[j-1])/subset[j-1] for j in range(1,len(subset))]
            volatility = std(returns) if returns else 0
            
            freq_data.append({
                'period': window,
                'amplitude': volatility,
                'frequency': 1.0 / window if window > 0 else 0
            })
            
        return freq_data
        
    def calculate_probability_density(self, price_levels):
        """计算概率密度 P(x) = |Ψ|²"""
        psi = self.build_psi()
        if not psi:
            return {}
            
        amplitudes = psi['frequencies']
        if not amplitudes:
            amplitudes = [{'amplitude': psi['amplitude']}]
            
        # 概率密度 = 振幅平方
        prob_density = {}
        for level in price_levels:
            prob = 0
            for freq in amplitudes:
                prob += (freq['amplitude'] ** 2)
            prob_density[level] = prob / len(amplitudes) if amplitudes else prob
            
        # 归一化
        total = sum(prob_density.values())
        if total > 0:
            prob_density = {k: v/total for k, v in prob_density.items()}
            
        return prob_density
        
    def superposition_state(self):
        """叠加态分析 - 价格同时处于多种状态"""
        psi = self.build_psi()
        if not psi:
            return {}
            
        # 价格分布的多种可能性
        price_range = max(self.closes) - min(self.closes)
        avg_price = mean(self.closes)
        
        states = []
        for n, energy in enumerate(ENERGY_LEVELS[:5]):
            prob = math.exp(-energy / psi['energy']) if psi['energy'] > 0 else 0
            price_center = avg_price * (1 + (n - 2) * 0.02)
            
            states.append({
                'level': n,
                'state': f'|{n}⟩',
                'energy': energy,
                'probability': prob,
                'price_center': price_center,
                'width': price_range * 0.1 * (n + 1)
            })
            
        # 归一化概率
        total = sum(s['probability'] for s in states)
        if total > 0:
            for s in states:
                s['probability'] /= total
                
        return {
            'states': states,
            'superposition': True,
            'dominant_state': max(states, key=lambda x: x['probability']) if states else None
        }

# ============================================
# Boundary Conditions
# ============================================
class BoundaryConditions:
    """边界条件分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        
    def find_boundaries(self):
        """找出势垒和势阱"""
        if len(self.data) < 50:
            return self._default_boundaries()
            
        # 分析价格分布
        price_array = self.closes[-100:] if len(self.closes) >= 100 else self.closes
        
        # 找出局部极值
        highs = []
        lows = []
        
        for i in range(5, len(price_array) - 5):
            if price_array[i] == max(price_array[i-5:i+6]):
                highs.append(price_array[i])
            if price_array[i] == min(price_array[i-5:i+6]):
                lows.append(price_array[i])
                
        if not highs or not lows:
            return self._default_boundaries()
            
        # 边界价格
        upper = max(highs[-10:]) if len(highs) >= 10 else max(highs)
        lower = min(lows[-10:]) if len(lows) >= 10 else min(lows)
        mid = mean(price_array)
        
        # 边界强度 (基于价格触及边界的次数)
        upper_touches = sum(1 for h in highs if h >= upper * 0.98)
        lower_touches = sum(1 for l in lows if l <= lower * 1.02)
        
        # 边界类型
        upper_type = 'barrier_strong' if upper_touches > 3 else 'barrier_weak'
        lower_type = 'well_deep' if lower_touches > 3 else 'well_shallow'
        
        # 当前价格位置
        current = self.closes[-1]
        position_ratio = (current - lower) / (upper - lower) if upper != lower else 0.5
        
        return {
            'upper': upper,
            'lower': lower,
            'mid': mid,
            'width': upper - lower,
            'upper_type': upper_type,
            'lower_type': lower_type,
            'upper_strength': min(1.0, upper_touches / 10),
            'lower_strength': min(1.0, lower_touches / 10),
            'current_position': position_ratio,
            'current_ratio': position_ratio,
            'tunneling_probability': self._calc_tunneling(upper, lower, current)
        }
        
    def _calc_tunneling(self, upper, lower, current):
        """计算隧穿概率"""
        # 如果价格接近边界，可能隧穿
        distance_to_upper = abs(upper - current) / upper if upper > 0 else 1
        distance_to_lower = abs(current - lower) / lower if lower > 0 else 1
        
        # 隧穿概率 = e^(-2γd)
        gamma = QUANTUM_PARAMS['tunneling_factor']
        
        if distance_to_upper < 0.05:
            prob = math.exp(-2 * gamma * (1 / distance_to_upper))
            return min(0.9, prob)
        elif distance_to_lower < 0.05:
            prob = math.exp(-2 * gamma * (1 / distance_to_lower))
            return min(0.9, prob)
            
        return 0.0
        
    def _default_boundaries(self):
        current = self.closes[-1] if self.closes else 100
        return {
            'upper': current * 1.05,
            'lower': current * 0.95,
            'mid': current,
            'width': current * 0.1,
            'upper_type': 'barrier_weak',
            'lower_type': 'well_shallow',
            'upper_strength': 0.3,
            'lower_strength': 0.3,
            'current_position': 0.5,
            'current_ratio': 0.5,
            'tunneling_probability': 0.0
        }
        
    def detect_phase_transition(self):
        """检测相变 (市场状态转变)"""
        if len(self.data) < 100:
            return {'transition': False}
            
        # 比较前半和后半的统计特性
        mid = len(self.data) // 2
        first_half = self.closes[:mid]
        second_half = self.closes[mid:]
        
        vol1 = std(first_half) / mean(first_half) if first_half else 0
        vol2 = std(second_half) / mean(second_half) if second_half else 0
        
        # 相变信号
        vol_change = abs(vol2 - vol1) / vol1 if vol1 > 0 else 0
        
        return {
            'transition': vol_change > 0.5,  # 波动率变化超过50%
            'vol_change': vol_change,
            'old_phase': 'low_volatility' if vol1 < vol2 else 'high_volatility',
            'new_phase': 'high_volatility' if vol1 < vol2 else 'low_volatility',
            'transition_strength': min(1.0, vol_change)
        }

# ============================================
# Turning Point Detection
# ============================================
class QuantumTurningPoint:
    """量子转折点检测"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.times = [d['time'] for d in data]
        
    def find_quantum_turning_points(self, threshold=0.03):
        """找出量子化转折点"""
        if len(self.data) < 50:
            return []
            
        turning_points = []
        
        for i in range(10, len(self.closes) - 10):
            price = self.closes[i]
            
            # 局部顶
            if price == max(self.closes[i-10:i+11]):
                gain = (price - self.closes[i-10]) / self.closes[i-10] if self.closes[i-10] > 0 else 0
                if gain > threshold:
                    turning_points.append({
                        'index': i,
                        'time': self.times[i],
                        'type': 'top',
                        'price': price,
                        'gain': gain,
                        'quantum_type': self._classify_top(price, i)
                    })
                    
            # 局部底
            if price == min(self.closes[i-10:i+11]):
                drop = (self.closes[i-10] - price) / self.closes[i-10] if self.closes[i-10] > 0 else 0
                if drop > threshold:
                    turning_points.append({
                        'index': i,
                        'time': self.times[i],
                        'type': 'bottom',
                        'price': price,
                        'drop': drop,
                        'quantum_type': self._classify_bottom(price, i)
                    })
                
        return turning_points
        
    def _classify_top(self, price, index):
        """分类顶部转折"""
        if len(self.closes) < 50:
            return 'unknown'
            
        # 检查是否是量子态转变
        recent_vol = std(self.closes[index-20:index]) if index >= 20 else std(self.closes[:index])
        future_vol = std(self.closes[index:index+20]) if index + 20 <= len(self.closes) else std(self.closes[index:])
        
        if future_vol < recent_vol * 0.5:
            return 'collapse'  # 波函数坍缩
        elif future_vol > recent_vol * 1.5:
            return 'tunneling'  # 隧穿
        else:
            return 'interference'  # 干涉
            
    def _classify_bottom(self, price, index):
        """分类底部转折"""
        if len(self.closes) < 50:
            return 'unknown'
            
        recent_vol = std(self.closes[index-20:index]) if index >= 20 else std(self.closes[:index])
        future_vol = std(self.closes[index:index+20]) if index + 20 <= len(self.closes) else std(self.closes[index:])
        
        if future_vol > recent_vol * 1.5:
            return 'collapse'
        elif future_vol < recent_vol * 0.7:
            return 'tunneling'
        else:
            return 'entanglement'
            
    def predict_next_turning_point(self, historical_points):
        """预测下次转折点"""
        if not historical_points:
            return {'time': None, 'type': None, 'probability': 0.3}
            
        # 分析历史转折点间隔
        if len(historical_points) < 2:
            last = historical_points[-1]
            avg_interval = 4 * 3600  # 默认4小时
        else:
            intervals = []
            for i in range(1, len(historical_points)):
                dt = historical_points[i]['time'] - historical_points[i-1]['time']
                intervals.append(dt)
            avg_interval = mean(intervals)
            
        # 预测下次转折
        last_time = historical_points[-1]['time']
        next_time = last_time + avg_interval
        
        # 预测类型 (交替或延续)
        recent_types = [tp['type'] for tp in historical_points[-5:]]
        if len(recent_types) >= 2:
            if recent_types[-1] == recent_types[-2]:
                predicted_type = 'bottom' if recent_types[-1] == 'top' else 'top'
            else:
                predicted_type = recent_types[-1]
        else:
            predicted_type = 'top'
            
        # 概率
        prob = min(0.9, 0.4 + len(historical_points) * 0.05)
        
        return {
            'time': next_time,
            'time_str': datetime.fromtimestamp(next_time).strftime('%Y-%m-%d %H:%M'),
            'type': predicted_type,
            'probability': prob,
            'confidence': 'high' if len(historical_points) > 10 else 'medium'
        }

# ============================================
# Cycle Analysis
# ============================================
class CycleAnalysis:
    """量子周期分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        
    def find_quantum_cycles(self):
        """找出量子化周期"""
        if len(self.data) < 100:
            return {'primary': None, 'secondary': None, 'harmonics': []}
            
        # FFT找主周期
        frequencies = self._fft_cycles()
        
        if not frequencies:
            return self._default_cycles()
            
        # 排序找主周期
        frequencies.sort(key=lambda x: x['power'], reverse=True)
        
        primary = frequencies[0] if frequencies else None
        secondary = frequencies[1] if len(frequencies) > 1 else None
        
        # 谐波
        harmonics = []
        if primary:
            base_freq = primary['frequency']
            for n in [2, 3, 4, 5]:
                harmonics.append({
                    'n': n,
                    'frequency': base_freq * n,
                    'period': 1 / (base_freq * n) if base_freq > 0 else 0,
                    'power': primary['power'] / n
                })
                
        return {
            'primary': primary,
            'secondary': secondary,
            'harmonics': harmonics[:4],
            'quantum_numbers': self._calculate_quantum_numbers(frequencies)
        }
        
    def _fft_cycles(self):
        """FFT周期分析"""
        if len(self.closes) < 64:
            return []
            
        # 简化: 使用自相关找周期
        prices = self.closes[-200:]  # 最近200个点
        n = len(prices)
        
        # 计算收益率
        returns = [(prices[i]-prices[i-1])/prices[i-1] for i in range(1, n)]
        
        # 自相关
        max_lag = min(50, n // 2)
        correlations = []
        
        for lag in range(5, max_lag):
            c = sum(returns[i] * returns[i-lag] for i in range(lag, n-1))
            c /= (n - lag)
            correlations.append({'lag': lag, 'correlation': c})
            
        # 找峰值 (周期)
        peaks = []
        for i in range(2, len(correlations)-2):
            if correlations[i]['correlation'] > correlations[i-1]['correlation']:
                if correlations[i]['correlation'] > correlations[i+1]['correlation']:
                    if correlations[i]['correlation'] > 0.1:  # 阈值
                        peaks.append({
                            'period': correlations[i]['lag'],
                            'power': correlations[i]['correlation']
                        })
                        
        return peaks
        
    def _calculate_quantum_numbers(self, frequencies):
        """计算量子数 (n²关系)"""
        if not frequencies:
            return []
            
        quantum_numbers = []
        for f in frequencies[:5]:
            # n = sqrt(T/T1)
            if f['period'] > 0:
                n = math.sqrt(f['period'] / 4)  # 基态周期4
                quantum_numbers.append({
                    'n': round(n),
                    'state': f'|{round(n)}⟩',
                    'period': f['period'],
                    'energy': (round(n) ** 2) * 0.01
                })
                
        return quantum_numbers
        
    def _default_cycles(self):
        return {
            'primary': {'period': 24, 'power': 0.5},
            'secondary': {'period': 168, 'power': 0.3},
            'harmonics': [],
            'quantum_numbers': []
        }
        
    def predict_next_cycle_top(self, cycles):
        """预测下次周期顶部"""
        if not cycles or not cycles['primary']:
            return {'time': None, 'probability': 0.3}
            
        primary_period = cycles['primary']['period']
        
        # 找到最后一个局部顶
        closes = self.closes
        last_top_time = None
        last_top_idx = 0
        
        for i in range(10, len(closes) - 10):
            if closes[i] == max(closes[i-10:i+11]):
                last_top_idx = i
                last_top_time = self.data[i]['time']
                break
                
        if not last_top_time:
            last_top_time = self.data[-1]['time']
            
        # 下次周期顶
        next_top_time = last_top_time + primary_period * 3600  # 假设period单位是小时
        
        return {
            'time': next_top_time,
            'time_str': datetime.fromtimestamp(next_top_time).strftime('%Y-%m-%d %H:%M'),
            'period': primary_period,
            'probability': 0.7
        }

# ============================================
# Quantum Engine
# ============================================
class QuantumEngine:
    """量子力学交易分析引擎"""
    
    def __init__(self):
        self.params = QUANTUM_PARAMS
        self.wave_function = None
        self.boundaries = None
        self.turning_points = []
        self.cycles = {}
        
    def analyze(self, coin, interval='1h', period='90d'):
        """完整量子分析"""
        period_map = {'7d': 168, '30d': 720, '90d': 2160}
        limit = min(period_map.get(period, 720), 500)
        
        data = get_price_data(coin, interval, limit)
        
        if not data:
            return None
            
        # 1. 波函数分析
        self.wave_function = WaveFunction(data)
        psi = self.wave_function.build_psi()
        superposition = self.wave_function.superposition_state()
        
        # 2. 边界条件
        boundary = BoundaryConditions(data)
        boundaries = boundary.find_boundaries()
        phase_transition = boundary.detect_phase_transition()
        
        # 3. 转折点
        turning = QuantumTurningPoint(data)
        turning_points = turning.find_quantum_turning_points()
        next_turning = turning.predict_next_turning_point(turning_points)
        
        # 4. 周期
        cycle = CycleAnalysis(data)
        cycles = cycle.find_quantum_cycles()
        next_cycle_top = cycle.predict_next_cycle_top(cycles)
        
        # 5. 综合量子态
        quantum_state = self._calculate_quantum_state(
            psi, boundaries, turning_points, cycles
        )
        
        # 6. 预测
        prediction = self._make_prediction(
            quantum_state, boundaries, next_turning, next_cycle_top
        )
        
        return {
            'coin': coin,
            'timeframe': interval,
            'period': period,
            'quantum_state': quantum_state,
            'psi': psi,
            'superposition': superposition,
            'boundaries': boundaries,
            'phase_transition': phase_transition,
            'turning_points': turning_points,
            'next_turning_point': next_turning,
            'cycles': cycles,
            'next_cycle_top': next_cycle_top,
            'prediction': prediction
        }
        
    def _calculate_quantum_state(self, psi, boundaries, turning_points, cycles):
        """计算量子态"""
        if not psi:
            return {'level': 0, 'state': '|0⟩', 'energy': 0.01, 'coherence': 0.5}
            
        # 能量决定能级
        energy = psi['energy']
        level = 0
        for i, e in enumerate(ENERGY_LEVELS):
            if energy >= e:
                level = i
                
        state_info = QUANTUM_STATES.get(level, QUANTUM_STATES[4])
        
        # 相干性 (基于边界强度)
        coherence = 1.0 - QUANTUM_PARAMS['decoherence_rate']
        
        # 稳定性
        stability_score = coherence * (1 - energy)
        
        return {
            'level': level,
            'state': f'|{level}⟩',
            'state_name': state_info['name'],
            'energy': energy,
            'coherence': coherence,
            'stability': stability_score,
            'description': state_info['description']
        }
        
    def _make_prediction(self, quantum_state, boundaries, next_turning, next_cycle_top):
        """生成预测"""
        current_position = boundaries.get('current_ratio', 0.5)
        tunneling_prob = boundaries.get('tunneling_probability', 0)
        next_type = next_turning.get('type')
        next_time = next_turning.get('time_str')
        
        # 操作建议
        if tunneling_prob > 0.3:
            action = 'QUANTUM_TUNNEL'  # 可能有隧穿
            direction = 'break_upper' if current_position > 0.7 else 'break_lower'
        elif quantum_state['coherence'] > 0.8:
            action = 'HOLD'  # 高相干性, 观望
            direction = None
        elif next_type == 'top':
            action = 'QUANTUM_SELL' if quantum_state['level'] > 2 else 'REDUCE'
            direction = 'potential_top'
        elif next_type == 'bottom':
            action = 'QUANTUM_BUY' if quantum_state['level'] < 2 else 'ACCUMULATE'
            direction = 'potential_bottom'
        else:
            action = 'OBSERVE'
            direction = None
            
        return {
            'action': action,
            'direction': direction,
            'tunneling_probability': tunneling_prob,
            'confidence': quantum_state['coherence'] * next_turning.get('probability', 0.5),
            'reasoning': self._generate_reasoning(quantum_state, boundaries, next_turning)
        }
        
    def _generate_reasoning(self, quantum_state, boundaries, next_turning):
        """生成推理"""
        parts = []
        
        # 量子态
        parts.append(f"量子态{quantum_state['state']}({quantum_state['state_name']})")
        
        # 位置
        pos = boundaries.get('current_ratio', 0.5)
        if pos > 0.7:
            parts.append("价格位于强势区域")
        elif pos < 0.3:
            parts.append("价格位于弱势区域")
        else:
            parts.append("价格位于中性区域")
            
        # 隧穿
        tunnel = boundaries.get('tunneling_probability', 0)
        if tunnel > 0.2:
            parts.append(f"存在{tunnel:.0%}的隧穿概率")
            
        # 转折
        if next_turning.get('type'):
            parts.append(f"预计{next_turning['type']}在{next_turning.get('time_str', '某个时间点')}")
            
        return "; ".join(parts)

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-quantum - 量子力学交易分析")
        print("Usage:")
        print("  python quantum_engine.py <coin> [interval] [period]")
        print("Example:")
        print("  python quantum_engine.py BTC 1h 90d")
        sys.exit(1)
        
    coin = sys.argv[1].upper()
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    period = sys.argv[3] if len(sys.argv) > 3 else '90d'
    
    print(f"\n⚛️ 量子力学分析: {coin} ({interval}, {period})")
    print("="*60)
    
    engine = QuantumEngine()
    result = engine.analyze(coin, interval, period)
    
    if result:
        state = result['quantum_state']
        
        print(f"\n⚛️ 量子态:")
        print(f"   态: {state['state']} ({state['state_name']})")
        print(f"   能量: {state['energy']:.6f}")
        print(f"   相干性: {state['coherence']:.1%}")
        print(f"   稳定性: {state['stability']:.2f}")
        print(f"   描述: {state['description']}")
        
        boundaries = result['boundaries']
        print(f"\n📊 边界条件:")
        print(f"   上边界: ${boundaries['upper']:.2f} ({boundaries['upper_type']})")
        print(f"   下边界: ${boundaries['lower']:.2f} ({boundaries['lower_type']})")
        print(f"   宽度: ${boundaries['width']:.2f}")
        print(f"   当前位置: {boundaries['current_ratio']:.1%}")
        print(f"   隧穿概率: {boundaries['tunneling_probability']:.1%}")
        
        print(f"\n🔄 相变检测:")
        pt = result['phase_transition']
        print(f"   相变: {'是' if pt['transition'] else '否'}")
        if pt['transition']:
            print(f"   {pt['old_phase']} → {pt['new_phase']}")
            print(f"   强度: {pt['transition_strength']:.2f}")
            
        print(f"\n🎯 转折点预测:")
        tp = result['next_turning_point']
        if tp['time']:
            print(f"   时间: {tp['time_str']}")
            print(f"   类型: {tp['type']}")
            print(f"   概率: {tp['probability']:.0%}")
            print(f"   置信度: {tp['confidence']}")
            
        cycles = result['cycles']
        print(f"\n🔁 量子周期:")
        if cycles['primary']:
            print(f"   主周期: {cycles['primary']['period']:.0f} 单位时间")
        if cycles['secondary']:
            print(f"   次周期: {cycles['secondary']['period']:.0f} 单位时间")
        if cycles.get('quantum_numbers'):
            print(f"   量子数:")
            for qn in cycles['quantum_numbers'][:3]:
                print(f"     n={qn['n']}: {qn['state']} 能量={qn['energy']:.4f}")
                
        pred = result['prediction']
        print(f"\n💡 预测操作:")
        print(f"   操作: {pred['action']}")
        if pred['direction']:
            print(f"   方向: {pred['direction']}")
        print(f"   置信度: {pred['confidence']:.0%}")
        print(f"   推理: {pred['reasoning']}")
    else:
        print("数据获取失败")
