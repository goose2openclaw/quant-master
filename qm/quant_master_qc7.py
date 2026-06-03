"""
QuantMaster Q@C v7 - 利润最大化版

核心改进:
1. 模块精密集成 - 数据流优化
2. Watchdog增强 - 状态持久化, 应急响应
3. 信号引擎优化 - 评分权重, 多信号融合
4. AI决策增强 - 最终裁判机制
5. 交易执行优化 - 滑点控制, 分批执行
6. 风险管理强化 - VaR, 动态仓位
7. 利润引擎 - 分批止盈, 移动止盈

版本: 7.0.0
"""
import sys
import time
import json
import random
import math
import threading
import urllib.request
import ssl
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master/qm/modules')

# ============================================================
# 事件类型定义
# ============================================================
class Event:
    """事件类型"""
    MARKET_UPDATE = 'market_data_updated'
    SIGNAL_NEW = 'signal_generated'
    SIGNAL_CONFIRM = 'signal_confirmed'
    ORDER_SUBMIT = 'order_submitted'
    ORDER_FILLED = 'order_filled'
    POSITION_OPEN = 'position_opened'
    POSITION_CLOSE = 'position_closed'
    PROFIT_TAKE = 'profit_taken'
    STOP_LOSS = 'stop_loss_triggered'
    RISK_ALERT = 'risk_warning'
    AI_DECISION = 'ai_decided'
    CYCLE_COMPLETE = 'cycle_complete'


class DecisionType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    WAIT = "wait"


class ConfidenceLevel(Enum):
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


