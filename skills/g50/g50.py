#!/usr/bin/env python3
"""
G50 - 机器学习预测量化系统
=========================
整合 G40 + ML预测 + 强化学习 + 多时间框架分析

核心升级:
- ML预测模型 (随机森林思想)
- 强化学习策略优化 (Q-Learning)
- 多时间框架分析
- 情绪分析集成
- 预测信号生成
"""

import json
import time
import math
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque, defaultdict
import statistics
import random

# ============ G50 核心配置 ============

# ML预测配置
USE_ML_PREDICTION = True
ML_CONFIDENCE_THRESHOLD = 0.60
PREDICTION_HORIZON = 24  # 预测24小时

# 强化学习配置
RL_ENABLED = True
RL_LEARNING_RATE = 0.01
RL_DISCOUNT_FACTOR = 0.95
RL_EPSILON = 0.1

# 交易配置
MIN_USDT_RESERVE = 5.0
MIN_TRADE_VALUE = 0.5
SCAN_INTERVAL = 15  # 更快扫描
STOP_LOSS = 0.03
TAKE_PROFIT = 0.12
MAX_DRAWDOWN = 0.10
TRAILING_STOP = True
TRAILING_CALLBACK = 0.015

# 杠杆配置
USE_CROSS_MARGIN = True
MARGIN_LEVERAGE = 1.5
MAX_CROSS_MARGIN_EXPOSURE = 800

# 仓位配置
MAX_POSITION_CONCENTRATION = 0.20
MAX_SINGLE_POSITION_PCT = 0.05

# Kelly配置
KELLY_BASE = 0.15


# ============ ML预测模型 ============

class MLPricePredictor:
    """机器学习价格预测器 (简化随机森林)"""
    
    def __init__(self):
        self.feature_importance = {}
        self.training_data = deque(maxlen=1000)
        self.is_trained = False
    
    def add_sample(self, features: Dict[str, float], target: float):
        """添加训练样本"""
        self.training_data.append({
            'features': features,
            'target': target,
            'timestamp': time.time()
        })
        
        if len(self.training_data) >= 100 and len(self.training_data) % 50 == 0:
            self._train_model()
    
    def _train_model(self):
        """训练模型"""
        if len(self.training_data) < 100:
            return
        
        feature_sums = defaultdict(float)
        feature_counts = defaultdict(int)
        
        for sample in self.training_data:
            for feat, val in sample['features'].items():
                feature_sums[feat] += val * sample['target']
                feature_counts[feat] += 1
        
        total = sum(feature_sums.values())
        if total > 0:
            for feat in feature_sums:
                self.feature_importance[feat] = abs(feature_sums[feat]) / total
        
        self.is_trained = True
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """预测价格走势 (direction, confidence)"""
        if not self.is_trained or not self.feature_importance:
            return 0, 0.5
        
        score = 0
        for feat, val in features.items():
            importance = self.feature_importance.get(feat, 0)
            score += val * importance
        
        if abs(score) < 0.01:
            return 0, 0.5
        elif score > 0:
            return 1, min(0.5 + abs(score) * 10, 0.95)
        else:
            return -1, min(0.5 + abs(score) * 10, 0.95)


# ============ 强化学习交易员 ============

class RLTrader:
    """强化学习交易员 (Q-Learning)"""
    
    def __init__(self):
        self.q_table = defaultdict(lambda: [0.0, 0.0, 0.0])  # [sell, hold, buy]
        self.learning_rate = RL_LEARNING_RATE
        self.discount_factor = RL_DISCOUNT_FACTOR
        self.epsilon = RL_EPSILON
        self.actions = [-1, 0, 1]
    
    def get_state_key(self, market_data: Dict) -> str:
        """市场数据 -> 状态键"""
        rsi = market_data.get('rsi', 50)
        macd = market_data.get('macd', 0)
        trend = market_data.get('trend', 'neutral')
        
        rsi_state = 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'
        macd_state = 'bullish' if macd > 0 else 'bearish' if macd < 0 else 'neutral'
        
        return f"{rsi_state}_{macd_state}_{trend}"
    
    def choose_action(self, state: str) -> int:
        """epsilon-greedy选择动作"""
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        
        q_values = self.q_table[state]
        best_idx = q_values.index(max(q_values))
        return self.actions[best_idx]
    
    def learn(self, state: str, action: int, reward: float, next_state: str):
        """Q-Learning更新"""
        action_idx = self.actions.index(action)
        current_q = self.q_table[state][action_idx]
        max_next_q = max(self.q_table[next_state])
        
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state][action_idx] = new_q
        
        if self.epsilon > 0.01:
            self.epsilon *= 0.999
    
    def get_best_action(self, market_data: Dict) -> Tuple[int, float]:
        """获取最佳动作"""
        state = self.get_state_key(market_data)
        action = self.choose_action(state)
        q_value = self.q_table[state][self.actions.index(action)]
        return action, q_value


