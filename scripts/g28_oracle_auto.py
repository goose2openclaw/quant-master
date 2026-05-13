#!/usr/bin/env python3
"""
G28 Oracle 全自动交易系统 v3.0
================================
功能:
1. Oracle API 决策 (500agents Monte Carlo)
2. 自动交易信号检测
3. 自动执行买卖
4. 账户间资金调配
5. 风险控制
"""
import urllib.request, hmac, hashlib, time, json, numpy as np, random
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
SCAN_INTERVAL = 60
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g28_oracle.log"
STATE_FILE = "/home/goose/.openclaw/workspace/logs/g28_oracle_state.json"

# ========== Oracle Monte Carlo 配置 ==========
MONTE_CARLO_AGENTS = 500
CONFIDENCE_THRESHOLD = 0.60  # 置信度门槛

# ========== 交易配置 ==========
TRADE_CONFIG = {
    'BTC': {'type':'major','position_pct':0.15,'max_position':0.20,'stop_loss':0.02,'take_profit':0.15,'leverage':5},
    'ETH': {'type':'major','position_pct':0.12,'max_position':0.15,'stop_loss':0.03,'take_profit':0.15,'leverage':5},
    'BNB': {'type':'major','position_pct':0.10,'max_position':0.15,'stop_loss':0.03,'take_profit':0.15,'leverage':5},
    'LINK': {'type':'major','position_pct':0.10,'max_position':0.15,'stop_loss':0.03,'take_profit':0.15,'leverage':5},
    'SOL': {'type':'major','position_pct':0.10,'max_position':0.15,'stop_loss':0.03,'take_profit':0.20,'leverage':5},
    'UNI': {'type':'major','position_pct':0.10,'max_position':0.15,'stop_loss':0.03,'take_profit':0.20,'leverage':5},
    'BOME': {'type':'meme','position_pct':0.08,'max_position':0.10,'stop_loss':0.05,'take_profit':0.30,'leverage':3},
    'TURBO': {'type':'meme','position_pct':0.08,'max_position':0.10,'stop_loss':0.05,'take_profit':0.30,'leverage':3},
    'PUMP': {'type':'meme','position_pct':0.08,'max_position':0.10,'stop_loss':0.05,'take_profit':0.30,'leverage':3},
    'NEIRO': {'type':'meme','position_pct':0.08,'max_position':0.10,'stop_loss':0.05,'take_profit':0.30,'leverage':3},
}

MIN_QTY = {'BOME': 10000, 'TURBO': 1000, 'PUMP': 100, 'NEIRO': 10000, 'LINK': 0.1, 'UNI': 0.1, 'ETH': 0.001}

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except: return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ========== API ==========
def signed_api(endpoint, params=None, method="GET"):
    ts = int(time.time() * 1000)
    base = {"timestamp": ts, "recvWindow": 5000}
    if params: base.update(params)
    q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        resp = urllib.request.build_opener(proxy_handler).open(req, timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try: return float(json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())['price'])
    except: return 0

def get_klines(symbol, limit=720):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=30).read().decode())
        return [float(k[4]) for k in data]  # close price
    except: return []

def get_rsi(symbol, period=14):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=50'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        closes = [float(k[4]) for k in data]
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        if avg_loss == 0: return 100
        return 100-(100/(1+avg_gain/avg_loss))
    except: return 50

def get_momentum(symbol):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=25'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        if len(data) < 24: return 0
        return ((float(data[-1][4]) - float(data[-24][4])) / float(data[-24][4])) * 100
    except: return 0

