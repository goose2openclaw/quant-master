#!/usr/bin/env python3
"""
G23 持续监控版 - 自动迭代优化
===========================
功能:
1. 每5分钟自动扫描信号
2. 发现机会自动执行
3. 自动记录收益
4. 基于历史表现动态调整参数
5. 收益最大化
"""
import urllib.request, hmac, hashlib, time, json, numpy as np, sqlite3
from datetime import datetime
from pathlib import Path

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 动态参数 (自动优化)
PARAMS = {
    'rsi_period': 14,
    'oversold': 30,      # 买入阈值
    'overbought': 70,    # 卖出阈值
    'min_score': 75,     # 最小评分
    'position_size': 0.9 # 仓位比例
}

# 币种配置
COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']

# ========== 数据库 (记录交易历史) ==========
DB_PATH = 'logs/g23_trades.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trades
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT, coin TEXT, side TEXT,
                  price REAL, qty REAL, amount REAL,
                  profit_pct REAL, rsi REAL, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS params
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT, rsi_period INTEGER,
                  oversold INTEGER, overbought INTEGER,
                  total_profit REAL, trade_count INTEGER)''')
    conn.commit()
    conn.close()

def log_trade(coin, side, price, qty, amount, profit_pct, rsi, status='closed'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO trades (timestamp, coin, side, price, qty, amount, profit_pct, rsi, status)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (datetime.now().isoformat(), coin, side, price, qty, amount, profit_pct, rsi, status))
    conn.commit()
    conn.close()

def get_recent_profit():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT SUM(profit_pct) FROM trades WHERE status="closed"')
    result = c.fetchone()
    conn.close()
    return result[0] or 0

def optimize_params():
    """基于历史表现优化参数"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 分析最近10笔交易
    c.execute('SELECT profit_pct, rsi FROM trades ORDER BY id DESC LIMIT 10')
    recent = c.fetchall()
    
    if len(recent) < 3:
        conn.close()
        return PARAMS
    
    profits = [r[0] for r in recent if r[0] is not None]
    avg_profit = np.mean(profits) if profits else 0
    
    # 如果平均收益>2%,可以更激进
    if avg_profit > 2:
        PARAMS['oversold'] = max(25, PARAMS['oversold'] - 2)
        PARAMS['overbought'] = min(75, PARAMS['overbought'] + 2)
        PARAMS['min_score'] = max(60, PARAMS['min_score'] - 5)
    # 如果平均收益<0.5%,需要更保守
    elif avg_profit < 0.5 and avg_profit > 0:
        PARAMS['oversold'] = min(35, PARAMS['oversold'] + 2)
        PARAMS['overbought'] = max(65, PARAMS['overbought'] - 2)
        PARAMS['min_score'] = min(85, PARAMS['min_score'] + 5)
    
    # 记录参数
    c.execute('INSERT INTO params (timestamp, rsi_period, oversold, overbought, total_profit, trade_count) VALUES (?, ?, ?, ?, ?, ?)',
              (datetime.now().isoformat(), PARAMS['rsi_period'], PARAMS['oversold'], PARAMS['overbought'], avg_profit, len(recent)))
    conn.commit()
    conn.close()
    
    return PARAMS

# ========== 工具函数 ==========
def api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except: return {}

def price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=10)
    return float(json.loads(resp.read().decode())['price'])

def klines(sym, limit=100):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=15)
    return [float(k[4]) for k in json.loads(resp.read().decode())]

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def get_funding_rate(symbol):
    url = f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode())
        return float(data.get('lastFundingRate', 0)) * 100
    except: return 0

def get_balance():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    if 'balances' in data:
        for b in data['balances']:
            if b['asset'] == 'USDT': return float(b['free'])
    return 0

def get_positions():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    positions = {}
    if 'balances' in data:
        for b in data['balances']:
            free = float(b.get('free', 0))
            if free > 0.00001 and b['asset'] != 'USDT':
                try:
                    p = price(b['asset']+'USDT')
                    positions[b['asset']] = {'qty': free, 'price': p}
                except: pass
    return positions

def buy(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, 'POST')

def sell(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, 'POST')

# ========== 主循环 ==========
def main():
    log_path = Path('logs/g23_auto.log')
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    init_db()
    
    # 优化参数
    params = optimize_params()
    
    ts = datetime.now().strftime('%H:%M:%S')
    total_profit = get_recent_profit()
    
    with open(log_path, 'a') as f:
        f.write(f"\n[{ts}] G23 Auto 运行 | 总收益:{total_profit:.2f}% | 参数:RSI{params['rsi_period']}/{params['oversold']}/{params['overbought']}\n")
    
    print(f"\n[{ts}] G23 Auto | 总收益:{total_profit:.2f}%")
    print(f"  参数: RSI{params['rsi_period']}/{params['oversold']}/{params['overbought']}")
    
    # 分析信号
    usdt = get_balance()
    positions = get_positions()
    
    buy_signal = None
    sell_signal = None
    
    for coin in COINS:
        try:
            prices = klines(f'{coin}USDT', 100)
            rsi = calc_rsi(prices, params['rsi_period'])
            funding = get_funding_rate(f'{coin}USDT')
            
            # 买入信号
            if rsi < params['oversold']:
                score = (params['oversold'] - rsi) * 2 + (funding if funding > 0 else 0)
                if score > params['min_score']:
                    buy_signal = (coin, rsi, score)
            
            # 卖出信号
            if rsi > params['overbought'] and coin in positions:
                score = (rsi - params['overbought']) * 2
                if score > params['min_score']:
                    sell_signal = (coin, rsi, score)
                    
        except: pass
    
    # 执行交易
    if buy_signal and usdt > 10:
        coin, rsi, score = buy_signal
        amount = usdt * params['position_size']
        p = price(f'{coin}USDT')
        qty = round(amount / p, 4)
        
        result = buy(f'{coin}USDT', qty)
        if 'orderId' in result:
            log_trade(coin, 'BUY', p, qty, amount, None, rsi, 'open')
            print(f"  ✅ BUY {coin}: {qty} @ ${p:.2f} (RSI={rsi:.0f}, score={score:.0f})")
            with open(log_path, 'a') as f:
                f.write(f"  ✅ BUY {coin}: {qty} @ ${p:.2f} (RSI={rsi:.0f})\n")
    
    elif sell_signal:
        coin, rsi, score = sell_signal
        pos = positions[coin]
        qty = round(pos['qty'] * 0.95, 4)
        
        # 估算利润
        buy_price = pos.get('buy_price', pos['price'])
        profit = (pos['price'] - buy_price) / buy_price * 100
        
        result = sell(f'{coin}USDT', qty)
        if 'orderId' in result:
            log_trade(coin, 'SELL', pos['price'], qty, pos['qty'] * pos['price'], profit, rsi, 'closed')
            print(f"  🔴 SELL {coin}: {qty} @ ${pos['price']:.2f} (profit={profit:.2f}%)")
            with open(log_path, 'a') as f:
                f.write(f"  🔴 SELL {coin}: profit={profit:.2f}%\n")
    
    else:
        print(f"  ⏸️ 无信号 (USDT=${usdt:.2f})")
    
    print()

if __name__ == '__main__':
    main()
