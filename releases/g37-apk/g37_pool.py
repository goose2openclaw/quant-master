#!/usr/bin/env python3
"""
G37 Pool Strategy - 撞球策略终极版 v3.0
==========================================
整合Top6 Meme动态交易

架构:
- 撞球策略: 周期轮转，连续进球
- Top6 Meme: RSI<35 + 动量确认入场
- 动态止盈/止损
- go-core预测融合
- 全自动自主交易
"""

import urllib.request, hmac, hashlib, time, json, sys, math
from datetime import datetime
from collections import deque

sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-core')

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g37_pool.log"

# go-core
GOCORE_AVAILABLE = False
try:
    from go_core import GoCore
    GOCORE_AVAILABLE = True
except: print("⚠️ go-core不可用")

# ============ Top6 Meme + 撞球常量 ============
PHASE_CONSOLIDATION, PHASE_EARLY, PHASE_ACCELERATION, PHASE_PEAK, PHASE_DECLINE = 0, 1, 2, 3, 4
PHASE_NAMES = {0: "盘整", 1: "启动", 2: "加速", 3: "高峰", 4: "衰退"}

# Top6 Meme (专注高收益)
TOP6_MEME = ['BOME', 'TURBO', 'BONK', 'FLOKI', 'PEPE', 'NEIRO']
# 主流Top
TOP_MAJOR = ['DOGE', 'ADA', 'ATOM', 'DOT', 'ETC', 'NEAR']
ALL_COINS = TOP6_MEME + TOP_MAJOR

# 策略参数
MAX_ACTIVE = 3
KELLY_BASE = 0.30
STOP_LOSS = 0.05
TAKE_PROFIT_BASE = 0.15
TRAILING_STOP = 0.08
SCAN_INTERVAL = 30
SWITCH_COOLDOWN = 600

# Top6特殊参数
TOP6_RSI_ENTER = 35
TOP6_MOM_ENTER = 0.02
TOP6_STOP_LOSS = 0.05
TOP6_TAKE_PROFIT = 0.20

# ============ 全局状态 ============
_g_account = {'usdt': 0, 'coins': {}, 'time': 0}
positions = {}
last_switch = {}
history = deque(maxlen=200)
go_core = None

# ============ 工具函数 ============
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
        except:
            if i < retries - 1: time.sleep(0.3)
    return None

def api_signed(endpoint, params=None, method="GET", retries=3):
    for i in range(retries):
        try:
            ts = int(time.time() * 1000)
            base = {"timestamp": ts, "recvWindow": 5000}
            if params: base.update(params)
            q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
            sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
            url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
            req = urllib.request.Request(url, method=method)
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(req, timeout=15).read().decode())
        except:
            if i < retries - 1: time.sleep(0.5)
    return None

def get_price(symbol):
    try: return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=100):
    data = api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    if not data: return []
    return [{'close': float(k[4]), 'high': float(k[2]), 'low': float(k[3]), 'volume': float(k[5])} for k in data]

def get_rsi(closes, period=14):
    if len(closes) < period+1: return 50
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period
    if avg_loss==0: return 100
    return 100-(100/(1+avg_gain/(avg_loss+1e-10)))

def get_momentum(closes, period=20):
    if len(closes)<period+1: return 0
    return (closes[-1]-closes[0])/closes[0]

def get_volatility(closes, period=20):
    if len(closes)<period+1: return 0.02
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1,len(closes))]
    mean = sum(returns[-period:])/len(returns[-period:])
    variance = sum((r-mean)**2 for r in returns[-period:])/len(returns[-period:])
    return math.sqrt(variance)

# ============ go-core预测 ============
def get_go_core_signal(coin):
    global go_core
    if not GOCORE_AVAILABLE: return None
    try:
        if go_core is None: go_core = GoCore(num_agents=150)
        return go_core.predict(coin, interval='1h', period='7d')
    except: return None

# ============ Top6 Meme 分析 ============
def analyze_top6_meme(coin):
    """Top6 Meme专用分析"""
    data = get_klines(f"{coin}USDT", '1h', 100)
    if not data: return None
    
    closes = [d['close'] for d in data]
    rsi = get_rsi(closes)
    mom = get_momentum(closes, 12)
    vol = get_volatility(closes)
    
    # 趋势
    ma5 = sum(closes[-5:])/5
    ma20 = sum(closes[-20:])/20 if len(closes) >= 20 else ma5
    trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
    
    return {
        'coin': coin,
        'price': closes[-1],
        'rsi': rsi,
        'momentum': mom,
        'volatility': vol,
        'trend': trend,
        'closes': closes
    }

