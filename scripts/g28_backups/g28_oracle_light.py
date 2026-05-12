#!/usr/bin/env python3
"""
G28 Oracle 全自动交易系统 v3.1 (轻量版)
========================================
功能:
1. Oracle 快速决策
2. 自动交易执行
3. 账户资金调配
"""
import urllib.request, hmac, hashlib, time, json
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g28_oracle.log"

TRADE_CONFIG = {
    'BTC': {'type':'major','position_pct':0.15},
    'ETH': {'type':'major','position_pct':0.12},
    'BNB': {'type':'major','position_pct':0.10},
    'LINK': {'type':'major','position_pct':0.10},
    'SOL': {'type':'major','position_pct':0.10},
    'UNI': {'type':'major','position_pct':0.10},
    'BOME': {'type':'meme','position_pct':0.08},
    'TURBO': {'type':'meme','position_pct':0.08},
    'PUMP': {'type':'meme','position_pct':0.08},
    'NEIRO': {'type':'meme','position_pct':0.08},
}

MIN_QTY = {'BOME': 10000, 'TURBO': 1000, 'PUMP': 100, 'NEIRO': 10000, 'LINK': 0.1, 'ETH': 0.001}

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

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

def oracle_decision(rsi, momentum, coin_type):
    """Oracle决策"""
    buy_thresh = 35 if coin_type == "meme" else 40
    sell_thresh = 75 if coin_type == "meme" else 70
    
    if rsi < buy_thresh and momentum < -2: return "STRONG_BUY"
    if rsi < buy_thresh: return "BUY"
    if rsi > sell_thresh and momentum > 3: return "STRONG_SELL"
    if rsi > sell_thresh - 5: return "SELL"
    return "HOLD"

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

def place_order(symbol, side, quantity):
    params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
    result = signed_api("/api/v3/order", params, "POST")
    if 'error' in result:
        return None
    return result

def get_total(spot_acc):
    total = spot_acc['usdt']
    for coin, qty in spot_acc['coins'].items():
        total += qty * get_price(f"{coin}USDT")
    return total

def main():
    log("=" * 70)
    log("G28 Oracle 全自动交易系统 v3.1 🔮 ORACLE MODE")
    log("=" * 70)
    
    while True:
        try:
            spot_acc = get_account()
            total = get_total(spot_acc)
            
            log(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} | 总资产: ${total:.2f} | USDT: ${spot_acc['usdt']:.2f}")
            
            executed = []
            for coin, cfg in TRADE_CONFIG.items():
                rsi = get_rsi(f"{coin}USDT")
                momentum = get_momentum(f"{coin}USDT")
                decision = oracle_decision(rsi, momentum, cfg['type'])
                
                price = get_price(f"{coin}USDT")
                current_qty = spot_acc['coins'].get(coin, 0)
                current_value = current_qty * price
                target_value = total * cfg['position_pct']
                
                log(f"  🔮 {coin}: {decision} (RSI:{rsi:.1f} 动量:{momentum:+.2f}% 持仓:${current_value:.2f})")
                
                # 执行
                if decision in ['STRONG_BUY', 'BUY'] and current_value < target_value:
                    min_qty = MIN_QTY.get(coin, 1)
                    available = min(spot_acc['usdt'], total * 0.1)
                    qty = max(min_qty * 3, available / price * 0.8)
                    if qty >= min_qty and spot_acc['usdt'] > 5:
                        result = place_order(f"{coin}USDT", "BUY", qty)
                        if result:
                            spot_acc['usdt'] -= qty * price * 0.999
                            spot_acc['coins'][coin] = spot_acc['coins'].get(coin, 0) + qty
                            executed.append(f"买入{coin}")
                
                elif decision in ['STRONG_SELL', 'SELL'] and current_qty > 0:
                    min_qty = MIN_QTY.get(coin, 1)
                    sell_qty = current_qty * 0.5
                    if sell_qty >= min_qty:
                        result = place_order(f"{coin}USDT", "SELL", sell_qty)
                        if result:
                            spot_acc['usdt'] += sell_qty * price * 0.999
                            spot_acc['coins'][coin] = current_qty - sell_qty
                            executed.append(f"卖出{coin}")
            
            if executed:
                log(f"  📋 执行: {', '.join(executed)}")
            
            time.sleep(60)
            
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
