#!/usr/bin/env python3
"""
go-fastlane - 快慢自适应双通道引擎
主路(30秒) + 快车道(3秒) + 插针捕捉
"""
import math, json, time, urllib.request, threading
from datetime import datetime
from collections import defaultdict
import hmac, hashlib

# ============================================
# Configuration
# ============================================
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','DOT','LINK','UNI','AVAX','MATIC','ATOM','LTC','ETC','AAVE','APT','NEAR','FIL']
MEME_COINS = ['PEPE','SHIB','FLOKI','WIF','BABYDOGE','COOKIE','AI','NEIRO','BOME','TURBO','PUMP','BONK']

# ============================================
# Data Utilities
# ============================================
def api_get(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())

def get_klines(symbol, interval='1h', limit=100):
    try:
        return api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    except: return []

def get_price(symbol):
    try:
        return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

def get_24hr_ticker(symbol):
    try:
        data = api_get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}')
        return {
            'price': float(data['lastPrice']),
            'change_1h': float(data.get('priceChangePercent', 0)),
            'volume': float(data['volume']),
            'quote_volume': float(data['quoteVolume'])
        }
    except: return None

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
    return json.loads(opener.open(req, timeout=10).read().decode())

def place_market_order(symbol, side, quantity):
    params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
    return api_signed_post("/api/v3/order", params)

# ============================================
# Price Cache
# ============================================
class PriceCache:
    def __init__(self):
        self.prices = {}  # coin -> {price, time, history[]}
        self.history_len = 60  # Keep 60 data points
        
    def update(self, coin, price):
        now = time.time()
        if coin not in self.prices:
            self.prices[coin] = {'price': price, 'time': now, 'history': []}
        else:
            self.prices[coin]['price'] = price
            self.prices[coin]['time'] = now
            
        # Add to history
        self.prices[coin]['history'].append({'price': price, 'time': now})
        
        # Trim history
        cutoff = now - 300  # 5 minutes
        self.prices[coin]['history'] = [
            h for h in self.prices[coin]['history'] if h['time'] > cutoff
        ]
        
    def get_change(self, coin, minutes=1):
        if coin not in self.prices or len(self.prices[coin]['history']) < 2:
            return 0, 0
            
        now = time.time()
        cutoff = now - minutes * 60
        
        hist = [h for h in self.prices[coin]['history'] if h['time'] > cutoff]
        
        if len(hist) < 2:
            return 0, 0
            
        oldest = hist[0]['price']
        newest = hist[-1]['price']
        change_pct = (newest - oldest) / oldest * 100 if oldest > 0 else 0
        change_abs = newest - oldest
        
        return change_pct, change_abs

# ============================================
# Flash Signal Detector (快车道)
# ============================================
class FlashDetector:
    """插针检测器"""
    
    def __init__(self, cache):
        self.cache = cache
        self.threshold_1m = 1.0    # 1分钟1%触发
        self.threshold_3m = 2.0    # 3分钟2%触发
        self.volume_ratio = 3.0    # 成交量3倍
        self.rsi_change_threshold = 8
        
    def check(self, coin):
        """检测插针"""
        # Get price changes
        change_1m, _ = self.cache.get_change(coin, 1)
        change_3m, _ = self.cache.get_change(coin, 3)
        
        # Get current price
        price = get_price(f"{coin}USDT")
        if price <= 0:
            return None
            
        # Check triggers
        triggers = []
        
        if abs(change_1m) >= self.threshold_1m:
            triggers.append(f"1m变动{change_1m:+.1f}%")
            
        if abs(change_3m) >= self.threshold_3m:
            triggers.append(f"3m变动{change_3m:+.1f}%")
        
        if triggers:
            # Calculate confidence
            confidence = min(0.95, 0.5 + abs(change_1m) * 0.1)
            
            signal_type = "FLASH_BUY" if change_1m > 0 else "FLASH_SELL"
            
            return {
                'level': 'L1',
                'type': signal_type,
                'coin': coin,
                'price': price,
                'change_1m': change_1m,
                'change_3m': change_3m,
                'triggers': triggers,
                'confidence': confidence,
                'action': f"{signal_type.replace('FLASH_','')} {coin}",
                'execution_time': '< 5s',
                'auto_execute': True
            }
            
        return None