def should_enter_top6(analysis):
    """Top6 Meme入场判断"""
    if not analysis: return False, 0
    
    score = 0
    
    # RSI超卖
    if analysis['rsi'] < TOP6_RSI_ENTER:
        score += 40
    elif analysis['rsi'] < 40:
        score += 20
    
    # 正动量
    if analysis['momentum'] > TOP6_MOM_ENTER:
        score += 30
    elif analysis['momentum'] > 0:
        score += 15
    
    # 上涨趋势
    if analysis['trend'] > 0.03:
        score += 20
    elif analysis['trend'] > 0:
        score += 10
    
    # go-core确认
    go_sig = get_go_core_signal(analysis['coin'])
    if go_sig and go_sig['confidence'] > 0.45:
        if go_sig['signal'] == 'buy':
            score += go_sig['confidence'] * 20
    
    return score >= 70, score

def should_exit_top6(coin, position):
    """Top6 Meme出场判断"""
    data = get_klines(f"{coin}USDT", '1h', 50)
    if not data: return False, 0, ""
    
    closes = [d['close'] for d in data]
    rsi = get_rsi(closes)
    current = closes[-1]
    
    entry = position['entry']
    high = position.get('high', entry)
    pnl = (current - entry) / entry
    
    # 止损
    if pnl <= -TOP6_STOP_LOSS:
        return True, pnl, f"止损({pnl:.1%})"
    
    # 止盈
    if pnl >= TOP6_TAKE_PROFIT:
        return True, pnl, f"止盈({pnl:.1%})"
    
    # 追踪止盈
    if pnl > 0.12:
        highs = [d['high'] for d in data[-24:]]
        max_high = max(highs)
        drawdown = (max_high - current) / max_high
        if drawdown >= TRAILING_STOP:
            return True, pnl, f"追踪止盈({pnl:.1%})"
    
    # RSI超买
    if rsi > 70 and pnl > 0.05:
        return True, pnl, f"RSI超买({rsi:.0f})"
    
    # 动量转负
    mom = get_momentum(closes, 12)
    if mom < -0.03 and pnl > 0.05:
        return True, pnl, f"动量转负({mom:.1%})"
    
    return False, pnl, f"持有({pnl:+.1%})"

# ============ 撞球周期分析 ============
def detect_phase(coin):
    """撞球周期阶段检测"""
    data_1h = get_klines(f"{coin}USDT", '1h', 200)
    data_4h = get_klines(f"{coin}USDT", '4h', 100)
    if not data_1h: return PHASE_CONSOLIDATION
    
    closes_1h = [d['close'] for d in data_1h]
    closes_4h = [d['close'] for d in data_4h] if data_4h else closes_1h
    
    rsi = get_rsi(closes_1h)
    mom_short = get_momentum(closes_1h[-24:]) if len(closes_1h) >= 24 else 0
    mom_long = get_momentum(closes_1h[-168:]) if len(closes_1h) >= 168 else get_momentum(closes_1h)
    
    if mom_long < -0.08:
        return PHASE_DECLINE if mom_short < 0 else PHASE_EARLY
    
    if mom_long > 0.15:
        if rsi > 75: return PHASE_PEAK
        if mom_short > 0.03 and rsi > 55: return PHASE_ACCELERATION
        if rsi < 50: return PHASE_EARLY
        return PHASE_CONSOLIDATION
    
    if rsi > 72: return PHASE_PEAK
    if mom_short > 0.025 and rsi > 50: return PHASE_ACCELERATION
    if rsi < 45 and mom_short > 0: return PHASE_EARLY
    
    return PHASE_CONSOLIDATION

def get_cycle_score(coin):
    """撞球周期评分"""
    phase = detect_phase(coin)
    data_1h = get_klines(f"{coin}USDT", '1h', 200)
    if not data_1h: return 50
    
    closes_1h = [d['close'] for d in data_1h]
    rsi = get_rsi(closes_1h)
    mom = get_momentum(closes_1h[-24:]) if len(closes_1h) >= 24 else 0
    
    score = 50
    phase_scores = {PHASE_ACCELERATION: 35, PHASE_EARLY: 25, PHASE_CONSOLIDATION: 10, PHASE_PEAK: -15, PHASE_DECLINE: -35}
    score += phase_scores.get(phase, 0)
    
    if 40 <= rsi <= 60: score += 15
    elif rsi < 35: score += 20
    elif rsi > 80: score -= 25
    
    if mom > 0.06: score += 20
    elif mom > 0.03: score += 15
    elif mom < -0.02: score -= 20
    
    # go-core融合
    go_sig = get_go_core_signal(coin)
    if go_sig and go_sig['confidence'] > 0.45:
        score += go_sig['confidence'] * 25
    
    return max(0, min(100, score))

