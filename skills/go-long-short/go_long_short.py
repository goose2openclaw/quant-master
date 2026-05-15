#!/usr/bin/env python3
"""
go-long-short - 多空双向交易技能
===================
支持做多、做空和多空切换的综合交易策略
"""

import json
import time
import math
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import deque

# ============ 配置 ============

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

LONG_THRESHOLD = 0.6
SHORT_THRESHOLD = -0.6
SWITCH_COOLDOWN = 300
MAX_SHORT_POSITIONS = 2
SHORT_STOP_LOSS = 0.04
LONG_STOP_LOSS = 0.05
MARGIN_RATIO = 2

STATE_FILE = "/home/goose/.openclaw/workspace/.go_long_short_state.json"

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
        data = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
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
class DirectionSignal:
    symbol: str
    direction: str        # long/short/neutral
    confidence: float    # 0-1
    signal: float        # -1 to 1
    reason: str
    sources: Dict[str, float]  # 各信号来源贡献
    entry_price: float
    stop_loss: float
    take_profit: float
    leverage: int

@dataclass
class SwitchSignal:
    should_switch: bool
    from_direction: str
    to_direction: str
    reason: str
    confidence: float

@dataclass
class Position:
    symbol: str
    direction: str       # long/short
    entry_price: float
    current_price: float
    quantity: float
    pnl: float
    leverage: int
    open_time: float

# ============ go系列组件连接 ============

class GoComponents:
    """go系列组件连接器"""
    
    @staticmethod
    def get_core_signal(symbol: str) -> Dict:
        """go-core 核心预测"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5}
        
        closes = [k['close'] for k in klines]
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        mom_long = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else mom
        
        signal = mom_long * 5
        signal = max(-1, min(1, signal))
        confidence = abs(signal) * 0.8
        
        return {'signal': signal, 'confidence': confidence}
    
    @staticmethod
    def get_thermo_signal(symbol: str) -> Dict:
        """go-thermo 热力学"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'temperature': 0.5, 'phase': 'normal'}
        
        closes = [k['close'] for k in klines]
        returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
        volatility = math.sqrt(sum(r**2 for r in returns) / len(returns)) if returns else 0
        trend = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0
        temp = volatility / (abs(trend) + 0.01)
        
        return {
            'temperature': min(1, temp),
            'phase': 'hot' if temp > 1 else 'cold' if temp < 0.5 else 'normal'
        }
    
    @staticmethod
    def get_detect_signal(symbol: str) -> Dict:
        """go-detect 机构侦测"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'pressure': 0, 'direction': 'neutral'}
        
        volumes = [k['volume'] for k in klines]
        closes = [k['close'] for k in klines]
        
        avg_vol = sum(volumes) / len(volumes) if volumes else 0
        recent_vol = volumes[-1] if volumes else avg_vol
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        price_change = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0
        
        pressure = vol_ratio * abs(price_change) * 10
        direction = "long" if price_change > 0 else "short" if price_change < 0 else "neutral"
        
        return {'pressure': min(1, pressure), 'direction': direction}
    
    @staticmethod
    def get_pool_phase(symbol: str) -> int:
        """go-pool 撞球阶段"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return 0
        
        closes = [k['close'] for k in klines]
        rsi = GoComponents._rsi(closes)
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        mom_long = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else mom
        
        if mom_long < -0.08: phase = 4  # 衰退
        elif mom_long > 0.15:
            if rsi > 75: phase = 3  # 高峰
            elif mom > 0.03 and rsi > 55: phase = 2  # 加速
            else: phase = 1  # 启动
        elif rsi > 72: phase = 3
        elif mom > 0.025 and rsi > 50: phase = 2
        elif rsi < 45 and mom > 0: phase = 1
        else: phase = 0  # 盘整
        
        return phase
    
    @staticmethod
    def get_rotate_signal(symbol: str) -> Dict:
        """go-rotate 轮动信号"""
        klines = get_klines(symbol, '5m', 100)
        if not klines: return {'action': 'hold', 'confidence': 0.5}
        
        closes = [k['close'] for k in klines]
        current_price = closes[-1]
        mean_price = sum(closes) / len(closes)
        
        # 简单z-score
        variance = sum((x - mean_price) ** 2 for x in closes) / len(closes)
        std_price = math.sqrt(variance)
        zscore = (current_price - mean_price) / std_price if std_price > 0 else 0
        
        rsi = GoComponents._rsi(closes)
        
        if zscore < -1.5 or rsi < 35:
            return {'action': 'buy', 'confidence': min(1, abs(zscore) / 2)}
        elif zscore > 1.5 or rsi > 65:
            return {'action': 'sell', 'confidence': min(1, zscore / 2)}
        
        return {'action': 'hold', 'confidence': 0.5}
    
    @staticmethod
    def _rsi(closes, period=14):
        if len(closes) < period+1: return 50
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        return 100-(100/(1+avg_gain/(avg_loss+1e-10))) if avg_loss != 0 else 100

