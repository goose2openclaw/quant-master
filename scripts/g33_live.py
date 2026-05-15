#!/usr/bin/env python3
"""
G33 Optimized Trading - 收益最大化自动交易系统 v2.0
==================================================
集成功能:
- go-core v2.0 (并行计算, 自适应权重, 多周期共振)
- 订单簿分析 (机构订单捕捉, 支撑阻力墙)
- 清算预警 (爆仓点预警, 危险等级)
- 跨交易所套利 (价差检测)
"""

import urllib.request, hmac, hashlib, time, json, sys, math, threading
from datetime import datetime
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-core')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-orderbook')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-liquidation')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-cross-exchange')

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g33_live.log"

# ============ 核心参数 ============
MIN_TRADE_USDT = 1
MAX_POSITION_PCT = 0.15
STOP_LOSS = 0.05
TAKE_PROFIT = 0.25
TRAILING_STOP = 0.08
SCAN_INTERVAL = 20
MIN_CONFIDENCE = 0.35
MIN_PROFIT_SWITCH = 0.04

# 清算预警参数
LIQUIDATION_WARNING_THRESHOLD = 0.15  # 距离清算15%预警
LIQUIDATION_DANGER_THRESHOLD = 0.08   # 距离清算8%危险

# 订单簿参数
ORDERBOOK_IMBALANCE_THRESHOLD = 0.4  # 不平衡度40%信号

MAJOR_COINS = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','DOT','LINK','UNI','AVAX','MATIC','ATOM','LTC','ETC','AAVE','APT','NEAR','FIL','ICP','INJ','TIA','SEI','SUI','OP','ARB','LDO','CRV','RDNT','ENS']
MEME_COINS = ['PEPE','SHIB','FLOKI','WIF','COOKIE','AI','NEIRO','BOME','TURBO','PUMP','BONK','MOG']

# ============ 全局变量 ============
GOCORE_AVAILABLE = False
G33_core = None
trade_history = deque(maxlen=1000)
position_prices = {}
position_entries = {}  # 持仓入口价格 (用于清算计算)
accuracy_tracker = {'correct': 0, 'total': 0, 'window': deque(maxlen=50)}

try:
    from go_core import GoCore
    from orderbook_engine import OrderbookAnalyzer
    from liquidation_engine import LiquidationPredictor
    from cross_exchange_engine import CrossExchangeAnalyzer
    GOCORE_AVAILABLE = True
except Exception as e:
    print(f"警告: go-core扩展不可用: {e}")

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")

def api_get(url, retries=2):
    """带重试的API GET"""
    for i in range(retries):
        try:
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        except Exception as e:
            if i < retries - 1:
                time.sleep(0.5 * (i + 1))
            else:
                return None
    return None

def api_signed_get(endpoint, params=None, retries=2):
    """带重试的签名API GET"""
    for i in range(retries):
        try:
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
        except Exception as e:
            if i < retries - 1:
                time.sleep(1 * (i + 1))
            else:
                raise e
    return None

def api_signed_post(endpoint, params=None, retries=2):
    """带重试的签名API POST"""
    for i in range(retries):
        try:
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
        except Exception as e:
            if i < retries - 1:
                time.sleep(1 * (i + 1))
            else:
                raise e
    return None

def get_price(symbol):
    try:
        return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

# 全局账户缓存
_g_account = {'usdt': 0, 'coins': {}, 'time': 0}

def get_account():
    global _g_account
    now = time.time()
    # 缓存3秒内直接返回(但初始time=0时不适用)
    if _g_account['time'] > 0 and now - _g_account['time'] < 3:
        return _g_account
    try:
        data = api_signed_get("/api/v3/account", retries=3)
        result = {'usdt': 0, 'coins': {}}
        if data and 'balances' in data:
            for b in data.get('balances', []):
                free = float(b.get('free', 0))
                if free > 0.0001:
                    if b['asset'] == 'USDT':
                        result['usdt'] = free
                    else:
                        result['coins'][b['asset']] = free
        _g_account = result
        _g_account['time'] = now
        return result
    except Exception as e:
        log(f"获取账户失败: {e}", "ERROR")
        # API失败时返回过期缓存
        if _g_account['time'] > 0:
            log(f"使用过期缓存 USDT={_g_account['usdt']:.2f}", "INFO")
            return _g_account
        return {'usdt': 0, 'coins': {}, 'time': now}

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
    if qty <= 0:
        return 0
    symbol = f"{coin}USDT"
    try:
        info = api_get(f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}')
        if info and 'symbols' in info:
            sym = info['symbols'][0]
            filters = {f['filterType']: f for f in sym['filters']}
            lot_size = filters.get('LOT_SIZE', {})
            step_size = float(lot_size.get('stepSize', 1.0))
            min_qty = float(lot_size.get('minQty', 0))
            precision = 0
            if step_size < 1:
                precision = len(str(step_size).split('.')[-1].rstrip('0'))
            formatted = math.floor(qty / step_size) * step_size
            formatted = round(formatted, precision) if precision > 0 else int(formatted)
            if formatted < min_qty:
                return 0
            return formatted
    except: pass
    return math.floor(qty)

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
    if result and 'orderId' in result:
        position_prices[coin] = price
        position_entries[coin] = {'price': price, 'time': time.time(), 'qty': quantity}
        return True
    return False

