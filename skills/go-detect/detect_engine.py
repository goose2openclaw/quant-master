#!/usr/bin/env python3
"""
go-detect - 量化机构侦测与追踪引擎
识别量化机构特征,估算占比,追踪行为,预测转折点
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

# 侦测参数
DETECTION_PARAMS = {
    'min_trades': 1000,
    'lookback_window': 500,
    'fingerprint_window': 50,
    'confidence_threshold': 0.6,
    'activity_threshold': 0.7,
    'wall_detection_sensitivity': 0.8,
}

# 机构类型
INSTITUTION_TYPES = {
    'market_makers': {
        'name': '做市商',
        'weight': 0.25,
        'features': ['spread_control', 'inventory_manage', 'quote_frequency']
    },
    'trend_followers': {
        'name': '趋势跟踪',
        'weight': 0.30,
        'features': ['momentum_drive', 'breakout_sensitive', 'position_build']
    },
    'mean_reverters': {
        'name': '均值回归',
        'weight': 0.20,
        'features': ['reversion_drive', 'overbought_sell', 'oversold_buy']
    },
    'hft': {
        'name': '高频交易',
        'weight': 0.15,
        'features': ['latency_sensitive', 'micro_pattern', 'quote_stuffing']
    },
    'stat_arb': {
        'name': '统计套利',
        'weight': 0.10,
        'features': ['pair_trade', 'cointegration', 'basis_trade']
    }
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

def get_trades(symbol, limit=100):
    try:
        return api_get(f'https://api.binance.com/api/v3/trades?symbol={symbol}&limit={limit}')
    except: return []

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
# Fingerprint Analysis
# ============================================
class FingerprintAnalyzer:
    """量化指纹分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.volumes = [d['volume'] for d in data]
        self.times = [d['time'] for d in data]
        
    def analyze_orderbook_fingerprint(self):
        """订单簿指纹"""
        if len(self.data) < 20:
            return {}
            
        # 基于价格微观结构分析
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(1, len(self.closes))]
        
        # 计算各种指纹特征
        features = {}
        
        # 1. 报价密度 (价格变化频率)
        price_changes = [1 if abs(r) > 0.001 else 0 for r in returns]
        features['quote_density'] = sum(price_changes) / len(price_changes)
        
        # 2. 价差模式 (基于日内波动)
        daily_ranges = [(self.data[i]['high'] - self.data[i]['low']) / self.data[i]['close'] 
                       for i in range(len(self.data))]
        features['spread_pattern'] = std(daily_ranges) / mean(daily_ranges) if mean(daily_ranges) > 0 else 0
        
        # 3. 深度不平衡 (上涨vs下跌量)
        up_vol = sum(self.volumes[i] for i in range(len(self.closes)-1) 
                    if self.closes[i] > self.closes[i-1])
        down_vol = sum(self.volumes[i] for i in range(len(self.closes)-1) 
                     if self.closes[i] < self.closes[i-1])
        total_vol = up_vol + down_vol
        if total_vol > 0:
            features['depth_imbalance'] = abs(up_vol - down_vol) / total_vol
        else:
            features['depth_imbalance'] = 0
            
        # 4. 取消比率 (高波动=可能的高取消)
        features['cancel_ratio'] = features['spread_pattern']
        
        return features
        
    def analyze_volume_fingerprint(self):
        """成交量指纹"""
        if len(self.data) < 20:
            return {}
            
        features = {}
        
        # 1. 成交量模式
        volumes = self.volumes
        vol_std = std(volumes[-50:])
        vol_mean = mean(volumes[-50:])
        features['volume_pattern'] = vol_std / vol_mean if vol_mean > 0 else 0
        
        # 2. 时间分布 (成交集中在什么时候)
        volumes_by_hour = defaultdict(list)
        for i, d in enumerate(self.data):
            hour = (d['time'] // 3600) % 24
            volumes_by_hour[hour].append(d['volume'])
            
        hourly_activity = [mean(volumes_by_hour[h]) for h in range(24)]
        features['time_distribution'] = std(hourly_activity) / mean(hourly_activity) if mean(hourly_activity) > 0 else 0
        
        # 3. 交易大小 (成交量/交易次数估算)
        avg_trade_size = mean([v / 100 for v in volumes[-50:]])  # 假设每秒约100笔交易
        features['trade_size'] = min(1.0, avg_trade_size)
        
        # 4. 动量轮廓
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(1, len(self.closes))]
        recent_momentum = mean(returns[-20:]) if len(returns) >= 20 else mean(returns)
        features['momentum_profile'] = abs(recent_momentum) * 10
        
        return features
        
    def analyze_price_fingerprint(self):
        """价格指纹"""
        if len(self.data) < 20:
            return {}
            
        features = {}
        closes = self.closes
        
        # 1. 收益率分布
        returns = [(closes[i] - closes[i-1]) / closes[i-1] 
                   for i in range(1, len(closes))]
        
        # 尖峰厚尾检测
        mean_ret = mean(returns)
        std_ret = std(returns)
        if std_ret > 0:
            skewness = sum((r - mean_ret) ** 3 for r in returns) / (len(returns) * std_ret ** 3)
            kurtosis = sum((r - mean_ret) ** 4 for r in returns) / (len(returns) * std_ret ** 4) - 3
        else:
            skewness, kurtosis = 0, 0
            
        features['return_distribution'] = abs(kurtosis) / 10  # 归一化
        
        # 2. 波动率聚集
        vol_windows = [std(returns[i:i+10]) for i in range(0, len(returns)-10, 10)]
        features['volatility_cluster'] = std(vol_windows) / mean(vol_windows) if mean(vol_windows) > 0 else 0
        
        # 3. 自相关性 (动量 or 均值回归)
        n = min(50, len(returns))
        autocorr = sum(returns[i] * returns[i-1] for i in range(1, n)) / n
        features['autocorrelation'] = autocorr * 10  # 正=动量, 负=回归
        
        # 4. 跳频次数
        jumps = sum(1 for r in returns if abs(r) > 3 * std_ret)
        features['jump_frequency'] = jumps / len(returns)
        
        return features
        
    def get_all_fingerprints(self):
        """获取所有指纹"""
        return {
            'orderbook': self.analyze_orderbook_fingerprint(),
            'volume': self.analyze_volume_fingerprint(),
            'price': self.analyze_price_fingerprint()
        }