# ============ 多空策略 ============

class LongShortStrategy:
    """多空双向交易策略"""
    
    def __init__(self, pool_strategy=None, rotate_strategy=None, asset_manager=None):
        self.pool = pool_strategy
        self.rotate = rotate_strategy
        self.asset = asset_manager
        
        self.positions = {}  # symbol -> Position
        self.last_switch = {}  # symbol -> timestamp
        self.signal_history = deque(maxlen=100)
        
        self.load_state()
    
    def load_state(self):
        """加载状态"""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE) as f:
                    state = json.load(f)
                    self.positions = {k: Position(**v) for k, v in state.get('positions', {}).items()}
                    self.last_switch = state.get('last_switch', {})
        except: pass
    
    def save_state(self):
        """保存状态"""
        try:
            state = {
                'positions': {k: asdict(v) for k, v in self.positions.items()},
                'last_switch': self.last_switch,
                'timestamp': time.time()
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f)
        except: pass
    
    def get_signal(self, symbol: str) -> DirectionSignal:
        """获取多空信号"""
        # 获取各组件信号
        core = GoComponents.get_core_signal(symbol)
        thermo = GoComponents.get_thermo_signal(symbol)
        detect = GoComponents.get_detect_signal(symbol)
        pool_phase = GoComponents.get_pool_phase(symbol)
        rotate = GoComponents.get_rotate_signal(symbol)
        
        # 综合评分
        weights = {
            'core': 0.25,
            'thermo': 0.15,
            'detect': 0.20,
            'pool': 0.20,
            'rotate': 0.20
        }
        
        signals = {
            'core': core['signal'],
            'thermo': 1 - thermo['temperature'] if thermo['phase'] == 'cold' else -thermo['temperature'],
            'detect': 0.5 if detect['direction'] == 'long' else -0.5 if detect['direction'] == 'short' else 0,
            'pool': self._pool_phase_to_signal(pool_phase),
            'rotate': 0.5 if rotate['action'] == 'buy' else -0.5 if rotate['action'] == 'sell' else 0
        }
        
        # 加权综合
        combined = sum(signals[k] * weights[k] for k in weights)
        
        # 方向判断
        if combined > LONG_THRESHOLD:
            direction = 'long'
        elif combined < SHORT_THRESHOLD:
            direction = 'short'
        else:
            direction = 'neutral'
        
        # 信心度
        confidence = min(1, abs(combined))
        
        # 止损止盈
        current_price = get_price(f"{symbol}USDT")
        if direction == 'long':
            stop_loss = current_price * (1 - LONG_STOP_LOSS)
            take_profit = current_price * (1 + LONG_STOP_LOSS * 4)
        elif direction == 'short':
            stop_loss = current_price * (1 + SHORT_STOP_LOSS)
            take_profit = current_price * (1 - SHORT_STOP_LOSS * 4)
        else:
            stop_loss = 0
            take_profit = 0
        
        # 信号来源
        sources = {k: signals[k] * weights[k] for k in weights}
        
        return DirectionSignal(
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            signal=combined,
            reason=self._generate_reason(direction, sources, pool_phase, thermo),
            sources=sources,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            leverage=MARGIN_RATIO if direction != 'neutral' else 1
        )
    
    def _pool_phase_to_signal(self, phase: int) -> float:
        """撞球阶段转信号"""
        phase_signals = {
            0: 0,    # 盘整
            1: 0.5,  # 启动
            2: 0.8,  # 加速
            3: -0.8, # 高峰
            4: -0.5  # 衰退
        }
        return phase_signals.get(phase, 0)
    
    def _generate_reason(self, direction: str, sources: Dict, pool_phase: int, thermo: Dict) -> str:
        """生成信号原因"""
        reasons = []
        
        if direction == 'long':
            if sources['core'] > 0.1: reasons.append("核心看涨")
            if sources['pool'] > 0.3: reasons.append(f"撞球{pool_phase}阶段")
            if sources['rotate'] > 0.1: reasons.append("轮动买入")
            if thermo['phase'] == 'cold': reasons.append("市场冷却")
        elif direction == 'short':
            if sources['core'] < -0.1: reasons.append("核心看跌")
            if sources['pool'] < -0.3: reasons.append(f"撞球{pool_phase}阶段")
            if sources['rotate'] < -0.1: reasons.append("轮动卖出")
            if thermo['phase'] == 'hot': reasons.append("市场过热")
        else:
            reasons.append("等待信号")
        
        return "; ".join(reasons) if reasons else "无明显信号"
    
    def get_switch_signal(self, symbol: str) -> SwitchSignal:
        """获取切换信号"""
        if symbol not in self.positions:
            return SwitchSignal(False, 'none', 'none', '无持仓', 0)
        
        current_pos = self.positions[symbol]
        current_dir = current_pos.direction
        
        # 检查冷却
        if symbol in self.last_switch:
            if time.time() - self.last_switch[symbol] < SWITCH_COOLDOWN:
                return SwitchSignal(False, current_dir, current_dir, '冷却中', 0)
        
        # 获取新信号
        new_signal = self.get_signal(symbol)
        
        # 判断是否需要切换
        should_switch = False
        to_direction = current_dir
        
        if current_dir == 'long' and new_signal.direction == 'short':
            should_switch = True
            to_direction = 'short'
        elif current_dir == 'short' and new_signal.direction == 'long':
            should_switch = True
            to_direction = 'long'
        
        if should_switch:
            self.last_switch[symbol] = time.time()
        
        return SwitchSignal(
            should_switch=should_switch,
            from_direction=current_dir,
            to_direction=to_direction,
            reason=new_signal.reason,
            confidence=new_signal.confidence
        )
    
    def open_long(self, symbol: str, size: float = 0.3) -> Dict:
        """开多仓"""
        current_price = get_price(f"{symbol}USDT")
        
        position = Position(
            symbol=symbol,
            direction='long',
            entry_price=current_price,
            current_price=current_price,
            quantity=size,
            pnl=0,
            leverage=MARGIN_RATIO,
            open_time=time.time()
        )
        
        self.positions[symbol] = position
        self.save_state()
        
        return {
            'action': 'open_long',
            'symbol': symbol,
            'entry': current_price,
            'size': size,
            'leverage': MARGIN_RATIO
        }
    
    def open_short(self, symbol: str, size: float = 0.3) -> Dict:
        """开空仓"""
        # 检查空仓数量
        short_count = sum(1 for p in self.positions.values() if p.direction == 'short')
        if short_count >= MAX_SHORT_POSITIONS:
            return {'action': 'rejected', 'reason': 'max_short_positions'}
        
        current_price = get_price(f"{symbol}USDT")
        
        position = Position(
            symbol=symbol,
            direction='short',
            entry_price=current_price,
            current_price=current_price,
            quantity=size,
            pnl=0,
            leverage=MARGIN_RATIO,
            open_time=time.time()
        )
        
        self.positions[symbol] = position
        self.save_state()
        
        return {
            'action': 'open_short',
            'symbol': symbol,
            'entry': current_price,
            'size': size,
            'leverage': MARGIN_RATIO
        }
    
    def close_position(self, symbol: str) -> Dict:
        """平仓"""
        if symbol not in self.positions:
            return {'action': 'none', 'reason': 'no_position'}
        
        pos = self.positions[symbol]
        current_price = get_price(f"{symbol}USDT")
        
        if pos.direction == 'long':
            pnl = (current_price - pos.entry_price) / pos.entry_price
        else:
            pnl = (pos.entry_price - current_price) / pos.entry_price
        
        del self.positions[symbol]
        self.save_state()
        
        return {
            'action': 'close',
            'symbol': symbol,
            'entry': pos.entry_price,
            'exit': current_price,
            'pnl': pnl
        }
    
    def switch_direction(self, symbol: str) -> Dict:
        """多空切换"""
        if symbol not in self.positions:
            return {'action': 'none', 'reason': 'no_position'}
        
        pos = self.positions[symbol]
        current_dir = pos.direction
        
        # 平仓
        close_result = self.close_position(symbol)
        
        # 反向开仓
        if current_dir == 'long':
            open_result = self.open_short(symbol, pos.quantity)
        else:
            open_result = self.open_long(symbol, pos.quantity)
        
        return {
            'action': 'switch',
            'from': current_dir,
            'to': 'short' if current_dir == 'long' else 'long',
            'close': close_result,
            'open': open_result
        }
    
    def update_positions(self):
        """更新持仓状态"""
        for symbol, pos in list(self.positions.items()):
            current_price = get_price(f"{symbol}USDT")
            pos.current_price = current_price
            
            if pos.direction == 'long':
                pos.pnl = (current_price - pos.entry_price) / pos.entry_price
            else:
                pos.pnl = (pos.entry_price - current_price) / pos.entry_price
        
        self.save_state()
    
    def get_positions_summary(self) -> Dict:
        """获取持仓汇总"""
        self.update_positions()
        
        total_pnl = sum(p.pnl for p in self.positions.values())
        longs = [p for p in self.positions.values() if p.direction == 'long']
        shorts = [p for p in self.positions.values() if p.direction == 'short']
        
        return {
            'total': len(self.positions),
            'longs': len(longs),
            'shorts': len(shorts),
            'total_pnl': total_pnl,
            'positions': {symbol: asdict(pos) for symbol, pos in self.positions.items()}
        }