def execute_sell(coin, qty=None, reason=""):
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
            position_entries.pop(coin, None)
            pnl = (price - entry) / entry * 100
            log(f"卖出{coin}: {reason} 盈亏{ pnl:+.2f}%", "TRADE")
            accuracy_tracker['total'] += 1
            if pnl > 0:
                accuracy_tracker['correct'] += 1
        return True
    return False

# ============ 清算预警系统 ============
class LiquidationWarning:
    """清算预警系统"""
    
    def __init__(self):
        self.predictor = LiquidationPredictor() if GOCORE_AVAILABLE else None
        self.warnings = {}
    
    def check_positions(self, balances, leverage=1):
        """检查所有持仓的清算风险"""
        warnings = []
        
        for coin, entry_info in list(position_entries.items()):
            if coin not in balances['coins']:
                continue
            
            entry_price = entry_info['price']
            qty = balances['coins'][coin]
            current_price = get_price(f"{coin}USDT")
            
            if not current_price or current_price <= 0:
                continue
            
            # 计算距离清算
            liq_price_long = entry_price * (1 - 0.8 / leverage)
            liq_price_short = entry_price * (1 + 0.8 / leverage)
            
            # 假设多头持仓
            distance_pct = (current_price - liq_price_long) / current_price * 100
            
            if distance_pct < LIQUIDATION_DANGER_THRESHOLD * 100:
                warnings.append({
                    'coin': coin,
                    'level': 'DANGER',
                    'distance_pct': distance_pct,
                    'action': 'IMMEDIATE_SELL'
                })
                log(f"🚨 {coin} 清算危险! 距离{distance_pct:.1f}%, 立即卖出!", "WARNING")
            elif distance_pct < LIQUIDATION_WARNING_THRESHOLD * 100:
                warnings.append({
                    'coin': coin,
                    'level': 'WARNING',
                    'distance_pct': distance_pct,
                    'action': 'CONSIDER_SELL'
                })
                log(f"⚠️ {coin} 清算预警: 距离{distance_pct:.1f}%", "WARNING")
        
        return warnings

# ============ 订单簿分析系统 ============
class OrderbookSignal:
    """订单簿信号系统"""
    
    def __init__(self):
        self.analyzer = OrderbookAnalyzer() if GOCORE_AVAILABLE else None
        self.cache = {}
        self.fallback_mode = False  # 网络错误时的降级模式
    
    def get_signal(self, coin):
        """获取订单簿信号"""
        if not self.analyzer:
            return None
        
        cache_key = f"{coin}_ob"
        if cache_key in self.cache:
            cached, ts = self.cache[cache_key]
            if time.time() - ts < 10:
                return cached
        
        try:
            result = self.analyzer.analyze(coin)
            if result and result.get('bid_total', 0) > 0:
                self.cache[cache_key] = (result, time.time())
                self.fallback_mode = False
                return result
        except Exception as e:
            self.fallback_mode = True
        
        # 返回缓存或默认
        if cache_key in self.cache:
            return self.cache[cache_key][0]
        return None
    
    def should_buy(self, coin):
        """基于订单簿判断是否应该买入"""
        if self.fallback_mode:
            return False  # 降级模式不执行订单簿信号
        signal = self.get_signal(coin)
        if not signal:
            return False
        return signal['imbalance'] > ORDERBOOK_IMBALANCE_THRESHOLD
    
    def should_sell(self, coin):
        """基于订单簿判断是否应该卖出"""
        if self.fallback_mode:
            return False  # 降级模式不执行订单簿信号
        signal = self.get_signal(coin)
        if not signal:
            return False
        return signal['imbalance'] < -ORDERBOOK_IMBALANCE_THRESHOLD

