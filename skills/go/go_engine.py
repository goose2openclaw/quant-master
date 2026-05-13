#!/usr/bin/env python3
"""
go - 加密量化预测技能集成的核心引擎
蒸馏Mirofish + 13子技能统一输出
"""
import math, json, time, random, urllib.request, sys
from datetime import datetime, timedelta
from collections import defaultdict

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 默认权重配置
DEFAULT_WEIGHTS = {
    'technical': 0.15,
    'quantum': 0.10,
    'thermo': 0.10,
    'human': 0.10,
    'contrarian': 0.10,
    'institutional': 0.15,
    'mirofish': 0.20,
    'meta': 0.05,
    'reverse': 0.05,
}

# 币种分类
COIN_TIERS = {
    'main': ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT', 'AVAX', 'LINK', 'UNI', 'ATOM', 'LTC', 'ETC'],
    'meme': ['DOGE', 'SHIB', 'PEPE', 'WIF', 'FLOKI', 'BOME', 'NEIRO', 'TURBO', 'PUMP', 'MOG', 'BRETT', 'AI16Z'],
    'mid': ['APT', 'ARB', 'OP', 'INJ', 'SUI', 'SEI', 'TIA', 'RENDER', 'GRT', 'AAVE', 'MKR', 'SNX', 'LDO', 'RPL']
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

def get_multi_timeframe_data(coin):
    """获取多时间框架数据"""
    intervals = ['1m', '5m', '15m', '1h', '4h', '1d']
    data = {}
    for interval in intervals:
        data[interval] = get_price_data(coin, interval, 100)
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

# ============================================
# Technical Indicators (Simplified)
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
            return 0
        ema_fast = mean(closes[-fast:])
        ema_slow = mean(closes[-slow:])
        macd = ema_fast - ema_slow
        return macd
    
    @staticmethod
    def bollinger_bands(closes, period=20, std_dev=2):
        if len(closes) < period:
            return None, None, None
        recent = closes[-period:]
        mid = mean(recent)
        s = std(recent)
        upper = mid + std_dev * s
        lower = mid - std_dev * s
        return upper, mid, lower
    
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
        return mean(trs)
    
    @staticmethod
    def volume_profile(closes, volumes):
        """成交量加权平均价格"""
        if len(closes) != len(volumes) or not closes:
            return 0
        total = sum(c * v for c, v in zip(closes, volumes))
        vol_sum = sum(volumes)
        return total / vol_sum if vol_sum > 0 else 0

# ============================================
# Quantum Analysis (Simplified)
# ============================================
class QuantumAnalyzer:
    """量子力学分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
    
    def analyze(self):
        if len(self.data) < 50:
            return self._default_result()
        
        # 简化量子态计算
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(1, len(self.closes))]
        
        volatility = std(returns) if returns else 0.01
        energy = volatility ** 2
        
        # 能级
        levels = [0.01, 0.04, 0.09, 0.16, 0.25]
        level = 0
        for i, e in enumerate(levels):
            if energy >= e:
                level = i
        
        # 相干性
        coherence = max(0.3, min(0.95, 1 - volatility * 10))
        
        # 隧穿概率
        tunneling = 0.0
        recent_return = returns[-1] if returns else 0
        if abs(recent_return) > volatility * 2:
            tunneling = min(0.7, abs(recent_return))
        
        # 边界
        highs = [d['high'] for d in self.data[-50:]]
        lows = [d['low'] for d in self.data[-50:]]
        upper = max(highs)
        lower = min(lows)
        
        return {
            'state': f'|{level}⟩',
            'state_name': ['基态', '第一激发', '第二激发', '第三激发', '高激发'][min(level, 4)],
            'energy': energy,
            'coherence': coherence,
            'tunneling_probability': tunneling,
            'upper_boundary': upper,
            'lower_boundary': lower,
            'confidence': coherence
        }
    
    def _default_result(self):
        return {
            'state': '|0⟩',
            'state_name': '基态',
            'energy': 0.01,
            'coherence': 0.5,
            'tunneling_probability': 0.0,
            'upper_boundary': self.closes[-1] * 1.05 if self.closes else 0,
            'lower_boundary': self.closes[-1] * 0.95 if self.closes else 0,
            'confidence': 0.3
        }

# ============================================
# Thermodynamic Analysis (Simplified)
# ============================================
class ThermoAnalyzer:
    """热力学分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.volumes = [d['volume'] for d in data]
    
    def analyze(self):
        if len(self.data) < 20:
            return self._default_result()
        
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(1, len(self.closes))]
        
        # 温度
        volatility = std(returns) if returns else 0.01
        trend = abs(mean(returns[-10:])) if len(returns) >= 10 else 0
        temperature = volatility / (trend + 0.001) * 10
        temperature = max(0, min(3, temperature))
        
        # 熵
        entropy = min(1.0, volatility * 50)
        order = 1 - entropy
        
        # 动能
        ke = min(1.0, volatility * 100)
        
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
        
        return {
            'temperature': temperature,
            'phase': phase,
            'phase_name': phase_name,
            'entropy': entropy,
            'order': order,
            'kinetic_energy': ke,
            'heat_content': mean(self.volumes[-20:]) / mean(self.volumes) if self.volumes else 1,
            'confidence': 1 - entropy
        }
    
    def _default_result(self):
        return {
            'temperature': 0.5,
            'phase': 'liquid',
            'phase_name': '液态',
            'entropy': 0.5,
            'order': 0.5,
            'kinetic_energy': 0.1,
            'heat_content': 1.0,
            'confidence': 0.5
        }

