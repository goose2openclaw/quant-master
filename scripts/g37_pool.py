#!/usr/bin/env python3
"""
G37 Pool Strategy - 撞球策略终极版 v3.1
==========================================
增强稳定性:
1. 启动时从API同步持仓
2. 状态持久化到磁盘
3. 更强的错误恢复
"""

import urllib.request, hmac, hashlib, time, json, sys, math, os
from datetime import datetime
from collections import deque

sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-core')

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g37_pool.log"
STATE_FILE = "/home/goose/.openclaw/workspace/.g37_state.json"

GOCORE_AVAILABLE = False
try:
    from go_core import GoCore
    GOCORE_AVAILABLE = True
except: pass

PHASE_NAMES = {0: "盘整", 1: "启动", 2: "加速", 3: "高峰", 4: "衰退"}
TOP6_MEME = ['BOME', 'TURBO', 'BONK', 'FLOKI', 'PEPE', 'NEIRO']
TOP_MAJOR = ['DOGE', 'ADA', 'ATOM', 'DOT', 'ETC', 'NEAR']
ALL_COINS = TOP6_MEME + TOP_MAJOR

MAX_ACTIVE = 3
KELLY_BASE = 0.30
STOP_LOSS = 0.05
TAKE_PROFIT_BASE = 0.15
SCAN_INTERVAL = 30

positions = {}
last_switch = {}
history = deque(maxlen=200)
go_core = None

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")

