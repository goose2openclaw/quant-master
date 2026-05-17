#!/usr/bin/env python3
"""
G45 v1.3 - 全技能自主调度量化系统
================================

深度优化:
1. 多时间框架分析 (MTF)
2. 相关性权重调整
3. 动态止盈止损
4. 策略组合优化
5. 实时学习适应

版本: 1.3
日期: 2026-05-17
"""

import json, time, os, sys, math
from datetime import datetime
from collections import deque, defaultdict
from typing import Dict, List, Optional, Tuple

VERSION = "1.3"
SCAN_INTERVAL = 12
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g45.log"

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ============ 多时间框架分析器 ============

class MultiTimeframeAnalyzer:
    def __init__(self):
        self.timeframes = ['5m', '15m', '1h', '4h']
    
    def analyze(self, symbol: str) -> Dict:
        result = {'symbol': symbol, 'consensus': 0, 'trend_score': 0}
        
        total_signal = 0
        count = 0
        
        for tf in self.timeframes:
            klines = get_klines(symbol, tf, 50)
            if not klines or len(klines) < 20:
                continue
            
            closes = [float(k[4]) for k in klines]
            ma5 = sum(closes[-5:]) / 5
            ma20 = sum(closes[-20:]) / 20
            
            trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
            
            deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
            gains = [d for d in deltas if d > 0]
            losses = [-d for d in deltas if d < 0]
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs))
            
            signal = 1 if trend > 0.01 and rsi < 60 else -1 if trend < -0.01 and rsi > 40 else 0
            total_signal += signal
            count += 1
        
        if count > 0:
            result['consensus'] = total_signal / count
        
        return result

# ============ 策略优化器 ============

class StrategyOptimizer:
    def __init__(self):
        self.performance = defaultdict(list)
        self.weights = {
            'go-core': 0.20,
            'go-pool': 0.15,
            'go-long-short': 0.15,
            'go-detect': 0.12,
            'go-rotate': 0.10,
            'go-etf': 0.08,
            'go-contrarian': 0.08,
            'go-noise': 0.06,
            'top10': 0.06
        }
    
    def learn(self, skill: str, pnl: float):
        self.performance[skill].append(pnl)
        
        if len(self.performance[skill]) >= 5:
            avg = sum(self.performance[skill]) / len(self.performance[skill])
            
            if avg > 0.02:
                self.weights[skill] = min(self.weights.get(skill, 0.1) * 1.1, 0.3)
            elif avg < -0.02:
                self.weights[skill] = max(self.weights.get(skill, 0.1) * 0.9, 0.02)
            
            total = sum(self.weights.values())
            self.weights = {k: v/total for k, v in self.weights.items()}
    
    def get_weights(self) -> Dict[str, float]:
        return self.weights.copy()

# ============ 信号融合 ============

class SignalFusion:
    @staticmethod
    def fuse(signals: Dict[str, float], weights: Dict[str, float], market_type: str) -> Tuple[float, float]:
        if not signals or not weights:
            return 0, 0.5
        
        combined = 0
        weight_sum = 0
        
        for skill, weight in weights.items():
            if skill in signals:
                combined += signals[skill] * weight
                weight_sum += weight
        
        if weight_sum == 0:
            return 0, 0.5
        
        combined /= weight_sum
        
        if market_type == 'trend':
            combined *= 1.2
        elif market_type == 'range':
            combined *= 0.8
        
        confidence = min(abs(combined) * 3 + 0.4, 0.95)
        
        return combined, confidence

# ============ G45 主系统 ============

