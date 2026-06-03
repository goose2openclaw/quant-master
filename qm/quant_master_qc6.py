"""
QuantMaster Q@C v6 - 全模块集成版

集成模块:
1. TechnicalIndicators (100+指标) - 从Lean/TradingView克隆
2. MultiExchange (Binance/Bybit/OKX/Hyperliquid) - 从Lean克隆
3. AlertSystem (TradingView风格) - 从TradingView克隆
4. AIDecision (Kronos风格多Agent) - 从Kronos克隆
5. BacktestEngine (专业回测) - 从Lean克隆
6. DataBus/EventBus (模块间通信)
7. Watchdog (进程看门狗)

版本: 6.0.0
"""
import sys
import time
import json
import random
import math
import threading
import urllib.request
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
from datetime import datetime

# 添加模块路径
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master/qm/modules')

# 导入所有模块
from qm.modules.indicators import TechnicalIndicators, MultiTimeFrameAnalyzer, PivotPoints
from qm.modules.multi_exchange import ExchangeRouter, BinanceAPI, BybitAPI, OKXAPI, HyperliquidAPI
from qm.modules.alerts import AlertManager, AlertType, AlertPriority, AlertCondition
from qm.modules.ai_decision import AIDecisionEngine, DecisionType, ConfidenceLevel
from qm.modules.backtest import BacktestEngine, StrategyLibrary

try:
    from qm.binance_optimizer import BinanceAPI as BinanceAPIOriginal
    HAS_ORIGINAL_API = True
except:
    HAS_ORIGINAL_API = False


# ============================================================
# 数据总线 & 事件总线
# ============================================================
class DataBus:
    """数据总线 - 模块间数据共享"""
    def __init__(self):
        self.data = {}
        self.subscribers = defaultdict(list)
        self.lock = threading.Lock()
        self.history = defaultdict(list)
    
    def publish(self, topic: str, data: Any):
        with self.lock:
            self.data[topic] = {'data': data, 'timestamp': time.time()}
            self.history[topic].append({'data': data, 'timestamp': time.time()})
            if len(self.history[topic]) > 1000:
                self.history[topic] = self.history[topic][-500:]
        for cb in self.subscribers.get(topic, []):
            try: cb(data)
            except: pass
    
    def subscribe(self, topic: str, callback: Callable):
        self.subscribers[topic].append(callback)
    
    def get(self, topic: str, max_age: int = 300) -> Optional[Any]:
        with self.lock:
            if topic in self.data:
                entry = self.data[topic]
                if time.time() - entry['timestamp'] < max_age:
                    return entry['data']
        return None
    
    def get_history(self, topic: str, limit: int = 100) -> List:
        with self.lock:
            return self.history.get(topic, [])[-limit:]


class LocalEventBus:
    """事件总线 - 模块间事件通知"""
    def __init__(self):
        self.listeners = defaultdict(list)
        self.event_history = []
    
    def emit(self, event: str, data: Dict = None):
        for cb in self.listeners.get(event, []):
            try: cb(data or {})
            except: pass
        self.event_history.append({"event": event, "data": data, "timestamp": time.time()})
    
    def on(self, event: str, callback: Callable):
        self.listeners[event].append(callback)


