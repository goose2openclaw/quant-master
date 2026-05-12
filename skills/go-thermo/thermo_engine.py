#!/usr/bin/env python3
"""
go-thermo - 热力学交易分析引擎
基于热力学原理分析市场状态、预测转折点
"""
import math, json, time, random, urllib.request
from datetime import datetime, timedelta
from collections import defaultdict
import hmac, hashlib

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 热力学参数
THERMO_PARAMS = {
    'boltzmann_k': 1.0,
    'temperature_scale': 1.0,
    'entropy_threshold': 0.7,
    'phase_critical_temp': 1.2,
    'heat_transfer_coef': 0.15,
    'energy_levels': [0.01, 0.05, 0.15, 0.3, 0.5],
    'boundary_conductivity': 0.1,
    'r': 0.01,  # 气体常数
}

# 热力学阶段
THERMO_PHASES = {
    'solid': {'name': '固态', 'description': '低波动盘整', 'entropy': 'low', 'temperature': 'cold'},
    'liquid': {'name': '液态', 'description': '中等波动', 'entropy': 'medium', 'temperature': 'normal'},
    'gas': {'name': '气态', 'description': '高波动无序', 'entropy': 'high', 'temperature': 'hot'},
    'plasma': {'name': '等离子态', 'description': '极端波动', 'entropy': 'extreme', 'temperature': 'overheated'},
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
    min_v, max_v = min(values), max(values)
    if max_v == min_v: return [0.5] * len(values)
    return [(v - min_v) / (max_v - min_v) for v in values]

# ============================================
# Temperature Analysis
# ============================================
class TemperatureAnalyzer:
    """市场温度分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.volumes = [d['volume'] for d in data]
        
    def calculate_price_temperature(self, window=20):
        """基于波动率的价格温度"""
        if len(self.data) < window + 1:
            return 0.5
            
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(1, len(self.closes))]
        recent_returns = returns[-window:]
        
        # 波动率
        volatility = std(recent_returns) if recent_returns else 0
        
        # 趋势强度
        trend = abs(sum(recent_returns) / len(recent_returns))
        
        # 温度 = 波动率 / (趋势 + 小值) × 缩放因子
        T = volatility / (trend + 0.001) * 10
        
        return min(3.0, max(0.0, T))
        
    def calculate_volume_temperature(self, window=20):
        """基于成交量的热度"""
        if len(self.volumes) < window + 1:
            return 0.5
            
        recent_vol = mean(self.volumes[-window:])
        avg_vol = mean(self.volumes[-window*3:-window]) if len(self.volumes) >= window*4 else mean(self.volumes)
        
        # 成交量比率
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        # 温度
        T = min(vol_ratio / 2, 2.0)
        
        return min(3.0, max(0.0, T))
        
    def calculate_momentum_temperature(self, window=20):
        """基于动量的温度"""
        if len(self.closes) < window + 1:
            return 0.5
            
        # 价格变化率
        recent = self.closes[-window:]
        momentum = (recent[-1] - recent[0]) / recent[0] if recent[0] > 0 else 0
        
        # 温度 = 动量绝对值 × 系数
        T = abs(momentum) * 50
        
        return min(3.0, max(0.0, T))
        
    def calculate_composite_temperature(self, window=20):
        """综合温度"""
        T_price = self.calculate_price_temperature(window)
        T_volume = self.calculate_volume_temperature(window)
        T_momentum = self.calculate_momentum_temperature(window)
        
        # 加权平均
        T = T_price * 0.5 + T_volume * 0.3 + T_momentum * 0.2
        
        return min(3.0, max(0.0, T))
        
    def get_temperature_phase(self, T):
        """获取温度阶段"""
        if T > 2.0:
            return 'overheated', '等离子态', 'EXTREME'
        elif T > 1.2:
            return 'hot', '气态', 'HIGH'
        elif T > 0.7:
            return 'normal', '液态', 'MEDIUM'
        elif T > 0.3:
            return 'cold', '固态', 'LOW'
        else:
            return 'frozen', '极冷', 'MINIMAL'

# ============================================
# Entropy Analysis
# ============================================
class EntropyAnalyzer:
    """熵分析 - 市场无序程度"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        
    def calculate_shannon_entropy(self, bins=20):
        """香农熵 H = -Σ p_i ln(p_i)"""
        if len(self.data) < bins * 2:
            return 0.5, 0.5
            
        # 划分价格区间
        prices = self.closes[-500:] if len(self.closes) >= 500 else self.closes
        min_p, max_p = min(prices), max(prices)
        
        if max_p == min_p:
            return 0.0, 1.0
            
        bin_width = (max_p - min_p) / bins
        bin_counts = [0] * bins
        
        for p in prices:
            idx = int((p - min_p) / bin_width)
            if idx >= bins:
                idx = bins - 1
            bin_counts[idx] += 1
            
        # 计算概率分布
        total = sum(bin_counts)
        if total == 0:
            return 0.5, 0.5
            
        probabilities = [c / total for c in bin_counts]
        
        # 香农熵
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log(p)
                
        # 归一化 (最大熵 = ln(bins))
        max_entropy = math.log(bins)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.5
        
        # 有序度 (1 - 归一化熵)
        order = 1 - normalized_entropy
        
        return normalized_entropy, order
        
    def calculate_conditional_entropy(self, window=50):
        """条件熵 - 价格转移的无序程度"""
        if len(self.closes) < window + 1:
            return 0.5
            
        # 价格变动方向
        changes = []
        for i in range(1, len(self.closes)):
            if self.closes[i] > self.closes[i-1]:
                changes.append(1)  # 上涨
            elif self.closes[i] < self.closes[i-1]:
                changes.append(-1)  # 下跌
            else:
                changes.append(0)  # 持平
                
        recent = changes[-window:]
        
        # 计算转移概率
        transitions = defaultdict(int)
        total = 0
        for i in range(1, len(recent)):
            key = (recent[i-1], recent[i])
            transitions[key] += 1
            total += 1
            
        if total == 0:
            return 0.5
            
        # 条件熵
        entropy = 0.0
        for (prev, curr), count in transitions.items():
            p = count / total
            if p > 0:
                entropy -= p * math.log(p)
                
        return min(1.0, entropy / 2.0)  # 归一化
        
    def detect_entropy_spike(self, window=100):
        """检测熵突增 (趋势可能反转)"""
        if len(self.closes) < window:
            return False, 0
            
        entropies = []
        step = 20
        for i in range(step, len(self.closes) - step, step):
            subset_data = self.data[max(0, i-step):i]
            ent, _ = self.calculate_shannon_entropy()
            entropies.append(ent)
            
        if len(entropies) < 3:
            return False, 0
            
        # 检测熵增
        recent_entropy = mean(entropies[-3:])
        prev_entropy = mean(entropies[-6:-3]) if len(entropies) >= 6 else recent_entropy
        
        entropy_change = recent_entropy - prev_entropy
        
        # 熵突增
        if entropy_change > 0.1:
            return True, entropy_change
            
        return False, entropy_change

# ============================================
# Boltzmann Distribution
# ============================================
class BoltzmannAnalyzer:
    """玻尔兹曼分布分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        
    def calculate_boltzmann_probabilities(self, energy_levels=None):
        """计算各能量级的玻尔兹曼概率"""
        if energy_levels is None:
            energy_levels = THERMO_PARAMS['energy_levels']
            
        T = THERMO_PARAMS['temperature_scale']
        k = THERMO_PARAMS['boltzmann_k']
        
        # 计算配分函数 Z = Σ e^(-E_i / kT)
        partition_func = 0.0
        energies = []
        for E in energy_levels:
            boltz_factor = math.exp(-E / (k * T + 0.001))
            partition_func += boltz_factor
            energies.append(boltz_factor)
            
        if partition_func == 0:
            partition_func = 1.0
            
        # 计算概率
        probabilities = []
        for e in energies:
            p = e / partition_func
            probabilities.append(p)
            
        return {
            'probabilities': probabilities,
            'partition_function': partition_func,
            'most_probable_state': energy_levels[probabilities.index(max(probabilities))] if probabilities else 0,
            'expected_energy': sum(E * p for E, p in zip(energy_levels, probabilities))
        }
        
    def calculate_gibbs_free_energy(self, H, T, S):
        """计算吉布斯自由能 G = H - TS"""
        G = H - T * S
        return G
        
    def predict_phase_transition(self, T, S):
        """预测相变"""
        T_critical = THERMO_PARAMS['phase_critical_temp']
        
        # 计算dG/dt
        dG = -S * (T - T_critical)  # 简化的dG估计
        
        # 相变信号
        if abs(dG) < 0.1:
            return {'transition': True, 'type': 'critical', 'stability': 'unstable'}
        elif dG < 0:
            return {'transition': False, 'type': 'spontaneous', 'stability': 'stable'}
        else:
            return {'transition': False, 'type': 'non_spontaneous', 'stability': 'metastable'}

# ============================================
# Kinetic Energy Analysis
# ============================================
class KineticEnergyAnalyzer:
    """动能分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.volumes = [d['volume'] for d in data]
        
    def calculate_price_kinetic_energy(self, window=20):
        """计算价格动能 KE = ½mv²"""
        if len(self.data) < window + 1:
            return 0.0
            
        # 价格变化率作为"速度"
        velocities = []
        for i in range(1, min(window + 1, len(self.closes))):
            v = (self.closes[-i] - self.closes[-i-1]) / self.closes[-i-1]
            velocities.append(v)
            
        if not velocities:
            return 0.0
            
        # 速度 = 价格变化率
        v_squared = [v ** 2 for v in velocities]
        avg_v2 = mean(v_squared)
        
        # 动能 = ½ × v²
        ke = 0.5 * avg_v2
        
        return min(1.0, ke * 100)  # 归一化
        
    def calculate_volume_kinetic_energy(self, window=20):
        """计算成交量动能"""
        if len(self.volumes) < window + 1:
            return 0.0
            
        recent_vol = self.volumes[-window:]
        avg_vol = mean(self.volumes[-window*3:-window]) if len(self.volumes) >= window*4 else mean(self.volumes)
        
        # 成交量变化率
        vol_velocities = []
        for i in range(1, len(recent_vol)):
            v = (recent_vol[i] - recent_vol[i-1]) / (recent_vol[i-1] + 1)
            vol_velocities.append(v)
            
        if not vol_velocities:
            return 0.0
            
        avg_v2 = mean([v ** 2 for v in vol_velocities])
        ke = 0.5 * avg_v2
        
        return min(1.0, ke * 100)
        
    def calculate_total_kinetic_energy(self, window=20):
        """计算总动能"""
        ke_price = self.calculate_price_kinetic_energy(window)
        ke_volume = self.calculate_volume_kinetic_energy(window)
        
        # 体积加权
        total_ke = ke_price * 0.7 + ke_volume * 0.3
        
        return min(1.0, total_ke)
        
    def classify_kinetic_energy(self, ke):
        """动能分类"""
        if ke > 0.8:
            return 'extreme', '极强动能'
        elif ke > 0.5:
            return 'high', '高动能'
        elif ke > 0.2:
            return 'medium', '中动能'
        elif ke > 0.05:
            return 'low', '低动能'
        else:
            return 'minimal', '极低动能'

# ============================================
# Heat Cycle Analysis
# ============================================
class HeatCycleAnalyzer:
    """热循环分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        
    def detect_heat_cycle(self):
        """检测热力学周期"""
        if len(self.data) < 100:
            return self._default_cycle()
            
        # 分析温度历史
        temp_analyzer = TemperatureAnalyzer(self.data)
        temperatures = []
        
        for i in range(20, len(self.data), 10):
            T = temp_analyzer.calculate_composite_temperature(20)
            temperatures.append({
                'index': i,
                'temperature': T,
                'time': self.data[i]['time']
            })
            
        if len(temperatures) < 5:
            return self._default_cycle()
            
        # 找温度周期
        max_temp = max(t['temperature'] for t in temperatures)
        min_temp = min(t['temperature'] for t in temperatures)
        avg_temp = mean([t['temperature'] for t in temperatures])
        
        # 当前温度位置
        current_T = temperatures[-1]['temperature']
        
        # 热循环阶段
        if current_T > avg_temp * 1.3:
            phase = 'cooling'
            next_phase = 'cold'
        elif current_T < avg_temp * 0.7:
            phase = 'heating'
            next_phase = 'hot'
        else:
            phase = 'stable'
            next_phase = 'stable'
            
        # 周期长度估算
        temp_changes = [temperatures[i+1]['temperature'] - temperatures[i]['temperature'] 
                        for i in range(len(temperatures)-1)]
        
        zero_crossings = sum(1 for tc in temp_changes if tc * (tc + 1) < 0)  # 符号变化
        
        cycle_length = len(temperatures) / max(1, zero_crossings) if zero_crossings > 0 else len(temperatures)
        
        return {
            'current_phase': phase,
            'next_phase': next_phase,
            'current_temperature': current_T,
            'average_temperature': avg_temp,
            'max_temperature': max_temp,
            'min_temperature': min_temp,
            'cycle_length': cycle_length * 10,  # 转换回数据点数
            'heat_content': self._calculate_heat_content(temperatures)
        }
        
    def _calculate_heat_content(self, temperatures):
        """计算热量含量"""
        if not temperatures:
            return 0
            
        # 积分方式估算热量
        total_heat = sum(t['temperature'] for t in temperatures)
        return total_heat / len(temperatures)
        
    def _default_cycle(self):
        return {
            'current_phase': 'unknown',
            'next_phase': 'unknown',
            'current_temperature': 0.5,
            'average_temperature': 0.5,
            'max_temperature': 1.0,
            'min_temperature': 0.0,
            'cycle_length': 100,
            'heat_content': 0.5
        }
        
    def predict_next_turning_point(self, cycle_data):
        """预测下次转折点"""
        if not cycle_data or cycle_data['cycle_length'] == 0:
            return {'time': None, 'type': None, 'probability': 0.3}
            
        # 基于周期预测
        cycle_len = cycle_data['cycle_length']
        last_time = self.data[-1]['time']
        
        # 下次转折时间
        next_time = last_time + cycle_len * 0.5  # 半周期后
            
        # 基于温度趋势判断类型
        if cycle_data['current_phase'] == 'heating':
            next_type = 'top'  # 加热到顶部
        elif cycle_data['current_phase'] == 'cooling':
            next_type = 'bottom'  # 冷却到底部
        else:
            next_type = 'consolidation'
            
        return {
            'time': next_time,
            'time_str': datetime.fromtimestamp(next_time).strftime('%Y-%m-%d %H:%M'),
            'type': next_type,
            'probability': 0.6,
            'phase': cycle_data['current_phase']
        }

# ============================================
# Boundary Analysis
# ============================================
class BoundaryAnalyzer:
    """热力学边界分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        
    def find_thermal_boundaries(self):
        """找出热力学边界"""
        if len(self.data) < 50:
            return self._default_boundaries()
            
        # 局部极值
        highs = []
        lows = []
        
        for i in range(10, len(self.closes) - 10):
            if self.closes[i] == max(self.closes[i-10:i+11]):
                highs.append((i, self.closes[i]))
            if self.closes[i] == min(self.closes[i-10:i+11]):
                lows.append((i, self.closes[i]))
                
        if not highs or not lows:
            return self._default_boundaries()
            
        # 边界
        upper = max(h for _, h in highs[-20:])
        lower = min(l for _, l in lows[-20:])
        mid = (upper + lower) / 2
        
        # 边界强度
        upper_touches = sum(1 for i, h in highs[-20:] if h >= upper * 0.98)
        lower_touches = sum(1 for i, l in lows[-20:] if l <= lower * 1.02)
        
        # 热传导系数
        kappa = THERMO_PARAMS['boundary_conductivity']
        
        # 边界类型
        if upper_touches > 3:
            upper_type = 'adiabatic'  # 绝热边界, 难以穿透
        else:
            upper_type = 'permeable'  # 可渗透边界
            
        if lower_touches > 3:
            lower_type = 'adiabatic'
        else:
            lower_type = 'permeable'
            
        return {
            'upper': upper,
            'lower': lower,
            'mid': mid,
            'upper_type': upper_type,
            'lower_type': lower_type,
            'upper_strength': min(1.0, upper_touches / 10),
            'lower_strength': min(1.0, lower_touches / 10),
            'conductivity': kappa,
            'heat_resistance': 1.0 / (kappa + 0.001)
        }
        
    def _default_boundaries(self):
        current = self.closes[-1] if self.closes else 100
        return {
            'upper': current * 1.05,
            'lower': current * 0.95,
            'mid': current,
            'upper_type': 'permeable',
            'lower_type': 'permeable',
            'upper_strength': 0.3,
            'lower_strength': 0.3,
            'conductivity': 0.1,
            'heat_resistance': 10.0
        }

# ============================================
# Thermo Engine
# ============================================
class ThermoEngine:
    """热力学交易分析引擎"""
    
    def __init__(self):
        self.params = THERMO_PARAMS
        
    def analyze(self, coin, interval='1h', period='90d'):
        """完整热力学分析"""
        period_map = {'7d': 168, '30d': 720, '90d': 2160}
        limit = min(period_map.get(period, 720), 500)
        
        data = get_price_data(coin, interval, limit)
        
        if not data:
            return None
            
        # 1. 温度分析
        temp_analyzer = TemperatureAnalyzer(data)
        temperature = temp_analyzer.calculate_composite_temperature()
        temp_phase, temp_phase_name, temp_level = temp_analyzer.get_temperature_phase(temperature)
        
        # 2. 熵分析
        entropy_analyzer = EntropyAnalyzer(data)
        entropy, order = entropy_analyzer.calculate_shannon_entropy()
        conditional_entropy = entropy_analyzer.calculate_conditional_entropy()
        entropy_spike, entropy_change = entropy_analyzer.detect_entropy_spike()
        
        # 3. 玻尔兹曼分析
        boltz_analyzer = BoltzmannAnalyzer(data)
        boltz_probs = boltz_analyzer.calculate_boltzmann_probabilities()
        
        # 4. 动能分析
        ke_analyzer = KineticEnergyAnalyzer(data)
        kinetic_energy = ke_analyzer.calculate_total_kinetic_energy()
        ke_level, ke_name = ke_analyzer.classify_kinetic_energy(kinetic_energy)
        
        # 5. 热循环
        heat_analyzer = HeatCycleAnalyzer(data)
        heat_cycle = heat_analyzer.detect_heat_cycle()
        next_turning = heat_analyzer.predict_next_turning_point(heat_cycle)
        
        # 6. 边界
        boundary_analyzer = BoundaryAnalyzer(data)
        boundaries = boundary_analyzer.find_thermal_boundaries()
        
        # 7. 相变预测
        phase_info = boltz_analyzer.predict_phase_transition(temperature, entropy)
        
        # 8. 综合预测
        prediction = self._make_prediction(
            temperature, temp_phase, entropy, order,
            kinetic_energy, ke_level, heat_cycle, next_turning, phase_info
        )
        
        return {
            'coin': coin,
            'timeframe': interval,
            'period': period,
            'temperature': {
                'value': temperature,
                'phase': temp_phase,
                'phase_name': temp_phase_name,
                'level': temp_level
            },
            'entropy': {
                'value': entropy,
                'order': order,
                'conditional': conditional_entropy,
                'spike': entropy_spike,
                'change': entropy_change
            },
            'boltzmann': boltz_probs,
            'kinetic_energy': {
                'value': kinetic_energy,
                'level': ke_level,
                'name': ke_name
            },
            'heat_cycle': heat_cycle,
            'boundaries': boundaries,
            'phase_transition': phase_info,
            'next_turning_point': next_turning,
            'prediction': prediction
        }
        
    def _make_prediction(self, temperature, temp_phase, entropy, order,
                        kinetic_energy, ke_level, heat_cycle, next_turning, phase_info):
        """生成预测"""
        # 综合评分
        heat_score = temperature * 0.3 + kinetic_energy * 0.3 + (1 - order) * 0.2
        
        # 转折概率
        turning_prob = 0.3
        
        if phase_info['transition']:
            turning_prob += 0.3
        if entropy > 0.7:
            turning_prob += 0.2
        if temperature > 1.5 or temperature < 0.3:
            turning_prob += 0.2
            
        turning_prob = min(0.95, turning_prob)
        
        # 操作建议
        if temperature > 2.0:
            action = 'COOL_DOWN'  # 过热, 观望或反向
            direction = 'sell'
        elif temperature < 0.3:
            action = 'HEAT_UP'  # 过冷, 可能突破
            direction = 'buy'
        elif heat_cycle['current_phase'] == 'heating':
            action = 'RIDE_HEAT'
            direction = 'buy'
        elif heat_cycle['current_phase'] == 'cooling':
            action = 'REDUCE_HEAT'
            direction = 'sell'
        elif phase_info['transition']:
            action = 'PHASE_CHANGE'
            direction = 'adjust'
        else:
            action = 'MAINTAIN'
            direction = 'hold'
            
        return {
            'action': action,
            'direction': direction,
            'turning_probability': turning_prob,
            'heat_score': heat_score,
            'confidence': (1 - order) * turning_prob,
            'reasoning': self._generate_reasoning(
                temperature, temp_phase, entropy, order,
                kinetic_energy, ke_level, heat_cycle, phase_info
            )
        }
        
    def _generate_reasoning(self, temperature, temp_phase, entropy, order,
                           kinetic_energy, ke_level, heat_cycle, phase_info):
        """生成推理"""
        parts = []
        
        # 温度
        parts.append(f"温度{temperature:.2f}({temp_phase})")
        
        # 熵
        if entropy > 0.7:
            parts.append("高熵无序")
        elif entropy < 0.3:
            parts.append("低熵有序")
        else:
            parts.append("中熵稳定")
            
        # 动能
        parts.append(f"动能{ke_level}")
        
        # 热循环
        if heat_cycle['current_phase'] == 'heating':
            parts.append("加热中")
        elif heat_cycle['current_phase'] == 'cooling':
            parts.append("冷却中")
            
        # 相变
        if phase_info['transition']:
            parts.append("相变临界")
            
        return "; ".join(parts)

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-thermo - 热力学交易分析")
        print("Usage:")
        print("  python thermo_engine.py <coin> [interval] [period]")
        print("Example:")
        print("  python thermo_engine.py BTC 1h 90d")
        sys.exit(1)
        
    coin = sys.argv[1].upper()
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    period = sys.argv[3] if len(sys.argv) > 3 else '90d'
    
    print(f"\n🌡️ 热力学分析: {coin} ({interval}, {period})")
    print("="*60)
    
    engine = ThermoEngine()
    result = engine.analyze(coin, interval, period)
    
    if result:
        temp = result['temperature']
        print(f"\n🌡️ 市场温度:")
        print(f"   温度值: {temp['value']:.3f}")
        print(f"   阶段: {temp['phase_name']} ({temp['phase']})")
        print(f"   级别: {temp['level']}")
        
        entropy = result['entropy']
        print(f"\n📊 熵分析:")
        print(f"   熵值: {entropy['value']:.4f}")
        print(f"   有序度: {entropy['order']:.1%}")
        print(f"   条件熵: {entropy['conditional']:.4f}")
        print(f"   熵突增: {'是' if entropy['spike'] else '否'} ({entropy['change']:.3f})")
        
        boltz = result['boltzmann']
        print(f"\n⚛️ 玻尔兹曼分布:")
        print(f"   最可能状态能量: {boltz['most_probable_state']:.4f}")
        print(f"   期望能量: {boltz['expected_energy']:.4f}")
        print(f"   配分函数: {boltz['partition_function']:.4f}")
        
        ke = result['kinetic_energy']
        print(f"\n⚡ 动能:")
        print(f"   动能值: {ke['value']:.4f}")
        print(f"   级别: {ke['name']} ({ke['level']})")
        
        cycle = result['heat_cycle']
        print(f"\n🔥 热循环:")
        print(f"   当前阶段: {cycle['current_phase']}")
        print(f"   平均温度: {cycle['average_temperature']:.3f}")
        print(f"   热量: {cycle['heat_content']:.3f}")
        
        boundaries = result['boundaries']
        print(f"\n�边界条件:")
        print(f"   上边界: ${boundaries['upper']:.2f} ({boundaries['upper_type']})")
        print(f"   下边界: ${boundaries['lower']:.2f} ({boundaries['lower_type']})")
        
        pt = result['phase_transition']
        print(f"\n🔄 相变:")
        print(f"   相变: {'是' if pt['transition'] else '否'}")
        print(f"   类型: {pt['type']}")
        print(f"   稳定性: {pt['stability']}")
        
        turning = result['next_turning_point']
        print(f"\n🎯 转折点预测:")
        if turning['time']:
            print(f"   时间: {turning['time_str']}")
            print(f"   类型: {turning['type']}")
            print(f"   概率: {turning['probability']:.0%}")
            
        pred = result['prediction']
        print(f"\n💡 预测操作:")
        print(f"   操作: {pred['action']}")
        print(f"   方向: {pred['direction']}")
        print(f"   转折概率: {pred['turning_probability']:.0%}")
        print(f"   置信度: {pred['confidence']:.0%}")
        print(f"   推理: {pred['reasoning']}")
    else:
        print("数据获取失败")
