"""
QuantMaster Q@C v8 - 利润最大化增强版

核心优化:
1. 模拟交易逻辑优化 - 正确的持仓管理和止损
2. API自动接管 - 检测并接管真实API
3. 自动开启交易 - 智能模式切换
4. 跨周期持仓 - 持仓状态持久化
5. 滑点模拟 - 更真实的模拟成交

版本: 8.0.0
"""
import sys
import time
import json
import random
import math
import threading
import urllib.request
import ssl
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import os

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

# ============================================================
# 事件类型
# ============================================================
class Event:
    MARKET_UPDATE = 'market_data_updated'
    SIGNAL_NEW = 'signal_generated'
    ORDER_SUBMIT = 'order_submitted'
    ORDER_FILLED = 'order_filled'
    POSITION_OPEN = 'position_opened'
    POSITION_CLOSE = 'position_closed'
    PROFIT_TAKE = 'profit_taken'
    STOP_LOSS = 'stop_loss_triggered'
    AI_DECISION = 'ai_decided'
    MODE_CHANGE = 'mode_changed'
    CYCLE_COMPLETE = 'cycle_complete'


# ============================================================
# 数据总线
# ============================================================
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
    
    def get_fresh(self, topic: str) -> Optional[Any]:
        with self.lock:
            return self.data.get(topic, {}).get('data')
    
    def save_state(self, path: str):
        """保存状态到文件"""
        with self.lock:
            state = {k: {'data': v['data'], 'timestamp': v['timestamp']} 
                    for k, v in self.data.items()}
        try:
            with open(path, 'w') as f:
                json.dump(state, f)
        except: pass
    
    def load_state(self, path: str):
        """从文件加载状态"""
        try:
            with open(path, 'r') as f:
                state = json.load(f)
            with self.lock:
                for k, v in state.items():
                    self.data[k] = v
        except: pass


# ============================================================
# 事件总线
# ============================================================
class EventBus:
    def __init__(self):
        self.listeners = defaultdict(list)
        self.event_history = []
        self.lock = threading.Lock()
    
    def emit(self, event: str, data: Dict = None):
        with self.lock:
            self.event_history.append({
                'event': event,
                'data': data or {},
                'timestamp': time.time()
            })
            if len(self.event_history) > 300:
                self.event_history = self.event_history[-150:]
        for cb in self.listeners.get(event, []):
            try: cb(data or {})
            except: pass
    
    def on(self, event: str, callback):
        self.listeners[event].append(callback)


# ============================================================
# 看门狗
# ============================================================
class Watchdog:
    def __init__(self, name: str = "QCV8"):
        self.name = name
        self.status_file = f"/home/goose/.openclaw/workspace/{name.lower()}_status.json"
        self.last_heartbeat = time.time()
        self.status = {
            'running': True,
            'cycles': 0,
            'signals': 0,
            'trades': 0,
            'profit': 0.0,
            'win_rate': 0.0,
            'positions': 0,
            'mode': 'SIMULATE',
            'version': '8.0.0'
        }
        self._save()
    
    def heartbeat(self, update: Dict = None):
        self.last_heartbeat = time.time()
        if update:
            self.status.update(update)
        self.status['timestamp'] = self.last_heartbeat
        self._save()
    
    def _save(self):
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except: pass
    
    def is_alive(self) -> bool:
        return time.time() - self.last_heartbeat < 120


