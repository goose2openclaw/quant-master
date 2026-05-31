"""
网格优化器 - 参数扫描
"""
from itertools import product
from concurrent.futures import ThreadPoolExecutor, as_completed

class GridOptimizer:
    """
    网格优化器 - 暴力参数扫描
    """
    def __init__(self, strategy_class, data, metric='total_return'):
        self.strategy_class = strategy_class
        self.data = data
        self.metric = metric
        self.results = []
    
    def add_param(self, name, values):
        """添加参数"""
        if not hasattr(self, 'param_grid'):
            self.param_grid = {}
        self.param_grid[name] = values
    
    def run(self, n_workers=4):
        """运行优化"""
        if not hasattr(self, 'param_grid'):
            print("[Optimizer] 无参数")
            return []
        
        # 生成参数组合
        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())
        combinations = list(product(*values))
        
        print(f"[Optimizer] 开始优化 {len(combinations)} 组参数...")
        
        # 并行回测
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {}
            for combo in combinations:
                params = dict(zip(keys, combo))
                future = executor.submit(self._backtest, params)
                futures[future] = params
            
            for i, future in enumerate(as_completed(futures)):
                params = futures[future]
                try:
                    result = future.result()
                    if result:
                        result['params'] = params
                        self.results.append(result)
                        print(f"[{i+1}/{len(combinations)}] {params} -> {result.get(self.metric, 0):.2f}")
                except Exception as e:
                    print(f"[Optimizer] Error: {e}")
        
        # 排序
        self.results.sort(key=lambda x: x.get(self.metric, 0), reverse=True)
        return self.results
    
    def _backtest(self, params):
        """单次回测"""
        try:
            strategy = self.strategy_class(**params)
            from backtest.engine import BacktestEngine
            engine = BacktestEngine()
            engine.set_strategy(strategy)
            stats = engine.run(self.data.get('symbol'), self.data.get('start'), 
                             self.data.get('end'), self.data.get('interval', '1m'))
            return stats
        except:
            return None
    
    def get_best(self, n=5):
        """获取最优参数"""
        return self.results[:n]
    
    def get_worst(self, n=5):
        """获取最差参数"""
        return self.results[-n:]

class GeneticOptimizer:
    """
    遗传算法优化器
    """
    def __init__(self, strategy_class, param_space, metric='total_return'):
        self.strategy_class = strategy_class
        self.param_space = param_space
        self.metric = metric
        self.population = []
        self.generations = 20
        self.pop_size = 20
        self.mutation_rate = 0.1
        self.crossover_rate = 0.7
    
    def _random_param(self):
        import random
        return {k: random.choice(v) for k, v in self.param_space.items()}
    
    def _mutate(self, params):
        import random
        if random.random() < self.mutation_rate:
            key = random.choice(list(self.param_space.keys()))
            params[key] = random.choice(self.param_space[key])
        return params
    
    def _crossover(self, p1, p2):
        import random
        child = {}
        for k in p1.keys():
            child[k] = p1[k] if random.random() < 0.5 else p2[k]
        return child
    
    def _fitness(self, params):
        """评估适应度"""
        try:
            strategy = self.strategy_class(**params)
            from backtest.engine import BacktestEngine
            engine = BacktestEngine()
            engine.set_strategy(strategy)
            stats = engine.run('BTCUSDT', '2024-01-01', '2024-12-31')
            return stats.get(self.metric, 0) if stats else 0
        except:
            return 0
    
    def run(self):
        """运行遗传优化"""
        import random
        print("[GA Optimizer] 开始优化...")
        
        # 初始化种群
        self.population = [self._random_param() for _ in range(self.pop_size)]
        
        best = None
        best_fitness = float('-inf')
        
        for gen in range(self.generations):
            # 评估
            fitnesses = [(p, self._fitness(p)) for p in self.population]
            fitnesses.sort(key=lambda x: x[1], reverse=True)
            
            if fitnesses[0][1] > best_fitness:
                best_fitness = fitnesses[0][1]
                best = fitnesses[0][0]
            
            print(f"[Gen {gen+1}/{self.generations}] Best: {best_fitness:.2f}")
            
            # 选择
            parents = [p for p, _ in fitnesses[:self.pop_size//2]]
            
            # 生成新一代
            new_pop = parents[:2]  # 保留最优
            while len(new_pop) < self.pop_size:
                if random.random() < self.crossover_rate and len(parents) >= 2:
                    p1, p2 = random.sample(parents, 2)
                    child = self._mutate(self._crossover(p1, p2))
                else:
                    child = self._mutate(random.choice(parents))
                new_pop.append(child)
            
            self.population = new_pop
        
        return {'best_params': best, 'best_fitness': best_fitness}
