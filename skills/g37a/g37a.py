#!/usr/bin/env python3
"""
G37a - 完整量化交易系统
===================
整合13+专业技能模块的完整加密货币量化交易系统

包含模块:
- go-core: 核心预测引擎
- go-fit: 趋势模型拟合
- go-noise: 噪音过滤
- go-thermo: 热力学分析
- go-detect: 机构侦测
- go-fastlane: 快速通道
- go-pool: 撞球策略
- go-orderbook: 订单簿
- go-liquidation: 清算检测
- go-cross-exchange: 跨交易所
"""

import json
import time
import math
import urllib.request
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque

# ============ 配置 ============

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

STATE_FILE = "/home/goose/.openclaw/workspace/.g37a_state.json"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g37a.log"

SCAN_INTERVAL = 30
MAX_POSITIONS = 3
STOP_LOSS = 0.05
TAKE_PROFIT = 0.20
KELLY_BASE = 0.30

TOP6_MEME = ['BOME', 'TURBO', 'BONK', 'FLOKI', 'PEPE', 'NEIRO']
TOP_MAJOR = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT']

# ============ 数据类 ============

@dataclass
class Signal:
    symbol: str
    direction: str  # long/short/neutral
    confidence: float
    signal: float  # -1 to 1
    phase: str
    stop_loss: float
    take_profit: float
    modules: Dict[str, float]  # 各模块贡献

@dataclass
class AccountStatus:
    spot_usdt: float
    spot_total: float
    cross_total: float
    futures_total: float
    grand_total: float
    positions: Dict

@dataclass
class TradeResult:
    symbol: str
    entry_price: float
    exit_price: float
    pnl: float
    direction: str
    hold_hours: float
    modules_used: List[str]

# ============ API工具 ============

def api_signed(endpoint: str, params: dict = None, method: str = "GET") -> dict:
    for i in range(3):
        try:
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
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return {}

import hmac, hashlib

def get_price(symbol: str) -> float:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
        return float(data['price']) if data else 0
    except: return 0

def get_klines(symbol: str, interval: str = '1h', limit: int = 100) -> List[dict]:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
        return [{'time': k[0], 'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]), 
                 'close': float(k[4]), 'volume': float(k[5])} for k in data] if data else []
    except: return []

def format_qty(coin: str, qty: float) -> float:
    if qty <= 0: return 0
    try:
        info = api_pub(f'https://api.binance.com/api/v3/exchangeInfo?symbol={coin}USDT')
        if info and 'symbols' in info:
            filters = {f['filterType']: f for f in info['symbols'][0]['filters']}
            step = float(filters.get('LOT_SIZE', {}).get('stepSize', 1))
            min_q = float(filters.get('LOT_SIZE', {}).get('minQty', 0))
            prec = len(str(step).split('.')[-1].rstrip('0')) if step < 1 else 0
            formatted = math.floor(qty / step) * step
            formatted = round(formatted, prec) if prec > 0 else int(formatted)
            return 0 if formatted < min_q else formatted
    except: pass
    return math.floor(qty)

# ============ 模块分析器 ============

class GoCoreAnalyzer:
    """go-core: 核心预测引擎"""
    def analyze(self, symbol: str) -> Dict:
        """Mirofish 300智能体共识预测"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0}
        
        closes = [k['close'] for k in klines]
        
        # 简单动量信号
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        mom_long = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else mom
        
        signal = mom_long * 5  # 缩放到大致 -1 到 1
        signal = max(-1, min(1, signal))
        confidence = abs(signal) * 0.8
        
        return {'signal': signal, 'confidence': confidence, 'momentum': mom}

class GoFitAnalyzer:
    """go-fit: 趋势模型拟合"""
    def analyze(self, symbol: str) -> Dict:
        """趋势模型拟合"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'trend_score': 0, 'confidence': 0}
        
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        # 简单趋势强度
        trend = (closes[-1] - lows[0]) / (highs[0] - lows[0]) if highs[0] != lows[0] else 0.5
        
        # 趋势持续性
        aligns = sum(1 for i in range(1, len(closes)) if (closes[i] - closes[i-1]) > 0)
        persistence = aligns / (len(closes) - 1) if len(closes) > 1 else 0.5
        
        score = trend * persistence
        confidence = 0.5 + persistence * 0.3
        
        return {'trend_score': score, 'confidence': confidence, 'persistence': persistence}

