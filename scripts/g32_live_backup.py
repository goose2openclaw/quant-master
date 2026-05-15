#!/usr/bin/env python3
"""
G32 Optimized Trading - 收益最大化自动交易系统
功能: 钱包管理、智能调仓、止损止盈、多维度信号
"""

import urllib.request, hmac, hashlib, time, json, sys, math, threading
from datetime import datetime
from collections import defaultdict, deque

sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-core')

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g32_live.log"

# ============ 核心参数优化 ============
MIN_TRADE_USDT = 1           # 最低交易金额
MAX_POSITION_PCT = 0.15      # 最大仓位比例 (15%)
STOP_LOSS = 0.05            # 止损5%
TAKE_PROFIT = 0.25          # 止盈25%
TRAILING_STOP = 0.08         # 追踪止损8%
SCAN_INTERVAL = 20          # 扫描间隔(秒)
MIN_CONFIDENCE = 0.35        # 最低置信度
MIN_PROFIT_SWITCH = 0.04    # 调仓最小收益差

MAJOR_COINS = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','DOT','LINK','UNI','AVAX','MATIC','ATOM','LTC','ETC','AAVE','APT','NEAR','FIL','ICP','INJ','TIA','SEI','SUI','OP','ARB','LDO','CRV','RDNT','ENS']
MEME_COINS = ['PEPE','SHIB','FLOKI','WIF','BABYDOGE','COOKIE','AI','NEIRO','BOME','TURBO','PUMP','BONK']

# ============ 全局变量 ============
GOCORE_AVAILABLE = False
g32_core = None
trade_history = deque(maxlen=1000)  # 交易历史
position_prices = {}  # 持仓买入价
accuracy_tracker = {'correct': 0, 'total': 0, 'window': deque(maxlen=50)}

try:
    from go_core import GoCore
    GOCORE_AVAILABLE = True
except:
    print("警告: go-core不可用，使用RSI备选方案")

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
    except: return None

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

def get_prices(symbols):
    """批量获取价格"""
    prices = {}
    for s in symbols:
        prices[s] = get_price(f"{s}USDT")
    return prices

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

def get_exchange_info(symbol):
    """获取交易对精度信息"""
    try:
        data = api_get(f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}')
        if data and 'symbols' in data:
            sym = data['symbols'][0]
            filters = {f['filterType']: f for f in sym['filters']}
            lot_size = filters.get('LOT_SIZE', {})
            step_size = float(lot_size.get('stepSize', 1.0))
            min_qty = float(lot_size.get('minQty', 0))
            precision = 0
            if step_size < 1:
                precision = len(str(step_size).split('.')[-1].rstrip('0'))
            return {'stepSize': step_size, 'minQty': min_qty, 'precision': precision}
    except:
        pass
    return {'stepSize': 1.0, 'minQty': 0, 'precision': 0}

def format_qty(coin, qty):
    """格式化数量"""
    if qty <= 0:
        return 0
    symbol = f"{coin}USDT"
    info = get_exchange_info(symbol)
    step_size = info['stepSize']
    min_qty = info['minQty']
    precision = info['precision']
    
    formatted = math.floor(qty / step_size) * step_size
    formatted = round(formatted, precision) if precision > 0 else int(formatted)
    
    if formatted < min_qty:
        return 0
    return formatted

def place_order(symbol, side, quantity):
    try:
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity
        }
        result = api_signed_post("/api/v3/order", params)
        if 'orderId' in result:
            log(f"订单成功: {side} {quantity} {symbol}", "TRADE")
            return result
        else:
            log(f"订单失败: {result}", "ERROR")
            return None
    except Exception as e:
        log(f"下单异常: {e}", "ERROR")
        return None

def execute_buy(coin, confidence, total_value):
    """执行买入"""
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0:
        log(f"{coin}: 获取价格失败", "ERROR")
        return False
    
    position_value = total_value * MAX_POSITION_PCT * max(0.5, confidence)
    quantity = position_value / price
    quantity = format_qty(coin, quantity)
    
    if quantity * price < MIN_TRADE_USDT:
        log(f"{coin}: 金额不足 ${quantity * price:.2f}", "WARNING")
        return False
    
    result = place_order(symbol, "BUY", quantity)
    if result and 'orderId' in result:
        position_prices[coin] = price  # 记录买入价
        return True
    return False

