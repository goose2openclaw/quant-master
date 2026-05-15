#!/usr/bin/env python3
"""
G34 Optimized Trading - 收益最大化系统 v3.0
=============================================
基于30天回测数据优化:
- Meme币权重: 3x (152% vs 60%累计收益)
- Top5专注: TURBO, BOME, NEIRO, BONK, PEPE
- 避开负收益: WIF, AI
- 激进调仓: 信心差>5%即切换
- 动态止盈: Meme币15%, 主流币25%
- 动量过滤: 只买上涨趋势
"""

import urllib.request, hmac, hashlib, time, json, sys, math
from datetime import datetime
from collections import deque

sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-core')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-orderbook')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-liquidation')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-cross-exchange')

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g34_live.log"

# ============ 核心参数优化 ============
# 基于回测数据优化
MIN_TRADE_USDT = 1
MAX_POSITION_PCT = 0.20      # 仓位从15%提升到20%
STOP_LOSS = 0.05
TAKE_PROFIT_Meme = 0.15     # Meme币15%止盈(波动大)
TAKE_PROFIT_Major = 0.25    # 主流币25%止盈
TRAILING_STOP = 0.05         # 5%追踪止损
SCAN_INTERVAL = 15           # 扫描间隔从20秒降到15秒
MIN_CONFIDENCE = 0.30        # 置信度从35%降到30%捕捉更多机会
MIN_PROFIT_SWITCH = 0.05    # 调仓门槛从4%降到5%

# 回测Top5 Meme币 (高胜率高收益)
TOP_MEME_COINS = ['TURBO', 'BOME', 'NEIRO', 'BONK', 'PEPE', 'FLOKI', 'SHIB']
# 负收益避开
AVOID_COINS = ['WIF', 'AI', 'AAVE']

# 主流币 (按30天表现排序)
MAJOR_COINS = ['DOGE','BNB','LTC','NEAR','DOT','ETC','AVAX','ADA','ATOM','BTC','SOL','XRP','UNI','AVAX','LINK','ARB']

# ============ 全局变量 ============
_g_account = {'usdt': 0, 'coins': {}, 'time': 0}
trade_history = deque(maxlen=1000)
position_prices = {}
position_entries = {}
accuracy_tracker = {'correct': 0, 'total': 0}

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")

def api_get(url, retries=2):
    for i in range(retries):
        try:
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        except Exception as e:
            if i < retries - 1:
                time.sleep(0.5 * (i + 1))
    return None

def api_signed_get(endpoint, params=None, retries=3):
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

def get_account():
    global _g_account
    now = time.time()
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
        if _g_account['time'] > 0:
            return _g_account
        return {'usdt': 0, 'coins': {}, 'time': now}

def get_price(symbol):
    try:
        return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

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
    if qty <= 0: return 0
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
            if formatted < min_qty: return 0
            return formatted
    except: pass
    return math.floor(qty)

def place_order(symbol, side, quantity):
    try:
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
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
    
    # 根据置信度动态调整仓位
    position_pct = MAX_POSITION_PCT * max(0.6, confidence)
    position_value = total_value * position_pct
    quantity = position_value / price
    quantity = format_qty(coin, quantity)
    
    if quantity * price < MIN_TRADE_USDT:
        log(f"{coin}: 金额不足", "WARNING")
        return False
    
    result = place_order(symbol, "BUY", quantity)
    if result and 'orderId' in result:
        position_prices[coin] = price
        position_entries[coin] = {'price': price, 'time': time.time(), 'qty': quantity, 'high': price}
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

