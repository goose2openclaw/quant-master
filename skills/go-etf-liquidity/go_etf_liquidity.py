#!/usr/bin/env python3
"""
go-etf-liquidity - ETF与外部流动性分析技能
===================
追踪ETF资金流向、做市商趋势和外部流动性
"""

import json
import time
import math
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

# ============ 配置 ============

PROXY = "http://172.29.144.1:7897"

ETF_FLOW_THRESHOLD = 10_000_000  # 1000万
MM_INVENTORY_CHANGE = 0.20  # 20%
ORACLE_CONFIDENCE = 0.8
LIQUIDITY_WINDOW = 24  # 小时

# ETF配置 (模拟数据)
ETF_CONFIG = {
    'BTC': {
        'ibit': {'nav': 69500, 'shares': 200_000_000},
        'fbtc': {'nav': 69500, 'shares': 80_000_000},
        'arct': {'nav': 69500, 'shares': 30_000_000}
    },
    'ETH': {
        'ethw': {'nav': 3450, 'shares': 100_000_000},
        'feth': {'nav': 3450, 'shares': 40_000_000}
    }
}

# 预言机配置
ORACLE_SOURCES = {
    'chainlink': {'weight': 0.4, 'active': True},
    'band': {'weight': 0.3, 'active': True},
    'pyth': {'weight': 0.2, 'active': True},
    'api3': {'weight': 0.1, 'active': True}
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

def get_klines(symbol: str, interval: str = '1h', limit: int = 100) -> List[dict]:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}')
        return [{'time': k[0], 'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]),
                 'close': float(k[4]), 'volume': float(k[5])} for k in data] if data else []
    except: return []

def get_orderbook(symbol: str, limit: int = 20) -> Dict:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/depth?symbol={symbol}USDT&limit={limit}')
        if data:
            bids = [[float(p), float(q)] for p, q in data.get('bids', [])]
            asks = [[float(p), float(q)] for p, q in data.get('asks', [])]
            bid_depth = sum(q for _, q in bids)
            ask_depth = sum(q for _, q in asks)
            return {
                'bids': bids,
                'asks': asks,
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'spread': asks[0][0] - bids[0][0] if asks and bids else 0
            }
    except: pass
    return {'bids': [], 'asks': [], 'bid_depth': 0, 'ask_depth': 0, 'spread': 0}

def get_recent_trades(symbol: str, limit: int = 100) -> List[dict]:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/trades?symbol={symbol}USDT&limit={limit}')
        return [{'price': float(t['price']), 'qty': float(t['qty']), 
                 'time': t['time'], 'is_buyer_maker': t['isBuyerMaker']} 
                for t in data] if data else []
    except: return []

# ============ 数据类 ============

@dataclass
class ETFFlow:
    symbol: str
    net_flow: float
    inflow: float
    outflow: float
    direction: str  # in/out/neutral
    impact: float   # 对价格的影响

@dataclass
class MMTrend:
    symbol: str
    trend: str       # bullish/bearish/neutral
    confidence: float
    inventory_change: float
    spread_change: float
    signals: List[Dict]

@dataclass
class OracleSignal:
    source: str
    price: float
    confidence: float
    timestamp: float

@dataclass
class LiquidityPrediction:
    symbol: str
    predicted_bid_depth: float
    predicted_ask_depth: float
    support_level: float
    resistance_level: float
    confidence: float
    signals: Dict

@dataclass
class LiquiditySignal:
    symbol: str
    direction: str   # bullish/bearish/neutral
    confidence: float
    etf_flow: ETFFlow
    mm_trend: MMTrend
    liquidity: LiquidityPrediction
    reason: str

# ============ ETF分析 ============

