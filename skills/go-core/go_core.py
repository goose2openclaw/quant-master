#!/usr/bin/env python3
"""
go-core v2.0 - 加密量化预测核心引擎 (增强版)
=============================================
优化阶段:
- Phase 1: 性能优化 (并行计算, 缓存, 增量计算)
- Phase 2: 准确性提升 (自适应权重, 多时间框架共振)
- Phase 3: 新功能扩展 (订单簿, 清算预测, 跨交易所)
"""
import math, json, time, random, urllib.request, sys, threading, hashlib
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 默认权重
DEFAULT_WEIGHTS = {
    'technical': 0.20,
    'quantum': 0.10,
    'thermo': 0.10,
    'human': 0.10,
    'contrarian': 0.10,
    'institutional': 0.15,
    'mirofish': 0.15,
}

# 自适应权重配置 - Phase 2
MARKET_STATE_WEIGHTS = {
    'bull': {
        'technical': 0.25, 'momentum': 0.20, 'quantum': 0.08,
        'thermo': 0.08, 'human': 0.10, 'contrarian': 0.07, 'institutional': 0.12, 'mirofish': 0.10
    },
    'bear': {
        'technical': 0.15, 'momentum': 0.10, 'quantum': 0.12,
        'thermo': 0.12, 'human': 0.08, 'contrarian': 0.18, 'institutional': 0.15, 'mirofish': 0.10
    },
    'sideways': {
        'technical': 0.20, 'mean_reversion': 0.20, 'quantum': 0.10,
        'thermo': 0.10, 'human': 0.10, 'contrarian': 0.10, 'institutional': 0.10, 'mirofish': 0.10
    },
    'high_vol': {
        'technical': 0.15, 'volatility': 0.20, 'quantum': 0.12,
        'thermo': 0.15, 'contrarian': 0.15, 'institutional': 0.13, 'mirofish': 0.10
    },
    'low_vol': {
        'technical': 0.25, 'mean_reversion': 0.15, 'quantum': 0.10,
        'thermo': 0.08, 'human': 0.12, 'contrarian': 0.10, 'institutional': 0.10, 'mirofish': 0.10
    }
}

# 币种分类
COIN_TIERS = {
    'main': ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT', 'LINK', 'UNI', 'AVAX', 'ATOM', 'LTC', 'ETC', 'AAVE', 'APT', 'NEAR'],
    'meme': ['PEPE', 'SHIB', 'FLOKI', 'WIF', 'BOME', 'NEIRO', 'TURBO', 'PUMP', 'MOG', 'BONK', 'AI16Z', 'FWOG'],
    'mid': ['APT', 'ARB', 'OP', 'INJ', 'SUI', 'SEI', 'TIA', 'RENDER', 'GRT', 'AAVE', 'MKR', 'SNX', 'LDO', 'RPL']
}

# ============================================
# Phase 1: Cache System (性能优化)
# ============================================
class DataCache:
    """高性能缓存系统"""
    
    def __init__(self, max_size=100, ttl=300):
        self._cache = {}
        self._timestamps = {}
        self._max_size = max_size
        self._ttl = ttl  # seconds
        self._lock = threading.RLock()
    
    def _make_key(self, prefix, *args, **kwargs):
        key_str = prefix + "_" + "_".join(map(str, args))
        if kwargs:
            key_str += "_" + "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key):
        with self._lock:
            if key in self._cache:
                if time.time() - self._timestamps.get(key, 0) < self._ttl:
                    return copy.deepcopy(self._cache[key])
                else:
                    del self._cache[key]
                    del self._timestamps[key]
        return None
    
    def set(self, key, value):
        with self._lock:
            if len(self._cache) >= self._max_size:
                oldest = min(self._timestamps, key=self._timestamps.get)
                del self._cache[oldest]
                del self._timestamps[oldest]
            self._cache[key] = copy.deepcopy(value)
            self._timestamps[key] = time.time()
    
    def invalidate(self, key_prefix=None):
        with self._lock:
            if key_prefix is None:
                self._cache.clear()
                self._timestamps.clear()
            else:
                keys = [k for k in self._cache if k.startswith(key_prefix)]
                for k in keys:
                    del self._cache[k]
                    del self._timestamps[k]