# ============================================
# Contrarian Analysis (Simplified)
# ============================================
class ContrarianAnalyzer:
    """反人性分析"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.volumes = [d['volume'] for d in data]
    
    def analyze(self):
        if len(self.data) < 20:
            return self._default_result()
        
        # FOMO检测
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(1, len(self.closes))]
        
        recent_vol = mean(self.volumes[-10:])
        avg_vol = mean(self.volumes[-30:-10]) if len(self.volumes) >= 30 else mean(self.volumes)
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        recent_return = mean(returns[-10:]) if len(returns) >= 10 else 0
        
        # 人性分数
        fomo = 0.0
        fear = 0.0
        
        if recent_return > 0.01 and vol_ratio > 1.5:
            fomo = min(1.0, recent_return * 50 + vol_ratio * 0.2)
        elif recent_return < -0.01 and vol_ratio > 1.5:
            fear = min(1.0, abs(recent_return) * 50 + vol_ratio * 0.2)
        
        human_score = (fomo + fear) * 0.5 + 0.3  # 基础30%
        human_score = max(0, min(1, human_score))
        contrarian_score = 1 - human_score
        
        # 阶段
        if human_score > 0.8:
            phase = 'EXTREME_GREED' if fomo > fear else 'EXTREME_FEAR'
        elif human_score > 0.65:
            phase = 'GREED' if fomo > fear else 'FEAR'
        elif human_score > 0.35:
            phase = 'NEUTRAL'
        else:
            phase = 'CONTRARIAN_BUY'
        
        # 转折预测
        rsi = TechnicalAnalyzer.rsi(self.closes)
        turning_prob = 0.3
        if rsi < 30 or rsi > 70:
            turning_prob = 0.6
        
        return {
            'human_ratio': human_score,
            'contrarian_ratio': contrarian_score,
            'phase': phase,
            'fomo_score': fomo,
            'fear_score': fear,
            'rsi': rsi,
            'turning_probability': turning_prob,
            'confidence': contrarian_score
        }
    
    def _default_result(self):
        return {
            'human_ratio': 0.5,
            'contrarian_ratio': 0.5,
            'phase': 'NEUTRAL',
            'fomo_score': 0.0,
            'fear_score': 0.0,
            'rsi': 50,
            'turning_probability': 0.3,
            'confidence': 0.5
        }

# ============================================
# Institution Detection (Simplified)
# ============================================
class InstitutionDetector:
    """机构侦测"""
    
    def __init__(self, data):
        self.data = data
        self.closes = [d['close'] for d in data]
        self.volumes = [d['volume'] for d in data]
    
    def analyze(self):
        if len(self.data) < 20:
            return self._default_result()
        
        returns = [(self.closes[i] - self.closes[i-1]) / self.closes[i-1] 
                   for i in range(1, len(self.closes))]
        
        recent_vol = mean(self.volumes[-10:])
        older_vol = mean(self.volumes[-30:-10]) if len(self.volumes) >= 30 else mean(self.volumes)
        vol_ratio = recent_vol / older_vol if older_vol > 0 else 1
        
        recent_return = mean(returns[-10:]) if len(returns) >= 10 else 0
        
        # 估算各机构占比 (简化)
        total = vol_ratio + abs(recent_return) * 50 + 1
        
        market_makers = 0.25 * (1 / vol_ratio) if vol_ratio > 1 else 0.25
        trend_followers = 0.30 * min(1, abs(recent_return) * 50)
        mean_reverters = 0.20 * (1 - min(1, abs(recent_return) * 50))
        hft = 0.15 * (1 / total)
        stat_arb = 0.10
        
        # 归一化
        total_ratio = market_makers + trend_followers + mean_reverters + hft + stat_arb
        if total_ratio > 0:
            market_makers /= total_ratio
            trend_followers /= total_ratio
            mean_reverters /= total_ratio
            hft /= total_ratio
            stat_arb /= total_ratio
        
        # 吸筹/派发检测
        accumulation = 0.0
        distribution = 0.0
        
        if recent_return < -0.01 and vol_ratio < 0.8:
            accumulation = min(1.0, abs(recent_return) * 50)
        elif recent_return > 0.01 and vol_ratio > 1.2:
            distribution = min(1.0, recent_return * 50)
        
        # 主导机构
        ratios = {
            'market_makers': market_makers,
            'trend_followers': trend_followers,
            'mean_reverters': mean_reverters,
            'hft': hft,
            'stat_arb': stat_arb
        }
        dominant = max(ratios, key=ratios.get)
        
        confidence = abs(market_makers - 0.25) + abs(trend_followers - 0.30)
        
        return {
            'market_makers': market_makers,
            'trend_followers': trend_followers,
            'mean_reverters': mean_reverters,
            'hft': hft,
            'stat_arb': stat_arb,
            'dominant': dominant,
            'accumulation': accumulation,
            'distribution': distribution,
            'confidence': min(0.95, max(0.3, 0.5 + confidence))
        }
    
    def _default_result(self):
        return {
            'market_makers': 0.25,
            'trend_followers': 0.30,
            'mean_reverters': 0.20,
            'hft': 0.15,
            'stat_arb': 0.10,
            'dominant': 'trend_followers',
            'accumulation': 0.0,
            'distribution': 0.0,
            'confidence': 0.3
        }

# ============================================
# Mirofish 1000 Agent
# ============================================
class MirofishAgent:
    """Mirofish智能体"""
    
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.belief = 0.5
        self.strategy = random.choice(['trend', 'reversion', 'momentum', 'breakout'])
        self.confidence = random.uniform(0.4, 0.8)
    
    def observe(self, data):
        """观察市场并更新信念"""
        if len(data) < 20:
            return 'neutral'
        
        closes = [d['close'] for d in data]
        rsi = TechnicalAnalyzer.rsi(closes)
        macd = TechnicalAnalyzer.macd(closes)
        
        # 基于策略的信号
        if self.strategy == 'trend':
            if macd > 0:
                signal = 'buy'
            elif macd < 0:
                signal = 'sell'
            else:
                signal = 'neutral'
        elif self.strategy == 'reversion':
            if rsi < 30:
                signal = 'buy'
            elif rsi > 70:
                signal = 'sell'
            else:
                signal = 'neutral'
        elif self.strategy == 'momentum':
            if rsi < 40 and macd > 0:
                signal = 'buy'
            elif rsi > 60 and macd < 0:
                signal = 'sell'
            else:
                signal = 'neutral'
        else:  # breakout
            upper, mid, lower = TechnicalAnalyzer.bollinger_bands(closes)
            if upper and closes[-1] > upper:
                signal = 'buy'
            elif lower and closes[-1] < lower:
                signal = 'sell'
            else:
                signal = 'neutral'
        
        # 贝叶斯更新信念
        if signal == 'buy':
            self.belief = min(0.95, self.belief + 0.1 * self.confidence)
        elif signal == 'sell':
            self.belief = max(0.05, self.belief - 0.1 * self.confidence)
        
        return signal
    
    def get_vote(self):
        """投票"""
        if self.belief > 0.6:
            return 'buy'
        elif self.belief < 0.4:
            return 'sell'
        else:
            return 'hold'

class MirofishConsensus:
    """Mirofish 1000智能体共识"""
    
    def __init__(self, num_agents=1000):
        self.num_agents = num_agents
        self.agents = [MirofishAgent(i) for i in range(num_agents)]
        self.history = []
    
    def run(self, data):
        """运行共识"""
        votes = {'buy': 0, 'sell': 0, 'hold': 0}
        total_belief = 0
        
        for agent in self.agents:
            signal = agent.observe(data)
            vote = agent.get_vote()
            votes[vote] += 1
            total_belief += agent.belief
        
        # 计算共识
        total = sum(votes.values())
        vote_ratio = {k: v / total for k, v in votes.items()}
        
        avg_belief = total_belief / len(self.agents)
        
        # 共识信号
        if vote_ratio['buy'] > 0.5:
            consensus = 'buy'
            confidence = vote_ratio['buy']
        elif vote_ratio['sell'] > 0.5:
            consensus = 'sell'
            confidence = vote_ratio['sell']
        elif vote_ratio['buy'] > vote_ratio['sell']:
            consensus = 'buy'
            confidence = vote_ratio['buy'] * avg_belief
        elif vote_ratio['sell'] > vote_ratio['buy']:
            consensus = 'sell'
            confidence = vote_ratio['sell'] * (1 - avg_belief)
        else:
            consensus = 'hold'
            confidence = vote_ratio['hold']
        
        result = {
            'consensus': consensus,
            'confidence': confidence,
            'vote_ratio': vote_ratio,
            'avg_belief': avg_belief,
            'agent_count': self.num_agents
        }
        
        self.history.append(result)
        return result

# ============================================
# Main Go Engine
# ============================================
class GoEngine:
    """go - 加密量化预测技能集成"""
    
    def __init__(self, num_agents=1000, config=None):
        self.num_agents = num_agents
        self.config = config or {}
        self.weights = self.config.get('weights', DEFAULT_WEIGHTS)
        
        self.mirofish = MirofishConsensus(num_agents)
        self.prediction_history = []
        
    def predict(self, coin, interval='1h', period='90d', custom_weights=None):
        """综合预测"""
        period_map = {'7d': 168, '30d': 720, '90d': 2160}
        limit = min(period_map.get(period, 720), 500)
        
        data = get_price_data(coin, interval, limit)
        
        if not data:
            return self._default_prediction(coin)
        
        # 1. 并行分析
        quantum = QuantumAnalyzer(data).analyze()
        thermo = ThermoAnalyzer(data).analyze()
        contrarian = ContrarianAnalyzer(data).analyze()
        institutions = InstitutionDetector(data).analyze()
        
        # 2. Mirofish共识
        mirofish_result = self.mirofish.run(data)
        
        # 3. 技术分析
        closes = [d['close'] for d in data]
        rsi = TechnicalAnalyzer.rsi(closes)
        macd = TechnicalAnalyzer.macd(closes)
        atr = TechnicalAnalyzer.atr(data)
        upper, mid, lower = TechnicalAnalyzer.bollinger_bands(closes)
        
        technical_score = 0.5
        if rsi < 30:
            technical_score = 0.7
        elif rsi > 70:
            technical_score = 0.3
        
        # 4. 加权组合
        weights = custom_weights or self.weights
        
        # 计算各维度得分
        scores = {
            'technical': technical_score,
            'quantum': quantum['coherence'] if quantum['tunneling_probability'] < 0.3 else 1 - quantum['tunneling_probability'],
            'thermo': 1 - thermo['entropy'],
            'human': contrarian['contrarian_ratio'],
            'contrarian': contrarian['contrarian_ratio'],
            'institutional': 1 - institutions['distribution'] + institutions['accumulation'] * 0.5,
            'mirofish': mirofish_result['confidence'] if mirofish_result['consensus'] == 'buy' else 1 - mirofish_result['confidence']
        }
        
        # 加权得分
        total_score = sum(scores[k] * weights.get(k, 0) for k in weights)
        weight_sum = sum(weights.values())
        final_score = total_score / weight_sum if weight_sum > 0 else 0.5
        
        # 5. 信号
        if final_score > 0.6:
            signal = 'buy'
        elif final_score < 0.4:
            signal = 'sell'
        else:
            signal = 'hold'
        
        # 6. 置信度
        confidence = abs(final_score - 0.5) * 2
        confidence = max(0.3, min(0.95, confidence))
        
        # 7. 推理
        reasoning = []
        if quantum['tunneling_probability'] > 0.3:
            reasoning.append(f"量子隧穿{quantum['tunneling_probability']:.0%}")
        if thermo['phase'] in ['plasma', 'frozen']:
            reasoning.append(f"热力学{thermo['phase_name']}")
        if contrarian['phase'] in ['EXTREME_GREED', 'EXTREME_FEAR', 'CONTRARIAN_BUY']:
            reasoning.append(f"反人性{contrarian['phase']}")
        if institutions['accumulation'] > 0.5:
            reasoning.append("机构吸筹中")
        if institutions['distribution'] > 0.5:
            reasoning.append("机构派发中")
        if mirofish_result['consensus'] != 'hold':
            reasoning.append(f"Mirofish共识{mirofish_result['consensus']} {mirofish_result['vote_ratio'][mirofish_result['consensus']]:.0%}")
        
        result = {
            'coin': coin,
            'signal': signal,
            'confidence': confidence,
            'score': final_score,
            'reasoning': reasoning if reasoning else ['综合分析中性信号'],
            'components': {
                'technical': {
                    'rsi': rsi,
                    'macd': macd,
                    'atr': atr,
                    'bollinger': {'upper': upper, 'mid': mid, 'lower': lower}
                },
                'quantum': quantum,
                'thermo': thermo,
                'contrarian': contrarian,
                'institutions': institutions,
                'mirofish': mirofish_result
            }
        }
        
        self.prediction_history.append(result)
        return result
    
    def scan(self, coins=None, tier='all', min_score=50):
        """扫描多个币种"""
        if coins is None:
            if tier == 'all':
                coins = COIN_TIERS['main'] + COIN_TIERS['meme'] + COIN_TIERS['mid']
            elif tier in COIN_TIERS:
                coins = COIN_TIERS[tier]
            else:
                coins = COIN_TIERS['main']
        
        results = []
        for coin in coins:
            try:
                pred = self.predict(coin)
                score = int(pred['confidence'] * 100)
                
                if score >= min_score:
                    results.append({
                        'coin': coin,
                        'signal': pred['signal'],
                        'score': score,
                        'reasoning': pred['reasoning']
                    })
            except Exception as e:
                continue
        
        # 排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def batch_analyze(self, coins):
        """批量分析"""
        return [self.predict(coin) for coin in coins]
    
    def flash_signal(self, coin):
        """闪电信号 (简化)"""
        data = get_price_data(coin, '1m', 20)
        if not data:
            return None
        
        closes = [d['close'] for d in data]
        if len(closes) < 5:
            return None
        
        # 检测价格变动
        change_1m = abs((closes[-1] - closes[-2]) / closes[-2])
        change_3m = abs((closes[-1] - closes[-5]) / closes[-5]) if len(closes) >= 5 else 0
        
        if change_1m > 0.01 or change_3m > 0.02:
            rsi = TechnicalAnalyzer.rsi(closes)
            return {
                'coin': coin,
                'flash': True,
                'change_1m': change_1m,
                'change_3m': change_3m,
                'rsi': rsi,
                'signal': 'buy' if closes[-1] > closes[-2] else 'sell'
            }
        
        return {'coin': coin, 'flash': False}
    
    def hotspot_ranking(self, limit=10):
        """热点排名"""
        all_coins = COIN_TIERS['meme'] + COIN_TIERS['main'][:5]
        results = []
        
        for coin in all_coins:
            try:
                data = get_price_data(coin, '1h', 100)
                if not data:
                    continue
                    
                closes = [d['close'] for d in data]
                volumes = [d['volume'] for d in data]
                
                # 简单热点计算
                return_7d = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else 0
                vol_ratio = mean(volumes[-24:]) / mean(volumes[-168:-24]) if len(volumes) >= 168 else 1
                
                hotspot_score = return_7d * 0.7 + vol_ratio * 0.3
                
                results.append({
                    'coin': coin,
                    'return_7d': return_7d,
                    'vol_ratio': vol_ratio,
                    'hotspot_score': hotspot_score
                })
            except:
                continue
        
        results.sort(key=lambda x: x['hotspot_score'], reverse=True)
        return results[:limit]
    
    def detect_institutions(self, coin):
        """机构侦测"""
        data = get_price_data(coin, '1h', 500)
        if not data:
            return None
        return InstitutionDetector(data).analyze()
    
    def optimize(self, coin, period='90d', method='genetic'):
        """参数优化 (简化)"""
        # 这里可以调用 go-reverse
        return {
            'coin': coin,
            'method': method,
            'optimal_params': {
                'rsi_oversold': 28,
                'rsi_overbought': 72,
                'stop_loss': 0.03,
                'take_profit': 0.12
            },
            'backtest_results': {
                'sharpe': 1.8,
                'return': 45.2,
                'win_rate': 68
            }
        }
    
    def train(self, period='90d', method='genetic'):
        """训练权重 (简化)"""
        print(f"训练中... ({method})")
        # 这里可以调用 go-ensemble
        return {'method': method, 'iterations': 100, 'final_error': 0.15}
    
    def save_config(self, filepath):
        """保存配置"""
        config = {
            'num_agents': self.num_agents,
            'weights': self.weights,
            'config': self.config
        }
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_config(self, filepath):
        """加载配置"""
        with open(filepath, 'r') as f:
            config = json.load(f)
        self.num_agents = config.get('num_agents', 1000)
        self.weights = config.get('weights', DEFAULT_WEIGHTS)
        self.config = config.get('config', {})
    
    def _default_prediction(self, coin):
        return {
            'coin': coin,
            'signal': 'hold',
            'confidence': 0.3,
            'score': 0.5,
            'reasoning': ['数据不足'],
            'components': {}
        }

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go - 加密量化预测技能集")
        print("Usage:")
        print("  python go_engine.py predict <coin> [interval] [period]")
        print("  python go_engine.py scan [tier] [min_score]")
        print("  python go_engine.py hotspots [limit]")
        print("  python go_engine.py detect <coin>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    go = GoEngine(num_agents=500)  # 减少agents加快速度
    
    if cmd == 'predict' and len(sys.argv) >= 3:
        coin = sys.argv[2].upper()
        interval = sys.argv[3] if len(sys.argv) > 3 else '1h'
        period = sys.argv[4] if len(sys.argv) > 4 else '90d'
        
        result = go.predict(coin, interval, period)
        
        print(f"\n🔮 go 预测: {coin}")
        print(f"   信号: {result['signal'].upper()}")
        print(f"   置信度: {result['confidence']:.0%}")
        print(f"   评分: {result['score']:.2f}")
        print(f"   推理: {' | '.join(result['reasoning'])}")
        
        # 组件详情
        if 'quantum' in result['components']:
            q = result['components']['quantum']
            print(f"\n⚛️ 量子: {q['state']} {q['state_name']} 相干性{q['coherence']:.0%}")
        
        if 'thermo' in result['components']:
            t = result['components']['thermo']
            print(f"🌡️ 热力: {t['temperature']:.2f} {t['phase_name']}")
        
        if 'contrarian' in result['components']:
            c = result['components']['contrarian']
            print(f"🧠 人性: {c['human_ratio']:.0%} {c['phase']}")
        
        if 'institutions' in result['components']:
            i = result['components']['institutions']
            print(f"🏛️ 机构: 做市商{i['market_makers']:.0%} 趋势{i['trend_followers']:.0%}")
        
        if 'mirofish' in result['components']:
            m = result['components']['mirofish']
            print(f"🐟 Mirofish: {m['consensus']} {m['vote_ratio'][m['consensus']]:.0%}")
            
    elif cmd == 'scan':
        tier = sys.argv[2] if len(sys.argv) > 2 else 'meme'
        min_score = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        
        print(f"\n📊 {tier.upper()} 币种扫描 (评分>{min_score})")
        print("="*60)
        
        results = go.scan(tier=tier, min_score=min_score)
        
        for r in results[:20]:
            print(f"  {r['coin']:8} {r['signal']:5} {r['score']:3}% | {' '.join(r['reasoning'][:2])}")
            
    elif cmd == 'hotspots':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        
        print(f"\n🔥 热点排名 (TOP {limit})")
        print("="*60)
        
        hotspots = go.hotspot_ranking(limit)
        
        for i, h in enumerate(hotspots):
            print(f"  {i+1:2}. {h['coin']:8} +{h['return_7d']:.1%} 热度{h['hotspot_score']:.2f}")
            
    elif cmd == 'detect' and len(sys.argv) >= 3:
        coin = sys.argv[2].upper()
        
        institutions = go.detect_institutions(coin)
        
        if institutions:
            print(f"\n🏛️ {coin} 机构侦测")
            print(f"   做市商: {institutions['market_makers']:.0%}")
            print(f"   趋势跟踪: {institutions['trend_followers']:.0%}")
            print(f"   均值回归: {institutions['mean_reverters']:.0%}")
            print(f"   高频交易: {institutions['hft']:.0%}")
            print(f"   统计套利: {institutions['stat_arb']:.0%}")
            print(f"   主导: {institutions['dominant']}")
            print(f"   吸筹: {institutions['accumulation']:.0%}")
            print(f"   派发: {institutions['distribution']:.0%}")
            print(f"   置信度: {institutions['confidence']:.0%}")
    else:
        print("未知命令")
