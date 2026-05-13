#!/usr/bin/env python3
"""
G29 Live - 激进版收益最大化 (修复版)
"""
import urllib.request, hmac, hashlib, time, json, random, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g29.log"

TRADE_CONFIG = {
    'BTC': {'type':'major','position_pct':1.0,'min':0.0001},
    'ETH': {'type':'major','position_pct':1.0,'min':0.001},
    'LINK': {'type':'major','position_pct':1.0,'min':0.1},
    'SOL': {'type':'major','position_pct':1.0,'min':0.01},
    'UNI': {'type':'major','position_pct':1.0,'min':0.01},
    'BOME': {'type':'meme','position_pct':1.0,'min':10000},
    'TURBO': {'type':'meme','position_pct':1.0,'min':1000},
    'PUMP': {'type':'meme','position_pct':1.0,'min':100},
    'NEIRO': {'type':'meme','position_pct':1.0,'min':10000},
}

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def proxy_get(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    return json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())

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

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try: 
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        return float(data['price'])
    except: 
        return 0

def get_klines(symbol, interval, limit):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try: return json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
    except: return []

def get_rsi(symbol, period=14):
    data = get_klines(symbol, '1h', 50)
    if not data or len(data) < period + 1: return 50
    closes = [float(k[4]) for k in data]
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period
    if avg_loss == 0: return 100
    return 100-(100/(1+avg_gain/avg_loss))

def oracle_aggressive(rsi, momentum, coin_type):
    buy_thresh = 38 if coin_type == "meme" else 42
    sell_thresh = 68 if coin_type == "meme" else 65
    
    score = 0
    if rsi < 30: score += 45
    elif rsi < 35: score += 30
    elif rsi < buy_thresh: score += 15
    elif rsi > sell_thresh: score -= 40
    elif rsi > 60: score -= 20
    
    if momentum < -2: score += 20
    elif momentum < 0: score += 10
    elif momentum > 3: score -= 25
    
    if score >= 30: return "STRONG_BUY"
    elif score >= 15: return "BUY"
    elif score <= -30: return "STRONG_SELL"
    elif score <= -15: return "SELL"
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
    if 'error' in str(result): return None
    return result

def get_total(spot_acc):
    total = spot_acc['usdt']
    for coin, qty in spot_acc['coins'].items():
        price = get_price(f"{coin}USDT")
        if price > 0:
            total += qty * price
    return total

def main():
    log("=" * 80)
    log("G29 Live - 激进版收益最大化 (修复版)")
    log("=" * 80)
    
    while True:
        try:
            spot_acc = get_account()
            total = get_total(spot_acc)
            
            log(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} | 总资产: ${total:.2f} | USDT: ${spot_acc['usdt']:.2f}")
            
            for coin, cfg in TRADE_CONFIG.items():
                symbol = f"{coin}USDT"
                
                rsi = get_rsi(symbol)
                klines = get_klines(symbol, '1h', 25)
                if not klines or len(klines) < 24:
                    continue
                momentum = ((float(klines[-1][4]) - float(klines[-24][4])) / float(klines[-24][4])) * 100
                
                decision = oracle_aggressive(rsi, momentum, cfg['type'])
                
                price = get_price(symbol)
                if price <= 0:
                    log(f"  ⚠️ {coin}: 价格获取失败")
                    continue
                    
                current_qty = spot_acc['coins'].get(coin, 0)
                current_value = current_qty * price
                
                sig = "🔮" if decision != "HOLD" else "  "
                log(f"  {sig} {coin}: {decision} (RSI:{rsi:.1f} 动量:{momentum:+.1f}%)")
                
                # 买入 (需要足够USDT)
                if decision in ['STRONG_BUY', 'BUY'] and current_value < total * 0.9:
                    min_qty = cfg.get('min', 1)
                    buy_value = spot_acc['usdt'] * 0.95  # 使用实际USDT的95%
                    
                    if buy_value < 5:  # 太少不交易
                        log(f"       ⚠️ USDT不足 ${spot_acc['usdt']:.2f}")
                        continue
                    
                    if coin == 'meme':
                        buy_qty = int((buy_value / price) / 100) * 100
                        buy_qty = max(min_qty, buy_qty)
                    else:
                        buy_qty = max(min_qty, buy_value / price)
                    
                    if buy_qty >= min_qty and spot_acc['usdt'] >= buy_qty * price * 1.001:
                        result = place_order(symbol, "BUY", buy_qty)
                        if result:
                            log(f"       ✅ 买入 {coin}: {buy_qty} @ ${price:.6f}")
                            spot_acc = get_account()
                
                # 卖出
                elif decision in ['STRONG_SELL', 'SELL'] and current_qty > cfg.get('min', 1):
                    sell_qty = current_qty
                    result = place_order(symbol, "SELL", sell_qty)
                    if result:
                        log(f"       ✅ 卖出 {coin}: {sell_qty} @ ${price:.6f}")
                        spot_acc = get_account()
            
            log(f"\n等待30秒...")
            time.sleep(30)
            
        except Exception as e:
            log(f"错误: {e}")
            import traceback
            log(traceback.format_exc())
            time.sleep(30)

if __name__ == "__main__":
    main()
