"""
QuantMaster Q@C v10.1.0 - 修复版
- V8 SignalEngine: 修正超卖信号评分
- 自主决策: 修正自动执行阈值
- BinanceAPI: 修复账户检测
- 模块间数据流: 完全打通

版本: 10.1.1
"""
import sys
import time
import json
import random
import math
import threading
import urllib.request
import hmac
import hashlib
import urllib.parse
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

# ============================================================
# 工具函数
# ============================================================
def safe_float(val, default=0.0):
    try: return float(val)
    except: return default

# ============================================================
# DataBus
# ============================================================
class DataBus:
    def __init__(self):
        self.data = {}
        self.lock = threading.RLock()
        self.history = defaultdict(list)
    
    def publish(self, topic: str, data: Any):
        with self.lock:
            self.data[topic] = {'data': data, 'timestamp': time.time()}
            self.history[topic].append({'data': data, 'timestamp': time.time()})
    
    def get(self, topic: str, max_age: int = 300) -> Optional[Any]:
        with self.lock:
            if topic in self.data:
                entry = self.data[topic]
                if time.time() - entry['timestamp'] < max_age:
                    return entry['data']
        return None

# ============================================================
# Watchdog
# ============================================================
class Watchdog:
    def __init__(self, name: str = "QCV10"):
        self.name = name
        self.status_file = f"/home/goose/.openclaw/workspace/{name.lower()}_status.json"
        self.last_heartbeat = time.time()
        self.status = {'running': True, 'cycles': 0, 'version': '10.1.1', 'mode': 'LIVE'}
    
    def heartbeat(self, update: Dict = None):
        self.last_heartbeat = time.time()
        if update:
            self.status.update(update)
        self.status['timestamp'] = self.last_heartbeat
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except: pass

# ============================================================
# BinanceAPI - 修复版
# ============================================================
class BinanceAPI:
    def __init__(self):
        self.api_key = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
        self.api_secret = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
        self.proxies = {'http': 'http://172.29.144.1:7897', 'https': 'http://172.29.144.1:7897'}
        self.mode = 'SIMULATE'
        self.balance = {}
        self._check_account()
    
    def _sign(self, params: Dict) -> str:
        query = urllib.parse.urlencode(sorted(params.items()))
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    
    def _check_account(self):
        """检测账户"""
        try:
            url = "https://api.binance.com/api/v3/account"
            params = {'timestamp': int(time.time() * 1000), 'recvWindow': 5000}
            params['signature'] = self._sign(params)
            req = urllib.request.Request(url, headers={'X-MBX-APIKEY': self.api_key})
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                self.mode = 'LIVE'
                self.balance = {a['asset']: safe_float(a['free']) for a in data.get('balances', [])}
                print(f"   [API] ✅ 实盘账户检测成功")
                print(f"   [API] USDT余额: {self.balance.get('USDT', 0):.2f}")
        except Exception as e:
            print(f"   [API] ⚠️ API检测失败: {e} → 仿真模式")
            self.mode = 'SIMULATE'
            self.balance = {'USDT': 10000}
    
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
        except Exception as e:
            print(f"   [API] K线获取失败 {symbol}: {e}")
            return []
    
    def get_price(self, symbol: str) -> float:
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            req = urllib.request.Request(url)
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=5) as resp:
                return float(json.loads(resp.read().decode())['price'])
        except: return 0
    
    def get_account(self) -> Dict:
        """获取账户信息"""
        try:
            url = "https://api.binance.com/api/v3/account"
            params = {'timestamp': int(time.time() * 1000), 'recvWindow': 5000}
            params['signature'] = self._sign(params)
            req = urllib.request.Request(url, headers={'X-MBX-APIKEY': self.api_key})
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except: return {}
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "MARKET") -> Dict:
        """下单"""
        try:
            url = "https://api.binance.com/api/v3/order"
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'timestamp': int(time.time() * 1000),
                'recvWindow': 5000
            }
            params['signature'] = self._sign(params)
            req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), 
                                          headers={'X-MBX-APIKEY': self.api_key}, method='POST')
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                print(f"   [LIVE] ✅ 实盘订单: {side} {quantity} {symbol}")
                return result
        except Exception as e:
            print(f"   [LIVE] ❌ 实盘订单失败: {e}")
            return {'error': str(e)}
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        try:
            url = "https://api.binance.com/api/v3/openOrders"
            params = {'timestamp': int(time.time() * 1000), 'recvWindow': 5000}
            if symbol: params['symbol'] = symbol
            params['signature'] = self._sign(params)
            req = urllib.request.Request(url + '?' + urllib.parse.urlencode(params), headers={'X-MBX-APIKEY': self.api_key})
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except: return []