class ETFAnalyzer:
    """ETF资金流向分析"""
    
    def __init__(self):
        self.etf_cache = {}
        self.last_update = {}
    
    def get_etf_flow(self, symbol: str) -> ETFFlow:
        """获取ETF净流入"""
        now = time.time()
        
        # 缓存检查
        if symbol in self.etf_cache:
            if now - self.last_update.get(symbol, 0) < 3600:  # 1小时缓存
                return self.etf_cache[symbol]
        
        # 模拟ETF数据 (实际应从API获取)
        etf_data = self._simulate_etf_data(symbol)
        
        # 计算流动
        net_flow = etf_data['inflow'] - etf_data['outflow']
        direction = 'in' if net_flow > 0 else 'out' if net_flow < 0 else 'neutral'
        
        # 计算影响
        price = get_price(symbol)
        impact = (net_flow / 1_000_000) / price if price > 0 else 0
        
        result = ETFFlow(
            symbol=symbol,
            net_flow=net_flow,
            inflow=etf_data['inflow'],
            outflow=etf_data['outflow'],
            direction=direction,
            impact=min(1, max(-1, impact))
        )
        
        self.etf_cache[symbol] = result
        self.last_update[symbol] = now
        
        return result
    
    def _simulate_etf_data(self, symbol: str) -> Dict:
        """模拟ETF数据 (实际应从数据源获取)"""
        klines = get_klines(symbol, '1d', 30)
        if not klines:
            return {'inflow': 0, 'outflow': 0}
        
        closes = [k['close'] for k in klines]
        recent_vol = sum(k['volume'] for k in klines[-7:]) / 7
        
        # 模拟ETF流入/流出
        base_flow = recent_vol * 0.1
        
        # 根据价格趋势调整
        price_change = (closes[-1] - closes[-7]) / closes[-7] if len(closes) >= 7 else 0
        
        if price_change > 0:
            inflow = base_flow * (1 + price_change * 5)
            outflow = base_flow * 0.3
        else:
            inflow = base_flow * 0.3
            outflow = base_flow * (1 + abs(price_change) * 5)
        
        return {
            'inflow': inflow,
            'outflow': outflow
        }
    
    def get_etf_signal(self, symbol: str) -> Dict:
        """获取ETF信号"""
        flow = self.get_etf_flow(symbol)
        
        if flow.direction == 'in':
            signal = 0.5 * flow.impact
        elif flow.direction == 'out':
            signal = -0.5 * flow.impact
        else:
            signal = 0
        
        return {
            'signal': signal,
            'confidence': min(1, abs(flow.net_flow) / ETF_FLOW_THRESHOLD),
            'direction': flow.direction
        }

# ============ 做市商追踪 ============

class MMTracker:
    """做市商趋势追踪"""
    
    def __init__(self):
        self.orderbook_history = deque(maxlen=100)
        self.trade_history = deque(maxlen=100)
    
    def get_mm_trend(self, symbol: str) -> MMTrend:
        """获取做市商趋势"""
        # 获取订单簿
        ob = get_orderbook(symbol, 50)
        self.orderbook_history.append(ob)
        
        # 获取成交
        trades = get_recent_trades(symbol, 200)
        self.trade_history.append(trades)
        
        if len(self.orderbook_history) < 2:
            return MMTrend(
                symbol=symbol,
                trend='neutral',
                confidence=0.5,
                inventory_change=0,
                spread_change=0,
                signals=[]
            )
        
        # 计算库存变化
        inventory_change = self._calculate_inventory_change(trades)
        
        # 计算价差变化
        spread_change = self._calculate_spread_change()
        
        # 综合判断
        signals = []
        
        if inventory_change > MM_INVENTORY_CHANGE:
            trend = 'bullish'
            confidence = min(0.9, 0.5 + abs(inventory_change))
            signals.append({'type': 'inventory_increase', 'weight': 0.4})
        elif inventory_change < -MM_INVENTORY_CHANGE:
            trend = 'bearish'
            confidence = min(0.9, 0.5 + abs(inventory_change))
            signals.append({'type': 'inventory_decrease', 'weight': 0.4})
        else:
            trend = 'neutral'
            confidence = 0.5
            signals.append({'type': 'inventory_stable', 'weight': 0.2})
        
        # 价差信号
        if spread_change < -0.1:
            signals.append({'type': 'spread_narrow', 'weight': 0.2})
        elif spread_change > 0.1:
            signals.append({'type': 'spread_wide', 'weight': 0.2})
        
        return MMTrend(
            symbol=symbol,
            trend=trend,
            confidence=confidence,
            inventory_change=inventory_change,
            spread_change=spread_change,
            signals=signals
        )
    
    def _calculate_inventory_change(self, trades: List[dict]) -> float:
        """计算库存变化 (模拟)"""
        if not trades:
            return 0
        
        # 计算净买入/卖出
        buy_volume = sum(t['qty'] for t in trades if not t['is_buyer_maker'])
        sell_volume = sum(t['qty'] for t in trades if t['is_buyer_maker'])
        
        total_volume = buy_volume + sell_volume
        if total_volume == 0:
            return 0
        
        # 库存变化 = (买入 - 卖出) / 总量
        return (buy_volume - sell_volume) / total_volume
    
    def _calculate_spread_change(self) -> float:
        """计算价差变化"""
        if len(self.orderbook_history) < 2:
            return 0
        
        recent = self.orderbook_history[-1]
        previous = self.orderbook_history[-2]
        
        if recent['bid_depth'] == 0 or previous['bid_depth'] == 0:
            return 0
        
        recent_spread = recent['spread']
        previous_spread = previous['spread']
        
        if previous_spread == 0:
            return 0
        
        return (recent_spread - previous_spread) / previous_spread
    
    def get_mm_signal(self, symbol: str) -> Dict:
        """获取做市商信号"""
        trend = self.get_mm_trend(symbol)
        
        if trend.trend == 'bullish':
            signal = 0.5
        elif trend.trend == 'bearish':
            signal = -0.5
        else:
            signal = 0
        
        return {
            'signal': signal,
            'confidence': trend.confidence,
            'trend': trend.trend
        }

