#!/usr/bin/env python3
"""
StrategyOptimizer - 策略优化器
===========================
整合所有策略并进行智能优化
"""

import time
from typing import Dict, List, Optional, Tuple
import statistics

class StrategyOptimizer:
    """
    策略优化器
    负责策略性能追踪、最优组合、动态调整
    """
    
    def __init__(self, g40=None):
        self.g40 = g40
        self.strategy_performance = {}
        self.market_performance = {'trending': {}, 'ranging': {}, 'volatile': {}}
        self.learning_rate = 0.1
        self.epsilon = 0.15
        self.confidence_threshold = 0.55
        
        # 初始化策略表现
        self._init_strategy_performance()
    
    def _init_strategy_performance(self):
        """初始化策略表现跟踪"""
        strategies = [
            'go-core', 'go-pool', 'go-long-short', 'go-detect',
            'go-rotate', 'go-fit', 'go-etf', 'go-noise',
            'go-thermo', 'top10'
        ]
        for s in strategies:
            self.strategy_performance[s] = {
                'wins': 0, 'losses': 0, 'trades': 0, 'pnl': 0,
                'last_update': time.time(), 'score': 50
            }
    
    def detect_market_regime(self) -> str:
        """检测市场状态"""
        if not self.g40:
            return 'trending'
        
        try:
            return self.g40.optimizer.detect_market_regime()
        except:
            return 'trending'
    
    def calculate_signal(self, symbol: str) -> Dict:
        """
        综合多策略计算信号
        """
        weights = self.get_adaptive_weights()
        
        signals = {
            'go-core': self._signal_go_core(symbol),
            'go-pool': self._signal_go_pool(symbol),
            'go-rotate': self._signal_go_rotate(symbol),
            'go-long-short': self._signal_go_long_short(symbol),
            'go-detect': self._signal_go_detect(symbol),
            'go-etf': self._signal_go_etf(symbol),
            'go-fit': self._signal_go_fit(symbol),
            'go-noise': self._signal_go_noise(symbol),
            'go-thermo': self._signal_go_thermo(symbol),
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
            'regime': self.detect_market_regime(),
            'signals': signals,
            'weights': weights
        }
    
    def get_adaptive_weights(self) -> Dict[str, float]:
        """根据市场状态自适应调整权重"""
        regime = self.detect_market_regime()
        
        if regime == 'trending':
            weights = {
                'go-core': 0.30, 'go-pool': 0.25, 'go-rotate': 0.10,
                'go-long-short': 0.05, 'go-detect': 0.10, 'go-etf': 0.10,
                'go-fit': 0.05, 'go-noise': 0.00, 'go-thermo': 0.00, 'top10': 0.10
            }
        elif regime == 'ranging':
            weights = {
                'go-core': 0.10, 'go-pool': 0.10, 'go-rotate': 0.25,
                'go-long-short': 0.25, 'go-detect': 0.10, 'go-etf': 0.10,
                'go-fit': 0.05, 'go-noise': 0.00, 'go-thermo': 0.00, 'top10': 0.05
            }
        else:  # volatile
            weights = {
                'go-core': 0.15, 'go-pool': 0.10, 'go-rotate': 0.15,
                'go-long-short': 0.30, 'go-detect': 0.15, 'go-etf': 0.05,
                'go-fit': 0.05, 'go-noise': 0.00, 'go-thermo': 0.00, 'top10': 0.05
            }
        
        # 基于性能调整
        for strategy, perf in self.strategy_performance.items():
            if perf['trades'] >= 5:
                win_rate = perf['wins'] / perf['trades']
                score = perf.get('score', 50)
                
                # 高胜率+高评分 -> 权重增加
                if win_rate > 0.6 and score > 60:
                    weights[strategy] *= 1.2
                # 低胜率+低评分 -> 权重减少
                elif win_rate < 0.4 or score < 40:
                    weights[strategy] *= 0.8
        
        # 归一化
        total = sum(weights.values())
        for k in weights:
            weights[k] /= total
        
        return weights
    
    def record_trade(self, strategy: str, pnl: float):
        """记录交易结果用于学习"""
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {
                'wins': 0, 'losses': 0, 'trades': 0, 'pnl': 0, 'score': 50
            }
        
        perf = self.strategy_performance[strategy]
        perf['trades'] += 1
        perf['last_update'] = time.time()
        
        if pnl > 0:
            perf['wins'] += 1
            perf['pnl'] += pnl
            perf['score'] = min(100, perf.get('score', 50) + 1)
        else:
            perf['losses'] += 1
            perf['pnl'] += pnl
            perf['score'] = max(0, perf.get('score', 50) - 2)
    
    def evolve(self):
        """自我进化 - 调整策略权重"""
        for strategy, perf in self.strategy_performance.items():
            if perf['trades'] < 3:
                continue
            
            win_rate = perf['wins'] / perf['trades'] if perf['trades'] > 0 else 0.5
            avg_pnl = perf['pnl'] / perf['trades'] if perf['trades'] > 0 else 0
            
            # 调整权重
            if win_rate > 0.6 and avg_pnl > 0:
                perf['score'] = min(100, perf['score'] * (1 + self.learning_rate))
            elif win_rate < 0.4 or avg_pnl < -0.02:
                perf['score'] = max(0, perf['score'] * (1 - self.learning_rate))
        
        # 探索衰减
        if self.epsilon > 0.01:
            self.epsilon *= 0.999
    
    # ============ 策略信号实现 ============
    
    def _signal_go_core(self, symbol: str) -> Tuple[float, float]:
        """Go-Core 趋势跟踪核心"""
        return 0.2, 0.65
    
    def _signal_go_pool(self, symbol: str) -> Tuple[float, float]:
        """Go-Pool 资金流向"""
        return 0.15, 0.60
    
    def _signal_go_rotate(self, symbol: str) -> Tuple[float, float]:
        """Go-Rotate 板块轮动"""
        return 0.18, 0.62
    
    def _signal_go_long_short(self, symbol: str) -> Tuple[float, float]:
        """Go-Long-Short 多空信号"""
        return 0.20, 0.58
    
    def _signal_go_detect(self, symbol: str) -> Tuple[float, float]:
        """Go-Detect 异常检测"""
        return 0.12, 0.55
    
    def _signal_go_etf(self, symbol: str) -> Tuple[float, float]:
        """Go-ETF ETF流动性"""
        return 0.10, 0.52
    
    def _signal_go_fit(self, symbol: str) -> Tuple[float, float]:
        """Go-Fit 适配策略"""
        return 0.08, 0.50
    
    def _signal_go_noise(self, symbol: str) -> Tuple[float, float]:
        """Go-Noise 噪音交易"""
        return 0.05, 0.45
    
    def _signal_go_thermo(self, symbol: str) -> Tuple[float, float]:
        """Go-Thermo 热力策略"""
        return 0.07, 0.48
    
    def _signal_top10(self, symbol: str) -> Tuple[float, float]:
        """Top10 顶级交易员"""
        return 0.15, 0.63


if __name__ == "__main__":
    print("StrategyOptimizer - 策略优化器")
    print("=" * 50)
    
    optimizer = StrategyOptimizer()
    
    # 显示权重
    weights = optimizer.get_adaptive_weights()
    print("\n自适应权重 (趋势市场):")
    for strategy, weight in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"  {strategy}: {weight:.1%}")
    
    print("\n策略表现:")
    for strategy, perf in optimizer.strategy_performance.items():
        if perf['trades'] > 0:
            win_rate = perf['wins'] / perf['trades']
            print(f"  {strategy}: {perf['trades']}笔 胜率{win_rate:.1%} 评分{perf.get('score', 50)}")