def execute_sell(coin, qty=None, reason=""):
    """执行卖出"""
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0:
        log(f"{coin}: 获取价格失败", "ERROR")
        return False
    
    if qty is None:
        balances = get_account()
        qty = balances['coins'].get(coin, 0)
    
    quantity = format_qty(coin, qty)
    if quantity * price < MIN_TRADE_USDT:
        return False
    
    result = place_order(symbol, "SELL", quantity)
    if result and 'orderId' in result:
        if coin in position_prices:
            entry = position_prices.pop(coin)
            pnl = (price - entry) / entry * 100
            log(f"卖出{coin}: {reason} 盈亏{ pnl:+.2f}%", "TRADE")
            # 更新准确率
            accuracy_tracker['total'] += 1
            if pnl > 0:
                accuracy_tracker['correct'] += 1
        return True
    return False

def execute_switch(from_coin, to_coin, confidence_diff):
    """智能调仓: 从低信心币种切换到高信心币种"""
    balances = get_account()
    if from_coin not in balances['coins']:
        return False
    
    from_price = get_price(f"{from_coin}USDT")
    to_price = get_price(f"{to_coin}USDT")
    qty = balances['coins'][from_coin]
    
    if from_price <= 0 or to_price <= 0:
        return False
    
    # 先卖出
    quantity = format_qty(from_coin, qty)
    sell_result = place_order(f"{from_coin}USDT", "SELL", quantity)
    if not sell_result or 'orderId' not in sell_result:
        return False
    
    time.sleep(1)
    
    # 再买入
    usdt_value = qty * from_price
    to_qty = usdt_value / to_price
    to_qty = format_qty(to_coin, to_qty)
    
    buy_result = place_order(f"{to_coin}USDT", "BUY", to_qty)
    if buy_result and 'orderId' in buy_result:
        position_prices[to_coin] = to_price
        log(f"调仓完成: {from_coin} → {to_coin} (信心差{confidence_diff:+.0f}%)", "TRADE")
        return True
    
    return False

# ============ RSI备选信号 ============
def get_rsi(coin, period=14):
    """获取RSI"""
    try:
        url = f'https://api.binance.com/api/v3/klines?symbol={coin}USDT&interval=1h&limit=100'
        data = api_get(url)
        if not data:
            return 50
        closes = [float(d[4]) for d in data]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except:
        return 50

def get_ma(coin, period=20):
    """获取MA"""
    try:
        url = f'https://api.binance.com/api/v3/klines?symbol={coin}USDT&interval=1h&limit={period+1}'
        data = api_get(url)
        if not data:
            return 0
        closes = [float(d[4]) for d in data]
        return sum(closes[-period:]) / period
    except:
        return 0

def get_volatility(coin):
    """获取波动率"""
    try:
        url = f'https://api.binance.com/api/v3/klines?symbol={coin}USDT&interval=1h&limit=24'
        data = api_get(url)
        if not data:
            return 0
        highs = [float(d[2]) for d in data]
        lows = [float(d[3]) for d in data]
        closes = [float(d[4]) for d in data]
        avg_range = sum(h - l for h, l in zip(highs, lows)) / len(highs)
        return avg_range / (sum(closes) / len(closes))
    except:
        return 0

def get_signal_rsi(coin):
    """RSI备选信号"""
    rsi = get_rsi(coin)
    ma5 = get_ma(coin, 5)
    ma20 = get_ma(coin, 20)
    price = get_price(f"{coin}USDT")
    
    score = 50
    signal = "hold"
    
    # RSI超卖 + MA多头
    if rsi < 35 and ma5 > ma20:
        score = 70 + (35 - rsi)
        signal = "buy"
    elif rsi > 70:
        score = 70 + (rsi - 70)
        signal = "sell"
    
    # 波动率调整
    vol = get_volatility(coin)
    if vol > 0.05:  # 高波动
        score *= 0.9
    
    return {
        'signal': signal,
        'confidence': score / 100,
        'score': score,
        'rsi': rsi,
        'reasoning': [f"RSI:{rsi:.1f}", f"波动率:{vol:.3f}"]
    }

