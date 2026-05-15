#!/usr/bin/env python3
"""
G40 - 超级自主量化交易系统 v4.0
===================
整合 资产管�ite + 撞球 + 轮动 + 多空 + ETF + 自主调仓 的终极系统

核心升级:
- G40Optimizer: 超强自主优化器
- AutoRebalancer Pro: 智能调仓大师
- MultiStrategy Fusion: 多策略融合决策
- RiskParity: 风险平价仓位管理
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

# ============ G40 核心配置 ============

# 交易配置
MIN_USDT_RESERVE = 3.0        # 最低USDT储备
MIN_TRADE_VALUE = 0.3         # 最小交易价值
SCAN_INTERVAL = 25             # 扫描间隔(秒)
STOP_LOSS = 0.05              # 止损5%
TAKE_PROFIT = 0.25            # 止盈25%
MAX_DRAWDOWN = 0.15           # 最大回撤15%

# 杠杆配置
USE_CROSS_MARGIN = True       # 使用全仓杠杆
MARGIN_LEVERAGE = 2           # 杠杆倍数降低到2倍，更安全

# 账户管理配置
MAX_SINGLE_POSITION_PCT = 0.20    # 单币种最大占比20%
MAX_MARGIN_POSITION_PCT = 0.40    # 杠杆账户最大占比40%
MAX_CROSS_MARGIN_EXPOSURE = 1000  # 全仓杠杆最大敞口$1000

# 自主调仓配置
MAX_POSITION_CONCENTRATION = 0.20   # 单币种最大集中度20%
REBALANCE_THRESHOLD = 0.03         # 偏离3%即触发调仓
REBALANCE_COOLDOWN = 120            # 调仓冷却2分钟

# 资产配置
AUTO_CONVERT_THRESHOLD = 0.3       # 小于此金额自动转换
CONVERT_COOLDOWN = 120              # 转换冷却2分钟

# 策略权重配置
KELLY_BASE = 0.25                  # Kelly基础比例
MAX_POSITIONS = 5                  # 最大持仓数

# 流动性评分
LIQUIDITY_SCORE = {
    'BTC': 100, 'ETH': 95, 'BNB': 90, 'SOL': 85, 
    'XRP': 80, 'ADA': 75, 'DOT': 70, 'LINK': 65,
    'DOGE': 60, 'SHIB': 30, 'PEPE': 25, 'BONK': 25,
    'FLOKI': 20, 'NEIRO': 15, 'BOME': 20, 'TURBO': 15,
    'LTC': 55, 'ETC': 45, 'AVAX': 60, 'MATIC': 55
}

# ============ 工具函数 ============

def get_price(symbol: str) -> float:
    """获取币种价格"""
    try:
        d = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT')
        return float(d['price']) if d else 0
    except: return 0

def format_quantity(quantity: float, symbol: str) -> str:
    """格式化下单数量"""
    if quantity >= 1000: return f"{int(quantity)}"
    if quantity >= 1: return f"{quantity:.4f}"
    if quantity >= 0.001: return f"{quantity:.6f}"
    return f"{quantity:.8f}"

# ============ G40 超强自主优化器 ============

class G40Optimizer:
    """
    G40 核心大脑 - 自主学习优化器
    - 策略选择: 基于市场状态选择最佳策略
    - 权重优化: 动态调整策略权重
    - 趋势预测: 预判市场走势
    - 风险控制: 动态风控线
    """
    
    def __init__(self, g40):
        self.g40 = g40
        self.strategy_performance = defaultdict(lambda: {'wins': 0, 'losses': 0, 'trades': 0, 'pnl': 0})
        self.market_regime = 'unknown'  # trending, ranging, volatile
        self.strategy_weights = {
            'go-core': 0.20,
            'go-pool': 0.20,
            'go-rotate': 0.15,
            'go-long-short': 0.15,
            'go-detect': 0.10,
            'go-etf': 0.10,
            'top10': 0.10
        }
        self.epsilon = 0.15  # 探索率
        self.learning_rate = 0.08
        self.confidence_threshold = 0.55
        
    def detect_market_regime(self) -> str:
        """检测市场状态"""
        try:
            btc = get_price('BTC')
            # 获取主流币波动率
            volatilities = []
            for sym in ['BTC', 'ETH', 'SOL', 'XRP']:
                try:
                    d = api_pub(f'https://api.binance.com/api/v3/klines?symbol={sym}USDT&interval=1h&limit=24')
                    if d and len(d) > 10:
                        highs = [float(k[2]) for k in d[-24:]]
                        lows = [float(k[3]) for k in d[-24:]]
                        close = [float(k[4]) for k in d[-24:]]
                        volatility = (max(highs) - min(lows)) / max(highs) if max(highs) > 0 else 0
                        volatilities.append(volatility / close[-1] if close[-1] > 0 else 0)
                except: pass
            
            avg_vol = statistics.mean(volatilities) if volatilities else 0.05
            
            # 检测趋势
            if avg_vol > 0.03:
                self.market_regime = 'volatile'
            elif avg_vol < 0.015:
                self.market_regime = 'ranging'
            else:
                self.market_regime = 'trending'
                
            return self.market_regime
        except: return 'unknown'
    
    def get_adaptive_weights(self) -> Dict[str, float]:
        """根据市场状态自适应调整权重"""
        regime = self.detect_market_regime()
        
        if regime == 'trending':
            weights = {
                'go-core': 0.25, 'go-pool': 0.20, 'go-rotate': 0.15,
                'go-long-short': 0.10, 'go-detect': 0.10, 'go-etf': 0.10, 'top10': 0.10
            }
        elif regime == 'ranging':
            weights = {
                'go-core': 0.15, 'go-pool': 0.10, 'go-rotate': 0.20,
                'go-long-short': 0.20, 'go-detect': 0.10, 'go-etf': 0.15, 'top10': 0.10
            }
        else:  # volatile
            weights = {
                'go-core': 0.20, 'go-pool': 0.15, 'go-rotate': 0.15,
                'go-long-short': 0.20, 'go-detect': 0.15, 'go-etf': 0.10, 'top10': 0.05
            }
        
        self.strategy_weights = weights
        return weights
    
    def calculate_signal(self, symbol: str) -> Dict:
        """综合多策略计算信号"""
        weights = self.get_adaptive_weights()
        
        signals = {
            'go-core': self._signal_go_core(symbol),
            'go-pool': self._signal_go_pool(symbol),
            'go-rotate': self._signal_go_rotate(symbol),
            'go-long-short': self._signal_go_long_short(symbol),
            'go-detect': self._signal_go_detect(symbol),
            'go-etf': self._signal_go_etf(symbol),
            'top10': self._signal_top10(symbol)
        }
        
        # 加权融合信号
        combined_signal = 0
        total_weight = 0
        for strategy, (sig, conf) in signals.items():
            weight = weights.get(strategy, 0.1)
            combined_signal += sig * weight
            total_weight += weight
        
        final_signal = combined_signal / total_weight if total_weight > 0 else 0
        avg_confidence = statistics.mean([c for _, c in signals.values()]) if signals else 0.5
        
        return {
            'signal': final_signal,
            'confidence': avg_confidence,
            'regime': self.market_regime,
            'signals': signals,
            'weights': weights
        }
    
    def _signal_go_core(self, symbol: str) -> Tuple[float, float]:
        """Go-Core 核心信号 - 趋势跟踪"""
        try:
            d = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50')
            if not d or len(d) < 20: return 0, 0.5
            
            closes = [float(k[4]) for k in d[-20:]]
            ma5 = sum(closes[-5:]) / 5
            ma20 = sum(closes[-20:]) / 20
            current = closes[-1]
            
            # 趋势强度
            trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
            
            # 动量
            momentum = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] > 0 else 0
            
            signal = (trend + momentum) * 2
            confidence = min(abs(trend) * 10 + 0.5, 0.95)
            
            return signal, confidence
        except: return 0, 0.5
    
    def _signal_go_pool(self, symbol: str) -> Tuple[float, float]:
        """Go-Pool 撞球信号 - 资金流向"""
        try:
            d = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=24')
            if not d or len(d) < 12: return 0, 0.5
            
            volumes = [float(k[5]) for k in d[-24:]]
            prices = [float(k[4]) for k in d[-24:]]
            
            # 资金流入/流出
            inflows = sum(v for i, v in enumerate(volumes[1:]) if prices[i+1] > prices[i])
            outflows = sum(v for i, v in enumerate(volumes[1:]) if prices[i+1] < prices[i])
            
            net_flow = (inflows - outflows) / sum(volumes) if sum(volumes) > 0 else 0
            
            signal = net_flow * 5
            confidence = min(abs(net_flow) * 5 + 0.5, 0.90)
            
            return signal, confidence
        except: return 0, 0.5
    
    def _signal_go_rotate(self, symbol: str) -> Tuple[float, float]:
        """Go-Rotate 轮动信号 - 板块轮动"""
        try:
            # 获取多个币种表现
            syms = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK']
            if symbol in syms:
                syms.remove(symbol)
            syms = syms[:5]
            
            performances = []
            for sym in syms:
                try:
                    d = api_pub(f'https://api.binance.com/api/v3/klines?symbol={sym}USDT&interval=4h&limit=10')
                    if d and len(d) > 5:
                        perf = (float(d[-1][4]) - float(d[-5][4])) / float(d[-5][4])
                        performances.append((sym, perf))
                except: pass
            
            if not performances: return 0, 0.5
            
            # 当前币种表现
            current_perf = 0
            for sym, perf in performances:
                if sym == symbol:
                    current_perf = perf
                    break
            
            # 轮动排名
            sorted_perfs = sorted(performances, key=lambda x: -x[1])
            rank = next((i for i, (s, _) in enumerate(sorted_perfs) if s == symbol), len(sorted_perfs))
            
            signal = (len(sorted_perfs) - rank) / len(sorted_perfs) - 0.5
            confidence = 0.5 + (1 - rank / len(sorted_perfs)) * 0.3
            
            return signal * 2, confidence
        except: return 0, 0.5
    
    def _signal_go_long_short(self, symbol: str) -> Tuple[float, float]:
        """Go-Long-Short 多空信号"""
        try:
            d = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50')
            if not d or len(d) < 20: return 0, 0.5
            
            highs = [float(k[2]) for k in d[-20:]]
            lows = [float(k[3]) for k in d[-20:]]
            
            # 多空比率
            range_size = (max(highs) - min(lows)) / min(lows) if min(lows) > 0 else 0
            
            # 多空信号
            if range_size > 0.05:
                signal = 0.3  # 宽幅震荡
            elif range_size < 0.02:
                signal = 0.1  # 窄幅整理
            else:
                signal = 0.2
            
            return signal, 0.6
        except: return 0, 0.5
    
    def _signal_go_detect(self, symbol: str) -> Tuple[float, float]:
        """Go-Detect 异常检测信号"""
        try:
            d = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=100')
            if not d or len(d) < 50: return 0, 0.5
            
            closes = [float(k[4]) for k in d[-50:]]
            
            # 异常波动检测
            mean = statistics.mean(closes)
            stdev = statistics.stdev(closes) if len(closes) > 1 else 0
            zscore = (closes[-1] - mean) / stdev if stdev > 0 else 0
            
            # 异常信号
            if abs(zscore) > 2:
                signal = -zscore * 0.2  # 超卖/超买反转
                confidence = 0.8
            else:
                signal = zscore * 0.1
                confidence = 0.5
            
            return signal, confidence
        except: return 0, 0.5
    
    def _signal_go_etf(self, symbol: str) -> Tuple[float, float]:
        """Go-ETF ETF流动性信号"""
        try:
            # 检测整体市场资金流
            total_inflow = 0
            for sym in ['BTC', 'ETH', 'SOL']:
                try:
                    d = api_pub(f'https://api.binance.com/api/v3/klines?symbol={sym}USDT&interval=1h&limit=24')
                    if d and len(d) > 10:
                        inflow = float(d[-1][5]) - float(d[-10][5])
                        total_inflow += inflow
                except: pass
            
            signal = 0.2 if total_inflow > 0 else -0.1
            return signal, 0.55
        except: return 0, 0.5
    
    def _signal_top10(self, symbol: str) -> Tuple[float, float]:
        """Top10 交易员信号"""
        # 基于Meme币和主流币动量
        try:
            d = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=10')
            if not d: return 0, 0.5
            
            recent = [float(k[4]) for k in d[-10:]]
            momentum = (recent[-1] - recent[0]) / recent[0] if recent[0] > 0 else 0
            
            signal = momentum * 3
            confidence = min(abs(momentum) * 10 + 0.5, 0.85)
            
            return signal, confidence
        except: return 0, 0.5
    
    def record_trade(self, symbol: str, strategy: str, pnl: float):
        """记录交易结果用于学习"""
        self.strategy_performance[strategy]['trades'] += 1
        if pnl > 0:
            self.strategy_performance[strategy]['wins'] += 1
            self.strategy_performance[strategy]['pnl'] += pnl
        else:
            self.strategy_performance[strategy]['losses'] += 1
            self.strategy_performance[strategy]['pnl'] += pnl
    
    def evolve(self):
        """自我进化 - 调整策略权重"""
        # 基于表现调整权重
        for strategy, perf in self.strategy_performance.items():
            if perf['trades'] < 3: continue
            
            win_rate = perf['wins'] / perf['trades'] if perf['trades'] > 0 else 0.5
            avg_pnl = perf['pnl'] / perf['trades'] if perf['trades'] > 0 else 0
            
            # 调整权重
            if win_rate > 0.6 and avg_pnl > 0:
                self.strategy_weights[strategy] *= (1 + self.learning_rate)
            elif win_rate < 0.4 or avg_pnl < -0.02:
                self.strategy_weights[strategy] *= (1 - self.learning_rate)
        
        # 归一化权重
        total = sum(self.strategy_weights.values())
        for k in self.strategy_weights:
            self.strategy_weights[k] /= total


# ============ G40 智能资产管理器Pro ============

class AssetManagerPro:
    """
    资产管理Pro - 智能分配、转换、杠杆调度
    """
    
    def __init__(self, g40):
        self.g40 = g40
        self.last_convert_time = 0
        self.last_leverage_check = 0
        self.conversion_log = []
        
    def get_spot_usdt(self) -> float:
        """获取现货USDT"""
        try:
            account = self.g40._api_signed("/api/v3/account")
            for b in account.get('balances', []):
                if b['asset'] == 'USDT':
                    return float(b.get('free', 0))
        except: pass
        return 0
    
    def get_all_holdings(self) -> dict:
        """获取所有持仓"""
        holdings = {}
        try:
            account = self.g40._api_signed("/api/v3/account")
            for b in account.get('balances', []):
                free = float(b.get('free', 0))
                locked = float(b.get('locked', 0))
                total = free + locked
                if total > 0.0001:
                    holdings[b['asset']] = {'free': free, 'locked': locked, 'total': total}
        except: pass
        return holdings
    
    def get_price_dict(self) -> dict:
        """获取价格字典"""
        prices = {}
        for sym in LIQUIDITY_SCORE.keys():
            prices[sym] = get_price(sym)
        return prices
    
    def get_total_assets(self) -> Tuple[float, dict]:
        """获取总资产和持仓明细"""
        usdt = self.get_spot_usdt()
        holdings = self.get_all_holdings()
        prices = self.get_price_dict()
        
        total = usdt
        details = {'USDT': {'value': usdt, 'pct': 0, 'amount': usdt, 'price': 1}}
        
        for asset, data in holdings.items():
            if asset == 'USDT': continue
            price = prices.get(asset, 0)
            if price <= 0:
                price = get_price(asset)
            value = data['total'] * price
            total += value
            details[asset] = {'value': value, 'amount': data['total'], 'price': price}
        
        # 计算百分比
        for asset in details:
            if 'pct' not in details[asset]:
                details[asset]['pct'] = details[asset]['value'] / total if total > 0 else 0
        
        return total, details
    
    def auto_convert_small_holdings(self) -> dict:
        """自动转换小额持仓"""
        result = {'converted': [], 'total': 0}
        
        if time.time() - self.last_convert_time < CONVERT_COOLDOWN:
            return result
        
        usdt = self.get_spot_usdt()
        if usdt >= MIN_USDT_RESERVE:
            return result
        
        holdings = self.get_all_holdings()
        prices = self.get_price_dict()
        
        for asset, data in holdings.items():
            if asset == 'USDT' or asset in ['BTC', 'ETH', 'BNB']: continue
            
            value = data['total'] * prices.get(asset, 0)
            if value < AUTO_CONVERT_THRESHOLD and data['total'] > 0:
                # 卖出
                try:
                    qty = format_quantity(data['total'], asset)
                    resp = place_order(asset, "SELL", data['total'])
                    if resp.get('success'):
                        new_usdt = self.get_spot_usdt()
                        converted = new_usdt - usdt
                        result['converted'].append(asset)
                        result['total'] += converted
                        self.g40.log(f"自动转换 {asset}: {data['total']:.4f} = ${converted:.2f}", "INFO")
                except: pass
        
        if result['converted']:
            self.last_convert_time = time.time()
        
        return result
    
    def should_use_leverage(self, required: float, current_margin_exposure: float = 0) -> bool:
        """判断是否使用杠杆 - 带风控"""
        if not USE_CROSS_MARGIN:
            return False
        
        usdt = self.get_spot_usdt()
        
        # 检查全仓杠杆敞口
        if current_margin_exposure >= MAX_CROSS_MARGIN_EXPOSURE:
            self.g40.log(f"全仓杠杆已达上限${MAX_CROSS_MARGIN_EXPOSURE}", "WARN")
            return False
        
        # 现货不足且超过阈值
        if required > usdt and usdt >= MIN_TRADE_VALUE:
            return True
        
        # USDT低于最低储备也用杠杆
        if usdt < MIN_USDT_RESERVE and required > 0:
            return True
        
        return False
    
    def execute_with_leverage(self, symbol: str, side: str, signal: float, price: float, spot_usdt: float, current_exposure: float = 0) -> dict:
        """杠杆执行交易 - 带风控"""
        try:
            # 检查是否超过杠杆上限
            if current_exposure >= MAX_CROSS_MARGIN_EXPOSURE:
                return {'success': False, 'error': '杠杆敞口已达上限'}
            
            # 计算杠杆金额 (限制最大敞口)
            available_margin = MAX_CROSS_MARGIN_EXPOSURE - current_exposure
            margin_budget = min(spot_usdt * MARGIN_LEVERAGE, available_margin)
            
            if margin_budget < MIN_TRADE_VALUE:
                return {'success': False, 'error': '杠杆预算不足'}
            
            quantity = margin_budget / price
            
            self.g40.log(f"⚡ 杠杆交易 {symbol} {side} {quantity:.4f} @ ${price:.6f}", "INFO")
            
            # 执行市价单
            resp = place_order(symbol, side, quantity)
            
            if resp.get('success'):
                self.g40.log(f"✅ 杠杆交易成功: {symbol}", "INFO")
                return {'success': True, 'leverage': True, 'quantity': quantity}
            else:
                self.g40.log(f"❌ 杠杆交易失败: {resp.get('error')}", "ERROR")
                return {'success': False, 'error': resp.get('error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============ G40 自主调仓大师Pro ============

class AutoRebalancerPro:
    """
    自主调仓大师Pro - 智能分散风险
    - 集中度管理
    - 动态再平衡
    - 趋势止盈
    """
    
    def __init__(self, g40):
        self.g40 = g40
        self.last_rebalance = 0
        self.max_concentration = MAX_POSITION_CONCENTRATION
        self.rebalance_cooldown = REBALANCE_COOLDOWN
        self.target_positions = {}  # 目标持仓
        self.margin_exposure_limit = MAX_CROSS_MARGIN_EXPOSURE
        
    def get_concentrations(self) -> dict:
        """计算持仓集中度"""
        am = self.g40.asset_manager
        total, details = am.get_total_assets()
        
        concentrations = {}
        for asset, data in details.items():
            if data['value'] > 1:  # 只关注$1以上
                concentrations[asset] = {
                    'value': data['value'],
                    'pct': data['pct'],
                    'amount': data.get('amount', 0),
                    'price': data.get('price', get_price(asset))
                }
        
        return concentrations
    
    def get_cross_margin_exposure(self) -> float:
        """获取全仓杠杆敞口"""
        try:
            cross = self.g40._api_signed("/sapi/v1/margin/account")
            total = 0
            for a in cross.get('userAssets', []):
                net = float(a.get('netAsset', 0))
                if net > 0:  # 做多才算敞口
                    asset = a['asset']
                    price = get_price(asset)
                    total += net * price
            return total
        except: return 0
    
    def calculate_target_positions(self) -> dict:
        """计算目标持仓比例"""
        total, details = self.g40.asset_manager.get_total_assets()
        
        # 风险平价配置
        targets = {}
        
        # BTC/ETH 主流币 - 较大仓位
        for asset in ['BTC', 'ETH']:
            if asset in details:
                targets[asset] = 0.15  # 15%
        
        # 主流币种
        mainstream = ['SOL', 'XRP', 'ADA', 'DOT', 'LINK']
        mainstream_pct = 0.10  # 各10%
        
        # Meme币总占比不超过20%
        meme_limit = 0.20
        
        # 基于集中度计算目标
        concentrations = self.get_concentrations()
        
        for asset, data in concentrations.items():
            if asset == 'USDT': continue
            
            current_pct = data['pct']
            
            if asset in ['BTC', 'ETH']:
                targets[asset] = min(current_pct, 0.20)
            elif asset in mainstream:
                targets[asset] = min(current_pct, mainstream_pct)
            elif current_pct > self.max_concentration:
                targets[asset] = self.max_concentration  # 强制降低
            else:
                targets[asset] = current_pct
        
        return targets
    
    def rebalance_if_needed(self) -> dict:
        """检查并执行调仓"""
        now = time.time()
        if now - self.last_rebalance < self.rebalance_cooldown:
            return {"action": "skip", "reason": "冷却中"}
        
        concentrations = self.get_concentrations()
        
        # 找出需要调仓的币种
        over_positions = []
        under_positions = []
        
        for asset, data in concentrations.items():
            if asset == 'USDT': continue
            
            pct = data['pct']
            
            if pct > self.max_concentration:
                over_positions.append((asset, data, pct - self.max_concentration))
            elif pct < 0.05 and pct > 0.01:  # 小仓位但值得加
                under_positions.append((asset, data))
        
        if not over_positions and not under_positions:
            return {"action": "skip", "reason": "无需调仓"}
        
        results = []
        
        # 减持超限币种
        for asset, data, excess in sorted(over_positions, key=lambda x: -x[2]):
            # 卖出超出的部分
            sell_value = data['value'] * (excess / data['pct'])
            sell_amount = sell_value / data['price'] if data['price'] > 0 else 0
            
            if sell_amount > 0.0001:
                try:
                    resp = place_order(asset, "SELL", sell_amount)
                    if resp.get('success'):
                        self.g40.log(f"🔄 调仓卖出 {asset}: {sell_amount:.4f} (占比{data['pct']:.1%}→{self.max_concentration:.1%})", "INFO")
                        results.append({'action': 'sell', 'asset': asset, 'amount': sell_amount})
                except Exception as e:
                    self.g40.log(f"调仓失败 {asset}: {e}", "ERROR")
        
        if results:
            self.last_rebalance = now
            return {"action": "rebalanced", "results": results}
        
        return {"action": "failed"}
    
    def emergency_rebalance(self):
        """紧急调仓 - 集中度或杠杆超标"""
        concentrations = self.get_concentrations()
        
        # 1. 处理集中度超标的币种
        emergency_positions = [(a, d) for a, d in concentrations.items() 
                              if d['pct'] > 0.35 and a != 'USDT']
        
        if emergency_positions:
            self.g40.log(f"🚨 紧急调仓触发: {len(emergency_positions)}个集中度超标持仓", "WARN")
        
        for asset, data in emergency_positions:
            target_pct = 0.20
            excess_pct = data['pct'] - target_pct
            sell_value = data['value'] * (excess_pct / data['pct'])
            sell_amount = sell_value / data['price'] if data['price'] > 0 else 0
            
            if sell_amount > 0.0001:
                try:
                    resp = place_order(asset, "SELL", sell_amount)
                    if resp.get('success'):
                        self.g40.log(f"🚨 紧急调仓 {asset}: 卖出{sell_amount:.4f}", "WARN")
                except: pass
        
        # 2. 检查并减少全仓杠杆敞口
        total, details = self.g40.asset_manager.get_total_assets()
        margin_value = sum(d['value'] for a, d in details.items() 
                         if a not in ['USDT'] and d.get('pct', 0) > 0.25)
        
        if margin_value > self.margin_exposure_limit:
            self.g40.log(f"⚠️ 全仓杠杆敞口${margin_value:.2f}超过限制${self.margin_exposure_limit}", "WARN")
            # 需要平掉部分杠杆仓位
            # 优先平掉盈利最多的
            pass


# ============ G40 主系统 ============

class G40:
    """
    G40 超级自主量化交易系统
    """
    
    def __init__(self):
        self.version = "4.0"
        self.name = "G40 超级自主量化系统"
        self.running = False
        self.state_file = "/home/goose/.openclaw/workspace/.g40_state.json"
        self.log_file = "/home/goose/.openclaw/workspace/logs/g40.log"
        
        # 核心组件
        self.optimizer = G40Optimizer(self)
        self.asset_manager = AssetManagerPro(self)
        self.rebalancer = AutoRebalancerPro(self)
        
        # 状态
        self.active_trades = {}
        self.trade_history = []
        self.stats = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
        
        # 初始化
        self._init_logger()
        
    def _init_logger(self):
        """初始化日志"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log(self, msg: str, level: str = "INFO"):
        """记录日志"""
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        log_line = f"[{ts}] [{level}] {msg}\n"
        
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
    
    def get_account_status(self) -> dict:
        """获取账户状态"""
        try:
            account = self._api_signed("/api/v3/account")
            spot_usdt = 0
            holdings = {}
            
            for b in account.get('balances', []):
                free = float(b.get('free', 0))
                if free > 0.0001:
                    holdings[b['asset']] = free
                    if b['asset'] == 'USDT':
                        spot_usdt = free
            
            total = spot_usdt
            for asset, amount in holdings.items():
                if asset != 'USDT':
                    price = get_price(asset)
                    total += amount * price
            
            return {
                'spot_usdt': spot_usdt,
                'total': total,
                'holdings': holdings
            }
        except Exception as e:
            self.log(f"获取账户失败: {e}", "ERROR")
            return {'spot_usdt': 0, 'total': 0, 'holdings': {}}
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """分析单个币种"""
        signal_data = self.optimizer.calculate_signal(symbol)
        
        return {
            'symbol': symbol,
            'signal': signal_data['signal'],
            'confidence': signal_data['confidence'],
            'regime': signal_data['regime'],
            'price': get_price(symbol),
            'action': 'skip'
        }
    
    def execute_trade(self, symbol: str, signal: float, confidence: float) -> dict:
        """执行交易"""
        if confidence < self.optimizer.confidence_threshold:
            return {'action': 'skip', 'reason': '信心度不足'}
        
        price = get_price(symbol)
        if price <= 0:
            return {'action': 'skip', 'reason': '价格获取失败'}
        
        usdt = self.asset_manager.get_spot_usdt()
        budget = usdt * KELLY_BASE * confidence
        
        if budget < MIN_TRADE_VALUE:
            # 尝试杠杆
            if self.asset_manager.should_use_leverage(MIN_TRADE_VALUE):
                return self.asset_manager.execute_with_leverage(symbol, "BUY", signal, price, usdt)
            return {'action': 'skip', 'reason': '资金不足'}
        
        # 计算数量
        quantity = budget / price
        
        # 执行
        resp = place_order(symbol, "BUY", quantity)
        if resp.get('success'):
            return {'action': 'trade', 'symbol': symbol, 'quantity': quantity, 'price': price}
        
        return {'action': 'skip', 'reason': resp.get('error', '交易失败')}
    
    def scan_and_trade(self):
        """扫描并交易"""
        # 自主调仓
        self.rebalancer.rebalance_if_needed()
        
        # 自动转换小额持仓
        self.asset_manager.auto_convert_small_holdings()
        
        # 分析币种
        symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 
                   'DOGE', 'SHIB', 'PEPE', 'BOME', 'NEIRO', 'TURBO', 'FLOKI']
        
        signals = []
        for sym in symbols:
            try:
                result = self.analyze_symbol(sym)
                if result['confidence'] > 0.6:
                    signals.append(result)
            except: pass
        
        # 排序
        signals.sort(key=lambda x: -(x['signal'] * x['confidence']))
        
        # 执行最佳信号
        if signals:
            best = signals[0]
            if best['signal'] > 0.3:
                self.execute_trade(best['symbol'], best['signal'], best['confidence'])
    
    def run(self):
        """运行系统"""
        self.running = True
        self.log(f"{self.name} 启动", "INFO")
        
        while self.running:
            try:
                # 获取账户状态
                status = self.get_account_status()
                self.log(f"总资产: ${status['total']:.2f}", "INFO")
                
                # 扫描交易
                self.scan_and_trade()
                
            except Exception as e:
                import traceback
                self.log(f"运行异常: {e}: {traceback.format_exc()[:200]}", "ERROR")
            
            time.sleep(SCAN_INTERVAL)
    
    def stop(self):
        """停止系统"""
        self.running = False
        self.log(f"{self.name} 停止", "INFO")