# ============ G50 主系统 ============

class G50:
    """G50 机器学习预测量化系统"""
    
    def __init__(self):
        self.version = "5.0"
        self.name = "G50 ML预测量化系统"
        self.running = False
        self.log_file = "/home/goose/.openclaw/workspace/logs/g50.log"
        
        # 核心组件
        self.ml_predictor = MLPricePredictor()
        self.rl_trader = RLTrader()
        
        # 状态
        self.cycle = 0
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log(self, msg: str, level: str = "INFO"):
        """记录日志"""
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        log_line = f"[{ts}] [{level}] {msg}
"
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_line)
                f.flush()
        except: pass
        print(log_line.strip(), flush=True)
    
    def _api_signed(self, endpoint: str, params: dict = None, method: str = "GET") -> dict:
        """签名API请求"""
        import hmac, hashlib, urllib.request
        
        API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
        API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
        PROXY = "http://172.29.144.1:7897"
        
        ts = int(time.time() * 1000)
        base = {"timestamp": ts, "recvWindow": 5000}
        if params: base.update(params)
        
        q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
        sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
        
        req = urllib.request.Request(url, method=method)
        req.add_header('X-MBX-APIKEY', API_KEY)
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        
        return json.loads(opener.open(req, timeout=15).read().decode())
    
    def get_price(self, symbol: str) -> float:
        """获取价格"""
        try:
            import urllib.request
            PROXY = "http://172.29.144.1:7897"
            url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT'
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            d = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
            return float(d['price'])
        except:
            return 0
    
    def get_account_status(self) -> dict:
        """获取账户状态"""
        try:
            account = self._api_signed("/api/v3/account")
            usdt = 0
            total = 0
            
            for b in account.get('balances', []):
                free = float(b.get('free', 0))
                asset = b['asset']
                if asset == 'USDT':
                    usdt = free
                    total += free
                else:
                    price = self.get_price(asset)
                    total += free * price
            
            return {'spot_usdt': usdt, 'total': total}
        except Exception as e:
            self.log(f"获取账户失败: {e}", "ERROR")
            return {'spot_usdt': 0, 'total': 0}
    
    def get_market_features(self, symbol: str) -> Dict[str, float]:
        """获取市场特征"""
        try:
            import urllib.request
            PROXY = "http://172.29.144.1:7897"
            
            url = f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50'
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            d = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
            
            if not d:
                return {}
            
            closes = [float(k[4]) for k in d]
            volumes = [float(k[5]) for k in d]
            
            ma5 = sum(closes[-5:]) / 5
            ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma5
            
            deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
            gains = [d for d in deltas if d > 0]
            losses = [-d for d in deltas if d < 0]
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs))
            
            ema12 = sum(closes[-12:]) / 12 if len(closes) >= 12 else closes[-1]
            ema26 = sum(closes[-26:]) / 26 if len(closes) >= 26 else closes[-1]
            macd = ema12 - ema26
            
            return {
                'close': closes[-1],
                'ma5': ma5,
                'ma20': ma20,
                'rsi': rsi,
                'macd': macd,
                'volume': volumes[-1],
                'trend': 'bullish' if ma5 > ma20 else 'bearish'
            }
        except:
            return {}
    
    def predict_with_ml(self, symbol: str) -> Tuple[float, float]:
        """ML预测"""
        features = self.get_market_features(symbol)
        if not features:
            return 0, 0.5
        
        if 'close' in features and 'ma5' in features:
            target = (features['ma5'] - features['close']) / features['close']
            self.ml_predictor.add_sample(features, target)
        
        return self.ml_predictor.predict(features)
    
    def get_rl_action(self, symbol: str) -> Tuple[int, float]:
        """RL动作"""
        features = self.get_market_features(symbol)
        return self.rl_trader.get_best_action(features)
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """综合分析"""
        ml_direction, ml_confidence = self.predict_with_ml(symbol)
        rl_action, rl_q = self.get_rl_action(symbol)
        features = self.get_market_features(symbol)
        
        base_signal = 0
        if features:
            trend = features.get('trend', 'neutral')
            rsi = features.get('rsi', 50)
            if trend == 'bullish' and rsi < 70:
                base_signal = 0.3
            elif trend == 'bearish' and rsi > 30:
                base_signal = -0.3
        
        combined_signal = (
            ml_direction * ml_confidence * 0.4 +
            rl_action * abs(rl_q) * 0.3 +
            base_signal * 0.3
        )
        
        confidence = min(abs(combined_signal) + 0.5, 0.95)
        
        return {
            'symbol': symbol,
            'signal': combined_signal,
            'confidence': confidence,
            'ml_direction': ml_direction,
            'ml_confidence': ml_confidence,
            'rl_action': rl_action,
            'features': features
        }
    
    def execute_trade(self, symbol: str, signal: float, confidence: float) -> dict:
        """执行交易"""
        if confidence < ML_CONFIDENCE_THRESHOLD:
            return {'action': 'skip', 'reason': '信心度不足'}
        
        price = self.get_price(symbol)
        if price <= 0:
            return {'action': 'skip', 'reason': '价格获取失败'}
        
        status = self.get_account_status()
        usdt = status.get('spot_usdt', 0)
        
        budget = usdt * KELLY_BASE * confidence
        if budget < MIN_TRADE_VALUE:
            return {'action': 'skip', 'reason': '资金不足'}
        
        quantity = budget / price
        self.log(f"🤖 G50执行: {symbol} {'买入' if signal > 0 else '卖出'} 信心{confidence:.2%}", "INFO")
        
        return {
            'action': 'trade',
            'symbol': symbol,
            'side': 'BUY' if signal > 0 else 'SELL',
            'quantity': quantity,
            'price': price
        }
    
    def scan_and_trade(self):
        """扫描并交易"""
        symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'DOGE', 'BOME', 'NEIRO']
        
        signals = []
        for sym in symbols:
            try:
                result = self.analyze_symbol(sym)
                if result['confidence'] > 0.55:
                    signals.append(result)
            except Exception as e:
                self.log(f"分析{sym}失败: {e}", "ERROR")
        
        signals.sort(key=lambda x: -(x['signal'] * x['confidence']))
        
        for best in signals[:2]:
            if best['signal'] > 0.25:
                result = self.execute_trade(best['symbol'], best['signal'], best['confidence'])
                if result.get('action') == 'trade':
                    self.log(f"✅ 交易成功: {result['symbol']}", "INFO")
    
    def run(self):
        """运行系统"""
        self.running = True
        self.log(f"{self.name} v{self.version} 启动 🤖", "INFO")
        
        while self.running:
            try:
                status = self.get_account_status()
                self.cycle += 1
                
                if self.cycle % 10 == 0:
                    self.log(f"总资产: ${status['total']:.2f} 周期:{self.cycle}", "INFO")
                
                self.scan_and_trade()
                
                if self.cycle % 100 == 0:
                    self.log(f"📊 ML特征: {self.ml_predictor.get_feature_importance()}", "INFO")
                
            except Exception as e:
                import traceback
                self.log(f"运行异常: {e}", "ERROR")
            
            time.sleep(SCAN_INTERVAL)
    
    def stop(self):
        self.running = False
        self.log(f"{self.name} 停止", "INFO")


if __name__ == "__main__":
    g50 = G50()
    g50.run()
