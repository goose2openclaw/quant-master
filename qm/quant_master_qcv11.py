"""
QuantMaster Q@C v11 - 完全体
- V8核心 + G12增补 + Mirofish仿真
- 全模块打通 + API完全接管
- Skill/APK/WebUI/GitHub 一体化

版本: 11.0.0
"""
import sys
import time
import json
import math
import threading
import urllib.request
import hmac
import hashlib
import urllib.parse
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

# ============================================================
# 工具
# ============================================================
def safe_float(v, default=0.0):
    try: return float(v)
    except: return default

# ============================================================
# DataBus
# ============================================================
class DataBus:
    def __init__(self):
        self.data = {}
        self.lock = threading.RLock()
        self.history = defaultdict(list)
    
    def publish(self, topic: str, data):
        with self.lock:
            self.data[topic] = {'data': data, 'ts': time.time()}
            self.history[topic].append({'data': data, 'ts': time.time()})
            if len(self.history[topic]) > 1000:
                self.history[topic] = self.history[topic][-500:]
    
    def get(self, topic: str, max_age=300):
        with self.lock:
            if topic in self.data:
                e = self.data[topic]
                if time.time() - e['ts'] < max_age:
                    return e['data']
        return None
    
    def get_history(self, topic: str, limit=100):
        with self.lock:
            return self.history.get(topic, [])[-limit:]

# ============================================================
# Watchdog
# ============================================================
class Watchdog:
    def __init__(self, name="QCV11"):
        self.name = name
        self.status_file = f"/home/goose/.openclaw/workspace/{name.lower()}_status.json"
        self.last_ts = time.time()
        self.last_cycle_ts = time.time()
        self.cycle_count = 0
        self.status = {
            'running': True, 
            'cycles': 0, 
            'version': '11.0.0', 
            'mode': 'LIVE',
            'health': 'HEALTHY',
            'last_heartbeat': None,
            'uptime': 0,
            'responsiveness': 0,
            'decisions': 0,
            'approved_trades': 0
        }
        self.health_log = []
    
    def heartbeat(self, update=None):
        now = time.time()
        self.last_ts = now
        self.cycle_count += 1
        
        if update: 
            self.status.update(update)
        
        # Calculate responsiveness (how close to 60s target)
        cycle_interval = now - self.last_cycle_ts
        if cycle_interval > 0 and cycle_interval < 300:
            # 60s = 100%, 120s = 50%, 180s+ = 0%
            self.status['responsiveness'] = max(0, min(100, 100 - (cycle_interval - 60) * 2.5))
        else:
            self.status['responsiveness'] = 100 if cycle_interval <= 60 else 50
        self.last_cycle_ts = now
        
        self.status['cycles'] = self.cycle_count
        self.status['last_heartbeat'] = now
        self.status['uptime'] = now - self.last_ts if self.last_ts else 0
        self.status['health'] = self._check_health()
        
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except: pass
        
        # Log health
        self.health_log.append({'ts': now, 'health': self.status['health'], 'cycles': self.cycle_count})
        if len(self.health_log) > 100:
            self.health_log = self.health_log[-50:]
    
    def _check_health(self):
        now = time.time()
        if now - self.last_ts > 120:
            return 'UNHEALTHY'
        elif now - self.last_ts > 90:
            return 'DEGRADED'
        return 'HEALTHY'
    
    def get_health_report(self):
        return {
            'health': self.status.get('health', 'UNKNOWN'),
            'cycles': self.cycle_count,
            'responsiveness': self.status.get('responsiveness', 0),
            'uptime_seconds': time.time() - self.last_ts,
            'recent_health': self.health_log[-5:]
        }

