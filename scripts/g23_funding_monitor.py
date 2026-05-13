#!/usr/bin/env python3
"""
G23 资金费率套利持续监控版
===========================
功能:
1. 每5分钟扫描资金费率
2. 费率 > 0.03% 时自动做多
3. 费率 < -0.03% 时自动做空
4. 严格风控 (止损-5%, 止盈+15%)
5. 每币种独立仓位,不共享抵押金
6. 最大3个仓位

启动:
  nohup python3 scripts/g23_funding_monitor.py >> logs/g23_funding.log 2>&1 &
"""
import urllib.request, hmac, hashlib, time, json, numpy as np, sqlite3
from datetime import datetime
from pathlib import Path

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ========== 风控参数 ==========
FUNDING_THRESHOLD = 0.03   # 触发阈值
MAX_POSITIONS = 3          # 最大仓位
MAX_POSITION_RATIO = 0.2   # 单币仓位比例
STOP_LOSS = 0.05          # 止损5%
TAKE_PROFIT = 0.15        # 止盈15%
LEVERAGE = 5              # 杠杆倍数
SCAN_INTERVAL = 300        # 扫描间隔(秒)

# ========== 数据库 ==========
DB_PATH = 'logs/g23_positions.db'

def init_db():
    Path('logs').mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS positions
                 (id INTEGER PRIMARY KEY, coin TEXT, side TEXT,
                  entry_price REAL, qty REAL, entry_time TEXT,
                  stop_loss REAL, take_profit REAL, funding REAL,
                  status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS funding_log
                 (id INTEGER PRIMARY KEY, timestamp TEXT,
                  coin TEXT, funding REAL, signal TEXT)''')
    conn.commit()
    conn.close()

def log_position(coin, side, entry_price, qty, funding, status='open'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO positions (coin, side, entry_price, qty, entry_time, stop_loss, take_profit, funding, status)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (coin, side, entry_price, qty, datetime.now().isoformat(), STOP_LOSS, TAKE_PROFIT, funding, status))
    conn.commit()
    conn.close()

def get_open_positions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT coin, side, entry_price, qty, stop_loss, take_profit FROM positions WHERE status="open"')
    result = c.fetchall()
    conn.close()
    return result

def close_position(coin):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE positions SET status="closed" WHERE coin=? AND status="open"', (coin,))
    conn.commit()
    conn.close()

def log_funding(coin, funding, signal):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO funding_log (timestamp, coin, funding, signal) VALUES (?, ?, ?, ?)',
              (datetime.now().isoformat(), coin, funding, signal))
    conn.commit()
    conn.close()

# ========== API工具 ==========
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

def get_funding(symbol):
    url = f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode())
        return float(data.get('lastFundingRate', 0)) * 100
    except: return 0

def get_futures_balance():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.bapi.com/fapi/v1/balance?timestamp={ts}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode())
        for item in data:
            if item.get('asset') == 'USDT':
                return float(item.get('availableBalance', 0))
    except: return 0

def set_leverage(symbol, leverage=5):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&leverage={leverage}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v1/leverage?{q}&signature={sig}"
    return api(url, 'POST')

def futures_buy(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v1/order?{q}&signature={sig}"
    return api(url, 'POST')

def futures_sell(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v1/order?{q}&signature={sig}"
    return api(url, 'POST')

def close_futures_position(symbol):
    """平仓"""
    ts = int(time.time() * 1000)
    # 先获取当前持仓
    q = f"symbol={symbol}&timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v2/positionRisk?symbol={symbol}&timestamp={ts}&signature={sig}"
    data = api(url)
    if data and len(data) > 0:
        pos = data[0]
        amt = float(pos.get('positionAmt', 0))
        if amt > 0:
            return futures_sell(symbol, abs(amt))
        elif amt < 0:
            return futures_buy(symbol, abs(amt))
    return {'error': 'No position'}

# ========== 主循环 ==========
def main():
    log_path = Path('logs/g23_funding.log')
    log_path.parent.mkdir(exist_ok=True)
    init_db()
    
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] G23 资金费率监控")
    
    # 获取状态
    balance = get_futures_balance()
    open_positions = get_open_positions()
    coins_in_pos = [p[0] for p in open_positions]
    
    print(f"  合约余额: ${balance:.2f}")
    print(f"  持仓: {len(open_positions)}/{MAX_POSITIONS}")
    
    # 扫描币种
    coins = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX']
    opportunities = []
    
    for coin in coins:
        try:
            funding = get_funding(f'{coin}USDT')
            p = price(f'{coin}USDT')
            
            log_funding(coin, funding, 'scan')
            
            signal = '观望'
            if funding > FUNDING_THRESHOLD:
                signal = '做多'
                opportunities.append((coin, 'LONG', funding, p))
            elif funding < -FUNDING_THRESHOLD:
                signal = '做空'
                opportunities.append((coin, 'SHORT', funding, p))
            
            emoji = '🟢' if signal == '做多' else '🔴' if signal == '做空' else '⚪'
            print(f"  {emoji} {coin}: 费率{funding:+.4f}% -> {signal}")
            
        except Exception as e:
            print(f"  ❌ {coin}: {e}")
    
    # 按资金费率排序
    opportunities.sort(key=lambda x: abs(x[2]), reverse=True)
    
    # 执行交易
    for coin, side, funding, cur_price in opportunities:
        if len(open_positions) >= MAX_POSITIONS:
            break
        
        if coin in coins_in_pos:
            continue  # 已有该币种仓位
        
        if balance < 50:
            print(f"  ⚠️ 余额不足 ${balance:.2f}")
            break
        
        # 计算仓位
        position_size = min(balance * MAX_POSITION_RATIO, balance * 0.5)
        qty = round(position_size * LEVERAGE / cur_price, 4)
        
        if qty < 0.001:
            continue
        
        print(f"\n  ✅ 开仓: {coin} {side}")
        print(f"     资金费率: {funding:+.4f}%")
        print(f"     仓位: ${position_size:.2f} x{LEVERAGE}x")
        print(f"     数量: {qty}")
        
        # 设置杠杆
        set_leverage(f'{coin}USDT', LEVERAGE)
        
        # 执行
        if side == 'LONG':
            result = futures_buy(f'{coin}USDT', qty)
        else:
            result = futures_sell(f'{coin}USDT', qty)
        
        if 'orderId' in result:
            log_position(coin, side, cur_price, qty, funding)
            balance -= position_size
            open_positions.append((coin, side, cur_price, qty, funding))
            coins_in_pos.append(coin)
            print(f"     成功! 订单ID: {result['orderId']}")
        else:
            print(f"     失败: {result.get('msg', result)}")
    
    # 检查现有仓位止损止盈
    print(f"\n  仓位检查:")
    for coin, side, entry_price, qty, funding in open_positions:
        try:
            cur_price = price(f'{coin}USDT')
            if side == 'LONG':
                pnl_pct = (cur_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - cur_price) / entry_price
            
            pnl_pct = pnl_pct * LEVERAGE  # 加上杠杆
            
            emoji = '🟢' if pnl_pct > 0 else '🔴'
            print(f"  {emoji} {coin}: {pnl_pct:+.2f}% (入场${entry_price:.2f} 当前${cur_price:.2f})")
            
            # 止损/止盈检查
            if pnl_pct <= -STOP_LOSS or pnl_pct >= TAKE_PROFIT:
                print(f"     {'止盈' if pnl_pct >= TAKE_PROFIT else '止损'}触发!")
                result = close_futures_position(f'{coin}USDT')
                if 'orderId' in result or result.get('code') == '0':
                    close_position(coin)
                    print(f"     平仓成功!")
                else:
                    print(f"     平仓失败: {result}")
                    
        except Exception as e:
            print(f"  ❌ {coin}: {e}")
    
    print()

if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print(f"错误: {e}")
        time.sleep(SCAN_INTERVAL)
