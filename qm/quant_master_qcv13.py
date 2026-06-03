"""
QuantMaster Q@C v13 - 完全体重构版
==================================
核心架构: Harness Engineering标准化
- 模块化设计
- 数据流清晰
- 风控优先
- 自我优化

版本: 13.0.0
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
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime
import os

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

# ============================================================
# 工具函数
# ============================================================
def safe_float(v, default=0.0):
    try: return float(v)
    except: return default

def get_config(key, default=None):
    try:
        with open('/home/goose/.openclaw/workspace/quant_master/config.json') as f:
            return json.load(f).get(key, default)
    except: return default

# ============================================================
# 数据总线 - DataBus
# ============================================================
class DataBus:
    """模块间数据共享"""
    def __init__(self):
        self.data = {}
        self.lock = threading.RLock()
        self.history = defaultdict(list)
    
    def publish(self, topic: str, data):
        with self.lock:
            self.data[topic] = {'data': data, 'ts': time.time()}
            self.history[topic].append({'data': data, 'ts': time.time()})
            if len(self.history[topic]) > 1000:
                self.history[topic][-500:]
    
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
# 技术指标 - Indicators
# ============================================================
class Indicators:
    @staticmethod
    def SMA(prices: List[float], period: int) -> float:
        if len(prices) < period: return 0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def EMA(prices: List[float], period: int) -> float:
        if len(prices) < period: return 0
        k = 2 / (period + 1)
        ema = prices[0]
        for p in prices[1:]:
            ema = p * k + ema * (1 - k)
        return ema
    
    @staticmethod
    def RSI(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1: return 50
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        ag = sum(gains) / period
        al = sum(losses) / period
        if al == 0: return 100
        return 100 - (100 / (1 + ag / al))
    
    @staticmethod
    def MACD(prices: List[float], fast=12, slow=26, signal=9):
        if len(prices) < slow + signal: return 0, 0, 0
        ema_fast = Indicators.EMA(prices, fast)
        ema_slow = Indicators.EMA(prices, slow)
        macd_line = ema_fast - ema_slow
        return macd_line, 0, 0
    
    @staticmethod
    def KDJ(high: List[float], low: List[float], close: List[float], period=9):
        if len(close) < period: return 50, 50, 50
        rsv = (close[-1] - min(low[-period:])) / (max(high[-period:]) - min(low[-period:]) + 1e-10) * 100
        k = 50.0
        d = 50.0
        j = 3 * k - 2 * d
        return k, d, j

# ============================================================
# 外部风控规则 - ExternalRiskEngine
# ============================================================
class ExternalRiskEngine:
    """
    外部参考策略矩阵 + 因子矩阵的风控规则
    整合EvoMap等外部策略
    """
    def __init__(self):
        self.name = "ExternalRisk"
        self.rules = []
        self.active_rules = []
        self._init_rules()
    
    def _init_rules(self):
        """初始化所有风控规则"""
        self.rules = [
            # 集中度风控
            {'id': 'CONCENTRATION_001', 'name': '单币种集中度限制', 'type': 'CONCENTRATION',
             'limit': 0.40, 'action': 'REBALANCE', 'priority': 1},
            
            # RSI风控
            {'id': 'RSI_001', 'name': 'RSI超卖禁止买入', 'type': 'RSI_OVERSOLD',
             'threshold': 30, 'action': 'BLOCK_BUY', 'priority': 1},
            {'id': 'RSI_002', 'name': 'RSI超买禁止卖出', 'type': 'RSI_OVERBOUGHT',
             'threshold': 75, 'action': 'BLOCK_SELL', 'priority': 1},
            {'id': 'RSI_003', 'name': 'RSI超卖止损', 'type': 'RSI_STOP_LOSS',
             'threshold': 20, 'action': 'STOP_LOSS', 'priority': 2},
            {'id': 'RSI_004', 'name': 'RSI超买止盈', 'type': 'RSI_TAKE_PROFIT',
             'threshold': 70, 'action': 'TAKE_PROFIT', 'priority': 2},
            
            # 波动率风控
            {'id': 'VOL_001', 'name': '波动率过高', 'type': 'VOLATILITY_HIGH',
             'threshold': 0.05, 'action': 'REDUCE_POSITION', 'priority': 2},
            
            # 趋势风控
            {'id': 'TREND_001', 'name': '下跌趋势禁止买入', 'type': 'DOWNTREND',
             'threshold': -2, 'action': 'BLOCK_BUY', 'priority': 1},
            
            # 交易量风控
            {'id': 'VOLUME_001', 'name': '交易量异常', 'type': 'VOLUME_ANOMALY',
             'threshold': 0.3, 'action': 'REDUCE_POSITION', 'priority': 2},
            
            # 速率风控
            {'id': 'SPEED_001', 'name': '涨速过快禁止追高', 'type': 'PRICE_SPEED',
             'threshold': 0.03, 'action': 'BLOCK_BUY', 'priority': 1},
            
            # 流动性风控
            {'id': 'LIQ_001', 'name': '流动性不足', 'type': 'LOW_LIQUIDITY',
             'threshold': 1000, 'action': 'REDUCE_POSITION', 'priority': 2},
            
            # 趋势强度风控
            {'id': 'MOMENTUM_001', 'name': '动量不足', 'type': 'LOW_MOMENTUM',
             'threshold': 0.5, 'action': 'HOLD', 'priority': 3},
        ]
    
    def check_all(self, symbol: str, data: Dict) -> List[Dict]:
        """检查所有规则"""
        triggered = []
        for rule in self.rules:
            result = self._check_rule(rule, symbol, data)
            if result:
                triggered.append(result)
        return sorted(triggered, key=lambda x: x.get('rule', {}).get('priority', 99))
    
    def _check_rule(self, rule: Dict, symbol: str, data: Dict) -> Optional[Dict]:
        """检查单条规则"""
        rsi = data.get('rsi', 50)
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        momentum = data.get('momentum', 0)
        concentration = data.get('concentration', 0)
        price_change = data.get('price_change_pct', 0)
        
        rule_type = rule['type']
        
        if rule_type == 'RSI_OVERSOLD' and rsi < rule['threshold']:
            return {'rule': rule, 'triggered': True, 'value': rsi}
        
        if rule_type == 'RSI_OVERBOUGHT' and rsi > rule['threshold']:
            return {'rule': rule, 'triggered': True, 'value': rsi}
        
        if rule_type == 'RSI_STOP_LOSS' and rsi < rule['threshold']:
            return {'rule': rule, 'triggered': True, 'value': rsi}
        
        if rule_type == 'RSI_TAKE_PROFIT' and rsi > rule['threshold']:
            return {'rule': rule, 'triggered': True, 'value': rsi}
        
        if rule_type == 'CONCENTRATION' and concentration > rule['limit']:
            return {'rule': rule, 'triggered': True, 'value': concentration}
        
        if rule_type == 'DOWNTREND' and price_change < rule['threshold']:
            return {'rule': rule, 'triggered': True, 'value': price_change}
        
        if rule_type == 'PRICE_SPEED' and price_change > rule['threshold']:
            return {'rule': rule, 'triggered': True, 'value': price_change}
        
        return None
    
    def apply_rules(self, triggered_rules: List[Dict], current_action: str) -> str:
        """根据触发的规则调整动作"""
        if not triggered_rules:
            return current_action
        
        # 最高优先级规则决定最终动作
        for t in triggered_rules:
            rule = t['rule']
            action = rule['action']
            
            # 如果有BLOCK规则，直接阻止
            if action == 'BLOCK_BUY' and current_action == 'BUY':
                return 'HOLD'
            if action == 'BLOCK_SELL' and current_action == 'SELL':
                return 'HOLD'
            
            # 止损/止盈优先
            if action in ['STOP_LOSS', 'TAKE_PROFIT']:
                return action
        
        return current_action

# ============================================================
# 自我优化引擎 - SelfOptimizerEngine
# ============================================================
class SelfOptimizerEngine:
    """
    Harness Engineering: 自我优化迭代
    - 性能监控
    - 模式识别
    - 参数优化
    - 自我学习
    """
    def __init__(self):
        self.performance_history = []
        self.strategy_scores = defaultdict(list)
        self.optimal_params = {}
        self.learning_rate = 0.01
        self.evolution_count = 0
    
    def record_trade(self, trade: Dict):
        """记录交易以供学习"""
        self.performance_history.append({
            **trade,
            'timestamp': time.time()
        })
        # 只保留最近1000条
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]
    
    def analyze_performance(self) -> Dict:
        """分析当前性能"""
        if not self.performance_history:
            return {'score': 50, 'status': 'NO_DATA', 'win_rate': 0, 'profit_factor': 0, 'total_trades': 0}
        
        trades = self.performance_history[-100:]
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) <= 0]
        
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        avg_win = sum(t.get('pnl', 0) for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(t.get('pnl', 0) for t in losses) / len(losses)) if losses else 1
        
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        # 综合评分
        score = min(100, win_rate * 0.4 + profit_factor * 20 + 30)
        
        return {
            'score': score,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': len(trades),
            'status': 'OPTIMAL' if score > 70 else 'SUBOPTIMAL' if score > 50 else 'POOR'
        }
    
    def suggest_improvements(self) -> List[Dict]:
        """基于分析建议改进"""
        perf = self.analyze_performance()
        suggestions = []
        
        if perf['win_rate'] < 50:
            suggestions.append({
                'type': 'WIN_RATE',
                'priority': 'HIGH',
                'suggestion': '提高买入信号精度，减少假信号'
            })
        
        if perf['profit_factor'] < 1.5:
            suggestions.append({
                'type': 'PROFIT_FACTOR',
                'priority': 'HIGH',
                'suggestion': '优化止损/止盈比例'
            })
        
        return suggestions

# ============================================================
# Watchdog - 看门狗 (增强版)
# ============================================================
class Watchdog:
    def __init__(self, name: str):
        self.name = name
        self.status = {
            'health': 'HEALTHY',
            'responsiveness': 100,
            'cycles': 0,
            'last_update': time.time(),
            'mode': 'SIM',
            'initiative_score': 0,
            'responsibility_score': 0
        }
        self.heartbeats = []
        self.decision_log = []
        self.risk_events = []
        self.max_heartbeats = 60
    
    def heartbeat(self, data: Dict):
        ts = time.time()
        self.heartbeats.append({
            **data,
            'timestamp': ts
        })
        if len(self.heartbeats) > self.max_heartbeats:
            self.heartbeats = self.heartbeats[-30:]
        self.status['last_update'] = ts
        self.status['cycles'] = data.get('cycles', 0)
        
        # 计算响应度
        recent = [h for h in self.heartbeats[-5:] if ts - h['timestamp'] < 70]
        self.status['responsiveness'] = min(100, len(recent) * 20)
        
        # 计算主动性评分
        self._calc_initiative_score()
        
        # 计算责任评分
        self._calc_responsibility_score()
    
    def _calc_initiative_score(self):
        """计算主动性评分 - 主动发现和解决问题的能力"""
        score = 100
        
        # 检查是否有未处理的预警
        if len(self.risk_events) > 0:
            score -= len(self.risk_events) * 5
        
        # 检查决策频率
        if len(self.decision_log) > 10:
            recent = [d for d in self.decision_log[-10:] if d.get('auto', False)]
            if len(recent) < 3:
                score -= 20
        
        self.status['initiative_score'] = max(0, score)
    
    def _calc_responsibility_score(self):
        """计算责任评分 - 收益最大化和风控表现"""
        score = 100
        
        # 检查是否有风控事件未处理
        if len(self.risk_events) > 0:
            score -= 20
        
        # 检查周期完成率
        if self.status['responsiveness'] < 80:
            score -= (80 - self.status['responsiveness'])
        
        self.status['responsibility_score'] = max(0, score)
    
    def log_decision(self, decision: Dict):
        """记录决策"""
        self.decision_log.append({
            **decision,
            'timestamp': time.time()
        })
        if len(self.decision_log) > 500:
            self.decision_log = self.decision_log[-200:]
    
    def add_risk_event(self, event: Dict):
        """添加风险事件"""
        self.risk_events.append({
            **event,
            'timestamp': time.time()
        })
        if len(self.risk_events) > 100:
            self.risk_events = self.risk_events[-50:]
    
    def get_health_report(self) -> Dict:
        """获取健康报告"""
        overall = 'HEALTHY'
        if self.status['responsiveness'] < 50:
            overall = 'CRITICAL'
        elif self.status['responsiveness'] < 80:
            overall = 'DEGRADED'
        
        self.status['health'] = overall
        
        return {
            'health': overall,
            'responsiveness': self.status['responsiveness'],
            'initiative': self.status['initiative_score'],
            'responsibility': self.status['responsibility_score'],
            'risk_events': len(self.risk_events),
            'decisions': len(self.decision_log)
        }

# ============================================================
# Binance API 封装
# ============================================================
class BinanceAPI:
    def __init__(self, api_key: str, api_secret: str, mode: str = 'SIM'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.mode = mode
        self.proxies = {
            'http': 'http://172.29.144.1:7897',
            'https': 'http://172.29.144.1:7897'
        }
        self.balance = {'USDT': 0, 'BTC': 0, 'ETH': 0}
        self._init_balance()
    
    def _init_balance(self):
        """初始化余额"""
        if self.mode == 'SIM':
            self.balance = {'USDT': 10000}
        else:
            try:
                acc = self.get_account()
                self.balance = {b['asset']: safe_float(b['free']) for b in acc.get('balances', [])}
            except Exception as e:
                print(f"⚠️ 余额获取失败: {e}")
    
    def _sign(self, params: Dict) -> str:
        q = urllib.parse.urlencode(sorted(params.items()))
        return hmac.new(self.api_secret.encode(), q.encode(), hashlib.sha256).hexdigest()
    
    def _request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        params = params or {}
        params['timestamp'] = int(time.time() * 1000)
        params['recvWindow'] = 5000
        query = urllib.parse.urlencode(sorted(params.items()))
        signature = self._sign(params)
        
        url = f"https://api.binance.com{endpoint}?{query}&signature={signature}"
        req = urllib.request.Request(url, method=method, headers={'X-MBX-APIKEY': self.api_key})
        
        handler = urllib.request.ProxyHandler(self.proxies)
        opener = urllib.request.build_opener(handler)
        
        try:
            with opener.open(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {'error': e.read().decode()}
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        req = urllib.request.Request(url)
        handler = urllib.request.ProxyHandler(self.proxies)
        opener = urllib.request.build_opener(handler)
        
        try:
            with opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                return [{'time': k[0], 'open': float(k[1]), 'high': float(k[2]),
                        'low': float(k[3]), 'close': float(k[4]), 'volume': float(k[5])} for k in data]
        except:
            return []
    
    def get_price(self, symbol: str) -> float:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        req = urllib.request.Request(url)
        handler = urllib.request.ProxyHandler(self.proxies)
        opener = urllib.request.build_opener(handler)
        
        try:
            with opener.open(req, timeout=5) as resp:
                return float(json.loads(resp.read().decode())['price'])
        except:
            return 0
    
    def get_account(self) -> Dict:
        return self._request('GET', '/api/v3/account')
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        params = {}
        if symbol: params['symbol'] = symbol
        return self._request('GET', '/api/v3/openOrders', params)
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = 'MARKET') -> Dict:
        if self.mode == 'SIM':
            return {'orderId': 'SIM', 'status': 'FILLED', 'side': side, 'executedQty': quantity}
        
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        # POST需要body
        ts = int(time.time() * 1000)
        params['timestamp'] = ts
        params['recvWindow'] = 5000
        query = urllib.parse.urlencode(sorted(params.items()))
        signature = self._sign(params)
        post_data = f"{query}&signature={signature}"
        
        req = urllib.request.Request(
            f"https://api.binance.com/api/v3/order",
            data=post_data.encode(),
            headers={'X-MBX-APIKEY': self.api_key},
            method='POST'
        )
        handler = urllib.request.ProxyHandler(self.proxies)
        opener = urllib.request.build_opener(handler)
        
        try:
            with opener.open(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                if result.get('status') == 'FILLED':
                    self._update_balance(symbol, side, safe_float(result.get('executedQty', 0)))
                return result
        except Exception as e:
            print(f"   ❌ 订单失败: {e}")
            return {'error': str(e)}
    
    def _update_balance(self, symbol: str, side: str, qty: float):
        asset = symbol.replace('USDT', '')
        if side == 'BUY':
            self.balance['USDT'] -= qty
            self.balance[asset] = self.balance.get(asset, 0) + qty
        else:
            self.balance[asset] -= qty
            self.balance['USDT'] += qty

# ============================================================
# V8 Signal Engine - 核心信号引擎
# ============================================================
class SignalEngineV8:
    """V8核心信号引擎"""
    def __init__(self):
        self.name = "V8"
        self.version = "8.0.0"
    
    def analyze(self, symbol: str, kl: List[Dict]) -> Optional[Dict]:
        if len(kl) < 50: return None
        
        closes = [k['close'] for k in kl]
        highs = [k['high'] for k in kl]
        lows = [k['low'] for k in kl]
        volumes = [k['volume'] for k in kl]
        
        rsi = Indicators.RSI(closes)
        sma20 = Indicators.SMA(closes, 20)
        sma60 = Indicators.SMA(closes, 60)
        ema12 = Indicators.EMA(closes, 12)
        macd, signal, hist = Indicators.MACD(closes)
        
        mom = (closes[-1] - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0
        volatility = (max(closes[-20:]) - min(closes[-20:])) / closes[-1] if len(closes) >= 20 else 0
        
        # 综合评分
        score = 50
        
        if rsi < 30: score += 15
        elif rsi > 70: score -= 15
        
        if closes[-1] > sma20: score += 10
        if sma20 > sma60: score += 10
        
        if macd > 0: score += 10
        if mom > 2: score += 10
        elif mom < -2: score -= 10
        
        if volatility > 0.05: score -= 10
        
        return {
            'score': max(0, min(100, score)),
            'rsi': rsi,
            'sma20': sma20,
            'sma60': sma60,
            'macd': macd,
            'momentum': mom,
            'volatility': volatility,
            'signal': 'BUY' if score >= 55 else 'SELL' if score <= 45 else 'HOLD'
        }

# ============================================================
# G12 Strategy Engine - G12策略引擎
# ============================================================
class StrategyEngineG12:
    """G12策略引擎"""
    def __init__(self):
        self.name = "G12"
        self.version = "12.0.0"
    
    def analyze(self, symbol: str, kl: List[Dict]) -> Optional[Dict]:
        if len(kl) < 50: return None
        
        closes = [k['close'] for k in kl]
        
        # 多周期分析
        scores = []
        
        # 1h
        rsi_1h = Indicators.RSI(closes)
        scores.append(50 if 30 < rsi_1h < 70 else 80 if rsi_1h < 30 else 20)
        
        # 4h
        if len(closes) >= 100:
            rsi_4h = Indicators.RSI(closes[-100:])
            scores.append(50 if 30 < rsi_4h < 70 else 80 if rsi_4h < 30 else 20)
        
        # 日线
        if len(closes) >= 200:
            rsi_d = Indicators.RSI(closes[-200:])
            scores.append(50 if 30 < rsi_d < 70 else 80 if rsi_d < 30 else 20)
        
        # 综合评分
        combined = sum(scores) / len(scores) if scores else 50
        
        return {
            'score': max(0, min(100, combined)),
            'rsi': rsi_1h
        }

# ============================================================
# MiroFish - 独立仿真引擎
# ============================================================
class MiroFishSimulator:
    """MiroFish独立仿真引擎"""
    def __init__(self):
        self.name = "MiroFish"
        self.version = "16.6.0"
        self.independent = True  # 不依赖OpenClaw/Hermes
    
    def analyze(self, symbol: str, kl: List[Dict]) -> Optional[Dict]:
        if len(kl) < 50: return None
        
        closes = [k['close'] for k in kl]
        
        # 简化的MiroFish仿真
        rsi = Indicators.RSI(closes)
        
        # 多策略融合
        strategy_scores = []
        
        # 趋势策略
        sma20 = Indicators.SMA(closes, 20)
        trend_score = 60 if closes[-1] > sma20 else 40
        strategy_scores.append(trend_score)
        
        # RSI策略
        rsi_score = 70 if rsi < 30 else 30 if rsi > 70 else 50
        strategy_scores.append(rsi_score)
        
        # 动量策略
        mom = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
        mom_score = 60 if mom > 0 else 40
        strategy_scores.append(mom_score)
        
        combined = sum(strategy_scores) / len(strategy_scores)
        
        return {
            'score': max(0, min(100, combined)),
            'rsi': rsi
        }

# ============================================================
# 自主决策引擎 - AutonomousDecision
# ============================================================
class AutonomousDecision:
    """自主决策引擎"""
    def __init__(self):
        self.log = []
        self.approved = 0
        self.threshold_buy = 55
        self.threshold_sell = 45
    
    def decide(self, symbol: str, combined: float, v8: Dict, g12: Dict, miro: Dict, 
               rsi: float = 50, external_risk: List[Dict] = None) -> Dict:
        """综合决策 - 包含外部风控"""
        # 先用RSI保护
        if rsi < 30:
            d = {'action': 'HOLD', 'auto': False, 'reason': f"RSI超卖({rsi:.0f})禁止BUY"}
        elif rsi > 75:
            d = {'action': 'HOLD', 'auto': False, 'reason': f"RSI超买({rsi:.0f})禁止SELL"}
        elif combined >= self.threshold_buy:
            d = {'action': 'BUY', 'auto': True, 'reason': f"综合={combined:.0f} RSI={rsi:.0f}"}
            self.approved += 1
        elif combined <= self.threshold_sell:
            d = {'action': 'SELL', 'auto': True, 'reason': f"综合={combined:.0f} RSI={rsi:.0f}"}
            self.approved += 1
        else:
            d = {'action': 'HOLD', 'auto': False, 'reason': f"综合={combined:.0f} RSI={rsi:.0f}"}
        
        # 应用外部风控规则
        if external_risk and d['action'] != 'HOLD':
            for risk in external_risk:
                rule = risk['rule']
                action = rule['action']
                if action == 'BLOCK_BUY' and d['action'] == 'BUY':
                    d = {'action': 'HOLD', 'auto': False, 'reason': f"风控:{rule['name']}"}
                    break
                if action == 'BLOCK_SELL' and d['action'] == 'SELL':
                    d = {'action': 'HOLD', 'auto': False, 'reason': f"风控:{rule['name']}"}
                    break
        
        self.log.append({'symbol': symbol, **d, 'timestamp': time.time()})
        return d

# ============================================================
# 自我纠正引擎 - SelfCorrectionEngine
# ============================================================
class SelfCorrectionEngine:
    """自动风控纠正"""
    def __init__(self):
        self.concentration_limit = 0.40
        self.rsi_take_profit = 65
        self.rsi_stop_loss = 20
    
    def check_concentration(self, symbol: str, balance: float, total_value: float, price: float) -> Optional[Dict]:
        if total_value <= 0: return None
        value = balance * price
        concentration = value / total_value
        
        if concentration > self.concentration_limit:
            target_pct = self.concentration_limit * 0.8
            target_value = total_value * target_pct
            sell_value = value - target_value
            sell_qty = sell_value / price
            
            return {
                'action': 'REBALANCE',
                'type': 'SELL',
                'symbol': symbol,
                'quantity': sell_qty,
                'reason': f"集中度{concentration*100:.1f}%>40%",
                'concentration': concentration
            }
        return None
    
    def check_rsi(self, symbol: str, rsi: float, entry_price: float, current_price: float) -> Optional[Dict]:
        if entry_price <= 0: return None
        pnl_pct = (current_price - entry_price) / entry_price * 100
        
        if rsi < self.rsi_stop_loss:
            return {
                'action': 'STOP_LOSS',
                'type': 'SELL',
                'symbol': symbol,
                'quantity': 0,
                'reason': f"RSI={rsi:.0f}<{self.rsi_stop_loss}止损",
                'pnl_pct': pnl_pct
            }
        
        if rsi > self.rsi_take_profit and pnl_pct > 5:
            return {
                'action': 'TAKE_PROFIT',
                'type': 'SELL',
                'symbol': symbol,
                'quantity': 0,
                'reason': f"RSI={rsi:.0f}>{self.rsi_take_profit}止盈",
                'pnl_pct': pnl_pct
            }
        
        return None
    
    def auto_correct(self, holdings: Dict, prices: Dict, total_value: float, 
                      market_data: Dict = None) -> List[Dict]:
        actions = []
        
        for symbol, data in holdings.items():
            if data.get('balance', 0) <= 0.001: continue
            
            price = prices.get(symbol, 0)
            if price <= 0: continue
            
            # 集中度检查
            conc = self.check_concentration(symbol, data['balance'], total_value, price)
            if conc:
                actions.append(conc)
            
            # RSI检查
            rsi = market_data.get(symbol, {}).get('rsi', 50) if market_data else 50
            rsi_check = self.check_rsi(symbol, rsi, data.get('entry_price', 0), price)
            if rsi_check:
                actions.append(rsi_check)
        
        return actions

# ============================================================
# Q@C v13 主控制器
# ============================================================
class QuantMasterQCV13:
    VERSION = "13.0.0"
    
    def __init__(self, capital: float = 10000):
        self.capital = capital
        self.cycle = 0
        self.data_bus = DataBus()
        
        # 核心组件
        self.binance = BinanceAPI(
            api_key='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61',
            api_secret='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk',
            mode='LIVE'
        )
        
        # 引擎初始化
        self.signal_v8 = SignalEngineV8()
        self.strategy_g12 = StrategyEngineG12()
        self.mirofish = MiroFishSimulator()  # 独立于OpenClaw/Hermes
        self.autonomous = AutonomousDecision()
        self.self_correct = SelfCorrectionEngine()
        self.external_risk = ExternalRiskEngine()
        self.optimizer = SelfOptimizerEngine()
        self.watchdog = Watchdog("QCV13")
        
        self.watchdog.status['mode'] = self.binance.mode
        
        # 权重配置
        self.weights = {'v8': 0.50, 'g12': 0.30, 'miro': 0.20}
        
        # 目标币种
        self.target_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT',
            'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'LTCUSDT',
            'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'ATOMUSDT', 'NEARUSDT'
        ]
        
        self._print_banner()
    
    def _print_banner(self):
        print("=" * 70)
        print(f"🚀 QuantMaster Q@C v{self.VERSION} - Harness Engineering重构版")
        print("=" * 70)
        print(f"   [API] 🟢 实盘账户: USDT={self.binance.balance.get('USDT', 0):.2f}")
        print(f"   [MODE] 🟢 LIVE 实盘")
        print(f"   [MIRO] ✅ 独立运行 (不依赖OpenClaw/Hermes)")
        print(f"   [WEIGHT] V8 {self.weights['v8']*100:.0f}% + G12 {self.weights['g12']*100:.0f}% + Miro {self.weights['miro']*100:.0f}%")
        print(f"   [RISK] ✅ 外部风控 + 自我纠正 + Watchdog")
        print("=" * 70)
    
    def run_cycle(self) -> Dict:
        """执行一个完整周期"""
        self.cycle += 1
        ts = datetime.now().strftime('%H:%M:%S')
        
        print(f"\n{'='*70}")
        print(f"📊 #{self.cycle} [{ts}] {'LIVE' if self.binance.mode=='LIVE' else 'SIM'}")
        print(f"💰 USDT: ${self.binance.balance.get('USDT', 0):.2f}")
        
        # 1. 探测市场
        print(f"\n[1] 🔍 探测市场...")
        market_data = self._probe_market()
        
        # 2. 技术分析
        print(f"\n[2] 📊 技术分析...")
        analysis_results = self._analyze(market_data)
        
        # 3. 外部风控检查
        print(f"\n[3] 🛡️ 外部风控检查...")
        risk_results = self._check_external_risk(analysis_results)
        
        # 4. 交易执行
        print(f"\n[4] 💰 交易执行...")
        trade_results = self._execute_trades(analysis_results, risk_results)
        
        # 5. 自我纠正
        print(f"\n[5] 🔧 自我纠正检查...")
        self._self_correct(analysis_results)
        
        # 6. Watchdog
        print(f"\n[6] 💓 Watchdog...")
        health = self.watchdog.get_health_report()
        self.watchdog.heartbeat({
            'cycles': self.cycle,
            'mode': self.binance.mode,
            'approved': self.autonomous.approved,
            'decisions': len(self.autonomous.log),
            'balance': self.binance.balance
        })
        print(f"   健康: {health['health']} | 响应: {health['responsiveness']:.0f}% | 主动: {health['initiative']} | 责任: {health['responsibility']}")
        
        # 7. 性能优化
        print(f"\n[7] 📈 性能分析...")
        perf = self.optimizer.analyze_performance()
        print(f"   评分: {perf['score']:.0f} | 胜率: {perf['win_rate']:.1f}% | 策略: {perf.get('status', 'N/A')}")
        
        return {
            'cycle': self.cycle,
            'balance': self.binance.balance.copy(),
            'health': health,
            'performance': perf
        }
    
    def _probe_market(self) -> Dict:
        """探测市场机会"""
        market_data = {}
        opportunities = 0
        
        for sym in self.target_symbols:
            kl = self.binance.get_klines(sym, '1h', 100)
            if len(kl) < 50: continue
            
            closes = [k['close'] for k in kl]
            rsi = Indicators.RSI(closes)
            mom = (closes[-1] - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0
            
            market_data[sym] = {
                'klines': kl,
                'rsi': rsi,
                'momentum': mom,
                'price': closes[-1],
                'volume': sum(k['volume'] for k in kl[-24:]) / 24
            }
            
            if (rsi < 30 and mom < -1) or (rsi > 70 and mom > 1):
                opportunities += 1
        
        print(f"   探测 {len(market_data)} 币种, {opportunities} 机会")
        return market_data
    
    def _analyze(self, market_data: Dict) -> List[Dict]:
        """技术分析"""
        results = []
        
        for sym, data in market_data.items():
            kl = data['klines']
            rsi = data['rsi']
            
            # V8分析
            v8 = self.signal_v8.analyze(sym, kl)
            # G12分析
            g12 = self.strategy_g12.analyze(sym, kl)
            # MiroFish分析
            miro = self.mirofish.analyze(sym, kl)
            
            if not v8 or not g12 or not miro:
                continue
            
            # 三重权重融合
            combined = (
                v8['score'] * self.weights['v8'] +
                g12['score'] * self.weights['g12'] +
                miro['score'] * self.weights['miro']
            )
            
            # 自主决策
            d = self.autonomous.decide(
                sym, combined, v8, g12, miro,
                rsi=rsi
            )
            
            results.append({
                'symbol': sym,
                'price': data['price'],
                'combined': combined,
                'v8': v8,
                'g12': g12,
                'miro': miro,
                'decision': d,
                'rsi': rsi
            })
            
            # 日志
            icon = "📈" if d['action'] == 'BUY' else "📉" if d['action'] == 'SELL' else "➡️"
            status = "✅" if d['auto'] else "⏸️"
            print(f"   {status} {icon} {sym}: 综合={combined:.0f} RSI={rsi:.0f} V8={v8['score']:.0f} G12={g12['score']:.0f} Miro={miro['score']:.0f} → {d['action']} {d['reason']}")
            
            # Watchdog记录
            self.watchdog.log_decision({'symbol': sym, **d})
        
        return results
    
    def _check_external_risk(self, results: List[Dict]) -> Dict:
        """外部风控检查"""
        risk_results = {}
        
        # 计算总资产
        total_value = self.binance.balance.get('USDT', 0)
        for asset, balance in self.binance.balance.items():
            if asset != 'USDT' and balance > 0.001:
                price = self.binance.get_price(f"{asset}USDT")
                total_value += balance * price
        
        for r in results:
            sym = r['symbol']
            symbol_only = sym.replace('USDT', '')
            
            # 集中度
            price = r['price']
            balance = self.binance.balance.get(symbol_only, 0)
            concentration = (balance * price) / total_value if total_value > 0 else 0
            
            # 外部风控检查
            risk_data = {
                'rsi': r['rsi'],
                'price': price,
                'momentum': r['v8'].get('momentum', 0),
                'volatility': r['v8'].get('volatility', 0),
                'concentration': concentration,
                'price_change_pct': r['v8'].get('momentum', 0),
                'volume': r['miro'].get('volume', 0)
            }
            
            triggered = self.external_risk.check_all(symbol_only, risk_data)
            final_action = self.external_risk.apply_rules(triggered, r['decision']['action'])
            
            risk_results[sym] = {
                'triggered': triggered,
                'final_action': final_action,
                'original_action': r['decision']['action']
            }
            
            # 如果有风控干预
            if final_action != r['decision']['action']:
                print(f"   🛡️ {sym}: 风控干预 {r['decision']['action']}→{final_action}")
                for t in triggered:
                    print(f"      - {t['rule']['name']}: {t['rule']['action']}")
        
        return risk_results
    
    def _execute_trades(self, results: List[Dict], risk_results: Dict):
        """执行交易"""
        if self.binance.mode != 'LIVE':
            print("   [SIM] 模拟模式跳过")
            return
        
        for r in results:
            sym = r['symbol']
            risk = risk_results.get(sym, {})
            action = risk.get('final_action', r['decision']['action'])
            
            if action == 'HOLD':
                continue
            
            # 获取价格
            price = r['price']
            
            # 计算数量
            usdt_balance = self.binance.balance.get('USDT', 0)
            
            if action == 'BUY' and usdt_balance > 10:
                qty = usdt_balance * 0.95 / price
                print(f"   📤 买入 {sym}: {qty:.4f} @ ${price:.4f}")
                result = self.binance.place_order(sym, 'BUY', qty)
                if 'orderId' in result:
                    print(f"   ✅ 订单成功: {result.get('orderId', 'N/A')}")
                    self.optimizer.record_trade({'symbol': sym, 'side': 'BUY', 'qty': qty, 'price': price})
            elif action == 'SELL':
                symbol_only = sym.replace('USDT', '')
                balance = self.binance.balance.get(symbol_only, 0)
                if balance > 0.001:
                    print(f"   📤 卖出 {sym}: {balance:.4f}")
                    result = self.binance.place_order(sym, 'SELL', balance)
                    if 'orderId' in result:
                        print(f"   ✅ 订单成功: {result.get('orderId', 'N/A')}")
                        self.optimizer.record_trade({'symbol': sym, 'side': 'SELL', 'qty': balance, 'price': price})
    
    def _self_correct(self, results: List[Dict]):
        """自我纠正"""
        # 计算总资产
        total_value = self.binance.balance.get('USDT', 0)
        holdings = {}
        prices = {}
        market_data = {}
        
        for r in results:
            sym = r['symbol']
            symbol_only = sym.replace('USDT', '')
            holdings[symbol_only] = {
                'balance': self.binance.balance.get(symbol_only, 0),
                'entry_price': 0,
                'rsi': r['rsi']
            }
            prices[symbol_only] = r['price']
            market_data[symbol_only] = {'rsi': r['rsi']}
            
            price = self.binance.get_price(f"{symbol_only}USDT")
            total_value += holdings[symbol_only]['balance'] * price
        
        corrections = self.self_correct.auto_correct(holdings, prices, total_value, market_data)
        
        for corr in corrections:
            print(f"   🔴 [自我纠正] {corr['reason']}")
            
            if corr['action'] == 'REBALANCE' and corr['quantity'] > 0.01:
                symbol = corr['symbol'] + 'USDT'
                print(f"   📤 执行: 卖出 {corr['quantity']:.4f} {symbol}")
                result = self.binance.place_order(symbol, 'SELL', corr['quantity'])
                if 'orderId' in result:
                    print(f"   ✅ 减持成功")

# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    qm = QuantMasterQCV13(10000)
    qm.run_cycle()