# ============================================
# Main Lane Detector (主路)
# ============================================
class MainDetector:
    """主路检测器"""
    
    def __init__(self, cache):
        self.cache = cache
        
    def get_rsi(self, coin):
        """计算RSI"""
        data = get_klines(f"{coin}USDT", '1h', 50)
        if len(data) < 15:
            return 50
        closes = [float(k[4]) for k in data]
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-14:]]
        losses = [-d if d<0 else 0 for d in deltas[-14:]]
        avg_gain = sum(gains)/14
        avg_loss = sum(losses)/14
        if avg_loss == 0:
            return 100
        return 100-(100/(1+avg_gain/avg_loss))
        
    def get_momentum(self, coin):
        """计算动量"""
        data = get_klines(f"{coin}USDT", '1h', 25)
        if len(data) < 24:
            return 0
        return ((float(data[-1][4]) - float(data[-24][4])) / float(data[-24][4])) * 100
        
    def oracle_score(self, coin):
        """Oracle评分"""
        rsi = self.get_rsi(coin)
        momentum = self.get_momentum(coin)
        
        score = 0
        
        # RSI
        if rsi < 25: score += 50
        elif rsi < 30: score += 40
        elif rsi < 35: score += 25
        elif rsi < 40: score += 10
        elif rsi > 75: score -= 50
        elif rsi > 70: score -= 35
        elif rsi > 65: score -= 20
        elif rsi > 60: score -= 10
        
        # Momentum
        if momentum < -4: score += 30
        elif momentum < -2: score += 20
        elif momentum < 0: score += 10
        elif momentum > 4: score -= 30
        elif momentum > 2: score -= 20
        
        return score, rsi, momentum
        
    def check(self, coin):
        """主路检测"""
        score, rsi, momentum = self.oracle_score(coin)
        price = get_price(f"{coin}USDT")
        
        if score >= 50:
            signal = "STRONG_BUY"
        elif score >= 20:
            signal = "BUY"
        elif score >= -20:
            signal = "HOLD"
        elif score >= -50:
            signal = "SELL"
        else:
            signal = "STRONG_SELL"
            
        return {
            'level': 'L2' if score >= 50 or score <= -50 else 'L3',
            'type': signal,
            'coin': coin,
            'score': score,
            'rsi': rsi,
            'momentum': momentum,
            'price': price,
            'confidence': min(1.0, abs(score) / 50)
        }

# ============================================
# Fastlane Engine
# ============================================
class FastlaneEngine:
    """快慢自适应双通道引擎"""
    
    def __init__(self):
        self.cache = PriceCache()
        self.flash_detector = FlashDetector(self.cache)
        self.main_detector = MainDetector(self.cache)
        
        self.main_interval = 30
        self.fast_interval = 3
        self.auto_execute = True
        
        self.main_signals = {}
        self.flash_signals = {}
        
        self.main_running = False
        self.fast_running = False
        self.main_thread = None
        self.fast_thread = None
        
        self.watch_coins = MAJOR_COINS + MEME_COINS
        
    def start(self, main_interval=30, fast_interval=3, 
              flash_threshold=1.0, auto_execute=True):
        """启动双通道"""
        self.main_interval = main_interval
        self.fast_interval = fast_interval
        self.auto_execute = auto_execute
        
        self.flash_detector.threshold_1m = flash_threshold
        
        self.main_running = True
        self.fast_running = True
        
        # Start main lane thread
        self.main_thread = threading.Thread(target=self._main_loop)
        self.main_thread.daemon = True
        self.main_thread.start()
        
        # Start fast lane thread
        self.fast_thread = threading.Thread(target=self._fast_loop)
        self.fast_thread.daemon = True
        self.fast_thread.start()
        
        print(f"🚀 Fastlane started - Main:{main_interval}s Fast:{fast_interval}s Threshold:{flash_threshold}%")
        
    def stop(self):
        """停止双通道"""
        self.main_running = False
        self.fast_running = False
        print("⏹️ Fastlane stopped")
        
    def _main_loop(self):
        """主路循环"""
        while self.main_running:
            try:
                for coin in self.watch_coins:
                    price = get_price(f"{coin}USDT")
                    if price > 0:
                        self.cache.update(coin, price)
                        
                    signal = self.main_detector.check(coin)
                    self.main_signals[coin] = signal
                    
                time.sleep(self.main_interval)
            except Exception as e:
                print(f"Main lane error: {e}")
                time.sleep(5)
                
    def _fast_loop(self):
        """快车道循环"""
        while self.fast_running:
            try:
                # Check flash signals on important coins
                for coin in self.watch_coins[:20]:  # Top 20
                    # Update price
                    price = get_price(f"{coin}USDT")
                    if price > 0:
                        self.cache.update(coin, price)
                    
                    # Check flash
                    flash = self.flash_detector.check(coin)
                    if flash:
                        self.flash_signals[coin] = flash
                        
                        print(f"\n🔥 FLASH DETECTED: {coin}")
                        print(f"   1m变动: {flash['change_1m']:+.1f}%")
                        print(f"   3m变动: {flash['change_3m']:+.1f}%")
                        print(f"   触发原因: {', '.join(flash['triggers'])}")
                        print(f"   置信度: {flash['confidence']:.0%}")
                        
                        # Auto execute
                        if self.auto_execute:
                            self._execute_flash(flash)
                
                time.sleep(self.fast_interval)
            except Exception as e:
                print(f"Fast lane error: {e}")
                time.sleep(1)
                
    def _execute_flash(self, flash):
        """执行快车道信号"""
        coin = flash['coin']
        action = flash['type']  # FLASH_BUY or FLASH_SELL
        
        # Determine quantity
        try:
            if coin in ['BOME', 'NEIRO']:
                qty = 10000
            elif coin in ['PEPE', 'SHIB', 'FLOKI', 'WIF', 'BONK', 'AI', 'COOKIE', 'PUMP']:
                qty = 50000
            elif coin == 'TURBO':
                qty = 5000
            else:
                qty = 10  # Major coins
                
            symbol = f"{coin}USDT"
            side = "BUY" if "BUY" in action else "SELL"
            
            result = place_market_order(symbol, side, qty)
            if result and 'orderId' in str(result):
                print(f"   ✅ 快车道执行成功: {side} {qty} {coin}")
            else:
                print(f"   ❌ 执行失败")
        except Exception as e:
            print(f"   ❌ 执行错误: {e}")
            
    def get_signals(self):
        """获取所有信号"""
        return {
            'main': self.main_signals,
            'flash': self.flash_signals
        }
        
    def get_flash_signals(self):
        """获取快车道信号"""
        return self.flash_signals
        
    def get_main_signals(self):
        """获取主路信号"""
        return self.main_signals
        
    def check_flash(self, coin):
        """手动检查快车道"""
        price = get_price(f"{coin}USDT")
        if price > 0:
            self.cache.update(coin, price)
        return self.flash_detector.check(coin)
        
    def check_main(self, coin):
        """手动检查主路"""
        return self.main_detector.check(coin)
        
    def get_top_signals(self, n=5):
        """获取最强信号"""
        signals = []
        for coin, sig in self.main_signals.items():
            if sig['type'] in ['STRONG_BUY', 'BUY']:
                signals.append(sig)
        return sorted(signals, key=lambda x: x['score'], reverse=True)[:n]
        
    def status(self):
        """获取状态"""
        flash_count = len(self.flash_signals)
        main_count = len(self.main_signals)
        active_flashes = [f for f in self.flash_signals.values() if f['confidence'] > 0.7]
        
        return {
            'main_running': self.main_running,
            'fast_running': self.fast_running,
            'main_interval': self.main_interval,
            'fast_interval': self.fast_interval,
            'total_signals': main_count,
            'flash_signals': flash_count,
            'active_flashes': len(active_flashes)
        }

