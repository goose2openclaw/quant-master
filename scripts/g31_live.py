#!/usr/bin/env python3
"""
G31 Live Trading - go-core驱动的实盘交易系统
"""
import urllib.request, hmac, hashlib, time, json, sys, math, threading
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-core')

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g31_live.log"

MAJOR_COINS = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','DOT','LINK','UNI','AVAX','MATIC','ATOM','LTC','ETC','AAVE','APT','NEAR','FIL','ICP','INJ','TIA','SEI','SUI','OP','ARB','LDO','CRV','RDNT','ENS']
MEME_COINS = ['PEPE','SHIB','FLOKI','WIF','BABYDOGE','COOKIE','AI','NEIRO','BOME','TURBO','PUMP','BONK']

MIN_TRADE_USDT = 3
MAX_POSITION_PCT = 0.10
STOP_LOSS = 0.03
TAKE_PROFIT = 0.15

try:
    from go_core import GoCore
    GOCORE_AVAILABLE = True
except:
    GOCORE_AVAILABLE = False
    print("警告: go-core不可用")

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")

def api_get(url):
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except Exception as e:
        log(f"API GET错误: {e}", "ERROR")
        return None

def api_signed_get(endpoint, params=None):
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

def get_account():
    try:
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
    except Exception as e:
        log(f"获取账户失败: {e}", "ERROR")
        return {'usdt': 0, 'coins': {}}

def get_total_value(balances):
    total = balances['usdt']
    for coin, qty in balances['coins'].items():
        try:
            price = get_price(f"{coin}USDT")
            if price > 0:
                total += qty * price
        except: pass
    return total

def format_qty(coin, qty):
    if coin in ['BOME', 'NEIRO']:
        return int(qty / 100) * 100
    elif coin in ['PUMP', 'PEPE', 'SHIB', 'FLOKI', 'WIF', 'BONK', 'AI', 'COOKIE', 'BABYDOGE']:
        return int(qty / 1000) * 1000
    elif coin == 'TURBO':
        return int(qty / 1000) * 1000
    elif coin in ['BTC', 'ETH']:
        return round(qty * 0.99, 5)
    else:
        return round(qty * 0.99, 3)

def place_order(symbol, side, quantity):
    try:
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
        result = api_signed_post("/api/v3/order", params)
        log(f"下单: {symbol} {side} {quantity}", "TRADE")
        return result
    except Exception as e:
        log(f"下单失败: {e}", "ERROR")
        return None

def execute_buy(coin, confidence, total_value):
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0:
        log(f"{coin}: 获取价格失败", "ERROR")
        return False
    
    position_value = total_value * MAX_POSITION_PCT * max(0.5, confidence)
    quantity = position_value / price
    quantity = format_qty(coin, quantity)
    
    if quantity * price < MIN_TRADE_USDT:
        log(f"{coin}: 金额不足", "WARNING")
        return False
    
    result = place_order(symbol, "BUY", quantity)
    return result and 'orderId' in result

def execute_sell(coin, qty):
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0:
        log(f"{coin}: 获取价格失败", "ERROR")
        return False
    
    quantity = format_qty(coin, qty)
    if quantity * price < MIN_TRADE_USDT:
        return False
    
    result = place_order(symbol, "SELL", quantity)
    return result and 'orderId' in result