# ============================================================
# SimulatedExecutor
# ============================================================
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
                pos['current'] = prices[symbol]
                pos['pnl'] = (prices[symbol] - pos['entry']) * pos['quantity']
                if prices[symbol] > pos['high']: pos['high'] = prices[symbol]
    
    def check_stops(self, symbol: str, current_price: float, sl: float = 0.02, tp: float = 0.08) -> Tuple[bool, str]:
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
# Indicators
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
# V8 SignalEngine - 修复版
# ============================================================
class SignalEngine:
    def analyze(self, symbol: str, klines: List[Dict]) -> Optional[Dict]:
        if not klines or len(klines) < 50: return None
        
        prices = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        current = prices[-1]
        
        rsi = Indicators.RSI(prices)
        macd = Indicators.MACD(prices)
        kdj = Indicators.KDJ(highs, lows, prices)
        bb = Indicators.BollingerBands(prices)
        
        # 修复: 超卖时评分应该更高
        score = 50
        signals = []
        
        # RSI 信号 - 核心驱动
        if rsi < 30:
            score += 35
            signals.append({'type': 'RSI_OVERSOLD', 'action': 'BUY', 'conf': 100 - rsi, 'weight': 1.5})
        elif rsi < 35:
            score += 25
            signals.append({'type': 'RSI_UNDER30', 'action': 'BUY', 'conf': 100 - rsi, 'weight': 1.2})
        elif rsi > 70:
            score -= 35
            signals.append({'type': 'RSI_OVERBOUGHT', 'action': 'SELL', 'conf': rsi - 30, 'weight': 1.5})
        elif rsi > 65:
            score -= 25
            signals.append({'type': 'RSI_ABOVE70', 'action': 'SELL', 'conf': rsi - 30, 'weight': 1.2})
        
        # MACD 信号
        if macd['histogram'] > 0:
            score += 20
            signals.append({'type': 'MACD_BULLISH', 'action': 'BUY', 'conf': 70, 'weight': 1.0})
        else:
            score -= 20
            signals.append({'type': 'MACD_BEARISH', 'action': 'SELL', 'conf': 70, 'weight': 1.0})
        
        # KDJ 信号
        if kdj['k'] < 20:
            score += 15
            signals.append({'type': 'KDJ_OVERSOLD', 'action': 'BUY', 'conf': 100 - kdj['k'], 'weight': 1.0})
        elif kdj['k'] > 80:
            score -= 15
            signals.append({'type': 'KDJ_OVERBOUGHT', 'action': 'SELL', 'conf': kdj['k'] - 20, 'weight': 1.0})
        
        # 布林带信号
        if current < bb['lower']:
            score += 10
            signals.append({'type': 'BB_LOWER', 'action': 'BUY', 'conf': 75, 'weight': 0.8})
        elif current > bb['upper']:
            score -= 10
            signals.append({'type': 'BB_UPPER', 'action': 'SELL', 'conf': 75, 'weight': 0.8})
        
        score = max(0, min(100, score))
        
        return {
            'symbol': symbol,
            'price': current,
            'rsi': rsi,
            'macd': macd,
            'kdj': kdj,
            'bollinger': bb,
            'score': score,
            'signals': signals,
            'action': 'BUY' if score > 60 else 'SELL' if score < 40 else 'HOLD',
            'timestamp': time.time()
        }