def main():
    ls = LongShortStrategy()
    
    print("=== 多空信号测试 ===")
    for symbol in ['BTC', 'ETH', 'PEPE']:
        sig = ls.get_signal(symbol)
        print(f"{sig.symbol}: {sig.direction} {sig.confidence:.0%}")
        print(f"  信号值: {sig.signal:+.2f}")
        print(f"  原因: {sig.reason}")
        print()

if __name__ == "__main__":
    main()

# ============ 高级功能 ============

class AdvancedLongShort(LongShortStrategy):
    """高级多空策略 - 增强版"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_daily_loss = 0.10  # 10%
        self.weekly_loss_limit = 0.20  # 20%
        self.consecutive_losses = 0
        self.last_loss_time = 0
        self.trade_cooldown = 1800  # 30分钟
    
    def get_dynamic_leverage(self, symbol: str) -> int:
        """根据市场波动率动态调整杠杆"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return 2
        
        closes = [k['close'] for k in klines]
        returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
        volatility = sum(abs(r) for r in returns[-20:]) / 20 if returns else 0.01
        
        if volatility < 0.01:
            return 5  # 低波动用高杠杆
        elif volatility < 0.02:
            return 3
        elif volatility < 0.03:
            return 2
        else:
            return 1  # 高波动用低杠杆或不用杠杆
    
    def calculate_position_size(self, symbol: str, risk_percent: float = 0.02) -> float:
        """根据风险百分比计算仓位"""
        account = self.asset.get_account_status() if self.asset else None
        if not account: return 0.1
        
        balance = account.spot_total
        entry = get_price(f"{symbol}USDT")
        stop_loss = entry * (1 - LONG_STOP_LOSS)
        
        risk_amount = balance * risk_percent
        position_size = risk_amount / (entry - stop_loss) if entry > stop_loss else 0
        
        return min(position_size, balance * 0.2 / entry)  # 不超过账户20%
    
    def check_risk_limits(self) -> Tuple[bool, str]:
        """检查风险限制"""
        now = time.time()
        
        # 检查冷却
        if now - self.last_loss_time < self.trade_cooldown:
            return False, "冷却中"
        
        # 检查连续亏损
        if self.consecutive_losses >= 3:
            return False, "连续3次亏损，停止交易"
        
        return True, "正常"
    
    def record_trade_result(self, symbol: str, pnl: float):
        """记录交易结果"""
        if pnl < 0:
            self.consecutive_losses += 1
            self.last_loss_time = time.time()
        else:
            self.consecutive_losses = 0
    
    def get_correlation_matrix(self, symbols: List[str]) -> Dict:
        """计算币种相关性矩阵"""
        try:
            import numpy as np
            import pandas as pd
            
            prices = {}
            for symbol in symbols:
                klines = get_klines(symbol, '1d', 30)
                closes = [k['close'] for k in klines]
                if len(closes) >= 20:
                    prices[symbol] = closes
            
            if len(prices) < 2:
                return {}
            
            df = pd.DataFrame(prices)
            corr = df.corr()
            return corr.to_dict()
        except:
            return {}
    
    def find_low_correlation_pairs(self, symbols: List[str]) -> List[Tuple[str, str]]:
        """寻找低相关性币对用于对冲"""
        corr_matrix = self.get_correlation_matrix(symbols)
        pairs = []
        
        for s1 in symbols:
            for s2 in symbols:
                if s1 != s2:
                    corr = corr_matrix.get(s1, {}).get(s2, 0)
                    if corr < 0.3:  # 低相关性
                        pairs.append((s1, s2, corr))
        
        pairs.sort(key=lambda x: x[2])
        return [(p[0], p[1]) for p in pairs[:5]]
    
    def execute_with_risk_management(self, symbol: str, direction: str, size: float = None) -> Dict:
        """带风险管理的执行"""
        # 检查风险限制
        can_trade, reason = self.check_risk_limits()
        if not can_trade:
            return {'action': 'rejected', 'reason': reason}
        
        # 计算仓位
        if size is None:
            size = self.calculate_position_size(symbol)
        
        # 执行交易
        if direction == 'long':
            result = self.open_long(symbol, size)
        else:
            result = self.open_short(symbol, size)
        
        return result

