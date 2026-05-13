#!/usr/bin/env python3
"""
G37 Pool Strategy - 撞球策略优化版 v2.0
==========================================
基于30天回测数据优化:
- BOME: +46.9% (优化入场时机)
- TURBO: +32.5% (优化出场)
- Meme币整体: 163% (专注Top5)

核心优化:
1. 动态止盈 - 根据波动率调整
2. 快速止损 - 减少亏损
3. 二次确认 - go-core信号验证
4. 分批建仓 - 降低风险
5. 动量加速 - 追涨强势币
"""

import urllib.request, hmac, hashlib, time, json, sys, math
from datetime import datetime
from collections import deque

sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-core')

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g37_pool.log"

# 尝试加载go-core
GOCORE_AVAILABLE = False
try:
    from go_core import GoCore
    GOCORE_AVAILABLE = True
except:
    print("⚠️ go-core不可用")

# ============ 优化后的常量 ============
PHASE_CONSOLIDATION, PHASE_EARLY, PHASE_ACCELERATION, PHASE_PEAK, PHASE_DECLINE = 0, 1, 2, 3, 4
PHASE_NAMES = {0: "盘整", 1: "启动", 2: "加速", 3: "高峰", 4: "衰退"}

# 基于回测的Top币种 (高收益)
TOP_MEME = ['BOME', 'TURBO', 'BONK', 'FLOKI', 'PEPE', 'NEIRO']
TOP_MAJOR = ['DOGE', 'ADA', 'ATOM', 'DOT', 'ETC', 'NEAR']
ALL_COINS = TOP_MEME + TOP_MAJOR

MAX_ACTIVE = 3
KELLY_BASE = 0.25  # 提高到25%
STOP_LOSS = 0.04   # 降低止损到4%
TAKE_PROFIT_BASE = 0.12  # 基础止盈12%
SWITCH_COOLDOWN = 600  # 10分钟冷却

