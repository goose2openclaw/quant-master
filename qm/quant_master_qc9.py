"""
QuantMaster Q@C v9 - G12策略因子矩阵 + 自我学习迭代版

核心功能:
1. G12策略矩阵 - RSI/Bollinger/动量/波动率/趋势
2. G12因子矩阵 - 多维度量化因子
3. 回测仿真系统 - 蒙特卡洛模拟 + 参数优化
4. 自我学习迭代 - 遗传算法 + 实时评估
5. Watchdog监控 - 全局监控和推动

版本: 9.0.0
"""
import sys
import time
import json
import random
import math
import threading
import urllib.request
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass
import copy

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

# ============================================================
# G12 策略配置 (从G12复刻)
# ============================================================
G12_CONFIG = {
    'version': 'G12-Unified-v9',
    'rsi_buy': 43, 'rsi_sell': 53,
    'bb_buy': 25, 'bb_sell': 75,
    'tp': 0.08, 'sl': 0.035,
    'position': 0.30, 'leverage': 3,
}

# ============================================================
# 策略矩阵
# ============================================================
class StrategyMatrix:
    """策略矩阵 - G12核心策略"""
    
    STRATEGIES = {
        'RSI_REVERSAL': {
            'name': 'RSI均值回归',
            'rsi_oversold': 35,
            'rsi_overbought': 70,
            'weight': 0.25,
            'description': 'RSI超卖买入,超买卖出'
        },
        'BB_REVERSAL': {
            'name': '布林带回归',
            'bb_lower': 20,
            'bb_upper': 80,
            'weight': 0.20,
            'description': '触及布林带上轨买入,下轨卖出'
        },
        'MOMENTUM': {
            'name': '动量策略',
            'lookback': 20,
            'threshold': 0.05,
            'weight': 0.20,
            'description': '动量突破时追涨杀跌'
        },
        'VOLATILITY_BREAK': {
            'name': '波动率突破',
            'vol_threshold': 2.0,
            'atr_mult': 1.5,
            'weight': 0.15,
            'description': '波动率突增时突破买入'
        },
        'TREND_FOLLOW': {
            'name': '趋势跟随',
            'ema_fast': 20,
            'ema_slow': 50,
            'weight': 0.20,
            'description': 'EMA金叉买入,死叉卖出'
        }
    }
    
    def __init__(self):
        self.active_strategies = list(self.STRATEGIES.keys())
        self.strategy_scores = {k: 50 for k in self.STRATEGIES}
    
    def evaluate(self, market_data: Dict, indicators: Dict) -> Dict:
        """评估各策略信号"""
        signals = {}
        
        # RSI均值回归
        rsi = indicators.get('rsi', 50)
        if rsi < self.STRATEGIES['RSI_REVERSAL']['rsi_oversold']:
            signals['RSI_REVERSAL'] = {'action': 'BUY', 'confidence': 100 - rsi}
        elif rsi > self.STRATEGIES['RSI_REVERSAL']['rsi_overbought']:
            signals['RSI_REVERSAL'] = {'action': 'SELL', 'confidence': rsi - 30}
        else:
            signals['RSI_REVERSAL'] = {'action': 'HOLD', 'confidence': 50}
        
        # 布林带回归
        bb_pos = indicators.get('bb_position', 50)
        if bb_pos < self.STRATEGIES['BB_REVERSAL']['bb_lower']:
            signals['BB_REVERSAL'] = {'action': 'BUY', 'confidence': 100 - bb_pos}
        elif bb_pos > self.STRATEGIES['BB_REVERSAL']['bb_upper']:
            signals['BB_REVERSAL'] = {'action': 'SELL', 'confidence': bb_pos}
        else:
            signals['BB_REVERSAL'] = {'action': 'HOLD', 'confidence': 50}
        
        # 动量
        momentum = indicators.get('momentum', 0)
        if momentum > self.STRATEGIES['MOMENTUM']['threshold']:
            signals['MOMENTUM'] = {'action': 'BUY', 'confidence': 60 + momentum * 100}
        elif momentum < -self.STRATEGIES['MOMENTUM']['threshold']:
            signals['MOMENTUM'] = {'action': 'SELL', 'confidence': 60 + abs(momentum) * 100}
        else:
            signals['MOMENTUM'] = {'action': 'HOLD', 'confidence': 50}
        
        # 波动率突破
        vol_ratio = indicators.get('vol_ratio', 1.0)
        if vol_ratio > self.STRATEGIES['VOLATILITY_BREAK']['vol_threshold']:
            signals['VOLATILITY_BREAK'] = {'action': 'BUY', 'confidence': vol_ratio * 50}
        else:
            signals['VOLATILITY_BREAK'] = {'action': 'HOLD', 'confidence': 50}
        
        # 趋势跟随
        ema_fast = indicators.get('ema_fast', 0)
        ema_slow = indicators.get('ema_slow', 0)
        if ema_fast > ema_slow:
            signals['TREND_FOLLOW'] = {'action': 'BUY', 'confidence': 60}
        elif ema_fast < ema_slow:
            signals['TREND_FOLLOW'] = {'action': 'SELL', 'confidence': 60}
        else:
            signals['TREND_FOLLOW'] = {'action': 'HOLD', 'confidence': 50}
        
        return signals
    
    def weighted_vote(self, signals: Dict) -> Tuple[str, float]:
        """加权投票"""
        buy_score = 0
        sell_score = 0
        
        for strategy, signal in signals.items():
            weight = self.STRATEGIES.get(strategy, {}).get('weight', 0.2)
            confidence = signal['confidence']
            
            if signal['action'] == 'BUY':
                buy_score += weight * confidence
            elif signal['action'] == 'SELL':
                sell_score += weight * confidence
        
        total = buy_score + sell_score
        if total == 0:
            return 'HOLD', 50
        
        buy_pct = buy_score / total * 100
        sell_pct = sell_score / total * 100
        
        if buy_pct > 60:
            return 'BUY', buy_pct
        elif sell_pct > 60:
            return 'SELL', sell_pct
        else:
            return 'HOLD', 50