def should_enter_cycle(coin):
    """撞球周期入场"""
    phase = detect_phase(coin)
    score = get_cycle_score(coin)
    
    if phase in [PHASE_EARLY, PHASE_ACCELERATION] and score >= 65:
        return True, score, PHASE_NAMES[phase]
    
    data = get_klines(f"{coin}USDT", '1h', 100)
    if data:
        rsi = get_rsi([d['close'] for d in data])
        if phase == PHASE_DECLINE and rsi < 35 and score >= 60:
            return True, score, f"超卖反弹"
    
    return False, score, PHASE_NAMES[phase]

def should_exit_cycle(coin, position):
    """撞球周期出场"""
    data = get_klines(f"{coin}USDT", '1h', 50)
    if not data: return False, 0, ""
    
    current = data[-1]['close']
    pnl = (current - position['entry']) / position['entry']
    phase = detect_phase(coin)
    
    if phase == PHASE_PEAK and pnl > 0.08: return True, pnl, "高峰止盈"
    if pnl <= -STOP_LOSS: return True, pnl, "止损"
    
    if pnl > 0.10:
        highs = [d['high'] for d in data[-24:]]
        drawdown = (max(highs) - current) / max(highs)
        if drawdown > 0.08: return True, pnl, "追踪止盈"
    
    if phase == PHASE_DECLINE and pnl > 0: return True, pnl, "衰退退出"
    
    return False, pnl, f"持有({pnl:+.1%})"

# ============ 综合入场/出场 ============
def should_enter(coin):
    """综合入场判断"""
    # Top6 Meme优先
    if coin in TOP6_MEME:
        analysis = analyze_top6_meme(coin)
        if analysis:
            enter, score = should_enter_top6(analysis)
            if enter: return True, score, "Top6信号"
    
    # 撞球周期
    enter, score, reason = should_enter_cycle(coin)
    return enter, score, reason

def should_exit(coin, position):
    """综合出场判断"""
    # Top6 Meme
    if coin in TOP6_MEME:
        exit, pnl, reason = should_exit_top6(coin, position)
        if exit: return exit, pnl, reason
    
    # 撞球周期
    return should_exit_cycle(coin, position)

# ============ 交易函数 ============
def get_account():
    global _g_account
    now = time.time()
    if _g_account['time'] > 0 and now - _g_account['time'] < 3: return _g_account
    try:
        data = api_signed("/api/v3/account")
        result = {'usdt': 0, 'coins': {}}
        if data and 'balances' in data:
            for b in data.get('balances', []):
                free = float(b.get('free', 0))
                if free > 0.0001:
                    if b['asset'] == 'USDT': result['usdt'] = free
                    else: result['coins'][b['asset']] = free
        _g_account = result; _g_account['time'] = now
        return result
    except Exception as e:
        log(f"账户失败: {e}", "ERROR")
        return _g_account if _g_account['time'] > 0 else {'usdt': 0, 'coins': {}, 'time': now}

def get_total_value(balances):
    total = balances['usdt']
    for coin, qty in balances['coins'].items():
        price = get_price(f"{coin}USDT")
        if price > 0: total += qty * price
    return total

def format_qty(coin, qty):
    if qty <= 0: return 0
    symbol = f"{coin}USDT"
    try:
        info = api_get(f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}')
        if info and 'symbols' in info:
            sym = info['symbols'][0]
            filters = {f['filterType']: f for f in sym['filters']}
            lot = filters.get('LOT_SIZE', {})
            step = float(lot.get('stepSize', 1.0))
            min_q = float(lot.get('minQty', 0))
            prec = len(str(step).split('.')[-1].rstrip('0')) if step < 1 else 0
            formatted = math.floor(qty / step) * step
            formatted = round(formatted, prec) if prec > 0 else int(formatted)
            if formatted < min_q: return 0
            return formatted
    except: pass
    return math.floor(qty)

def place_order(symbol, side, quantity):
    try:
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
        result = api_signed("/api/v3/order", params, "POST")
        if result and 'orderId' in result:
            log(f"订单成功: {side} {quantity} {symbol}", "TRADE")
            return result
    except Exception as e: log(f"订单失败: {e}", "ERROR")
    return None