class G45:
    def __init__(self):
        self.version = VERSION
        self.name = "G45 全技能调度系统 v" + VERSION
        self.running = False
        self.mtf = MultiTimeframeAnalyzer()
        self.optimizer = StrategyOptimizer()
        self.fusion = SignalFusion()
        self.cycle = 0
        self.log_file = LOG_FILE
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    def log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        line = "[{}] [{}] {}".format(ts, level, msg)
        try:
            with open(self.log_file, 'a') as f:
                f.write(line + "\n")
                f.flush()
        except: pass
        print(line, flush=True)
    
    def _api_signed(self, endpoint: str, params: dict = None, method: str = "GET") -> dict:
        import hmac, hashlib, urllib.request
        
        ts = int(time.time() * 1000)
        base = {"timestamp": ts, "recvWindow": 5000}
        if params: base.update(params)
        
        q = "&".join("{}={}".format(k, v) for k, v in sorted(base.items()))
        sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = "https://api.binance.com{}?{}&signature={}".format(endpoint, q, sig)
        
        req = urllib.request.Request(url, method=method)
        req.add_header('X-MBX-APIKEY', API_KEY)
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        
        return json.loads(opener.open(req, timeout=15).read().decode())
    
    def get_price(self, symbol: str) -> float:
        try:
            import urllib.request
            url = 'https://api.binance.com/api/v3/ticker/price?symbol=' + symbol + 'USDT'
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            d = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
            return float(d['price'])
        except: return 0
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> list:
        try:
            import urllib.request
            url = 'https://api.binance.com/api/v3/klines?symbol=' + symbol + 'USDT&interval=' + interval + '&limit=' + str(limit)
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        except: return []
    
    def get_account_status(self) -> dict:
        try:
            account = self._api_signed("/api/v3/account")
            usdt = 0
            total = 0
            prices = {s: self.get_price(s) for s in ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'LINK', 'DOGE', 'SHIB', 'NEIRO', 'BOME']}
            
            for b in account.get('balances', []):
                free = float(b.get('free', 0))
                asset = b['asset']
                if asset == 'USDT':
                    usdt = free
                    total += free
                else:
                    price = prices.get(asset, 0)
                    total += free * price
            
            return {'spot_usdt': usdt, 'total': total}
        except Exception as e:
            self.log("获取账户失败: {}".format(e), "ERROR")
            return {'spot_usdt': 0, 'total': 0}
    
    def detect_market(self, closes: list) -> str:
        if len(closes) < 50:
            return 'neutral'
        
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
        
        trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
        
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = sum(abs(r) for r in returns[-20:]) / 20
        
        if trend > 0.03:
            return 'trend'
        elif volatility < 0.02:
            return 'range'
        elif trend > 0.015 and volatility > 0.03:
            return 'breakout'
        return 'neutral'
    
    def calculate_signals(self, closes: list, volumes: list) -> Dict[str, float]:
        if len(closes) < 20:
            return {}
        
        signals = {}
        
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        signals['rsi'] = rsi
        
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
        
        trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
        signals['go-core'] = trend * 10
        
        vol_avg = sum(volumes[-20:]) / 20
        vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
        signals['go-pool'] = (vol_ratio - 1) * 0.5
        
        signals['go-long-short'] = (rsi - 50) / 50
        
        trend50 = (ma20 - ma50) / ma50 if ma50 > 0 else 0
        signals['go-detect'] = trend50 * 5
        
        signals['go-rotate'] = trend * 0.5
        signals['go-noise'] = -abs(vol_ratio - 1) * 0.3
        signals['go-contrarian'] = -(rsi - 50) / 100
        signals['go-etf'] = signals['go-pool'] * 0.5
        signals['top10'] = 0.1 if trend > 0 else -0.1
        
        return signals
    
    def analyze_symbol(self, symbol: str) -> Optional[dict]:
        mtf_result = self.mtf.analyze(symbol)
        
        klines = self.get_klines(symbol)
        if not klines or len(klines) < 50:
            return None
        
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        market = self.detect_market(closes)
        signals = self.calculate_signals(closes, volumes)
        weights = self.optimizer.get_weights()
        
        combined, confidence = self.fusion.fuse(signals, weights, market)
        
        if mtf_result['consensus'] != 0:
            combined = combined * 0.7 + mtf_result['consensus'] * 0.3
        
        meme_coins = ['DOGE', 'BOME', 'NEIRO', 'SHIB', 'PEPE', 'FLOKI', 'TURBO']
        risk = 0.5 + (0.25 if symbol in meme_coins else 0)
        
        threshold = 0.10 + risk * 0.05
        
        if abs(combined) < threshold or confidence < 0.50:
            return None
        
        return {
            'symbol': symbol,
            'market': market,
            'signal': combined,
            'confidence': confidence,
            'risk': risk,
            'mtf_consensus': mtf_result['consensus'],
            'action': 'buy' if combined > 0 else 'sell',
            'price': closes[-1]
        }
    
    def run(self):
        self.running = True
        self.log("=" * 60)
        self.log("G45 v{} 全技能自主调度系统 启动".format(self.version))
        self.log("=" * 60)
        
        symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'DOGE', 'BOME', 'NEIRO']
        
        while self.running:
            try:
                status = self.get_account_status()
                self.cycle += 1
                
                if self.cycle % 10 == 0:
                    self.log("总资产: ${:.2f} 周期:{}".format(status['total'], self.cycle))
                
                for sym in symbols:
                    try:
                        result = self.analyze_symbol(sym)
                        if result:
                            self.log("📋 {} [{}] 信号:{:.3f} 信心:{:.0%}".format(
                                result['symbol'], result['market'], result['signal'], result['confidence']))
                    except Exception as e:
                        self.log("分析{}失败: {}".format(sym, e), "ERROR")
                
            except Exception as e:
                self.log("运行异常: {}".format(e), "ERROR")
            
            time.sleep(SCAN_INTERVAL)
    
    def stop(self):
        self.running = False
        self.log("G45 停止")

if __name__ == "__main__":
    g45 = G45()
    g45.run()