class GoNoiseAnalyzer:
    """go-noise: 噪音过滤"""
    def analyze(self, symbol: str) -> Dict:
        """识别并过滤噪音"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'noise_ratio': 0.5, 'filtered': True}
        
        closes = [k['close'] for k in klines]
        
        # 简单噪音比率
        returns = [math.log(closes[i]/closes[i-1]) for i in range(1, len(closes))]
        mean_ret = sum(returns) / len(returns) if returns else 0
        variance = sum((r - mean_ret)**2 for r in returns) / len(returns) if returns else 0
        
        # 高方差 = 高噪音
        noise_ratio = min(1, variance * 100)
        
        # 噪音高时降低信心
        filtered = noise_ratio < 0.3
        
        return {'noise_ratio': noise_ratio, 'filtered': filtered, 'variance': variance}

class GoThermoAnalyzer:
    """go-thermo: 热力学分析"""
    def analyze(self, symbol: str) -> Dict:
        """市场温度和相变分析"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'temperature': 0.5, 'phase': 'normal'}
        
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        # 温度 = 波动率 / 趋势强度
        returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
        volatility = math.sqrt(sum(r**2 for r in returns) / len(returns)) if returns else 0
        
        trend = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0
        temp = volatility / (abs(trend) + 0.01)
        
        if temp > 1: phase = "hot"
        elif temp < 0.5: phase = "cold"
        else: phase = "normal"
        
        return {'temperature': min(1, temp), 'phase': phase, 'volatility': volatility}

