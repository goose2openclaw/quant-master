#!/usr/bin/env python3
"""
G28 全自动交易系统 v2.0
========================
功能:
1. 自动交易信号检测
2. 自动执行买卖
3. 账户间资金调配
4. 风险控制
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
SCAN_INTERVAL = 60
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g28_auto_trades.log"
STATE_FILE = "/home/goose/.openclaw/workspace/logs/g28_auto_state.json"

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

# 最小下单量
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

# ========== 账户管理 ==========
def get_account():
    """获取现货账户"""
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
    """获取合约账户"""
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

def transfer_to_futures(amount):
    """转入合约"""
    params = {"asset": "USDT", "amount": amount, "type": 1}
    result = signed_api("/sapi/v1/asset/transfer", params, "POST")
    if 'error' in result:
        log(f"转入合约失败: {result['error']}")
        return False
    log(f"✅ 转入合约 ${amount:.2f}")
    return True

def transfer_to_spot(amount):
    """转出现货"""
    params = {"asset": "USDT", "amount": amount, "type": 2}
    result = signed_api("/sapi/v1/asset/transfer", params, "POST")
    if 'error' in result:
        log(f"转出现货失败: {result['error']}")
        return False
    log(f"✅ 转出现货 ${amount:.2f}")
    return True

# ========== 交易执行 ==========
def place_order(symbol, side, quantity):
    """下单"""
    params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
    result = signed_api("/api/v3/order", params, "POST")
    if 'error' in result:
        log(f"下单失败: {result['error']}")
        return None
    log(f"✅ {side} {quantity} {symbol}")
    return result

# ========== 核心策略 ==========
def oracle_decision(rsi, momentum, coin_type):
    """Oracle决策"""
    buy_thresh = 35 if coin_type == "meme" else 40
    sell_thresh = 75 if coin_type == "meme" else 70
    
    if rsi < buy_thresh and momentum < -2: return "STRONG_BUY"
    if rsi < buy_thresh: return "BUY"
    if rsi > sell_thresh and momentum > 3: return "STRONG_SELL"
    if rsi > sell_thresh - 5: return "SELL"
    return "HOLD"

def get_total_assets(spot_acc, futures_balance):
    """计算总资产"""
    total = spot_acc['usdt']
    for coin, qty in spot_acc['coins'].items():
        price = get_price(f"{coin}USDT")
        total += qty * price
    total += futures_balance
    return total

def auto_trade(spot_acc, futures_balance, state):
    """自动交易"""
    executed = []
    
    for coin, cfg in TRADE_CONFIG.items():
        try:
            rsi = get_rsi(f"{coin}USDT")
            momentum = get_momentum(f"{coin}USDT")
            price = get_price(f"{coin}USDT")
            decision = oracle_decision(rsi, momentum, cfg['type'])
            
            current_qty = spot_acc['coins'].get(coin, 0)
            current_value = current_qty * price
            total = get_total_assets(spot_acc, futures_balance)
            target_position = total * cfg['position_pct']
            
            log(f"  {coin}: {decision} (RSI:{rsi:.1f} 动量:{momentum:+.2f}% 持仓:${current_value:.2f})")
            
            # 买入信号
            if decision in ['STRONG_BUY', 'BUY'] and current_value < target_position:
                min_qty = MIN_QTY.get(coin, 1)
                available = min(spot_acc['usdt'], total * 0.1)  # 最多用10%
                
                if coin in ['BOME', 'NEIRO', 'TURBO', 'PUMP']:
                    qty = max(min_qty * 5, available / price * 0.8)
                else:
                    qty = max(min_qty, available / price * 0.5)
                
                if qty >= min_qty:
                    result = place_order(f"{coin}USDT", "BUY", qty)
                    if result:
                        spot_acc['usdt'] -= qty * price * 0.999  # 扣除
                        spot_acc['coins'][coin] = spot_acc['coins'].get(coin, 0) + qty
                        executed.append(f"买入 {coin}")
                        state[coin] = {'action': 'BUY', 'price': price, 'time': time.time()}
            
            # 卖出信号
            elif decision in ['STRONG_SELL', 'SELL'] and current_qty > 0:
                min_qty = MIN_QTY.get(coin, 1)
                sell_qty = current_qty * 0.5
                
                if sell_qty >= min_qty:
                    result = place_order(f"{coin}USDT", "SELL", sell_qty)
                    if result:
                        spot_acc['usdt'] += sell_qty * price * 0.999
                        spot_acc['coins'][coin] = current_qty - sell_qty
                        executed.append(f"卖出 {coin}")
                        state[coin] = {'action': 'SELL', 'price': price, 'time': time.time()}
            
            # 止盈 (持仓价值超过目标20%)
            elif current_value > target_position * 1.2 and current_qty > 0:
                if rsi > 60:  # RSI偏高
                    min_qty = MIN_QTY.get(coin, 1)
                    sell_qty = current_qty * 0.3
                    if sell_qty >= min_qty:
                        place_order(f"{coin}USDT", "SELL", sell_qty)
                        executed.append(f"止盈 {coin}")
        
        except Exception as e:
            log(f"  {coin} 错误: {e}")
    
    return executed

def capital_rebalance(spot_acc, futures_balance):
    """资金再平衡"""
    total = get_total_assets(spot_acc, futures_balance)
    
    # 目标: 现货60% 合约40%
    target_futures = total * 0.4
    target_spot = total * 0.6
    
    # 合约资金不足 → 从现货转入
    if futures_balance < target_futures - 20:
        transfer_amount = min(spot_acc['usdt'] * 0.2, target_futures - futures_balance)
        if transfer_amount > 10:
            transfer_to_futures(transfer_amount)
            spot_acc['usdt'] -= transfer_amount
    
    # 合约资金过剩 → 转回现货
    elif futures_balance > target_futures + 50:
        transfer_amount = (futures_balance - target_futures) * 0.5
        if transfer_amount > 10:
            transfer_to_spot(transfer_amount)

# ========== 主循环 ==========
def main():
    log("=" * 70)
    log("G28 全自动交易系统 v2.0 ⚠️ AUTO MODE")
    log(f"扫描间隔: {SCAN_INTERVAL}秒")
    log("=" * 70)
    
    state = load_state()
    
    while True:
        try:
            spot_acc = get_account()
            futures_balance = get_futures_balance()
            total = get_total_assets(spot_acc, futures_balance)
            
            log(f"\n{'='*60}")
            log(f"⏰ {datetime.now().strftime('%H:%M:%S')} | 总资产: ${total:.2f}")
            log(f"  现货: ${spot_acc['usdt']:.2f} | 合约: ${futures_balance:.2f}")
            
            # 执行自动交易
            executed = auto_trade(spot_acc, futures_balance, state)
            if executed:
                log(f"  📋 执行: {', '.join(executed)}")
            
            # 资金再平衡
            capital_rebalance(spot_acc, futures_balance)
            
            save_state(state)
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