# 全局缓存
GLOBAL_CACHE = DataCache(max_size=500, ttl=60)

# ============================================
# Data Utilities
# ============================================
def api_get(url, timeout=10):
    cache_key = GLOBAL_CACHE._make_key('api_get', url)
    cached = GLOBAL_CACHE.get(cache_key)
    if cached is not None:
        return cached
    
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        result = json.loads(opener.open(urllib.request.Request(url), timeout=timeout).read().decode())
        GLOBAL_CACHE.set(cache_key, result)
        return result
    except Exception as e:
        return None

def get_klines(symbol, interval='1h', limit=500):
    cache_key = GLOBAL_CACHE._make_key('klines', symbol, interval, limit)
    cached = GLOBAL_CACHE.get(cache_key)
    if cached is not None:
        return cached
    result = api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}') or []
    if result:
        GLOBAL_CACHE.set(cache_key, result)
    return result

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

# Phase 3: 跨交易所支持
EXCHANGES = {
    'binance': 'https://api.binance.com',
    'okx': 'https://www.okx.com',
    'bybit': 'https://api.bybit.com',
    'gate': 'https://api.gateio.tv'
}

def get_cross_exchange_prices(coin):
    """Phase 3: 跨交易所价格对比"""
    prices = {}
    for exchange, base_url in EXCHANGES.items():
        try:
            if exchange == 'binance':
                url = f'{base_url}/api/v3/ticker/price?symbol={coin}USDT'
            else:
                url = f'{base_url}/api/v3/ticker/price?symbol={coin}USDT'
            data = api_get(url)
            if data and 'price' in data:
                prices[exchange] = float(data['price'])
        except:
            pass
    return prices

# ============================================
# Technical Analysis
# ============================================
class TechnicalAnalyzer:
    """技术分析"""
    
    @staticmethod
    def rsi(closes, period=14):
        if len(closes) < period + 1:
            return 50
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        return 100 - (100 / (1 + avg_gain / avg_loss))
    
    @staticmethod
    def macd(closes, fast=12, slow=26, signal=9):
        if len(closes) < slow:
            return 0, 0, 0
        ema_fast = sum(closes[-fast:]) / fast
        ema_slow = sum(closes[-slow:]) / slow
        macd_line = ema_fast - ema_slow
        signal_line = macd_line * 0.9
        return macd_line, signal_line, ema_fast - ema_slow
    
    @staticmethod
    def bollinger_bands(closes, period=20, std_dev=2):
        if len(closes) < period:
            return None, None, None
        recent = closes[-period:]
        mid = sum(recent) / len(recent)
        s = math.sqrt(sum((v - mid) ** 2 for v in recent) / len(recent))
        return mid + std_dev * s, mid, mid - std_dev * s
    
    @staticmethod
    def atr(data, period=14):
        if len(data) < period + 1:
            return 0
        trs = []
        for i in range(1, min(len(data), period + 1)):
            tr = max(
                data[i]['high'] - data[i]['low'],
                abs(data[i]['high'] - data[i-1]['close']),
                abs(data[i]['low'] - data[i-1]['close'])
            )
            trs.append(tr)
        return sum(trs) / len(trs) if trs else 0
    
    @staticmethod
    def adx(closes, period=14):
        if len(closes) < period * 2:
            return 25
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        adx_val = min(100, std(returns[-period:]) * 500)
        return adx_val
    
    @staticmethod
    def stochastic(highs, lows, closes, k_period=14, d_period=3):
        if len(closes) < k_period:
            return 50, 50
        recent_close = closes[-1]
        lowest_low = min(lows[-k_period:])
        highest_high = max(highs[-k_period:])
        if highest_high == lowest_low:
            return 50, 50
        k = (recent_close - lowest_low) / (highest_high - lowest_low) * 100
        return k, k