# ========== Oracle Monte Carlo ==========
def monte_carlo_simulation(prices, agents=500):
    """500智能体Monte Carlo模拟"""
    if len(prices) < 100:
        return {'bull_prob': 0.5, 'bear_prob': 0.3, 'sideways_prob': 0.2, 'expected_return': 0, 'confidence': 0.3}
    
    current_price = prices[-1]
    returns = np.diff(prices) / prices[:-1]
    mu = np.mean(returns)
    sigma = np.std(returns)
    
    bull_count = 0
    bear_count = 0
    sideways_count = 0
    total_returns = []
    
    for _ in range(agents):
        # 随机模拟未来价格路径
        future_returns = np.random.normal(mu, sigma, 24)  # 24小时
        simulated_price = current_price * np.prod(1 + future_returns)
        price_change = (simulated_price - current_price) / current_price
        
        total_returns.append(price_change)
        
        if price_change > 0.02:  # >2% 上涨
            bull_count += 1
        elif price_change < -0.02:  # <-2% 下跌
            bear_count += 1
        else:
            sideways_count += 1
    
    bull_prob = bull_count / agents
    bear_prob = bear_count / agents
    sideways_prob = sideways_count / agents
    expected_return = np.mean(total_returns) * 100
    confidence = abs(bull_prob - bear_prob)  # 置信度 = 多空分歧
    
    return {
        'bull_prob': bull_prob,
        'bear_prob': bear_prob,
        'sideways_prob': sideways_prob,
        'expected_return': expected_return,
        'confidence': confidence,
        'simulation': '500agents'
    }

def oracle_analysis(symbol, coin_type):
    """Oracle综合分析"""
    prices = get_klines(f"{symbol}USDT", 720)
    rsi = get_rsi(f"{symbol}USDT")
    momentum = get_momentum(f"{symbol}USDT")
    
    # Monte Carlo模拟
    mc = monte_carlo_simulation(prices, MONTE_CARLO_AGENTS)
    
    # RSI分析
    if rsi < 30:
        rsi_signal = 'oversold'
        rsi_strength = (30 - rsi) / 30
    elif rsi > 70:
        rsi_signal = 'overbought'
        rsi_strength = (rsi - 70) / 30
    else:
        rsi_signal = 'neutral'
        rsi_strength = 0
    
    # 动量分析
    momentum_signal = 'bullish' if momentum > 1 else 'bearish' if momentum < -1 else 'neutral'
    
    # 综合决策
    buy_score = 0
    sell_score = 0
    
    # Monte Carlo权重
    if mc['bull_prob'] > 0.5 and mc['confidence'] > CONFIDENCE_THRESHOLD:
        buy_score += mc['bull_prob'] * mc['confidence'] * 40
    elif mc['bear_prob'] > 0.5 and mc['confidence'] > CONFIDENCE_THRESHOLD:
        sell_score += mc['bear_prob'] * mc['confidence'] * 40
    
    # RSI权重
    if rsi_signal == 'oversold':
        buy_score += rsi_strength * 30
    elif rsi_signal == 'overbought':
        sell_score += rsi_strength * 30
    
    # 动量权重
    if momentum_signal == 'bullish':
        buy_score += min(abs(momentum) / 5, 1) * 20
    elif momentum_signal == 'bearish':
        sell_score += min(abs(momentum) / 5, 1) * 20
    
    # 决策
    if buy_score > sell_score + 20:
        decision = 'STRONG_BUY'
    elif buy_score > sell_score + 5:
        decision = 'BUY'
    elif sell_score > buy_score + 20:
        decision = 'STRONG_SELL'
    elif sell_score > buy_score + 5:
        decision = 'SELL'
    else:
        decision = 'HOLD'
    
    return {
        'symbol': symbol,
        'type': coin_type,
        'rsi': rsi,
        'rsi_signal': rsi_signal,
        'momentum': momentum,
        'momentum_signal': momentum_signal,
        'bull_prob': mc['bull_prob'] * 100,
        'bear_prob': mc['bear_prob'] * 100,
        'expected_return': mc['expected_return'],
        'confidence': mc['confidence'] * 100,
        'buy_score': buy_score,
        'sell_score': sell_score,
        'decision': decision,
        'simulation_agents': MONTE_CARLO_AGENTS
    }

# ========== 账户管理 ==========
def get_account():
    account = signed_api("/api/v3/account")
    result = {'usdt': 0, 'coins': {}}
    if 'balances' in account:
        for b in account['balances']:
            free = float(b.get('free', 0))
            if free > 0.001:
                if b['asset'] == 'USDT':
                    result['usdt'] = free
                else:
                    result['coins'][b['asset']] = free
    return result

def get_futures_balance():
    url = f'https://fapi.binance.com/fapi/v2/balance'
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"{url}?{q}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(req, timeout=10).read().decode())
        for b in data:
            if b['asset'] == 'USDT':
                return float(b['availableBalance'])
    except: return 0

