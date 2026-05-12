#!/usr/bin/env python3
"""
go-reverse - 逆向仿真参数优化引擎
针对每个币种进行历史数据逆向拟合，生成专属参数集
"""
import math, json, time, random, urllib.request
from datetime import datetime, timedelta
from collections import defaultdict
import hmac, hashlib

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 默认参数范围
PARAM_RANGES = {
    'rsi_oversold': (20, 40),
    'rsi_overbought': (60, 80),
    'momentum_threshold': (0.01, 0.10),
    'stop_loss': (0.02, 0.10),
    'take_profit': (0.05, 0.30),
    'position_size': (0.05, 0.25),
    'ma_short': (5, 30),
    'ma_long': (20, 200),
    'atr_multiplier': (1.5, 3.0),
    'volume_threshold': (1.0, 3.0),
}

# 默认起始参数
DEFAULT_PARAMS = {
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'momentum_threshold': 0.05,
    'stop_loss': 0.05,
    'take_profit': 0.15,
    'position_size': 0.10,
    'ma_short': 20,
    'ma_long': 50,
    'atr_multiplier': 2.0,
    'volume_threshold': 1.5,
}

# ============================================
# Data Utilities
# ============================================
def api_get(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())

def get_klines(symbol, interval='1h', limit=500):
    try:
        return api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    except: return []

def get_price_data(coin, interval='1h', limit=500):
    klines = get_klines(f"{coin}USDT", interval, limit)
    data = []
    for k in klines:
        data.append({
            'time': k[0] // 1000,
            'open': float(k[1]),
            'high': float(k[2]),
            'low': float(k[3]),
            'close': float(k[4]),
            'volume': float(k[5])
        })
    return data

# ============================================
# Backtest Engine
# ============================================
class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, params):
        self.params = params
        
    def sma(self, closes, period):
        if len(closes) < period: return None
        return sum(closes[-period:]) / period
        
    def rsi(self, closes, period=14):
        if len(closes) < period + 1: return 50
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        if avg_loss == 0: return 100
        return 100-(100/(1+avg_gain/avg_loss))
        
    def momentum(self, closes, period=14):
        if len(closes) < period + 1: return 0
        return (closes[-1] - closes[-period-1]) / closes[-period-1]
        
    def atr(self, data, period=14):
        if len(data) < period + 1: return 0
        trs = []
        for i in range(1, min(len(data), period + 1)):
            tr = max(
                data[i]['high'] - data[i]['low'],
                abs(data[i]['high'] - data[i-1]['close']),
                abs(data[i]['low'] - data[i-1]['close'])
            )
            trs.append(tr)
        return sum(trs) / len(trs) if trs else 0
        
    def run(self, data):
        """运行回测"""
        if len(data) < 50:
            return self._default_result()
            
        closes = [d['close'] for d in data]
        highs = [d['high'] for d in data]
        lows = [d['low'] for d in data]
        volumes = [d['volume'] for d in data]
        
        p = self.params
        initial_capital = 10000
        capital = initial_capital
        position = 0
        trades = []
        wins = 0
        losses = 0
        max_dd = 0
        peak = initial_capital
        
        for i in range(50, len(data)):
            current_price = closes[i]
            rsi_val = self.rsi(closes[:i], 14)
            mom_val = self.momentum(closes[:i], 14)
            
            # 买入信号
            if position == 0:
                if rsi_val < p['rsi_oversold'] and mom_val < -p['momentum_threshold']:
                    position_size = capital * p['position_size']
                    position = position_size / current_price
                    entry_price = current_price
                    capital = capital - position_size
                    
            # 卖出信号
            elif position > 0:
                pnl_pct = (current_price - entry_price) / entry_price
                
                # 止损
                if pnl_pct < -p['stop_loss']:
                    capital = position * current_price
                    pnl = capital - initial_capital
                    trades.append({'pnl': pnl, 'win': pnl > 0})
                    if pnl > 0: wins += 1
                    else: losses += 1
                    position = 0
                    
                # 止盈
                elif pnl_pct > p['take_profit']:
                    capital = position * current_price
                    pnl = capital - initial_capital
                    trades.append({'pnl': pnl, 'win': pnl > 0})
                    if pnl > 0: wins += 1
                    else: losses += 1
                    position = 0
                    
            # 更新最大回撤
            if position > 0:
                current_value = capital + position * current_price
            else:
                current_value = capital
            peak = max(peak, current_value)
            dd = (peak - current_value) / peak * 100
            max_dd = max(max_dd, dd)
            
        # 计算结果
        final_capital = capital if position == 0 else capital + position * closes[-1]
        total_return = (final_capital - initial_capital) / initial_capital * 100
        trade_count = len(trades)
        win_rate = wins / trade_count * 100 if trade_count > 0 else 0
        
        # 计算夏普比率 (简化)
        if trades:
            returns = [t['pnl'] / initial_capital * 100 for t in trades]
            avg_return = sum(returns) / len(returns)
            std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 1
            sharpe = avg_return / std_return * math.sqrt(252) if std_return > 0 else 0
        else:
            sharpe = 0
            
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'trade_count': trade_count,
            'final_capital': final_capital,
            'wins': wins,
            'losses': losses
        }
        
    def _default_result(self):
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'trade_count': 0,
            'final_capital': 10000,
            'wins': 0,
            'losses': 0
        }