# ============ 预言机集成 ============

class Oracle集成:
    """预言机信号融合"""
    
    def __init__(self):
        self.oracle_cache = {}
        self.last_update = {}
    
    def get_oracle_price(self, symbol: str) -> Dict:
        """获取预言机价格 (模拟)"""
        now = time.time()
        
        # 缓存
        if symbol in self.oracle_cache:
            if now - self.last_update.get(symbol, 0) < 300:  # 5分钟
                return self.oracle_cache[symbol]
        
        # 模拟预言机数据
        binance_price = get_price(symbol)
        
        # Chainlink (权重最高)
        chainlink = {
            'source': 'chainlink',
            'price': binance_price * (1 + (hash(symbol) % 100 - 50) / 10000),
            'confidence': 0.85
        }
        
        # Band Protocol
        band = {
            'source': 'band',
            'price': binance_price * (1 + (hash(symbol + 'b') % 100 - 50) / 10000),
            'confidence': 0.80
        }
        
        # Pyth
        pyth = {
            'source': 'pyth',
            'price': binance_price * (1 + (hash(symbol + 'p') % 100 - 50) / 10000),
            'confidence': 0.75
        }
        
        # API3
        api3 = {
            'source': 'api3',
            'price': binance_price * (1 + (hash(symbol + 'a') % 100 - 50) / 10000),
            'confidence': 0.70
        }
        
        oracles = [chainlink, band, pyth, api3]
        
        # 融合信号
        valid = [o for o in oracles if o['confidence'] >= ORACLE_CONFIDENCE]
        
        if not valid:
            result = {'signal': 0, 'confidence': 0, 'sources': 0}
        else:
            weighted = sum(o['price'] * o['confidence'] for o in valid)
            total_conf = sum(o['confidence'] for o in valid)
            
            # 计算信号 (相对于binance)
            avg_price = weighted / total_conf
            signal = (avg_price - binance_price) / binance_price
            
            result = {
                'signal': signal,
                'confidence': total_conf / len(oracles),
                'sources': len(valid),
                'avg_price': avg_price
            }
        
        self.oracle_cache[symbol] = result
        self.last_update[symbol] = now
        
        return result
    
    def get_oracle_signal(self, symbol: str) -> Dict:
        """获取预言机信号"""
        oracle = self.get_oracle_price(symbol)
        return {
            'signal': oracle['signal'],
            'confidence': oracle['confidence']
        }

# ============ 流动性预测 ============

class LiquidityPredictor:
    """流动性预测"""
    
    def __init__(self):
        self.liquidity_history = deque(maxlen=168)  # 7天
    
    def predict_liquidity(self, symbol: str, window: int = 24) -> LiquidityPrediction:
        """预测未来流动性"""
        # 历史流动性
        historical = self._get_historical_liquidity(symbol, window)
        
        # ETF影响
        etf = ETFAnalyzer()
        etf_flow = etf.get_etf_flow(symbol)
        
        # 做市商趋势
        mm = MMTracker()
        mm_trend = mm.get_mm_trend(symbol)
        
        # 预言机
        oracle = Oracle集成()
        oracle_signal = oracle.get_oracle_price(symbol)
        
        # 综合预测
        avg_bid = historical['avg_bid_depth']
        avg_ask = historical['avg_ask_depth']
        
        # ETF影响
        etf_impact = 1 + (etf_flow.impact * 0.3)
        
        # 做市商影响
        if mm_trend.trend == 'bullish':
            mm_impact = 1.2
        elif mm_trend.trend == 'bearish':
            mm_impact = 0.8
        else:
            mm_impact = 1.0
        
        predicted_bid = avg_bid * etf_impact * mm_impact
        predicted_ask = avg_ask * etf_impact * mm_impact
        
        # 支撑阻力位
        price = get_price(symbol)
        support = price * 0.98
        resistance = price * 1.02
        
        return LiquidityPrediction(
            symbol=symbol,
            predicted_bid_depth=predicted_bid,
            predicted_ask_depth=predicted_ask,
            support_level=support,
            resistance_level=resistance,
            confidence=0.75,
            signals={
                'etf_impact': etf_flow.impact,
                'mm_impact': 1 if mm_trend.trend == 'bullish' else -1 if mm_trend.trend == 'bearish' else 0,
                'oracle_impact': oracle_signal['signal']
            }
        )
    
    def _get_historical_liquidity(self, symbol: str, window: int) -> Dict:
        """获取历史流动性"""
        klines = get_klines(symbol, '1h', window)
        
        if not klines:
            return {'avg_bid_depth': 0, 'avg_ask_depth': 0}
        
        volumes = [k['volume'] for k in klines]
        avg_volume = sum(volumes) / len(volumes)
        
        # 假设订单簿深度与成交量相关
        avg_bid = avg_volume * 0.4
        avg_ask = avg_volume * 0.4
        
        return {
            'avg_bid_depth': avg_bid,
            'avg_ask_depth': avg_ask
        }
    
    def find_support_resistance(self, symbol: str) -> Dict:
        """寻找支撑阻力位"""
        klines = get_klines(symbol, '1d', 30)
        if not klines:
            return {'support': 0, 'resistance': 0}
        
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        # 计算关键价位
        resistance = max(highs[-5:]) if len(highs) >= 5 else max(highs)
        support = min(lows[-5:]) if len(lows) >= 5 else min(lows)
        
        return {
            'support': support,
            'resistance': resistance
        }