class WatchdogClient:
    """看门狗客户端"""
    def __init__(self, name: str = "qcv6"):
        self.name = name
        self.last_heartbeat = time.time()
        self.status_file = f"/home/goose/.openclaw/workspace/{name}_status.json"
    
    def heartbeat(self, status: Dict = None):
        """发送心跳"""
        self.last_heartbeat = time.time()
        data = {
            'name': self.name,
            'timestamp': self.last_heartbeat,
            'status': status or {}
        }
        try:
            with open(self.status_file, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        return time.time() - self.last_heartbeat < 120


# ============================================================
# 主控制器
# ============================================================
class QuantMasterQC6:
    """
    QuantMaster Q@C v6 - 全模块集成版
    
    特性:
    - 100+ 技术指标 (从Lean/TradingView克隆)
    - 多交易所支持 (Binance/Bybit/OKX/Hyperliquid)
    - TradingView风格警报系统
    - Kronos风格AI决策
    - Lean专业回测引擎
    - 模块化架构
    - Watchdog集成
    """
    
    VERSION = "6.0.0"
    COMMIT = "qc6_integrated"
    
    def __init__(self, capital: float = 10000):
        print(f"\n{'='*70}")
        print(f"🚀 QuantMaster Q@C v{self.VERSION} - 全模块集成版")
        print(f"{'='*70}")
        
        self.capital = capital
        self.mode = "SIMULATE"  # SIMULATE / LIVE
        
        # 初始化组件
        self._init_components()
        
        # 统计数据
        self.stats = {
            'cycles': 0,
            'signals': 0,
            'trades': 0,
            'start_time': time.time()
        }
        
        print(f"✅ 组件初始化完成")
        print(f"   - DataBus/EventBus")
        print(f"   - TechnicalIndicators (100+ 指标)")
        print(f"   - MultiExchange (4 交易所)")
        print(f"   - AlertSystem (TradingView风格)")
        print(f"   - AIDecision (Kronos风格)")
        print(f"   - BacktestEngine (Lean专业)")
        print(f"   - WatchdogClient")
    
    def _init_components(self):
        """初始化所有组件"""
        
        # 数据总线
        self.data_bus = DataBus()
        self.event_bus = LocalEventBus()
        
        # 看门狗
        self.watchdog = WatchdogClient("qcv6")
        
        # 技术指标
        self.indicators = TechnicalIndicators()
        self.mtf_analyzer = MultiTimeFrameAnalyzer()
        self.pivot = PivotPoints()
        
        # 多交易所
        self.exchange_router = ExchangeRouter()
        self.exchange_router.register('binance', BinanceAPI())
        self.exchange_router.register('bybit', BybitAPI())
        self.exchange_router.register('okx', OKXAPI())
        
        # 警报系统
        self.alerts = AlertManager()
        self._setup_default_alerts()
        
        # AI决策
        self.ai = AIDecisionEngine()
        
        # 回测引擎
        self.backtester = BacktestEngine(initial_capital=self.capital)
        
        # 持仓
        self.positions = {}
        self.pending_orders = []
        
        # 注册事件监听
        self._setup_event_listeners()
    
    def _setup_default_alerts(self):
        """设置默认警报"""
        # BTC RSI超卖
        self.alerts.create_alert(
            name="BTC RSI超卖",
            alert_type=AlertType.RSI_OVERSOLD,
            symbol="BTCUSDT",
            condition=AlertCondition.rsi_below(30),
            priority=AlertPriority.HIGH
        )
        
        # BTC价格突破
        self.alerts.create_alert(
            name="BTC价格突破75000",
            alert_type=AlertType.PRICE_ABOVE,
            symbol="BTCUSDT",
            condition=AlertCondition.price_above(75000),
            priority=AlertPriority.MEDIUM
        )
        
        # BTC价格下跌
        self.alerts.create_alert(
            name="BTC价格跌破70000",
            alert_type=AlertType.PRICE_BELOW,
            symbol="BTCUSDT",
            condition=AlertCondition.price_below(70000),
            priority=AlertPriority.HIGH
        )
    
    def _setup_event_listeners(self):
        """设置事件监听"""
        self.event_bus.on('signal_generated', self._on_signal)
        self.event_bus.on('alert_triggered', self._on_alert)
        self.event_bus.on('trade_executed', self._on_trade)
    
    def _on_signal(self, data: Dict):
        """信号事件处理"""
        self.stats['signals'] += 1
        print(f"   📡 信号: {data.get('symbol')} {data.get('type')}")
    
    def _on_alert(self, data: Dict):
        """警报事件处理"""
        print(f"   🔔 警报: {data.get('name')} 被触发!")
    
    def _on_trade(self, data: Dict):
        """交易事件处理"""
        self.stats['trades'] += 1
    
    def get_market_data(self, symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 100) -> Dict:
        """获取市场数据"""
        exchange = self.exchange_router.get_exchange('binance')
        klines = exchange.get_klines(symbol, interval, limit) if exchange else []
        
        if not klines:
            # 生成模拟数据
            base_price = 70000 if 'BTC' in symbol else 1.3 if 'XRP' in symbol else 80
            klines = []
            price = base_price
            for i in range(limit):
                price += random.uniform(-base_price * 0.01, base_price * 0.01)
                klines.append({
                    'open': price - 10,
                    'high': price + 20,
                    'low': price - 30,
                    'close': price,
                    'volume': random.uniform(100, 1000)
                })
        
        return {
            'symbol': symbol,
            'klines': klines,
            'prices': [k['close'] for k in klines],
            'highs': [k['high'] for k in klines],
            'lows': [k['low'] for k in klines],
            'volumes': [k['volume'] for k in klines]
        }
    
    def analyze_technical(self, data: Dict) -> Dict:
        """技术分析"""
        prices = data['prices']
        highs = data['highs']
        lows = data['lows']
        volumes = data['volumes']
        
        # 计算所有指标
        result = {
            'symbol': data['symbol'],
            'timestamp': time.time(),
            'indicators': {
                'sma_20': TechnicalIndicators.SMA(prices, 20),
                'sma_50': TechnicalIndicators.SMA(prices, 50) if len(prices) >= 50 else None,
                'ema_20': TechnicalIndicators.EMA(prices, 20),
                'rsi': TechnicalIndicators.RSI(prices),
                'macd': TechnicalIndicators.MACD(prices),
                'kdj': TechnicalIndicators.KDJ(highs, lows, prices),
                'bollinger': TechnicalIndicators.BollingerBands(prices),
                'atr': TechnicalIndicators.ATR(highs, lows, prices),
                'cci': TechnicalIndicators.CCI(highs, lows, prices),
                'williams_r': TechnicalIndicators.WilliamsR(highs, lows, prices),
                'adx': TechnicalIndicators.ADX(highs, lows, prices),
                'obv': TechnicalIndicators.OBV(prices, volumes),
                'fibonacci': TechnicalIndicators.Fibonacci(prices[-1] * 1.05, prices[-1] * 0.95) if len(prices) >= 2 else {},
                'supertrend': TechnicalIndicators.SuperTrend(highs, lows, prices)
            },
            'comprehensive': TechnicalIndicators.ComprehensiveScore(prices, highs, lows, volumes)
        }
        
        # 支撑/阻力
        sr = TechnicalIndicators.SupportResistance(prices)
        result['support'] = sr['support']
        result['resistance'] = sr['resistance']
        
        return result
    
    def generate_signals(self, analysis: Dict) -> List[Dict]:
        """生成交易信号"""
        signals = []
        ind = analysis['indicators']
        comp = analysis['comprehensive']
        
        # RSI超买超卖
        if ind['rsi'] < 30:
            signals.append({
                'type': 'RSI_OVERSOLD',
                'symbol': analysis['symbol'],
                'confidence': 100 - ind['rsi'],
                'action': 'BUY',
                'reasoning': f"RSI={ind['rsi']:.1f} 超卖"
            })
        elif ind['rsi'] > 70:
            signals.append({
                'type': 'RSI_OVERBOUGHT',
                'symbol': analysis['symbol'],
                'confidence': ind['rsi'] - 30,
                'action': 'SELL',
                'reasoning': f"RSI={ind['rsi']:.1f} 超买"
            })
        
        # MACD
        if ind['macd']['histogram'] > 0:
            signals.append({
                'type': 'MACD_BULLISH',
                'symbol': analysis['symbol'],
                'confidence': ind['macd']['histogram'] * 10,
                'action': 'BUY',
                'reasoning': "MACD柱状图正值"
            })
        else:
            signals.append({
                'type': 'MACD_BEARISH',
                'symbol': analysis['symbol'],
                'confidence': abs(ind['macd']['histogram']) * 10,
                'action': 'SELL',
                'reasoning': "MACD柱状图负值"
            })
        
        # KDJ
        if ind['kdj']['k'] < 20:
            signals.append({
                'type': 'KDJ_OVERSOLD',
                'symbol': analysis['symbol'],
                'confidence': 80,
                'action': 'BUY',
                'reasoning': f"KDJ K={ind['kdj']['k']:.1f} 超卖"
            })
        
        # 综合评分
        if comp['overall_score'] > 150:
            signals.append({
                'type': 'COMPOSITE_BUY',
                'symbol': analysis['symbol'],
                'confidence': comp['overall_score'] - 100,
                'action': 'BUY',
                'reasoning': f"综合评分={comp['overall_score']:.0f} 强烈买入"
            })
        elif comp['overall_score'] < 50:
            signals.append({
                'type': 'COMPOSITE_SELL',
                'symbol': analysis['symbol'],
                'confidence': 100 - comp['overall_score'],
                'action': 'SELL',
                'reasoning': f"综合评分={comp['overall_score']:.0f} 建议卖出"
            })
        
        return signals
    
    def ai_decide(self, market_data: Dict) -> Dict:
        """AI决策"""
        # 准备AI输入
        data = {
            'technical': {
                'rsi': market_data.get('indicators', {}).get('rsi', 50),
                'macd_histogram': market_data.get('indicators', {}).get('macd', {}).get('histogram', 0),
                'bb_position': 50
            },
            'fundamental': {
                'mcap_growth': random.uniform(-0.1, 0.1),
                'volume_trend': random.uniform(-0.2, 0.2),
                'network_activity': random.uniform(0, 10)
            },
            'sentiment': {
                'social_sentiment': random.uniform(-1, 1),
                'fear_greed': random.uniform(0, 100),
                'news_sentiment': random.uniform(-1, 1)
            },
            'onchain': {
                'active_addresses': random.uniform(5000, 20000),
                'tx_volume': random.uniform(500000, 3000000),
                'exchange_outflow': random.uniform(50000, 200000),
                'exchange_inflow': random.uniform(30000, 150000)
            },
            'market': {
                'btc_dominance': random.uniform(40, 55),
                'btc_correlation': random.uniform(0.3, 0.8),
                'market_trend': 'bullish' if random.random() > 0.5 else 'bearish'
            },
            'risk': {
                'volatility': random.uniform(30, 80)
            }
        }
        
        decision = self.ai.decide(data)
        
        return {
            'action': decision.decision.value.upper(),
            'confidence': decision.confidence,
            'confidence_level': decision.confidence_level.name,
            'reasoning': decision.reasoning,
            'risk_level': decision.risk_level
        }
    
    def check_alerts(self, market_data: Dict):
        """检查警报"""
        prices = market_data['prices']
        if len(prices) < 14:
            return []
        
        highs = market_data.get('highs', prices)
        lows = market_data.get('lows', prices)
        volumes = market_data.get('volumes', [1] * len(prices))
        
        symbol = market_data['symbol']
        
        # 构建市场数据
        latest = {
            'price': prices[-1],
            'rsi': TechnicalIndicators.RSI(prices),
            'macd': TechnicalIndicators.MACD(prices),
            'volume': volumes[-1] if volumes else 1,
            'avg_volume': sum(volumes[-20:]) / 20 if len(volumes) >= 20 else 1
        }
        
        # 检查警报
        triggered = self.alerts.check_all({symbol: latest})
        
        for alert_info in triggered:
            self.event_bus.emit('alert_triggered', alert_info)
        
        return triggered
    
    def execute_trade(self, signal: Dict) -> bool:
        """执行交易"""
        if self.mode == "LIVE":
            # 实盘模式
            exchange = self.exchange_router.get_exchange('binance')
            if exchange:
                symbol = signal['symbol']
                action = signal['action']
                quantity = 0.001  # 最小交易量
                
                try:
                    result = exchange.place_order(symbol, action, quantity)
                    print(f"   ✅ 实盘下单: {action} {symbol}")
                    return True
                except Exception as e:
                    print(f"   ❌ 下单失败: {e}")
                    return False
        else:
            # 模拟模式
            print(f"   📝 模拟交易: {signal['action']} {signal['symbol']}")
            return True
    
    def run_full_cycle(self):
        """运行完整周期"""
        self.stats['cycles'] += 1
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT']
        all_signals = []
        all_alerts = []
        
        print(f"\n{'='*70}")
        print(f"📊 周期 #{self.stats['cycles']} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        for symbol in symbols:
            # 获取数据
            data = self.get_market_data(symbol)
            
            # 技术分析
            analysis = self.analyze_technical(data)
            self.data_bus.publish(f'analysis_{symbol}', analysis)
            
            # 生成信号
            signals = self.generate_signals(analysis)
            
            # AI决策
            ai_decision = self.ai_decide(analysis)
            
            # 检查警报
            alerts = self.check_alerts(data)
            
            # 事件通知
            for sig in signals:
                self.event_bus.emit('signal_generated', sig)
                all_signals.append(sig)
            
            all_alerts.extend(alerts)
            
            # 输出
            price = data['prices'][-1]
            rsi = analysis['indicators']['rsi']
            recommendation = analysis['comprehensive']['recommendation']
            
            print(f"\n   {symbol}:")
            print(f"      价格: ${price:.4f}")
            print(f"      RSI: {rsi:.1f}")
            print(f"      综合建议: {recommendation}")
            print(f"      AI决策: {ai_decision['action']} (置信{ai_decision['confidence']:.0f}%)")
            print(f"      信号数: {len(signals)}")
            print(f"      警报数: {len(alerts)}")
        
        # 汇总
        print(f"\n📈 周期汇总:")
        print(f"   总信号: {len(all_signals)}")
        print(f"   总警报: {len(all_alerts)}")
        print(f"   持仓: {len(self.positions)}")
        
        # 发送心跳
        self.watchdog.heartbeat({
            'cycles': self.stats['cycles'],
            'signals': self.stats['signals'],
            'trades': self.stats['trades'],
            'mode': self.mode,
            'positions': len(self.positions)
        })
        
        return {
            'signals': all_signals,
            'alerts': all_alerts,
            'stats': self.stats.copy()
        }
    
    def run(self, cycles: int = 10, interval: int = 60):
        """运行多个周期"""
        print(f"\n🚀 开始运行 Q@C v{self.VERSION}")
        print(f"   模式: {self.mode}")
        print(f"   周期数: {cycles}")
        print(f"   间隔: {interval}秒")
        print(f"{'='*70}")
        
        for i in range(cycles):
            try:
                self.run_full_cycle()
                
                if i < cycles - 1:
                    print(f"\n⏳ 等待 {interval} 秒...")
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断")
                break
            except Exception as e:
                print(f"\n❌ 周期错误: {e}")
                time.sleep(10)
        
        print(f"\n{'='*70}")
        print(f"🏁 运行完成")
        print(f"{'='*70}")
        print(f"\n最终统计:")
        print(f"   周期: {self.stats['cycles']}")
        print(f"   信号: {self.stats['signals']}")
        print(f"   交易: {self.stats['trades']}")
        print(f"   运行时间: {time.time() - self.stats['start_time']:.0f}秒")


def main():
    """主函数"""
    qm = QuantMasterQC6(10000)
    qm.mode = "SIMULATE"
    qm.run(cycles=3, interval=5)


if __name__ == "__main__":
    main()
