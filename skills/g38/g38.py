#!/usr/bin/env python3
"""
G38 - 自主优化量化交易系统
=========================
整合 G37a + Top10交易员策略 + 资产管理

特性:
- G37a 所有模块
- 十大交易员策略
- 资产管理器
- 自主优化
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

STATE_FILE = "/home/goose/.openclaw/workspace/.g38_state.json"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g38.log"

SCAN_INTERVAL = 30
STOP_LOSS = 0.05
TAKE_PROFIT = 0.20
KELLY_BASE = 0.30

MAINSTREAM_COINS = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT']
MEME_COINS = ['PEPE', 'BONK', 'SHIB', 'DOGE', 'FLOKI', 'BOME', 'TURBO', 'NEIRO']

# ============ Top10 交易员定义 ============

TRADERS = {
    'Soros': {
        'strategy': 'reflexivity',
        'weight': 0.12,
        'stop_loss': 0.08,
        'take_profit': 0.25,
        'best_for': ['BTC', 'ETH', 'ETF'],
        'score': 0,
        'wins': 0,
        'losses': 0
    },
    'Druckenmiller': {
        'strategy': 'liquidity',
        'weight': 0.10,
        'stop_loss': 0.06,
        'take_profit': 0.20,
        'best_for': ['BTC', 'ETH', 'LINK'],
        'score': 0,
        'wins': 0,
        'losses': 0
    },
    'Kovner': {
        'strategy': 'breakout',
        'weight': 0.08,
        'stop_loss': 0.05,
        'take_profit': 0.18,
        'best_for': ['LINK', 'AAVE', 'UNI'],
        'score': 0,
        'wins': 0,
        'losses': 0
    },
    'Marcus': {
        'strategy': 'trend_following',
        'weight': 0.15,
        'stop_loss': 0.10,
        'take_profit': 0.30,
        'best_for': ['BTC', 'ETH', 'SOL'],
        'score': 0,
        'wins': 0,
        'losses': 0
    },
    'Jones': {
        'strategy': 'ma_system',
        'weight': 0.12,
        'stop_loss': 0.05,
        'take_profit': 0.20,
        'best_for': ['BTC', 'ETH', 'DOGE'],
        'score': 0,
        'wins': 0,
        'losses': 0
    },
    'Dennis': {
        'strategy': 'systematic',
        'weight': 0.08,
        'stop_loss': 0.05,
        'take_profit': 0.15,
        'best_for': ['BTC', 'ETH', 'SOL'],
        'score': 0,
        'wins': 0,
        'losses': 0
    },
    'Schwartz': {
        'strategy': 'candlestick',
        'weight': 0.10,
        'stop_loss': 0.08,
        'take_profit': 0.25,
        'best_for': ['DOGE', 'SHIB', 'PEPE', 'BONK'],
        'score': 0,
        'wins': 0,
        'losses': 0
    },
    'Lipschutz': {
        'strategy': 'trend_trade',
        'weight': 0.08,
        'stop_loss': 0.06,
        'take_profit': 0.22,
        'best_for': ['BTC', 'ETH', 'SOL'],
        'score': 0,
        'wins': 0,
        'losses': 0
    },
    'Livermore': {
        'strategy': 'key_reversal',
        'weight': 0.09,
        'stop_loss': 0.07,
        'take_profit': 0.25,
        'best_for': ['BTC', 'ETH'],
        'score': 0,
        'wins': 0,
        'losses': 0
    },
    'Rogers': {
        'strategy': 'trend_id',
        'weight': 0.08,
        'stop_loss': 0.05,
        'take_profit': 0.20,
        'best_for': ['BTC', 'ETH'],
        'score': 0,
        'wins': 0,
        'losses': 0
    }
}

# ============ 数据类 ============

@dataclass
class G38Signal:
    symbol: str
    direction: str
    confidence: float
    signal: float
    phase: str
    stop_loss: float
    take_profit: float
    top_traders: List[str]
    market_type: str  # trending / ranging
    g37a_signal: float
    trader_signal: float
    asset_signal: float

@dataclass
class AccountStatus:
    spot_usdt: float
    spot_total: float
    cross_total: float
    isolated_total: float
    futures_total: float
    grand_total: float
    positions: Dict

# ============ API工具 ============

def api_signed(endpoint: str, params: dict = None, method: str = "GET") -> dict:
    for i in range(3):
        try:
            import hmac, hashlib
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
        data = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
        return float(data['price']) if data else 0
    except: return 0

def get_klines(symbol: str, interval: str = '1h', limit: int = 100) -> List[dict]:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
        return [{'time': k[0], 'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]),
                 'close': float(k[4]), 'volume': float(k[5])} for k in data] if data else []
    except: return []

# ============ G37a 模块 (简化版) ============

class G37aAnalyzer:
    """G37a 核心分析器"""
    
    def analyze(self, symbol: str) -> Dict:
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'phase': 'consolidation'}
        
        closes = [k['close'] for k in klines]
        
        # 简单动量
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        mom_long = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else mom
        
        # RSI
        rsi = self._rsi(closes)
        
        # 阶段判断
        if abs(mom_long) > 0.15:
            phase = "trend"
        elif rsi > 70 or rsi < 30:
            phase = "momentum"
        else:
            phase = "consolidation"
        
        signal = mom_long * 5
        signal = max(-1, min(1, signal))
        confidence = abs(signal) * 0.8 + 0.2
        
        return {'signal': signal, 'confidence': confidence, 'phase': phase, 'rsi': rsi}
    
    def _rsi(self, closes, period=14):
        if len(closes) < period+1: return 50
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        return 100-(100/(1+avg_gain/(avg_loss+1e-10))) if avg_loss != 0 else 100

# ============ Top10 交易员分析器 ============

class Top10TraderAnalyzer:
    """Top10 交易员策略分析"""
    
    def __init__(self):
        self.traders = {k: v.copy() for k, v in TRADERS.items()}
    
    def analyze(self, symbol: str) -> Dict:
        """分析各交易员对 symbol 的信号"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'trader_signals': {}, 'combined': 0}
        
        closes = [k['close'] for k in klines]
        rsi = self._rsi(closes)
        
        trader_signals = {}
        combined = 0
        total_weight = 0
        
        for name, trader in self.traders.items():
            signal = self._get_trader_signal(name, klines, rsi, symbol)
            trader_signals[name] = signal * trader['weight']
            combined += signal * trader['weight']
            total_weight += trader['weight']
        
        combined = combined / total_weight if total_weight > 0 else 0
        
        return {
            'trader_signals': trader_signals,
            'combined': combined,
            'top_traders': self._get_top_traders(trader_signals)
        }
    
    def _get_trader_signal(self, name: str, klines: List, rsi: float, symbol: str) -> float:
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        # 基础信号
        signal = 0
        
        if name == 'Soros':
            # 反身性: 趋势持续时增强
            mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
            signal = 0.5 if abs(mom) > 0.02 else -0.3
        
        elif name == 'Druckenmiller':
            # 流动性: 大成交量确认
            volumes = [k['volume'] for k in klines]
            avg_vol = sum(volumes) / len(volumes)
            recent_vol = volumes[-1] if volumes else avg_vol
            vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
            signal = 0.6 if vol_ratio > 1.5 else 0.2
        
        elif name == 'Kovner':
            # 突破: 创20日新高/新低
            high_20 = max(closes[-20:]) if len(closes) >= 20 else max(closes)
            low_20 = min(closes[-20:]) if len(closes) >= 20 else min(closes)
            if closes[-1] >= high_20: signal = 0.7
            elif closes[-1] <= low_20: signal = -0.7
            else: signal = 0
        
        elif name == 'Marcus':
            # 趋势跟踪
            mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
            signal = min(1, mom * 10) if mom > 0 else max(-1, mom * 10)
        
        elif name == 'Jones':
            # 均线系统
            ma_short = sum(closes[-10:]) / 10 if len(closes) >= 10 else closes[-1]
            ma_long = sum(closes[-30:]) / 30 if len(closes) >= 30 else ma_short
            if ma_short > ma_long: signal = 0.6
            elif ma_short < ma_long: signal = -0.6
            else: signal = 0
        
        elif name == 'Dennis':
            # 系统化: 唐奇安通道
            high_20 = max(closes[-20:]) if len(closes) >= 20 else max(closes)
            low_20 = min(closes[-20:]) if len(closes) >= 20 else min(closes)
            if closes[-1] > high_20: signal = 0.6
            elif closes[-1] < low_20: signal = -0.6
            else: signal = 0
        
        elif name == 'Schwartz':
            # K线形态: RSI极端
            if rsi < 30: signal = 0.7
            elif rsi > 70: signal = -0.5
            else: signal = 0
        
        elif name == 'Lipschutz':
            # 趋势交易
            mom = (closes[-1] - closes[-10]) / closes[-10] if len(closes) >= 10 else 0
            signal = 0.5 if mom > 0.02 else -0.5
        
        elif name == 'Livermore':
            # 关键转折
            if len(closes) >= 5:
                if closes[-1] > closes[-2] and closes[-2] < closes[-3]: signal = 0.6
                elif closes[-1] < closes[-2] and closes[-2] > closes[-3]: signal = -0.6
                else: signal = 0
            else: signal = 0
        
        elif name == 'Rogers':
            # 趋势识别
            up_count = sum(1 for i in range(1, min(10, len(closes))) if closes[-i] > closes[-i-1])
            signal = (up_count - 5) / 5
        
        return signal
    
    def _get_top_traders(self, signals: Dict) -> List[str]:
        sorted_traders = sorted(signals.items(), key=lambda x: abs(x[1]), reverse=True)
        return [t[0] for t in sorted_traders[:3]]
    
    def _rsi(self, closes, period=14):
        if len(closes) < period+1: return 50
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        return 100-(100/(1+avg_gain/(avg_loss+1e-10))) if avg_loss != 0 else 100
    
    def update_weights(self):
        """自主优化: 根据表现调整权重"""
        for name, trader in self.traders.items():
            if trader['losses'] >= 3:
                # 连续亏损，降低权重
                trader['weight'] *= 0.8
            if trader['wins'] >= 5:
                # 连续盈利，增加权重
                trader['weight'] *= 1.1
            
            # 限制权重范围
            trader['weight'] = max(0.05, min(0.20, trader['weight']))