def save_state():
    """保存状态"""
    try:
        state = {
            'positions': positions.copy(),
            'last_switch': last_switch.copy(),
            'time': time.time()
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        log(f"保存状态失败: {e}", "ERROR")

def load_state():
    """加载状态"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        log(f"加载状态失败: {e}", "ERROR")
    return {'positions': {}, 'last_switch': {}}

def api_get(url, retries=2):
    for i in range(retries):
        try:
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        except:
            if i < retries - 1: time.sleep(0.3)
    return None

def api_signed(endpoint, params=None, method="GET"):
    for i in range(3):
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
            if i < 2: time.sleep(0.5)
    return None

def get_price(symbol):
    try: return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=100):
    data = api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    return [] if not data else [{'close': float(k[4]), 'high': float(k[2])} for k in data]

def get_rsi(closes, period=14):
    if len(closes) < period+1: return 50
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period
    return 100-(100/(1+avg_gain/(avg_loss+1e-10))) if avg_loss != 0 else 100

def get_momentum(closes, period=20):
    return (closes[-1]-closes[0])/closes[0] if len(closes) >= period else 0

def get_go_core_signal(coin):
    global go_core
    if not GOCORE_AVAILABLE: return None
    try:
        if go_core is None: go_core = GoCore(num_agents=100)
        return go_core.predict(coin, interval='1h', period='7d')
    except: return None

def get_account():
    """获取账户 - 不使用缓存，每次都请求API"""
    try:
        data = api_signed("/api/v3/account")
        result = {'usdt': 0, 'coins': {}}
        if data and 'balances' in data:
            for b in data.get('balances', []):
                free = float(b.get('free', 0))
                if free > 0.0001:
                    if b['asset'] == 'USDT': result['usdt'] = free
                    else: result['coins'][b['asset']] = free
        return result
    except Exception as e:
        log(f"获取账户失败: {e}", "ERROR")
        return {'usdt': 0, 'coins': {}}

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
            prec = len(str(step).split('.')[-1].rstrip('0')) if step < 1 else 0
            formatted = math.floor(qty / step) * step
            formatted = round(formatted, prec) if prec > 0 else int(formatted)
            return 0 if formatted < min_q else formatted
    except: pass
    return math.floor(qty)

def place_order(symbol, side, quantity):
    try:
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": str(quantity)}
        result = api_signed("/api/v3/order", params, "POST")
        if result and 'orderId' in result:
            log(f"订单成功: {side} {quantity} {symbol}", "TRADE")
            return result
        log(f"订单失败: {result}", "ERROR")
    except Exception as e:
        log(f"订单失败: {e}", "ERROR")
    return None

def buy_coin(coin, usdt_balance):
    global positions, last_switch
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0: return False
    
    pct = KELLY_BASE * 1.5
    qty = (usdt_balance * pct) / price
    qty = format_qty(coin, qty)
    
    if qty * price < 1:
        log(f"{coin}: 金额不足 ${usdt_balance*pct:.2f} < $1", "WARNING")
        return False
    
    if place_order(symbol, "BUY", qty):
        positions[coin] = {'entry': price, 'entry_time': time.time(), 'high': price}
        last_switch[coin] = time.time()
        history.append({'coin': coin, 'action': 'BUY', 'price': price, 'time': time.time()})
        save_state()
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
        log(f"卖出 {coin}: {reason} {pnl:+.2f}%", "TRADE")
        history.append({'coin': coin, 'action': 'SELL', 'price': price, 'pnl': pnl, 'reason': reason, 'time': time.time()})
        del positions[coin]
        save_state()
        return True
    return False

def detect_phase(coin):
    data = get_klines(f"{coin}USDT", '1h', 200)
    if not data: return 0
    closes = [d['close'] for d in data]
    rsi = get_rsi(closes)
    mom = get_momentum(closes[-24:]) if len(closes) >= 24 else 0
    mom_long = get_momentum(closes[-168:]) if len(closes) >= 168 else mom
    
    if mom_long < -0.08: return 4 if mom < 0 else 1
    if mom_long > 0.15:
        if rsi > 75: return 3
        if mom > 0.03 and rsi > 55: return 2
        if rsi < 50: return 1
        return 0
    if rsi > 72: return 3
    if mom > 0.025 and rsi > 50: return 2
    if rsi < 45 and mom > 0: return 1
    return 0

def get_cycle_score(coin):
    phase = detect_phase(coin)
    data = get_klines(f"{coin}USDT", '1h', 100)
    if not data: return 50
    closes = [d['close'] for d in data]
    rsi = get_rsi(closes)
    mom = get_momentum(closes[-24:]) if len(closes) >= 24 else 0
    
    score = 50
    phase_scores = {2: 35, 1: 25, 0: 10, 3: -15, 4: -35}
    score += phase_scores.get(phase, 0)
    if 40 <= rsi <= 60: score += 15
    elif rsi < 35: score += 20
    elif rsi > 80: score -= 25
    if mom > 0.06: score += 20
    elif mom > 0.03: score += 15
    elif mom < -0.02: score -= 20
    
    go_sig = get_go_core_signal(coin)
    if go_sig and go_sig.get('confidence', 0) > 0.45:
        score += go_sig['confidence'] * 25
    
    return max(0, min(100, score))

def should_enter(coin):
    phase = detect_phase(coin)
    score = get_cycle_score(coin)
    if phase in [1, 2] and score >= 65:
        return True, score, PHASE_NAMES[phase]
    return False, score, PHASE_NAMES[phase]

def should_exit(coin, position):
    data = get_klines(f"{coin}USDT", '1h', 50)
    if not data: return False, 0, ""
    current = data[-1]['close']
    pnl = (current - position['entry']) / position['entry']
    phase = detect_phase(coin)
    
    if pnl <= -STOP_LOSS: return True, pnl, "止损"
    if phase == 3 and pnl > 0.08: return True, pnl, "高峰止盈"
    if pnl > 0.10:
        highs = [d['high'] for d in data[-24:]]
        if (max(highs) - current) / max(highs) > 0.08: return True, pnl, "追踪止盈"
    if phase == 4 and pnl > 0: return True, pnl, "衰退退出"
    return False, pnl, f"持有({pnl:+.1%})"

def sync_positions_from_api():
    """从API同步持仓到positions"""
    global positions
    balances = get_account()
    api_coins = set(balances['coins'].keys())
    
    # 添加API中有但positions中没有的币种
    for coin in api_coins:
        if coin not in positions and coin != 'USDT':
            price = get_price(f"{coin}USDT")
            if price > 0:
                positions[coin] = {'entry': price, 'entry_time': time.time(), 'high': price}
                log(f"同步持仓: {coin} @ ${price}", "INFO")
    
    # 移除positions中但API中没有的币种
    for coin in list(positions.keys()):
        if coin not in api_coins:
            del positions[coin]
            log(f"移除持仓: {coin}", "INFO")
    
    save_state()

def run():
    global positions
    
    log("=" * 60, "INFO")
    log("G37 v3.1 撞球策略启动", "INFO")
    log("增强稳定性: API同步 + 状态持久化", "INFO")
    log("=" * 60, "INFO")
    
    # 从磁盘加载状态
    saved_state = load_state()
    positions.update(saved_state.get('positions', {}))
    last_switch.update(saved_state.get('last_switch', {}))
    
    # 从API同步持仓
    log("从API同步持仓...", "INFO")
    sync_positions_from_api()
    
    # 从API获取真实USDT
    balances = get_account()
    start_value = get_total_value(balances)
    log(f"初始资产: ${start_value:.2f}", "INFO")
    log(f"同步后持仓: {list(positions.keys())}", "INFO")
    
    while True:
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            log(f"\n{'='*60}", "INFO")
            log(f"G37扫描 ({ts})", "INFO")
            
            balances = get_account()
            total = get_total_value(balances)
            usdt = balances['usdt']
            log(f"资产: USDT=${usdt:.2f} 总计=${total:.2f}", "INFO")
            
            # 检查持仓
            for coin in list(positions.keys()):
                info = positions[coin]
                exit, pnl, reason = should_exit(coin, info)
                current = get_price(f"{coin}USDT")
                if current > info['high']: positions[coin]['high'] = current
                if exit: sell_coin(coin, reason)
            
            # 扫描候选
            candidates = []
            for coin in ALL_COINS:
                if coin in positions: continue
                if coin in balances['coins']: continue
                enter, score, reason = should_enter(coin)
                if enter: candidates.append({'coin': coin, 'score': score, 'reason': reason})
            
            # 执行买入 - 利益最大化
            if candidates and (usdt >= 5 or len(positions) < MAX_ACTIVE):
                # 优先Top6 Meme
                top6_candidates = [c for c in candidates if c['coin'] in TOP6_MEME]
                if top6_candidates:
                    best = top6_candidates[0]
                else:
                    candidates.sort(key=lambda x: -x['score'])
                    best = candidates[0]
                
                can_switch = best['coin'] not in last_switch or time.time() - last_switch[best['coin']] > 300
                
                if len(positions) < MAX_ACTIVE:
                    # 有空位，直接买入
                    if can_switch and usdt >= 5:
                        log(f"🎯进球: {best['coin']} ({best['reason']}, 评分{best['score']:.0f})", "INFO")
                        buy_coin(best['coin'], usdt)
                elif best['score'] > 75:
                    # 满仓但有高分信号，考虑调换
                    for coin in list(positions.keys()):
                        phase = detect_phase(coin)
                        if phase == 4:  # 衰退期
                            info = positions[coin]
                            current = get_price(f"{coin}USDT")
                            pnl = (current - info['entry']) / info['entry'] if info['entry'] > 0 else 0
                            if pnl < 0.05:  # 小亏就换
                                log(f"🔄调换: {coin}->{best['coin']} (评分{best['score']:.0f})", "INFO")
                                sell_coin(coin, "调换")
                                time.sleep(1)
                                buy_coin(best['coin'], usdt + 10)
                                break
            
            # ====== 自动调换: 利益最大化 ======
            if len(positions) > 0 and usdt < 10:
                # USDT不足，尝试卖出衰退期持仓
                for coin in list(positions.keys()):
                    phase = detect_phase(coin)
                    info = positions[coin]
                    current = get_price(f"{coin}USDT")
                    pnl = (current - info['entry']) / info['entry'] if info['entry'] > 0 else 0
                    
                    # 衰退期 或 亏损超过10% -> 考虑卖出
                    if phase == 4 or (pnl < -0.10 and phase in [0, 4]):
                        log(f"自动调换: 卖出 {coin} (阶段{PHASE_NAMES[phase]}, {pnl:+.1%})", "INFO")
                        sell_coin(coin, f"自动调换-{PHASE_NAMES[phase]}")
            
            # 显示状态
            log(f"持仓 ({len(positions)}/{MAX_ACTIVE}):", "INFO")
            for coin, info in positions.items():
                phase = detect_phase(coin)
                current = get_price(f"{coin}USDT")
                pnl = (current - info['entry']) / info['entry'] * 100
                log(f"  {coin}: {PHASE_NAMES[phase]} {pnl:+.1%}", "INFO")
            
            if not positions: log("  等待进球...", "INFO")
            
            if start_value > 0:
                pnl = (total - start_value) / start_value * 100
                log(f"累计收益: {pnl:+.2f}%", "INFO")
            
            save_state()  # 定期保存
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            log(f"错误: {e}", "ERROR")
            import traceback; traceback.print_exc()
            time.sleep(10)

if __name__ == '__main__':
    print("G37 v3.1 撞球策略")
    try: run()
    except KeyboardInterrupt: print("\n停止")
    except Exception as e: log(f"FATAL: {e}", "ERROR")