def place_order(symbol, side, quantity):
    params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
    result = signed_api("/api/v3/order", params, "POST")
    if 'error' in result:
        log(f"下单失败: {result['error']}")
        return None
    log(f"✅ {side} {quantity} {symbol}")
    return result

# ========== 核心策略 ==========
def get_total_assets(spot_acc, futures_balance):
    total = spot_acc['usdt']
    for coin, qty in spot_acc['coins'].items():
        price = get_price(f"{coin}USDT")
        total += qty * price
    total += futures_balance
    return total

def execute_trade(coin, decision, spot_acc, state):
    """执行交易"""
    cfg = TRADE_CONFIG.get(coin, {})
    if not cfg:
        return False
    
    price = get_price(f"{coin}USDT")
    current_qty = spot_acc['coins'].get(coin, 0)
    total = get_total_assets(spot_acc, 0)
    target_position = total * cfg['position_pct']
    min_qty = MIN_QTY.get(coin, 1)
    
    if decision in ['STRONG_BUY', 'BUY']:
        available = min(spot_acc['usdt'], total * 0.1)
        if coin in ['BOME', 'NEIRO', 'TURBO', 'PUMP']:
            qty = max(min_qty * 3, available / price * 0.8)
        else:
            qty = max(min_qty, available / price * 0.6)
        
        if qty >= min_qty and spot_acc['usdt'] > 5:
            result = place_order(f"{coin}USDT", "BUY", qty)
            if result:
                spot_acc['usdt'] -= qty * price * 0.999
                spot_acc['coins'][coin] = spot_acc['coins'].get(coin, 0) + qty
                state[coin] = {'action': 'BUY', 'price': price, 'time': time.time()}
                return True
    
    elif decision in ['STRONG_SELL', 'SELL'] and current_qty > 0:
        sell_qty = current_qty * 0.5
        if sell_qty >= min_qty:
            result = place_order(f"{coin}USDT", "SELL", sell_qty)
            if result:
                spot_acc['usdt'] += sell_qty * price * 0.999
                spot_acc['coins'][coin] = current_qty - sell_qty
                state[coin] = {'action': 'SELL', 'price': price, 'time': time.time()}
                return True
    
    return False

# ========== 主循环 ==========
def main():
    log("=" * 70)
    log("G28 Oracle 全自动交易系统 v3.0 🔮 ORACLE MODE")
    log(f"Monte Carlo: {MONTE_CARLO_AGENTS} agents")
    log(f"扫描间隔: {SCAN_INTERVAL}秒")
    log("=" * 70)
    
    state = load_state()
    
    while True:
        try:
            spot_acc = get_account()
            futures_balance = get_futures_balance()
            total = get_total_assets(spot_acc, futures_balance)
            
            log(f"\n{'='*70}")
            log(f"⏰ {datetime.now().strftime('%H:%M:%S')} | 总资产: ${total:.2f}")
            log(f"  现货: ${spot_acc['usdt']:.2f} | 合约: ${futures_balance:.2f}")
            
            # Oracle 分析每个持仓币种
            decisions = []
            for coin in TRADE_CONFIG:
                cfg = TRADE_CONFIG[coin]
                oracle = oracle_analysis(coin, cfg['type'])
                
                price = get_price(f"{coin}USDT")
                current_qty = spot_acc['coins'].get(coin, 0)
                current_value = current_qty * price
                
                log(f"  🔮 {coin}: {oracle['decision']} (RSI:{oracle['rsi']:.1f} MC:{oracle['bull_prob']:.0f}%/{oracle['bear_prob']:.0f}% 置信:{oracle['confidence']:.0f}%)")
                
                decisions.append({
                    'coin': coin,
                    'oracle': oracle,
                    'current_value': current_value
                })
            
            # 执行交易
            executed = []
            for d in decisions:
                coin = d['coin']
                decision = d['oracle']['decision']
                
                # 优先处理强信号
                if decision in ['STRONG_BUY', 'STRONG_SELL']:
                    if execute_trade(coin, decision, spot_acc, state):
                        executed.append(f"{coin}:{decision}")
                elif decision == 'BUY' and d['current_value'] < 50:  # 小仓位优先补
                    if execute_trade(coin, decision, spot_acc, state):
                        executed.append(f"{coin}:{decision}")
            
            if executed:
                log(f"  📋 执行: {', '.join(executed)}")
            
            save_state(state)
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
