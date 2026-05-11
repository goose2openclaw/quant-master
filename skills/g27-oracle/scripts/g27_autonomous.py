#!/usr/bin/env python3
"""
G27 自主迭代版 - Oracle全持仓管理
====================================
核心功能:
1. 全持仓扫描: 对所有持仓币种进行复盘 + Mirofish + Oracle
2. 分币种策略: 主流币和Meme币采取不同策略
3. 个性化策略: 每个币种有自己独特的参数
4. 差异化操作: 不同币种不同操作
5. Oracle决策: AI神谕决策系统

Heremes指令 (2026-05-11):
- 继续迭代G26
- 写入代码，放入heartbeat
- 形成G27
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime
import random

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 币种分类
MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI', 'BNB']
MEME_COINS = ['PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO']

# 每个币种的个性化策略
COIN_STRATEGIES = {
    # 主流币 - 稳健策略
    'BTC': {'type': 'major', 'oversold': 30, 'overbought': 75, 'stop': 0.02, 'take': 0.15, 'leverage': 5, 'position': 0.15, 'max_position': 0.20},
    'ETH': {'type': 'major', 'oversold': 40, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.12, 'max_position': 0.15},
    'SOL': {'type': 'major', 'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.20, 'leverage': 5, 'position': 0.10, 'max_position': 0.15},
    'DOGE': {'type': 'major', 'oversold': 40, 'overbought': 70, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.15, 'max_position': 0.20},
    'LINK': {'type': 'major', 'oversold': 35, 'overbought': 70, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.15, 'max_position': 0.15},
    'XRP': {'type': 'major', 'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10, 'max_position': 0.15},
    'ADA': {'type': 'major', 'oversold': 30, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10, 'max_position': 0.15},
    'AVAX': {'type': 'major', 'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10, 'max_position': 0.15},
    'DOT': {'type': 'major', 'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10, 'max_position': 0.15},
    'UNI': {'type': 'major', 'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.20, 'leverage': 5, 'position': 0.12, 'max_position': 0.15},
    'BNB': {'type': 'major', 'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10, 'max_position': 0.15},
    
    # Meme币 - 激进策略
    'PEPE': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'PENGU': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'BONK': {'type': 'meme', 'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'SHIB': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'TRUMP': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'PUMP': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'WIF': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'FLOKI': {'type': 'meme', 'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'NEIRO': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'VANA': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'PNUT': {'type': 'meme', 'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'BOME': {'type': 'meme', 'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.35, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'TURBO': {'type': 'meme', 'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'MEME': {'type': 'meme', 'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
    'KAITO': {'type': 'meme', 'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10},
}

MONTE_CARLO_AGENTS = 500

def api(url):
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return json.loads(opener.open(req, timeout=30).read().decode())
    except: return {}

def signed_api_post(endpoint, params=None):
    ts = int(time.time() * 1000)
    base_params = {"timestamp": ts}
    if params: base_params.update(params)
    q = "&".join(f"{k}={v}" for k, v in base_params.items())
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url, method='POST')
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: 
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except Exception as e: return {"error": str(e)}

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url)
    try: return float(json.loads(opener.open(req, timeout=10).read().decode())['price'])
    except: return 0

def klines(sym, limit=720):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url)
    try: return [float(k[4]) for k in json.loads(opener.open(req, timeout=30).read().decode())]
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

def get_account():
    """获取账户信息"""
    ts = int(time.time() * 1000)
    params = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except: return {}

def get_holdings():
    """获取持仓"""
    account = get_account()
    holdings = {}
    if 'balances' in account:
        for b in account['balances']:
            free = float(b.get('free', 0))
            if free > 0.001:
                holdings[b['asset']] = free
    return holdings

def review_coin(coin):
    """复盘单个币种"""
    strategy = COIN_STRATEGIES.get(coin)
    if not strategy:
        return None
    
    prices = klines(f"{coin}USDT", 720)
    if len(prices) < 500:
        return None
    
    # RSI计算
    rsi_vals = [calc_rsi(prices[i-50:i]) if i >= 50 else 50 for i in range(len(prices))]
    current_rsi = rsi_vals[-1]
    
    # 动量
    momentum_1h = (prices[-1] / prices[-2] - 1) * 100 if len(prices) >= 2 else 0
    momentum_24h = (prices[-1] / prices[-24] - 1) * 100 if len(prices) >= 24 else 0
    
    # 价格位置
    current_price = prices[-1]
    price_high_30d = max(prices[-720:])
    price_low_30d = min(prices[-720:])
    price_position = (current_price - price_low_30d) / (price_high_30d - price_low_30d) * 100 if price_high_30d != price_low_30d else 50
    
    return {
        'coin': coin,
        'rsi': current_rsi,
        'momentum_1h': momentum_1h,
        'momentum_24h': momentum_24h,
        'price_position': price_position,
        'strategy': strategy,
    }

def mirofish_simulation(coin, review_data):
    """Mirofish 500智能体仿真"""
    prices = klines(f"{coin}USDT", 720)
    if len(prices) < 500:
        return None
    
    rsi_vals = [calc_rsi(prices[i-50:i]) if i >= 50 else 50 for i in range(len(prices))]
    strategy = review_data['strategy']
    
    wins = 0
    total_return = 0
    simulation_results = []
    
    for agent in range(MONTE_CARLO_AGENTS):
        rsi_buy = random.randint(25, 40)
        rsi_sell = random.randint(65, 80)
        stop_loss = random.uniform(0.02, 0.08)
        take_profit = random.uniform(0.10, 0.40)
        
        position = None
        agent_return = 0
        agent_trades = 0
        
        for i in range(100, len(prices)):
            rsi = rsi_vals[i]
            
            if position is None:
                if rsi < rsi_buy:
                    position = prices[i]
            else:
                pnl = (prices[i] - position) / position
                if pnl <= -stop_loss or pnl >= take_profit or rsi > rsi_sell:
                    agent_return += pnl
                    agent_trades += 1
                    position = None
        
        if agent_trades > 0:
            wins += 1 if agent_return > 0 else 0
            total_return += agent_return
            simulation_results.append(agent_return)
    
    win_rate_sim = wins / MONTE_CARLO_AGENTS * 100
    avg_return_sim = total_return / MONTE_CARLO_AGENTS * 100
    
    simulation_results.sort()
    percentile_95 = simulation_results[int(len(simulation_results) * 0.95)] * 100 if simulation_results else 0
    
    return {
        'win_rate_sim': win_rate_sim,
        'avg_return_sim': avg_return_sim,
        'percentile_95': percentile_95,
    }

def oracle_decision(coin, review_data, simulation_data):
    """Oracle AI神谕决策系统"""
    rsi = review_data['rsi']
    momentum_24h = review_data['momentum_24h']
    strategy = review_data['strategy']
    win_rate_sim = simulation_data['win_rate_sim']
    percentile_95 = simulation_data['percentile_95']
    
    signal_strength = win_rate_sim
    confidence = percentile_95
    
    # Oracle决策矩阵
    if rsi < 25 and signal_strength > 90 and confidence > 40:
        action = 'STRONG_BUY'
    elif rsi < 30 and signal_strength > 75 and confidence > 30:
        action = 'BUY'
    elif rsi < strategy['oversold'] and signal_strength > 60 and confidence > 20:
        action = 'ADD'  # 加仓
    elif rsi >= 30 and rsi <= 50 and signal_strength > 50 and confidence > 10:
        action = 'HOLD'
    elif rsi > strategy['overbought'] and signal_strength > 60 and confidence > 10:
        action = 'REDUCE'  # 减仓
    elif rsi > 80 and signal_strength > 50 and confidence > 0:
        action = 'SELL'
    else:
        action = 'HOLD'
    
    return {
        'action': action,
        'signal_strength': signal_strength,
        'confidence': confidence,
        'rsi': rsi,
        'momentum_24h': momentum_24h,
    }

def execute_action(coin, action, review_data, current_price, holding_amount, usdt_balance):
    """执行操作"""
    strategy = review_data['strategy']
    
    if action == 'HOLD':
        return None
    
    symbol = f"{coin}USDT"
    
    if action in ['BUY', 'STRONG_BUY']:
        # 买入/加仓
        allocation = 100 if action == 'BUY' else 150
        if usdt_balance < allocation:
            allocation = usdt_balance * 0.8
        
        if allocation < 5:
            return None
        
        order = signed_api_post("/api/v3/order", {
            "symbol": symbol,
            "side": "BUY",
            "type": "MARKET",
            "quoteOrderQty": allocation
        })
        
        if 'orderId' in order:
            return f"BUY {order['executedQty']} {coin} @ ${current_price}"
        return f"BUY failed: {order.get('error', order)}"
    
    elif action == 'REDUCE':
        # 减仓50%
        quantity = holding_amount * 0.5
        if quantity < 10:
            return None
        
        order = signed_api_post("/api/v3/order", {
            "symbol": symbol,
            "side": "SELL",
            "type": "MARKET",
            "quantity": quantity
        })
        
        if 'orderId' in order:
            return f"REDUCE {quantity} {coin} @ ${current_price}"
        return f"REDUCE failed: {order.get('error', order)}"
    
    elif action == 'SELL':
        # 全部卖出
        quantity = holding_amount
        if quantity < 10:
            return None
        
        order = signed_api_post("/api/v3/order", {
            "symbol": symbol,
            "side": "SELL",
            "type": "MARKET",
            "quantity": quantity
        })
        
        if 'orderId' in order:
            return f"SELL {quantity} {coin} @ ${current_price}"
        return f"SELL failed: {order.get('error', order)}"
    
    return None

def run_cycle():
    """运行完整周期"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*70}")
    print(f"🌟 G27 Oracle全持仓管理 [{ts}]")
    print(f"{'='*70}")
    
    # 获取持仓
    holdings = get_holdings()
    print(f"\n持仓: {list(holdings.keys())}")
    
    if len(holdings) <= 1:
        print("⚠️ 无持仓或仅剩USDT")
        return
    
    # USDT余额
    usdt = holdings.get('USDT', 0)
    print(f"USDT: ${usdt:.2f}")
    
    # 获取所有持仓币种的价格
    prices = {}
    for coin in holdings.keys():
        if coin != 'USDT':
            prices[coin] = get_price(f"{coin}USDT")
    
    results = []
    
    print(f"\n{'='*70}")
    print("【Oracle 全持仓分析】")
    print("=" * 70)
    
    for coin in holdings.keys():
        if coin == 'USDT':
            continue
        
        current_price = prices.get(coin, 0)
        if current_price == 0:
            continue
        
        holding_amount = holdings[coin]
        holding_value = holding_amount * current_price
        
        # 1. 复盘
        review = review_coin(coin)
        if not review:
            continue
        
        # 2. Mirofish仿真
        simulation = mirofish_simulation(coin, review)
        if not simulation:
            continue
        
        # 3. Oracle决策
        oracle = oracle_decision(coin, review, simulation)
        
        strategy = review['strategy']
        coin_type = 'Meme' if strategy['type'] == 'meme' else 'Major'
        
        print(f"\n{'='*50}")
        print(f"📊 {coin} ({coin_type})")
        print(f"{'='*50}")
        print(f"  持仓: {holding_amount:.4f} = ${holding_value:.2f}")
        print(f"  RSI: {oracle['rsi']:.1f} (阈值: {strategy['oversold']}/{strategy['overbought']})")
        print(f"  24h动量: {oracle['momentum_24h']:+.2f}%")
        print(f"  仿真胜率: {oracle['signal_strength']:.1f}%")
        print(f"  置信度: {oracle['confidence']:+.2f}%")
        print(f"  决策: {oracle['action']}")
        
        # 4. 执行
        if oracle['action'] != 'HOLD':
            result = execute_action(coin, oracle['action'], review, current_price, holding_amount, usdt)
            if result:
                print(f"  执行: {result}")
                results.append({'coin': coin, 'action': oracle['action'], 'result': result})
                usdt = get_holdings().get('USDT', usdt)
    
    print(f"\n{'='*70}")
    print("【汇总】")
    print("=" * 70)
    print(f"处理币种: {len(holdings) - 1}")
    print(f"操作次数: {len(results)}")
    for r in results:
        print(f"  {r['coin']}: {r['action']} → {r['result']}")
    
    if not results:
        print("  无操作")
    
    return results

def main():
    print("G27 Oracle全持仓管理系统启动")
    print("=" * 70)
    run_cycle()

if __name__ == '__main__':
    main()