# ============================================
# Quantum Analysis
# ============================================
class QuantumAnalyzer:
    """量子力学分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
    
    def analyze(self):
        if len(self.data) < 50:
            return self._default()
        
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(1, len(self.closes))]
        
        volatility = std(returns) if returns else 0.01
        energy = volatility ** 2
        
        levels = [0.005, 0.02, 0.05, 0.1, 0.2]
        level = 0
        for i, e in enumerate(levels):
            if energy >= e:
                level = i
        
        coherence = max(0.3, min(0.95, 1 - volatility * 10))
        
        tunneling = 0.0
        recent = returns[-10:] if len(returns) >= 10 else returns
        if recent:
            max_return = max(abs(r) for r in recent)
            if max_return > volatility * 2:
                tunneling = min(0.7, max_return)
        
        highs = [d['high'] for d in self.data[-50:]]
        lows = [d['low'] for d in self.data[-50:]]
        
        return {
            'state': f'|{level}⟩',
            'state_name': ['基态', '激发态1', '激发态2', '激发态3', '高激发'][min(level, 4)],
            'energy': energy,
            'coherence': coherence,
            'tunneling': tunneling,
            'upper_bound': max(highs),
            'lower_bound': min(lows),
            'confidence': coherence
        }
    
    def _default(self):
        return {
            'state': '|0⟩', 'state_name': '基态', 'energy': 0, 'coherence': 0.5,
            'tunneling': 0, 'upper_bound': 0, 'lower_bound': 0, 'confidence': 0.5
        }

# ============================================
# Thermo Analysis
# ============================================
class ThermoAnalyzer:
    """热力学分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.volumes = [d['volume'] for d in data]
    
    def analyze(self):
        if len(self.data) < 20:
            return self._default()
        
        closes = self.closes
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        
        volatility = std(returns) if returns else 0.01
        trend = (closes[-1] - closes[0]) / closes[0] if closes[0] != 0 else 0
        
        # 温度 T = volatility / |trend| * scaling
        if abs(trend) > 0.001:
            temperature = volatility / abs(trend) * 2
        else:
            temperature = volatility * 20
        
        # 相位
        if temperature > 2.0:
            phase = 'plasma'
            phase_name = '等离子态'
        elif temperature > 1.2:
            phase = 'gas'
            phase_name = '气态'
        elif temperature > 0.7:
            phase = 'liquid'
            phase_name = '液态'
        elif temperature > 0.3:
            phase = 'solid'
            phase_name = '固态'
        else:
            phase = 'frozen'
            phase_name = '极冷'
        
        # 熵
        if len(returns) >= 10:
            hist = [0] * 10
            for r in returns[-10:]:
                idx = min(9, int(abs(r) * 100))
                hist[idx] += 1
            total = sum(hist)
            entropy = -sum((h/total * math.log(h/total + 1e-10) for h in hist if h > 0))
        else:
            entropy = 0
        
        return {
            'temperature': temperature,
            'phase': phase,
            'phase_name': phase_name,
            'entropy': entropy,
            'trend': trend,
            'volatility': volatility,
            'confidence': 1 - min(entropy / 3, 0.5)
        }
    
    def _default(self):
        return {'temperature': 1.0, 'phase': 'liquid', 'phase_name': '液态', 
                'entropy': 1.0, 'trend': 0, 'volatility': 0.01, 'confidence': 0.5}

# ============================================
# Contrarian Analysis
# ============================================
class ContrarianAnalyzer:
    """反人性分析"""
    
    def __init__(self, data):
        self.data = data
    
    def analyze(self):
        if len(self.data) < 20:
            return self._default()
        
        closes = [d['close'] for d in self.data]
        volumes = [d['volume'] for d in self.data]
        
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        
        # 人性因素
        fomo = 0.0
        fear = 0.0
        herd = 0.0
        
        if len(returns) >= 10:
            recent = returns[-10:]
            if sum(1 for r in recent if r > 0) > 6:
                fomo = 0.7
            if sum(1 for r in recent if r < 0) > 6:
                fear = 0.7
            
            if abs(sum(recent)) > std(recent) * 3:
                herd = 0.8
        
        human_ratio = (fomo + fear + herd) / 3
        contrarian_ratio = 1 - human_ratio
        
        if human_ratio > 0.8:
            phase = 'EXTREME_GREED' if fomo > fear else 'EXTREME_FEAR'
        elif human_ratio > 0.65:
            phase = 'GREED' if fomo > fear else 'FEAR'
        elif human_ratio > 0.35:
            phase = 'NEUTRAL'
        else:
            phase = 'CONTRARIAN'
        
        return {
            'human_ratio': human_ratio,
            'contrarian_ratio': contrarian_ratio,
            'fomo': fomo,
            'fear': fear,
            'herd': herd,
            'phase': phase,
            'confidence': 0.5 + contrarian_ratio * 0.3
        }
    
    def _default(self):
        return {'human_ratio': 0.5, 'contrarian_ratio': 0.5, 'fomo': 0, 'fear': 0,
                'herd': 0, 'phase': 'NEUTRAL', 'confidence': 0.5}