# ============ 资产管理器 ============

class AssetMonitor:
    """资产管理与自主调换"""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.positions = {}
        self.last_switch = {}
        self.switch_cooldown = 300  # 5分钟冷却
    
    def get_account_status(self) -> AccountStatus:
        """获取四大账户状态"""
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
                    price = get_price(f"{asset}USDT") if asset != 'USDT' else 1
                    cross_total += abs(net) * price
        
        # 逐仓杠杆
        isolated_total = 0
        
        # 合约
        futures_total = 0
        futures_data = api_signed("/fapi/v2/account")
        if futures_data and 'error' not in futures_data:
            futures_total = float(futures_data.get('totalMarginBalance', 0))
        
        grand_total = spot_total + cross_total + isolated_total + futures_total
        
        return AccountStatus(
            spot_usdt=spot_usdt,
            spot_total=spot_total,
            cross_total=cross_total,
            isolated_total=isolated_total,
            futures_total=futures_total,
            grand_total=grand_total,
            positions=positions
        )
    
    def should_switch(self, symbol: str, new_signal: float) -> bool:
        """判断是否应该切换"""
        current = self.positions.get(symbol, {})
        if not current:
            return True  # 无持仓，可以买入
        
        # 检查冷却
        if symbol in self.last_switch:
            if time.time() - self.last_switch[symbol] < self.switch_cooldown:
                return False
        
        # 检查止损/止盈
        entry = current.get('entry', 0)
        current_price = get_price(f"{symbol}USDT")
        if entry > 0:
            pnl = (current_price - entry) / entry
            if pnl < -STOP_LOSS or pnl > TAKE_PROFIT:
                return True
        
        # 信号变强
        old_signal = current.get('signal', 0)
        if abs(new_signal) > abs(old_signal) * 1.2:
            return True
        
        return False
    
    def save_state(self):
        """保存状态"""
        try:
            state = {
                'positions': self.positions,
                'last_switch': self.last_switch,
                'timestamp': time.time()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except: pass
    
    def load_state(self):
        """加载状态"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file) as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.last_switch = state.get('last_switch', {})
        except: pass

# ============ G38 主系统 ============

class G38:
    """G38 自主优化量化交易系统"""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.log_file = LOG_FILE
        self.is_running = False
        
        # 初始化组件
        self.g37a = G37aAnalyzer()
        self.top10 = Top10TraderAnalyzer()
        self.asset = AssetMonitor()
        
        self.asset.load_state()
    
    def log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        try:
            with open(self.log_file, "a") as f:
                f.write(line + "\n")
        except: pass
    
    def analyze(self, symbol: str) -> G38Signal:
        """完整分析"""
        # G37a 分析
        g37a_result = self.g37a.analyze(symbol)
        
        # Top10 交易员分析
        top10_result = self.top10.analyze(symbol)
        
        # 市场类型判断
        market_type = self._detect_market_type(symbol)
        
        # 综合信号
        g37a_weight = 0.4 if market_type == 'trending' else 0.3
        trader_weight = 0.4 if market_type == 'trending' else 0.3
        asset_weight = 0.2
        
        combined_signal = (
            g37a_result['signal'] * g37a_weight +
            top10_result['combined'] * trader_weight +
            g37a_result['signal'] * 0.2  # asset signal 用 g37a 代替
        )
        
        direction = 'long' if combined_signal > 0.1 else 'short' if combined_signal < -0.1 else 'neutral'
        confidence = min(1, abs(combined_signal) * 0.8 + 0.2)
        
        return G38Signal(
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            signal=combined_signal,
            phase=g37a_result['phase'],
            stop_loss=STOP_LOSS,
            take_profit=TAKE_PROFIT,
            top_traders=top10_result['top_traders'],
            market_type=market_type,
            g37a_signal=g37a_result['signal'],
            trader_signal=top10_result['combined'],
            asset_signal=g37a_result['signal']
        )
    
    def _detect_market_type(self, symbol: str) -> str:
        """检测市场类型"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return 'ranging'
        
        closes = [k['close'] for k in klines]
        
        # 计算趋势强度
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        
        # 计算波动率
        returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
        volatility = sum(abs(r) for r in returns[-20:]) / 20 if returns else 0
        
        # 判断市场类型
        if abs(mom) > 0.08 and volatility > 0.02:
            return 'trending'
        elif abs(mom) < 0.03 and volatility < 0.015:
            return 'ranging'
        else:
            return 'mixed'
    
    def batch_analyze(self, symbols: List[str]) -> List[G38Signal]:
        """批量分析"""
        return [self.analyze(s) for s in symbols]
    
    def get_account_status(self) -> AccountStatus:
        """获取账户状态"""
        return self.asset.get_account_status()
    
    def run(self):
        """主运行循环"""
        self.log("=" * 60)
        self.log("G38 自主优化系统启动", "INFO")
        self.log("=" * 60)
        
        self.is_running = True
        
        while self.is_running:
            try:
                # 账户状态
                status = self.get_account_status()
                
                self.log(f"\n{'='*60}")
                self.log(f"📊 G38 账户状态")
                self.log(f"{'='*60}")
                self.log(f"现货: ${status.spot_total:.2f}")
                self.log(f"全仓杠杆: ${status.cross_total:.2f}")
                self.log(f"合约: ${status.futures_total:.2f}")
                self.log(f"总资产: ${status.grand_total:.2f}")
                
                # 分析
                all_symbols = MAINSTREAM_COINS + MEME_COINS
                results = self.batch_analyze(all_symbols)
                
                # 趋势市场信号
                trending = [r for r in results if r.market_type == 'trending' and r.direction != 'neutral']
                trending.sort(key=lambda x: -x.confidence)
                
                # 震荡市场信号
                ranging = [r for r in results if r.market_type == 'ranging' and r.direction != 'neutral']
                ranging.sort(key=lambda x: -x.confidence)
                
                self.log(f"\n📈 趋势市场信号:")
                for r in trending[:3]:
                    self.log(f"  {r.symbol}: {r.direction} {r.confidence:.0%} ({', '.join(r.top_traders)})")
                
                self.log(f"\n📊 震荡市场信号:")
                for r in ranging[:3]:
                    self.log(f"  {r.symbol}: {r.direction} {r.confidence:.0%} ({', '.join(r.top_traders)})")
                
                # 自主优化
                self.top10.update_weights()
                
                self.asset.save_state()
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                self.log(f"错误: {e}", "ERROR")
                import traceback; traceback.print_exc()
                time.sleep(10)
    
    def stop(self):
        self.is_running = False

def main():
    g = G38()
    try:
        g.run()
    except KeyboardInterrupt:
        g.stop()

if __name__ == "__main__":
    main()