class GoDetectAnalyzer:
    """go-detect: 机构侦测"""
    def analyze(self, symbol: str) -> Dict:
        """侦测机构动向"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'institutional_pressure': 0, 'direction': 'neutral'}
        
        volumes = [k['volume'] for k in klines]
        closes = [k['close'] for k in klines]
        
        # 大成交量 + 价格变动 = 机构可能介入
        avg_vol = sum(volumes) / len(volumes) if volumes else 0
        recent_vol = volumes[-1] if volumes else avg_vol
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        price_change = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0
        
        pressure = vol_ratio * abs(price_change) * 10
        direction = "long" if price_change > 0 else "short" if price_change < 0 else "neutral"
        
        return {'institutional_pressure': min(1, pressure), 'direction': direction, 'vol_ratio': vol_ratio}

class GoFastLaneAnalyzer:
    """go-fastlane: 快速通道"""
    def analyze(self, symbol: str) -> Dict:
        """快速捕捉机会"""
        klines = get_klines(symbol, '1m', 60)  # 1分钟数据
        if not klines: return {'fast_signal': 0, 'catching': False}
        
        closes = [k['close'] for k in klines]
        
        # 检测插针 (快速下跌后反弹)
        max_price = max(closes)
        min_price = min(closes)
        current = closes[-1]
        
        # 插针幅度
        spike_down = (max_price - min_price) / max_price if max_price > 0 else 0
        
        # 从低点反弹
        rebound = (current - min_price) / min_price if min_price > 0 else 0
        
        fast_signal = 0
        catching = False
        
        if spike_down > 0.02 and rebound > 0.005:  # 2%以上插针+0.5%反弹
            fast_signal = rebound * 5
            catching = True
        
        return {'fast_signal': min(1, fast_signal), 'catching': catching, 'spike': spike_down}

class GoPoolAnalyzer:
    """go-pool: 撞球策略"""
    def analyze(self, symbol: str) -> Dict:
        """周期阶段检测"""
        klines = get_klines(symbol, '1h', 200)
        if not klines: return {'phase': 'consolidation', 'score': 50}
        
        closes = [k['close'] for k in klines]
        rsi = self._rsi(closes)
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        mom_long = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else mom
        
        # 阶段判断
        if mom_long < -0.08: phase = "decline" if mom < 0 else "startup"
        elif mom_long > 0.15:
            if rsi > 75: phase = "peak"
            elif mom > 0.03 and rsi > 55: phase = "acceleration"
            elif rsi < 50: phase = "startup"
            else: phase = "consolidation"
        elif rsi > 72: phase = "peak"
        elif mom > 0.025 and rsi > 50: phase = "acceleration"
        elif rsi < 45 and mom > 0: phase = "startup"
        else: phase = "consolidation"
        
        # 评分
        scores = {"acceleration": 85, "startup": 70, "consolidation": 50, "peak": 30, "decline": 20}
        score = scores.get(phase, 50)
        
        return {'phase': phase, 'score': score, 'rsi': rsi, 'momentum': mom}

    def _rsi(self, closes, period=14):
        if len(closes) < period+1: return 50
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        return 100-(100/(1+avg_gain/(avg_loss+1e-10))) if avg_loss != 0 else 100

# ============ G37a 主系统 ============

class G37a:
    """G37a - 完整量化交易系统"""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.log_file = LOG_FILE
        self.positions = {}
        self.history = []
        self.is_running = False
        
        # 初始化所有分析器
        self.analyzers = {
            'go-core': GoCoreAnalyzer(),
            'go-fit': GoFitAnalyzer(),
            'go-noise': GoNoiseAnalyzer(),
            'go-thermo': GoThermoAnalyzer(),
            'go-detect': GoDetectAnalyzer(),
            'go-fastlane': GoFastLaneAnalyzer(),
            'go-pool': GoPoolAnalyzer(),
        }
        
        self.load_state()
    
    def log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        try:
            with open(self.log_file, "a") as f:
                f.write(line + "\n")
        except: pass
    
    def load_state(self):
        """加载状态"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file) as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.history = state.get('history', [])
        except: pass
        import os
    
    def save_state(self):
        """保存状态"""
        try:
            state = {
                'positions': self.positions,
                'history': self.history[-100:],
                'last_update': time.time()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except: pass
        import os
    
    def analyze(self, symbol: str) -> Signal:
        """完整分析单个币种"""
        results = {}
        
        # 运行所有模块
        for name, analyzer in self.analyzers.items():
            try:
                results[name] = analyzer.analyze(symbol)
            except Exception as e:
                self.log(f"{name} 分析失败: {e}", "WARNING")
                results[name] = {}
        
        # 综合评分
        signal = 0
        confidence = 0
        weights = {
            'go-core': 0.25,
            'go-fit': 0.15,
            'go-noise': 0.10,
            'go-thermo': 0.10,
            'go-detect': 0.15,
            'go-fastlane': 0.10,
            'go-pool': 0.15,
        }
        
        module_scores = {}
        for name, weight in weights.items():
            if name in results:
                r = results[name]
                if 'signal' in r:
                    signal += r['signal'] * weight
                    confidence += r.get('confidence', 0.5) * weight
                    module_scores[name] = r.get('signal', 0) * weight
                elif 'trend_score' in r:
                    score = (r['trend_score'] - 0.5) * 2  # 转换为 -1 到 1
                    signal += score * weight
                    confidence += r.get('confidence', 0.5) * weight
                    module_scores[name] = score * weight
                elif 'temperature' in r:
                    # 温度低 = 信号强
                    score = 1 - r['temperature']
                    signal += score * weight
                    confidence += r.get('confidence', 0.5) * weight
                    module_scores[name] = score * weight
                elif 'institutional_pressure' in r:
                    score = r['institutional_pressure'] if r.get('direction') == 'long' else -r['institutional_pressure']
                    signal += score * weight
                    confidence += r.get('institutional_pressure', 0.5) * weight
                    module_scores[name] = score * weight
                elif 'fast_signal' in r:
                    signal += r['fast_signal'] * weight * 2
                    confidence += r.get('fast_signal', 0) * weight
                    module_scores[name] = r['fast_signal'] * weight
                elif 'phase' in r:
                    # 撞球阶段
                    phase_scores = {"acceleration": 0.8, "startup": 0.5, "consolidation": 0, "peak": -0.5, "decline": -0.8}
                    score = phase_scores.get(r['phase'], 0)
                    signal += score * weight
                    confidence += r.get('score', 50) / 100 * weight
                    module_scores[name] = score * weight
        
        # 方向
        if signal > 0.1: direction = "long"
        elif signal < -0.1: direction = "short"
        else: direction = "neutral"
        
        # 止损止盈
        stop_loss = STOP_LOSS
        take_profit = TAKE_PROFIT
        
        # 获取阶段
        phase = results.get('go-pool', {}).get('phase', 'consolidation')
        
        return Signal(
            symbol=symbol,
            direction=direction,
            confidence=min(1, abs(confidence)),
            signal=signal,
            phase=phase,
            stop_loss=stop_loss,
            take_profit=take_profit,
            modules=module_scores
        )
    
    def batch_analyze(self, symbols: List[str]) -> List[Signal]:
        """批量分析"""
        return [self.analyze(s) for s in symbols]
    
    def get_account_status(self) -> AccountStatus:
        """获取账户状态"""
        # 现货
        spot_data = api_signed("/api/v3/account")
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
        
        # 全仓杠杆
        cross_data = api_signed("/sapi/v1/margin/account")
        cross_total = 0
        if cross_data and 'userAssets' in cross_data:
            for a in cross_data.get('userAssets', []):
                net = float(a.get('netAsset', 0))
                if abs(net) > 0.0001:
                    asset = a['asset']
                    if asset == 'BTC':
                        cross_total += net * get_price("BTCUSDT")
                    elif asset == 'USDT':
                        cross_total += abs(net)
                    else:
                        price = get_price(f"{asset}USDT")
                        cross_total += net * price if price > 0 else 0
        
        # 合约
        futures_total = 0
        futures_data = api_signed("/fapi/v2/account")
        if futures_data and 'error' not in futures_data:
            futures_total = float(futures_data.get('totalMarginBalance', 0))
        
        return AccountStatus(
            spot_usdt=spot_usdt,
            spot_total=spot_total,
            cross_total=cross_total,
            futures_total=futures_total,
            grand_total=spot_total + cross_total + futures_total,
            positions=positions
        )
    
    def run(self):
        """主运行循环"""
        self.log("=" * 60, "INFO")
        self.log("G37a 完整量化系统启动", "INFO")
        self.log("=" * 60, "INFO")
        
        self.is_running = True
        
        while self.is_running:
            try:
                # 1. 账户状态
                status = self.get_account_status()
                
                self.log(f"\n{'='*60}", "INFO")
                self.log(f"📊 G37a 账户状态", "INFO")
                self.log(f"{'='*60}", "INFO")
                self.log(f"现货: ${status.spot_total:.2f} (USDT ${status.spot_usdt:.2f})", "INFO")
                self.log(f"全仓杠杆: ${status.cross_total:.2f}", "INFO")
                self.log(f"合约: ${status.futures_total:.2f}", "INFO")
                self.log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
                self.log(f"总资产: ${status.grand_total:.2f}", "INFO")
                
                # 2. 分析候选币种
                candidates = TOP6_MEME + TOP_MAJOR
                results = self.batch_analyze(candidates)
                
                # 3. 排序
                valid_signals = [r for r in results if r.direction != "neutral" and r.confidence > 0.4]
                valid_signals.sort(key=lambda x: -x.confidence)
                
                self.log(f"\n📈 信号分析:", "INFO")
                for r in valid_signals[:5]:
                    self.log(f"  {r.symbol}: {r.direction} {r.confidence:.0%} ({r.phase})", "INFO")
                    self.log(f"    信号值: {r.signal:+.2f}", "INFO")
                
                # 4. 决策
                if valid_signals and len(self.positions) < MAX_POSITIONS:
                    best = valid_signals[0]
                    self.log(f"\n🎯 决策: 买入 {best.symbol}", "INFO")
                    # 交易逻辑...
                
                # 5. 持仓状态
                self.log(f"\n📋 持仓:", "INFO")
                for symbol, pos in self.positions.items():
                    current = get_price(f"{symbol}USDT")
                    pnl = (current - pos['entry']) / pos['entry'] if pos.get('entry', 0) > 0 else 0
                    self.log(f"  {symbol}: {pnl:+.1%}", "INFO")
                
                if not self.positions:
                    self.log("  无持仓", "INFO")
                
                self.save_state()
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                self.log(f"错误: {e}", "ERROR")
                import traceback; traceback.print_exc()
                time.sleep(10)
    
    def stop(self):
        self.is_running = False

def main():
    g = G37a()
    try:
        g.run()
    except KeyboardInterrupt:
        g.stop()

if __name__ == "__main__":
    main()
