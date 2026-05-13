#!/usr/bin/env python3
"""
G27 Oracle 全持仓管理 - 持续监控版
优化: 低CPU占用 + 看门狗自动重启
"""
import urllib.request, hmac, hashlib, time, json, os, sys
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
SCAN_INTERVAL = 30  # 每30秒扫描
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g27_continuous.log"

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def api_signed(endpoint, params=None):
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
    try:
        resp = opener.open(req, timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        return float(data['price'])
    except: return 0

def get_rsi(symbol, interval="1h", period=14):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={period+1}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        closes = [float(k[4]) for k in data]
        if len(closes) < period + 1: return 50
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0: return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except: return 50

def get_momentum(symbol, interval="1h"):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=25'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        if len(data) < 24: return 0
        old = float(data[-24][4])
        new = float(data[-1][4])
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

def analyze_coin(symbol, amount, coin_type):
    price = get_price(f"{symbol}USDT")
    if price == 0: return None
    value = amount * price
    rsi = get_rsi(f"{symbol}USDT")
    momentum = get_momentum(f"{symbol}USDT")
    decision = oracle_decision(rsi, momentum, coin_type)
    return {"symbol": symbol, "amount": amount, "value": value, "rsi": rsi, "momentum": momentum, "decision": decision}

def main():
    log("=" * 60)
    log("G27 Oracle 持续监控启动")
    log(f"扫描间隔: {SCAN_INTERVAL}秒")
    log("=" * 60)
    
    coins = [
        ("ETH", 0.0034, "Major"), ("BNB", 0.0116, "Major"),
        ("LINK", 1.77, "Major"), ("SOL", 0.0729, "Major"),
        ("UNI", 2.25, "Major"), ("BOME", 505265.0, "Meme"),
        ("NEIRO", 94506.0, "Meme"), ("TURBO", 56541.0, "Meme"),
        ("PUMP", 49317.0, "Meme"),
    ]
    
    while True:
        try:
            ts = datetime.now().strftime("%m-%d %H:%M:%S")
            decisions = []
            for symbol, amount, ctype in coins:
                result = analyze_coin(symbol, amount, ctype)
                if result:
                    decisions.append(result)
            
            # 输出简洁状态
            actions = [d['decision'] for d in decisions]
            buy_count = actions.count('BUY') + actions.count('ADD')
            sell_count = actions.count('SELL') + actions.count('REDUCE')
            
            log(f"[{ts}] 扫描 {len(decisions)}币 | 买入信号:{buy_count} 卖出信号:{sell_count} HOLD:{actions.count('HOLD')}")
            
            if buy_count > 0 or sell_count > 0:
                for d in decisions:
                    if d['decision'] != 'HOLD':
                        log(f"  → {d['symbol']}: {d['decision']} (RSI:{d['rsi']:.1f} 动量:{d['momentum']:+.2f}%)")
            
            time.sleep(SCAN_INTERVAL)
        except Exception as e:
            log(f"错误: {e}, 10秒后重试...")
            time.sleep(10)

if __name__ == "__main__":
    main()