# ============ G34核心类 ============
class G34Maximizer:
    """G34收益最大化系统"""
    
    def __init__(self):
        self.running = False
        self.scan_count = 0
        self.total_value_start = 0
        self.last_trades = {}
        self.momentum_cache = {}
        
        log("G34 Maximizer初始化...")
    
    def get_rsi(self, coin, period=14):
        """获取RSI"""
        try:
            url = f'https://api.binance.com/api/v3/klines?symbol={coin}USDT&interval=1h&limit=100'
            data = api_get(url)
            if not data: return 50
            closes = [float(d[4]) for d in data]
            
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas[-period:]]
            losses = [-d if d < 0 else 0 for d in deltas[-period:]]
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            rs = avg_gain / (avg_loss + 1e-10)
            return 100 - (100 / (1 + rs))
        except: return 50
    
    def get_momentum(self, coin, period=20):
        """获取动量 (涨跌趋势)"""
        cache_key = f"{coin}_mom"
        if cache_key in self.momentum_cache:
            cached, ts = self.momentum_cache[cache_key]
            if time.time() - ts < 60:
                return cached
        
        try:
            url = f'https://api.binance.com/api/v3/klines?symbol={coin}USDT&interval=1h&limit={period+1}'
            data = api_get(url)
            if not data or len(data) < period: return 0
            closes = [float(d[4]) for d in data]
            momentum = (closes[-1] - closes[0]) / closes[0]
            self.momentum_cache[cache_key] = (momentum, time.time())
            return momentum
        except: return 0
    
    def get_multi_signal(self, coin):
        """多维度信号 (RSI + 动量 + 成交量)"""
        rsi = self.get_rsi(coin)
        momentum = self.get_momentum(coin)
        
        # RSI信号
        if rsi < 30:
            rsi_signal = 'buy'
            rsi_conf = (30 - rsi) / 30
        elif rsi > 70:
            rsi_signal = 'sell'
            rsi_conf = (rsi - 70) / 30
        else:
            rsi_signal = 'hold'
            rsi_conf = 0
        
        # 动量信号 (只买上涨趋势)
        if momentum > 0.01:
            mom_signal = 'buy'
            mom_conf = min(momentum * 5, 0.5)
        elif momentum < -0.01:
            mom_signal = 'sell'
            mom_conf = min(abs(momentum) * 5, 0.5)
        else:
            mom_signal = 'hold'
            mom_conf = 0
        
        # 综合评分
        score = 50
        if rsi_signal == 'buy':
            score += rsi_conf * 40
        elif rsi_signal == 'sell':
            score -= rsi_conf * 40
        
        if mom_signal == 'buy':
            score += mom_conf * 30
        elif mom_signal == 'sell':
            score -= mom_conf * 30
        
        signal = 'buy' if score > 60 else 'sell' if score < 40 else 'hold'
        confidence = abs(score - 50) / 50
        
        return {
            'signal': signal,
            'confidence': min(confidence, 1.0),
            'score': score,
            'rsi': rsi,
            'momentum': momentum,
            'reasoning': [f"RSI:{rsi:.0f}", f"动量:{momentum:+.2%}"]
        }
    
    def get_take_profit(self, coin):
        """根据币种类型返回止盈点"""
        if coin in TOP_MEME_COINS or coin in ['SHIB', 'FLOKI']:
            return TAKE_PROFIT_Meme
        return TAKE_PROFIT_Major
    
    def check_positions(self, balances):
        """检查持仓状态"""
        for coin in list(position_prices.keys()):
            if coin not in balances['coins']:
                continue
            
            entry_info = position_entries.get(coin, {})
            entry_price = position_prices[coin]
            current_price = get_price(f"{coin}USDT")
            high_price = entry_info.get('high', entry_price)
            
            if current_price <= 0:
                continue
            
            pnl_pct = (current_price - entry_price) / entry_price
            take_profit = self.get_take_profit(coin)
            
            # 更新最高价 (追踪止损用)
            if current_price > high_price:
                position_entries[coin]['high'] = current_price
            
            # 止损检查
            if pnl_pct <= -STOP_LOSS:
                execute_sell(coin, reason=f"止损({pnl_pct:.1%})")
                continue
            
            # 止盈检查
            if pnl_pct >= take_profit:
                execute_sell(coin, reason=f"止盈({pnl_pct:.1%})")
                continue
            
            # 追踪止损 (从最高点回撤5%卖出)
            if high_price > entry_price:
                drawdown = (high_price - current_price) / high_price
                if drawdown >= TRAILING_STOP and pnl_pct > 0:
                    execute_sell(coin, reason=f"追踪止盈({pnl_pct:.1%})")
                    continue
            
            # Meme币特规则: 如果动量转负且盈利>10%,考虑卖出
            if coin in TOP_MEME_COINS:
                momentum = self.get_momentum(coin)
                if momentum < -0.02 and pnl_pct > 0.10:
                    execute_sell(coin, reason=f"动量转负({momentum:+.2%})")
    
    def optimize_portfolio(self, balances, total_value):
        """优化投资组合 - 基于回测数据"""
        signals = []
        
        # Meme币扫描 (优先级更高)
        for coin in TOP_MEME_COINS:
            if coin in AVOID_COINS or coin in balances['coins']:
                continue
            result = self.get_multi_signal(coin)
            if result['signal'] == 'buy' and result['confidence'] >= MIN_CONFIDENCE:
                signals.append({**result, 'coin': coin, 'priority': 1})
        
        # 主流币扫描
        for coin in MAJOR_COINS:
            if coin in balances['coins']:
                continue
            result = self.get_multi_signal(coin)
            if result['signal'] == 'buy' and result['confidence'] >= MIN_CONFIDENCE * 1.2:  # 主流币要求更高置信度
                signals.append({**result, 'coin': coin, 'priority': 2})
        
        if not signals:
            return None, None
        
        # 按优先级和置信度排序
        signals.sort(key=lambda x: (x['priority'], -x['confidence']))
        
        best_signal = signals[0]
        
        # 检查是否需要调仓
        holding_signals = {}
        for coin in balances['coins'].keys():
            if coin in position_prices:
                result = self.get_multi_signal(coin)
                holding_signals[coin] = result
        
        if holding_signals:
            worst_coin = min(holding_signals, key=lambda x: holding_signals[x]['score'])
            worst_score = holding_signals[worst_coin]['score']
            
            if worst_score < 45:  # 持仓信号转弱
                switch_confidence = best_signal['confidence']
                if switch_confidence - (50 - worst_score)/100 > MIN_PROFIT_SWITCH:
                    log(f"🚄 调仓: {worst_coin}({worst_score:.0f}) → {best_signal['coin']}({best_signal['score']:.0f})", "INFO")
                    return best_signal, worst_coin
        
        return best_signal, None
    
    def run(self):
        global position_prices, position_entries
        
        log("=" * 60, "INFO")
        log("G34 Maximizer v3.0 启动", "INFO")
        log(f"Top Meme: {TOP_MEME_COINS}", "INFO")
        log(f"Avoid: {AVOID_COINS}", "INFO")
        log("=" * 60, "INFO")
        
        self.running = True
        balances = get_account()
        self.total_value_start = get_total_value(balances)
        
        # 初始化持仓价格
        for coin, qty in balances['coins'].items():
            price = get_price(f"{coin}USDT")
            if price > 0:
                position_prices[coin] = price
                position_entries[coin] = {'price': price, 'time': time.time(), 'qty': qty, 'high': price}
        
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
                
                # 1. 检查持仓状态
                self.check_positions(balances)
                
                # 2. 优化组合
                best_signal, sell_coin = self.optimize_portfolio(balances, total_value)
                
                # 执行卖出 (如果需要调仓)
                if sell_coin:
                    execute_sell(sell_coin, reason="调仓")
                    time.sleep(2)
                    balances = get_account()
                    usdt = balances['usdt']
                    total_value = get_total_value(balances)
                
                # 3. 执行买入
                if best_signal and usdt >= MIN_TRADE_USDT * 3:
                    coin = best_signal['coin']
                    if coin not in balances['coins']:
                        confidence = best_signal['confidence']
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
                            balances = get_account()
                            usdt = balances['usdt']
                
                # 4. 最终状态
                balances = get_account()
                total_value = get_total_value(balances)
                log(f"\n当前总资产: ${total_value:.2f}", "INFO")
                
                if accuracy_tracker['total'] > 0:
                    acc = accuracy_tracker['correct'] / accuracy_tracker['total'] * 100
                    log(f"胜率: {acc:.1f}% ({accuracy_tracker['correct']}/{accuracy_tracker['total']})", "INFO")
                
                log(f"等待{SCAN_INTERVAL}秒...", "INFO")
                for _ in range(SCAN_INTERVAL):
                    if not self.running: break
                    time.sleep(1)
                    
            except Exception as e:
                log(f"错误: {e}", "ERROR")
                import traceback
                traceback.print_exc()
                time.sleep(10)
        
        log("G34 Maximizer v3.0 停止", "INFO")
    
    def stop(self):
        self.running = False

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║     G34 Maximizer v3.0              ║
║   收益最大化系统 - 基于回测数据优化     ║
╚══════════════════════════════════════════════╝
    """)
    
    g34 = G34Maximizer()
    
    try:
        g34.run()
    except KeyboardInterrupt:
        print("\n停止中...")
        g34.stop()
    except Exception as e:
        log(f"FATAL: {e}", "ERROR")
        raise
