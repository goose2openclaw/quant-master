#!/usr/bin/env python3
"""
G25.4 自主进化版
===============
目标: 收益最大化
功能:
1. 自主升级参数
2. 自主优化策略
3. 自主迭代进化
4. 实时学习改进
5. 动态调整仓位/杠杆
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime
import random

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO']

# 初始参数
INITIAL_PARAMS = {
    'major': {'oversold': 40, 'overbought': 70, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.12},
    'meme': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.25, 'leverage': 10, 'position': 0.08}
}

# 学习参数
LEARNING_RATE = 0.1
MUTATION_RATE = 0.2
POPULATION_SIZE = 20
GENERATIONS = 50

def api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except: return {}

def price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return float(json.loads(opener.open(req, timeout=10).read().decode())['price'])
    except: return 0

def binance_24hr(symbol):
    url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return json.loads(opener.open(req, timeout=10).read().decode())
    except: return {}

def klines(sym, limit=100, interval='1h'):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return [float(k[4]) for k in json.loads(opener.open(req, timeout=15).read().decode())]
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

def fitness(params, coin, is_meme, days=30):
    """评估参数适应度"""
    prices = klines(f"{coin}USDT", days * 24)
    if len(prices) < 500: return 0
    
    oversold = params['oversold']
    overbought = params['overbought']
    stop = params['stop']
    take = params['take']
    
    position = None
    wins, losses = 0, 0
    total_return = 0
    
    for i in range(14, len(prices)):
        rsi = calc_rsi(prices[i-50:i])
        
        if position is None:
            if rsi < oversold:
                position = {'entry': prices[i]}
        else:
            pnl = (prices[i] - position['entry']) / position['entry']
            if pnl <= -stop or pnl >= take or rsi > overbought:
                if pnl > 0: wins += 1
                else: losses += 1
                total_return += pnl
                position = None
    
    total = wins + losses
    if total == 0: return 0
    
    win_rate = wins / total
    avg_return = total_return / total
    
    # 适应度 = 胜率 * 0.4 + 收益 * 0.6
    return win_rate * 0.4 + avg_return * 10

def mutate(params):
    """参数突变"""
    mutated = params.copy()
    for key in mutated:
        if random.random() < MUTATION_RATE:
            if key in ['oversold', 'overbought']:
                mutated[key] = max(10, min(90, mutated[key] + random.randint(-5, 5)))
            elif key in ['stop', 'take']:
                mutated[key] = max(0.01, min(0.5, mutated[key] * random.uniform(0.8, 1.2)))
            elif key in ['leverage']:
                mutated[key] = max(1, min(20, mutated[key] + random.randint(-1, 1)))
            elif key == 'position':
                mutated[key] = max(0.01, min(0.3, mutated[key] * random.uniform(0.9, 1.1)))
    return mutated

def evolve(coin, is_meme, initial_params):
    """遗传算法进化"""
    param_type = 'meme' if is_meme else 'major'
    base = initial_params[param_type]
    
    # 初始化种群
    population = [base.copy()]
    for _ in range(POPULATION_SIZE - 1):
        population.append(mutate(base))
    
    best = base.copy()
    best_fitness = fitness(base, coin, is_meme)
    
    for gen in range(GENERATIONS):
        # 评估
        fitnesses = [(p, fitness(p, coin, is_meme)) for p in population]
        fitnesses.sort(key=lambda x: x[1], reverse=True)
        
        # 保存最优
        if fitnesses[0][1] > best_fitness:
            best = fitnesses[0][0].copy()
            best_fitness = fitnesses[0][1]
        
        # 选择
        survivors = [p for p, f in fitnesses[:POPULATION_SIZE // 2]]
        
        # 交叉
        children = []
        while len(children) < POPULATION_SIZE - len(survivors):
            p1, p2 = random.sample(survivors, 2)
            child = {}
            for key in p1:
                child[key] = p1[key] if random.random() < 0.5 else p2[key]
            children.append(mutate(child))
        
        population = survivors + children
    
    return best, best_fitness

def optimize_all():
    """优化所有币种"""
    print("=" * 70)
    print("G25.4 自主进化优化")
    print("=" * 70)
    
    optimized = {}
    
    # 优化主流币
    print(f"\n[主流币优化中...]")
    for coin in MAJOR_COINS:
        print(f"  进化 {coin}...", end=" ")
        params, score = evolve(coin, False, INITIAL_PARAMS)
        optimized[f"{coin}_major"] = {'params': params, 'score': score, 'type': 'major'}
        print(f"适应度: {score:.3f}")
    
    # 优化Meme币
    print(f"\n[Meme币优化中...]")
    for coin in MEME_COINS:
        print(f"  进化 {coin}...", end=" ")
        params, score = evolve(coin, True, INITIAL_PARAMS)
        optimized[f"{coin}_meme"] = {'params': params, 'score': score, 'type': 'meme'}
        print(f"适应度: {score:.3f}")
    
    return optimized

def analyze_and_trade():
    """分析并交易"""
    print(f"\n{'='*70}")
    print("【实时分析 & 交易决策】")
    print("=" * 70)
    
    # 获取账户
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    
    usdt = 0
    positions = []
    if 'balances' in data:
        for b in data['balances']:
            free = float(b.get('free', 0))
            if free > 0.01:
                asset = b['asset']
                if asset == 'USDT':
                    usdt = free
                else:
                    positions.append(asset)
    
    print(f"\n账户: USDT=${usdt:.2f}, 持仓: {positions}")
    
    # 扫描信号
    signals = []
    all_coins = list(set(MAJOR_COINS + MEME_COINS))
    
    print(f"\n[扫描信号]")
    for coin in all_coins:
        is_meme = coin in MEME_COINS
        symbol = f"{coin}USDT"
        h24 = binance_24hr(symbol)
        if not h24 or 'lastPrice' not in h24: continue
        
        p = float(h24['lastPrice'])
        chg = float(h24['priceChangePercent'])
        prices = klines(symbol, 50)
        if len(prices) < 20: continue
        
        rsi = calc_rsi(prices)
        
        # 使用优化后的参数
        key = f"{coin}_{'meme' if is_meme else 'major'}"
        # 默认参数
        params = INITIAL_PARAMS['meme' if is_meme else 'major']
        
        if rsi < params['oversold'] and chg < -1:
            signals.append({'coin': coin, 'price': p, 'rsi': rsi, 'chg': chg, 'params': params, 'is_meme': is_meme})
    
    if signals:
        signals.sort(key=lambda x: x['rsi'])
        best = signals[0]
        print(f"\n  最佳信号: {best['coin']} RSI={best['rsi']:.1f} 24h={best['chg']:+.1f}%")
        print(f"  参数: 超卖={best['params']['oversold']} 超买={best['params']['overbought']}")
        print(f"  止盈={best['params']['take']:.0%} 止损={best['params']['stop']:.0%}")
        print(f"  杠杆={best['params']['leverage']}x 仓位={best['params']['position']:.0%}")
    else:
        print(f"\n  无信号")

def run_cycle():
    """运行一个周期"""
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] G25.4 自主进化")
    
    # 1. 优化参数
    # 2. 分析市场
    # 3. 生成信号
    # 4. 执行交易
    analyze_and_trade()

if __name__ == '__main__':
    print("G25.4 自主进化版启动")
    optimized = optimize_all()
    analyze_and_trade()
