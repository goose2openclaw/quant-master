#!/usr/bin/env python3
"""
go-hotspot - 投资热点分析与追踪引擎
BTC归一化相对价格，资金流向，热点轮动分析
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

MAJOR_COINS = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','DOT','LINK','UNI','AVAX','MATIC','ATOM','LTC','ETC','AAVE','APT','NEAR','FIL','ICP','INJ','TIA','SEI','SUI','OP','ARB','LDO','CRV','RDNT','ENS']
MEME_COINS = ['PEPE','SHIB','FLOKI','WIF','BABYDOGE','COOKIE','AI','NEIRO','BOME','TURBO','PUMP','BONK','MEME','AIDOGE','ELON','FRED','MOODENG']

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

def momentum(values, period=14):
    if len(values) < period + 1: return 0
    return (values[-1] - values[-period-1]) / values[-period-1] * 100

def rate_of_change(values, period=14):
    if len(values) < period + 1: return 0
    return (values[-1] - values[-period-1]) / values[-period-1]

# ============================================
# Hotspot Models
# ============================================
class HotspotModel:
    """热点模型基类"""
    def __init__(self, model_id, name):
        self.model_id = model_id
        self.name = name
        self.score = 0.0
        self.weight = 0.0
        self.parameters = {}
        
    def analyze(self, asset_data, btc_data):
        """分析热点"""
        raise NotImplementedError

class RelativePerformanceModel(HotspotModel):
    """相对BTC表现模型"""
    def __init__(self, period=24):
        super().__init__('rel_btc_perf', f'BTC相对表现({period}h)')
        self.period = period
        
    def analyze(self, asset_data, btc_data):
        if not asset_data or not btc_data or len(asset_data) < self.period + 1:
            return 0
            
        asset_closes = [d['close'] for d in asset_data]
        btc_closes = [d['close'] for d in btc_data]
        
        # 归一化价格
        asset_norm = [asset_closes[i] / asset_closes[0] for i in range(len(asset_closes))]
        btc_norm = [btc_closes[i] / btc_closes[0] for i in range(len(btc_closes))]
        
        # 相对表现
        rel_perf = (asset_norm[-1] / btc_norm[-1] - 1) * 100 if btc_norm[-1] != 0 else 0
        
        # 转换为热点分数
        self.score = max(-100, min(100, rel_perf * 10))
        self.parameters = {
            'relative_performance': rel_perf,
            'asset_change': (asset_closes[-1] / asset_closes[0] - 1) * 100,
            'btc_change': (btc_closes[-1] / btc_closes[0] - 1) * 100
        }
        return self.score

class RelativeMomentumModel(HotspotModel):
    """相对动量模型"""
    def __init__(self, period=24):
        super().__init__('rel_momentum', f'相对动量({period}h)')
        self.period = period
        
    def analyze(self, asset_data, btc_data):
        if not asset_data or not btc_data or len(asset_data) < self.period + 1:
            return 0
            
        asset_closes = [d['close'] for d in asset_data]
        btc_closes = [d['close'] for d in btc_data]
        
        # 计算动量
        asset_mom = momentum(asset_closes, self.period)
        btc_mom = momentum(btc_closes, self.period)
        
        # 相对动量
        rel_mom = asset_mom - btc_mom
        
        self.score = max(-50, min(50, rel_mom * 5))
        self.parameters = {
            'asset_momentum': asset_mom,
            'btc_momentum': btc_mom,
            'relative_momentum': rel_mom
        }
        return self.score

class FlowDirectionModel(HotspotModel):
    """资金流向模型"""
    def __init__(self):
        super().__init__('flow_direction', '资金流向')
        
    def analyze(self, asset_data, btc_data):
        if not asset_data or len(asset_data) < 24:
            return 0
            
        volumes = [d['volume'] for d in asset_data]
        closes = [d['close'] for d in asset_data]
        
        # 计算成交量加权价格变化
        recent_vol = mean(volumes[-6:])
        avg_vol = mean(volumes)
        
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        # 价格变化
        price_change = (closes[-1] - closes[-6]) / closes[-6] * 100 if closes[-6] != 0 else 0
        
        # 资金流入信号
        if price_change > 0 and vol_ratio > 1.2:
            self.score = 40 + min(20, (price_change + vol_ratio) * 10)
        elif price_change < 0 and vol_ratio > 1.2:
            self.score = -40 - min(20, (abs(price_change) + vol_ratio) * 10)
        else:
            self.score = price_change * 2
            
        self.parameters = {
            'price_change': price_change,
            'volume_ratio': vol_ratio,
            'flow_direction': 'INFLOW' if price_change > 0 else 'OUTFLOW'
        }
        return self.score

class VolumeHotspotModel(HotspotModel):
    """成交量热点模型"""
    def __init__(self):
        super().__init__('volume_hotspot', '成交量热点')
        
    def analyze(self, asset_data, btc_data):
        if not asset_data or not btc_data or len(asset_data) < 24:
            return 0
            
        asset_vol = [d['volume'] for d in asset_data]
        btc_vol = [d['volume'] for d in btc_data]
        
        # 相对成交量
        asset_vol_avg = mean(asset_vol[-24:])
        btc_vol_avg = mean(btc_vol[-24:])
        
        rel_vol = (asset_vol_avg / btc_vol_avg) if btc_vol_avg > 0 else 1
        
        # 成交量热点分数
        if rel_vol > 2:
            self.score = 60
        elif rel_vol > 1.5:
            self.score = 40
        elif rel_vol > 1:
            self.score = 20
        elif rel_vol > 0.7:
            self.score = -20
        else:
            self.score = -40
            
        self.parameters = {
            'relative_volume': rel_vol,
            'asset_vol_avg': asset_vol_avg,
            'btc_vol_avg': btc_vol_avg
        }
        return self.score

class BTCDominanceModel(HotspotModel):
    """BTC主导地位模型"""
    def __init__(self):
        super().__init__('btc_dominance', 'BTC主导')
        
    def analyze(self, asset_data, btc_data):
        if not asset_data or not btc_data:
            return 0
            
        # 简化:BTC上涨通常意味着主导地位上升
        btc_closes = [d['close'] for d in btc_data]
        btc_change = (btc_closes[-1] / btc_closes[0] - 1) * 100 if btc_closes[0] != 0 else 0
        
        # BTC强则alt相对弱
        self.score = -btc_change * 2
        
        self.parameters = {
            'btc_change': btc_change,
            'dominance_signal': 'BTC_STRONG' if btc_change > 0 else 'ALT_STRONG'
        }
        return self.score

class CrossCorrelationModel(HotspotModel):
    """跨资产相关性模型"""
    def __init__(self, period=24):
        super().__init__('cross_corr', f'跨资产相关({period}h)')
        self.period = period
        
    def analyze(self, asset_data, btc_data):
        if not asset_data or not btc_data or len(asset_data) < self.period:
            return 0
            
        asset_closes = [d['close'] for d in asset_data[-self.period:]]
        btc_closes = [d['close'] for d in btc_data[-self.period:]]
        
        corr = correlation(asset_closes, btc_closes)
        
        # 高相关性意味着同涨同跌，低相关性意味着分化
        # 如果低相关且BTC弱alt强 = 热点切换
        self.score = (1 - corr) * 50  # -50 to +50
        
        self.parameters = {
            'correlation': corr,
            'signal': 'DIVERGENT' if corr < 0.5 else 'CORRELATED'
        }
        return self.score

class LeverageRatioModel(HotspotModel):
    """杠杆比率模型 (简化)"""
    def __init__(self):
        super().__init__('lever_ratio', '杠杆比率')
        
    def analyze(self, asset_data, btc_data):
        if not asset_data:
            return 0
            
        # 基于价格波动性估算杠杆需求
        closes = [d['close'] for d in asset_data]
        highs = [d['high'] for d in asset_data]
        lows = [d['low'] for d in asset_data]
        
        # 日内波动
        volatility = mean([(highs[i] - lows[i]) / closes[i] * 100 for i in range(len(closes))])
        
        # 高波动 = 高杠杆需求
        if volatility > 5:
            self.score = 30
        elif volatility > 3:
            self.score = 15
        elif volatility > 1:
            self.score = 0
        else:
            self.score = -15
            
        self.parameters = {
            'volatility': volatility,
            'leverage_signal': 'HIGH_LEVER' if volatility > 3 else 'LOW_LEVER'
        }
        return self.score

class AccelerationModel(HotspotModel):
    """热点加速模型"""
    def __init__(self, period=12):
        super().__init__('hotspot_accel', f'热点加速({period}h)')
        self.period = period
        
    def analyze(self, asset_data, btc_data):
        if not asset_data or not btc_data or len(asset_data) < self.period * 2:
            return 0
            
        asset_closes = [d['close'] for d in asset_data]
        btc_closes = [d['close'] for d in btc_data]
        
        # 归一化
        asset_norm = [asset_closes[i] / asset_closes[0] for i in range(len(asset_closes))]
        btc_norm = [btc_closes[i] / btc_closes[0] for i in range(len(btc_closes))]
        
        # 计算前半段和后半段的相对表现
        mid = len(asset_norm) // 2
        first_half = (asset_norm[mid-1] / btc_norm[mid-1]) - (asset_norm[0] / btc_norm[0])
        second_half = (asset_norm[-1] / btc_norm[-1]) - (asset_norm[mid] / btc_norm[mid])
        
        acceleration = second_half - first_half
        
        # 加速 = 热点形成
        self.score = max(-30, min(30, acceleration * 500))
        
        self.parameters = {
            'first_half_perf': first_half * 100,
            'second_half_perf': second_half * 100,
            'acceleration': acceleration * 100,
            'trend': 'ACCELERATING' if acceleration > 0 else 'DECELERATING'
        }
        return self.score

# ============================================
# Hotspot Engine
# ============================================
class HotspotEngine:
    """投资热点分析引擎"""
    
    def __init__(self):
        self.models = []
        self.data = {}
        self.btc_data = None
        self.results = {}
        self.weights = {
            'relative_performance': 0.30,
            'relative_momentum': 0.25,
            'flow_direction': 0.20,
            'volume_hotspot': 0.15,
            'cross_correlation': 0.10,
        }
        
    def load_data(self, coins, interval='1h', period='7d'):
        """加载数据"""
        period_map = {'7d': 168, '30d': 720, '90d': 2160}
        limit = period_map.get(period, 168)
        
        # 加载BTC数据
        self.btc_data = get_price_data('BTC', interval, min(limit, 500))
        
        # 加载各币种数据
        for coin in coins:
            self.data[coin] = get_price_data(coin, interval, min(limit, 500))
            time.sleep(0.1)  # Rate limit
            
    def analyze(self, coins, interval='1h', period='7d'):
        """分析热点"""
        self.load_data(coins, interval, period)
        
        if not self.btc_data:
            return None
            
        # 初始化模型
        self.models = [
            RelativePerformanceModel(24),
            RelativeMomentumModel(24),
            FlowDirectionModel(),
            VolumeHotspotModel(),
            CrossCorrelationModel(24),
            AccelerationModel(12),
        ]
        
        # 分析每个币种
        for coin in coins:
            if coin not in self.data or not self.data[coin]:
                continue
                
            asset_scores = []
            for model in self.models:
                score = model.analyze(self.data[coin], self.btc_data)
                asset_scores.append({
                    'model': model.model_id,
                    'name': model.name,
                    'score': score,
                    'weight': self.weights.get(model.model_id, 0.1),
                    'parameters': model.parameters
                })
            
            # 计算加权热点分数
            total_weight = sum(s['weight'] for s in asset_scores)
            weighted_score = sum(s['score'] * s['weight'] for s in asset_scores) / total_weight
            
            self.results[coin] = {
                'scores': asset_scores,
                'weighted_score': weighted_score,
                'signal': self._get_signal(weighted_score),
                'confidence': min(1.0, abs(weighted_score) / 50)
            }
            
        return self
        
    def _get_signal(self, score):
        """获取信号"""
        if score > 40:
            return 'STRONG_HOTSPOT'
        elif score > 20:
            return 'HOTSPOT'
        elif score > 5:
            return 'WARM'
        elif score > -5:
            return 'NEUTRAL'
        elif score > -20:
            return 'COOL'
        else:
            return 'COLD'
            
    def get_ranking(self, n=10):
        """获取热点排名"""
        sorted_results = sorted(self.results.items(), 
                              key=lambda x: x[1]['weighted_score'], 
                              reverse=True)
        ranking = []
        for i, (coin, data) in enumerate(sorted_results[:n], 1):
            ranking.append({
                'rank': i,
                'coin': coin,
                'score': data['weighted_score'],
                'signal': data['signal'],
                'confidence': data['confidence']
            })
        return ranking
        
    def get_signal(self, coin):
        """获取特定币种信号"""
        if coin not in self.results:
            return None
        return self.results[coin]
        
    def get_flow_map(self):
        """获取资金流动图"""
        ranking = self.get_ranking(20)
        
        # 分类
        inflows = [r for r in ranking if r['score'] > 0]
        outflows = [r for r in ranking if r['score'] < 0]
        
        # 热点转移
        hotspots = inflows[:5] if inflows else []
        coldspots = outflows[:5] if outflows else []
        
        return {
            'inflows': inflows,
            'outflows': outflows,
            'hotspots': hotspots,
            'coldspots': coldspots,
            'dominant_trend': 'ALT_SEASON' if inflows and outflows and 
                               mean([r['score'] for r in inflows]) > mean([abs(r['score']) for r in outflows])
                               else 'BTC_SEASON'
        }
        
    def get_hotspot_temperature(self, coin):
        """获取热点温度"""
        if coin not in self.results:
            return 0
            
        data = self.results[coin]
        score = data['weighted_score']
        
        # 转换为温度 (0-100)
        temp = 50 + score * 0.5
        return max(0, min(100, temp))
        
    def get_trend(self, coin):
        """获取热点趋势"""
        if coin not in self.results:
            return None
            
        data = self.results[coin]
        scores = data['scores']
        
        # 找到加速模型
        accel_model = next((s for s in scores if s['model'] == 'hotspot_accel'), None)
        
        if accel_model:
            return {
                'trend': accel_model['parameters'].get('trend', 'UNKNOWN'),
                'acceleration': accel_model['parameters'].get('acceleration', 0)
            }
        return None
        
    def summary(self):
        """获取摘要"""
        ranking = self.get_ranking(15)
        flow = self.get_flow_map()
        
        return {
            'ranking': ranking,
            'flow': flow,
            'results': self.results
        }

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-hotspot - 投资热点分析引擎")
        print("Usage: python hotspot_engine.py <coin1,coin2,...> [interval] [period]")
        print("Example: python hotspot_engine.py BTC,ETH,PEPE,FLOKI 1h 7d")
        sys.exit(1)
        
    coins = sys.argv[1].upper().split(',')
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    period = sys.argv[3] if len(sys.argv) > 3 else '7d'
    
    print(f"\n🔥 投资热点分析: {', '.join(coins)} ({interval}, {period})")
    print("="*70)
    
    engine = HotspotEngine()
    result = engine.analyze(coins, interval, period)
    
    if result:
        summary = result.summary()
        
        # 热点排名
        print(f"\n🏆 热点排名:")
        print("-"*70)
        for r in summary['ranking'][:10]:
            icon = '🔥' if r['signal'] == 'STRONG_HOTSPOT' else '🌡️' if r['signal'] == 'HOTSPOT' else '📈' if r['signal'] == 'WARM' else '➡️'
            print(f"{r['rank']:2}. {icon} {r['coin']:<10} {r['score']:>+7.2f}  {r['signal']:<18} (置信度:{r['confidence']:.0%})")
        
        # 资金流向
        flow = summary['flow']
        print(f"\n💰 资金流向:")
        print(f"   主导趋势: {'🔥 ALT_SEASON 山寨季' if flow['dominant_trend'] == 'ALT_SEASON' else '📊 BTC_SEASON 比特币季'}")
        
        if flow['hotspots']:
            print(f"   热点币种: {', '.join([h['coin'] for h in flow['hotspots'][:5]])}")
        if flow['coldspots']:
            print(f"   冷门币种: {', '.join([c['coin'] for c in flow['coldspots'][:5]])}")
        
        # 各币种详情
        print(f"\n📊 详细分析:")
        for coin in coins[:5]:
            if coin in result.results:
                data = result.results[coin]
                trend = result.get_trend(coin)
                temp = result.get_hotspot_temperature(coin)
                
                print(f"\n   【{coin}】")
                print(f"   热点分数: {data['weighted_score']:+.2f} ({data['signal']})")
                print(f"   热点温度: {temp:.1f}°C")
                if trend:
                    print(f"   热点趋势: {trend['trend']} (加速度:{trend['acceleration']:+.2f}%)")
    else:
        print("数据获取失败")
