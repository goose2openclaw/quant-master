#!/usr/bin/env python3
"""
G19 Ultra - 1000智能体演化系统 (优化版)
"""
import requests, numpy as np, time, hmac, hashlib, random, json
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
AGENTS = 1000
GENERATIONS = 10

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

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

class Agent:
    def __init__(self):
        self.genes = {
            'rsi_buy': random.randint(20, 45),
            'rsi_sell': random.randint(55, 80),
            'tp': round(random.uniform(0.05, 0.20), 3),
            'sl': round(random.uniform(0.02, 0.08), 3),
        }
        self.fitness = 0
    
    def crossover(self, other):
        child = Agent()
        for k in self.genes:
            child.genes[k] = random.choice([self.genes[k], other.genes[k]])
        return child
    
    def mutate(self):
        for k in self.genes:
            if random.random() < 0.2:
                if k == 'rsi_buy':
                    self.genes[k] = random.randint(20, 45)
                elif k == 'rsi_sell':
                    self.genes[k] = random.randint(55, 80)
                elif k in ['tp', 'sl']:
                    self.genes[k] = round(random.uniform(0.05, 0.20), 3)

def backtest(agent, prices):
    if len(prices) < 50: return 0
    capital = 100
    position = None
    
    for i in range(30, len(prices) - 1):
        rsi = calc_rsi(prices[:i+1])
        
        if position is None:
            if rsi < agent.genes['rsi_buy']:
                position = prices[i]
        else:
            pnl = (prices[i] - position) / position
            if pnl >= agent.genes['tp'] or pnl <= -agent.genes['sl'] or rsi > agent.genes['rsi_sell']:
                capital *= (1 + pnl)
                position = None
    
    return capital - 100

def main():
    print("=" * 70)
    print("G19 Ultra - 1000智能体演化系统")
    print(f"配置: {AGENTS}智能体 x {GENERATIONS}代 x {len(COINS)}币种")
    print("=" * 70)
    
    # 加载数据
    print("\n加载数据...")
    prices_data = {}
    for coin in COINS:
        prices = get_klines(f'{coin}USDT', 720)
        if prices:
            prices_data[coin] = prices
            print(f"  {coin}: {len(prices)}条")
    
    # 各币种演化
    results = {}
    for coin, prices in prices_data.items():
        print(f"\n{coin}: {AGENTS}智能体 x {GENERATIONS}代演化中...")
        agents = [Agent() for _ in range(AGENTS)]
        
        for gen in range(GENERATIONS):
            # 批量回测
            for a in agents:
                a.fitness = backtest(a, prices)
            
            # 排序
            agents.sort(key=lambda x: x.fitness, reverse=True)
            
            # 精英+繁殖
            survivors = agents[:50]
            new_agents = survivors.copy()
            while len(new_agents) < AGENTS:
                p1, p2 = random.sample(survivors[:20], 2)
                child = p1.crossover(p2)
                child.mutate()
                new_agents.append(child)
            agents = new_agents
            
            if gen % 2 == 0:
                print(f"  Gen {gen+1}: 最佳={agents[0].fitness:+.2f}%")
        
        best = agents[0]
        results[coin] = {'fitness': best.fitness, 'genes': best.genes}
        print(f"  最终: {best.fitness:+.2f}%")
    
    # 跨币种调配
    print("\n" + "=" * 70)
    print("【跨币种调配 (MiroFish)】")
    print("=" * 70)
    
    total = sum(max(0, r['fitness']) for r in results.values())
    if total == 0: total = 1
    
    allocations = {}
    for coin, r in sorted(results.items(), key=lambda x: -x[1]['fitness']):
        w = max(0, r['fitness']) / total
        allocations[coin] = w
        print(f"  {coin:6}: {w*100:5.1f}% | RSI {r['genes']['rsi_buy']}/{r['genes']['rsi_sell']} | TP {r['genes']['tp']*100:.0f}% | {r['fitness']:+.1f}%")
    
    # 保存结果
    output = {
        'results': results,
        'allocations': allocations,
        'timestamp': datetime.now().isoformat()
    }
    with open('/home/goose/.openclaw/workspace/logs/g19_1000_result.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n✅ G19 1000智能体演化完成!")

if __name__ == '__main__':
    main()