# ============ 全局函数 ============

_api_pub_cache = {}
_api_pub_time = {}

def api_pub(url: str) -> dict:
    """公共API请求(带缓存)"""
    global _api_pub_cache, _api_pub_time
    
    now = time.time()
    if url in _api_pub_cache and now - _api_pub_time.get(url, 0) < 5:
        return _api_pub_cache[url]
    
    import urllib.request
    PROXY = "http://172.29.144.1:7897"
    
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        resp = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        _api_pub_cache[url] = resp
        _api_pub_time[url] = now
        return resp
    except:
        return _api_pub_cache.get(url, {})


def place_order(symbol: str, side: str, quantity: float, order_type: str = "MARKET") -> dict:
    """下单"""
    import hmac, hashlib, urllib.request
    
    API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
    API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
    PROXY = "http://172.29.144.1:7897"
    
    ts = int(time.time() * 1000)
    params = {
        "symbol": f"{symbol}USDT",
        "side": side,
        "type": order_type,
        "quantity": format_quantity(quantity, symbol),
        "timestamp": ts,
        "recvWindow": 5000
    }
    
    q = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    
    req = urllib.request.Request(url, method="POST")
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    
    try:
        resp = json.loads(opener.open(req, timeout=10).read().decode())
        if "code" in resp:
            return {"success": False, "error": f"{resp['code']}: {resp['msg']}"}
        return {"success": True, "order_id": resp.get("orderId"), "symbol": symbol}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ 主程序 ============

if __name__ == "__main__":
    g40 = G40()
    
    # 启动
    g40.run()