def buy_coin(coin, total_value):
    global positions, last_switch
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0: return False
    
    pct = KELLY_BASE * 1.5 if detect_phase(coin) == PHASE_ACCELERATION else KELLY_BASE
    qty = (total_value * pct) / price
    qty = format_qty(coin, qty)
    if qty * price < 1: return False
    
    if place_order(symbol, "BUY", qty):
        positions[coin] = {'entry': price, 'entry_time': time.time(), 'high': price}
        last_switch[coin] = time.time()
        history.append({'coin': coin, 'action': 'BUY', 'price': price, 'time': time.time()})
        return True
    return False

def sell_coin(coin, reason=""):
    global positions
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0: return False
    
    balances = get_account()
    qty = balances['coins'].get(coin, 0)
    if qty <= 0: return False
    qty = format_qty(coin, qty)
    if qty * price < 1: return False
    
    if place_order(symbol, "SELL", qty) and coin in positions:
        entry = positions[coin]['entry']
        pnl = (price - entry) / entry * 100
        log(f"🎱卖出 {coin}: {reason} {pnl:+.2f}%", "TRADE")
        history.append({'coin': coin, 'action': 'SELL', 'price': price, 'pnl': pnl, 'reason': reason, 'time': time.time()})
        del positions[coin]
        return True
    return False

# ============ G37主循环 ============
def run():
    global positions
    
    log("=" * 60, "INFO")
    log("G37 Pool Strategy 撞球终极版 v3.0 启动", "INFO")
    log("整合: Top6 Meme + 撞球周期 + go-core", "INFO")
    log(f"Top6: {', '.join(TOP6_MEME)}", "INFO")
    log("=" * 60, "INFO")
    
    if GOCORE_AVAILABLE: log("✅ go-core 已加载", "INFO")
    
    start_value = get_total_value(get_account())
    log(f"初始资产: ${start_value:.2f}", "INFO")
    
    while True:
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            log(f"\n{'='*60}", "INFO")
            log(f"🎱 G37撞球扫描 ({ts})", "INFO")
            
            balances = get_account()
            total = get_total_value(balances)
            usdt = balances['usdt']
            log(f"资产: USDT={usdt:.2f} 总计=${total:.2f}", "INFO")
            
            # 1. 检查持仓
            for coin in list(positions.keys()):
                info = positions[coin]
                exit, pnl, reason = should_exit(coin, info)
                
                cur = get_price(f"{coin}USDT")
                if cur > info['high']: positions[coin]['high'] = cur
                
                if exit: sell_coin(coin, reason)
            
            # 2. 扫描候选
            candidates = []
            for coin in ALL_COINS:
                if coin in positions: continue
                if coin in balances['coins']: continue
                
                enter, score, reason = should_enter(coin)
                if enter: candidates.append({'coin': coin, 'score': score, 'reason': reason})
            
            # 3. 撞球切换
            if len(positions) < MAX_ACTIVE and candidates:
                candidates.sort(key=lambda x: -x['score'])
                best = candidates[0]
                
                can_switch = best['coin'] not in last_switch or time.time() - last_switch[best['coin']] > SWITCH_COOLDOWN
                
                if can_switch and usdt >= 5:
                    log(f"🎱进球: {best['coin']} ({best['reason']}, 评分{best['score']:.0f})", "INFO")
                    buy_coin(best['coin'], total)
            
            # 4. 显示状态
            log(f"撞球状态 ({len(positions)}/{MAX_ACTIVE}):", "INFO")
            for coin, info in positions.items():
                phase = detect_phase(coin)
                cur = get_price(f"{coin}USDT")
                pnl = (cur - info['entry']) / info['entry'] * 100
                log(f"  🎯 {coin}: {PHASE_NAMES[phase]} {pnl:+.1%}", "INFO")
            
            if not positions: log("  等待进球...", "INFO")
            
            if start_value > 0:
                pnl = (total - start_value) / start_value * 100
                log(f"累计收益: {pnl:+.2f}%", "INFO")
            
            log(f"扫描间隔: {SCAN_INTERVAL}秒", "INFO")
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            log(f"错误: {e}", "ERROR")
            import traceback; traceback.print_exc()
            time.sleep(10)

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║     G37 Pool Strategy v3.0        ║
║   Top6 Meme + 撞球周期 + go-core  ║
╚══════════════════════════════════════════════╝
    """)
    try: run()
    except KeyboardInterrupt: print("\n停止G37...")
    except Exception as e: log(f"FATAL: {e}", "ERROR")
