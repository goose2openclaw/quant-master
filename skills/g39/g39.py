#!/usr/bin/env python3
"""
G39 - 全集成自主量化交易系统
===================
整合 G38 + 轮动 + 多空 + ETF流动性 + 资产管理的超级系统
"""

import json
import time
import math
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque

# ============ 配置 ============

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

STATE_FILE = "/home/goose/.openclaw/workspace/.g39_state.json"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g39.log"

SCAN_INTERVAL = 30
STOP_LOSS = 0.05
TAKE_PROFIT = 0.20
KELLY_BASE = 0.30
MAX_POSITIONS = 3

MAINSTREAM = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT']
MEME = ['PEPE', 'BONK', 'DOGE', 'SHIB', 'FLOKI', 'BOME', 'TURBO', 'NEIRO']

# ============ API工具 ============

def api_signed(endpoint: str, params: dict = None, method: str = "GET") -> dict:
    for i in range(3):
        try:
            import hmac, hashlib, urllib.request
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
        except:
            if i < 2: time.sleep(0.3)
    return {}

def api_pub(url: str) -> dict:
    try:
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return {}

import urllib.request

def get_price(symbol: str) -> float:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT')
        return float(data['price']) if data else 0
    except: return 0

def get_klines(symbol: str, interval: str = '1h', limit: int = 100) -> List[dict]:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}')
        return [{'time': k[0], 'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]),
                 'close': float(k[4]), 'volume': float(k[5])} for k in data] if data else []
    except: return []

# ============ 数据类 ============

@dataclass
class G39Signal:
    symbol: str
    direction: str
    confidence: float
    signal: float
    strategy: str
    phase: str
    market_type: str
    stop_loss: float
    take_profit: float
    position_size: float
    top_traders: List[str]
    sources: Dict[str, float]

@dataclass
class AccountStatus:
    spot_total: float
    cross_total: float
    isolated_total: float
    futures_total: float
    grand_total: float
    spot_usdt: float

# ============ 统计分析 ============

