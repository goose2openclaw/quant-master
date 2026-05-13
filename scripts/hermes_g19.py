#!/usr/bin/env python3
"""
G19 - 1000智能体演化系统 + MiroFish生态整合
核心: G18 Ultra回测引擎 + 1000 Agent仿真 + 自主跨币种调配
"""
import requests, numpy as np, time, hmac, hashlib, random, json
from datetime import datetime
from collections import defaultdict

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
GENERATIONS = 50  # 演化代数
AGENTS_PER_COIN = 1000  # 每币种智能体数量
TOP_SURVIVORS = 50  # 保留精英数

LOG_FILE = '/home/goose/.openclaw/workspace/logs/g19_evolution.log'

# ========== API ==========
def sign(params):
    params['recvWindow'] = 5000
    params['timestamp'] = int(time.time()*1000)
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + '&signature=' + sig

def api_get(url, params=None):
    try:
        params = params or {}
        r = requests.get(url + '?' + sign(params), headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return {}

def get_price(symbol):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(sym, limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [float(k[4]) for k in r.json()]
    except: return []

# ========== 技术指标 ==========
def calc_ema(prices, period):
    if len(prices) < period: return None
    ema = prices[0]
    smoothing = 2.0 / (period + 1)
    for p in prices[1:]:
        ema = (p - ema) * smoothing + ema
    return ema

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

# ========== 智能体类 ==========
class Agent:
    def __init__(self, coin, generation=0):
        self.coin = coin
        self.generation = generation
        self.fitness = 0
        
        # 随机基因 (参数)
        self.genes = {
            'rsi_buy': random.randint(20, 45),
            'rsi_sell': random.randint(55, 80),
            'ema_fast': random.randint(5, 20),
            'ema_slow': random.randint(20, 50),
            'tp': round(random.uniform(0.05, 0.20), 3),
            'sl': round(random.uniform(0.02, 0.08), 3),
            'position_size': round(random.uniform(0.1, 0.5), 2),
            'use_macd': random.choice([True, False]),
            'macd_weight': round(random.uniform(0.0, 0.3), 2),
        }
    
    def crossover(self, other):
        """交叉繁殖"""
        child = Agent(self.coin, self.generation + 1)
        for key in self.genes:
            child.genes[key] = random.choice([self.genes[key], other.genes[key]])
        return child
    
    def mutate(self, rate=0.2):
        """基因突变"""
        for key in self.genes:
            if random.random() < rate:
                if key in ['rsi_buy']:
                    child.genes[key] = random.randint(20, 45)
                elif key in ['rsi_sell']:
                    child.genes[key] = random.randint(55, 80)
                elif key in ['ema_fast']:
                    child.genes[key] = random.randint(5, 20)
                elif key in ['ema_slow']:
                    child.genes[key] = random.randint(20, 50)
                elif key in ['tp', 'sl', 'position_size', 'macd_weight']:
                    child.genes[key] = round(random.uniform(0.0, 0.3), 3)

# ========== 回测单币种 ==========
def backtest_agent(agent, prices):
    """回测单个智能体"""
    if len(prices) < 100:
        return 0
    
    capital = 100
    position = None
    entry_price = 0
    genes = agent.genes
    
    for i in range(50, len(prices) - 1):
        p = prices[:i+1]
        rsi = calc_rsi(p)
        ema_fast = calc_ema(p, genes['ema_fast'])
        ema_slow = calc_ema(p, genes['ema_slow'])
        
        if position is None:
            # 买入信号
            buy = rsi < genes['rsi_buy']
            if buy and ema_fast and ema_slow and ema_fast > ema_slow:
                position = prices[i]
                entry_price = prices[i]
        else:
            # 卖出信号
            pnl_pct = (prices[i] - entry_price) / entry_price
            if pnl_pct >= genes['tp'] or pnl_pct <= -genes['sl'] or rsi > genes['rsi_sell']:
                capital *= (1 + pnl_pct)
                position = None
    
    return capital - 100

# ========== 演化引擎 ==========
class EvolutionEngine:
    def __init__(self, coin, prices):
        self.coin = coin
        self.prices = prices
        self.agents = [Agent(coin) for _ in range(AGENTS_PER_COIN)]
        self.best_agent = None
        self.best_fitness = -999
        self.history = []
    
    def evaluate(self):
        """评估所有智能体"""
        for agent in self.agents:
            agent.fitness = backtest_agent(agent, self.prices)
        
        # 排序
        self.agents.sort(key=lambda a: a.fitness, reverse=True)
        
        # 记录最佳
        if self.agents[0].fitness > self.best_fitness:
            self.best_fitness = self.agents[0].fitness
            self.best_agent = Agent(self.coin)
            self.best_agent.genes = self.agents[0].genes.copy()
            self.best_agent.fitness = self.best_fitness
        
        return self.agents[0].fitness
    
    def evolve(self):
        """演化一代"""
        # 评估
        self.evaluate()
        
        # 精英保留
        survivors = self.agents[:TOP_SURVIVORS]
        
        # 生成新一代
        new_agents = survivors.copy()
        while len(new_agents) < AGENTS_PER_COIN:
            parent1, parent2 = random.sample(survivors[:20], 2)
            child = parent1.crossover(parent2)
            child.mutate(rate=0.3)
            new_agents.append(child)
        
        self.agents = new_agents
    
    def run(self, generations=GENERATIONS):
        """运行演化"""
        print(f"  开始演化 {self.coin} ({AGENTS_PER_COIN}智能体 x {generations}代)...")
        
        for gen in range(generations):
            self.evolve()
            
            if gen % 10 == 0 or gen == generations - 1:
                print(f"    Gen {gen+1}: 最佳收益={self.best_fitness:+.2f}%")
        
        return self.best_agent

# ========== 跨币种调配器 ==========
class CrossCoinAllocator:
    """MiroFish风格的跨币种调配"""
    
    def __init__(self, coin_agents):
        self.coin_agents = coin_agents  # 各币种最佳智能体
        self.allocation = {}  # 资金分配
        self.confidence = {}  # 信心指数
    
    def calculate_allocation(self, prices_data):
        """基于智能体表现和当前市场计算分配"""
        total_fitness = sum(a.fitness for a in self.coin_agents.values())
        if total_fitness <= 0:
            total_fitness = 1
        
        allocations = {}
        confidences = {}
        
        for coin, agent in self.coin_agents.items():
            prices = prices_data.get(coin, [])
            if len(prices) < 50:
                allocations[coin] = 0
                confidences[coin] = 0
                continue
            
            # 当前市场信号
            rsi = calc_rsi(prices)
            
            # 适应度权重
            fitness_weight = max(0, agent.fitness) / total_fitness
            
            # RSI调整
            if rsi < 35:
                rsi_signal = 1.5  # 超卖,加仓
            elif rsi < 45:
                rsi_signal = 1.2
            elif rsi > 65:
                rsi_signal = 0.5  # 超买,减仓
            elif rsi > 55:
                rsi_signal = 0.8
            else:
                rsi_signal = 1.0
            
            # 最终分配权重
            final_weight = fitness_weight * rsi_signal
            
            allocations[coin] = final_weight
            confidences[coin] = min(1.0, abs(agent.fitness) / 50) if agent.fitness > 0 else 0.5
        
        # 归一化
        total = sum(allocations.values())
        if total > 0:
            for coin in allocations:
                allocations[coin] /= total
        
        self.allocation = allocations
        self.confidence = confidences
        
        return allocations

# ========== G19主程序 ==========
def main():
    print("=" * 70)
    print("G19 - 1000智能体演化系统 + MiroFish生态整合")
    print("=" * 70)
    print(f"配置: {AGENTS_PER_COIN}智能体/币种 x {GENERATIONS}代演化")
    
    # 加载数据
    print("\n📊 加载市场数据...")
    prices_data = {}
    for coin in COINS:
        prices = get_klines(f'{coin}USDT', 720)
        if prices:
            prices_data[coin] = prices
            print(f"  {coin}: {len(prices)}条")
    
    # 各币种演化
    print("\n🔬 智能体演化中...")
    coin_agents = {}
    
    for coin in COINS:
        if coin not in prices_data:
            continue
        
        engine = EvolutionEngine(coin, prices_data[coin])
        best = engine.run(GENERATIONS)
        coin_agents[coin] = best
        
        print(f"  {coin}: 最佳收益 {best.fitness:+.2f}%")
        print(f"    RSI: {best.genes['rsi_buy']}/{best.genes['rsi_sell']}")
        print(f"    EMA: {best.genes['ema_fast']}/{best.genes['ema_slow']}")
        print(f"    TP/SL: {best.genes['tp']*100:.0f}%/{best.genes['sl']*100:.0f}%")
    
    # 跨币种调配
    print("\n🎯 跨币种调配 (MiroFish)")
    allocator = CrossCoinAllocator(coin_agents)
    allocations = allocator.calculate_allocation(prices_data)
    
    print("\n【资金分配】")
    for coin, weight in sorted(allocations.items(), key=lambda x: -x[1]):
        conf = allocator.confidence.get(coin, 0)
        agent = coin_agents.get(coin)
        fitness = agent.fitness if agent else 0
        print(f"  {coin:6}: {weight*100:5.1f}% (置信:{conf:.0%}, 历史收益:{fitness:+.1f}%)")
    
    # 保存结果
    result = {
        'coin_agents': {c: {'genes': a.genes, 'fitness': a.fitness} for c, a in coin_agents.items()},
        'allocations': allocations,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('/home/goose/.openclaw/workspace/logs/g19_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ G19演化完成! 结果已保存")
    
    # 当前信号
    print("\n【当前信号】")
    for coin, prices in prices_data.items():
        rsi = calc_rsi(prices)
        weight = allocations.get(coin, 0)
        conf = allocator.confidence.get(coin, 0)
        
        signal = 'BUY' if rsi < 35 and weight > 0.1 else 'SELL' if rsi > 65 else 'HOLD'
        emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
        
        print(f"  {emoji} {coin:6}: RSI={rsi:5.1f}, 分配={weight*100:5.1f}%, 置信={conf:.0%}")

if __name__ == '__main__':
    main()