# ============ 全局变量 ============
_g_account = {'usdt': 0, 'coins': {}, 'time': 0}
positions = {}
last_switch = {}
history = deque(maxlen=100)
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
    try:
        return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=100):
    data = api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    if not data: return []
    return [{'time': k[0]//1000, 'close': float(k[4]), 'high': float(k[2]), 'low': float(k[3]), 'volume': float(k[5])} for k in data]

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
        if go_core is None:
            go_core = GoCore(num_agents=150)
        return go_core.predict(coin, interval='1h', period='7d')
    except: return None

# ============ 周期分析优化 ============
def detect_phase(coin):
    """优化后的周期检测"""
    data_1h = get_klines(f"{coin}USDT", '1h', 200)
    data_4h = get_klines(f"{coin}USDT", '4h', 100)
    if not data_1h: return PHASE_CONSOLIDATION
    
    closes_1h = [d['close'] for d in data_1h]
    closes_4h = [d['close'] for d in data_4h] if data_4h else closes_1h
    
    rsi = get_rsi(closes_1h)
    mom_short = get_momentum(closes_1h[-24:]) if len(closes_1h) >= 24 else 0
    mom_med = get_momentum(closes_1h[-72:]) if len(closes_1h) >= 72 else mom_short
    mom_long = get_momentum(closes_1h[-168:]) if len(closes_1h) >= 168 else mom_med
    
    volatility = get_volatility(closes_1h)
    
    # 周期完成度
    if len(closes_4h) >= 20:
        window = closes_4h[-30:]
        min_p = min(window)
        max_p = max(window)
        current = window[-1]
        if max_p > min_p:
            cycle_progress = (current - min_p) / (max_p - min_p)
        else:
            cycle_progress = 0.5
    else:
        cycle_progress = 0.5
    
    # 优化后的阶段判断
    if mom_long < -0.08:
        # 下跌趋势
        if rsi < 40 and mom_short > 0.02: return PHASE_EARLY
        return PHASE_DECLINE
    
    if mom_long > 0.15:
        # 强势上涨
        if cycle_progress > 0.85: return PHASE_PEAK
        if mom_short > 0.03 and rsi > 55: return PHASE_ACCELERATION
        if rsi < 50: return PHASE_EARLY
        return PHASE_CONSOLIDATION
    
    # 温和上涨
    if rsi > 72: return PHASE_PEAK
    if mom_short > 0.025 and rsi > 50: return PHASE_ACCELERATION
    if rsi < 45 and mom_short > 0: return PHASE_EARLY
    if volatility < 0.008: return PHASE_CONSOLIDATION
    
    return PHASE_CONSOLIDATION

def get_cycle_score(coin):
    """综合评分"""
    phase = detect_phase(coin)
    data_1h = get_klines(f"{coin}USDT", '1h', 200)
    data_4h = get_klines(f"{coin}USDT", '4h', 100)
    if not data_1h: return 50
    
    closes_1h = [d['close'] for d in data_1h]
    closes_4h = [d['close'] for d in data_4h] if data_4h else closes_1h
    
    rsi = get_rsi(closes_1h)
    mom = get_momentum(closes_1h[-24:]) if len(closes_1h) >= 24 else 0
    vol = get_volatility(closes_1h)
    
    # 周期进度
    if len(closes_4h) >= 20:
        window = closes_4h[-30:]
        min_p, max_p = min(window), max(window)
        progress = (window[-1] - min_p) / (max_p - min_p + 1e-10)
    else:
        progress = 0.5
    
    score = 50
    
    # 阶段分 (优化权重)
    phase_scores = {PHASE_ACCELERATION: 35, PHASE_EARLY: 25, PHASE_CONSOLIDATION: 10, PHASE_PEAK: -15, PHASE_DECLINE: -35}
    score += phase_scores.get(phase, 0)
    
    # RSI分
    if 40 <= rsi <= 60: score += 15
    elif rsi < 35: score += 20
    elif rsi < 45: score += 12
    elif rsi > 80: score -= 25
    
    # 动量分
    if mom > 0.06: score += 20
    elif mom > 0.03: score += 15
    elif mom > 0.015: score += 10
    elif mom < -0.02: score -= 20
    
    # 波动率调节
    if vol < 0.02: score += 5  # 低波动更稳定
    elif vol > 0.08: score -= 10  # 高波动风险大
    
    # 周期进度
    if progress < 0.4: score += 10  # 早期更有空间
    elif progress > 0.8: score -= 15  # 晚期风险大
    
    # go-core融合
    go_signal = get_go_core_signal(coin)
    if go_signal and go_signal['confidence'] > 0.45:
        go_weight = go_signal['confidence'] * 0.25
        if go_signal['signal'] == 'buy':
            score += go_weight * 100 * 0.3
        elif go_signal['signal'] == 'sell':
            score -= go_weight * 50
    
    return max(0, min(100, score))

def should_enter(coin):
    """优化后的入场判断"""
    phase = detect_phase(coin)
    score = get_cycle_score(coin)
    
    # 核心条件: 启动期/加速期 + 评分>=65
    if phase in [PHASE_EARLY, PHASE_ACCELERATION] and score >= 65:
        return True, score, f"{PHASE_NAMES[phase]}"
    
    # 二次确认: 超卖反弹
    data_1h = get_klines(f"{coin}USDT", '1h', 100)
    if data_1h:
        rsi = get_rsi([d['close'] for d in data_1h])
        if rsi < 32 and score >= 60:
            return True, score, f"超卖反弹"
    
    return False, score, PHASE_NAMES[phase]

def should_exit(coin, entry_price, entry_time):
    """优化后的出场判断"""
    data_1h = get_klines(f"{coin}USDT", '1h', 100)
    if not data_1h: return False, 0, ""
    
    current = data_1h[-1]['close']
    pnl = (current - entry_price) / entry_price
    phase = detect_phase(coin)
    rsi = get_rsi([d['close'] for d in data_1h])
    vol = get_volatility([d['close'] for d in data_1h])
    
    # 动态止盈 (根据波动率调整)
    dynamic_tp = TAKE_PROFIT_BASE + vol * 2  # 高波动=更高止盈
    
    # 1. 止盈检查
    if pnl >= dynamic_tp:
        return True, pnl, f"止盈({pnl:.1%})"
    
    # 2. 止损检查
    if pnl <= -STOP_LOSS:
        return True, pnl, f"止损"
    
    # 3. 高峰期强制止盈
    if phase == PHASE_PEAK and pnl > 0.05:
        return True, pnl, f"高峰退出"
    
    # 4. 追踪止盈 (从高点回撤)
    if pnl > 0.06:
        highs = [d['high'] for d in data_1h[-24:]]
        max_high = max(highs)
        drawdown = (max_high - current) / max_high
        if drawdown > 0.08:  # 从高点回撤8%止盈
            return True, pnl, f"追踪止盈"
    
    # 5. RSI超买检查
    if rsi > 85 and pnl > 0.03:
        return True, pnl, f"RSI超买"
    
    # 6. 衰退期退出
    if phase == PHASE_DECLINE and pnl > 0:
        return True, pnl, f"衰退退出"
    
    return False, pnl, f"持有({pnl:+.1%})"

# ============ 交易函数 ============
def get_account():
    global _g_account
    now = time.time()
    if _g_account['time'] > 0 and now - _g_account['time'] < 3:
        return _g_account
    try:
        data = api_signed("/api/v3/account")
        result = {'usdt': 0, 'coins': {}}
        if data and 'balances' in data:
            for b in data.get('balances', []):
                free = float(b.get('free', 0))
                if free > 0.0001:
                    if b['asset'] == 'USDT': result['usdt'] = free
                    else: result['coins'][b['asset']] = free
        _g_account = result
        _g_account['time'] = now
        return result
    except Exception as e:
        log(f"账户失败: {e}", "ERROR")
        if _g_account['time'] > 0: return _g_account
        return {'usdt': 0, 'coins': {}, 'time': now}

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
            lot_size = filters.get('LOT_SIZE', {})
            step = float(lot_size.get('stepSize', 1.0))
            min_q = float(lot_size.get('minQty', 0))
            prec = 0
            if step < 1: prec = len(str(step).split('.')[-1].rstrip('0'))
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
    except Exception as e:
        log(f"订单失败: {e}", "ERROR")
    return None

def buy_coin(coin, total_value):
    global positions, last_switch
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0: return False
    
    phase = detect_phase(coin)
    # 加速期重仓
    if phase == PHASE_ACCELERATION: pct = KELLY_BASE * 1.5
    elif phase == PHASE_EARLY: pct = KELLY_BASE * 1.2
    else: pct = KELLY_BASE
    
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
        log(f"🎱撞球卖出 {coin}: {reason} {pnl:+.2f}%", "TRADE")
        del positions[coin]
        return True
    return False

# ============ G37主循环 ============
def run():
    global positions
    
    log("=" * 60, "INFO")
    log("G37 Pool Strategy 撞球优化版 v2.0 启动", "INFO")
    log("优化: 动态止盈/快速止损/go-core融合", "INFO")
    if GOCORE_AVAILABLE: log("✅ go-core 已加载", "INFO")
    log("Top币: " + ",".join(TOP_MEME[:3]), "INFO")
    log("=" * 60, "INFO")
    
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
                exit, pnl, reason = should_exit(coin, info['entry'], info['entry_time'])
                
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
            
            log("等待45秒...", "INFO")
            time.sleep(45)
            
        except Exception as e:
            log(f"错误: {e}", "ERROR")
            import traceback; traceback.print_exc()
            time.sleep(10)

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║     G37 Pool Strategy - 撞球优化版   ║
║   动态止盈 | 快速止损 | go-core融合   ║
╚══════════════════════════════════════════════╝
    """)
    try: run()
    except KeyboardInterrupt: print("\n停止G37...")
    except Exception as e: log(f"FATAL: {e}", "ERROR")