# ============ G32核心类 ============
class G32Optimized:
    def __init__(self):
        self.running = False
        self.go_core = None
        self.last_trades = {}
        self.scan_count = 0
        self.total_value_start = 0
        self.best_coin = None
        self.worst_coin = None
        
        if GOCORE_AVAILABLE:
            log("初始化go-core...")
            self.go_core = GoCore(num_agents=300)
            log("go-core初始化完成")
        else:
            log("使用RSI备选方案")
    
    def predict(self, coin):
        """获取信号"""
        if self.go_core:
            try:
                return self.go_core.predict(coin, interval='1h', period='7d')
            except:
                pass
        return get_signal_rsi(coin)
    
    def scan(self, tier='all', min_score=40):
        """扫描所有币种"""
        coins = MAJOR_COINS + MEME_COINS if tier == 'all' else (MEME_COINS if tier == 'meme' else MAJOR_COINS)
        results = []
        
        for coin in coins:
            try:
                result = self.predict(coin)
                if result['confidence'] >= min_score / 100:
                    results.append({
                        'coin': coin,
                        'signal': result['signal'],
                        'confidence': result['confidence'],
                        'score': result['score'],
                        'reasoning': result.get('reasoning', [])
                    })
            except:
                pass
        
        # 按信心度排序
        results.sort(key=lambda x: -x['confidence'])
        return results
    
    def check_stop_loss_take_profit(self, balances):
        """检查止损止盈"""
        changed = False
        for coin, entry_price in list(position_prices.items()):
            if coin not in balances['coins']:
                continue
            
            current_price = get_price(f"{coin}USDT")
            if current_price <= 0:
                continue
            
            pnl_pct = (current_price - entry_price) / entry_price
            
            # 追踪止损
            if hasattr(self, 'peak_prices') and coin in self.peak_prices:
                peak = self.peak_prices[coin]
                if current_price > peak:
                    self.peak_prices[coin] = current_price
                    trail_stop = (peak - current_price) / peak
                    if trail_stop > TRAILING_STOP:
                        execute_sell(coin, reason="追踪止损")
                        changed = True
                        continue
            
            # 止盈/止损
            if pnl_pct <= -STOP_LOSS:
                execute_sell(coin, reason=f"止损({pnl_pct:.1%})")
                changed = True
            elif pnl_pct >= TAKE_PROFIT:
                execute_sell(coin, reason=f"止盈({pnl_pct:.1%})")
                changed = True
        
        return changed
    
    def find_worst_holding(self, balances, prices):
        """找到表现最差的持仓"""
        worst = None
        worst_pnl = 0
        
        for coin, entry_price in position_prices.items():
            if coin not in balances['coins']:
                continue
            current_price = prices.get(coin, 0)
            if current_price <= 0:
                continue
            pnl = (current_price - entry_price) / entry_price
            if pnl < worst_pnl:
                worst_pnl = pnl
                worst = coin
        
        return worst, worst_pnl
    
    def optimize_portfolio(self):
        """优化投资组合 - 智能调仓"""
        balances = get_account()
        prices = {}
        for coin in list(balances['coins'].keys()) + ['USDT']:
            prices[coin] = get_price(f"{coin}USDT")
        
        total_value = get_total_value(balances)
        
        # 扫描新信号
        signals = self.scan(min_score=MIN_CONFIDENCE * 100)
        
        if not signals:
            return
        
        best_signal = signals[0]
        
        # 找最差持仓
        worst_coin, worst_pnl = self.find_worst_holding(balances, prices)
        
        # 如果有更好的信号且当前持仓表现差，考虑调仓
        if worst_coin and worst_pnl < -0.03:  # 亏损超过3%
            best_new_confidence = best_signal['confidence']
            
            # 检查最差币的信号
            worst_signal = self.predict(worst_coin)
            
            # 如果新信号明显更好
            if best_new_confidence - worst_signal['confidence'] > MIN_PROFIT_SWITCH:
                log(f"调仓检查: {worst_coin}({worst_pnl:.1%}) → {best_signal['coin']}({best_new_confidence:.0%})", "INFO")
                execute_switch(worst_coin, best_signal['coin'], best_new_confidence - worst_signal['confidence'])
    
    def execute_buys(self, balances, total_value, usdt):
        """执行买入"""
        signals = self.scan(min_score=MIN_CONFIDENCE * 100)
        
        for r in signals[:5]:  # 最多5个
            coin = r['coin']
            
            # 冷却检查
            if coin in self.last_trades and time.time() - self.last_trades[coin] < 180:
                continue
            
            # 已持仓检查
            if coin in balances['coins']:
                continue
            
            # 资金检查
            if usdt < MIN_TRADE_USDT * 3:
                break
            
            confidence = r['confidence']
            
            if execute_buy(coin, confidence, total_value):
                self.last_trades[coin] = time.time()
                trade_history.append({
                    'coin': coin,
                    'action': 'BUY',
                    'confidence': confidence,
                    'price': get_price(f"{coin}USDT"),
                    'time': time.time()
                })
                log(f"买入: {coin} 信心{confidence:.0%} 理由:{r.get('reasoning', [])}", "TRADE")
                usdt = get_account()['usdt']  # 更新余额
    
    def execute_sells(self, balances):
        """执行卖出"""
        signals = self.scan(min_score=30)
        sell_signals = {r['coin']: r for r in signals if r['signal'] == 'sell' or r['confidence'] < 0.35}
        
        for coin in list(balances['coins'].keys()):
            if coin not in MAJOR_COINS and coin not in MEME_COINS:
                continue
            
            if coin in sell_signals:
                r = sell_signals[coin]
                log(f"卖出信号: {coin} 信心{r['confidence']:.0%}", "INFO")
                execute_sell(coin, reason=f"SELL信号({r['confidence']:.0%})")
    
    def run(self):
        log("=" * 60, "INFO")
        log("G32 Optimized Trading 启动 - 收益最大化", "INFO")
        log("=" * 60, "INFO")
        
        self.running = True
        self.peak_prices = {}
        
        # 初始化总价值
        balances = get_account()
        self.total_value_start = get_total_value(balances)
        log(f"初始总资产: ${self.total_value_start:.2f}", "INFO")
        
        while self.running:
            try:
                self.scan_count += 1
                ts = datetime.now().strftime("%H:%M:%S")
                log(f"\n{'='*60}", "INFO")
                log(f"扫描 #{self.scan_count} ({ts})", "INFO")
                
                # 获取账户
                balances = get_account()
                total_value = get_total_value(balances)
                usdt = balances['usdt']
                
                log(f"账户: USDT={usdt:.2f} 总计=${total_value:.2f}", "INFO")
                log(f"持仓: {list(balances['coins'].keys())}", "INFO")
                
                # 收益报告
                if self.total_value_start > 0:
                    pnl = (total_value - self.total_value_start) / self.total_value_start * 100
                    log(f"本次收益: {pnl:+.2f}%", "INFO")
                
                # 检查止损止盈
                self.check_stop_loss_take_profit(balances)
                
                # 优化投资组合
                self.optimize_portfolio()
                
                # 执行交易
                self.execute_buys(balances, total_value, usdt)
                self.execute_sells(balances)
                
                # 最终状态
                balances = get_account()
                total_value = get_total_value(balances)
                log(f"\n当前总资产: ${total_value:.2f}", "INFO")
                
                # 准确率
                if accuracy_tracker['total'] > 0:
                    acc = accuracy_tracker['correct'] / accuracy_tracker['total'] * 100
                    log(f"信号准确率: {acc:.1f}% ({accuracy_tracker['correct']}/{accuracy_tracker['total']})", "INFO")
                
                log(f"等待{SCAN_INTERVAL}秒...", "INFO")
                for _ in range(SCAN_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                log(f"错误: {e}", "ERROR")
                import traceback
                traceback.print_exc()
                time.sleep(10)
        
        log("G32 Optimized Trading 停止", "INFO")
    
    def stop(self):
        self.running = False

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║     G32 Optimized Trading - 收益最大化     ║
║   智能调仓 | 止损止盈 | 钱包管理        ║
╚══════════════════════════════════════════════╝
    """)
    
    g32 = G32Optimized()
    
    try:
        g32.run()
    except KeyboardInterrupt:
        print("\n停止中...")
        g32.stop()
    except Exception as e:
        log(f"FATAL: {e}", "ERROR")
        raise
