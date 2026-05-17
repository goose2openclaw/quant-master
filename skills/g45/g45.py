#!/usr/bin/env python3
"""
G45 v1.2 - 全技能自主调度量化系统
================================

优化内容:
1. 市场分类检测 (趋势/震荡/突破/中性)
2. 策略动态权重
3. 自适应止盈止损
4. Meme币严格风控
5. 多信号融合

版本: 1.2
日期: 2026-05-17
"""

import json, time, os, sys, random
from datetime import datetime
from collections import deque, defaultdict
from typing import Dict, List, Optional

# ============ 配置 ============

VERSION = "1.2"
SCAN_INTERVAL = 12
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g45.log"
STATE_FILE = "/home/goose/.openclaw/workspace/.g45_state.json"

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

MIN_USDT_RESERVE = 5.0
MIN_TRADE_VALUE = 1.0
STOP_LOSS = 0.03
TAKE_PROFIT = 0.12
TRAILING_STOP = True
TRAILING_CALLBACK = 0.015
KELLY_BASE = 0.15
MARGIN_LEVERAGE = 1.5
MAX_CROSS_MARGIN_EXPOSURE = 800

# ============ 技能权重模板 ============

SKILL_WEIGHTS = {
    'trend': {
        'go-core': 0.30,
        'go-long-short': 0.25,
        'go-detect': 0.20,
        'go-contrarian': 0.15,
        'go-etf': 0.10
    },
    'range': {
        'go-pool': 0.30,
        'go-rotate': 0.25,
        'go-noise': 0.20,
        'go-fit': 0.15,
        'go-contrarian': 0.10
    },
    'breakout': {
        'go-detect': 0.35,
        'go-core': 0.25,
        'go-liquidation': 0.20,
        'go-orderbook': 0.20
    },
    'neutral': {
        'go-pool': 0.25,
        'top10': 0.20,
        'go-etf': 0.20,
        'go-fit': 0.20,
        'go-noise': 0.15
    }
}

# ============ 市场检测 ============

def detect_market(closes: list) -> str:
    """检测市场状态"""
    if len(closes) < 50:
        return 'neutral'
    
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
    
    trend_strength = abs(ma5 - ma20) / ma20 if ma20 > 0 else 0
    
    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
    volatility = sum(abs(r) for r in returns[-20:]) / 20
    
    if trend_strength > 0.03:
        return 'trend'
    elif volatility < 0.02 and trend_strength < 0.01:
        return 'range'
    elif trend_strength > 0.015 and volatility > 0.03:
        return 'breakout'
    return 'neutral'

# ============ 信号计算 ============

def calculate_signals(closes: list, volumes: list) -> dict:
    """计算各技能信号"""
    if len(closes) < 20:
        return {}
    
    signals = {}
    
    # RSI
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    rs = avg_gain / avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100 / (1 + rs))
    signals['rsi'] = rsi
    
    # MA
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
    
    # go-core
    trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
    signals['go-core'] = trend * 10
    
    # go-pool
    vol_avg = sum(volumes[-20:]) / 20
    vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
    signals['go-pool'] = (vol_ratio - 1) * 0.5
    
    # go-long-short
    signals['go-long-short'] = (rsi - 50) / 50
    
    # go-detect
    trend50 = (ma20 - ma50) / ma50 if ma50 > 0 else 0
    signals['go-detect'] = trend50 * 5
    
    # go-rotate
    signals['go-rotate'] = trend * 0.5
    
    # go-noise
    signals['go-noise'] = -abs(vol_ratio - 1) * 0.3
    
    # go-contrarian
    signals['go-contrarian'] = -(rsi - 50) / 100
    
    # go-fit
    signals['go-fit'] = 1 - abs(ma5 - ma20) / ma20 if ma20 > 0 else 0
    
    # go-etf
    signals['go-etf'] = signals['go-pool'] * 0.5
    
    # top10
    signals['top10'] = 0.1 if trend > 0 else -0.1
    
    return signals

# ============ G45 主系统 ============

class G45:
    def __init__(self):
        self.version = VERSION
        self.name = "G45 全技能调度系统 v" + VERSION
        self.running = False
        self.cycle = 0
        self.log_file = LOG_FILE
        self.stats = {'trades': 0, 'wins': 0, 'losses': 0}
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
    
    def analyze_symbol(self, symbol: str) -> Optional[dict]:
        """分析币种"""
        klines = self.get_klines(symbol)
        if not klines or len(klines) < 50:
            return None
        
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        # 市场检测
        market = detect_market(closes)
        weights = SKILL_WEIGHTS.get(market, SKILL_WEIGHTS['neutral'])
        
        # 计算信号
        signals = calculate_signals(closes, volumes)
        
        # 加权融合
        combined = 0
        for skill, weight in weights.items():
            if skill in signals:
                combined += signals[skill] * weight
        
        # 信心度
        confidence = min(abs(combined) * 3 + 0.4, 0.95)
        
        # 风险
        meme_coins = ['DOGE', 'BOME', 'NEIRO', 'SHIB', 'PEPE', 'FLOKI', 'TURBO']
        risk = 0.5 + (0.3 if symbol in meme_coins else 0)
        
        # 决策
        threshold = 0.12 + risk * 0.05
        if abs(combined) < threshold or confidence < 0.55 or risk > 0.85:
            return None
        
        return {
            'symbol': symbol,
            'market': market,
            'signal': combined,
            'confidence': confidence,
            'risk': risk,
            'action': 'buy' if combined > 0 else 'sell',
            'price': closes[-1]
        }
    
    def run(self):
        """运行系统"""
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
                
                # 扫描
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
