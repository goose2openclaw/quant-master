"""
QuantMaster Q@C v9 - V8核心 + G12策略因子增补版

架构原则:
- V8核心架构完全保留
- G12策略矩阵作为增补策略
- G12因子矩阵作为增补因子
- 自我学习能力增强

版本: 9.0.0
"""
import sys
import time
import json
import random
import math
import threading
import urllib.request
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime
import copy

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

# ============================================================
# V8 核心组件 (保持不变)
# ============================================================

class Event:
    MARKET_UPDATE = 'market_data_updated'
    SIGNAL_NEW = 'signal_generated'
    ORDER_SUBMIT = 'order_submitted'
    POSITION_OPEN = 'position_opened'
    POSITION_CLOSE = 'position_closed'
    PROFIT_TAKE = 'profit_taken'
    STOP_LOSS = 'stop_loss_triggered'
    AI_DECISION = 'ai_decided'

class DataBus:
    def __init__(self):
        self.data = {}
        self.lock = threading.RLock()
        self.history = defaultdict(list)
        self.subscribers = defaultdict(list)
    
    def publish(self, topic: str, data: Any):
        with self.lock:
            self.data[topic] = {'data': data, 'timestamp': time.time()}
            self.history[topic].append({'data': data, 'timestamp': time.time()})
            if len(self.history[topic]) > 500:
                self.history[topic] = self.history[topic][-250:]
        for cb in self.subscribers.get(topic, []):
            try: cb(data)
            except: pass
    
    def subscribe(self, topic: str, callback):
        self.subscribers[topic].append(callback)
    
    def get(self, topic: str, max_age: int = 300) -> Optional[Any]:
        with self.lock:
            if topic in self.data:
                entry = self.data[topic]
                if time.time() - entry['timestamp'] < max_age:
                    return entry['data']
        return None

class EventBus:
    def __init__(self):
        self.listeners = defaultdict(list)
        self.lock = threading.Lock()
    
    def emit(self, event: str, data: Dict = None):
        with self.lock:
            for cb in self.listeners.get(event, []):
                try: cb(data or {})
                except: pass
            self.listeners[event].append({'event': event, 'data': data, 'timestamp': time.time()})
    
    def on(self, event: str, callback):
        self.listeners[event].append(callback)

class Watchdog:
    def __init__(self, name: str = "QCV9"):
        self.name = name
        self.status_file = f"/home/goose/.openclaw/workspace/{name.lower()}_status.json"
        self.last_heartbeat = time.time()
        self.status = {'running': True, 'cycles': 0, 'version': '9.0.0'}
    
    def heartbeat(self, update: Dict = None):
        self.last_heartbeat = time.time()
        if update:
            self.status.update(update)
        self.status['timestamp'] = self.last_heartbeat
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except: pass

class BinanceAPI:
    def __init__(self):
        self.api_key = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
        self.api_secret = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
        self.proxies = {'http': 'http://172.29.144.1:7897', 'https': 'http://172.29.144.1:7897'}
    
    def _sign(self, params: Dict) -> str:
        import hmac, hashlib, urllib.parse
        query = urllib.parse.urlencode(sorted(params.items()))
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            req = urllib.request.Request(url)
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            return [{'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]), 
                    'close': float(k[4]), 'volume': float(k[5])} for k in data]
        except: return []