# ============================================
# Institutional Fingerprint
# ============================================
class InstitutionalFingerprint:
    """机构指纹"""
    
    @staticmethod
    def market_maker_fingerprint(fp):
        """做市商指纹"""
        score = 0.0
        
        # 做市商特征: 稳定的报价密度, 低的depth_imbalance, 低的spread_pattern
        if 'quote_density' in fp['orderbook']:
            score += (1 - fp['orderbook']['quote_density']) * 0.3
        if 'depth_imbalance' in fp['orderbook']:
            score += (1 - fp['orderbook']['depth_imbalance']) * 0.3
        if 'spread_pattern' in fp['orderbook']:
            score += (1 - fp['orderbook']['spread_pattern']) * 0.2
        if 'volume_pattern' in fp['volume']:
            score += (1 - fp['volume']['volume_pattern']) * 0.2
            
        return min(1.0, score)
        
    @staticmethod
    def trend_follower_fingerprint(fp):
        """趋势跟踪指纹"""
        score = 0.0
        
        # 趋势跟踪特征: 高的momentum_profile, 正autocorrelation, 高的jump_frequency
        if 'momentum_profile' in fp['volume']:
            score += fp['volume']['momentum_profile'] * 0.4
        if 'autocorrelation' in fp['price']:
            score += max(0, fp['price']['autocorrelation']) * 0.3
        if 'jump_frequency' in fp['price']:
            score += fp['price']['jump_frequency'] * 10 * 0.2
            
        return min(1.0, score)
        
    @staticmethod
    def mean_reverter_fingerprint(fp):
        """均值回归指纹"""
        score = 0.0
        
        # 均值回归特征: 低的autocorrelation (负), 低的momentum_profile
        if 'autocorrelation' in fp['price']:
            score += max(0, -fp['price']['autocorrelation']) * 0.4
        if 'momentum_profile' in fp['volume']:
            score += (1 - fp['volume']['momentum_profile']) * 0.3
        if 'volatility_cluster' in fp['price']:
            score += fp['price']['volatility_cluster'] * 0.3
            
        return min(1.0, score)
        
    @staticmethod
    def hft_fingerprint(fp):
        """高频交易指纹"""
        score = 0.0
        
        # HFT特征: 高的quote_density, 高的spread_pattern (微观), 低的trade_size
        if 'quote_density' in fp['orderbook']:
            score += fp['orderbook']['quote_density'] * 0.4
        if 'spread_pattern' in fp['orderbook']:
            score += fp['orderbook']['spread_pattern'] * 0.3
        if 'trade_size' in fp['volume']:
            score += (1 - fp['volume']['trade_size']) * 0.3
            
        return min(1.0, score)
        
    @staticmethod
    def stat_arb_fingerprint(fp):
        """统计套利指纹"""
        score = 0.0
        
        # 统计套利特征: 低的jump_frequency, 稳定的volume_pattern
        if 'jump_frequency' in fp['price']:
            score += (1 - fp['price']['jump_frequency'] * 10) * 0.4
        if 'volume_pattern' in fp['volume']:
            score += (1 - fp['volume']['volume_pattern']) * 0.3
        if 'return_distribution' in fp['price']:
            score += (1 - fp['price']['return_distribution']) * 0.3
            
        return min(1.0, score)