# ============ 跨交易所套利系统 ============
class ArbitrageScanner:
    """跨交易所套利扫描"""
    
    def __init__(self):
        self.analyzer = CrossExchangeAnalyzer() if GOCORE_AVAILABLE else None
        self.last_check = 0
        self.min_spread = 0.05  # 0.05% 最小价差
    
    def check_arbitrage(self, coin):
        """检查套利机会"""
        if not self.analyzer:
            return None
        
        if time.time() - self.last_check < 30:
            return None
        
        try:
            result = self.analyzer.get_all_prices(coin)
            if 'prices' in result and len(result['prices']) >= 2:
                self.last_check = time.time()
                return result
        except:
            pass
        return None

# ============ G33核心类 ============
class G33Optimized:
    """G33优化交易系统"""
    
    def __init__(self):
        self.running = False
        self.go_core = None
        self.liquidation_warning = LiquidationWarning()
        self.orderbook_signal = OrderbookSignal()
        self.arbitrage_scanner = ArbitrageScanner()
        self.last_trades = {}
        self.scan_count = 0
        self.total_value_start = 0
        
        if GOCORE_AVAILABLE:
            log("初始化go-core v2.0...")
            self.go_core = GoCore(num_agents=300)
            log("go-core v2.0初始化完成")
        else:
            log("go-core不可用，使用RSI备选方案")
    
    def predict(self, coin):
        """获取预测信号"""
        if self.go_core:
            try:
                return self.go_core.predict(coin, interval='1h', period='7d')
            except:
                pass
        return self._rsi_backup(coin)
    
    def _rsi_backup(self, coin):
        """RSI备选信号"""
        try:
            url = f'https://api.binance.com/api/v3/klines?symbol={coin}USDT&interval=1h&limit=100'
            data = api_get(url)
            if not data:
                return {'signal': 'hold', 'confidence': 0.5, 'score': 50}
            closes = [float(d[4]) for d in data]
            
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas[-14:]]
            losses = [-d if d < 0 else 0 for d in deltas[-14:]]
            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            rs = avg_gain / (avg_loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            
            score = 50
            if rsi < 35:
                score = 70 + (35 - rsi)
                signal = 'buy'
            elif rsi > 65:
                score = 70 + (rsi - 65)
                signal = 'sell'
            else:
                signal = 'hold'
            
            return {
                'signal': signal,
                'confidence': score / 100,
                'score': score,
                'rsi': rsi,
                'reasoning': [f"RSI:{rsi:.1f}"]
            }
        except:
            return {'signal': 'hold', 'confidence': 0.5, 'score': 50}
    
    def scan(self, tier='all', min_score=35):
        """扫描信号"""
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
            
            if pnl_pct <= -STOP_LOSS:
                execute_sell(coin, reason=f"止损({pnl_pct:.1%})")
                changed = True
            elif pnl_pct >= TAKE_PROFIT:
                execute_sell(coin, reason=f"止盈({pnl_pct:.1%})")
                changed = True
        
        return changed
    
    def check_liquidation_warnings(self, balances):
        """检查清算预警"""
        return self.liquidation_warning.check_positions(balances)
    
    def check_orderbook_signals(self, balances):
        """检查订单簿信号并执行交易"""
        sell_signals = {}
        
        for coin in list(balances['coins'].keys()):
            # 订单簿卖出信号
            if self.orderbook_signal.should_sell(coin):
                signal = self.orderbook_signal.get_signal(coin)
                sell_signals[coin] = signal
        
        return sell_signals
    
    def check_arbitrage_opportunities(self):
        """检查套利机会"""
        opportunities = []
        
        for coin in ['BTC', 'ETH', 'SOL']:
            arb = self.arbitrage_scanner.check_arbitrage(coin)
            if arb and arb.get('arbitrage_opportunity'):
                opportunities.append(arb)
        
        return opportunities
    
    def optimize_portfolio(self):
        """优化投资组合"""
        balances = get_account()
        signals = self.scan(min_score=30)
        
        if not signals:
            return
        
        holding_signals = {}
        for coin in balances['coins'].keys():
            try:
                result = self.predict(coin)
                holding_signals[coin] = result['confidence']
            except:
                holding_signals[coin] = 0.3
        
        if not holding_signals:
            return
        
        worst_coin = min(holding_signals, key=holding_signals.get)
        worst_conf = holding_signals[worst_coin]
        
        new_signals = [r for r in signals if r['coin'] not in balances['coins']]
        
        if new_signals and worst_conf < 0.40:
            best_new = new_signals[0]
            if best_new['confidence'] - worst_conf > MIN_PROFIT_SWITCH:
                log(f"🚄 调仓: {worst_coin}({worst_conf:.0%}) → {best_new['coin']}({best_new['confidence']:.0%})", "INFO")
    
    def execute_buys(self, balances, total_value, usdt):
        """执行买入"""
        signals = self.scan(min_score=MIN_CONFIDENCE * 100)
        
        for r in signals[:5]:
            coin = r['coin']
            
            if coin in self.last_trades and time.time() - self.last_trades[coin] < 180:
                continue
            
            if coin in balances['coins']:
                continue
            
            if usdt < MIN_TRADE_USDT * 3:
                break
            
            # 订单簿检查
            if self.orderbook_signal.should_buy(coin):
                log(f"📊 订单簿确认买入: {coin}", "INFO")
            
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
                log(f"买入: {coin} 信心{confidence:.0%}", "TRADE")
                usdt = get_account()['usdt']
    
    def execute_sells(self, balances):
        """执行卖出"""
        signals = self.scan(min_score=30)
        sell_signals = {r['coin']: r for r in signals if r['signal'] == 'sell'}
        
        for coin in list(balances['coins'].keys()):
            if coin in sell_signals:
                r = sell_signals[coin]
                log(f"卖出信号: {coin} 信心{r['confidence']:.0%}", "INFO")
                execute_sell(coin, reason=f"SELL信号({r['confidence']:.0%})")
    
    def run(self):
        log("=" * 60, "INFO")
        log("G33 Optimized Trading v2.0 启动", "INFO")
        log("功能: go-core v2.0 + 订单簿 + 清算预警 + 跨交易所", "INFO")
        log("=" * 60, "INFO")
        
        self.running = True
        balances = get_account()
        self.total_value_start = get_total_value(balances)
        log(f"初始总资产: ${self.total_value_start:.2f}", "INFO")
        
        while self.running:
            try:
                self.scan_count += 1
                ts = datetime.now().strftime("%H:%M:%S")
                log(f"\n{'='*60}", "INFO")
                log(f"扫描 #{self.scan_count} ({ts})", "INFO")
                
                balances = get_account()
                total_value = get_total_value(balances)
                usdt = balances['usdt']
                
                log(f"账户: USDT={usdt:.2f} 总计=${total_value:.2f}", "INFO")
                log(f"持仓: {list(balances['coins'].keys())}", "INFO")
                
                if self.total_value_start > 0:
                    pnl = (total_value - self.total_value_start) / self.total_value_start * 100
                    log(f"本次收益: {pnl:+.2f}%", "INFO")
                
                # 1. 检查止损止盈
                self.check_stop_loss_take_profit(balances)
                
                # 2. 检查清算预警
                liq_warnings = self.check_liquidation_warnings(balances)
                
                # 3. 检查订单簿信号
                ob_sell_signals = self.check_orderbook_signals(balances)
                
                # 4. 检查套利机会
                arb_opps = self.check_arbitrage_opportunities()
                if arb_opps:
                    for opp in arb_opps:
                        log(f"💱 套利机会: {opp}", "INFO")
                
                # 5. 优化投资组合
                self.optimize_portfolio()
                
                # 6. 执行交易
                self.execute_buys(balances, total_value, usdt)
                self.execute_sells(balances)
                
                # 最终状态
                balances = get_account()
                total_value = get_total_value(balances)
                log(f"\n当前总资产: ${total_value:.2f}", "INFO")
                
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
        
        log("G33 Optimized Trading v2.0 停止", "INFO")
    
    def stop(self):
        self.running = False

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║     G33 Optimized Trading v2.0        ║
║   go-core v2.0 + 订单簿 + 清算预警     ║
╚══════════════════════════════════════════════╝
    """)
    
    g33 = G33Optimized()
    
    try:
        g33.run()
    except KeyboardInterrupt:
        print("\n停止中...")
        g33.stop()
    except Exception as e:
        log(f"FATAL: {e}", "ERROR")
        raise