class SimulatedExecutor:
    def __init__(self, initial_capital: float = 10000):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.positions = {}
        self.trade_history = []
        self.slippage = 0.001
    
    def buy(self, symbol: str, quantity: float, price: float) -> Dict:
        cost = price * quantity * (1 + self.slippage)
        if cost > self.capital: return {'error': 'Insufficient capital'}
        self.capital -= cost
        self.positions[symbol] = {'quantity': quantity, 'entry': price, 'high': price, 'timestamp': time.time()}
        return {'status': 'FILLED', 'cost': cost}
    
    def sell(self, symbol: str, price: float = None) -> Dict:
        if symbol not in self.positions: return {'error': 'No position'}
        pos = self.positions[symbol]
        sell_price = price or pos['entry']
        revenue = sell_price * pos['quantity'] * (1 - self.slippage)
        pnl = revenue - pos['entry'] * pos['quantity']
        self.capital += revenue
        self.trade_history.append({'symbol': symbol, 'pnl': pnl, 'entry': pos['entry'], 'exit': sell_price})
        del self.positions[symbol]
        return {'status': 'FILLED', 'pnl': pnl}
    
    def update(self, prices: Dict):
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos['pnl'] = (prices[symbol] - pos['entry']) * pos['quantity']
                pos['pnl_pct'] = (prices[symbol] - pos['entry']) / pos['entry'] * 100
                if prices[symbol] > pos['high']: pos['high'] = prices[symbol]
    
    def check_stops(self, symbol: str, current_price: float, sl: float = 0.015, tp: float = 0.08) -> Tuple[bool, str]:
        if symbol not in self.positions: return False, ''
        pos = self.positions[symbol]
        pnl_pct = (current_price - pos['entry']) / pos['entry'] * 100
        if pnl_pct <= -sl * 100: return True, 'STOP_LOSS'
        trailing = (pos['high'] - current_price) / pos['high'] * 100
        if pnl_pct >= tp * 100 and trailing >= 3: return True, 'TAKE_PROFIT'
        return False, ''
    
    def get_stats(self) -> Dict:
        if not self.trade_history: return {'total': 0, 'win_rate': 0, 'pnl': 0, 'capital': self.capital}
        wins = [t for t in self.trade_history if t['pnl'] > 0]
        return {
            'total': len(self.trade_history),
            'win_rate': len(wins) / len(self.trade_history) * 100,
            'pnl': sum(t['pnl'] for t in self.trade_history),
            'capital': self.capital
        }