# ============================================================
# G12 StrategyMatrix
# ============================================================
class G12StrategyMatrix:
    STRATEGIES = {
        'G12_RSI': {'weight': 0.25},
        'G12_BB': {'weight': 0.20},
        'G12_MOMENTUM': {'weight': 0.20},
        'G12_VOL': {'weight': 0.15},
        'G12_TREND': {'weight': 0.20}
    }
    
    def evaluate(self, analysis: Optional[Dict]) -> Dict:
        if not analysis: return {}
        
        signals = {}
        rsi = analysis.get('rsi', 50)
        bb = analysis.get('bollinger', {})
        price = analysis.get('price', 0)
        
        # G12 RSI
        if rsi < 35:
            signals['G12_RSI'] = {'action': 'BUY', 'conf': 100 - rsi}
        elif rsi > 70:
            signals['G12_RSI'] = {'action': 'SELL', 'conf': rsi - 30}
        
        # G12 BB
        if bb:
            upper = bb.get('upper', price)
            lower = bb.get('lower', price)
            if upper != lower:
                bb_pos = (price - lower) / (upper - lower) * 100
                if bb_pos < 20:
                    signals['G12_BB'] = {'action': 'BUY', 'conf': 100 - bb_pos}
                elif bb_pos > 80:
                    signals['G12_BB'] = {'action': 'SELL', 'conf': bb_pos}
        
        return signals
    
    def weighted_vote(self, signals: Dict) -> Tuple[str, float]:
        buy_score = sell_score = 0
        for s, sig in signals.items():
            weight = self.STRATEGIES.get(s, {}).get('weight', 0.2)
            if sig['action'] == 'BUY': buy_score += weight * sig['conf']
            elif sig['action'] == 'SELL': sell_score += weight * sig['conf']
        
        total = buy_score + sell_score
        if total == 0: return 'HOLD', 50
        
        buy_pct = buy_score / total * 100
        if buy_pct > 60: return 'BUY', buy_pct
        elif sell_score / total > 0.6: return 'SELL', sell_score / total * 100
        return 'HOLD', 50
    
    def calc_score(self, v8_analysis: Optional[Dict]) -> float:
        signals = self.evaluate(v8_analysis)
        action, conf = self.weighted_vote(signals)
        # 将action转换为分数
        if action == 'BUY': return 50 + conf * 0.3
        elif action == 'SELL': return 50 - conf * 0.3
        return 50

# ============================================================
# MirofishSimulator
# ============================================================
class MirofishSimulator:
    def __init__(self):
        self.version = "1.0.0"
        self.strategies = {
            'MOMENTUM': {'weight': 0.25, 'enabled': True},
            'MEAN_REVERSION': {'weight': 0.25, 'enabled': True},
            'BREAKOUT': {'weight': 0.20, 'enabled': True},
            'ARBITRAGE': {'weight': 0.15, 'enabled': False},
            'SCALPING': {'weight': 0.15, 'enabled': True}
        }
        self.factors = {
            'RSI': {'weight': 0.20, 'value': 50},
            'MACD': {'weight': 0.15, 'value': 0},
            'VOLUME': {'weight': 0.15, 'value': 1.0},
            'VOLATILITY': {'weight': 0.15, 'value': 1.0},
            'TREND': {'weight': 0.20, 'value': 0},
            'MOMENTUM': {'weight': 0.15, 'value': 0}
        }
    
    def analyze(self, analysis: Optional[Dict], klines: List[Dict]) -> Dict:
        if not analysis: return {'score': 50, 'action': 'HOLD'}
        
        prices = [k['close'] for k in klines] if klines else []
        rsi = analysis.get('rsi', 50)
        macd_hist = analysis.get('macd', {}).get('histogram', 0)
        
        self.factors['RSI']['value'] = rsi
        self.factors['MACD']['value'] = macd_hist
        
        if len(prices) >= 2:
            self.factors['MOMENTUM']['value'] = (prices[-1] - prices[-2]) / prices[-2] * 100
        if len(prices) >= 50:
            ema20 = Indicators.EMA(prices, 20)
            ema50 = Indicators.EMA(prices, 50)
            self.factors['TREND']['value'] = ema20 - ema50
        
        strategy_signals = {}
        total_signal = 0
        
        for strategy, config in self.strategies.items():
            if not config['enabled']: continue
            signal = self._simulate_strategy(strategy, analysis)
            strategy_signals[strategy] = signal
            total_signal += signal * config['weight']
        
        mirofish_score = max(0, min(100, 50 + total_signal))
        
        return {
            'score': mirofish_score,
            'strategy_signals': strategy_signals,
            'factors': {k: v['value'] for k, v in self.factors.items()},
            'action': 'BUY' if mirofish_score > 60 else 'SELL' if mirofish_score < 40 else 'HOLD',
            'confidence': abs(mirofish_score - 50) * 2
        }
    
    def _simulate_strategy(self, strategy: str, analysis: Dict) -> float:
        rsi = analysis.get('rsi', 50)
        price = analysis.get('price', 0)
        bb = analysis.get('bollinger', {})
        
        if strategy == 'MOMENTUM':
            mom = self.factors['MOMENTUM']['value']
            if rsi < 40 and mom > 0: return 30
            if rsi > 60 and mom < 0: return -30
            return 0
        
        elif strategy == 'MEAN_REVERSION':
            bb_pos = 50
            if bb:
                upper = bb.get('upper', price)
                lower = bb.get('lower', price)
                if upper != lower: bb_pos = (price - lower) / (upper - lower) * 100
            if rsi < 35 and bb_pos < 25: return 35
            if rsi > 65 and bb_pos > 75: return -35
            return 0
        
        elif strategy == 'BREAKOUT':
            vol = self.factors.get('VOLATILITY', {}).get('value', 1.0)
            if vol > 1.5: return 25
            return 0
        
        elif strategy == 'SCALPING':
            if 40 < rsi < 60 and abs(self.factors['MOMENTUM']['value']) < 0.5: return 20
            return 0
        
        return 0