# ============================================
# Composition Estimator
# ============================================
class CompositionEstimator:
    """机构占比估算"""
    
    def __init__(self):
        self.institutional_fingerprint = InstitutionalFingerprint()
        
    def estimate(self, fingerprints):
        """估算各机构占比"""
        # 计算各类机构的指纹得分
        scores = {
            'market_makers': self.institutional_fingerprint.market_maker_fingerprint(fingerprints),
            'trend_followers': self.institutional_fingerprint.trend_follower_fingerprint(fingerprints),
            'mean_reverters': self.institutional_fingerprint.mean_reverter_fingerprint(fingerprints),
            'hft': self.institutional_fingerprint.hft_fingerprint(fingerprints),
            'stat_arb': self.institutional_fingerprint.stat_arb_fingerprint(fingerprints),
        }
        
        # 归一化为概率
        total = sum(scores.values())
        if total == 0:
            # 默认分布
            return {
                'market_makers': 0.25,
                'trend_followers': 0.30,
                'mean_reverters': 0.20,
                'hft': 0.15,
                'stat_arb': 0.10,
                'confidence': 0.3
            }
            
        composition = {k: v / total for k, v in scores.items()}
        
        # 估算置信度 (基于分数差异)
        max_score = max(scores.values())
        min_score = min(scores.values())
        confidence = (max_score - min_score) / (max_score + 0.001)
        
        composition['confidence'] = min(0.95, confidence + 0.3)
        
        return composition
        
    def get_dominant_institution(self, composition):
        """获取主导机构"""
        # 排除置信度低的
        if composition['confidence'] < 0.4:
            return {'name': 'mixed', 'confidence': composition['confidence']}
            
        # 找最大占比
        exclude = ['confidence']
        max_key = max((k for k in composition if k not in exclude), 
                      key=lambda k: composition[k])
                      
        return {
            'name': max_key,
            'name_cn': INSTITUTION_TYPES[max_key]['name'],
            'ratio': composition[max_key],
            'confidence': composition['confidence']
        }