# ============================================
# Institutional Analysis (Phase 3)
# ============================================
class InstitutionalAnalyzer:
    """机构侦测分析"""
    
    def __init__(self, data):
        self.data = data
    
    def analyze(self):
        if len(self.data) < 50:
            return self._default()
        
        closes = [d['close'] for d in self.data]
        volumes = [d['volume'] for d in self.data]
        
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        
        # 订单簿分析 (模拟)
        bid_ask_spread = std(returns[-20:]) * 2
        
        # 成交量分析
        avg_volume = sum(volumes[-20:]) / 20
        recent_volume = volumes[-1] if volumes else avg_volume
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        
        # 机构类型判断
        market_makers = 0.0
        trend_followers = 0.0
        mean_reverters = 0.0
        
        if bid_ask_spread < 0.01:
            market_makers = 0.6
        
        if abs(returns[-1]) > std(returns[-20:]) * 2 and volume_ratio > 1.5:
            trend_followers = 0.7
        
        if abs(returns[-1]) < std(returns[-20:]) * 0.5:
            mean_reverters = 0.6
        
        return {
            'market_makers': market_makers,
            'trend_followers': trend_followers,
            'mean_reverters': mean_reverters,
            'volume_ratio': volume_ratio,
            'bid_ask_spread': bid_ask_spread,
            'dominant': max(['market_makers', 'trend_followers', 'mean_reverters'],
                          key=lambda x: eval(x)) if any([market_makers, trend_followers, mean_reverters]) else 'unknown',
            'confidence': 0.6
        }
    
    def _default(self):
        return {'market_makers': 0.3, 'trend_followers': 0.3, 'mean_reverters': 0.3,
                'volume_ratio': 1.0, 'bid_ask_spread': 0, 'dominant': 'unknown', 'confidence': 0.5}

# ============================================
# Liquidation Predictor (Phase 3)
# ============================================
class LiquidationPredictor:
    """清算预测"""
    
    @staticmethod
    def predict_liquidation(coin, entry_price, position_type='long', leverage=1):
        """
        预测清算价格
        position_type: 'long' or 'short'
        leverage: 杠杆倍数
        """
        if position_type == 'long':
            liquidation_price = entry_price * (1 - 1 / leverage * 0.8)
        else:
            liquidation_price = entry_price * (1 + 1 / leverage * 0.8)
        
        # 获取当前价格
        current_price = float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={coin}USDT')['price'])
        
        # 计算距离清算的距离
        distance_pct = abs(current_price - liquidation_price) / current_price * 100
        
        return {
            'liquidation_price': liquidation_price,
            'current_price': current_price,
            'distance_pct': distance_pct,
            'danger_level': 'HIGH' if distance_pct < 5 else 'MEDIUM' if distance_pct < 15 else 'LOW'
        }

# ============================================
# Market State Detector (Phase 2)
# ============================================
class MarketStateDetector:
    """市场状态检测 - Phase 2"""
    
    @staticmethod
    def detect(closes, volumes):
        if len(closes) < 50:
            return 'sideways'
        
        # 计算趋势
        ma_short = sum(closes[-20:]) / 20
        ma_long = sum(closes[-50:]) / 50
        trend = (ma_short - ma_long) / ma_long
        
        # 计算波动率
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = std(returns[-20:]) if len(returns) >= 20 else 0.01
        
        # 计算成交量变化
        avg_vol = sum(volumes[-20:]) / 20
        recent_vol = volumes[-1] if volumes else avg_vol
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        # 状态判断
        if trend > 0.02 and volatility > 0.02:
            return 'bull'
        elif trend < -0.02 and volatility > 0.02:
            return 'bear'
        elif volatility < 0.01 and vol_ratio < 0.8:
            return 'low_vol'
        elif volatility > 0.05:
            return 'high_vol'
        else:
            return 'sideways'