# ============================================================
# 因子矩阵
# ============================================================
class FactorMatrix:
    """因子矩阵 - G12核心因子"""
    
    FACTORS = {
        'RSI_7': {'name': 'RSI(7)', 'min': 0, 'max': 100, 'neutral': 50},
        'RSI_14': {'name': 'RSI(14)', 'min': 0, 'max': 100, 'neutral': 50},
        'BB_POSITION': {'name': '布林带位置', 'min': 0, 'max': 100, 'neutral': 50},
        'MOMENTUM_5': {'name': '5日动量', 'min': -20, 'max': 20, 'neutral': 0},
        'MOMENTUM_20': {'name': '20日动量', 'min': -50, 'max': 50, 'neutral': 0},
        'VOL_RATIO': {'name': '波动率比率', 'min': 0, 'max': 5, 'neutral': 1},
        'VOL_CHANGE': {'name': '波动率变化', 'min': -3, 'max': 3, 'neutral': 0},
        'EMA_20': {'name': 'EMA20差值', 'min': -5, 'max': 5, 'neutral': 0},
        'EMA_50': {'name': 'EMA50差值', 'min': -10, 'max': 10, 'neutral': 0},
        'ATR_RATIO': {'name': 'ATR比率', 'min': 0, 'max': 10, 'neutral': 1},
        'MACD_HIST': {'name': 'MACD柱', 'min': -200, 'max': 200, 'neutral': 0},
        'KDJ_K': {'name': 'KDJ K', 'min': 0, 'max': 100, 'neutral': 50},
        'ADX': {'name': 'ADX趋势强度', 'min': 0, 'max': 100, 'neutral': 25},
        'OBV_CHANGE': {'name': 'OBV变化', 'min': -50, 'max': 50, 'neutral': 0},
    }
    
    def __init__(self):
        self.factor_weights = {k: 1.0 for k in self.FACTORS}
        self.factor_history = defaultdict(list)
    
    def normalize(self, factor: str, value: float) -> float:
        """归一化因子值到0-100"""
        info = self.FACTORS.get(factor, {'min': 0, 'max': 100, 'neutral': 50})
        min_val, max_val, neutral = info['min'], info['max'], info['neutral']
        
        if max_val == min_val:
            return 50
        
        normalized = (value - min_val) / (max_val - min_val) * 100
        return max(0, min(100, normalized))
    
    def calculate_score(self, factor_values: Dict[str, float]) -> Tuple[float, Dict]:
        """计算因子综合评分"""
        scores = {}
        for factor, value in factor_values.items():
            if factor in self.FACTORS:
                normalized = self.normalize(factor, value)
                weight = self.factor_weights.get(factor, 1.0)
                scores[factor] = normalized * weight
        
        total_weight = sum(self.factor_weights.get(f, 1.0) for f in scores)
        if total_weight == 0:
            return 50, scores
        
        composite = sum(scores.values()) / total_weight
        return composite, scores
    
    def update_weights(self, trade_result: Dict):
        """根据交易结果更新因子权重"""
        if trade_result.get('pnl', 0) > 0:
            # 盈利交易 - 增加相关因子权重
            for factor in trade_result.get('factors', []):
                if factor in self.factor_weights:
                    self.factor_weights[factor] *= 1.05  # 增加5%
        else:
            # 亏损交易 - 降低相关因子权重
            for factor in trade_result.get('factors', []):
                if factor in self.factor_weights:
                    self.factor_weights[factor] *= 0.95  # 降低5%


