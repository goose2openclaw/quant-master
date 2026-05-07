#!/bin/bash
# Polymarket Mirofish 100智能体投资系统 v2
# 日期: 2026-05-07
# 修复: 添加代理支持

LOG_FILE="/tmp/polymarket_mirofish.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "Polymarket Mirofish $(date)"
echo "100智能体仿真投资系统"
echo "=========================================="

python3 << 'PYEOF'
import requests, json, time, random, math
from datetime import datetime
from collections import defaultdict

PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
POLYMARKET_API = "https://gamma-api.polymarket.com"

def get_polymarket_markets(limit=50):
    try:
        url = f"{POLYMARKET_API}/markets"
        params = {"limit": limit, "closed": "false", "orderBy": "volume24hr"}
        r = requests.get(url, params=params, proxies=PROXIES, timeout=15)
        if r.status_code == 200:
            return r.json()[:limit]
    except Exception as e:
        print(f"  API错误: {str(e)[:50]}")
    return None

def get_market_price(market_id):
    try:
        url = f"https://clob.polymarket.com/prices?market={market_id}"
        r = requests.get(url, proxies=PROXIES, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return float(data.get('price', 0.5)) if data else 0.5
    except: pass
    return 0.5

def generate_simulated_markets(n=30):
    topics = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AI", "Web3", "DeFi", "Layer2", "ETF", "Gold"]
    outcomes = ["YES", "NO", "UP", "DOWN", "APPROVE", "REJECT", ">$100K", "<$100K"]
    markets = []
    for i in range(n):
        topic = random.choice(topics)
        outcome = random.choice(outcomes)
        markets.append({
            'id': f'sim_{i}',
            'question': f"Will {topic} {outcome}?",
            'volume24hr': random.uniform(10000, 5000000),
            'liquidity': random.uniform(10000, 2000000),
            'outcomePrices': [random.uniform(0.2, 0.8), random.uniform(0.2, 0.8)]
        })
    return markets

class MirofishAgent:
    def __init__(self, agent_id, strategy):
        self.id = agent_id
        self.strategy = strategy
        self.capital = 1000
        self.wins = 0
        self.losses = 0
    
    def decide(self, markets):
        if not markets: return None
        if self.strategy == 'aggressive':
            return max(markets, key=lambda m: float(m.get('volume24hr',0)) * abs(0.5 - get_market_price(m.get('id',''))), default=None)
        elif self.strategy == 'conservative':
            filtered = [m for m in markets if 0.35 <= get_market_price(m.get('id','')) <= 0.65]
            return max(filtered, key=lambda m: float(m.get('liquidity',0)), default=None) if filtered else random.choice(markets)
        elif self.strategy == 'momentum':
            return max(markets, key=lambda m: float(m.get('volume24hr',0)), default=None)
        elif self.strategy == 'high_confidence':
            filtered = [m for m in markets if 0.4 <= get_market_price(m.get('id','')) <= 0.6]
            return max(filtered, key=lambda m: float(m.get('liquidity',0)), default=None) if filtered else random.choice(markets)
        else:
            return random.choice(markets)
    
    def trade(self, market):
        price = get_market_price(market.get('id',''))
        amount = random.uniform(20, 100)
        cost = amount * price
        if cost > self.capital: return
        prob = price
        result = random.random() < prob
        self.capital += amount - cost if result else -cost
        if result: self.wins += 1
        else: self.losses += 1

print("\n" + "="*60)
print("Polymarket Mirofish 100智能体投资系统")
print("="*60)

# 获取市场
print("\n【获取Polymarket市场】")
markets = get_polymarket_markets(30)

if not markets:
    print("  API不可用,使用模拟数据")
    markets = generate_simulated_markets(30)

print(f"  分析 {len(markets)} 个市场")
for m in markets[:3]:
    price = get_market_price(m.get('id',''))
    vol = float(m.get('volume24hr', 0))
    print(f"  • {m.get('question','')[:40]}...")
    print(f"    价格: {price:.2f} | 24h量: ${vol:,.0f}")

# Mirofish仿真
print("\n【100智能体仿真】")
strategies = ['aggressive']*25 + ['conservative']*25 + ['momentum']*20 + ['high_confidence']*15 + ['random']*15
agents = [MirofishAgent(i, strategies[i]) for i in range(100)]

for agent in agents:
    for _ in range(random.randint(3, 6)):
        m = agent.decide(markets)
        if m: agent.trade(m)
    
    total = agent.wins + agent.losses
    roi = (agent.capital - 1000) / 1000 * 100

# 分析结果
by_strat = defaultdict(list)
for a in agents:
    by_strat[a.strategy].append({'roi': (a.capital - 1000) / 1000 * 100, 'wins': a.wins, 'losses': a.losses})

print("\n【策略分析】")
for strat, res in sorted(by_strat.items(), key=lambda x: sum(r['roi'] for r in x[1])/len(x[1]), reverse=True):
    avg_roi = sum(r['roi'] for r in res) / len(res)
    wins = sum(r['wins'] for r in res)
    losses = sum(r['losses'] for r in res)
    wr = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0
    print(f"  {strat.upper():15}: ROI={avg_roi:+7.1f}%, WR={wr:5.1f}%")

print("\n" + "="*60)
PYEOF