# ============================================
# Multi-Timeframe Analyzer (Phase 2)
# ============================================
class MultiTimeframeAnalyzer:
    """多时间框架共振分析 - Phase 2"""
    
    def __init__(self, coin):
        self.coin = coin
    
    def analyze(self):
        timeframes = {
            '1h': {'interval': '1h', 'limit': 100},
            '4h': {'interval': '4h', 'limit': 100},
            '1d': {'interval': '1d', 'limit': 90}
        }
        
        results = {}
        
        def analyze_tf(tf_name, tf_config):
            data = get_price_data(self.coin, tf_config['interval'], tf_config['limit'])
            if len(data) < 20:
                return None
            
            closes = [d['close'] for d in data]
            rsi = TechnicalAnalyzer.rsi(closes)
            
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            trend = (closes[-1] - closes[-20]) / closes[-20] if len(closes) >= 20 else 0
            
            return {
                'rsi': rsi,
                'trend': trend,
                'signal': 'buy' if rsi < 40 and trend > 0 else 'sell' if rsi > 60 and trend < 0 else 'neutral'
            }
        
        # 并行分析各时间框架
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(analyze_tf, tf, cfg): tf for tf, cfg in timeframes.items()}
            for future in as_completed(futures):
                tf = futures[future]
                try:
                    results[tf] = future.result()
                except:
                    results[tf] = None
        
        # 计算共振信号
        buy_count = sum(1 for r in results.values() if r and r['signal'] == 'buy')
        sell_count = sum(1 for r in results.values() if r and r['signal'] == 'sell')
        
        if buy_count >= 2:
            resonance_signal = 'buy'
            confidence = 0.7 + buy_count * 0.1
        elif sell_count >= 2:
            resonance_signal = 'sell'
            confidence = 0.7 + sell_count * 0.1
        else:
            resonance_signal = 'neutral'
            confidence = 0.5
        
        return {
            'timeframes': results,
            'resonance_signal': resonance_signal,
            'confidence': min(confidence, 0.95),
            'buy_count': buy_count,
            'sell_count': sell_count
        }

# ============================================
# Mirofish Agent Simulation
# ============================================
class MirofishAgent:
    """Mirofish智能体"""
    
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.decision_power = random.uniform(0.5, 1.0)
    
    def vote(self, data, coin_type='main'):
        closes = [d['close'] for d in data[-100:]]
        if len(closes) < 20:
            return 'hold', 0.5
        
        rsi = TechnicalAnalyzer.rsi(closes)
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        
        # RSI超卖/超买信号
        signal = 'hold'
        confidence = 0.5
        
        if coin_type == 'meme':
            if rsi < 30:
                signal = 'buy'
                confidence = 0.7 + (30 - rsi) / 100
            elif rsi > 80:
                signal = 'sell'
                confidence = 0.7 + (rsi - 80) / 100
        else:
            if rsi < 35:
                signal = 'buy'
                confidence = 0.6 + (35 - rsi) / 100
            elif rsi > 70:
                signal = 'sell'
                confidence = 0.6 + (rsi - 70) / 100
        
        confidence = min(confidence * self.decision_power, 1.0)
        return signal, confidence