# ============================================
# Institutional Tracking
# ============================================
class InstitutionalTracker:
    """机构追踪"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.volumes = [d['volume'] for d in data]
        
    def track(self, composition):
        """追踪机构行为"""
        tracking = []
        
        # 检测吸筹 (accumulation)
        accumulation_score = self._detect_accumulation()
        if accumulation_score > 0.6:
            tracking.append({
                'institution': 'accumulator',
                'activity': accumulation_score,
                'direction': 'long',
                'pattern': '悄悄吸筹',
                'sign': '缩量下跌'
            })
            
        # 检测派发 (distribution)
        distribution_score = self._detect_distribution()
        if distribution_score > 0.6:
            tracking.append({
                'institution': 'distributor',
                'activity': distribution_score,
                'direction': 'short',
                'pattern': '高位派发',
                'sign': '放量上涨'
            })
            
        # 检测流动性提供
        lp_score = self._detect_liquidity_provider()
        if lp_score > 0.5:
            tracking.append({
                'institution': 'liquidity_provider',
                'activity': lp_score,
                'direction': 'neutral',
                'pattern': '提供流动性',
                'sign': '稳定价差'
            })
            
        # 检测动量点火
        momentum_ignition_score = self._detect_momentum_ignition()
        if momentum_ignition_score > 0.5:
            tracking.append({
                'institution': 'momentum_igniter',
                'activity': momentum_ignition_score,
                'direction': 'long' if self.closes[-1] > self.closes[-10] else 'short',
                'pattern': '动量点火',
                'sign': '快速拉升/砸盘'
            })
            
        return tracking
        
    def _detect_accumulation(self):
        """检测吸筹"""
        # 吸筹特征: 下跌但成交量萎缩
        if len(self.data) < 20:
            return 0.0
            
        recent_10 = mean(self.closes[-10:])
        older_10 = mean(self.closes[-20:-10])
        
        price_change = (recent_10 - older_10) / older_10 if older_10 > 0 else 0
        
        recent_vol = mean(self.volumes[-10:])
        older_vol = mean(self.volumes[-20:-10])
        
        vol_change = recent_vol / older_vol if older_vol > 0 else 1
        
        # 下跌 + 缩量 = 可能吸筹
        if price_change < -0.01 and vol_change < 0.8:
            return min(1.0, abs(price_change) * 50)
            
        return 0.0
        
    def _detect_distribution(self):
        """检测派发"""
        if len(self.data) < 20:
            return 0.0
            
        recent_10 = mean(self.closes[-10:])
        older_10 = mean(self.closes[-20:-10])
        
        price_change = (recent_10 - older_10) / older_10 if older_10 > 0 else 0
        
        recent_vol = mean(self.volumes[-10:])
        older_vol = mean(self.volumes[-20:-10])
        
        vol_change = recent_vol / older_vol if older_vol > 0 else 1
        
        # 上涨 + 放量 = 可能派发
        if price_change > 0.01 and vol_change > 1.2:
            return min(1.0, price_change * 50)
            
        return 0.0
        
    def _detect_liquidity_provider(self):
        """检测流动性提供者"""
        if len(self.data) < 20:
            return 0.0
            
        # 流动性提供者特征: 稳定的成交量, 低波动
        vol_std = std(self.volumes[-20:])
        vol_mean = mean(self.volumes[-20:])
        
        vol_stability = 1 - (vol_std / vol_mean) if vol_mean > 0 else 0
        
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(1, len(self.closes))]
        recent_volatility = std(returns[-20:])
        
        # 稳定成交量 + 低波动 = 可能是LP
        lp_score = vol_stability * 0.5 + (1 - min(1.0, recent_volatility * 100)) * 0.5
        
        return lp_score
        
    def _detect_momentum_ignition(self):
        """检测动量点火"""
        if len(self.data) < 20:
            return 0.0
            
        # 动量点火: 短时间内大幅波动
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(len(self.closes)-19, len(self.closes))]
        
        max_return = max(abs(r) for r in returns)
        avg_return = mean([abs(r) for r in returns])
        
        # 突然的大幅波动
        if max_return > avg_return * 5 and max_return > 0.02:
            return min(1.0, max_return * 20)
            
        return 0.0

# ============================================
# Wall Detection
# ============================================
class WallDetector:
    """订单簿墙检测"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        
    def detect_support_resistance(self):
        """检测支撑和阻力"""
        if len(self.data) < 50:
            return {'support': None, 'resistance': None, 'walls': []}
            
        # 找局部极值
        highs = []
        lows = []
        
        for i in range(10, len(self.closes) - 10):
            if self.closes[i] == max(self.closes[i-10:i+11]):
                highs.append(self.closes[i])
            if self.closes[i] == min(self.closes[i-10:i+11]):
                lows.append(self.closes[i])
                
        if not highs or not lows:
            return {'support': None, 'resistance': None, 'walls': []}
            
        # 聚类找墙
        from collections import Counter
        
        # 简化: 用直方图找密集区
        price_min = min(self.closes)
        price_max = max(self.closes)
        bins = 20
        bin_size = (price_max - price_min) / bins
        
        hist = Counter()
        for p in self.closes:
            idx = int((p - price_min) / bin_size)
            if idx >= bins:
                idx = bins - 1
            hist[idx] += 1
            
        # 找峰值 (墙)
        walls = []
        for bin_idx, count in hist.most_common(5):
            price_level = price_min + bin_idx * bin_size
            strength = count / len(self.closes)
            walls.append({
                'price': price_level,
                'strength': strength,
                'type': 'resistance' if price_level > self.closes[-1] else 'support'
            })
            
        # 排序
        walls.sort(key=lambda x: x['strength'], reverse=True)
        
        resistance = min(w['price'] for w in walls if w['type'] == 'resistance') if any(w['type'] == 'resistance' for w in walls) else None
        support = max(w['price'] for w in walls if w['type'] == 'support') if any(w['type'] == 'support' for w in walls) else None
        
        return {
            'support': support,
            'resistance': resistance,
            'walls': walls[:5]
        }