class G31Live:
    def __init__(self):
        self.running = False
        self.go_core = None
        self.last_trades = {}  # coin -> timestamp
        self.trade_history = []
        
        if GOCORE_AVAILABLE:
            log("初始化go-core...")
            self.go_core = GoCore(num_agents=300)
            log(f"go-core初始化完成")
        else:
            log("go-core不可用，退出", "ERROR")
            sys.exit(1)
    
    def predict(self, coin):
        if self.go_core:
            return self.go_core.predict(coin, interval='1h', period='7d')
        return None
    
    def scan_and_trade(self):
        balances = get_account()
        total_value = get_total_value(balances)
        usdt = balances['usdt']
        
        log(f"账户: USDT={usdt:.2f} 总计=${total_value:.2f}", "INFO")
        
        holdings = list(balances['coins'].keys())
        log(f"持仓: {holdings}", "INFO")
        
        # 检查止损/止盈
        for coin in holdings[:]:
            if coin not in MAJOR_COINS and coin not in MEME_COINS:
                continue
            
            symbol = f"{coin}USDT"
            try:
                price = get_price(symbol)
                if price <= 0: continue
                
                # 获取买入价 (简化:用当前持仓量和价值反推)
                qty = balances['coins'][coin]
                value = qty * price
                
                # 检查是否需要止损
                # 这里简化处理，实际应该记录买入价
                pass
            except: pass
        
        # 买入信号
        log("\n=== 买入扫描 ===", "INFO")
        
        # Meme币扫描
        if self.go_core:
            meme_results = self.go_core.scan(tier='meme', min_score=35)
            log(f"Meme扫描结果: {len(meme_results)} 个信号", "INFO")
            
            for r in meme_results[:3]:
                log(f"  {r['coin']}: {r['signal']} {r['score']}%", "INFO")
                coin = r['coin']
                
                # 冷却检查
                if coin in self.last_trades:
                    if time.time() - self.last_trades[coin] < 300:
                        continue
                
                # 检查是否已持仓
                if coin in balances['coins']:
                    continue
                
                # 检查USDT是否足够
                if usdt < MIN_TRADE_USDT * 2:
                    continue
                
                confidence = r['score'] / 100
                
                if execute_buy(coin, confidence, total_value):
                    self.last_trades[coin] = time.time()
                    self.trade_history.append({
                        'coin': coin,
                        'action': 'BUY',
                        'confidence': confidence,
                        'time': time.time()
                    })
                    log(f"买入完成: {coin} 置信度{confidence:.0%}", "TRADE")
                    break
        
        # 主流币扫描
        log("\n=== 主流币扫描 ===", "INFO")
        if self.go_core:
            major_results = self.go_core.scan(tier='main', min_score=35)
            log(f"主流币扫描结果: {len(major_results)} 个信号", "INFO")
            
            for r in major_results[:2]:
                log(f"  {r['coin']}: {r['signal']} {r['score']}%", "INFO")
                coin = r['coin']
                
                if coin in self.last_trades:
                    if time.time() - self.last_trades[coin] < 300:
                        continue
                
                if coin in balances['coins']:
                    continue
                
                if usdt < MIN_TRADE_USDT * 2:
                    continue
                
                confidence = r['score'] / 100
                
                if execute_buy(coin, confidence, total_value):
                    self.last_trades[coin] = time.time()
                    self.trade_history.append({
                        'coin': coin,
                        'action': 'BUY',
                        'confidence': confidence,
                        'time': time.time()
                    })
                    log(f"买入完成: {coin} 置信度{confidence:.0%}", "TRADE")
                    break
        
        # 更新账户
        balances = get_account()
        total_value = get_total_value(balances)
        log(f"\n当前总资产: ${total_value:.2f}", "INFO")
        
    def run(self):
        log("="*60, "INFO")
        log("G31 Live Trading 启动", "INFO")
        log("="*60, "INFO")
        
        self.running = True
        scan_count = 0
        
        while self.running:
            try:
                scan_count += 1
                ts = datetime.now().strftime("%H:%M:%S")
                log(f"\n{'='*60}", "INFO")
                log(f"扫描 #{scan_count} ({ts})", "INFO")
                
                self.scan_and_trade()
                
                log(f"等待60秒...", "INFO")
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                log(f"错误: {e}", "ERROR")
                time.sleep(10)
        
        log("G31 Live Trading 停止", "INFO")
    
    def stop(self):
        self.running = False

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║     G31 Live Trading - 实盘交易系统       ║
║        go-core + 自动交易                ║
╚══════════════════════════════════════════════╝
    """)
    
    g31 = G31Live()
    
    try:
        g31.run()
    except KeyboardInterrupt:
        print("\n停止中...")
        g31.stop()
    except Exception as e:
        log(f"FATAL: {e}", "ERROR")
        raise