# ============================================
# Main GoCore Class
# ============================================
class GoCore:
    """go-core 核心引擎 v2.0"""
    
    def __init__(self, num_agents=300):
        self.num_agents = num_agents
        self.agents = [MirofishAgent(i) for i in range(num_agents)]
        self.cache = DataCache(max_size=200, ttl=30)
        self.market_state = 'sideways'
        self.weights = DEFAULT_WEIGHTS.copy()
    
    def _detect_market_state(self, data):
        """检测市场状态"""
        closes = [d['close'] for d in data]
        volumes = [d['volume'] for d in data]
        self.market_state = MarketStateDetector.detect(closes, volumes)
        
        # 更新自适应权重
        if self.market_state in MARKET_STATE_WEIGHTS:
            self.weights = MARKET_STATE_WEIGHTS[self.market_state].copy()
    
    def _parallel_analyze(self, data):
        """Phase 1: 并行分析各维度"""
        results = {}
        
        def analyze_quantum():
            return QuantumAnalyzer(data).analyze()
        
        def analyze_thermo():
            return ThermoAnalyzer(data).analyze()
        
        def analyze_contrarian():
            return ContrarianAnalyzer(data).analyze()
        
        def analyze_institutional():
            return InstitutionalAnalyzer(data).analyze()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(analyze_quantum): 'quantum',
                executor.submit(analyze_thermo): 'thermo',
                executor.submit(analyze_contrarian): 'contrarian',
                executor.submit(analyze_institutional): 'institutional'
            }
            
            for future in as_completed(futures):
                component = futures[future]
                try:
                    results[component] = future.result()
                except Exception as e:
                    results[component] = {'confidence': 0.5}
        
        return results
    
    def predict(self, coin, interval='1h', period='90d', custom_weights=None):
        """预测"""
        cache_key = f"predict_{coin}_{interval}_{period}"
        if custom_weights is None:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        limit = {'7d': 200, '30d': 500, '90d': 1000}.get(period, 500)
        data = get_price_data(coin, interval, limit)
        
        if len(data) < 20:
            return {'signal': 'hold', 'confidence': 0.5, 'score': 0, 'reasoning': ['数据不足']}
        
        # 检测市场状态
        self._detect_market_state(data)
        
        # Phase 1: 并行分析
        components = self._parallel_analyze(data)
        
        # Phase 2: 多时间框架共振
        mtf = MultiTimeframeAnalyzer(coin)
        mtf_result = mtf.analyze()
        
        # Mirofish投票
        coin_type = 'meme' if coin in COIN_TIERS.get('meme', []) else 'main'
        votes = {'buy': 0, 'sell': 0, 'hold': 0}
        total_confidence = 0
        
        for agent in self.agents:
            signal, confidence = agent.vote(data, coin_type)
            votes[signal] += confidence
            total_confidence += confidence
        
        # 归一化
        for k in votes:
            votes[k] = votes[k] / total_confidence if total_confidence > 0 else 0
        
        mirofish_signal = max(votes, key=votes.get)
        mirofish_confidence = votes[mirofish_signal]
        
        # 加权组合
        weights = custom_weights if custom_weights else self.weights
        
        # 技术分析
        closes = [d['close'] for d in data]
        rsi = TechnicalAnalyzer.rsi(closes)
        tech_signal = 'buy' if rsi < 40 else 'sell' if rsi > 70 else 'neutral'
        tech_confidence = abs(50 - rsi) / 50
        
        # 综合评分
        total_score = 0
        total_weight = 0
        
        signal_scores = {'buy': 0, 'sell': 0, 'neutral': 0}
        
        # 技术因子
        score = tech_confidence * weights.get('technical', 0.2)
        total_score += score * (1 if tech_signal == 'buy' else -1 if tech_signal == 'sell' else 0)
        total_weight += weights.get('technical', 0.2)
        signal_scores['buy' if tech_signal == 'buy' else 'sell' if tech_signal == 'sell' else 'neutral'] += score
        
        # 量子因子
        quantum = components.get('quantum', {})
        q_conf = quantum.get('confidence', 0.5) * weights.get('quantum', 0.1)
        q_signal = 'buy' if quantum.get('tunneling', 0) > 0.3 else 'sell' if quantum.get('coherence', 0) < 0.4 else 'neutral'
        total_score += q_conf * (1 if q_signal == 'buy' else -1 if q_signal == 'sell' else 0)
        total_weight += weights.get('quantum', 0.1)
        signal_scores['buy' if q_signal == 'buy' else 'sell' if q_signal == 'sell' else 'neutral'] += q_conf
        
        # 热力因子
        thermo = components.get('thermo', {})
        t_conf = thermo.get('confidence', 0.5) * weights.get('thermo', 0.1)
        t_signal = 'buy' if thermo.get('phase') in ['frozen', 'solid'] else 'sell' if thermo.get('phase') in ['plasma', 'gas'] else 'neutral'
        total_score += t_conf * (1 if t_signal == 'buy' else -1 if t_signal == 'sell' else 0)
        total_weight += weights.get('thermo', 0.1)
        signal_scores['buy' if t_signal == 'buy' else 'sell' if t_signal == 'sell' else 'neutral'] += t_conf
        
        # 反人性
        contrarian = components.get('contrarian', {})
        c_conf = contrarian.get('contrarian_ratio', 0.5) * weights.get('contrarian', 0.1)
        c_signal = 'buy' if contrarian.get('phase') in ['EXTREME_FEAR', 'CONTRARIAN'] else 'sell' if contrarian.get('phase') in ['EXTREME_GREED', 'GREED'] else 'neutral'
        total_score += c_conf * (1 if c_signal == 'buy' else -1 if c_signal == 'sell' else 0)
        total_weight += weights.get('contrarian', 0.1)
        signal_scores['buy' if c_signal == 'buy' else 'sell' if c_signal == 'sell' else 'neutral'] += c_conf
        
        # Mirofish
        m_conf = mirofish_confidence * weights.get('mirofish', 0.15)
        total_score += m_conf * (1 if mirofish_signal == 'buy' else -1 if mirofish_signal == 'sell' else 0)
        total_weight += weights.get('mirofish', 0.15)
        signal_scores['buy' if mirofish_signal == 'buy' else 'sell' if mirofish_signal == 'sell' else 'neutral'] += m_conf
        
        # 多时间框架共振
        mtf_conf = mtf_result['confidence'] * 0.15
        mtf_signal = mtf_result['resonance_signal']
        total_score += mtf_conf * (1 if mtf_signal == 'buy' else -1 if mtf_signal == 'sell' else 0)
        total_weight += 0.15
        signal_scores['buy' if mtf_signal == 'buy' else 'sell' if mtf_signal == 'sell' else 'neutral'] += mtf_conf
        
        # 归一化
        if total_weight > 0:
            final_score = total_score / total_weight
            normalized_score = (final_score + 1) / 2
        else:
            normalized_score = 0.5
        
        signal = 'buy' if normalized_score > 0.55 else 'sell' if normalized_score < 0.45 else 'neutral'
        confidence = abs(normalized_score - 0.5) * 2
        
        reasoning = []
        if quantum.get('tunneling', 0) > 0.3:
            reasoning.append(f"量子隧穿{quantum['tunneling']:.0%}")
        if thermo.get('phase') in ['plasma', 'frozen']:
            reasoning.append(f"热{thermo['phase_name']}")
        if contrarian.get('phase') in ['EXTREME_GREED', 'EXTREME_FEAR', 'CONTRARIAN']:
            reasoning.append(f"反人性{contrarian['phase']}")
        if mtf_result['resonance_signal'] != 'neutral':
            reasoning.append(f"多周期共振{mtf_result['resonance_signal']}")
        if not reasoning:
            reasoning.append('市场中性')
        
        result = {
            'signal': signal,
            'confidence': min(confidence, 1.0),
            'score': int(normalized_score * 100),
            'reasoning': reasoning,
            'market_state': self.market_state,
            'mirofish_votes': votes,
            'components': components,
            'multi_timeframe': mtf_result
        }
        
        self.cache.set(cache_key, result)
        return result
    
    def scan(self, tier='all', min_score=50):
        """扫描信号"""
        coins = []
        if tier == 'all':
            coins = COIN_TIERS['main'] + COIN_TIERS['meme']
        elif tier == 'meme':
            coins = COIN_TIERS['meme']
        else:
            coins = COIN_TIERS['main']
        
        results = []
        for coin in coins:
            try:
                result = self.predict(coin)
                if result['confidence'] >= min_score / 100:
                    results.append({
                        'coin': coin,
                        'signal': result['signal'],
                        'score': result['score'],
                        'confidence': result['confidence'],
                        'reasoning': result['reasoning']
                    })
            except:
                pass
        
        results.sort(key=lambda x: -x['score'])
        return results

# ============================================
# Utility Functions
# ============================================
def mean(values):
    return sum(values) / len(values) if values else 0

def std(values):
    if len(values) < 2: return 0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))