# ============ 综合分析 ============

class ETFLiquidityAnalyzer:
    """ETF与流动性综合分析"""
    
    def __init__(self):
        self.etf = ETFAnalyzer()
        self.mm = MMTracker()
        self.oracle = Oracle集成()
        self.liquidity = LiquidityPredictor()
    
    def get_liquidity_signal(self, symbol: str) -> LiquiditySignal:
        """获取综合流动性信号"""
        # 各组件
        etf_flow = self.etf.get_etf_flow(symbol)
        mm_trend = self.mm.get_mm_trend(symbol)
        liquidity_pred = self.liquidity.predict_liquidity(symbol)
        
        # 综合评分
        signals = []
        
        # ETF信号
        if etf_flow.direction == 'in':
            signals.append(('etf', 0.3, 0.8))
        elif etf_flow.direction == 'out':
            signals.append(('etf', -0.3, 0.8))
        
        # 做市商信号
        if mm_trend.trend == 'bullish':
            signals.append(('mm', 0.25, mm_trend.confidence))
        elif mm_trend.trend == 'bearish':
            signals.append(('mm', -0.25, mm_trend.confidence))
        
        # 流动性信号
        if liquidity_pred.predicted_bid_depth > liquidity_pred.predicted_ask_depth * 1.1:
            signals.append(('liq', 0.2, 0.7))
        elif liquidity_pred.predicted_ask_depth > liquidity_pred.predicted_bid_depth * 1.1:
            signals.append(('liq', -0.2, 0.7))
        
        # 加权计算
        total_signal = sum(s[1] * s[2] for s in signals)
        total_weight = sum(s[2] for s in signals)
        combined = total_signal / total_weight if total_weight > 0 else 0
        
        # 方向判断
        if combined > 0.2:
            direction = 'bullish'
        elif combined < -0.2:
            direction = 'bearish'
        else:
            direction = 'neutral'
        
        # 置信度
        confidence = min(1, abs(combined) + 0.3)
        
        # 原因
        reasons = []
        if etf_flow.direction == 'in':
            reasons.append(f"ETF流入${etf_flow.inflow/1e6:.1f}M")
        elif etf_flow.direction == 'out':
            reasons.append(f"ETF流出${etf_flow.outflow/1e6:.1f}M")
        
        if mm_trend.trend == 'bullish':
            reasons.append("做市商看多")
        elif mm_trend.trend == 'bearish':
            reasons.append("做市商看空")
        
        return LiquiditySignal(
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            etf_flow=etf_flow,
            mm_trend=mm_trend,
            liquidity=liquidity_pred,
            reason="; ".join(reasons) if reasons else "无明显信号"
        )

def main():
    analyzer = ETFLiquidityAnalyzer()
    
    print("=== ETF与流动性信号 ===")
    for symbol in ['BTC', 'ETH', 'SOL']:
        signal = analyzer.get_liquidity_signal(symbol)
        print(f"\n{signal.symbol}: {signal.direction} ({signal.confidence:.0%})")
        print(f"  原因: {signal.reason}")
        print(f"  ETF净流: ${signal.etf_flow.net_flow/1e6:.2f}M")
        print(f"  做市商: {signal.mm_trend.trend}")

if __name__ == "__main__":
    main()