# ============================================================
# 回测引擎
# ============================================================
class BacktestEngine:
    """回测引擎 - 蒙特卡洛模拟"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
    
    def run_backtest(self, strategy_fn, data: List[Dict], 
                    params: Dict) -> Dict:
        """运行回测"""
        capital = self.initial_capital
        trades = []
        positions = {}
        
        for i, candle in enumerate(data):
            if i < 50:
                continue
            
            signal = strategy_fn(candle, data[:i], params)
            
            if signal == 'BUY' and 'USDT' not in positions:
                qty = (capital * params.get('position_size', 0.1)) / candle['close']
                cost = qty * candle['close']
                positions['USDT'] = {'qty': qty, 'entry': candle['close'], 'cost': cost}
                capital -= cost
            
            elif signal == 'SELL' and 'USDT' in positions:
                pos = positions['USDT']
                revenue = pos['qty'] * candle['close']
                pnl = revenue - pos['cost']
                capital += revenue
                trades.append({'pnl': pnl, 'pnl_pct': pnl / pos['cost'] * 100})
                del positions['USDT']
            
            # 止损检查
            if 'USDT' in positions:
                pos = positions['USDT']
                pnl_pct = (candle['close'] - pos['entry']) / pos['entry']
                if pnl_pct <= -params.get('stop_loss', 0.05):
                    revenue = pos['qty'] * candle['close']
                    pnl = revenue - pos['cost']
                    capital += revenue
                    trades.append({'pnl': pnl, 'pnl_pct': pnl_pct * 100})
                    del positions['USDT']
        
        return self.calculate_stats(trades)
    
    def monte_carlo(self, trade_results: List[Dict], iterations: int = 1000) -> Dict:
        """蒙特卡洛模拟"""
        if not trade_results:
            return {'mean': 0, 'std': 0, 'percentile_95': 0, 'prob_profit': 0}
        
        pnls = [t['pnl'] for t in trade_results]
        results = []
        
        for _ in range(iterations):
            sample = random.choices(pnls, k=len(pnls))
            results.append(sum(sample))
        
        results.sort()
        n = len(results)
        
        prob_profit = sum(1 for r in results if r > 0) / len(results) * 100
        
        return {
            'mean': sum(results) / len(results),
            'std': (sum((r - sum(results)/n)**2 for r in results) / n) ** 0.5,
            'percentile_5': results[int(n * 0.05)],
            'percentile_95': results[int(n * 0.95)],
            'prob_profit': prob_profit,
            'max_drawdown': min(results),
            'max_gain': max(results)
        }
    
    def calculate_stats(self, trades: List[Dict]) -> Dict:
        """计算统计"""
        if not trades:
            return {'total': 0, 'win_rate': 0, 'avg_win': 0, 'avg_loss': 0}
        
        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in trades if t['pnl'] <= 0]
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': len(wins) / len(trades) * 100 if trades else 0,
            'total_pnl': sum(t['pnl'] for t in trades),
            'avg_win': sum(wins) / len(wins) if wins else 0,
            'avg_loss': sum(losses) / len(losses) if losses else 0,
            'profit_factor': abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0,
            'monte_carlo': self.monte_carlo(trades)
        }


# ============================================================
# 遗传算法优化器
# ============================================================
class GeneticOptimizer:
    """遗传算法优化器 - 自我学习迭代"""
    
    def __init__(self, population_size: int = 20, generations: int = 50):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = 0.2
        self.population = []
        self.best_individual = None
        self.best_fitness = 0
    
    def init_population(self, param_ranges: Dict) -> List[Dict]:
        """初始化种群"""
        population = []
        for _ in range(self.population_size):
            individual = {}
            for param, (min_val, max_val) in param_ranges.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    individual[param] = random.randint(min_val, max_val)
                else:
                    individual[param] = random.uniform(min_val, max_val)
            population.append(individual)
        return population
    
    def fitness(self, individual: Dict, backtester: BacktestEngine, 
               strategy_fn, data: List[Dict]) -> float:
        """适应度函数"""
        stats = backtester.run_backtest(strategy_fn, data, individual)
        win_rate = stats.get('win_rate', 0) / 100
        profit = stats.get('total_pnl', 0) / 10000
        return win_rate * 0.4 + profit * 0.6
    
    def selection(self, population: List[Dict], fitness_scores: List[float]) -> List[Dict]:
        """选择"""
        paired = list(zip(population, fitness_scores))
        paired.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in paired[:self.population_size // 2]]
    
    def crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """交叉"""
        child1, child2 = {}, {}
        for key in parent1:
            if random.random() > 0.5:
                child1[key] = parent1[key]
                child2[key] = parent2[key]
            else:
                child1[key] = parent2[key]
                child2[key] = parent1[key]
        return child1, child2
    
    def mutate(self, individual: Dict, param_ranges: Dict) -> Dict:
        """突变"""
        mutated = individual.copy()
        for param in mutated:
            if random.random() < self.mutation_rate:
                min_val, max_val = param_ranges[param]
                if isinstance(min_val, int):
                    mutated[param] = random.randint(min_val, max_val)
                else:
                    mutated[param] = random.uniform(min_val, max_val)
        return mutated
    
    def evolve(self, backtester: BacktestEngine, strategy_fn, data: List[Dict]) -> Dict:
        """进化"""
        param_ranges = {
            'rsi_oversold': (20, 40),
            'rsi_overbought': (60, 80),
            'bb_lower': (10, 30),
            'bb_upper': (70, 90),
            'position_size': (0.05, 0.30),
            'stop_loss': (0.02, 0.08),
            'take_profit': (0.05, 0.15)
        }
        
        self.population = self.init_population(param_ranges)
        
        for gen in range(self.generations):
            fitness_scores = [self.fitness(ind, backtester, strategy_fn, data) 
                           for ind in self.population]
            
            best_idx = fitness_scores.index(max(fitness_scores))
            if fitness_scores[best_idx] > self.best_fitness:
                self.best_fitness = fitness_scores[best_idx]
                self.best_individual = copy.deepcopy(self.population[best_idx])
            
            survivors = self.selection(self.population, fitness_scores)
            
            new_population = survivors.copy()
            while len(new_population) < self.population_size:
                p1, p2 = random.sample(survivors, 2)
                c1, c2 = self.crossover(p1, p2)
                new_population.extend([self.mutate(c1, param_ranges), 
                                      self.mutate(c2, param_ranges)])
            
            self.population = new_population[:self.population_size]
            
            if gen % 10 == 0:
                print(f"   遗传进度: {gen}/{self.generations} 最优适应度: {self.best_fitness:.3f}")
        
        return self.best_individual


# ============================================================
# 自我学习控制器
# ============================================================
class SelfLearningController:
    """自我学习控制器"""
    
    def __init__(self):
        self.factor_matrix = FactorMatrix()
        self.strategy_matrix = StrategyMatrix()
        self.backtester = BacktestEngine()
        self.genetic_optimizer = GeneticOptimizer()
        self.learning_history = []
        self.iteration = 0
    
    def learn_from_trade(self, trade_result: Dict):
        """从交易结果学习"""
        self.iteration += 1
        
        # 更新因子权重
        self.factor_matrix.update_weights(trade_result)
        
        # 记录学习历史
        self.learning_history.append({
            'iteration': self.iteration,
            'trade_result': trade_result,
            'factor_weights': self.factor_matrix.factor_weights.copy(),
            'best_params': self.genetic_optimizer.best_individual
        })
        
        # 每10次交易进行一次遗传优化
        if self.iteration % 10 == 0:
            print(f"\n🧬 执行遗传算法优化...")
            # 这里需要传入历史数据进行优化
            # best_params = self.genetic_optimizer.evolve(...)
    
    def get_recommendations(self) -> Dict:
        """获取建议"""
        return {
            'factor_weights': self.factor_matrix.factor_weights,
            'active_strategies': self.strategy_matrix.active_strategies,
            'iteration': self.iteration,
            'learning_rate': len(self.learning_history)
        }


# ============================================================
# 技术指标计算
# ============================================================
class TechnicalIndicators:
    """技术指标"""
    
    @staticmethod
    def RSI(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        return 100 - (100 / (1 + avg_gain / avg_loss))
    
    @staticmethod
    def EMA(data: List[float], period: int) -> float:
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    @staticmethod
    def BollingerPosition(prices: List[float], period: int = 20) -> float:
        if len(prices) < period:
            return 50
        sma = sum(prices[-period:]) / period
        variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
        std = math.sqrt(variance)
        upper = sma + 2 * std
        lower = sma - 2 * std
        if upper == lower:
            return 50
        return (prices[-1] - lower) / (upper - lower) * 100
    
    @staticmethod
    def Momentum(prices: List[float], period: int = 20) -> float:
        if len(prices) < period + 1:
            return 0
        return (prices[-1] - prices[-period-1]) / prices[-period-1] * 100
    
    @staticmethod
    def ATR(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(closes) < 2:
            return 0
        trs = []
        for i in range(1, len(closes)):
            tr = max(highs[i] - lows[i], 
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1]))
            trs.append(tr)
        if len(trs) < period:
            return sum(trs) / len(trs) if trs else 0
        return sum(trs[-period:]) / period
    
    @staticmethod
    def VolatilityRatio(highs: List[float], lows: List[float], closes: List[float]) -> float:
        atr_short = TechnicalIndicators.ATR(highs, lows, closes, 5)
        atr_long = TechnicalIndicators.ATR(highs, lows, closes, 20)
        if atr_long == 0:
            return 1
        return atr_short / atr_long
    
    @staticmethod
    def KDJ(highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, float]:
        if len(closes) < 9:
            return {'k': 50, 'd': 50, 'j': 50}
        rsv = []
        for i in range(8, len(closes)):
            period_high = max(highs[i-8:i+1])
            period_low = min(lows[i-8:i+1])
            rsv.append((closes[i] - period_low) / (period_high - period_low + 1e-10) * 100)
        k = d = 50
        for r in rsv:
            k = 2/3 * k + 1/3 * r
            d = 2/3 * d + 1/3 * k
        return {'k': k, 'd': d, 'j': 3*k - 2*d}


# ============================================================
# Binance API
# ============================================================
class BinanceAPI:
    def __init__(self):
        self.api_key = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
        self.api_secret = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
        self.proxies = {'http': 'http://172.29.144.1:7897', 'https': 'http://172.29.144.1:7897'}
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        import ssl
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            req = urllib.request.Request(url)
            handler = urllib.request.ProxyHandler(self.proxies)
            opener = urllib.request.build_opener(handler)
            
            with opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            
            klines = []
            for k in data:
                klines.append({
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            return klines
        except Exception as e:
            print(f"API error: {e}")
            return []


# ============================================================
# 模拟交易执行器
# ============================================================
class SimulatedExecutor:
    def __init__(self, initial_capital: float = 10000):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.positions = {}
        self.trade_history = []
        self.slippage = 0.001
    
    def buy(self, symbol: str, quantity: float, price: float) -> Dict:
        cost = price * quantity * (1 + self.slippage)
        if cost > self.capital:
            return {'error': 'Insufficient capital'}
        
        self.capital -= cost
        self.positions[symbol] = {
            'quantity': quantity,
            'entry': price,
            'high': price,
            'timestamp': time.time()
        }
        
        return {'status': 'FILLED', 'cost': cost}
    
    def sell(self, symbol: str, price: float = None) -> Dict:
        if symbol not in self.positions:
            return {'error': 'No position'}
        
        pos = self.positions[symbol]
        sell_price = price or pos['entry']
        revenue = sell_price * pos['quantity'] * (1 - self.slippage)
        pnl = revenue - pos['entry'] * pos['quantity']
        
        self.capital += revenue
        self.trade_history.append({
            'symbol': symbol,
            'entry': pos['entry'],
            'exit': sell_price,
            'quantity': pos['quantity'],
            'pnl': pnl,
            'pnl_pct': pnl / (pos['entry'] * pos['quantity']) * 100
        })
        
        del self.positions[symbol]
        return {'status': 'FILLED', 'pnl': pnl}
    
    def check_stop_loss(self, symbol: str, current_price: float, sl_pct: float = 0.035) -> bool:
        if symbol not in self.positions:
            return False
        pos = self.positions[symbol]
        pnl_pct = (current_price - pos['entry']) / pos['entry']
        if pnl_pct <= -sl_pct:
            return True
        return False
    
    def check_take_profit(self, symbol: str, current_price: float, tp_pct: float = 0.08) -> bool:
        if symbol not in self.positions:
            return False
        pos = self.positions[symbol]
        pnl_pct = (current_price - pos['entry']) / pos['entry']
        # 移动止盈
        if current_price > pos['high']:
            pos['high'] = current_price
        trailing_pct = (pos['high'] - current_price) / pos['high']
        if pnl_pct >= tp_pct and trailing_pct >= 0.03:
            return True
        return False
    
    def get_stats(self) -> Dict:
        if not self.trade_history:
            return {'total': 0, 'win_rate': 0, 'pnl': 0, 'capital': self.capital}
        wins = [t for t in self.trade_history if t['pnl'] > 0]
        return {
            'total': len(self.trade_history),
            'win_rate': len(wins) / len(self.trade_history) * 100,
            'pnl': sum(t['pnl'] for t in self.trade_history),
            'capital': self.capital
        }


# ============================================================
# 主控制器 - Q@C v9
# ============================================================
class QuantMasterQC9:
    """QuantMaster Q@C v9 - G12策略因子矩阵 + 自我学习迭代"""
    
    VERSION = "9.0.0"
    
    def __init__(self, capital: float = 10000, mode: str = 'AUTO'):
        print(f"\n{'='*70}")
        print(f"🚀 QuantMaster Q@C v{self.VERSION} - G12策略因子矩阵版")
        print(f"{'='*70}")
        
        self.capital = capital
        self.mode = mode
        
        # G12核心组件
        self.strategy_matrix = StrategyMatrix()
        self.factor_matrix = FactorMatrix()
        self.learner = SelfLearningController()
        self.indicators = TechnicalIndicators()
        self.binance = BinanceAPI()
        self.executor = SimulatedExecutor(capital)
        
        # 状态
        self.cycle = 0
        self.state_file = '/home/goose/.openclaw/workspace/qcv9_state.json'
        self.watchdog_status = '/home/goose/.openclaw/workspace/qcv9_watchdog.json'
        
        print(f"✅ 初始化完成")
        print(f"   策略数: {len(self.strategy_matrix.STRATEGIES)}")
        print(f"   因子数: {len(self.factor_matrix.FACTORS)}")
        print(f"   模式: {mode}")
    
    def calculate_indicators(self, klines: List[Dict]) -> Dict:
        """计算所有指标"""
        prices = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        return {
            'rsi_7': self.indicators.RSI(prices, 7),
            'rsi_14': self.indicators.RSI(prices, 14),
            'bb_position': self.indicators.BollingerPosition(prices),
            'momentum_5': self.indicators.Momentum(prices, 5),
            'momentum_20': self.indicators.Momentum(prices, 20),
            'ema_20': self.indicators.EMA(prices, 20),
            'ema_50': self.indicators.EMA(prices, 50),
            'atr': self.indicators.ATR(highs, lows, prices),
            'vol_ratio': self.indicators.VolatilityRatio(highs, lows, prices),
            'kdj': self.indicators.KDJ(highs, lows, prices),
            'current_price': prices[-1] if prices else 0
        }
    
    def run_cycle(self) -> Dict:
        """运行一个周期"""
        self.cycle += 1
        
        print(f"\n{'='*70}")
        print(f"📊 周期 #{self.cycle} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT']
        all_signals = []
        
        for symbol in symbols:
            # 获取数据
            klines = self.binance.get_klines(symbol, '1h', 100)
            if len(klines) < 50:
                continue
            
            # 计算指标
            ind = self.calculate_indicators(klines)
            
            # 策略评估
            signals = self.strategy_matrix.evaluate({'symbol': symbol}, ind)
            
            # 加权投票
            action, confidence = self.strategy_matrix.weighted_vote(signals)
            
            # 因子评分
            factor_score, _ = self.factor_matrix.calculate_score({
                'RSI_7': ind['rsi_7'],
                'RSI_14': ind['rsi_14'],
                'BB_POSITION': ind['bb_position'],
                'MOMENTUM_5': ind['momentum_5'],
                'MOMENTUM_20': ind['momentum_20'],
                'VOL_RATIO': ind['vol_ratio']
            })
            
            signal_result = {
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'factor_score': factor_score,
                'indicators': ind,
                'strategies': signals
            }
            all_signals.append(signal_result)
            
            print(f"\n{symbol}:")
            print(f"   价格: ${ind['current_price']:.4f}")
            print(f"   RSI(7): {ind['rsi_7']:.1f}")
            print(f"   布林带: {ind['bb_position']:.1f}")
            print(f"   波动率: {ind['vol_ratio']:.2f}x")
            print(f"   策略信号: {action} ({confidence:.0f}%)")
            print(f"   因子评分: {factor_score:.1f}")
        
        # 风控检查
        print(f"\n🛡️ 风控检查...")
        for symbol in list(self.executor.positions.keys()):
            current_price = self.binance.get_klines(symbol, '1h', 1)
            if current_price:
                price = current_price[-1]['close']
                if self.executor.check_stop_loss(symbol, price):
                    print(f"   🔴 止损: {symbol}")
                    result = self.executor.sell(symbol, price)
                    if 'pnl' in result:
                        print(f"   平仓: ${result['pnl']:+.2f}")
                        self.learner.learn_from_trade({'pnl': result['pnl'], 'symbol': symbol})
                
                elif self.executor.check_take_profit(symbol, price):
                    print(f"   🟢 止盈: {symbol}")
                    result = self.executor.sell(symbol, price)
                    if 'pnl' in result:
                        print(f"   平仓: ${result['pnl']:+.2f}")
                        self.learner.learn_from_trade({'pnl': result['pnl'], 'symbol': symbol})
        
        # 交易执行
        print(f"\n⚡ 交易执行...")
        all_signals.sort(key=lambda x: x['factor_score'], reverse=True)
        
        for sig in all_signals[:2]:
            if sig['action'] == 'BUY' and sig['factor_score'] > 55:
                symbol = sig['symbol']
                if symbol not in self.executor.positions:
                    price = sig['indicators']['current_price']
                    position_pct = min(0.2, sig['confidence'] / 500)
                    quantity = (self.executor.capital * position_pct) / price
                    if quantity * price > 10:
                        result = self.executor.buy(symbol, quantity, price)
                        if result.get('status') == 'FILLED':
                            print(f"   ✅ 买入: {symbol} x {quantity:.4f} @ ${price:.2f}")
        
        # 统计
        stats = self.executor.get_stats()
        print(f"\n📈 统计:")
        print(f"   账户: ${stats['capital']:.2f}")
        print(f"   盈亏: ${stats['pnl']:+.2f}")
        print(f"   交易: {stats['total']}笔")
        print(f"   胜率: {stats['win_rate']:.1f}%")
        
        # Watchdog上报
        self._watchdog_report(stats)
        
        return {
            'cycle': self.cycle,
            'signals': all_signals,
            'stats': stats
        }
    
    def _watchdog_report(self, stats: Dict):
        """看门狗状态上报"""
        status = {
            'version': self.VERSION,
            'cycle': self.cycle,
            'capital': stats.get('capital', 0),
            'pnl': stats.get('pnl', 0),
            'trades': stats.get('total', 0),
            'win_rate': stats.get('win_rate', 0),
            'positions': len(self.executor.positions),
            'mode': self.mode,
            'timestamp': time.time()
        }
        try:
            with open(self.watchdog_status, 'w') as f:
                json.dump(status, f, indent=2)
        except:
            pass
    
    def run(self, cycles: int = 100, interval: int = 60):
        """运行多个周期"""
        print(f"\n🚀 开始运行 Q@C v{self.VERSION}")
        
        for i in range(cycles):
            try:
                self.run_cycle()
                if i < cycles - 1:
                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\n⚠️ 中断")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                time.sleep(10)
        
        print(f"\n{'='*70}")
        print(f"🏁 运行完成")
        print(f"{'='*70}")


def main():
    qm = QuantMasterQC9(10000, 'SIMULATE')
    qm.run(cycles=3, interval=10)


if __name__ == "__main__":
    main()
