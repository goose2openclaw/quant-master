#!/usr/bin/env python3
"""
G29 Auto - 全账户自主决策自动交易
1. 卖出高RSI持仓获取USDT
2. 买入低RSI强信号币种
"""
import urllib.request, hmac, hashlib, time, json, random, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g29.log"

TRADE_COINS = ['BTC','ETH','LINK','SOL','UNI','BOME','TURBO','PUMP','NEIRO']
MIN_TRADE = 10  # 最低交易额$10

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
        return {"error": str(e)}

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try: return float(json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())['price'])
    except: return 0

def get_klines(symbol, interval, limit):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try: return json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
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

def oracle_decision(rsi, momentum):
    score = 0
    if rsi < 30: score += 45
    elif rsi < 35: score += 30
    elif rsi < 40: score += 15
    elif rsi > 70: score -= 40
    elif rsi > 65: score -= 25
    elif rsi > 60: score -= 15
    
    if momentum < -3: score += 25
    elif momentum < -1: score += 15
    elif momentum > 3: score -= 25
    
    if score >= 30: return "STRONG_BUY"
    elif score >= 15: return "BUY"
    elif score <= -30: return "STRONG_SELL"
    elif score <= -15: return "SELL"
    return "HOLD"

def get_spot_balance():
    account = signed_api("/api/v3/account")
    balances = {}
    if 'balances' in account:
        for b in account['balances']:
            free = float(b.get('free', 0))
            if free > 0.0001:
                balances[b['asset']] = free
    return balances

def place_order(symbol, side, quantity):
    params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
    result = signed_api("/api/v3/order", params, "POST")
    if 'error' in str(result): return None
    return result

def get_total_value(balances):
    total = 0
    for coin, qty in balances.items():
        if coin == 'USDT':
            total += qty
        else:
            price = get_price(f"{coin}USDT")
            if price > 0:
                total += qty * price
    return total

def main():
    log("=" * 80)
    log("G29 Auto - 全账户自主交易")
    log("=" * 80)
    
    while True:
        try:
            balances = get_spot_balance()
            total = get_total_value(balances)
            usdt = balances.get('USDT', 0)
            
            log(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} | 总资产: ${total:.2f} | USDT: ${usdt:.2f}")
            
            # 分析所有币种
            analysis = []
            for coin in TRADE_COINS:
                if coin not in balances: continue
                qty = balances[coin]
                price = get_price(f"{coin}USDT")
                if price <= 0: continue
                value = qty * price
                if value < 1: continue
                
                rsi = get_rsi(f"{coin}USDT")
                momentum = get_momentum(f"{coin}USDT")
                decision = oracle_decision(rsi, momentum)
                
                analysis.append({
                    'coin': coin, 'qty': qty, 'price': price, 'value': value,
                    'rsi': rsi, 'momentum': momentum, 'decision': decision
                })
            
            # 按RSI排序
            analysis.sort(key=lambda x: x['rsi'])
            
            # 打印分析
            for a in analysis:
                sig = "🔮" if a['decision'] != "HOLD" else "  "
                log(f"  {sig} {a['coin']}: {a['decision']} RSI:{a['rsi']:.1f} 动量:{a['momentum']:+.1f}% 价值:${a['value']:.2f}")
            
            # 执行交易
            # 1. 先卖出高RSI的币
            for a in analysis:
                if a['decision'] in ['STRONG_SELL', 'SELL'] and a['value'] > MIN_TRADE:
                    result = place_order(f"{a['coin']}USDT", "SELL", a['qty'])
                    if result:
                        log(f"  ✅ 卖出 {a['coin']}: {a['qty']} @ ${a['price']:.6f} = ${a['value']:.2f}")
                        balances = get_spot_balance()
            
            # 2. 买入低RSI强信号
            usdt = balances.get('USDT', 0)
            if usdt > MIN_TRADE:
                # 找最低RSI的强买入信号
                buy_candidates = [a for a in analysis if a['decision'] in ['STRONG_BUY', 'BUY'] and a['value'] < total * 0.15]
                if buy_candidates:
                    target = buy_candidates[0]  # RSI最低的
                    buy_value = usdt * 0.95
                    buy_qty = buy_value / target['price']
                    
                    # 取整
                    if target['coin'] in ['BOME', 'NEIRO']:
                        buy_qty = int(buy_qty / 100) * 100
                    elif target['coin'] == 'TURBO':
                        buy_qty = int(buy_qty / 1000) * 1000
                    elif target['coin'] == 'PUMP':
                        buy_qty = int(buy_qty / 100) * 100
                    else:
                        buy_qty = int(buy_qty * 100) / 100
                    
                    if buy_qty > 0:
                        result = place_order(f"{target['coin']}USDT", "BUY", buy_qty)
                        if result:
                            log(f"  ✅ 买入 {target['coin']}: {buy_qty} @ ${target['price']:.6f} = ${buy_value:.2f}")
            
            log(f"\n等待30秒...")
            time.sleep(30)
            
        except Exception as e:
            log(f"错误: {e}")
            import traceback
            log(traceback.format_exc())
            time.sleep(30)

if __name__ == "__main__":
    main()
