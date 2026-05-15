#!/usr/bin/env python3
"""
go-rotate - 轮动策略技能
===================
板块轮动和币种轮动，与撞球(pool)策略形成互补
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

PROXY = "http://172.29.144.1:7897"

ROTATE_INTERVAL = 10  # 秒
POSITION_SIZE = 0.15   # 15%仓位
STD_THRESHOLD = 1.5    # 标准差阈值
STOP_LOSS = 0.03       # 3%止损
TAKE_PROFIT = 0.06     # 6%止盈
MAX_HOLD_TIME = 1800   # 30分钟
SECTOR_COUNT = 3       # 同时轮动板块数
COIN_PER_SECTOR = 2    # 每个板块币种数

# 板块配置
SECTORS = {
    'mainstream': ['BTC', 'ETH', 'SOL', 'XRP', 'ADA'],
    'defi': ['LINK', 'UNI', 'AAVE', 'MKR', 'CRV'],
    'layer2': ['ARB', 'OP', 'MATIC', 'APT', 'SUI'],
    'meme': ['PEPE', 'BONK', 'DOGE', 'SHIB', 'FLOKI'],
    'gamefi': ['GALA', 'IMX', 'AXS', 'MANA', 'SAND']
}

# 与撞球策略的协同阈值
POOL_PHASE_THRESHOLD = {
    'consolidation': 0,  # 盘整 → 使用轮动
    'startup': 1,        # 启动 → 减少轮动
    'acceleration': 2,   # 加速 → 禁用轮动
    'peak': 3,           # 高峰 → 退出轮动
    'decline': 4         # 衰退 → 启用轮动
}

# ============ API工具 ============

def api_pub(url: str) -> dict:
    try:
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return {}

def get_price(symbol: str) -> float:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT')
        return float(data['price']) if data else 0
    except: return 0

def get_klines(symbol: str, interval: str = '1m', limit: int = 100) -> List[dict]:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}')
        return [{'time': k[0], 'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]),
                 'close': float(k[4]), 'volume': float(k[5])} for k in data] if data else []
    except: return []

# ============ 数据类 ============

@dataclass
class RotationSignal:
    symbol: str
    action: str          # buy/sell/hold
    price: float
    reason: str
    confidence: float     # 0-1
    entry_price: float   # 建议入场价
    stop_loss: float
    take_profit: float
    holding_time: int    # 预计持仓秒数
    sector: str

@dataclass
class SectorRotation:
    sector: str
    coins: List[str]
    rotation_score: float
    direction: str       # in/out/stable

# ============ 统计分析 ============

class Statistics:
    """统计分析工具"""
    
    @staticmethod
    def mean(data: List[float]) -> float:
        return sum(data) / len(data) if data else 0
    
    @staticmethod
    def std(data: List[float]) -> float:
        if len(data) < 2: return 0
        m = Statistics.mean(data)
        variance = sum((x - m) ** 2 for x in data) / (len(data) - 1)
        return math.sqrt(variance)
    
    @staticmethod
    def zscore(value: float, data: List[float]) -> float:
        m = Statistics.mean(data)
        s = Statistics.std(data)
        return (value - m) / s if s > 0 else 0
    
    @staticmethod
    def rsi(closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1: return 50
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        return 100 - (100 / (1 + avg_gain / (avg_loss + 1e-10))) if avg_loss != 0 else 100

# ============ 轮动策略 ============

class RotationStrategy:
    """轮动策略"""
    
    def __init__(self, asset_manager=None):
        self.asset_manager = asset_manager
        self.positions = {}  # 当前持仓
        self.rotation_history = deque(maxlen=100)
        self.last_rotation = {}
        self.rotation_cooldown = 60  # 1分钟冷却
        
        self.load_state()
    
    def load_state(self):
        """加载状态"""
        try:
            state_file = "/home/goose/.openclaw/workspace/.go_rotate_state.json"
            if os.path.exists(state_file):
                with open(state_file) as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.rotation_history = deque(state.get('history', []), maxlen=100)
        except: pass
    
    def save_state(self):
        """保存状态"""
        try:
            state_file = "/home/goose/.openclaw/workspace/.go_rotate_state.json"
            state = {
                'positions': self.positions,
                'history': list(self.rotation_history)
            }
            with open(state_file, 'w') as f:
                json.dump(state, f)
        except: pass
    
    def get_signal(self, symbol: str, interval: str = '5m') -> RotationSignal:
        """获取单个币种轮动信号"""
        klines = get_klines(symbol, interval, 100)
        if not klines: return None
        
        closes = [k['close'] for k in klines]
        current_price = closes[-1]
        
        # 统计分析
        mean_price = Statistics.mean(closes)
        std_price = Statistics.std(closes)
        zscore = Statistics.zscore(current_price, closes)
        rsi = Statistics.rsi(closes)
        
        # 成交量分析
        volumes = [k['volume'] for k in klines]
        avg_volume = Statistics.mean(volumes)
        current_volume = volumes[-1] if volumes else avg_volume
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # 判断信号
        action = 'hold'
        reason = ''
        confidence = 0.5
        
        # 买入信号: 价格低于均值-1.5标准差 或 RSI<35
        if zscore < -STD_THRESHOLD or rsi < 35:
            action = 'buy'
            confidence = min(1, abs(zscore) / 2) if zscore < 0 else (35 - rsi) / 35
            reason = f"Z分数{zscore:.1f}<{-STD_THRESHOLD}" if zscore < -STD_THRESHOLD else f"RSI{rsi:.0f}<35"
        
        # 卖出信号: 价格高于均值+1.5标准差 或 RSI>65
        elif zscore > STD_THRESHOLD or rsi > 65:
            action = 'sell'
            confidence = min(1, zscore / 2) if zscore > 0 else (rsi - 65) / 35
            reason = f"Z分数{zscore:.1f}>{STD_THRESHOLD}" if zscore > STD_THRESHOLD else f"RSI{rsi:.0f}>65"
        
        # 极端信号
        elif rsi < 25 or rsi > 75:
            action = 'extreme'
            confidence = 0.9
            reason = f"RSI极端{rsi:.0f}"
        
        # 计算止损止盈
        if action == 'buy':
            stop_loss = current_price * (1 - STOP_LOSS)
            take_profit = current_price * (1 + TAKE_PROFIT)
        elif action == 'sell':
            stop_loss = current_price * (1 + STOP_LOSS)
            take_profit = current_price * (1 - TAKE_PROFIT)
        else:
            stop_loss = 0
            take_profit = 0
        
        return RotationSignal(
            symbol=symbol,
            action=action,
            price=current_price,
            reason=reason,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            holding_time=MAX_HOLD_TIME,
            sector=self._get_sector(symbol)
        )
    
    def _get_sector(self, symbol: str) -> str:
        """获取币种所属板块"""
        for sector, coins in SECTORS.items():
            if symbol in coins:
                return sector
        return 'unknown'
    
    def get_sector_rotation(self) -> List[SectorRotation]:
        """获取板块轮动列表"""
        sector_scores = []
        
        for sector_name, coins in SECTORS.items():
            # 分析板块内币种
            signals = []
            for coin in coins[:3]:  # 每个板块取前3个
                sig = self.get_signal(coin)
                if sig:
                    signals.append(sig)
            
            if not signals:
                continue
            
            # 计算板块轮动分数
            buy_count = sum(1 for s in signals if s.action == 'buy')
            sell_count = sum(1 for s in signals if s.action == 'sell')
            
            if buy_count > sell_count:
                direction = 'in'
                score = buy_count / len(signals)
            elif sell_count > buy_count:
                direction = 'out'
                score = sell_count / len(signals)
            else:
                direction = 'stable'
                score = 0.5
            
            sector_scores.append(SectorRotation(
                sector=sector_name,
                coins=coins[:COIN_PER_SECTOR],
                rotation_score=score,
                direction=direction
            ))
        
        # 按轮动分数排序
        sector_scores.sort(key=lambda x: x.rotation_score, reverse=True)
        return sector_scores[:SECTOR_COUNT]
    
    def get_rotation_trade(self) -> Optional[Tuple[str, str, float]]:
        """获取轮动交易信号 (symbol, action, price)"""
        sectors = self.get_sector_rotation()
        
        # 找低位板块的币种买入
        for sector in sectors:
            if sector.direction == 'in':
                for coin in sector.coins:
                    sig = self.get_signal(coin)
                    if sig and sig.action == 'buy' and sig.confidence > 0.5:
                        # 检查冷却
                        if coin in self.last_rotation:
                            if time.time() - self.last_rotation[coin] < self.rotation_cooldown:
                                continue
                        return (coin, 'buy', sig.price)
        
        # 找高位板块的币种卖出
        for sector in sectors:
            if sector.direction == 'out':
                for coin in sector.coins:
                    sig = self.get_signal(coin)
                    if sig and sig.action == 'sell' and sig.confidence > 0.5:
                        if coin in self.last_rotation:
                            if time.time() - self.last_rotation[coin] < self.rotation_cooldown:
                                continue
                        return (coin, 'sell', sig.price)
        
        return None
    
    def execute_rotation(self) -> Dict:
        """执行轮动"""
        trade = self.get_rotation_trade()
        if not trade:
            return {'action': 'none', 'reason': 'no_signal'}
        
        symbol, action, price = trade
        
        # 检查资金
        if self.asset_manager:
            positions = self.asset_manager.get_positions()
            if action == 'buy' and symbol in positions:
                return {'action': 'none', 'reason': 'already_holding', 'symbol': symbol}
            
            usdt = self.asset_manager.get_available_usdt()
            position_value = usdt * POSITION_SIZE
            quantity = position_value / price
            
            if action == 'buy' and position_value < 1:
                return {'action': 'none', 'reason': 'insufficient_funds'}
        
        # 记录交易
        self.last_rotation[symbol] = time.time()
        self.rotation_history.append({
            'symbol': symbol,
            'action': action,
            'price': price,
            'time': time.time()
        })
        
        self.save_state()
        
        return {
            'action': action,
            'symbol': symbol,
            'price': price,
            'position_size': POSITION_SIZE,
            'reason': 'rotation_signal'
        }
    
    def should_use_rotation(self, pool_phase: int) -> bool:
        """判断是否应该使用轮动策略"""
        # pool_phase: 0=盘整, 1=启动, 2=加速, 3=高峰, 4=衰退
        if pool_phase == 0 or pool_phase == 4:
            return True  # 盘整或衰退时使用轮动
        elif pool_phase == 1:
            return False  # 启动时不用
        else:
            return False  # 加速/高峰时不用
    
    def get_complementary_signal(self, pool_signal: Dict) -> Optional[Dict]:
        """获取与撞球策略互补的信号"""
        pool_phase = pool_signal.get('phase', 0)
        
        if not self.should_use_rotation(pool_phase):
            return None
        
        trade = self.get_rotation_trade()
        if not trade:
            return None
        
        symbol, action, price = trade
        
        return {
            'source': 'rotation',
            'symbol': symbol,
            'action': action,
            'price': price,
            'pool_phase': pool_phase,
            'confidence': self.get_signal(symbol).confidence if action != 'hold' else 0
        }

# ============ 与撞球策略的协同 ============

class PoolRotateSynergy:
    """撞球与轮动的协同"""
    
    def __init__(self):
        self.rotation = RotationStrategy()
        self.pool_state = {}
    
    def get_combined_signal(self, pool_analysis: Dict) -> List[Dict]:
        """获取撞球+轮动的组合信号"""
        signals = []
        
        # 撞球信号
        if 'pool_signal' in pool_analysis:
            signals.append({
                'source': 'pool',
                'symbol': pool_analysis['symbol'],
                'action': pool_analysis.get('action', 'hold'),
                'confidence': pool_analysis.get('confidence', 0.5),
                'phase': pool_analysis.get('phase', 0)
            })
        
        # 轮动互补信号
        rot_signal = self.rotation.get_complementary_signal(pool_analysis)
        if rot_signal:
            signals.append(rot_signal)
        
        return signals
    
    def decide_action(self, pool_analysis: Dict) -> Dict:
        """决定最终操作"""
        signals = self.get_combined_signal(pool_analysis)
        
        if not signals:
            return {'action': 'hold', 'reason': 'no_signal'}
        
        # 优先级: 轮动 > 撞球
        for sig in signals:
            if sig['source'] == 'rotation' and sig['action'] in ['buy', 'sell']:
                return {
                    'action': sig['action'],
                    'symbol': sig['symbol'],
                    'source': 'rotation',
                    'reason': f"轮动:{sig.get('reason', '')}",
                    'confidence': sig['confidence']
                }
        
        # 如果没有轮动信号，使用撞球信号
        for sig in signals:
            if sig['source'] == 'pool' and sig['action'] in ['buy', 'sell']:
                return {
                    'action': sig['action'],
                    'symbol': sig['symbol'],
                    'source': 'pool',
                    'reason': f"撞球阶段{sig['phase']}",
                    'confidence': sig['confidence']
                }
        
        return {'action': 'hold', 'reason': 'waiting'}

def main():
    rot = RotationStrategy()
    
    # 测试信号
    print("=== 轮动信号测试 ===")
    for sector in ['BTC', 'ETH', 'PEPE', 'BONK']:
        sig = rot.get_signal(sector)
        if sig:
            print(f"{sig.symbol}: {sig.action} @ {sig.price:.4f} ({sig.reason})")
    
    # 测试板块轮动
    print("\n=== 板块轮动 ===")
    sectors = rot.get_sector_rotation()
    for s in sectors:
        print(f"{s.sector}: {s.direction} ({s.rotation_score:.1%})")

if __name__ == "__main__":
    main()