# ============================================================
# Binance API 完全体
# ============================================================
class BinanceAPI:
    def __init__(self):
        self.api_key = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
        self.api_secret = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
        self.proxies = {'http': 'http://172.29.144.1:7897', 'https': 'http://172.29.144.1:7897'}
        self.mode = 'SIMULATE'
        self.balance = {}
        self.trade_history = []
        self._check_account()
    
    def _sign(self, params: Dict) -> str:
        q = urllib.parse.urlencode(sorted(params.items()))
        return hmac.new(self.api_secret.encode(), q.encode(), hashlib.sha256).hexdigest()
    
    def _check_account(self):
        """检测账户"""
        try:
            ts = int(time.time() * 1000)
            params = {'timestamp': ts, 'recvWindow': 5000}
            query = urllib.parse.urlencode(sorted(params.items()))
            signature = self._sign(params)
            url = f"https://api.binance.com/api/v3/account?{query}&signature={signature}"
            req = urllib.request.Request(url, headers={'X-MBX-APIKEY': self.api_key})
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                self.mode = 'LIVE'
                self.balance = {a['asset']: safe_float(a['free']) for a in data.get('balances', [])}
                print(f"   [API] 🟢 实盘账户: USDT={self.balance.get('USDT',0):.2f}")
        except Exception as e:
            print(f"   [API] 🔵 仿真模式 (API错误: {e})")
            self.mode = 'SIMULATE'
            self.balance = {'USDT': 10000}
    
    def get_klines(self, symbol: str, interval='1h', limit=100) -> List[Dict]:
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
            print(f"   [API] K线失败 {symbol}: {e}")
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
        try:
            ts = int(time.time() * 1000)
            params = {'timestamp': ts, 'recvWindow': 5000}
            query = urllib.parse.urlencode(sorted(params.items()))
            signature = self._sign(params)
            url = f"https://api.binance.com/api/v3/account?{query}&signature={signature}"
            req = urllib.request.Request(url, headers={'X-MBX-APIKEY': self.api_key})
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except: return {}
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type="MARKET") -> Dict:
        try:
            ts = int(time.time() * 1000)
            params = {
                'symbol': symbol, 'side': side, 'type': order_type,
                'quantity': quantity, 'timestamp': ts, 'recvWindow': 5000
            }
            query = urllib.parse.urlencode(sorted(params.items()))
            signature = self._sign(params)
            # POST with signature in body
            post_data = f"{query}&signature={signature}"
            req = urllib.request.Request(
                "https://api.binance.com/api/v3/order",
                data=post_data.encode(),
                headers={'X-MBX-APIKEY': self.api_key},
                method='POST'
            )
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                print(f"   [LIVE] ✅ 订单成功: {side} {quantity} {symbol}")
                self.trade_history.append({'symbol': symbol, 'side': side, 'qty': quantity, 'ts': time.time()})
                return result
        except Exception as e:
            print(f"   [LIVE] ❌ 订单失败: {e}")
            return {'error': str(e)}
    
    def get_open_orders(self, symbol=None) -> List[Dict]:
        try:
            url = "https://api.binance.com/api/v3/openOrders"
            params = {'timestamp': int(time.time()*1000), 'recvWindow': 5000}
            if symbol: params['symbol'] = symbol
            params['signature'] = self._sign(params)
            req = urllib.request.Request(url+'?'+urllib.parse.urlencode(params), headers={'X-MBX-APIKEY': self.api_key})
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except: return []
    
    def cancel_order(self, symbol: str, orderId: str) -> Dict:
        try:
            url = "https://api.binance.com/api/v3/order"
            params = {'symbol': symbol, 'orderId': orderId, 'timestamp': int(time.time()*1000), 'recvWindow': 5000}
            params['signature'] = self._sign(params)
            req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(),
                                        headers={'X-MBX-APIKEY': self.api_key}, method='DELETE')
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            with opener.open(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except: return {'error': 'cancel failed'}

# ============================================================
# SimulatedExecutor
# ============================================================
class SimulatedExecutor:
    def __init__(self, capital=10000):
        self.capital = capital
        self.initial_capital = capital
        self.positions = {}
        self.trade_history = []
        self.slippage = 0.001
    
    def buy(self, symbol: str, quantity: float, price: float) -> Dict:
        cost = price * quantity * (1 + self.slippage)
        if cost > self.capital: return {'error': 'Insufficient capital'}
        self.capital -= cost
        self.positions[symbol] = {'qty': quantity, 'entry': price, 'high': price, 'ts': time.time()}
        return {'status': 'FILLED', 'cost': cost}
    
    def sell(self, symbol: str, price: float = None) -> Dict:
        if symbol not in self.positions: return {'error': 'No position'}
        pos = self.positions[symbol]
        sp = price or pos['entry']
        revenue = sp * pos['qty'] * (1 - self.slippage)
        pnl = revenue - pos['entry'] * pos['qty']
        self.capital += revenue
        self.trade_history.append({'symbol': symbol, 'pnl': pnl, 'entry': pos['entry'], 'exit': sp})
        del self.positions[symbol]
        return {'status': 'FILLED', 'pnl': pnl}
    
    def update(self, prices: Dict):
        for sym, pos in self.positions.items():
            if sym in prices:
                pos['current'] = prices[sym]
                pos['pnl'] = (prices[sym] - pos['entry']) * pos['qty']
                if prices[sym] > pos['high']: pos['high'] = prices[sym]
    
    def check_stops(self, symbol: str, price: float, sl=0.02, tp=0.08) -> Tuple[bool, str]:
        if symbol not in self.positions: return False, ''
        pos = self.positions[symbol]
        pnl_pct = (price - pos['entry']) / pos['entry'] * 100
        if pnl_pct <= -sl*100: return True, 'STOP_LOSS'
        trailing = (pos['high'] - price) / pos['high'] * 100
        if pnl_pct >= tp*100 and trailing >= 3: return True, 'TAKE_PROFIT'
        return False, ''
    
    def get_stats(self) -> Dict:
        if not self.trade_history: return {'total': 0, 'win_rate': 0, 'pnl': 0, 'capital': self.capital}
        wins = [t for t in self.trade_history if t['pnl'] > 0]
        return {'total': len(self.trade_history), 'win_rate': len(wins)/len(self.trade_history)*100,
                'pnl': sum(t['pnl'] for t in self.trade_history), 'capital': self.capital}

# ============================================================
# Indicators
# ============================================================
class Indicators:
    @staticmethod
    def RSI(prices: List[float], period=14) -> float:
        if len(prices) < period+1: return 50
        deltas = [prices[i]-prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        ag = sum(gains)/period
        al = sum(losses)/period
        if al == 0: return 100
        return 100 - (100/(1 + ag/al))
    
    @staticmethod
    def EMA(data: List[float], period: int) -> float:
        if len(data) < period: return sum(data)/len(data) if data else 0
        mult = 2/(period+1)
        ema = sum(data[:period])/period
        for p in data[period:]: ema = (p-ema)*mult + ema
        return ema
    
    @staticmethod
    def MACD(prices: List[float], fast=12, slow=26) -> Dict[str, float]:
        if len(prices) < slow: return {'macd': 0, 'signal': 0, 'histogram': 0}
        ef = Indicators.EMA(prices, fast)
        es = Indicators.EMA(prices, slow)
        macd = ef - es
        return {'macd': macd, 'signal': macd*0.9, 'histogram': macd*0.1}
    
    @staticmethod
    def KDJ(highs, lows, closes, period=9) -> Dict[str, float]:
        if len(closes) < period: return {'k': 50, 'd': 50, 'j': 50}
        rsv_vals = []
        for i in range(period-1, len(closes)):
            ph = max(highs[i-period+1:i+1])
            pl = min(lows[i-period+1:i+1])
            rsv = (closes[i]-pl)/(ph-pl+1e-10)*100
            rsv_vals.append(rsv)
        k = d = 50
        for rsv in rsv_vals:
            k = 2/3*k + 1/3*rsv
            d = 2/3*d + 1/3*k
        return {'k': k, 'd': d, 'j': 3*k-2*d}
    
    @staticmethod
    def BollingerBands(prices: List[float], period=20, std=2) -> Dict[str, float]:
        if len(prices) < period:
            sma = sum(prices)/len(prices)
            return {'upper': sma, 'middle': sma, 'lower': sma}
        middle = sum(prices[-period:])/period
        var = sum((p-middle)**2 for p in prices[-period:])/period
        std_val = math.sqrt(var)
        return {'upper': middle+std*std_val, 'middle': middle, 'lower': middle-std*std_val}

# ============================================================
# V8 SignalEngine
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
        
        score = 50
        signals = []
        
        # RSI - 核心
        if rsi < 30:
            score += 40
            signals.append({'type': 'RSI_OVERSOLD', 'action': 'BUY', 'conf': 100-rsi, 'w': 1.5})
        elif rsi < 35:
            score += 25
            signals.append({'type': 'RSI_UNDER35', 'action': 'BUY', 'conf': 100-rsi, 'w': 1.2})
        elif rsi > 70:
            score -= 40
            signals.append({'type': 'RSI_OVERBOUGHT', 'action': 'SELL', 'conf': rsi-30, 'w': 1.5})
        elif rsi > 65:
            score -= 25
            signals.append({'type': 'RSI_ABOVE65', 'action': 'SELL', 'conf': rsi-30, 'w': 1.2})
        
        # MACD
        if macd['histogram'] > 0:
            score += 20
            signals.append({'type': 'MACD_BULL', 'action': 'BUY', 'conf': 70, 'w': 1.0})
        else:
            score -= 20
            signals.append({'type': 'MACD_BEAR', 'action': 'SELL', 'conf': 70, 'w': 1.0})
        
        # KDJ
        if kdj['k'] < 20:
            score += 15
            signals.append({'type': 'KDJ_OVERSOLD', 'action': 'BUY', 'conf': 100-kdj['k'], 'w': 1.0})
        elif kdj['k'] > 80:
            score -= 15
            signals.append({'type': 'KDJ_OVERBOUGHT', 'action': 'SELL', 'conf': kdj['k']-20, 'w': 1.0})
        
        # BB
        if current < bb['lower']:
            score += 10
            signals.append({'type': 'BB_LOWER', 'action': 'BUY', 'conf': 75, 'w': 0.8})
        elif current > bb['upper']:
            score -= 10
            signals.append({'type': 'BB_UPPER', 'action': 'SELL', 'conf': 75, 'w': 0.8})
        
        return {
            'symbol': symbol, 'price': current, 'rsi': rsi, 'macd': macd,
            'kdj': kdj, 'bollinger': bb, 'score': max(0, min(100, score)),
            'signals': signals, 'action': 'BUY' if score > 60 else 'SELL' if score < 40 else 'HOLD'
        }

# ============================================================
# G12 StrategyMatrix
# ============================================================
class G12StrategyMatrix:
    STRATEGIES = {
        'G12_RSI': {'w': 0.25},
        'G12_BB': {'w': 0.20},
        'G12_MOMENTUM': {'w': 0.20},
        'G12_VOL': {'w': 0.15},
        'G12_TREND': {'w': 0.20}
    }
    
    def evaluate(self, analysis: Optional[Dict]) -> Dict:
        if not analysis: return {}
        signals = {}
        rsi = analysis.get('rsi', 50)
        bb = analysis.get('bollinger', {})
        price = analysis.get('price', 0)
        
        if rsi < 35: signals['G12_RSI'] = {'action': 'BUY', 'conf': 100-rsi}
        elif rsi > 70: signals['G12_RSI'] = {'action': 'SELL', 'conf': rsi-30}
        
        if bb:
            upper = bb.get('upper', price)
            lower = bb.get('lower', price)
            if upper != lower:
                bb_pos = (price-lower)/(upper-lower)*100
                if bb_pos < 20: signals['G12_BB'] = {'action': 'BUY', 'conf': 100-bb_pos}
                elif bb_pos > 80: signals['G12_BB'] = {'action': 'SELL', 'conf': bb_pos}
        
        return signals
    
    def weighted_vote(self, signals: Dict) -> Tuple[str, float]:
        buy_s = sell_s = 0
        for s, sig in signals.items():
            w = self.STRATEGIES.get(s, {}).get('w', 0.2)
            if sig['action'] == 'BUY': buy_s += w * sig['conf']
            elif sig['action'] == 'SELL': sell_s += w * sig['conf']
        
        total = buy_s + sell_s
        if total == 0: return 'HOLD', 50
        bp = buy_s/total*100
        if bp > 60: return 'BUY', bp
        elif sell_s/total > 0.6: return 'SELL', sell_s/total*100
        return 'HOLD', 50
    
    def calc_score(self, analysis: Optional[Dict]) -> float:
        sigs = self.evaluate(analysis)
        act, conf = self.weighted_vote(sigs)
        if act == 'BUY': return 50 + conf*0.3
        elif act == 'SELL': return 50 - conf*0.3
        return 50

# ============================================================
# MirofishSimulator
# ============================================================
class MirofishSimulator:
    def __init__(self):
        self.version = "2.0.0"
        self.strategies = {
            'MOMENTUM': {'w': 0.25, 'enabled': True},
            'MEAN_REVERSION': {'w': 0.25, 'enabled': True},
            'BREAKOUT': {'w': 0.20, 'enabled': True},
            'SCALPING': {'w': 0.15, 'enabled': True},
            'TREND_RIDER': {'w': 0.15, 'enabled': True}
        }
        self.factors = {k: {'w': 1.0, 'v': 0} for k in ['RSI','MACD','VOLUME','VOLATILITY','TREND','MOMENTUM']}
    
    def analyze(self, analysis: Optional[Dict], klines: List[Dict]) -> Dict:
        if not analysis: return {'score': 50, 'action': 'HOLD'}
        prices = [k['close'] for k in klines] if klines else []
        rsi = analysis.get('rsi', 50)
        macd_h = analysis.get('macd', {}).get('histogram', 0)
        
        self.factors['RSI']['v'] = rsi
        self.factors['MACD']['v'] = macd_h
        if len(prices) >= 2:
            self.factors['MOMENTUM']['v'] = (prices[-1]-prices[-2])/prices[-2]*100
        if len(prices) >= 50:
            self.factors['TREND']['v'] = Indicators.EMA(prices, 20) - Indicators.EMA(prices, 50)
        
        sig_s = {}
        total = 0
        for strat, cfg in self.strategies.items():
            if not cfg['enabled']: continue
            s = self._simulate(strat, analysis)
            sig_s[strat] = s
            total += s * cfg['w']
        
        score = max(0, min(100, 50 + total))
        return {'score': score, 'signals': sig_s, 'action': 'BUY' if score > 60 else 'SELL' if score < 40 else 'HOLD'}
    
    def _simulate(self, strategy: str, analysis: Dict) -> float:
        rsi = analysis.get('rsi', 50)
        price = analysis.get('price', 0)
        bb = analysis.get('bollinger', {})
        mom = self.factors['MOMENTUM']['v']
        
        if strategy == 'MOMENTUM':
            if rsi < 40 and mom > 0: return 30
            if rsi > 60 and mom < 0: return -30
        elif strategy == 'MEAN_REVERSION':
            bb_pos = 50
            if bb:
                u, l = bb.get('upper', price), bb.get('lower', price)
                if u != l: bb_pos = (price-l)/(u-l)*100
            if rsi < 35 and bb_pos < 25: return 35
            if rsi > 65 and bb_pos > 75: return -35
        elif strategy == 'BREAKOUT':
            vol = self.factors.get('VOLATILITY', {}).get('v', 1.0)
            if vol > 1.5: return 25
        elif strategy == 'SCALPING':
            if 40 < rsi < 60 and abs(mom) < 0.5: return 20
        elif strategy == 'TREND_RIDER':
            trend = self.factors['TREND']['v']
            if trend > 0 and rsi < 60: return 25
            if trend < 0 and rsi > 40: return -25
        return 0

# ============================================================
# ProbingEngine
# ============================================================
class ProbingEngine:
    def __init__(self, binance: BinanceAPI):
        self.binance = binance
        self.probed = set()
        self.opps = []
    
    def probe(self) -> List[Dict]:
        opps = []
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT',
                   'DOGEUSDT', 'DOTUSDT', 'LINKUSDT', 'AVAXUSDT', 'MATICUSDT',
                   'NEIROUSDT', 'FETUSDT', 'RNDRUSDT', 'ARBUSDT', 'OPUSDT']
        
        for sym in symbols:
            try:
                kl = self.binance.get_klines(sym, '1h', 100)
                if len(kl) < 50: continue
                prices = [k['close'] for k in kl]
                rsi = Indicators.RSI(prices)
                mom = (prices[-1]-prices[-6])/prices[-6]*100 if len(prices) >= 6 else 0
                
                if rsi < 30 and mom < -1:
                    opps.append({'symbol': sym, 'type': 'OVERSOLD', 'rsi': rsi, 'mom': mom, 'action': 'BUY'})
                elif rsi > 70 and mom > 1:
                    opps.append({'symbol': sym, 'type': 'OVERBOUGHT', 'rsi': rsi, 'mom': mom, 'action': 'SELL'})
                self.probed.add(sym)
            except: pass
        
        self.opps = opps
        return opps

# ============================================================
# AutonomousDecision
# ============================================================
class AutonomousDecision:
    def __init__(self):
        self.log = []
        self.approved = 0
    
    def decide(self, symbol: str, combined: float, v8: float, g12: float, miro: float) -> Dict:
        # 激进阈值: BUY >= 55, SELL <= 45
        if combined >= 55:
            d = {'action': 'BUY', 'auto': True, 'reason': f"BUY信号 综合={combined:.0f}"}
            self.approved += 1
        elif combined <= 45:
            d = {'action': 'SELL', 'auto': True, 'reason': f"SELL信号 综合={combined:.0f}"}
            self.approved += 1
        else:
            d = {'action': 'HOLD', 'auto': False, 'reason': f"观望 综合={combined:.0f}"}
        
        self.log.append({'symbol': symbol, 'd': d, 'ts': time.time()})
        return d

# ============================================================
# Q@C v11 主控制器
# ============================================================
class QuantMasterQCV11:
    VERSION = "11.0.0"
    
    def __init__(self, capital=10000):
        print(f"\n{'='*70}")
        print(f"🚀 QuantMaster Q@C v{self.VERSION} - 完全体")
        print(f"{'='*70}")
        
        self.capital = capital
        self.binance = BinanceAPI()
        self.signal_engine = SignalEngine()
        self.g12 = G12StrategyMatrix()
        self.mirofish = MirofishSimulator()
        self.probing = ProbingEngine(self.binance)
        self.autonomous = AutonomousDecision()
        
        if self.binance.mode == 'LIVE':
            self.executor = None
            print(f"   [MODE] 🟢 LIVE 实盘")
        else:
            self.executor = SimulatedExecutor(capital)
            print(f"   [MODE] 🔵 SIMULATE 仿真")
        
        self.cycle = 0
        self.watchdog = Watchdog("QCV11")
        self.watchdog.status['mode'] = self.binance.mode
        self.data_bus = DataBus()
        
        print(f"✅ V8 50% + G12 30% + Mirofish 20%")
        print(f"✅ API完全接管: {'实盘' if self.binance.mode=='LIVE' else '仿真'}")
    
    def run_cycle(self) -> Dict:
        self.cycle += 1
        ts = datetime.now().strftime('%H:%M:%S')
        
        print(f"\n{'='*70}")
        print(f"📊 #{self.cycle} [{ts}] {'LIVE' if self.binance.mode=='LIVE' else 'SIM'}")
        print(f"{'='*70}")
        
        # 1. 探测
        print(f"\n[1] 🔍 探测: ", end="")
        opps = self.probing.probe()
        print(f"{len(self.probing.probed)}币种, {len(opps)}机会")
        
        # 2. 分析
        print(f"\n[2] 📊 分析:")
        weights = {'v8': 0.50, 'g12': 0.30, 'miro': 0.20}
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT']
        results = []
        
        for sym in symbols:
            kl = self.binance.get_klines(sym, '1h', 100)
            if len(kl) < 50: continue
            
            v8 = self.signal_engine.analyze(sym, kl)
            if not v8: continue
            
            v8_s = v8['score']
            g12_s = self.g12.calc_score(v8)
            miro_s = self.mirofish.analyze(v8, kl)['score']
            combined = v8_s*weights['v8'] + g12_s*weights['g12'] + miro_s*weights['miro']
            
            d = self.autonomous.decide(sym, combined, v8_s, g12_s, miro_s)
            
            results.append({
                'symbol': sym, 'price': v8['price'], 'rsi': v8['rsi'],
                'v8': v8_s, 'g12': g12_s, 'miro': miro_s,
                'combined': combined, 'decision': d
            })
            
            icon = "✅" if d['auto'] else "⏸️"
            print(f"    {icon} {sym}: V8={v8_s:.0f} G12={g12_s:.0f} Miro={miro_s:.0f} → {combined:.0f} [{d['action']}]")
        
        # 3. 交易
        print(f"\n[3] 💰 交易:")
        if self.binance.mode == 'LIVE':
            self._exec_live(results)
        else:
            self._exec_sim(results)
        
        # 4. 账户
        print(f"\n[4] 📋 账户:")
        if self.binance.mode == 'LIVE':
            acc = self.binance.get_account()
            bals = {a['asset']: safe_float(a['free']) for a in acc.get('balances',[]) if safe_float(a['free']) > 0.01}
            print(f"    余额: {bals}")
            print(f"    订单: {len(self.binance.get_open_orders())}")
        else:
            st = self.executor.get_stats()
            print(f"    ${st['capital']:.2f} ({st['pnl']:+.2f}) 胜率:{st['win_rate']:.0f}%")
        
        # 5. Watchdog
        health = self.watchdog.get_health_report()
        self.watchdog.heartbeat({
            'cycles': self.cycle, 
            'mode': self.binance.mode,
            'approved': self.autonomous.approved,
            'decisions': len(self.autonomous.log),
            'balance': self.binance.balance
        })
        print(f"\n[5] 💓 Watchdog: {health['health']} ({health['responsiveness']:.0f}%)")
        
        return {'cycle': self.cycle, 'results': results, 'opps': opps}
    
    def _exec_live(self, results: List[Dict]):
        for r in sorted(results, key=lambda x: x['combined'], reverse=True)[:2]:
            sym, price, d = r['symbol'], r['price'], r['decision']
            
            if d['action'] == 'BUY' and d['auto']:
                qty = self._calc_qty(sym, price, 0.2)
                if qty > 0:
                    self.binance.place_order(sym, 'BUY', qty)
                    
            elif d['action'] == 'SELL' and d['auto']:
                # Check if we own this asset
                base = sym.replace('USDT', '')
                owned = self.binance.balance.get(base, 0)
                if owned > 0:
                    # Sell 30% of what we own
                    qty = owned * 0.3
                    # Round appropriately
                    if 'BTC' in sym: qty = round(qty, 5)
                    elif 'ETH' in sym: qty = round(qty, 4)
                    else: qty = round(qty, 2)
                    if qty > 0:
                        self.binance.place_order(sym, 'SELL', qty)
    
    def _exec_sim(self, results: List[Dict]):
        for r in sorted(results, key=lambda x: x['combined'], reverse=True)[:2]:
            sym, price, d = r['symbol'], r['price'], r['decision']
            if d['action'] == 'BUY' and d['auto'] and sym not in self.executor.positions:
                self.executor.buy(sym, (self.executor.capital*0.2)/price, price)
                print(f"    ✅ 仿真买入: {sym}")
            elif d['action'] == 'SELL' and d['auto'] and sym in self.executor.positions:
                self.executor.sell(sym, price)
                print(f"    ✅ 仿真卖出: {sym}")
    
    def _calc_qty(self, symbol: str, price: float, pct: float) -> float:
        try:
            # Use cached balance first
            usdt = self.binance.balance.get('USDT', 0)
            if usdt <= 0:
                acc = self.binance.get_account()
                usdt = sum(safe_float(b['free']) for b in acc.get('balances',[]) if b['asset'] == 'USDT')
            
            if usdt <= 0 or price <= 0:
                return 0
            
            qty = (usdt * pct) / price
            
            # Minimum order sizes for common symbols
            min_orders = {
                'BTC': 0.00001,
                'ETH': 0.0001,
                'USDT': 1.0
            }
            
            # Round based on symbol
            for sym, min_qty in min_orders.items():
                if sym in symbol:
                    qty = max(qty, min_qty)
                    break
            
            if 'BTC' in symbol: return round(qty, 5)
            if 'ETH' in symbol: return round(qty, 4)
            return round(qty, 2)
        except Exception as e:
            print(f"   [ERROR] _calc_qty failed: {e}")
            return 0
    
    def run(self, cycles=100, interval=60):
        print(f"\n🚀 Q@C v{self.VERSION} 运行中...")
        for i in range(cycles):
            try:
                self.run_cycle()
                if i < cycles-1: time.sleep(interval)
            except KeyboardInterrupt:
                print("\n⚠️ 中断")
                break
            except Exception as e:
                print(f"\n❌ {e}")
                time.sleep(10)
        print(f"\n{'='*70}\n🏁 完成\n{'='*70}")

def main():
    QuantMasterQCV11(10000).run(cycles=3, interval=15)

if __name__ == "__main__":
    main()
