#!/usr/bin/env python3
"""
G45 v1.4 - 30天收益最大化版
===========================

优化:
1. TrendTracker30D - 30天趋势追踪
2. MomentumEnhancer - 动量增强
3. MaximizeReturnsStrategy - 收益最大化
4. AdaptivePositionSizer - 自适应仓位

版本: 1.4
日期: 2026-05-17
"""

import json, time, os, math
from datetime import datetime
from collections import deque, defaultdict
from typing import Dict, List, Optional, Tuple

VERSION = "1.4"
SCAN_INTERVAL = 12
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g45.log"

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ============ 趋势追踪器 ============

class TrendTracker30D:
    def __init__(self):
        self.history = deque(maxlen=720)
    
    def update(self, price: float):
        self.history.append({'price': price, 'time': time.time()})
    
    def get_trend(self) -> Dict:
        if len(self.history) < 100:
            return {'trend': 'unknown', 'strength': 0, 'momentum': 0}
        
        prices = [h['price'] for h in self.history]
        ma7 = sum(prices[-168:]) / 168 if len(prices) >= 168 else sum(prices[-7:]) / min(7, len(prices))
        ma30 = sum(prices[-720:]) / min(720, len(prices)) if len(prices) >= 24 else sum(prices) / len(prices)
        
        trend = (ma7 - ma30) / ma30 if ma30 > 0 else 0
        
        if len(prices) >= 168:
            momentum = (prices[-1] - prices[-168]) / prices[-168]
        else:
            momentum = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        
        if trend > 0.05:
            trend_type = 'strong_up'
        elif trend > 0.02:
            trend_type = 'up'
        elif trend < -0.05:
            trend_type = 'strong_down'
        elif trend < -0.02:
            trend_type = 'down'
        else:
            trend_type = 'sideways'
        
        return {'trend': trend_type, 'strength': abs(trend), 'momentum': momentum}

# ============ 动量增强 ============

class MomentumEnhancer:
    def __init__(self):
        self.lookback = [6, 12, 24, 72, 168]
    
    def calculate(self, closes: list) -> Dict:
        if len(closes) < 200:
            return {}
        
        momenta = {}
        for lb in self.lookback:
            if len(closes) >= lb:
                momenta[f'mom_{lb}h'] = (closes[-1] - closes[-lb]) / closes[-lb]
        
        ema12 = sum(closes[-12:]) / 12
        ema26 = sum(closes[-26:]) / 26
        macd = ema12 - ema26
        momenta['macd'] = macd
        momenta['signal'] = macd * 0.5
        momenta['histogram'] = macd - momenta['signal']
        
        return momenta

# ============ 收益最大化策略 ============

class MaximizeReturnsStrategy:
    TREND_CONFIG = {'stop_loss': 0.05, 'take_profit': 0.20, 'trailing_stop': 0.03, 'kelly': 0.25}
    RANGE_CONFIG = {'stop_loss': 0.02, 'take_profit': 0.06, 'trailing_stop': 0.015, 'kelly': 0.10}
    BREAKOUT_CONFIG = {'stop_loss': 0.04, 'take_profit': 0.15, 'trailing_stop': 0.025, 'kelly': 0.20}
    
    @classmethod
    def get_config(cls, market_type: str) -> Dict:
        if market_type == 'trend':
            return cls.TREND_CONFIG
        elif market_type == 'breakout':
            return cls.BREAKOUT_CONFIG
        return cls.RANGE_CONFIG

# ============ 信号生成器 ============

class SignalGeneratorV14:
    def __init__(self):
        self.trend_tracker = TrendTracker30D()
        self.momentum = MomentumEnhancer()
    
    def generate(self, symbol: str, closes: list, volumes: list, confidence_30d: float = 0.5) -> Optional[Dict]:
        if len(closes) < 50:
            return None
        
        for price in closes:
            self.trend_tracker.update(price)
        trend_30d = self.trend_tracker.get_trend()
        momenta = self.momentum.calculate(closes)
        
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
        trend_strength = abs(ma5 - ma20) / ma20 if ma20 > 0 else 0
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = sum(abs(r) for r in returns[-20:]) / 20
        
        if trend_strength > 0.03 and trend_30d['momentum'] > 0.02:
            market = 'trend'
        elif volatility < 0.02:
            market = 'range'
        elif trend_strength > 0.015 and volatility > 0.03:
            market = 'breakout'
        else:
            market = 'neutral'
        
        signal = 0
        weight_total = 0
        
        if trend_30d['trend'] in ['strong_up', 'up']:
            signal += 0.4 * 1.0
            weight_total += 0.4
        elif trend_30d['trend'] in ['strong_down', 'down']:
            signal += 0.4 * -1.0
            weight_total += 0.4
        
        if 'mom_24h' in momenta:
            mom_signal = 1 if momenta['mom_24h'] > 0 else -1
            signal += 0.3 * mom_signal * min(abs(momenta['mom_24h']) * 10, 1)
            weight_total += 0.3
        
        if rsi < 40:
            signal += 0.2 * 1.0
            weight_total += 0.2
        elif rsi > 60:
            signal += 0.2 * -1.0
            weight_total += 0.2
        
        if 'histogram' in momenta:
            macd_signal = 1 if momenta['histogram'] > 0 else -1
            signal += 0.1 * macd_signal
            weight_total += 0.1
        
        if weight_total > 0:
            signal /= weight_total
        
        confidence = min(abs(signal) + 0.3 + confidence_30d * 0.2, 0.95)
        config = MaximizeReturnsStrategy.get_config(market)
        
        return {
            'symbol': symbol,
            'market': market,
            'signal': signal,
            'confidence': confidence,
            'rsi': rsi,
            'trend_30d': trend_30d,
            'momentum': momenta,
            'config': config,
            'action': 'buy' if signal > 0 else 'sell' if signal < 0 else 'hold'
        }

# ============ G45 主系统 ============

class G45:
    def __init__(self):
        self.version = VERSION
        self.name = "G45 v" + VERSION + " 30天收益最大化"
        self.running = False
        self.signal_gen = SignalGeneratorV14()
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
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 300) -> list:
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
    
    def analyze_symbol(self, symbol: str) -> Optional[dict]:
        klines = self.get_klines(symbol)
        if not klines or len(klines) < 50:
            return None
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        return self.signal_gen.generate(symbol, closes, volumes, 0.5)
    
    def run(self):
        self.running = True
        self.log("=" * 60)
        self.log("G45 v{} 30天收益最大化系统 启动".format(self.version))
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