# ============ 对冲模式 ============

class HedgeMode:
    """对冲模式"""
    
    def __init__(self, long_short: LongShortStrategy):
        self.ls = long_short
        self.hedge_positions = {}
    
    def open_hedge(self, symbol: str, long_size: float, hedge_ratio: float = 0.5) -> Dict:
        """开对冲仓"""
        # 开多仓
        long_result = self.ls.open_long(symbol, long_size)
        
        # 开空仓对冲
        short_size = long_size * hedge_ratio
        short_result = self.ls.open_short(symbol, short_size)
        
        self.hedge_positions[symbol] = {
            'long': long_result,
            'short': short_result,
            'ratio': hedge_ratio
        }
        
        return {
            'action': 'hedge_open',
            'symbol': symbol,
            'long': long_result,
            'short': short_result,
            'hedge_ratio': hedge_ratio
        }
    
    def close_hedge(self, symbol: str) -> Dict:
        """平对冲仓"""
        if symbol not in self.hedge_positions:
            return {'action': 'none', 'reason': 'no_hedge'}
        
        long_result = self.ls.close_position(symbol)
        short_result = self.ls.close_position(symbol)
        
        hedge_pnl = long_result.get('pnl', 0) + short_result.get('pnl', 0)
        
        del self.hedge_positions[symbol]
        
        return {
            'action': 'hedge_close',
            'symbol': symbol,
            'long_pnl': long_result.get('pnl', 0),
            'short_pnl': short_result.get('pnl', 0),
            'total_pnl': hedge_pnl
        }
    
    def rebalance_hedge(self, symbol: str, new_ratio: float = 0.5) -> Dict:
        """重新平衡对冲"""
        if symbol not in self.hedge_positions:
            return self.open_hedge(symbol, 0.1, new_ratio)
        
        current_ratio = self.hedge_positions[symbol]['ratio']
        hedge = self.hedge_positions[symbol]
        
        if abs(new_ratio - current_ratio) < 0.1:
            return {'action': 'skip', 'reason': 'ratio_similar'}
        
        # 调整空头仓位
        long_size = 0.1  # 固定多头
        target_short = long_size * new_ratio
        current_short = long_size * current_ratio
        
        if target_short > current_short:
            # 增加空头
            self.ls.open_short(symbol, target_short - current_short)
        else:
            # 减少空头
            self.ls.close_position(symbol)
        
        self.hedge_positions[symbol]['ratio'] = new_ratio
        
        return {
            'action': 'rebalanced',
            'symbol': symbol,
            'new_ratio': new_ratio
        }