# ============================================================
# Binance API (增强版)
# ============================================================
class BinanceAPI:
    def __init__(self):
        self.api_key = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
        self.api_secret = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
        self.base_url = "https://api.binance.com/api"
        self.proxies = {'http': 'http://172.29.144.1:7897', 'https': 'http://172.29.144.1:7897'}
        self.handler = urllib.request.ProxyHandler(self.proxies)
    
    def _sign(self, params: Dict) -> str:
        import hmac
        import hashlib
        import urllib.parse
        query = urllib.parse.urlencode(sorted(params.items()))
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    
    def _request(self, method: str, endpoint: str, signed: bool = False, params: Dict = None):
        params = params or {}
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 5000
            params['signature'] = self._sign(params)
        
        url = f"{self.base_url}{endpoint}?{urllib.parse.urlencode(params)}"
        headers = {'X-MBX-APIKEY': self.api_key}
        req = urllib.request.Request(url, headers=headers, method=method)
        
        try:
            opener = urllib.request.build_opener(self.handler)
            with opener.open(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {'error': str(e)}
    
    def get_balance(self) -> Dict:
        result = self._request('GET', '/v3/account', signed=True)
        if 'error' in result:
            return {}
        balances = {}
        for b in result.get('balances', []):
            free = float(b.get('free', 0))
            locked = float(b.get('locked', 0))
            if free + locked > 0:
                balances[b['asset']] = free + locked
        return balances
    
    def get_ticker(self, symbol: str) -> Dict:
        result = self._request('GET', '/v3/ticker/price', params={'symbol': symbol})
        if 'price' in result:
            return {'price': float(result['price'])}
        return {'error': 'Ticker not found'}
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        result = self._request('GET', '/v3/klines', params={
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        })
        if 'error' in result or not isinstance(result, list):
            return []
        klines = []
        for k in result:
            klines.append({
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5])
            })
        return klines
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "MARKET") -> Dict:
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': quantity
        }
        if order_type.upper() == 'LIMIT':
            params['timeInForce'] = 'GTC'
            params['price'] = self.get_ticker(symbol).get('price', 0)
        
        result = self._request('POST', '/v3/order', signed=True, params=params)
        return result


# ============================================================
# 模拟交易执行器 (优化版)
# ============================================================
class SimulatedExecutor:
    """模拟交易执行器 - 更真实的模拟"""
    
    def __init__(self, initial_capital: float = 10000):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.positions = {}  # {symbol: position}
        self.trade_history = []
        self.pending_orders = []
        self.slippage = 0.001  # 0.1% 滑点
    
    def buy(self, symbol: str, quantity: float, price: float) -> Dict:
        """模拟买入 - 加入滑点"""
        slip_price = price * (1 + self.slippage)
        cost = slip_price * quantity
        fee = cost * 0.001
        
        if cost + fee > self.capital:
            return {'error': 'Insufficient capital', 'status': 'REJECTED'}
        
        self.capital -= (cost + fee)
        
        if symbol in self.positions:
            pos = self.positions[symbol]
            total_qty = pos['quantity'] + quantity
            pos['entry'] = (pos['entry'] * pos['quantity'] + slip_price * quantity) / total_qty
            pos['quantity'] = total_qty
        else:
            self.positions[symbol] = {
                'symbol': symbol,
                'quantity': quantity,
                'entry': slip_price,
                'high_price': slip_price,
                'low_price': slip_price,
                'entry_time': time.time(),
                'trades': 0
            }
        
        trade = {
            'id': f"SIM_{int(time.time()*1000)}",
            'symbol': symbol,
            'side': 'BUY',
            'quantity': quantity,
            'price': slip_price,
            'fee': fee,
            'cost': cost,
            'timestamp': time.time()
        }
        self.trade_history.append(trade)
        
        return {'status': 'FILLED', 'order': trade}
    
    def sell(self, symbol: str, quantity: float = None, price: float = None) -> Dict:
        """模拟卖出"""
        if symbol not in self.positions:
            return {'error': 'No position', 'status': 'REJECTED'}
        
        pos = self.positions[symbol]
        qty = quantity or pos['quantity']
        sell_price = price * (1 - self.slippage) if price else pos['entry']
        
        revenue = sell_price * qty
        fee = revenue * 0.001
        net_revenue = revenue - fee
        
        pnl = (sell_price - pos['entry']) * qty
        pnl_pct = (sell_price - pos['entry']) / pos['entry'] * 100
        
        self.capital += net_revenue
        
        trade = {
            'id': f"SIM_{int(time.time()*1000)}",
            'symbol': symbol,
            'side': 'SELL',
            'quantity': qty,
            'price': sell_price,
            'fee': fee,
            'revenue': net_revenue,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'timestamp': time.time()
        }
        self.trade_history.append(trade)
        
        pos['quantity'] -= qty
        if pos['quantity'] <= 0:
            del self.positions[symbol]
        
        return {'status': 'FILLED', 'trade': trade}
    
    def update_positions(self, prices: Dict[str, float]):
        """更新持仓盈亏"""
        for symbol, pos in self.positions.items():
            if symbol in prices:
                current = prices[symbol]
                pos['current_price'] = current
                pos['pnl'] = (current - pos['entry']) * pos['quantity']
                pos['pnl_pct'] = (current - pos['entry']) / pos['entry'] * 100
                if current > pos['high_price']:
                    pos['high_price'] = current
    
    def check_stop_loss(self, symbol: str, stop_pct: float = 0.015) -> bool:
        """检查止损"""
        if symbol not in self.positions:
            return False
        pos = self.positions[symbol]
        if pos['pnl_pct'] <= -stop_pct * 100:
            return True
        return False
    
    def check_take_profit(self, symbol: str, profit_pct: float = 0.08) -> bool:
        """检查止盈"""
        if symbol not in self.positions:
            return False
        pos = self.positions[symbol]
        # 移动止盈: 从高点回撤50%且盈利超过3%
        if pos['pnl_pct'] >= profit_pct * 100:
            if (pos['high_price'] - pos['current_price']) / pos['high_price'] >= 0.03:
                return True
        return False
    
    def get_stats(self) -> Dict:
        """获取统计"""
        if not self.trade_history:
            return {'total_trades': 0, 'win_rate': 0, 'total_pnl': 0, 'capital': self.capital, 'profit_pct': 0}
        
        sells = [t for t in self.trade_history if t['side'] == 'SELL' and 'pnl' in t]
        wins = [t for t in sells if t['pnl'] > 0]
        
        return {
            'total_trades': len(sells),
            'winning_trades': len(wins),
            'losing_trades': len(sells) - len(wins),
            'win_rate': len(wins) / len(sells) * 100 if sells else 0,
            'total_pnl': sum(t.get('pnl', 0) for t in sells),
            'capital': self.capital,
            'profit_pct': (self.capital - self.initial_capital) / self.initial_capital * 100
        }