# ============================================
# Grid Search Optimizer
# ============================================
class GridSearchOptimizer:
    """网格搜索优化器"""
    
    def __init__(self, param_ranges):
        self.param_ranges = param_ranges
        self.step_size = {
            'rsi_oversold': 2,
            'rsi_overbought': 2,
            'momentum_threshold': 0.01,
            'stop_loss': 0.005,
            'take_profit': 0.02,
            'position_size': 0.02,
            'ma_short': 5,
            'ma_long': 10,
            'atr_multiplier': 0.25,
            'volume_threshold': 0.25,
        }
        
    def generate_grid(self):
        """生成参数网格"""
        keys = list(self.param_ranges.keys())
        ranges = [self.param_ranges[k] for k in keys]
        step_sizes = [self.step_size.get(k, 1) for k in keys]
        
        # 生成网格点
        grid = []
        for i in range(len(keys)):
            values = []
            start, end = ranges[i]
            step = step_sizes[i]
            val = start
            while val <= end + 0.0001:
                values.append(val)
                val += step
            grid.append(values)
            
        return keys, grid
        
    def optimize(self, data, target='max_sharpe'):
        """网格搜索优化"""
        keys, grid = self.generate_grid()
        
        best_score = float('-inf')
        best_params = DEFAULT_PARAMS.copy()
        results = []
        
        total_combinations = 1
        for g in grid:
            total_combinations *= len(g)
            
        print(f"  网格搜索: {total_combinations} 种组合")
        
        # 简化为随机采样 (全网格太慢)
        samples = min(500, total_combinations)
        for _ in range(samples):
            params = {}
            for i, key in enumerate(keys):
                values = grid[i]
                params[key] = random.choice(values)
                
            backtest = BacktestEngine(params)
            result = backtest.run(data)
            
            # 计算目标分数
            if target == 'max_sharpe':
                score = result['sharpe_ratio']
            elif target == 'max_return':
                score = result['total_return']
            elif target == 'min_dd':
                score = -result['max_drawdown']
            elif target == 'max_winrate':
                score = result['win_rate']
            else:  # balance
                score = (result['sharpe_ratio'] * 0.3 + 
                        result['total_return'] * 0.3 + 
                        (100 - result['max_drawdown']) * 0.2 +
                        result['win_rate'] * 0.2)
                        
            results.append({'params': params.copy(), 'result': result, 'score': score})
            
            if score > best_score:
                best_score = score
                best_params = params.copy()
                
        return best_params, best_score, results

