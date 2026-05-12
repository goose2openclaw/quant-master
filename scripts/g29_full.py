#!/usr/bin/env python3
"""
G29 Full Auto - 全自动资产管理 (修复POST)
"""
import urllib.request, hmac, hashlib, time, json
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g29.log"

TRADE_COINS = ['BTC','ETH','LINK','SOL','UNI','BOME','TURBO','PUMP','NEIRO']
MIN_TRADE_USD = 5

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def api_get(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())

def api_signed_get(endpoint, params=None):
    """GET request for account info"""
    ts = int(time.time() * 1000)
    base = {"timestamp": ts, "recvWindow": 5000}
    if params: base.update(params)
    q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=15).read().decode())

def api_signed_post(endpoint, params=None):
    """POST request for orders"""
    ts = int(time.time() * 1000)
    base = {"timestamp": ts, "recvWindow": 5000}
    if params: base.update(params)
    q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url, method="POST")
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=15).read().decode())

def get_price(symbol):
    try:
        return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

def get_klines(symbol, interval, limit):
    try:
        return api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    except: return []

def get_rsi(symbol):
    data = get_klines(symbol, '1h', 50)
    if len(data) < 15: return 50
    closes = [float(k[4]) for k in data]
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d if d>0 else 0 for d in deltas[-14:]]
    losses = [-d if d<0 else 0 for d in deltas[-14:]]
    avg_gain = sum(gains)/14
    avg_loss = sum(losses)/14
    if avg_loss == 0: return 100
    return 100-(100/(1+avg_gain/avg_loss))

def get_momentum(symbol):
    data = get_klines(symbol, '1h', 25)
    if len(data) < 24: return 0
    return ((float(data[-1][4]) - float(data[-24][4])) / float(data[-24][4])) * 100

def oracle_score(rsi, momentum):
    score = 0
    if rsi < 25: score += 50
    elif rsi < 30: score += 40
    elif rsi < 35: score += 25
    elif rsi < 40: score += 10
    elif rsi > 75: score -= 50
    elif rsi > 70: score -= 35
    elif rsi > 65: score -= 20
    elif rsi > 60: score -= 10
    if momentum < -4: score += 30
    elif momentum < -2: score += 20
    elif momentum < 0: score += 10
    elif momentum > 4: score -= 30
    elif momentum > 2: score -= 20
    return score

def get_account():
    data = api_signed_get("/api/v3/account")
    result = {'usdt': 0, 'coins': {}}
    for b in data.get('balances', []):
        free = float(b.get('free', 0))
        if free > 0.0001:
            if b['asset'] == 'USDT':
                result['usdt'] = free
            else:
                result['coins'][b['asset']] = free
    return result

def place_order(symbol, side, quantity):
    params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
    return api_signed_post("/api/v3/order", params)

def get_total_value(balances):
    total = balances['usdt']
    for coin, qty in balances['coins'].items():
        price = get_price(f"{coin}USDT")
        if price > 0:
            total += qty * price
    return total

def sell_portion(coin, qty, price, target_value):
    sell_qty = min(qty, target_value / price)
    if coin in ['BOME', 'NEIRO', 'PUMP']:
        sell_qty = int(sell_qty / 100) * 100
    elif coin == 'TURBO':
        sell_qty = int(sell_qty / 1000) * 1000
    else:
        sell_qty = int(sell_qty * 100) / 100
    if sell_qty < qty * 0.1:
        sell_qty = qty * 0.1
        if coin in ['BOME', 'NEIRO', 'PUMP']:
            sell_qty = int(sell_qty / 100) * 100
        elif coin == 'TURBO':
            sell_qty = int(sell_qty / 1000) * 1000
        else:
            sell_qty = int(sell_qty * 100) / 100
    return sell_qty

def main():
    log("=" * 60)
    log("G29 Full Auto - POST修复版")
    log("=" * 60)
    
    while True:
        try:
            balances = get_account()
            total = get_total_value(balances)
            usdt = balances['usdt']
            
            log(f"\n总资产: ${total:.2f} | USDT: ${usdt:.2f}")
            
            analysis = []
            for coin in TRADE_COINS:
                if coin not in balances['coins']: continue
                qty = balances['coins'][coin]
                price = get_price(f"{coin}USDT")
                if price <= 0: continue
                value = qty * price
                if value < 1: continue
                
                rsi = get_rsi(f"{coin}USDT")
                momentum = get_momentum(f"{coin}USDT")
                score = oracle_score(rsi, momentum)
                
                analysis.append({
                    'coin': coin, 'qty': qty, 'price': price, 'value': value,
                    'rsi': rsi, 'momentum': momentum, 'score': score
                })
            
            analysis.sort(key=lambda x: x['score'], reverse=True)
            
            log(f"\n{'币种':<8} {'RSI':<6} {'动量':<8} {'评分':<6} {'价值':<10}")
            log("-" * 45)
            
            for a in analysis:
                sig = "🔴" if a['score'] < 0 else "🟡" if a['score'] < 20 else "🟢"
                log(f"{sig} {a['coin']:<6} {a['rsi']:>5.1f} {a['momentum']:>+7.1f}% {a['score']:>+5} ${a['value']:>8.2f}")
            
            # USDT不足时卖出
            if usdt < 50:
                log(f"\n⚠️ USDT不足 ${usdt:.2f}，启动资金调配...")
                for a in sorted(analysis, key=lambda x: x['score']):
                    if a['value'] > MIN_TRADE_USD:
                        sell_qty = sell_portion(a['coin'], a['qty'], a['price'], 50)
                        if sell_qty > 0:
                            log(f"\n📤 卖出 {a['coin']} x {sell_qty} (评分:{a['score']})")
                            result = place_order(f"{a['coin']}USDT", "SELL", sell_qty)
                            if result and 'orderId' in result:
                                log(f"   ✅ 卖出 {sell_qty} {a['coin']} @ ${a['price']:.6f} = ${sell_qty*a['price']:.2f}")
                                balances = get_account()
                                usdt = balances['usdt']
                                log(f"   USDT现在: ${usdt:.2f}")
                                break
                            else:
                                log(f"   ❌ 失败: {str(result)[:50]}")
            
            # 买入
            if usdt > MIN_TRADE_USD:
                for a in analysis:
                    if a['score'] > 30 and a['value'] < total * 0.15:
                        buy_value = usdt * 0.95
                        buy_qty = buy_value / a['price']
                        
                        if a['coin'] in ['BOME', 'NEIRO', 'PUMP']:
                            buy_qty = int(buy_qty / 100) * 100
                        elif a['coin'] == 'TURBO':
                            buy_qty = int(buy_qty / 1000) * 1000
                        else:
                            buy_qty = int(buy_qty * 100) / 100
                        
                        min_qty = {'BOME': 1000, 'NEIRO': 10000, 'PUMP': 100, 'TURBO': 1000}.get(a['coin'], 0.001)
                        if buy_qty >= min_qty:
                            log(f"\n📥 买入 {a['coin']} (评分:{a['score']})")
                            result = place_order(f"{a['coin']}USDT", "BUY", buy_qty)
                            if result and 'orderId' in result:
                                log(f"   ✅ 买入 {buy_qty} {a['coin']} @ ${a['price']:.6f} = ${buy_value:.2f}")
                                break
                            else:
                                log(f"   ❌ 失败: {str(result)[:50]}")
            
            log(f"\n等待30秒...")
            time.sleep(30)
            
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