# ============================================
# Turning Point Detection
# ============================================
class TurningPointDetector:
    """转折点检测"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.volumes = [d['volume'] for d in data]
        
    def find_turning_points(self, threshold=0.03):
        """找转折点"""
        if len(self.data) < 50:
            return []
            
        turning_points = []
        
        for i in range(10, len(self.closes) - 10):
            # 局部顶
            if self.closes[i] == max(self.closes[i-10:i+11]):
                gain = (self.closes[i] - self.closes[i-10]) / self.closes[i-10] if self.closes[i-10] > 0 else 0
                if gain > threshold:
                    turning_points.append({
                        'index': i,
                        'time': self.data[i]['time'],
                        'type': 'top',
                        'price': self.closes[i],
                        'gain': gain
                    })
                    
            # 局部底
            if self.closes[i] == min(self.closes[i-10:i+11]):
                drop = (self.closes[i-10] - self.closes[i]) / self.closes[i-10] if self.closes[i-10] > 0 else 0
                if drop > threshold:
                    turning_points.append({
                        'index': i,
                        'time': self.data[i]['time'],
                        'type': 'bottom',
                        'price': self.closes[i],
                        'drop': drop
                    })
                
        return turning_points
        
    def predict_next(self, historical_points, composition):
        """预测下次转折"""
        if not historical_points:
            return {'time': None, 'type': None, 'probability': 0.3}
            
        # 基于机构类型调整预测
        if composition:
            # 趋势跟踪主导时, 转折概率更高
            if composition.get('trend_followers', 0) > 0.4:
                base_prob = 0.6
            elif composition.get('market_makers', 0) > 0.4:
                base_prob = 0.4
            else:
                base_prob = 0.5
        else:
            base_prob = 0.5
            
        # 间隔分析
        if len(historical_points) >= 2:
            intervals = [historical_points[i+1]['time'] - historical_points[i]['time'] 
                        for i in range(len(historical_points)-1)]
            avg_interval = mean(intervals)
        else:
            avg_interval = 4 * 3600
            
        last_time = historical_points[-1]['time']
        next_time = last_time + avg_interval
        
        # 类型预测
        recent_types = [tp['type'] for tp in historical_points[-5:]]
        if len(recent_types) >= 2:
            predicted_type = 'bottom' if recent_types[-1] == 'top' else 'top'
        else:
            predicted_type = 'top'
            
        return {
            'time': next_time,
            'time_str': datetime.fromtimestamp(next_time).strftime('%Y-%m-%d %H:%M'),
            'type': predicted_type,
            'probability': base_prob,
            'interval': avg_interval
        }

# ============================================
# Detect Engine
# ============================================
class DetectEngine:
    """量化机构侦测引擎"""
    
    def __init__(self):
        self.params = DETECTION_PARAMS
        
    def analyze(self, coin, interval='1h', period='30d'):
        """完整侦测分析"""
        period_map = {'7d': 168, '30d': 720, '90d': 2160}
        limit = min(period_map.get(period, 720), 500)
        
        data = get_price_data(coin, interval, limit)
        
        if not data:
            return None
            
        # 1. 指纹分析
        fp_analyzer = FingerprintAnalyzer(data)
        fingerprints = fp_analyzer.get_all_fingerprints()
        
        # 2. 占比估算
        estimator = CompositionEstimator()
        composition = estimator.estimate(fingerprints)
        dominant = estimator.get_dominant_institution(composition)
        
        # 3. 机构追踪
        tracker = InstitutionalTracker(data)
        tracking = tracker.track(composition)
        
        # 4. 墙检测
        wall_detector = WallDetector(data)
        walls = wall_detector.detect_support_resistance()
        
        # 5. 转折点
        turning_detector = TurningPointDetector(data)
        turning_points = turning_detector.find_turning_points()
        next_turning = turning_detector.predict_next(turning_points, composition)
        
        # 6. 综合预测
        prediction = self._make_prediction(
            composition, dominant, tracking, walls, next_turning
        )
        
        return {
            'coin': coin,
            'timeframe': interval,
            'period': period,
            'fingerprints': fingerprints,
            'composition': composition,
            'dominant_institution': dominant,
            'tracking': tracking,
            'walls': walls,
            'turning_points': turning_points,
            'next_turning_point': next_turning,
            'prediction': prediction
        }
        
    def _make_prediction(self, composition, dominant, tracking, walls, next_turning):
        """生成预测"""
        # 转折概率
        turning_prob = next_turning.get('probability', 0.5)
        
        # 基于主导机构调整
        if dominant.get('name') == 'trend_followers':
            turning_prob += 0.15
        elif dominant.get('name') == 'market_makers':
            turning_prob -= 0.1
            
        # 基于追踪的机构行为
        for t in tracking:
            if t['institution'] == 'momentum_igniter':
                turning_prob += 0.1
            elif t['institution'] == 'distributor':
                turning_prob += 0.1
                
        turning_prob = min(0.95, max(0.1, turning_prob))
        
        # 操作建议
        direction = next_turning.get('type', 'top')
        if direction == 'top':
            if any(t['institution'] == 'distributor' for t in tracking):
                action = 'SELL_DISTRIBUTION'
            else:
                action = 'REDUCE_LONG'
        else:  # bottom
            if any(t['institution'] == 'accumulator' for t in tracking):
                action = 'BUY_ACCUMULATION'
            else:
                action = 'ADD_LONG'
                
        return {
            'action': action,
            'turning_probability': turning_prob,
            'next_turning': next_turning,
            'support': walls.get('support'),
            'resistance': walls.get('resistance'),
            'confidence': composition.get('confidence', 0.5) * turning_prob,
            'reasoning': self._generate_reasoning(composition, dominant, tracking, walls)
        }
        
    def _generate_reasoning(self, composition, dominant, tracking, walls):
        """生成推理"""
        parts = []
        
        # 主导机构
        if dominant.get('name') != 'mixed':
            parts.append(f"主导:{dominant['name_cn']}({dominant['ratio']:.0%})")
            
        # 追踪行为
        if tracking:
            for t in tracking[:2]:
                parts.append(f"{t['pattern']}({t['activity']:.0%})")
                
        # 边界
        if walls.get('support') and walls.get('resistance'):
            parts.append(f"支撑${walls['support']:.2f}")
            parts.append(f"阻力${walls['resistance']:.2f}")
            
        return "; ".join(parts) if parts else "综合分析"

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-detect - 量化机构侦测")
        print("Usage:")
        print("  python detect_engine.py <coin> [interval] [period]")
        print("Example:")
        print("  python detect_engine.py BTC 1h 30d")
        sys.exit(1)
        
    coin = sys.argv[1].upper()
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    period = sys.argv[3] if len(sys.argv) > 3 else '30d'
    
    print(f"\n🔍 量化机构侦测: {coin} ({interval}, {period})")
    print("="*60)
    
    engine = DetectEngine()
    result = engine.analyze(coin, interval, period)
    
    if result:
        comp = result['composition']
        print(f"\n📊 机构占比估算:")
        print(f"   做市商: {comp['market_makers']:.1%}")
        print(f"   趋势跟踪: {comp['trend_followers']:.1%}")
        print(f"   均值回归: {comp['mean_reverters']:.1%}")
        print(f"   高频交易: {comp['hft']:.1%}")
        print(f"   统计套利: {comp['stat_arb']:.1%}")
        print(f"   置信度: {comp['confidence']:.0%}")
        
        dom = result['dominant_institution']
        print(f"\n🏆 主导机构:")
        print(f"   类型: {dom.get('name_cn', dom.get('name', 'mixed'))}")
        if dom.get('ratio'):
            print(f"   占比: {dom['ratio']:.1%}")
            
        tracking = result['tracking']
        if tracking:
            print(f"\n🔎 机构追踪:")
            for t in tracking:
                print(f"   {t['pattern']}: {t['activity']:.0%} {t['direction']} ({t['sign']})")
                
        walls = result['walls']
        if walls.get('support') or walls.get('resistance'):
            print(f"\n🧱 支撑阻力:")
            if walls.get('support'):
                print(f"   支撑: ${walls['support']:.2f}")
            if walls.get('resistance'):
                print(f"   阻力: ${walls['resistance']:.2f}")
                
        turning = result['next_turning_point']
        if turning.get('time'):
            print(f"\n🎯 转折点预测:")
            print(f"   时间: {turning['time_str']}")
            print(f"   类型: {turning['type']}")
            print(f"   概率: {turning['probability']:.0%}")
            
        pred = result['prediction']
        print(f"\n💡 预测操作:")
        print(f"   操作: {pred['action']}")
        print(f"   转折概率: {pred['turning_probability']:.0%}")
        print(f"   置信度: {pred['confidence']:.0%}")
        print(f"   推理: {pred['reasoning']}")
    else:
        print("数据获取失败")