# ============ 跟踪止损 ============

class TrailingStop:
    """跟踪止损"""
    
    def __init__(self):
        self.highest_prices = {}
        self.lowest_prices = {}
    
    def update(self, symbol: str, direction: str, current_price: float):
        """更新跟踪价格"""
        if direction == 'long':
            if symbol not in self.highest_prices or current_price > self.highest_prices[symbol]:
                self.highest_prices[symbol] = current_price
        else:
            if symbol not in self.lowest_prices or current_price < self.lowest_prices[symbol]:
                self.lowest_prices[symbol] = current_price
    
    def should_stop(self, symbol: str, direction: str, current_price: float, 
                     trailing_percent: float = 0.05) -> bool:
        """判断是否触发跟踪止损"""
        if direction == 'long':
            if symbol not in self.highest_prices:
                return False
            highest = self.highest_prices[symbol]
            drawdown = (highest - current_price) / highest
            return drawdown >= trailing_percent
        else:
            if symbol not in self.lowest_prices:
                return False
            lowest = self.lowest_prices[symbol]
            drawup = (current_price - lowest) / lowest
            return drawup >= trailing_percent
    
    def reset(self, symbol: str):
        """重置跟踪"""
        if symbol in self.highest_prices:
            del self.highest_prices[symbol]
        if symbol in self.lowest_prices:
            del self.lowest_prices[symbol]