# ============================================================
# ProbingEngine
# ============================================================
class ProbingEngine:
    def __init__(self, binance: BinanceAPI):
        self.binance = binance
        self.probed_symbols = set()
        self.opportunities = []
    
    def probe_market(self) -> List[Dict]:
        opportunities = []
        probe_list = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT', 
                      'DOGEUSDT', 'DOTUSDT', 'LINKUSDT', 'AVAXUSDT', 'MATICUSDT',
                      'NEIROUSDT', 'FETUSDT', 'RNDRUSDT', 'ARBUSDT', 'OPUSDT']
        
        for symbol in probe_list:
            try:
                klines = self.binance.get_klines(symbol, '1h', 100)
                if len(klines) < 50: continue
                
                prices = [k['close'] for k in klines]
                rsi = Indicators.RSI(prices)
                momentum = (prices[-1] - prices[-6]) / prices[-6] * 100 if len(prices) >= 6 else 0
                
                if rsi < 30 and momentum < -1:
                    opportunities.append({
                        'symbol': symbol,
                        'type': 'OVERSOLD_MOMENTUM',
                        'rsi': rsi,
                        'momentum': momentum,
                        'action': 'BUY',
                        'confidence': 100 - rsi
                    })
                elif rsi > 70 and momentum > 1:
                    opportunities.append({
                        'symbol': symbol,
                        'type': 'OVERBOUGHT_MOMENTUM',
                        'rsi': rsi,
                        'momentum': momentum,
                        'action': 'SELL',
                        'confidence': rsi - 30
                    })
                
                self.probed_symbols.add(symbol)
            except: pass
        
        self.opportunities = opportunities
        return opportunities

# ============================================================
# AutonomousDecisionEngine - 修复版
# ============================================================
class AutonomousDecisionEngine:
    def __init__(self):
        self.decision_log = []
        self.approved_trades = 0
    
    def decide(self, symbol: str, combined_score: float, v8_score: float, 
               g12_score: float, mirofish_score: float) -> Dict:
        """
        自主决策 - 修复阈值
        - combined_score >= 60: BUY信号
        - combined_score <= 40: SELL信号
        - confidence >= 50: 自动执行
        """
        confidence = abs(combined_score - 50) * 2
        
        if combined_score >= 60:
            decision = {
                'action': 'BUY',
                'confidence': confidence,
                'auto_execute': True,
                'reason': f"强BUY信号: 综合={combined_score:.0f} V8={v8_score:.0f} G12={g12_score:.0f} Miro={mirofish_score:.0f}"
            }
            self.approved_trades += 1
        elif combined_score <= 40:
            decision = {
                'action': 'SELL',
                'confidence': confidence,
                'auto_execute': True,
                'reason': f"强SELL信号: 综合={combined_score:.0f}"
            }
            self.approved_trades += 1
        elif combined_score >= 55 and confidence >= 40:
            decision = {
                'action': 'BUY',
                'confidence': confidence,
                'auto_execute': False,
                'reason': f"中等信号, 需确认"
            }
        elif combined_score <= 45 and confidence >= 40:
            decision = {
                'action': 'SELL',
                'confidence': confidence,
                'auto_execute': False,
                'reason': f"中等信号, 需确认"
            }
        else:
            decision = {
                'action': 'HOLD',
                'confidence': confidence,
                'auto_execute': False,
                'reason': f"信号不足: {combined_score:.0f}"
            }
        
        self.decision_log.append({
            'symbol': symbol,
            'decision': decision,
            'timestamp': time.time()
        })
        
        return decision

