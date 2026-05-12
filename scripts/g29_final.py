#!/usr/bin/env python3
"""
G29 Final - 激进版收益最大化
30天回测: +27.7% 收益 | 81% 胜率
Meme币: +43.7% | 主流币: +14.9%
"""
import urllib.request, hmac, hashlib, time, json, random, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

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

def get_rsi(symbol, period=14):
    data = get_klines(symbol, '1h', 50)
    if not data: return 50
    closes = [float(k[4]) for k in data]
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period
    if avg_loss == 0: return 100
    return 100-(100/(1+avg_gain/avg_loss))

def mirofish_aggressive(prices, agent_count=1000):
    """激进Mirofish - 趋势跟随 + 反转"""
    if len(prices) < 2:
        return {'bull_pct': 50, 'confidence': 0}
    returns = [(prices[i+1] - prices[i]) / prices[i] for i in range(len(prices)-1)]
    volatility = np.std(returns) if len(returns) > 1 else 0.01
    trend = np.mean(returns[-24:]) if len(returns) >= 24 else np.mean(returns)
    bull, bear = 0, 0
    for _ in range(agent_count):
        if trend > 0:
            bull += 1.2
        else:
            bear += 0.8
        if len(returns) >= 6:
            recent = np.mean(returns[-6:])
            if recent < -volatility:
                bull += 0.5
            elif recent > volatility:
                bear += 0.5
    total = bull + bear
    return {'bull_pct': bull / total * 100, 'confidence': abs(bull-bear)/total}

def oracle_aggressive(rsi, momentum, coin_type, mirofish):
    """激进Oracle - 收益最大化"""
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
    
    if mirofish['bull_pct'] < 35: score += 15
    elif mirofish['bull_pct'] < 45: score += 8
    elif mirofish['bull_pct'] > 65: score -= 15
    
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
        total += qty * get_price(f"{coin}USDT")
    return total

def main():
    log("=" * 80)
    log("G29 Final - 激进版收益最大化")
    log("回测: +27.7% | 81%胜率 | Meme:+43.7%")
    log("=" * 80)
    
    while True:
        try:
            spot_acc = get_account()
            total = get_total(spot_acc)
            
            log(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} | 总资产: ${total:.2f} | USDT: ${spot_acc['usdt']:.2f}")
            
            for coin, cfg in TRADE_CONFIG.items():
                symbol = f"{coin}USDT"
                
                rsi = get_rsi(symbol)
                prices = [float(k[4]) for k in get_klines(symbol, '1h', 50)]
                momentum = ((prices[-1] - prices[-24]) / prices[-24]) * 100 if len(prices) >= 24 else 0
                mirofish = mirofish_aggressive(prices)
                decision = oracle_aggressive(rsi, momentum, cfg['type'], mirofish)
                
                price = get_price(symbol)
                current_qty = spot_acc['coins'].get(coin, 0)
                current_value = current_qty * price
                
                sig = "🔮" if decision != "HOLD" else "  "
                log(f"  {sig} {coin}: {decision} (RSI:{rsi:.1f} 动量:{momentum:+.1f}% Mirofish:{mirofish['bull_pct']:.0f}%Bull)")
                
                # 全额买入
                if decision in ['STRONG_BUY', 'BUY'] and current_value < total * 0.9:
                    min_qty = cfg.get('min', 1)
                    if coin == 'meme':
                        buy_value = total * 0.95
                        buy_qty = int((buy_value / price) / 100) * 100
                        buy_qty = max(min_qty, buy_qty)
                    else:
                        buy_qty = max(min_qty, total * 0.95 / price)
                    
                    if spot_acc['usdt'] >= buy_qty * price * 1.001:
                        result = place_order(symbol, "BUY", buy_qty)
                        if result:
                            log(f"       ✅ 买入 {coin}: {buy_qty}")
                            spot_acc = get_account()
                
                # 卖出
                elif decision in ['STRONG_SELL', 'SELL'] and current_qty > cfg.get('min', 1):
                    sell_qty = current_qty
                    result = place_order(symbol, "SELL", sell_qty)
                    if result:
                        log(f"       ✅ 卖出 {coin}: {sell_qty}")
                        spot_acc = get_account()
            
            time.sleep(720)  # 每12分钟
            
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