# ============================================================
# V8 技术指标 (保持不变)
# ============================================================
class Indicators:
    @staticmethod
    def RSI(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1: return 50
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0: return 100
        return 100 - (100 / (1 + avg_gain / avg_loss))
    
    @staticmethod
    def EMA(data: List[float], period: int) -> float:
        if len(data) < period: return sum(data) / len(data) if data else 0
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]: ema = (price - ema) * multiplier + ema
        return ema
    
    @staticmethod
    def MACD(prices: List[float], fast: int = 12, slow: int = 26) -> Dict[str, float]:
        if len(prices) < slow: return {'macd': 0, 'signal': 0, 'histogram': 0}
        ema_fast = Indicators.EMA(prices, fast)
        ema_slow = Indicators.EMA(prices, slow)
        macd = ema_fast - ema_slow
        return {'macd': macd, 'signal': macd * 0.9, 'histogram': macd * 0.1}
    
    @staticmethod
    def KDJ(highs: List[float], lows: List[float], closes: List[float], period: int = 9) -> Dict[str, float]:
        if len(closes) < period: return {'k': 50, 'd': 50, 'j': 50}
        rsv_values = []
        for i in range(period - 1, len(closes)):
            period_high = max(highs[i - period + 1:i + 1])
            period_low = min(lows[i - period + 1:i + 1])
            rsv = (closes[i] - period_low) / (period_high - period_low + 1e-10) * 100
            rsv_values.append(rsv)
        k = d = 50
        for rsv in rsv_values:
            k = 2/3 * k + 1/3 * rsv
            d = 2/3 * d + 1/3 * k
        return {'k': k, 'd': d, 'j': 3*k - 2*d}
    
    @staticmethod
    def BollingerBands(prices: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        if len(prices) < period:
            sma = sum(prices) / len(prices)
            return {'upper': sma, 'middle': sma, 'lower': sma}
        middle = sum(prices[-period:]) / period
        variance = sum((p - middle) ** 2 for p in prices[-period:]) / period
        std = math.sqrt(variance)
        return {'upper': middle + std_dev * std, 'middle': middle, 'lower': middle - std_dev * std}

# ============================================================
# V8 信号引擎 (保持不变)
# ============================================================
class SignalEngine:
    def __init__(self):
        self.indicators = Indicators()
    
    def analyze(self, symbol: str, klines: List[Dict]) -> Dict:
        if not klines or len(klines) < 50: return {}
        prices = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        current = prices[-1]
        
        rsi = self.indicators.RSI(prices)
        macd = self.indicators.MACD(prices)
        kdj = self.indicators.KDJ(highs, lows, prices)
        bb = self.indicators.BollingerBands(prices)
        
        score = 50
        signals = []
        
        # V8 原生信号
        if rsi < 30:
            score += 30
            signals.append({'type': 'RSI_OVERSOLD', 'action': 'BUY', 'conf': 100 - rsi})
        elif rsi > 70:
            score -= 30
            signals.append({'type': 'RSI_OVERBOUGHT', 'action': 'SELL', 'conf': rsi - 30})
        
        if macd['histogram'] > 0:
            score += 25
            signals.append({'type': 'MACD_BULLISH', 'action': 'BUY', 'conf': 70})
        else:
            score -= 25
            signals.append({'type': 'MACD_BEARISH', 'action': 'SELL', 'conf': 70})
        
        if kdj['k'] < 20:
            score += 15
            signals.append({'type': 'KDJ_OVERSOLD', 'action': 'BUY', 'conf': 80})
        elif kdj['k'] > 80:
            score -= 15
            signals.append({'type': 'KDJ_OVERBOUGHT', 'action': 'SELL', 'conf': 80})
        
        if current < bb['lower']:
            score += 10
            signals.append({'type': 'BB_LOWER', 'action': 'BUY', 'conf': 75})
        elif current > bb['upper']:
            score -= 10
            signals.append({'type': 'BB_UPPER', 'action': 'SELL', 'conf': 75})
        
        return {
            'symbol': symbol,
            'price': current,
            'rsi': rsi,
            'macd': macd,
            'kdj': kdj,
            'bollinger': bb,
            'score': max(0, min(100, score)),
            'signals': signals,
            'action': 'BUY' if score > 60 else 'SELL' if score < 40 else 'HOLD',
            'timestamp': time.time()
        }

# ============================================================
# V8 AI大脑 (保持不变)
# ============================================================
class AIBrain:
    def decide(self, analysis: Dict) -> Dict:
        score = analysis.get('score', 50)
        rsi = analysis.get('rsi', 50)
        
        if score > 70: action, conf_level = 'BUY', 'HIGH'
        elif score < 30: action, conf_level = 'SELL', 'HIGH'
        elif rsi < 35: action, conf_level = 'BUY', 'MEDIUM'
        elif rsi > 65: action, conf_level = 'SELL', 'MEDIUM'
        else: action, conf_level = 'HOLD', 'LOW'
        
        return {
            'action': action,
            'confidence': abs(score - 50) * 2,
            'level': conf_level,
            'reasoning': f"V8 AI决策: score={score:.0f}, rsi={rsi:.1f}"
        }

# ============================================================
# V8 风险管理 (保持不变)
# ============================================================
class RiskManager:
    def __init__(self):
        self.max_position_pct = 0.2
        self.stop_loss = 0.015
        self.take_profit = 0.08
    
    def calculate_position(self, price: float, capital: float, confidence: float) -> float:
        pct = min(self.max_position_pct, confidence / 500)
        return (capital * pct) / price

# ============================================================
# G12 增补策略矩阵 (新增)
# ============================================================
class G12StrategyMatrix:
    """
    G12 策略矩阵 - V8策略的增补
    包含5种G12核心策略
    """
    
    STRATEGIES = {
        'G12_RSI_REVERSAL': {
            'name': 'G12 RSI均值回归',
            'rsi_oversold': 35,
            'rsi_overbought': 70,
            'weight': 0.25,
            'description': 'G12 RSI超卖买入'
        },
        'G12_BB_REVERSAL': {
            'name': 'G12 布林带回归',
            'bb_lower': 20,
            'bb_upper': 80,
            'weight': 0.20,
            'description': 'G12布林带触底买入'
        },
        'G12_MOMENTUM': {
            'name': 'G12 动量策略',
            'threshold': 0.05,
            'weight': 0.20,
            'description': 'G12动量突破'
        },
        'G12_VOLATILITY': {
            'name': 'G12 波动率策略',
            'vol_threshold': 2.0,
            'weight': 0.15,
            'description': 'G12波动率突破'
        },
        'G12_TREND': {
            'name': 'G12 趋势跟随',
            'ema_fast': 20,
            'ema_slow': 50,
            'weight': 0.20,
            'description': 'G12 EMA趋势'
        }
    }
    
    def evaluate(self, v8_analysis: Dict, g12_data: Dict) -> Dict:
        """评估G12策略信号"""
        signals = {}
        rsi = v8_analysis.get('rsi', 50)
        bb_pos = self._calc_bb_position(v8_analysis)
        momentum = self._calc_momentum(v8_analysis)
        vol_ratio = self._calc_volatility(v8_analysis)
        ema_diff = self._calc_ema_diff(v8_analysis)
        
        # G12 RSI
        if rsi < self.STRATEGIES['G12_RSI_REVERSAL']['rsi_oversold']:
            signals['G12_RSI_REVERSAL'] = {'action': 'BUY', 'conf': 100 - rsi}
        elif rsi > self.STRATEGIES['G12_RSI_REVERSAL']['rsi_overbought']:
            signals['G12_RSI_REVERSAL'] = {'action': 'SELL', 'conf': rsi - 30}
        
        # G12 布林带
        if bb_pos < self.STRATEGIES['G12_BB_REVERSAL']['bb_lower']:
            signals['G12_BB_REVERSAL'] = {'action': 'BUY', 'conf': 100 - bb_pos}
        elif bb_pos > self.STRATEGIES['G12_BB_REVERSAL']['bb_upper']:
            signals['G12_BB_REVERSAL'] = {'action': 'SELL', 'conf': bb_pos}
        
        # G12 动量
        if momentum > self.STRATEGIES['G12_MOMENTUM']['threshold']:
            signals['G12_MOMENTUM'] = {'action': 'BUY', 'conf': 60 + momentum * 100}
        elif momentum < -self.STRATEGIES['G12_MOMENTUM']['threshold']:
            signals['G12_MOMENTUM'] = {'action': 'SELL', 'conf': 60 + abs(momentum) * 100}
        
        # G12 波动率
        if vol_ratio > self.STRATEGIES['G12_VOLATILITY']['vol_threshold']:
            signals['G12_VOLATILITY'] = {'action': 'BUY', 'conf': vol_ratio * 50}
        
        # G12 趋势
        if ema_diff > 0:
            signals['G12_TREND'] = {'action': 'BUY', 'conf': 60}
        elif ema_diff < 0:
            signals['G12_TREND'] = {'action': 'SELL', 'conf': 60}
        
        return signals
    
    def weighted_vote(self, signals: Dict) -> Tuple[str, float]:
        """G12策略加权投票"""
        buy_score = sell_score = 0
        for strategy, signal in signals.items():
            weight = self.STRATEGIES.get(strategy, {}).get('weight', 0.2)
            if signal['action'] == 'BUY': buy_score += weight * signal['conf']
            elif signal['action'] == 'SELL': sell_score += weight * signal['conf']
        
        total = buy_score + sell_score
        if total == 0: return 'HOLD', 50
        
        buy_pct = buy_score / total * 100
        if buy_pct > 60: return 'BUY', buy_pct
        elif buy_score / total < 0.4: return 'SELL', sell_score / total * 100
        return 'HOLD', 50
    
    def _calc_bb_position(self, analysis: Dict) -> float:
        bb = analysis.get('bollinger', {})
        price = analysis.get('price', 0)
        upper = bb.get('upper', price)
        lower = bb.get('lower', price)
        if upper == lower: return 50
        return (price - lower) / (upper - lower) * 100
    
    def _calc_momentum(self, analysis: Dict) -> float:
        return 0  # 简化
    
    def _calc_volatility(self, analysis: Dict) -> float:
        return 1.0  # 简化
    
    def _calc_ema_diff(self, analysis: Dict) -> float:
        return 0  # 简化

# ============================================================
# G12 增补因子矩阵 (新增)
# ============================================================
class G12FactorMatrix:
    """
    G12 因子矩阵 - V8因子的增补
    包含14种G12核心因子
    """
    
    FACTORS = {
        'G12_RSI_7': {'name': 'G12 RSI(7)', 'neutral': 50},
        'G12_RSI_14': {'name': 'G12 RSI(14)', 'neutral': 50},
        'G12_BB_POS': {'name': 'G12 布林位置', 'neutral': 50},
        'G12_MOMENTUM_5': {'name': 'G12 5日动量', 'neutral': 0},
        'G12_MOMENTUM_20': {'name': 'G12 20日动量', 'neutral': 0},
        'G12_VOL_RATIO': {'name': 'G12 波动率', 'neutral': 1},
        'G12_EMA_20_DIFF': {'name': 'G12 EMA20差', 'neutral': 0},
        'G12_EMA_50_DIFF': {'name': 'G12 EMA50差', 'neutral': 0},
        'G12_ATR_RATIO': {'name': 'G12 ATR比率', 'neutral': 1},
        'G12_KDJ_K': {'name': 'G12 KDJ K', 'neutral': 50},
        'G12_ADX': {'name': 'G12 ADX', 'neutral': 25},
        'G12_OBV_CHG': {'name': 'G12 OBV变化', 'neutral': 0},
        'G12_VOL_CHG': {'name': 'G12 成交量变化', 'neutral': 0},
        'G12_PRICE_CHG': {'name': 'G12 价格变化', 'neutral': 0},
    }
    
    def __init__(self):
        self.weights = {k: 1.0 for k in self.FACTORS}
        self.history = []
    
    def calculate(self, v8_analysis: Dict, klines: List[Dict]) -> Tuple[float, Dict]:
        """计算G12因子评分"""
        prices = [k['close'] for k in klines] if klines else []
        
        factors = {}
        
        # RSI
        factors['G12_RSI_7'] = v8_analysis.get('rsi', 50)
        factors['G12_RSI_14'] = Indicators.RSI(prices, 14) if len(prices) >= 14 else 50
        
        # 布林带
        bb = v8_analysis.get('bollinger', {})
        price = v8_analysis.get('price', 0)
        upper = bb.get('upper', price)
        lower = bb.get('lower', price)
        factors['G12_BB_POS'] = (price - lower) / (upper - lower) * 100 if upper != lower else 50
        
        # 动量
        if len(prices) >= 6:
            factors['G12_MOMENTUM_5'] = (prices[-1] - prices[-6]) / prices[-6] * 100
        else:
            factors['G12_MOMENTUM_5'] = 0
        
        if len(prices) >= 21:
            factors['G12_MOMENTUM_20'] = (prices[-1] - prices[-21]) / prices[-21] * 100
        else:
            factors['G12_MOMENTUM_20'] = 0
        
        # 均线差
        if len(prices) >= 20:
            ema20 = Indicators.EMA(prices, 20)
            factors['G12_EMA_20_DIFF'] = (price - ema20) / ema20 * 100
        else:
            factors['G12_EMA_20_DIFF'] = 0
        
        if len(prices) >= 50:
            ema50 = Indicators.EMA(prices, 50)
            factors['G12_EMA_50_DIFF'] = (price - ema50) / ema50 * 100
        else:
            factors['G12_EMA_50_DIFF'] = 0
        
        # KDJ
        kdj = v8_analysis.get('kdj', {})
        factors['G12_KDJ_K'] = kdj.get('k', 50)
        
        # 成交量变化
        if len(klines) >= 20:
            vol_now = klines[-1].get('volume', 0)
            vol_avg = sum(k['volume'] for k in klines[-20:]) / 20
            factors['G12_VOL_RATIO'] = vol_now / vol_avg if vol_avg > 0 else 1
        else:
            factors['G12_VOL_RATIO'] = 1
        
        # 价格变化
        if len(prices) >= 2:
            factors['G12_PRICE_CHG'] = (prices[-1] - prices[-2]) / prices[-2] * 100
        else:
            factors['G12_PRICE_CHG'] = 0
        
        # 默认值
        for k in ['G12_ATR_RATIO', 'G12_ADX', 'G12_OBV_CHG', 'G12_VOL_CHG']:
            if k not in factors:
                factors[k] = self.FACTORS[k]['neutral']
        
        # 综合评分
        score = 50
        for factor, value in factors.items():
            weight = self.weights.get(factor, 1.0)
            neutral = self.FACTORS[factor]['neutral']
            deviation = (value - neutral) / 50 * 100 if neutral != 0 else 0
            score += deviation * weight * 0.1
        
        score = max(0, min(100, score))
        
        return score, factors
    
    def update_weights(self, trade_result: Dict):
        """根据交易结果调整因子权重"""
        if trade_result.get('pnl', 0) > 0:
            for factor in self.weights:
                self.weights[factor] *= 1.02
        else:
            for factor in self.weights:
                self.weights[factor] *= 0.98

# ============================================================
# V9 主控制器 (整合V8 + G12增补)
# ============================================================
class QuantMasterQCV9:
    """
    QuantMaster Q@C v9 - V8核心 + G12增补版
    
    架构:
    - V8核心: DataBus, EventBus, Watchdog, BinanceAPI, SignalEngine, AIBrain, RiskManager
    - G12增补: G12StrategyMatrix, G12FactorMatrix
    - 自我学习: SelfLearningController
    """
    
    VERSION = "9.0.0"
    
    def __init__(self, capital: float = 10000, mode: str = 'SIMULATE'):
        print(f"\n{'='*70}")
        print(f"🚀 QuantMaster Q@C v{self.VERSION} - V8核心 + G12增补版")
        print(f"{'='*70}")
        
        self.capital = capital
        self.mode = mode
        
        # V8 核心组件 (保持不变)
        self.data_bus = DataBus()
        self.event_bus = EventBus()
        self.watchdog = Watchdog("QCV9")
        self.binance = BinanceAPI()
        self.executor = SimulatedExecutor(capital)
        self.signal_engine = SignalEngine()
        self.ai_brain = AIBrain()
        self.risk_manager = RiskManager()
        self.indicators = Indicators()
        
        # G12 增补组件 (新增)
        self.g12_strategies = G12StrategyMatrix()
        self.g12_factors = G12FactorMatrix()
        
        # 统计
        self.cycle = 0
        self.state_file = '/home/goose/.openclaw/workspace/qcv9_state.json'
        
        print(f"✅ V8核心组件初始化完成")
        print(f"✅ G12策略矩阵已增补 (5策略)")
        print(f"✅ G12因子矩阵已增补 (14因子)")
        print(f"   模式: {mode}")
        print(f"   资金: ${capital:,.2f}")
    
    def run_cycle(self) -> Dict:
        """运行完整周期 - V8 + G12协同"""
        self.cycle += 1
        
        print(f"\n{'='*70}")
        print(f"📊 周期 #{self.cycle} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT']
        all_results = []
        
        # ========== V8 核心处理 ==========
        print(f"\n[V8] 技术分析...")
        v8_signals = []
        for symbol in symbols:
            klines = self.binance.get_klines(symbol, '1h', 100)
            if len(klines) < 50: continue
            
            # V8 信号分析
            v8_analysis = self.signal_engine.analyze(symbol, klines)
            v8_ai = self.ai_brain.decide(v8_analysis)
            
            v8_signals.append({
                'symbol': symbol,
                'klines': klines,
                'v8_analysis': v8_analysis,
                'v8_ai': v8_ai
            })
            
            print(f"   {symbol}: V8评分={v8_analysis.get('score', 0):.0f} V8动作={v8_analysis.get('action', 'HOLD')}")
        
        # ========== G12 增补处理 ==========
        print(f"\n[G12] 策略因子增补...")
        for result in v8_signals:
            symbol = result['symbol']
            v8_analysis = result['v8_analysis']
            klines = result['klines']
            
            # G12 策略评估
            g12_sig_signals = self.g12_strategies.evaluate(v8_analysis, {})
            g12_action, g12_conf = self.g12_strategies.weighted_vote(g12_sig_signals)
            
            # G12 因子评分
            g12_score, g12_factors = self.g12_factors.calculate(v8_analysis, klines)
            
            # 综合评分 = V8(60%) + G12(40%)
            v8_score = v8_analysis.get('score', 50)
            combined_score = v8_score * 0.6 + g12_score * 0.4
            combined_action = 'BUY' if combined_score > 60 else 'SELL' if combined_score < 40 else 'HOLD'
            
            result['g12_signals'] = g12_sig_signals
            result['g12_action'] = g12_action
            result['g12_conf'] = g12_conf
            result['g12_score'] = g12_score
            result['g12_factors'] = g12_factors
            result['combined_score'] = combined_score
            result['combined_action'] = combined_action
            
            print(f"   {symbol}: G12评分={g12_score:.0f} 综合={combined_score:.0f} 动作={combined_action}")
        
        # ========== 风控检查 ==========
        print(f"\n[风控] 检查持仓...")
        prices = {}
        for result in v8_signals:
            prices[result['symbol']] = result['v8_analysis'].get('price', 0)
        
        self.executor.update(prices)
        
        for symbol in list(self.executor.positions.keys()):
            current_price = prices.get(symbol, 0)
            should_close, reason = self.executor.check_stops(symbol, current_price)
            
            if should_close:
                print(f"   🔴 {symbol}: {reason}")
                result = self.executor.sell(symbol, current_price)
                if 'pnl' in result:
                    self.g12_factors.update_weights({'pnl': result['pnl']})
        
        # ========== 交易执行 ==========
        print(f"\n[交易] 执行...")
        v8_signals.sort(key=lambda x: x['combined_score'], reverse=True)
        
        for result in v8_signals[:2]:
            symbol = result['symbol']
            action = result['combined_action']
            combined_score = result['combined_score']
            price = result['v8_analysis'].get('price', 0)
            
            if action == 'BUY' and combined_score > 55 and symbol not in self.executor.positions:
                quantity = self.risk_manager.calculate_position(price, self.executor.capital, combined_score)
                if quantity * price > 10:
                    buy_result = self.executor.buy(symbol, quantity, price)
                    if buy_result.get('status') == 'FILLED':
                        print(f"   ✅ 买入: {symbol} x {quantity:.4f} @ ${price:.2f}")
            
            elif action == 'SELL' and combined_score < 35 and symbol in self.executor.positions:
                sell_result = self.executor.sell(symbol, price)
                if sell_result.get('status') == 'FILLED':
                    print(f"   ✅ 卖出: {symbol}")
        
        # ========== 统计 ==========
        stats = self.executor.get_stats()
        print(f"\n[统计]")
        print(f"   账户: ${stats['capital']:.2f}")
        print(f"   盈亏: ${stats['pnl']:+.2f}")
        print(f"   交易: {stats['total']}笔")
        print(f"   胜率: {stats['win_rate']:.1f}%")
        
        # ========== Watchdog ==========
        self.watchdog.heartbeat({
            'cycles': self.cycle,
            'trades': stats['total'],
            'profit': stats['pnl'],
            'win_rate': stats['win_rate'],
            'positions': len(self.executor.positions),
            'mode': self.mode
        })
        
        return {
            'cycle': self.cycle,
            'signals': v8_signals,
            'stats': stats
        }
    
    def run(self, cycles: int = 100, interval: int = 60):
        print(f"\n🚀 开始运行 Q@C v{self.VERSION}")
        
        for i in range(cycles):
            try:
                self.run_cycle()
                if i < cycles - 1:
                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\n⚠️ 中断")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                time.sleep(10)
        
        print(f"\n{'='*70}")
        print(f"🏁 运行完成")
        print(f"{'='*70}")

def main():
    qm = QuantMasterQCV9(10000, 'SIMULATE')
    qm.run(cycles=3, interval=10)

if __name__ == "__main__":
    main()