class Statistics:
    @staticmethod
    def mean(data: List[float]) -> float:
        return sum(data) / len(data) if data else 0
    
    @staticmethod
    def std(data: List[float]) -> float:
        if len(data) < 2: return 0
        m = Statistics.mean(data)
        return math.sqrt(sum((x - m) ** 2 for x in data) / (len(data) - 1))
    
    @staticmethod
    def rsi(closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1: return 50
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        return 100 - (100 / (1 + avg_gain / (avg_loss + 1e-10))) if avg_loss != 0 else 100
    
    @staticmethod
    def zscore(value: float, data: List[float]) -> float:
        m = Statistics.mean(data)
        s = Statistics.std(data)
        return (value - m) / s if s > 0 else 0

# ============ Top10交易员 (来自G38) ============

TRADERS = {
    'Soros': {'weight': 0.12, 'stop_loss': 0.08, 'take_profit': 0.25, 'strategy': 'reflexivity'},
    'Druckenmiller': {'weight': 0.10, 'stop_loss': 0.06, 'take_profit': 0.20, 'strategy': 'liquidity'},
    'Marcus': {'weight': 0.15, 'stop_loss': 0.10, 'take_profit': 0.30, 'strategy': 'trend_following'},
    'Jones': {'weight': 0.12, 'stop_loss': 0.05, 'take_profit': 0.20, 'strategy': 'ma_system'},
    'Schwartz': {'weight': 0.10, 'stop_loss': 0.08, 'take_profit': 0.25, 'strategy': 'candlestick'},
    'Kovner': {'weight': 0.08, 'stop_loss': 0.05, 'take_profit': 0.18, 'strategy': 'breakout'},
    'Dennis': {'weight': 0.08, 'stop_loss': 0.05, 'take_profit': 0.15, 'strategy': 'systematic'},
    'Lipschutz': {'weight': 0.08, 'stop_loss': 0.06, 'take_profit': 0.22, 'strategy': 'trend_trade'},
    'Livermore': {'weight': 0.09, 'stop_loss': 0.07, 'take_profit': 0.25, 'strategy': 'key_reversal'},
    'Rogers': {'weight': 0.08, 'stop_loss': 0.05, 'take_profit': 0.20, 'strategy': 'trend_id'}
}

# ============ G39 主系统 ============

class G39:
    """G39 全集成自主量化交易系统"""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.log_file = LOG_FILE
        self.positions = {}
        self.history = []
        self.is_running = False
        self.strategy_weights = self._init_weights()
        
        self.load_state()
    
    def _init_weights(self) -> Dict:
        """初始化策略权重"""
        return {
            'go-core': 0.20,
            'go-fit': 0.10,
            'go-noise': 0.08,
            'go-thermo': 0.08,
            'go-detect': 0.12,
            'go-pool': 0.15,
            'go-rotate': 0.12,
            'go-long-short': 0.15,
            'go-etf': 0.10,
            'go-ensemble': 0.05,
            'go-meta': 0.05
        }
    
    def log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, "a") as f:
                f.write(line + "\n")
        except: pass
    
    def load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file) as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.history = state.get('history', [])
                    self.strategy_weights = state.get('weights', self.strategy_weights)
        except: pass
    
    def save_state(self):
        try:
            state = {
                'positions': self.positions,
                'history': self.history[-100:],
                'weights': self.strategy_weights,
                'timestamp': time.time()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except: pass
    
    # ============ 各模块信号 ============
    
    def _get_go_core_signal(self, symbol: str) -> Dict:
        """go-core 核心预测"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5}
        
        closes = [k['close'] for k in klines]
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        mom_long = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else mom
        
        signal = max(-1, min(1, mom_long * 5))
        confidence = abs(signal) * 0.8 + 0.2
        
        return {'signal': signal, 'confidence': confidence}
    
    def _get_go_fit_signal(self, symbol: str) -> Dict:
        """go-fit 趋势拟合"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'signal': 0, 'confidence': 0.5}
        
        closes = [k['close'] for k in klines]
        trend = (closes[-1] - closes[0]) / (max(closes) - min(closes) + 1e-10)
        aligns = sum(1 for i in range(1, len(closes)) if (closes[i] - closes[i-1]) > 0)
        persistence = aligns / (len(closes) - 1) if len(closes) > 1 else 0.5
        
        score = (trend + 1) / 2 * persistence
        return {'signal': (score - 0.5) * 2, 'confidence': 0.5 + persistence * 0.3}
    
    def _get_go_noise_signal(self, symbol: str) -> Dict:
        """go-noise 噪音过滤"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'signal': 0, 'confidence': 0.5}
        
        closes = [k['close'] for k in klines]
        returns = [math.log(closes[i]/closes[i-1]) for i in range(1, len(closes))]
        variance = sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns) if returns else 0
        noise_ratio = min(1, variance * 100)
        filtered = noise_ratio < 0.3
        
        return {'signal': -noise_ratio if filtered else noise_ratio * 0.5, 'confidence': 1 - noise_ratio}
    
    def _get_go_thermo_signal(self, symbol: str) -> Dict:
        """go-thermo 热力分析"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'phase': 'normal'}
        
        closes = [k['close'] for k in klines]
        returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
        volatility = math.sqrt(sum(r**2 for r in returns) / len(returns)) if returns else 0
        trend = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0
        temp = volatility / (abs(trend) + 0.01)
        
        phase = 'hot' if temp > 1 else 'cold' if temp < 0.5 else 'normal'
        signal = (1 - min(1, temp)) if phase == 'cold' else -(min(1, temp) - 0.5)
        
        return {'signal': signal, 'confidence': 0.6, 'phase': phase, 'temperature': temp}
    
    def _get_go_detect_signal(self, symbol: str) -> Dict:
        """go-detect 机构侦测"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'signal': 0, 'confidence': 0.5}
        
        volumes = [k['volume'] for k in klines]
        closes = [k['close'] for k in klines]
        
        avg_vol = sum(volumes) / len(volumes) if volumes else 0
        recent_vol = volumes[-1] if volumes else avg_vol
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        price_change = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0
        
        pressure = vol_ratio * abs(price_change) * 10
        direction = 'long' if price_change > 0 else 'short' if price_change < 0 else 'neutral'
        
        return {'signal': pressure if direction == 'long' else -pressure, 'confidence': min(1, pressure), 'direction': direction}
    
    def _get_go_pool_signal(self, symbol: str) -> Dict:
        """go-pool 撞球策略"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'phase': 'consolidation'}
        
        closes = [k['close'] for k in klines]
        rsi = Statistics.rsi(closes)
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        mom_long = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else mom
        
        # 阶段判断
        if mom_long < -0.08: phase = "decline"
        elif mom_long > 0.15:
            phase = "peak" if rsi > 75 else "acceleration" if mom > 0.03 and rsi > 55 else "startup"
        elif rsi > 72: phase = "peak"
        elif mom > 0.025 and rsi > 50: phase = "acceleration"
        elif rsi < 45 and mom > 0: phase = "startup"
        else: phase = "consolidation"
        
        phase_signals = {"acceleration": 0.8, "startup": 0.5, "consolidation": 0, "peak": -0.5, "decline": -0.8}
        
        return {'signal': phase_signals.get(phase, 0), 'confidence': 0.6, 'phase': phase}
    
    def _get_go_rotate_signal(self, symbol: str) -> Dict:
        """go-rotate 轮动策略"""
        klines = get_klines(symbol, '5m', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'action': 'hold'}
        
        closes = [k['close'] for k in klines]
        current_price = closes[-1]
        mean_price = Statistics.mean(closes)
        std_price = Statistics.std(closes)
        zscore = (current_price - mean_price) / std_price if std_price > 0 else 0
        rsi = Statistics.rsi(closes)
        
        if zscore < -1.5 or rsi < 35:
            action = 'buy'
            confidence = min(1, abs(zscore) / 2)
        elif zscore > 1.5 or rsi > 65:
            action = 'sell'
            confidence = min(1, zscore / 2)
        else:
            action = 'hold'
            confidence = 0.5
        
        signal = 0.5 if action == 'buy' else -0.5 if action == 'sell' else 0
        
        return {'signal': signal, 'confidence': confidence, 'action': action, 'zscore': zscore}
    
    def _get_go_long_short_signal(self, symbol: str) -> Dict:
        """go-long-short 多空策略"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'direction': 'neutral'}
        
        closes = [k['close'] for k in klines]
        rsi = Statistics.rsi(closes)
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        
        # 多空判断
        if rsi < 40 and mom > 0: direction = 'long'
        elif rsi > 60 and mom < 0: direction = 'short'
        else: direction = 'neutral'
        
        signal = 0.6 if direction == 'long' else -0.6 if direction == 'short' else 0
        
        return {'signal': signal, 'confidence': 0.7, 'direction': direction}
    
    def _get_go_etf_signal(self, symbol: str) -> Dict:
        """go-etf-liquidity ETF流动性"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'direction': 'neutral'}
        
        closes = [k['close'] for k in klines]
        volumes = [k['volume'] for k in klines]
        
        # 模拟ETF信号
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        vol_ratio = volumes[-1] / (sum(volumes) / len(volumes)) if volumes else 1
        
        signal = mom * 3
        direction = 'bullish' if signal > 0.2 else 'bearish' if signal < -0.2 else 'neutral'
        
        return {'signal': signal, 'confidence': 0.65, 'direction': direction}
    
    def _get_top10_trader_signal(self, symbol: str) -> Tuple[float, List[str]]:
        """Top10交易员信号"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return 0, []
        
        closes = [k['close'] for k in klines]
        rsi = Statistics.rsi(closes)
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        
        trader_signals = {}
        
        for name, trader in TRADERS.items():
            signal = 0
            if trader['strategy'] == 'trend_following':
                signal = min(1, mom * 10) if mom > 0 else max(-1, mom * 10)
            elif trader['strategy'] == 'candlestick':
                signal = 0.6 if rsi < 35 else -0.5 if rsi > 65 else 0
            elif trader['strategy'] == 'breakout':
                high_20 = max(closes[-20:]) if len(closes) >= 20 else max(closes)
                low_20 = min(closes[-20:]) if len(closes) >= 20 else min(closes)
                signal = 0.6 if closes[-1] >= high_20 else -0.6 if closes[-1] <= low_20 else 0
            else:
                signal = mom * 5
            
            trader_signals[name] = signal * trader['weight']
        
        combined = sum(trader_signals.values())
        top_traders = sorted(trader_signals.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        
        return combined, [t[0] for t in top_traders]
    
    # ============ 综合分析 ============
    
    def analyze(self, symbol: str) -> G39Signal:
        """完整分析"""
        # 获取各模块信号
        signals = {
            'go-core': self._get_go_core_signal(symbol),
            'go-fit': self._get_go_fit_signal(symbol),
            'go-noise': self._get_go_noise_signal(symbol),
            'go-thermo': self._get_go_thermo_signal(symbol),
            'go-detect': self._get_go_detect_signal(symbol),
            'go-pool': self._get_go_pool_signal(symbol),
            'go-rotate': self._get_go_rotate_signal(symbol),
            'go-long-short': self._get_go_long_short_signal(symbol),
            'go-etf': self._get_go_etf_signal(symbol)
        }
        
        # Top10交易员
        trader_signal, top_traders = self._get_top10_trader_signal(symbol)
        signals['top10'] = {'signal': trader_signal, 'confidence': 0.7}
        
        # 综合评分
        weights = {**self.strategy_weights, 'top10': 0.15}
        
        combined_signal = 0
        combined_confidence = 0
        total_weight = 0
        sources = {}
        
        for name, w in weights.items():
            if name in signals:
                s = signals[name]['signal']
                c = signals[name].get('confidence', 0.5)
                combined_signal += s * w
                combined_confidence += c * w
                sources[name] = s * w
                total_weight += w
        
        combined_signal /= total_weight
        combined_confidence /= total_weight
        
        # 市场类型
        pool = signals['go-pool']
        market_type = 'trending' if abs(combined_signal) > 0.3 and pool['phase'] in ['acceleration', 'decline'] else 'ranging'
        
        # 策略选择
        if market_type == 'trending':
            strategy = 'pool_long' if combined_signal > 0 else 'pool_short'
        else:
            strategy = 'rotate' if signals['go-rotate']['action'] != 'hold' else 'neutral'
        
        # 方向判断
        if combined_signal > 0.15: direction = 'long'
        elif combined_signal < -0.15: direction = 'short'
        else: direction = 'neutral'
        
        # 仓位
        position_size = KELLY_BASE if direction != 'neutral' else 0
        
        return G39Signal(
            symbol=symbol,
            direction=direction,
            confidence=min(1, abs(combined_confidence)),
            signal=combined_signal,
            strategy=strategy,
            phase=pool['phase'],
            market_type=market_type,
            stop_loss=STOP_LOSS,
            take_profit=TAKE_PROFIT,
            position_size=position_size,
            top_traders=top_traders,
            sources=sources
        )
    
    def batch_analyze(self, symbols: List[str]) -> List[G39Signal]:
        """批量分析"""
        return [self.analyze(s) for s in symbols]
    
    def get_account_status(self) -> AccountStatus:
        """获取四大账户状态"""
        def get_price(symbol):
            try:
                url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
                proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
                opener = urllib.request.build_opener(proxy_handler)
                data = json.loads(opener.open(urllib.request.Request(url), timeout=5).read().decode())
                return float(data['price'])
            except: return 0
        
        # 现货账户
        spot_data = self._api_signed("/api/v3/account")
        spot_usdt = 0
        spot_total = 0
        positions = {}
        
        if spot_data and 'balances' in spot_data:
            for b in spot_data.get('balances', []):
                free = float(b.get('free', 0))
                if free > 0.0001:
                    asset = b['asset']
                    if asset == 'USDT':
                        spot_usdt = free
                        spot_total += free
                    else:
                        price = get_price(f"{asset}USDT")
                        value = free * price
                        spot_total += value
                        if value > 1:
                            positions[asset] = {'amount': free, 'value': value, 'account': 'spot'}
        
        # 全仓杠杆账户
        cross_total = 0
        cross_data = self._api_signed("/sapi/v1/margin/account")
        if cross_data and 'userAssets' in cross_data:
            for a in cross_data.get('userAssets', []):
                net = float(a.get('netAsset', 0))
                if net != 0:
                    asset = a['asset']
                    if asset == 'BTC':
                        cross_total += net * get_price('BTCUSDT')
                    elif asset == 'USDT':
                        cross_total += net
                    else:
                        price = get_price(f"{asset}USDT")
                        cross_total += net * price if price > 0 else 0
        
        # 逐仓杠杆账户
        isolated_total = 0
        isolated_data = self._api_signed("/sapi/v1/margin/isolated/account")
        if isolated_data and 'assets' in isolated_data:
            for pair in isolated_data.get('assets', []):
                base = pair.get('baseAsset', {})
                quote = pair.get('quoteAsset', {})
                net_base = float(base.get('netAsset', 0))
                net_quote = float(quote.get('netAsset', 0))
                if net_base != 0 or net_quote != 0:
                    if base.get('asset') == 'BTC':
                        isolated_total += net_base * get_price('BTCUSDT')
                    elif quote.get('asset') == 'USDT':
                        isolated_total += abs(net_quote)
                    else:
                        if net_base != 0:
                            price = get_price(f"{base.get('asset')}USDT")
                            isolated_total += net_base * price if price > 0 else 0
        
        # 合约账户 (USDT-M)
        futures_total = 0
        futures_data = self._api_signed("/fapi/v2/account")
        if futures_data and 'error' not in futures_data:
            try:
                futures_total = float(futures_data.get('totalMarginBalance', 0))
            except:
                futures_total = 0
        
        grand_total = spot_total + cross_total + isolated_total + futures_total
        
        return AccountStatus(
            spot_total=spot_total,
            cross_total=cross_total,
            isolated_total=isolated_total,
            futures_total=futures_total,
            grand_total=grand_total,
            spot_usdt=spot_usdt
        )
    
    def _api_signed(self, endpoint, params=None):
        """签名API请求 - 调用全局api_signed"""
        return api_signed(endpoint, params)
    
    def run(self):
        """主运行循环"""
        self.log("=" * 60)
        self.log("G39 全集成系统启动", "INFO")
        self.log("=" * 60)
        
        self.is_running = True
        
        while self.is_running:
            try:
                # 账户状态
                status = self.get_account_status()
                
                self.log(f"\n{'='*60}")
                self.log(f"📊 G39 账户状态", "INFO")
                self.log(f"{'='*60}")
                self.log(f"现货: ${status.spot_total:.2f}", "INFO")
                self.log(f"全仓杠杆: ${status.cross_total:.2f}", "INFO")
                self.log(f"合约: ${status.futures_total:.2f}", "INFO")
                self.log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
                self.log(f"总资产: ${status.grand_total:.2f}", "INFO")
                
                # 分析
                all_symbols = MAINSTREAM + MEME
                results = self.batch_analyze(all_symbols)
                
                # 过滤有效信号
                valid = [r for r in results if r.direction != 'neutral' and r.confidence > 0.5]
                valid.sort(key=lambda x: -x.confidence)
                
                self.log(f"\n📈 Top信号:", "INFO")
                for r in valid[:5]:
                    self.log(f"  {r.symbol}: {r.direction} {r.confidence:.0%} [{r.strategy}] ({', '.join(r.top_traders[:2])})", "INFO")
                
                self.save_state()
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                self.log(f"错误: {e}", "ERROR")
                import traceback; traceback.print_exc()
                time.sleep(10)
    
    def stop(self):
        self.is_running = False

def main():
    g = G39()
    try:
        g.run()
    except KeyboardInterrupt:
        g.stop()

if __name__ == "__main__":
    main()

# ============ 自主优化模块 ============

class G39Optimizer:
    """G39 自主优化器"""
    
    def __init__(self, g39):
        self.g39 = g39
        self.strategy_performance = {name: {'wins': 0, 'losses': 0, 'returns': []} for name in g39.strategy_weights.keys()}
        self.trade_history = deque(maxlen=500)
        self.optimizer_cooldown = 3600  # 1小时优化一次
    
    def record_trade(self, strategy: str, pnl: float, market_type: str):
        """记录交易结果"""
        self.trade_history.append({
            'strategy': strategy,
            'pnl': pnl,
            'market_type': market_type,
            'time': time.time()
        })
        
        if pnl > 0:
            self.strategy_performance[strategy]['wins'] += 1
        else:
            self.strategy_performance[strategy]['losses'] += 1
        
        self.strategy_performance[strategy]['returns'].append(pnl)
        
        # 只保留最近100条记录
        if len(self.strategy_performance[strategy]['returns']) > 100:
            self.strategy_performance[strategy]['returns'] = self.strategy_performance[strategy]['returns'][-100:]
    
    def optimize_weights(self):
        """优化策略权重"""
        now = time.time()
        if hasattr(self, 'last_optimize') and now - self.last_optimize < self.optimizer_cooldown:
            return  # 冷却中
        
        self.last_optimize = now
        
        print("\n=== 自主优化 ===")
        
        for name in self.g39.strategy_weights:
            perf = self.strategy_performance[name]
            total = perf['wins'] + perf['losses']
            
            if total < 10:
                continue  # 数据不足
            
            win_rate = perf['wins'] / total
            returns = perf['returns']
            avg_return = sum(returns) / len(returns) if returns else 0
            
            old_weight = self.g39.strategy_weights[name]
            
            # 优化规则
            if win_rate < 0.4 or avg_return < -0.05:
                # 表现差，降低权重
                new_weight = old_weight * 0.8
                reason = f"表现差(胜率{win_rate:.0%}, 均收益{avg_return:+.1%})"
            elif win_rate > 0.6 and avg_return > 0.05:
                # 表现好，提高权重
                new_weight = old_weight * 1.1
                reason = f"表现好(胜率{win_rate:.0%}, 均收益{avg_return:+.1%})"
            else:
                new_weight = old_weight
                reason = "表现中等"
            
            # 限制范围
            new_weight = max(0.05, min(0.30, new_weight))
            
            if abs(new_weight - old_weight) > 0.01:
                self.g39.strategy_weights[name] = new_weight
                print(f"  {name}: {old_weight:.2f} → {new_weight:.2f} ({reason})")
        
        # 归一化
        total = sum(self.g39.strategy_weights.values())
        for name in self.g39.strategy_weights:
            self.g39.strategy_weights[name] /= total
        
        print("=" * 30)
    
    def get_strategy_score(self, name: str) -> float:
        """获取策略评分"""
        perf = self.strategy_performance.get(name, {'wins': 0, 'losses': 0, 'returns': []})
        total = perf['wins'] + perf['losses']
        
        if total < 5:
            return 0.5  # 数据不足返回中性
        
        win_rate = perf['wins'] / total
        avg_return = sum(perf['returns']) / len(perf['returns']) if perf['returns'] else 0
        
        # 综合评分
        score = win_rate * 0.6 + (avg_return + 0.1) * 2 * 0.4
        
        return max(0, min(1, score))
    
    def auto_switch_strategy(self, symbol: str, market_type: str) -> str:
        """自动切换策略"""
        # 根据市场类型选择最佳策略
        if market_type == 'trending':
            candidates = ['go-pool', 'go-core', 'go-long-short']
        else:
            candidates = ['go-rotate', 'go-long-short', 'go-etf']
        
        best_strategy = None
        best_score = 0
        
        for strategy in candidates:
            score = self.get_strategy_score(strategy)
            if score > best_score:
                best_score = score
                best_strategy = strategy
        
        return best_strategy or 'go-core'