# ============================================
# Genetic Optimizer
# ============================================
class GeneticOptimizer:
    """遗传算法优化器"""
    
    def __init__(self, param_ranges, population_size=50, generations=20):
        self.param_ranges = param_ranges
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = 0.2
        self.crossover_rate = 0.7
        
    def create_individual(self):
        """创建个体"""
        return {k: random.uniform(v[0], v[1]) for k, v in self.param_ranges.items()}
        
    def crossover(self, parent1, parent2):
        """交叉"""
        child = {}
        for k in parent1.keys():
            if random.random() < self.crossover_rate:
                child[k] = (parent1[k] + parent2[k]) / 2
            else:
                child[k] = parent1[k] if random.random() < 0.5 else parent2[k]
        return child
        
    def mutate(self, individual):
        """变异"""
        mutated = individual.copy()
        for k in mutated.keys():
            if random.random() < self.mutation_rate:
                min_val, max_val = self.param_ranges[k]
                range_size = max_val - min_val
                mutated[k] = mutated[k] + random.uniform(-0.1, 0.1) * range_size
                mutated[k] = max(min_val, min(max_val, mutated[k]))
        return mutated
        
    def optimize(self, data, target='max_sharpe'):
        """遗传优化"""
        # 初始化种群
        population = [self.create_individual() for _ in range(self.population_size)]
        
        best_params = None
        best_score = float('-inf')
        
        for gen in range(self.generations):
            # 评估
            scored = []
            for ind in population:
                backtest = BacktestEngine(ind)
                result = backtest.run(data)
                
                if target == 'max_sharpe':
                    score = result['sharpe_ratio']
                elif target == 'max_return':
                    score = result['total_return']
                elif target == 'min_dd':
                    score = -result['max_drawdown']
                else:
                    score = result['win_rate']
                    
                scored.append((ind, result, score))
                
                if score > best_score:
                    best_score = score
                    best_params = ind.copy()
                    
            # 排序选择
            scored.sort(key=lambda x: x[2], reverse=True)
            population = [ind for ind, _, _ in scored[:self.population_size//2]]
            
            # 生成新个体
            while len(population) < self.population_size:
                p1, p2 = random.sample(population[:10], 2)
                child = self.crossover(p1, p2)
                child = self.mutate(child)
                population.append(child)
                
            if gen % 5 == 0:
                print(f"  遗传进化: 第{gen+1}代, 最优分数={best_score:.3f}")
                
        return best_params, best_score, None

# ============================================
# Reverse Engine
# ============================================
class ReverseEngine:
    """逆向仿真参数优化引擎"""
    
    def __init__(self):
        self.param_sets = {}  # coin -> optimized params
        self.backtest_cache = {}  # coin -> data
        self.optimizer = GridSearchOptimizer(PARAM_RANGES)
        
    def load_data(self, coin, interval='1h', limit=500):
        """加载数据"""
        return get_price_data(coin, interval, limit)
        
    def optimize(self, coin, interval='1h', period='90d', 
                target='max_sharpe', method='grid'):
        """逆向优化"""
        print(f"\n🔄 逆向仿真优化: {coin}")
        print(f"  时间框架: {interval}")
        print(f"  回测周期: {period}")
        print(f"  优化目标: {target}")
        print(f"  优化方法: {method}")
        
        # 加载数据
        period_map = {'7d': 168, '30d': 720, '90d': 2160}
        limit = min(period_map.get(period, 720), 500)
        data = self.load_data(coin, interval, limit)
        
        if not data or len(data) < 100:
            print(f"  ❌ 数据不足")
            return None
            
        print(f"  📊 数据点数: {len(data)}")
        
        # 选择优化方法
        if method == 'genetic':
            opt = GeneticOptimizer(PARAM_RANGES, population_size=30, generations=15)
            best_params, best_score, _ = opt.optimize(data, target)
        else:  # grid
            best_params, best_score, _ = self.optimizer.optimize(data, target)
            
        # 验证结果
        backtest = BacktestEngine(best_params)
        result = backtest.run(data)
        
        # 存储
        self.param_sets[coin] = {
            'coin': coin,
            'timeframe': interval,
            'optimized_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'target': target,
            'method': method,
            'parameters': best_params,
            'backtest_results': result,
            'confidence': self._calculate_confidence(result)
        }
        
        # 输出结果
        print(f"\n  ✅ 优化完成!")
        print(f"  📈 收益率: {result['total_return']:+.2f}%")
        print(f"  📊 夏普比率: {result['sharpe_ratio']:.3f}")
        print(f"  📉 最大回撤: {result['max_drawdown']:.2f}%")
        print(f"  🎯 胜率: {result['win_rate']:.1f}%")
        print(f"  🔢 交易次数: {result['trade_count']}")
        
        return self.param_sets[coin]
        
    def _calculate_confidence(self, result):
        """计算置信度"""
        score = 0.5
        
        # 基于夏普
        if result['sharpe_ratio'] > 2:
            score += 0.2
        elif result['sharpe_ratio'] > 1:
            score += 0.1
            
        # 基于回撤
        if result['max_drawdown'] < 10:
            score += 0.15
        elif result['max_drawdown'] < 20:
            score += 0.1
            
        # 基于胜率
        if result['win_rate'] > 60:
            score += 0.1
        elif result['win_rate'] > 50:
            score += 0.05
            
        # 基于交易次数
        if result['trade_count'] > 20:
            score += 0.05
            
        return min(0.95, max(0.3, score))
        
    def batch_optimize(self, coins, interval='1h', period='90d', 
                       target='max_sharpe'):
        """批量优化"""
        results = {}
        for coin in coins:
            result = self.optimize(coin, interval, period, target)
            if result:
                results[coin] = result
            time.sleep(0.5)  # Rate limit
        return results
        
    def get_params(self, coin):
        """获取参数集"""
        return self.param_sets.get(coin, {}).get('parameters', DEFAULT_PARAMS)
        
    def get_result(self, coin):
        """获取完整结果"""
        return self.param_sets.get(coin)
        
    def get_all_params(self):
        """获取所有参数集"""
        return {coin: data['parameters'] for coin, data in self.param_sets.items()}
        
    def apply_params(self, coin, custom_params):
        """应用自定义参数"""
        params = custom_params if custom_params else self.get_params(coin)
        return BacktestEngine(params)

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-reverse - 逆向仿真参数优化")
        print("Usage:")
        print("  python reverse_engine.py optimize <coin> [interval] [period] [target]")
        print("  python reverse_engine.py batch <coin1,coin2,...> [interval]")
        print("  python reverse_engine.py params <coin>")
        sys.exit(1)
        
    cmd = sys.argv[1]
    engine = ReverseEngine()
    
    if cmd == 'optimize' and len(sys.argv) >= 3:
        coin = sys.argv[2].upper()
        interval = sys.argv[3] if len(sys.argv) > 3 else '1h'
        period = sys.argv[4] if len(sys.argv) > 4 else '90d'
        target = sys.argv[5] if len(sys.argv) > 5 else 'max_sharpe'
        
        engine.optimize(coin, interval, period, target)
        
    elif cmd == 'batch' and len(sys.argv) >= 3:
        coins = sys.argv[2].upper().split(',')
        interval = sys.argv[3] if len(sys.argv) > 3 else '1h'
        
        results = engine.batch_optimize(coins, interval)
        print(f"\n📊 批量优化完成: {len(results)} 个币种")
        
    elif cmd == 'params' and len(sys.argv) >= 3:
        coin = sys.argv[2].upper()
        params = engine.get_params(coin)
        if params:
            print(f"\n📋 {coin} 最优参数:")
            for k, v in params.items():
                print(f"  {k}: {v}")
        else:
            print(f"未找到 {coin} 的参数")
