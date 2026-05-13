#!/usr/bin/env python3
"""
G27 Oracle 自动交易版
⚠️ 自动执行买卖操作
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
SCAN_INTERVAL = 30
TRADE_LOG = "/home/goose/.openclaw/workspace/logs/g27_trades.log"
STATE_FILE = "/home/goose/.openclaw/workspace/logs/g27_state.json"

# 交易配置
TRADE_CONFIG = {
    'BOME': {'position_pct': 0.08, 'max_position': 0.10, 'stop_loss': 0.05},
    'TURBO': {'position_pct': 0.08, 'max_position': 0.10, 'stop_loss': 0.05},
    'PUMP': {'position_pct': 0.08, 'max_position': 0.10, 'stop_loss': 0.05},
    'NEIRO': {'position_pct': 0.08, 'max_position': 0.10, 'stop_loss': 0.05},
    'ETH': {'position_pct': 0.10, 'max_position': 0.15, 'stop_loss': 0.03},
    'BTC': {'position_pct': 0.10, 'max_position': 0.15, 'stop_loss': 0.02},
    'UNI': {'position_pct': 0.10, 'max_position': 0.15, 'stop_loss': 0.03},
    'LINK': {'position_pct': 0.10, 'max_position': 0.15, 'stop_loss': 0.03},
}

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(TRADE_LOG, "a") as f:
        f.write(line + "\n")

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except: return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

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
        log(f"API错误: {e}")
        return {"error": str(e)}

def place_order(symbol, side, quantity):
    """下单"""
    params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
    result = signed_api("/api/v3/order", params, "POST")
    if "error" in result:
        log(f"下单失败: {result['error']}")
        return None
    log(f"✅ {side} {quantity} {symbol}")
    return result

def get_balance():
    """获取USDT余额"""
    account = signed_api("/api/v3/account")
    if "error" in account: return 0
    for b in account.get('balances', []):
        if b['asset'] == 'USDT':
            return float(b['free'])
    return 0

def get_position(symbol):
    """获取持仓数量"""
    account = signed_api("/api/v3/account")
    if "error" in account: return 0
    for b in account.get('balances', []):
        if b['asset'] == symbol:
            return float(b['free'])
    return 0

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
        old = float(data[-24][4]); new = float(data[-1][4])
        return ((new - old) / old) * 100
    except: return 0

def oracle_decision(rsi, momentum, coin_type):
    buy_thresh = 35 if coin_type == "Meme" else 40
    sell_thresh = 75 if coin_type == "Meme" else 70
    if rsi < buy_thresh and momentum < -2: return "BUY"
    if rsi < buy_thresh: return "ADD"
    if rsi > sell_thresh and momentum > 3: return "SELL"
    if rsi > sell_thresh - 5: return "REDUCE"
    return "HOLD"

def main():
    log("=" * 60)
    log("G27 Oracle 自动交易启动 ⚠️")
    log(f"扫描间隔: {SCAN_INTERVAL}秒")
    log("=" * 60)
    
    coins = [
        ("ETH", 0.0034, "Major"), ("UNI", 2.25, "Major"),
        ("LINK", 1.77, "Major"), ("BOME", 505265.0, "Meme"),
        ("NEIRO", 94506.0, "Meme"), ("TURBO", 56541.0, "Meme"),
        ("PUMP", 49317.0, "Meme"),
    ]
    
    state = load_state()
    
    while True:
        try:
            usdt_balance = get_balance()
            log(f"[扫描] USDT余额: ${usdt_balance:.2f}")
            
            for symbol, amount, ctype in coins:
                rsi = get_rsi(f"{symbol}USDT")
                momentum = get_momentum(f"{symbol}USDT")
                decision = oracle_decision(rsi, momentum, ctype)
                
                config = TRADE_CONFIG.get(symbol, {'position_pct': 0.08, 'max_position': 0.10})
                
                # 检查是否可交易
                last_action = state.get(symbol, {}).get('action')
                last_rsi = state.get(symbol, {}).get('rsi', 0)
                
                # 交易逻辑
                if decision in ['BUY', 'ADD'] and last_action != 'BUY':
                    # 计算买入数量
                    position_value = usdt_balance * config['position_pct']
                    price = get_price(f"{symbol}USDT")
                    if price > 0:
                        quantity = position_value / price
                        # 最小下单量检查
                        if quantity > 10:  # Meme币最小10个
                            result = place_order(f"{symbol}USDT", "BUY", quantity)
                            if result:
                                state[symbol] = {'action': 'BUY', 'rsi': rsi, 'time': time.time()}
                                save_state(state)
                
                elif decision in ['SELL', 'REDUCE'] and last_action == 'BUY':
                    # 卖出
                    current_amount = get_position(symbol)
                    if current_amount > 10:
                        sell_qty = current_amount * 0.5  # 卖出一半
                        result = place_order(f"{symbol}USDT", "SELL", sell_qty)
                        if result:
                            state[symbol] = {'action': 'SELL', 'rsi': rsi, 'time': time.time()}
                            save_state(state)
                
                log(f"  {symbol}: {decision} (RSI:{rsi:.1f} 动量:{momentum:+.2f}%)")
            
            time.sleep(SCAN_INTERVAL)
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