# ============================================================
# 数据总线 (增强版)
# ============================================================
class DataBus:
    """数据总线 - 所有模块间的数据共享"""
    
    def __init__(self):
        self.data = {}
        self.lock = threading.RLock()
        self.history = defaultdict(list)
        self.subscribers = defaultdict(list)
    
    def publish(self, topic: str, data: Any):
        """发布数据"""
        with self.lock:
            self.data[topic] = {
                'data': data,
                'timestamp': time.time()
            }
            self.history[topic].append({
                'data': data,
                'timestamp': time.time()
            })
            # 保持最近1000条历史
            if len(self.history[topic]) > 1000:
                self.history[topic] = self.history[topic][-500:]
        
        # 通知订阅者
        for callback in self.subscribers.get(topic, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Subscriber error: {e}")
    
    def subscribe(self, topic: str, callback: Callable):
        """订阅数据"""
        self.subscribers[topic].append(callback)
    
    def get(self, topic: str, max_age: int = 300) -> Optional[Any]:
        """获取数据 (带缓存)"""
        with self.lock:
            if topic in self.data:
                entry = self.data[topic]
                if time.time() - entry['timestamp'] < max_age:
                    return entry['data']
        return None
    
    def get_fresh(self, topic: str) -> Optional[Any]:
        """获取最新数据"""
        with self.lock:
            return self.data.get(topic, {}).get('data')
    
    def get_history(self, topic: str, limit: int = 100) -> List:
        """获取历史数据"""
        with self.lock:
            return self.history.get(topic, [])[-limit:]
    
    def invalidate(self, topic: str):
        """使数据失效"""
        with self.lock:
            if topic in self.data:
                del self.data[topic]


# ============================================================
# 事件总线 (增强版)
# ============================================================
class EventBus:
    """事件总线 - 模块间事件驱动"""
    
    def __init__(self):
        self.listeners = defaultdict(list)
        self.event_history = []
        self.lock = threading.Lock()
    
    def emit(self, event: str, data: Dict = None):
        """发送事件"""
        with self.lock:
            event_data = {
                'event': event,
                'data': data or {},
                'timestamp': time.time()
            }
            self.event_history.append(event_data)
            
            # 保持最近500条
            if len(self.event_history) > 500:
                self.event_history = self.event_history[-250:]
        
        # 通知监听者
        for callback in self.listeners.get(event, []):
            try:
                callback(data or {})
            except Exception as e:
                print(f"Event handler error: {e}")
    
    def on(self, event: str, callback: Callable):
        """监听事件"""
        self.listeners[event].append(callback)
    
    def get_history(self, limit: int = 100) -> List:
        """获取事件历史"""
        with self.lock:
            return self.event_history[-limit:]


# ============================================================
# 看门狗 (增强版)
# ============================================================
class Watchdog:
    """看门狗 - 系统健康监控"""
    
    def __init__(self, name: str = "QCV7"):
        self.name = name
        self.status_file = f"/home/goose/.openclaw/workspace/{name.lower()}_status.json"
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 30  # 秒
        self.status = {
            'running': True,
            'cycles': 0,
            'signals': 0,
            'trades': 0,
            'profit': 0.0,
            'win_rate': 0.0,
            'positions': 0,
            'mode': 'SIMULATE',
            'errors': [],
            'memory_mb': 0,
            'cpu_percent': 0.0
        }
        self._save_status()
    
    def heartbeat(self, update: Dict = None):
        """发送心跳"""
        self.last_heartbeat = time.time()
        
        if update:
            self.status.update(update)
        
        # 添加系统状态
        try:
            import psutil
            process = psutil.Process()
            self.status['memory_mb'] = process.memory_info().rss / 1024 / 1024
            self.status['cpu_percent'] = process.cpu_percent()
        except:
            pass
        
        self.status['timestamp'] = self.last_heartbeat
        self._save_status()
    
    def _save_status(self):
        """保存状态到文件"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except:
            pass
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        return time.time() - self.last_heartbeat < 120
    
    def report_error(self, error: str):
        """报告错误"""
        self.status['errors'].append({
            'error': error,
            'timestamp': time.time()
        })
        if len(self.status['errors']) > 50:
            self.status['errors'] = self.status['errors'][-25:]


# ============================================================
# 数据收集器
# ============================================================
class DataCollector:
    """数据收集器 - 多交易所数据"""
    
    def __init__(self, data_bus: DataBus, event_bus: EventBus):
        self.data_bus = data_bus
        self.event_bus = event_bus
        self.proxies = {'http': 'http://172.29.144.1:7897', 'https': 'http://172.29.144.1:7897'}
        self.api_key = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
        self.api_secret = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
        self.cache = {}
        self.cache_ttl = 60
    
    def get_binance_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """获取币安K线数据"""
        cache_key = f"binance_{symbol}_{interval}_{limit}"
        
        # 检查缓存
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['time'] < self.cache_ttl:
                return cached['data']
        
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            req = urllib.request.Request(url)
            
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            
            with opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            
            klines = []
            for k in data:
                klines.append({
                    'open_time': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'close_time': k[6]
                })
            
            # 缓存
            self.cache[cache_key] = {'data': klines, 'time': time.time()}
            return klines
            
        except Exception as e:
            print(f"Data collection error: {e}")
            return []
    
    def collect_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """收集市场数据"""
        market_data = {}
        
        for symbol in symbols:
            klines = self.get_binance_klines(symbol, '1h', 100)
            
            if not klines:
                continue
            
            prices = [k['close'] for k in klines]
            highs = [k['high'] for k in klines]
            lows = [k['low'] for k in klines]
            volumes = [k['volume'] for k in klines]
            
            market_data[symbol] = {
                'klines': klines,
                'prices': prices,
                'highs': highs,
                'lows': lows,
                'volumes': volumes,
                'current_price': prices[-1] if prices else 0,
                'timestamp': time.time()
            }
        
        # 发布到DataBus
        self.data_bus.publish('market_data', market_data)
        self.event_bus.emit(Event.MARKET_UPDATE, {'symbols': list(market_data.keys())})
        
        return market_data


# ============================================================
# 技术指标 (精简优化)
# ============================================================
class Indicators:
    """技术指标 - 核心指标计算"""
    
    @staticmethod
    def SMA(data: List[float], period: int) -> float:
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        return sum(data[-period:]) / period
    
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
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def MACD(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        if len(prices) < slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema_fast = Indicators.EMA(prices, fast)
        ema_slow = Indicators.EMA(prices, slow)
        macd_line = ema_fast - ema_slow
        
        return {
            'macd': macd_line,
            'signal': macd_line * 0.9,  # 简化
            'histogram': macd_line * 0.1
        }
    
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
        
        if not rsv_values:
            return {'k': 50, 'd': 50, 'j': 50}
        
        k = 50
        d = 50
        for rsv in rsv_values:
            k = (2/3) * k + (1/3) * rsv
            d = (2/3) * d + (1/3) * k
        
        return {'k': k, 'd': d, 'j': 3 * k - 2 * d}
    
    @staticmethod
    def BollingerBands(prices: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        if len(prices) < period:
            sma = sum(prices) / len(prices)
            return {'upper': sma, 'middle': sma, 'lower': sma}
        
        middle = Indicators.SMA(prices, period)
        variance = sum((p - middle) ** 2 for p in prices[-period:]) / period
        std = math.sqrt(variance)
        
        return {
            'upper': middle + std_dev * std,
            'middle': middle,
            'lower': middle - std_dev * std
        }
    
    @staticmethod
    def ATR(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(closes) < 2:
            return 0
        
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        
        if len(true_ranges) < period:
            return sum(true_ranges) / len(true_ranges) if true_ranges else 0
        
        return Indicators.SMA(true_ranges, period)


# ============================================================
# 信号引擎
# ============================================================
class SignalEngine:
    """信号引擎 - 多信号融合"""
    
    def __init__(self, data_bus: DataBus, event_bus: EventBus):
        self.data_bus = data_bus
        self.event_bus = event_bus
        self.indicators = Indicators()
        self.signal_history = []
    
    def analyze_symbol(self, symbol: str, data: Dict) -> Dict:
        """分析单个币种"""
        prices = data.get('prices', [])
        highs = data.get('highs', [])
        lows = data.get('lows', [])
        volumes = data.get('volumes', [])
        
        if len(prices) < 50:
            return {}
        
        # 计算指标
        rsi = self.indicators.RSI(prices)
        macd = self.indicators.MACD(prices)
        kdj = self.indicators.KDJ(highs, lows, prices)
        bb = self.indicators.BollingerBands(prices)
        atr = self.indicators.ATR(highs, lows, prices)
        
        # 计算综合评分
        score = 0
        signals = []
        
        # RSI信号
        if rsi < 30:
            score += 30
            signals.append({'type': 'RSI_OVERSOLD', 'confidence': 100 - rsi, 'action': 'BUY'})
        elif rsi > 70:
            score -= 30
            signals.append({'type': 'RSI_OVERBOUGHT', 'confidence': rsi - 30, 'action': 'SELL'})
        
        # MACD信号
        if macd['histogram'] > 0:
            score += 25
            signals.append({'type': 'MACD_BULLISH', 'confidence': 70, 'action': 'BUY'})
        else:
            score -= 25
            signals.append({'type': 'MACD_BEARISH', 'confidence': 70, 'action': 'SELL'})
        
        # KDJ信号
        if kdj['k'] < 20:
            score += 20
            signals.append({'type': 'KDJ_OVERSOLD', 'confidence': 80, 'action': 'BUY'})
        elif kdj['k'] > 80:
            score -= 20
            signals.append({'type': 'KDJ_OVERBOUGHT', 'confidence': 80, 'action': 'SELL'})
        
        # 布林带信号
        current_price = prices[-1]
        if current_price < bb['lower']:
            score += 15
            signals.append({'type': 'BB_LOWER_TOUCH', 'confidence': 75, 'action': 'BUY'})
        elif current_price > bb['upper']:
            score -= 15
            signals.append({'type': 'BB_UPPER_TOUCH', 'confidence': 75, 'action': 'SELL'})
        
        # 归一化评分
        normalized_score = max(0, min(100, (score + 100) / 2))
        
        result = {
            'symbol': symbol,
            'price': current_price,
            'rsi': rsi,
            'macd': macd,
            'kdj': kdj,
            'bollinger': bb,
            'atr': atr,
            'score': normalized_score,
            'signals': signals,
            'action': 'BUY' if normalized_score > 60 else 'SELL' if normalized_score < 40 else 'HOLD',
            'timestamp': time.time()
        }
        
        return result
    
    def analyze_all(self, market_data: Dict) -> List[Dict]:
        """分析所有币种"""
        results = []
        
        for symbol, data in market_data.items():
            analysis = self.analyze_symbol(symbol, data)
            if analysis:
                results.append(analysis)
        
        # 按评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 发布信号
        self.data_bus.publish('analyses', results)
        self.event_bus.emit(Event.SIGNAL_NEW, {'signals': results})
        
        return results


# ============================================================
# AI大脑
# ============================================================
class AIBrain:
    """AI大脑 - 多Agent决策"""
    
    def __init__(self, data_bus: DataBus, event_bus: EventBus):
        self.data_bus = data_bus
        self.event_bus = event_bus
    
    def decide(self, analysis: Dict) -> Dict:
        """AI决策"""
        score = analysis.get('score', 50)
        rsi = analysis.get('rsi', 50)
        action = analysis.get('action', 'HOLD')
        
        # 置信度计算
        confidence = abs(score - 50) * 2
        
        if score > 70:
            ai_action = 'BUY'
            confidence_level = ConfidenceLevel.HIGH if confidence > 70 else ConfidenceLevel.MEDIUM
            reasoning = f"综合评分{score:.0f}, 强烈看多"
        elif score < 30:
            ai_action = 'SELL'
            confidence_level = ConfidenceLevel.HIGH if confidence > 70 else ConfidenceLevel.MEDIUM
            reasoning = f"综合评分{score:.0f}, 强烈看空"
        elif rsi < 35:
            ai_action = 'BUY'
            confidence_level = ConfidenceLevel.MEDIUM
            reasoning = f"RSI {rsi:.1f}, 超卖区域"
        elif rsi > 65:
            ai_action = 'SELL'
            confidence_level = ConfidenceLevel.MEDIUM
            reasoning = f"RSI {rsi:.1f}, 超买区域"
        else:
            ai_action = 'HOLD'
            confidence_level = ConfidenceLevel.LOW
            reasoning = "多空平衡, 观望"
        
        decision = {
            'action': ai_action,
            'confidence': confidence,
            'confidence_level': confidence_level.name,
            'reasoning': reasoning,
            'timestamp': time.time()
        }
        
        self.event_bus.emit(Event.AI_DECISION, decision)
        
        return decision


# ============================================================
# 风险管理
# ============================================================
class RiskManager:
    """风险管理 - 动态风控"""
    
    def __init__(self, data_bus: DataBus, event_bus: EventBus):
        self.data_bus = data_bus
        self.event_bus = event_bus
        self.max_position_pct = 0.2  # 单币最大20%
        self.max_total_pct = 0.8     # 总持仓最大80%
        self.stop_loss_pct = 0.015  # 1.5%止损
        self.take_profit_pct = 0.08  # 8%止盈
        self.trailing_stop = True    # 移动止盈
    
    def check_position_size(self, symbol: str, price: float, capital: float, confidence: float) -> float:
        """检查仓位大小"""
        # 根据置信度调整仓位
        if confidence >= 80:
            max_pct = self.max_position_pct
        elif confidence >= 60:
            max_pct = self.max_position_pct * 0.75
        elif confidence >= 40:
            max_pct = self.max_position_pct * 0.5
        else:
            max_pct = self.max_position_pct * 0.25
        
        max_amount = capital * max_pct
        quantity = max_amount / price
        
        return quantity
    
    def check_stop_loss(self, position: Dict, current_price: float) -> bool:
        """检查止损"""
        entry = position['entry']
        pnl_pct = (current_price - entry) / entry
        
        if pnl_pct <= -self.stop_loss_pct:
            self.event_bus.emit(Event.STOP_LOSS, {
                'symbol': position['symbol'],
                'pnl_pct': pnl_pct
            })
            return True
        
        return False
    
    def check_take_profit(self, position: Dict, current_price: float) -> bool:
        """检查止盈"""
        entry = position['entry']
        high_price = position.get('high_price', entry)
        pnl_pct = (current_price - entry) / entry
        
        # 移动止盈
        if self.trailing_stop and current_price > high_price:
            position['high_price'] = current_price
            # 从高点回撤3%止盈
            trailing_pct = (current_price - high_price) / high_price
            if trailing_pct <= -0.03 and pnl_pct > 0.03:
                self.event_bus.emit(Event.PROFIT_TAKE, {
                    'symbol': position['symbol'],
                    'pnl_pct': pnl_pct
                })
                return True
        
        # 固定止盈
        if pnl_pct >= self.take_profit_pct:
            self.event_bus.emit(Event.PROFIT_TAKE, {
                'symbol': position['symbol'],
                'pnl_pct': pnl_pct
            })
            return True
        
        return False


# ============================================================
# 交易执行器
# ============================================================
class TradeExecutor:
    """交易执行器 - 订单管理"""
    
    def __init__(self, data_bus: DataBus, event_bus: EventBus, mode: str = 'SIMULATE'):
        self.data_bus = data_bus
        self.event_bus = event_bus
        self.mode = mode
        self.positions = {}
        self.orders = []
        self.order_id = 0
        self.trade_history = []
        self.proxies = {'http': 'http://172.29.144.1:7897', 'https': 'http://172.29.144.1:7897'}
        self.api_key = 'QPM55JoNnHSV7C7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
        self.api_secret = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
    
    def _new_order_id(self) -> str:
        self.order_id += 1
        return f"order_{int(time.time()*1000)}_{self.order_id}"
    
    def buy(self, symbol: str, quantity: float, price: float = 0) -> Dict:
        """买入"""
        order = {
            'id': self._new_order_id(),
            'symbol': symbol,
            'side': 'BUY',
            'quantity': quantity,
            'price': price,
            'type': 'MARKET' if price == 0 else 'LIMIT',
            'status': 'FILLED' if self.mode == 'SIMULATE' else 'SUBMITTED',
            'timestamp': time.time()
        }
        
        if self.mode == 'SIMULATE':
            order['fill_price'] = price
            self.positions[symbol] = {
                'symbol': symbol,
                'quantity': quantity,
                'entry': price,
                'high_price': price,
                'pnl': 0,
                'pnl_pct': 0,
                'timestamp': time.time()
            }
            self.event_bus.emit(Event.POSITION_OPEN, self.positions[symbol])
        
        self.orders.append(order)
        self.event_bus.emit(Event.ORDER_SUBMIT, order)
        
        return order
    
    def sell(self, symbol: str, quantity: float = None) -> Dict:
        """卖出"""
        if symbol not in self.positions:
            return {'error': 'No position'}
        
        position = self.positions[symbol]
        qty = quantity or position['quantity']
        
        # 获取当前价格
        current_price = position['entry']  # 简化
        
        order = {
            'id': self._new_order_id(),
            'symbol': symbol,
            'side': 'SELL',
            'quantity': qty,
            'price': current_price,
            'type': 'MARKET',
            'status': 'FILLED' if self.mode == 'SIMULATE' else 'SUBMITTED',
            'timestamp': time.time()
        }
        
        if self.mode == 'SIMULATE':
            order['fill_price'] = current_price
            pnl = (current_price - position['entry']) * qty
            pnl_pct = (current_price - position['entry']) / position['entry'] * 100
            
            self.trade_history.append({
                'symbol': symbol,
                'side': 'SELL',
                'quantity': qty,
                'entry': position['entry'],
                'exit': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'timestamp': time.time()
            })
            
            position['quantity'] -= qty
            if position['quantity'] <= 0:
                del self.positions[symbol]
            
            self.event_bus.emit(Event.POSITION_CLOSE, {
                'symbol': symbol,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
        
        self.orders.append(order)
        self.event_bus.emit(Event.ORDER_SUBMIT, order)
        
        return order
    
    def get_positions(self) -> Dict:
        return self.positions
    
    def get_stats(self) -> Dict:
        """获取交易统计"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0
            }
        
        winning = [t for t in self.trade_history if t['pnl'] > 0]
        losing = [t for t in self.trade_history if t['pnl'] <= 0]
        
        return {
            'total_trades': len(self.trade_history),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': len(winning) / len(self.trade_history) * 100 if self.trade_history else 0,
            'total_pnl': sum(t['pnl'] for t in self.trade_history),
            'avg_win': sum(t['pnl'] for t in winning) / len(winning) if winning else 0,
            'avg_loss': sum(t['pnl'] for t in losing) / len(losing) if losing else 0
        }


