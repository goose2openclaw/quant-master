#!/usr/bin/env python3
"""
go-contrarian - 反人性分析引擎
识别人性特征，检测转折点，预测人性/反人性比例
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

# 人性因素权重
HUMAN_WEIGHTS = {
    'fomo': 0.15,        # FOMO追涨
    'fear': 0.15,        # 恐慌抛售
    'herd': 0.12,       # 羊群效应
    'anchoring': 0.10,   # 锚定效应
    'chasing': 0.13,     # 追涨杀跌
    'overconfidence': 0.10,  # 过度自信
    'regret_aversion': 0.10,  # 后悔厌恶
    'disposition': 0.15,   # 处置效应
}

# 反人性因素权重
CONTRARIAN_WEIGHTS = {
    'discipline': 0.20,     # 纪律
    'risk_management': 0.20, # 风险管理
    'patience': 0.15,       # 耐心
    'probabilistic': 0.15,  # 概率思维
    'independence': 0.15,    # 独立思考
    'contrarian': 0.15,      # 逆向
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
# Statistical Functions
# ============================================
def mean(values):
    return sum(values) / len(values) if values else 0

def std(values):
    if len(values) < 2: return 0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))

def correlation(x, y):
    if len(x) < 3 or len(y) < 3: return 0
    mx, my = mean(x), mean(y)
    sx, sy = std(x), std(y)
    if sx == 0 or sy == 0: return 0
    return sum((x[i] - mx) * (y[i] - my) for i in range(len(x))) / (len(x) * sx * sy)

# ============================================
# Human Behavior Detection
# ============================================
class HumanBehaviorDetector:
    """人性行为检测器"""
    
    def __init__(self):
        self.weights = HUMAN_WEIGHTS
        
    def detect_fomo(self, data, window=10):
        """检测FOMO (Fear Of Missing Out)"""
        if len(data) < window + 1:
            return 0, 0
            
        closes = [d['close'] for d in data]
        volumes = [d['volume'] for d in data]
        
        # FOMO特征: 价格上涨 + 成交量放大 + 加速
        recent_returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(len(closes)-window, len(closes))]
        recent_vol = mean(volumes[-window:])
        avg_vol = mean(volumes[-window*3:-window])
        
        price_momentum = sum(recent_returns) / window
        volume_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        # FOMO分数
        fomo_score = 0
        if price_momentum > 0.01:  # 价格上涨
            fomo_score += 0.5
        if volume_ratio > 1.5:  # 放量
            fomo_score += 0.3
        if len(recent_returns) > 2 and recent_returns[-1] > recent_returns[-2]:  # 加速
            fomo_score += 0.2
            
        return fomo_score, volume_ratio
        
    def detect_fear(self, data, window=10):
        """检测恐慌抛售"""
        if len(data) < window + 1:
            return 0, 0
            
        closes = [d['close'] for d in data]
        volumes = [d['volume'] for d in data]
        
        recent_returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(len(closes)-window, len(closes))]
        recent_vol = mean(volumes[-window:])
        avg_vol = mean(volumes[-window*3:-window])
        
        price_momentum = sum(recent_returns) / window
        volume_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        fear_score = 0
        if price_momentum < -0.01:  # 价格下跌
            fear_score += 0.5
        if volume_ratio > 1.5:  # 放量
            fear_score += 0.3
        if len(recent_returns) > 2 and recent_returns[-1] < recent_returns[-2]:  # 加速
            fear_score += 0.2
            
        return fear_score, volume_ratio
        
    def detect_herd(self, data):
        """检测羊群效应"""
        if len(data) < 30:
            return 0
            
        closes = [d['close'] for d in data]
        
        # 羊群效应: 与BTC高度相关
        btc_closes = [d['close'] for d in data]  # 简化:用自身
        
        # 计算动量一致性
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        positive = sum(1 for r in returns if r > 0) / len(returns)
        
        # 极度一致 = 羊群
        herd_score = abs(positive - 0.5) * 2  # 0-1 scale
        return herd_score
        
    def detect_chasing(self, data):
        """检测追涨杀跌"""
        if len(data) < 20:
            return 0
            
        closes = [d['close'] for d in data]
        
        # 追涨: 价格创新高后继续买入
        # 杀跌: 价格创新低后继续卖出
        
        # 计算N日高低点
        lookback = 20
        current_price = closes[-1]
        high_20 = max(closes[-lookback:])
        low_20 = min(closes[-lookback:])
        
        chasing_score = 0
        
        # 突破20日高点后继续上涨
        if current_price > high_20 * 0.98:
            chasing_score += 0.4
            
        # 跌破20日低点后继续下跌
        if current_price < low_20 * 1.02:
            chasing_score += 0.4
            
        # RSI极端
        rsi = self._calc_rsi(closes)
        if rsi > 75 or rsi < 25:
            chasing_score += 0.2
            
        return chasing_score
        
    def _calc_rsi(self, closes, period=14):
        if len(closes) < period + 1:
            return 50
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        if avg_loss == 0:
            return 100
        return 100-(100/(1+avg_gain/avg_loss))
        
    def detect_disposition(self, data):
        """检测处置效应 (盈利即跑, 亏损死守)"""
        if len(data) < 50:
            return 0
            
        closes = [d['close'] for d in data]
        
        # 处置效应: 上涨很快(急于兑现), 下跌很慢(不舍得止损)
        # 检测: 收益率分布
        
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        
        pos_returns = [r for r in returns if r > 0]
        neg_returns = [r for r in returns if r < 0]
        
        if not pos_returns or not neg_returns:
            return 0
            
        avg_pos = mean(pos_returns)
        avg_neg = mean(neg_returns)
        
        # 如果盈利平均幅度 < 亏损平均幅度, 说明倾向于卖盈守亏
        disposition = avg_pos / abs(avg_neg) if avg_neg != 0 else 1
        
        # disposition < 1 = 处置效应
        return max(0, 1 - disposition)

# ============================================
# Turning Point Detection
# ============================================
class TurningPointDetector:
    """转折点检测器"""
    
    def find_turning_points(self, data, threshold=0.03):
        """找出转折点"""
        if len(data) < 20:
            return []
            
        closes = [d['close'] for d in data]
        
        turning_points = []
        
        for i in range(5, len(closes) - 5):
            # 局部顶
            if closes[i] == max(closes[i-5:i+6]):
                # 计算前面涨幅
                if i >= 10:
                    gain = (closes[i] - closes[i-10]) / closes[i-10]
                    if gain > threshold:
                        turning_points.append({
                            'index': i,
                            'time': data[i]['time'],
                            'type': 'top',
                            'price': closes[i],
                            'gain': gain
                        })
                        
            # 局部底
            if closes[i] == min(closes[i-5:i+6]):
                if i >= 10:
                    drop = (closes[i-10] - closes[i]) / closes[i-10]
                    if drop > threshold:
                        turning_points.append({
                            'index': i,
                            'time': data[i]['time'],
                            'type': 'bottom',
                            'price': closes[i],
                            'drop': drop
                        })
                        
        return turning_points
        
    def analyze_turning_pattern(self, data, turning_points):
        """分析转折点的人性特征"""
        if not turning_points:
            return []
            
        detector = HumanBehaviorDetector()
        results = []
        
        for tp in turning_points:
            idx = tp['index']
            window_data = data[max(0, idx-20):idx+1]
            
            if tp['type'] == 'top':
                human_score, vol = detector.detect_fomo(window_data)
                human_score += vol * 0.2
            else:  # bottom
                human_score, vol = detector.detect_fear(window_data)
                human_score += vol * 0.2
                
            results.append({
                'time': tp['time'],
                'type': tp['type'],
                'human_score': min(1, human_score),
                'contrarian_score': 1 - min(1, human_score)
            })
            
        return results

# ============================================
# Human Ratio Calculator
# ============================================
class HumanRatioCalculator:
    """人性/反人性比例计算器"""
    
    def __init__(self):
        self.human_weights = HUMAN_WEIGHTS
        self.contrarian_weights = CONTRARIAN_WEIGHTS
        
    def calculate(self, data):
        """计算人性/反人性比例"""
        if len(data) < 20:
            return {'human': 0.5, 'contrarian': 0.5, 'phase': 'NEUTRAL'}
            
        detector = HumanBehaviorDetector()
        
        # 检测各种人性特征
        fomo_score, fomo_vol = detector.detect_fomo(data)
        fear_score, fear_vol = detector.detect_fear(data)
        herd_score = detector.detect_herd(data)
        chasing_score = detector.detect_chasing(data)
        disposition_score = detector.detect_disposition(data)
        
        # 计算人性总分
        human_score = (
            fomo_score * self.human_weights['fomo'] +
            fear_score * self.human_weights['fear'] +
            herd_score * self.human_weights['herd'] +
            chasing_score * self.human_weights['chasing'] +
            disposition_score * self.human_weights['disposition']
        )
        
        # 限制在0-1
        human_score = max(0, min(1, human_score))
        contrarian_score = 1 - human_score
        
        # 确定阶段
        phase = self._determine_phase(human_score, fomo_score, fear_score)
        
        return {
            'human': human_score,
            'contrarian': contrarian_score,
            'phase': phase,
            'fomo_score': fomo_score,
            'fear_score': fear_score,
            'herd_score': herd_score,
            'chasing_score': chasing_score,
            'disposition_score': disposition_score
        }
        
    def _determine_phase(self, human_score, fomo_score, fear_score):
        """确定人性阶段"""
        if human_score > 0.8:
            return 'EXTREME_GREED' if fomo_score > fear_score else 'EXTREME_FEAR'
        elif human_score > 0.65:
            return 'GREED' if fomo_score > fear_score else 'FEAR'
        elif human_score > 0.5:
            return 'CAUTIOUS_OPTIMISM' if fomo_score > fear_score else 'CAUTIOUS_PESSIMISM'
        elif human_score > 0.35:
            return 'NEUTRAL'
        elif human_score > 0.2:
            return 'CONTRARIAN_BUY_OPPORTUNITY'
        else:
            return 'EXTREME_CONTRARIAN'

# ============================================
# Contrarian Engine
# ============================================
class ContrarianEngine:
    """反人性分析引擎"""
    
    def __init__(self):
        self.detector = HumanBehaviorDetector()
        self.turning_detector = TurningPointDetector()
        self.ratio_calculator = HumanRatioCalculator()
        self.human_kline = []
        
    def analyze(self, coin, interval='1h', period='30d'):
        """分析人性特征"""
        period_map = {'7d': 168, '30d': 720, '90d': 2160}
        limit = min(period_map.get(period, 720), 500)
        
        data = get_price_data(coin, interval, limit)
        
        if not data:
            return None
            
        # 计算人性比例
        ratio = self.ratio_calculator.calculate(data)
        
        # 检测转折点
        turning_points = self.turning_detector.find_turning_points(data)
        turning_analysis = self.turning_detector.analyze_turning_pattern(data, turning_points)
        
        # 构建人性K线
        self._build_human_kline(data)
        
        # 预测下次转折点
        prediction = self._predict_turning_point(turning_analysis, ratio)
        
        return {
            'coin': coin,
            'timeframe': interval,
            'current': ratio,
            'turning_points': turning_points,
            'turning_analysis': turning_analysis,
            'human_kline': self.human_kline,
            'prediction': prediction
        }
        
    def _build_human_kline(self, data):
        """构建人性K线"""
        self.human_kline = []
        
        for i in range(20, len(data)):
            window_data = data[:i+1]
            ratio = self.ratio_calculator.calculate(window_data)
            
            self.human_kline.append({
                'time': data[i]['time'],
                'human_ratio': ratio['human'],
                'contrarian_ratio': ratio['contrarian'],
                'phase': ratio['phase']
            })
            
    def _predict_turning_point(self, turning_analysis, current_ratio):
        """预测下次转折点"""
        if not turning_analysis:
            return {
                'next_time': None,
                'expected_human_ratio': current_ratio['human'],
                'expected_phase': current_ratio['phase'],
                'confidence': 0.3,
                'action': 'HOLD'
            }
            
        # 分析历史转折点模式
        recent = turning_analysis[-5:] if len(turning_analysis) >= 5 else turning_analysis
        
        avg_human_before = mean([tp['human_score'] for tp in recent])
        
        # 预测下次人性比例
        if current_ratio['human'] > 0.7:
            # 人性高潮, 可能反转
            expected_ratio = current_ratio['human'] * 0.8
            action = 'CONTRARIAN_SELL'
            confidence = min(0.9, 0.5 + (current_ratio['human'] - 0.7))
        elif current_ratio['human'] < 0.3:
            # 人性低谷, 可能反弹
            expected_ratio = current_ratio['human'] * 1.3
            action = 'CONTRARIAN_BUY'
            confidence = min(0.9, 0.5 + (0.3 - current_ratio['human']))
        else:
            expected_ratio = current_ratio['human']
            action = 'HOLD'
            confidence = 0.5
            
        # 计算下次转折时间 (简化: 平均间隔)
        if len(recent) >= 2:
            avg_interval = (recent[-1]['time'] - recent[0]['time']) / len(recent)
        else:
            avg_interval = 3600 * 4  # 默认4小时
            
        next_time = datetime.now() + timedelta(seconds=avg_interval)
        
        return {
            'next_time': next_time.strftime('%Y-%m-%d %H:%M'),
            'expected_human_ratio': expected_ratio,
            'expected_phase': self._ratio_to_phase(expected_ratio),
            'confidence': confidence,
            'action': action
        }
        
    def _ratio_to_phase(self, ratio):
        """比例转阶段"""
        if ratio > 0.8:
            return 'EXTREME_HUMAN'
        elif ratio > 0.65:
            return 'HUMAN_DOMINANT'
        elif ratio > 0.5:
            return 'HUMAN_LEANING'
        elif ratio > 0.35:
            return 'NEUTRAL'
        elif ratio > 0.2:
            return 'CONTRARIAN_LEANING'
        else:
            return 'CONTRARIAN_DOMINANT'

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-contrarian - 反人性分析引擎")
        print("Usage:")
        print("  python contrarian_engine.py <coin> [interval] [period]")
        print("Example:")
        print("  python contrarian_engine.py BTC 1h 30d")
        sys.exit(1)
        
    coin = sys.argv[1].upper()
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    period = sys.argv[3] if len(sys.argv) > 3 else '30d'
    
    print(f"\n🧠 反人性分析: {coin} ({interval}, {period})")
    print("="*60)
    
    engine = ContrarianEngine()
    result = engine.analyze(coin, interval, period)
    
    if result:
        current = result['current']
        
        print(f"\n📊 当前人性/反人性比例:")
        print(f"   人性比例: {current['human']:.1%}")
        print(f"   反人性比例: {current['contrarian']:.1%}")
        print(f"   阶段: {current['phase']}")
        
        print(f"\n📈 人性特征分数:")
        print(f"   FOMO分数: {current.get('fomo_score', 0):.2f}")
        print(f"   恐慌分数: {current.get('fear_score', 0):.2f}")
        print(f"   羊群分数: {current.get('herd_score', 0):.2f}")
        print(f"   追涨杀跌: {current.get('chasing_score', 0):.2f}")
        print(f"   处置效应: {current.get('disposition_score', 0):.2f}")
        
        print(f"\n🎯 转折点预测:")
        pred = result['prediction']
        if pred['next_time']:
            print(f"   下次转折: {pred['next_time']}")
            print(f"   预期人性比: {pred['expected_human_ratio']:.1%}")
            print(f"   预期阶段: {pred['expected_phase']}")
            print(f"   置信度: {pred['confidence']:.0%}")
            print(f"   操作建议: {pred['action']}")
        else:
            print("   数据不足")
            
        print(f"\n📊 历史转折点: {len(result['turning_points'])} 个")
        if result['turning_analysis']:
            recent = result['turning_analysis'][-3:]
            for tp in recent:
                tp_type = "顶" if tp['type'] == 'top' else "底"
                print(f"   {datetime.fromtimestamp(tp['time']).strftime('%m-%d %H:%M')} {tp_type} 人性比:{tp['human_score']:.1%}")
    else:
        print("数据获取失败")