# ============================================
# Main
# ============================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("go-fastlane - 快慢自适应双通道")
        print("Usage:")
        print("  python fastlane_engine.py start [main_interval] [fast_interval] [threshold]")
        print("  python fastlane_engine.py flash <coin>")
        print("  python fastlane_engine.py status")
        print("  python fastlane_engine.py stop")
        sys.exit(1)
        
    cmd = sys.argv[1]
    engine = FastlaneEngine()
    
    if cmd == 'start':
        main_int = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        fast_int = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        
        engine.start(main_interval=main_int, fast_interval=fast_int, 
                    flash_threshold=threshold)
        
        print("\n双通道运行中，按 Ctrl+C 停止...")
        try:
            while True:
                time.sleep(10)
                status = engine.status()
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Main:{status['main_running']} Fast:{status['fast_running']} Signals:{status['total_signals']} Flashes:{status['flash_signals']}", end='')
        except KeyboardInterrupt:
            engine.stop()
            
    elif cmd == 'flash' and len(sys.argv) > 2:
        coin = sys.argv[2].upper()
        print(f"\n🔍 检查快车道: {coin}")
        result = engine.check_flash(coin)
        if result:
            print(f"🔥 插针信号!")
            print(f"   类型: {result['type']}")
            print(f"   1m变动: {result['change_1m']:+.1f}%")
            print(f"   置信度: {result['confidence']:.0%}")
        else:
            print(f"✅ 无插针信号")
            
    elif cmd == 'status':
        status = engine.status()
        print(f"\n📊 Fastlane 状态:")
        print(f"   主路: {'运行中' if status['main_running'] else '已停止'}")
        print(f"   快车道: {'运行中' if status['fast_running'] else '已停止'}")
        print(f"   主路间隔: {status['main_interval']}s")
        print(f"   快车道间隔: {status['fast_interval']}s")
        print(f"   总信号数: {status['total_signals']}")
        print(f"   插针信号数: {status['flash_signals']}")
        
    elif cmd == 'stop':
        engine.stop()