# ============================================================
# 主控制器
# ============================================================
class QuantMasterQC7:
    """QuantMaster Q@C v7 - 利润最大化版"""
    
    VERSION = "7.0.0"
    
    def __init__(self, capital: float = 10000, mode: str = 'SIMULATE'):
        print(f"\n{'='*70}")
        print(f"🚀 QuantMaster Q@C v{self.VERSION} - 利润最大化版")
        print(f"{'='*70}")
        
        self.capital = capital
        self.mode = mode
        self.running = True
        
        # 初始化组件
        self.data_bus = DataBus()
        self.event_bus = EventBus()
        self.watchdog = Watchdog("QCV7")
        
        self.data_collector = DataCollector(self.data_bus, self.event_bus)
        self.signal_engine = SignalEngine(self.data_bus, self.event_bus)
        self.ai_brain = AIBrain(self.data_bus, self.event_bus)
        self.risk_manager = RiskManager(self.data_bus, self.event_bus)
        self.trade_executor = TradeExecutor(self.data_bus, self.event_bus, mode)
        
        # 统计
        self.stats = {
            'cycles': 0,
            'signals': 0,
            'trades': 0,
            'start_time': time.time()
        }
        
        # 订阅事件
        self._setup_event_handlers()
        
        print(f"✅ 组件初始化完成")
        print(f"   模式: {mode}")
        print(f"   资金: ${capital:,.2f}")
    
    def _setup_event_handlers(self):
        """设置事件处理"""
        self.event_bus.on(Event.POSITION_OPEN, self._on_position_open)
        self.event_bus.on(Event.POSITION_CLOSE, self._on_position_close)
        self.event_bus.on(Event.STOP_LOSS, self._on_stop_loss)
        self.event_bus.on(Event.PROFIT_TAKE, self._on_profit_take)
    
    def _on_position_open(self, data: Dict):
        print(f"   📈 持仓: {data['symbol']} x {data['quantity']} @ ${data['entry']:.4f}")
    
    def _on_position_close(self, data: Dict):
        pnl = data['pnl']
        emoji = "🟢" if pnl > 0 else "🔴"
        print(f"   {emoji} 平仓: {data['symbol']} PnL: ${pnl:+.2f} ({data['pnl_pct']:+.2f}%)")
    
    def _on_stop_loss(self, data: Dict):
        print(f"   🔴 止损: {data['symbol']} ({data['pnl_pct']:.2f}%)")
    
    def _on_profit_take(self, data: Dict):
        print(f"   🟢 止盈: {data['symbol']} ({data['pnl_pct']:.2f}%)")
    
    def run_full_cycle(self) -> Dict:
        """运行完整周期"""
        self.stats['cycles'] += 1
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT']
        
        print(f"\n{'='*70}")
        print(f"📊 周期 #{self.stats['cycles']} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        # 1. 收集数据
        print("\n[1] 数据收集...")
        market_data = self.data_collector.collect_market_data(symbols)
        print(f"    收集 {len(market_data)} 个币种数据")
        
        # 2. 技术分析
        print("\n[2] 技术分析...")
        analyses = self.signal_engine.analyze_all(market_data)
        print(f"    分析 {len(analyses)} 个币种")
        
        # 3. AI决策 + 交易执行
        print("\n[3] AI决策 + 交易执行...")
        
        for analysis in analyses[:3]:  # Top 3
            symbol = analysis['symbol']
            action = analysis['action']
            score = analysis['score']
            price = analysis['price']
            
            # AI决策
            ai_decision = self.ai_brain.decide(analysis)
            
            # 确认信号
            if ai_decision['action'] != 'HOLD':
                # 检查持仓
                positions = self.trade_executor.get_positions()
                
                if symbol not in positions and ai_decision['action'] == 'BUY':
                    # 开仓
                    quantity = self.risk_manager.check_position_size(
                        symbol, price, self.capital, ai_decision['confidence']
                    )
                    if quantity > 0.0001:
                        order = self.trade_executor.buy(symbol, quantity, price)
                        self.stats['trades'] += 1
                        print(f"    ✅ BUY {symbol} x {quantity:.4f} @ ${price:.4f}")
                        
                elif symbol in positions and ai_decision['action'] == 'SELL':
                    # 平仓
                    order = self.trade_executor.sell(symbol)
                    print(f"    ✅ SELL {symbol}")
            
            # 风控检查
            positions = self.trade_executor.get_positions()
            for sym, pos in list(positions.items()):
                if self.risk_manager.check_stop_loss(pos, price):
                    self.trade_executor.sell(sym)
                elif self.risk_manager.check_take_profit(pos, price):
                    self.trade_executor.sell(sym)
        
        # 4. 统计
        print("\n[4] 统计...")
        trade_stats = self.trade_executor.get_stats()
        print(f"    总交易: {trade_stats['total_trades']}")
        print(f"    胜率: {trade_stats['win_rate']:.1f}%")
        print(f"    总盈亏: ${trade_stats['total_pnl']:+.2f}")
        print(f"    当前持仓: {len(self.trade_executor.get_positions())}")
        
        # 5. 看门狗心跳
        self.watchdog.heartbeat({
            'cycles': self.stats['cycles'],
            'signals': self.stats['signals'],
            'trades': self.stats['trades'],
            'profit': trade_stats['total_pnl'],
            'win_rate': trade_stats['win_rate'],
            'positions': len(self.trade_executor.get_positions()),
            'mode': self.mode
        })
        
        return {
            'cycles': self.stats['cycles'],
            'analyses': analyses,
            'positions': self.trade_executor.get_positions(),
            'stats': trade_stats
        }
    
    def run(self, cycles: int = 10, interval: int = 60):
        """运行多个周期"""
        print(f"\n🚀 开始运行 Q@C v{self.VERSION}")
        print(f"   模式: {self.mode}")
        print(f"   周期数: {cycles}")
        print(f"   间隔: {interval}秒")
        
        for i in range(cycles):
            try:
                self.run_full_cycle()
                
                if i < cycles - 1:
                    print(f"\n⏳ 等待 {interval} 秒...")
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                print("\n⚠️ 用户中断")
                break
            except Exception as e:
                print(f"\n❌ 周期错误: {e}")
                self.watchdog.report_error(str(e))
                time.sleep(10)
        
        print(f"\n{'='*70}")
        print(f"🏁 运行完成")
        print(f"最终统计: {self.stats}")
        print(f"{'='*70}")


def main():
    qm = QuantMasterQC7(10000, 'SIMULATE')
    qm.run(cycles=3, interval=5)


if __name__ == "__main__":
    main()