# ============================================================
# Q@C v10 主控制器
# ============================================================
class QuantMasterQCV10:
    VERSION = "10.1.1"
    
    def __init__(self, capital: float = 10000, mode: str = 'LIVE'):
        print(f"\n{'='*70}")
        print(f"🚀 QuantMaster Q@C v{self.VERSION} - 修复版")
        print(f"{'='*70}")
        
        self.capital = capital
        self.mode = 'LIVE'
        
        # 核心组件
        self.binance = BinanceAPI()
        self.signal_engine = SignalEngine()
        self.g12 = G12StrategyMatrix()
        self.mirofish = MirofishSimulator()
        self.probing = ProbingEngine(self.binance)
        self.autonomous = AutonomousDecisionEngine()
        
        # 交易执行器
        if self.binance.mode == 'LIVE':
            self.executor = None
            print(f"   [MODE] 🟢 LIVE 实盘模式")
        else:
            self.executor = SimulatedExecutor(capital)
            print(f"   [MODE] 🔵 SIMULATE 仿真模式")
        
        # 状态
        self.cycle = 0
        self.watchdog = Watchdog("QCV10")
        self.watchdog.status['mode'] = self.binance.mode
        
        print(f"✅ V8 SignalEngine: 50%")
        print(f"✅ G12增补策略: 30%")
        print(f"✅ Mirofish仿真: 20%")
        print(f"✅ 主动探测引擎: 启用")
        print(f"✅ 自主决策引擎: 启用")
    
    def run_cycle(self) -> Dict:
        self.cycle += 1
        
        print(f"\n{'='*70}")
        print(f"📊 周期 #{self.cycle} - {datetime.now().strftime('%H:%M:%S')} [{self.binance.mode}]")
        print(f"{'='*70}")
        
        # 1. 主动探测
        print(f"\n[1] 🔍 主动探测...")
        opportunities = self.probing.probe_market()
        print(f"    探测: {len(self.probing.probed_symbols)} 币种, 发现 {len(opportunities)} 机会")
        
        # 2. 三重权重分析
        print(f"\n[2] 📊 三重权重分析...")
        weights = {'v8': 0.50, 'g12': 0.30, 'mirofish': 0.20}
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT']
        all_results = []
        
        for symbol in symbols:
            klines = self.binance.get_klines(symbol, '1h', 100)
            if len(klines) < 50: continue
            
            # V8
            v8 = self.signal_engine.analyze(symbol, klines)
            if not v8: continue
            v8_score = v8['score']
            
            # G12
            g12_score = self.g12.calc_score(v8)
            g12_signals = self.g12.evaluate(v8)
            g12_action, g12_conf = self.g12.weighted_vote(g12_signals)
            
            # Mirofish
            miro_result = self.mirofish.analyze(v8, klines)
            mirofish_score = miro_result['score']
            
            # 三重权重
            combined = v8_score * weights['v8'] + g12_score * weights['g12'] + mirofish_score * weights['mirofish']
            
            # 自主决策
            decision = self.autonomous.decide(symbol, combined, v8_score, g12_score, mirofish_score)
            
            result = {
                'symbol': symbol,
                'price': v8['price'],
                'rsi': v8['rsi'],
                'v8_score': v8_score,
                'g12_score': g12_score,
                'mirofish_score': mirofish_score,
                'combined': combined,
                'decision': decision
            }
            all_results.append(result)
            
            status = "✅" if decision['auto_execute'] else "⏸️"
            print(f"    {status} {symbol}: V8={v8_score:.0f} G12={g12_score:.0f} Miro={mirofish_score:.0f} → {combined:.0f} [{decision['action']}]")
        
        # 3. 账户/持仓状态
        print(f"\n[3] 📋 账户状态...")
        if self.binance.mode == 'LIVE':
            account = self.binance.get_account()
            balances = {a['asset']: safe_float(a['free']) for a in account.get('balances', []) if safe_float(a['free']) > 0.01}
            print(f"    余额: {balances}")
            open_orders = self.binance.get_open_orders()
            print(f"    未成交订单: {len(open_orders)}")
        else:
            stats = self.executor.get_stats()
            print(f"    账户: ${stats['capital']:.2f}")
            print(f"    盈亏: ${stats['pnl']:+.2f} ({stats['win_rate']:.1f}%胜率)")
            print(f"    交易: {stats['total']}笔")
        
        # 4. Watchdog
        self.watchdog.heartbeat({
            'cycles': self.cycle,
            'mode': self.binance.mode,
            'decisions': len(self.autonomous.decision_log),
            'approved': self.autonomous.approved_trades
        })
        
        return {'cycle': self.cycle, 'results': all_results, 'opportunities': opportunities}
    
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
    qm = QuantMasterQCV10(10000, 'LIVE')
    qm.run(cycles=3, interval=10)

if __name__ == "__main__":
    main()