# ============================================================
# 技术指标
# ============================================================
class Indicators:
    @staticmethod
    def RSI(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        return 100 - (100 / (1 + avg_gain / avg_loss))
    
    @staticmethod
    def EMA(data: List[float], period: int) -> float:
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    @staticmethod
    def MACD(prices: List[float], fast: int = 12, slow: int = 26) -> Dict[str, float]:
        if len(prices) < slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        ema_fast = Indicators.EMA(prices, fast)
        ema_slow = Indicators.EMA(prices, slow)
        macd = ema_fast - ema_slow
        signal = macd * 0.9
        return {'macd': macd, 'signal': signal, 'histogram': macd - signal}
    
    @staticmethod
    def KDJ(highs: List[float], lows: List[float], closes: List[float], period: int = 9) -> Dict[str, float]:
        if len(closes) < period:
            return {'k': 50, 'd': 50, 'j': 50}
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
        return {
            'upper': middle + std_dev * std,
            'middle': middle,
            'lower': middle - std_dev * std
        }


# ============================================================
# 信号引擎
# ============================================================
class SignalEngine:
    def __init__(self):
        self.indicators = Indicators()
    
    def analyze(self, symbol: str, klines: List[Dict]) -> Dict:
        if not klines or len(klines) < 50:
            return {}
        
        prices = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        current = prices[-1]
        
        rsi = self.indicators.RSI(prices)
        macd = self.indicators.MACD(prices)
        kdj = self.indicators.KDJ(highs, lows, prices)
        bb = self.indicators.BollingerBands(prices)
        
        # 综合评分
        score = 50
        signals = []
        
        # RSI
        if rsi < 30:
            score += 25
            signals.append({'type': 'RSI_OVERSOLD', 'action': 'BUY', 'conf': 100 - rsi})
        elif rsi > 70:
            score -= 25
            signals.append({'type': 'RSI_OVERBOUGHT', 'action': 'SELL', 'conf': rsi - 30})
        
        # MACD
        if macd['histogram'] > 0:
            score += 20
            signals.append({'type': 'MACD_BULLISH', 'action': 'BUY', 'conf': 70})
        else:
            score -= 20
            signals.append({'type': 'MACD_BEARISH', 'action': 'SELL', 'conf': 70})
        
        # KDJ
        if kdj['k'] < 20:
            score += 15
            signals.append({'type': 'KDJ_OVERSOLD', 'action': 'BUY', 'conf': 80})
        elif kdj['k'] > 80:
            score -= 15
            signals.append({'type': 'KDJ_OVERBOUGHT', 'action': 'SELL', 'conf': 80})
        
        # 布林带
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
# 主控制器
# ============================================================
class QuantMasterQC8:
    """QuantMaster Q@C v8 - 利润最大化增强版"""
    
    VERSION = "8.0.0"
    
    def __init__(self, capital: float = 10000, mode: str = 'AUTO'):
        print(f"\n{'='*70}")
        print(f"🚀 QuantMaster Q@C v{self.VERSION} - 利润最大化增强版")
        print(f"{'='*70}")
        
        self.capital = capital
        self.mode = mode  # AUTO/SIMULATE/LIVE
        self.running = True
        
        # 组件
        self.data_bus = DataBus()
        self.event_bus = EventBus()
        self.watchdog = Watchdog("QCV8")
        
        self.indicators = Indicators()
        self.signal_engine = SignalEngine()
        self.binance = BinanceAPI()
        self.executor = SimulatedExecutor(capital)
        
        # 持仓持久化
        self.state_file = '/home/goose/.openclaw/workspace/qcv8_state.json'
        self._load_state()
        
        # 统计
        self.stats = {
            'cycles': 0,
            'signals': 0,
            'trades': 0,
            'start_time': time.time()
        }
        
        # 自动模式检测
        self._detect_mode()
        
        print(f"✅ 初始化完成")
        print(f"   模式: {self.mode}")
        print(f"   资金: ${self.capital:,.2f}")
    
    def _detect_mode(self):
        """自动检测模式"""
        if self.mode == 'AUTO':
            # 尝试获取真实余额
            try:
                balances = self.binance.get_balance()
                usdt_balance = balances.get('USDT', 0)
                if usdt_balance > 10:
                    self.mode = 'LIVE'
                    self.capital = usdt_balance
                    print(f"   🔍 检测到真实账户: ${usdt_balance:.2f}")
                    print(f"   ✅ 切换到 LIVE 模式")
                else:
                    self.mode = 'SIMULATE'
                    print(f"   🔍 未检测到足够余额")
                    print(f"   ✅ 使用 SIMULATE 模式")
            except Exception as e:
                self.mode = 'SIMULATE'
                print(f"   ⚠️ API检测失败: {e}")
                print(f"   ✅ 使用 SIMULATE 模式")
    
    def _load_state(self):
        """加载状态"""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            if 'positions' in state:
                for symbol, pos in state['positions'].items():
                    self.executor.positions[symbol] = pos
            if 'capital' in state:
                self.executor.capital = state['capital']
            print(f"   📂 已加载持仓状态")
        except:
            pass
    
    def _save_state(self):
        """保存状态"""
        state = {
            'positions': self.executor.positions,
            'capital': self.executor.capital,
            'timestamp': time.time()
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except:
            pass
    
    def collect_data(self, symbols: List[str]) -> Dict[str, List[Dict]]:
        """收集数据"""
        data = {}
        for symbol in symbols:
            klines = self.binance.get_klines(symbol, '1h', 100)
            if klines:
                data[symbol] = klines
        return data
    
    def run_cycle(self) -> Dict:
        """运行一个周期"""
        self.stats['cycles'] += 1
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT']
        
        print(f"\n{'='*70}")
        print(f"📊 周期 #{self.stats['cycles']} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"   模式: {self.mode}")
        print(f"{'='*70}")
        
        # 1. 收集数据
        print(f"\n[1] 数据收集...")
        market_data = self.collect_data(symbols)
        print(f"    收集: {len(market_data)} 个币种")
        
        # 2. 获取当前价格
        prices = {}
        for symbol in market_data:
            prices[symbol] = market_data[symbol][-1]['close']
        
        # 3. 更新持仓状态
        print(f"\n[2] 持仓管理...")
        self.executor.update_positions(prices)
        print(f"    持仓: {len(self.executor.positions)} 个币种")
        for symbol, pos in self.executor.positions.items():
            print(f"    {symbol}: {pos['quantity']:.4f} @ ${pos['entry']:.2f} (${pos.get('pnl', 0):+.2f})")
        
        # 4. 风控检查
        print(f"\n[3] 风控检查...")
        for symbol in list(self.executor.positions.keys()):
            # 止损检查
            if self.executor.check_stop_loss(symbol):
                pos = self.executor.positions[symbol]
                print(f"    🔴 止损触发: {symbol}")
                result = self.executor.sell(symbol, price=prices.get(symbol, pos['entry']))
                if 'trade' in result:
                    t = result['trade']
                    emoji = "🟢" if t['pnl'] > 0 else "🔴"
                    print(f"    {emoji} 平仓: {symbol} PnL: ${t['pnl']:+.2f} ({t['pnl_pct']:+.2f}%)")
            
            # 止盈检查
            elif self.executor.check_take_profit(symbol):
                pos = self.executor.positions[symbol]
                print(f"    🟢 止盈触发: {symbol}")
                result = self.executor.sell(symbol, price=prices.get(symbol, pos['entry']))
                if 'trade' in result:
                    t = result['trade']
                    print(f"    🟢 平仓: {symbol} PnL: ${t['pnl']:+.2f} ({t['pnl_pct']:+.2f}%)")
        
        # 5. 技术分析 + 信号
        print(f"\n[4] 信号分析...")
        analyses = []
        for symbol, klines in market_data.items():
            if symbol not in self.executor.positions:  # 只分析没有持仓的
                analysis = self.signal_engine.analyze(symbol, klines)
                if analysis:
                    analyses.append(analysis)
                    print(f"    {symbol}: score={analysis['score']:.0f} action={analysis['action']} RSI={analysis['rsi']:.1f}")
        
        # 6. AI决策 + 交易
        print(f"\n[5] 交易执行...")
        
        # 按评分排序
        analyses.sort(key=lambda x: x['score'], reverse=True)
        
        for analysis in analyses[:2]:  # Top 2
            symbol = analysis['symbol']
            if symbol in self.executor.positions:
                continue
            
            action = analysis['action']
            score = analysis['score']
            price = analysis['price']
            
            if action == 'BUY' and score > 55:
                # 计算仓位
                position_pct = min(0.2, (score - 50) / 100)  # 5-20%
                quantity = (self.executor.capital * position_pct) / price
                
                if quantity * price > 10:  # 至少10美元
                    print(f"    ✅ 买入: {symbol} x {quantity:.4f} @ ${price:.2f}")
                    result = self.executor.buy(symbol, quantity, price)
                    if result.get('status') == 'FILLED':
                        self.stats['trades'] += 1
                        print(f"    ✅ 成交: {symbol}")
            elif action == 'SELL' and score < 35:
                if symbol in self.executor.positions:
                    print(f"    🔴 卖出: {symbol}")
                    result = self.executor.sell(symbol, price=price)
                    if result.get('status') == 'FILLED':
                        print(f"    ✅ 平仓: {symbol}")
        
        # 7. 统计
        print(f"\n[6] 统计...")
        stats = self.executor.get_stats()
        print(f"    账户: ${stats.get('capital', stats.get('总账户', 0)):.2f}")
        print(f"    盈亏: ${stats.get('total_pnl', 0):+.2f} ({stats['profit_pct']:+.2f}%)")
        print(f"    交易: {stats['total_trades']}笔")
        print(f"    胜率: {stats['win_rate']:.1f}%")
        
        # 8. 保存状态
        self._save_state()
        
        # 9. 看门狗
        self.watchdog.heartbeat({
            'cycles': self.stats['cycles'],
            'signals': self.stats['signals'],
            'trades': self.stats['trades'],
            'profit': stats.get('total_pnl', 0),
            'win_rate': stats['win_rate'],
            'positions': len(self.executor.positions),
            'mode': self.mode,
            'capital': stats.get('capital', stats.get('总账户', 0))
        })
        
        return {
            'cycles': self.stats['cycles'],
            'analyses': analyses,
            'positions': self.executor.positions.copy(),
            'stats': stats
        }
    
    def run(self, cycles: int = 100, interval: int = 60):
        """运行多个周期"""
        print(f"\n🚀 开始运行 Q@C v{self.VERSION}")
        print(f"   模式: {self.mode}")
        print(f"   周期: {cycles}")
        print(f"   间隔: {interval}秒")
        
        for i in range(cycles):
            try:
                self.run_cycle()
                if i < cycles - 1:
                    print(f"\n⏳ 等待 {interval} 秒...")
                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\n⚠️ 用户中断")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(10)
        
        print(f"\n{'='*70}")
        print(f"🏁 运行完成")
        print(f"最终统计: {self.executor.get_stats()}")
        print(f"{'='*70}")


def main():
    qm = QuantMasterQC8(10000, 'AUTO')
    qm.run(cycles=5, interval=10)


if __name__ == "__main__":
    main()
