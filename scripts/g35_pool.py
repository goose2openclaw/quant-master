#!/usr/bin/env python3
"""
G35 Pool Strategy - 撞球策略版
================================
整合撞球策略的收益最大化系统

核心理念:
- 不同币种处于不同的回报周期阶段
- 系统识别并切换到正在加速的币种
- 享受完当前币种大半个回报周期后自然切换
- 始终保持"进球"状态
"""

import urllib.request, hmac, hashlib, time, json, sys, math
from datetime import datetime
from collections import deque

# 导入go-core系列组件
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-core')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-quantum')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-thermo')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-contrarian')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-detect')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-orderbook')
sys.path.insert(0, '/home/goose/.openclaw/workspace/skills/go-liquidation')

try:
    from go_core import GoCore
    GOCORE_AVAILABLE = True
except:
    GOCORE_AVAILABLE = False
    print("警告: go-core不可用")

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g35_pool.log"

# ============ 撞球策略常量 ============
PHASE_CONSOLIDATION = 0
PHASE_EARLY = 1
PHASE_ACCELERATION = 2
PHASE_PEAK = 3
PHASE_DECLINE = 4

PHASE_NAMES = {
    PHASE_CONSOLIDATION: "盘整",
    PHASE_EARLY: "启动",
    PHASE_ACCELERATION: "加速",
    PHASE_PEAK: "高峰",
    PHASE_DECLINE: "衰退"
}

MAX_ACTIVE_COINS = 3
KELLY_BASE = 0.20
MIN_CYCLE_COMPLETION = 0.3
SWITCH_COOLDOWN = 1200  # 20分钟冷却

MAJOR_COINS = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','DOT','LINK','UNI','AVAX','ATOM','LTC','ETC','NEAR']
MEME_COINS = ['TURBO','BOME','NEIRO','BONK','PEPE','FLOKI','SHIB','PUMP']
ALL_COINS = MAJOR_COINS + MEME_COINS

# ============ 全局变量 ============
_g_account = {'usdt': 0, 'coins': {}, 'time': 0}
positions = {}  # {coin: {'entry': price, 'entry_time': t, 'high': price}}
last_switch = {}
history = deque(maxlen=100)
scan_count = 0

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
            if i < retries - 1: time.sleep(0.5)
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
            if i < retries - 1: time.sleep(1)
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
    if len(closes)<period+1: return 0.01
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1,len(closes))]
    mean = sum(returns[-period:])/len(returns[-period:])
    variance = sum((r-mean)**2 for r in returns[-period:])/len(returns[-period:])
    return math.sqrt(variance)

# ============ 周期分析器 ============
def detect_phase(coin):
    """检测币种所处周期阶段"""
    data_1h = get_klines(f"{coin}USDT", '1h', 168)
    data_4h = get_klines(f"{coin}USDT", '4h', 90)
    if not data_1h: return PHASE_CONSOLIDATION
    
    closes_1h = [d['close'] for d in data_1h]
    closes_4h = [d['close'] for d in data_4h] if data_4h else closes_1h
    
    rsi = get_rsi(closes_1h)
    momentum_short = get_momentum(closes_1h[-24:])
    momentum_long = get_momentum(closes_1h[-168:]) if len(closes_1h)>=168 else get_momentum(closes_1h)
    
    # 周期完成度
    if len(closes_4h) >= 20:
        window = closes_4h[-30:]
        min_idx = window.index(min(window))
        min_price = window[min_idx]
        current_price = window[-1]
        if min_price > 0:
            vol = get_volatility(closes_4h)
            est_max = min_price * (1 + vol * 5)
            cycle_completion = (current_price - min_price) / (est_max - min_price + 1e-10)
        else:
            cycle_completion = 0.5
    else:
        cycle_completion = 0.5
    
    # 阶段判断
    if momentum_long < -0.05:
        if momentum_short > 0.03 and rsi < 60: return PHASE_EARLY
        return PHASE_DECLINE
    
    if momentum_long > 0.10:
        if rsi > 75: return PHASE_PEAK
        elif momentum_short > 0.02 and rsi > 50: return PHASE_ACCELERATION
        elif rsi < 50: return PHASE_EARLY
        return PHASE_CONSOLIDATION
    
    if rsi < 45 and momentum_short > 0: return PHASE_EARLY
    if rsi > 70: return PHASE_PEAK
    if get_volatility(closes_1h) < 0.01: return PHASE_CONSOLIDATION
    return PHASE_CONSOLIDATION

def get_cycle_score(coin):
    """获取周期评分"""
    phase = detect_phase(coin)
    data_1h = get_klines(f"{coin}USDT", '1h', 168)
    data_4h = get_klines(f"{coin}USDT", '4h', 90)
    if not data_1h: return 50
    
    closes_1h = [d['close'] for d in data_1h]
    closes_4h = [d['close'] for d in data_4h] if data_4h else closes_1h
    
    rsi = get_rsi(closes_1h)
    momentum = get_momentum(closes_1h[-24:])
    
    if len(closes_4h) >= 20:
        window = closes_4h[-30:]
        min_price = min(window)
        current_price = window[-1]
        vol = get_volatility(closes_4h)
        est_max = min_price * (1 + vol * 5)
        cycle_completion = (current_price - min_price) / (est_max - min_price + 1e-10) if est_max > min_price else 0.5
    else:
        cycle_completion = 0.5
    
    score = 50
    
    # 阶段分
    phase_bonus = {PHASE_ACCELERATION: 30, PHASE_EARLY: 20, PHASE_CONSOLIDATION: 5, PHASE_PEAK: -10, PHASE_DECLINE: -30}
    score += phase_bonus.get(phase, 0)
    
    # RSI分
    if 40 <= rsi <= 60: score += 10
    elif rsi < 30: score += 15
    elif rsi > 80: score -= 20
    
    # 动量分
    if momentum > 0.05: score += 15
    elif momentum > 0.02: score += 10
    elif momentum < -0.02: score -= 15
    
    # 周期完成度
    if cycle_completion < 0.5: score += 10
    elif cycle_completion > 0.8: score -= 15
    
    return max(0, min(100, score))

def should_enter_coin(coin):
    """是否应该进入"""
    phase = detect_phase(coin)
    score = get_cycle_score(coin)
    
    if phase in [PHASE_EARLY, PHASE_ACCELERATION] and score >= 65:
        return True, score, PHASE_NAMES[phase]
    
    data_1h = get_klines(f"{coin}USDT", '1h', 100)
    if data_1h:
        rsi = get_rsi([d['close'] for d in data_1h])
        if phase == PHASE_DECLINE and rsi < 35 and score >= 60:
            return True, score, f"超卖反弹"
    
    return False, score, PHASE_NAMES[phase]

def should_exit_coin(coin, entry_price):
    """是否应该退出"""
    data_1h = get_klines(f"{coin}USDT", '1h', 100)
    if not data_1h: return False, 0, ""
    
    current_price = data_1h[-1]['close']
    pnl_pct = (current_price - entry_price) / entry_price
    phase = detect_phase(coin)
    rsi = get_rsi([d['close'] for d in data_1h])
    
    # 止盈: 高峰期
    if phase == PHASE_PEAK and pnl_pct > 0.05: return True, pnl_pct, f"高峰止盈"
    
    # 止损
    if pnl_pct <= -0.05: return True, pnl_pct, "止损"
    
    # 追踪止盈
    if pnl_pct > 0.08:
        highs = [d['high'] for d in data_1h[-24:]]
        max_high = max(highs)
        drawdown = (max_high - current_price) / max_high
        if drawdown > 0.06: return True, pnl_pct, f"追踪止盈"
    
    # 衰退退出
    if phase == PHASE_DECLINE and pnl_pct > 0: return True, pnl_pct, f"衰退退出"
    
    return False, pnl_pct, f"持有({pnl_pct:+.1%})"

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
        log(f"获取账户失败: {e}", "ERROR")
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
            step_size = float(lot_size.get('stepSize', 1.0))
            min_qty = float(lot_size.get('minQty', 0))
            precision = 0
            if step_size < 1: precision = len(str(step_size).split('.')[-1].rstrip('0'))
            formatted = math.floor(qty / step_size) * step_size
            formatted = round(formatted, precision) if precision > 0 else int(formatted)
            if formatted < min_qty: return 0
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
        log(f"下单失败: {e}", "ERROR")
    return None

def buy_coin(coin, total_value):
    global positions, last_switch
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0: return False
    
    phase = detect_phase(coin)
    if phase == PHASE_ACCELERATION: position_pct = KELLY_BASE * 1.5
    elif phase == PHASE_EARLY: position_pct = KELLY_BASE * 1.2
    else: position_pct = KELLY_BASE
    
    position_value = total_value * position_pct
    quantity = position_value / price
    quantity = format_qty(coin, quantity)
    
    if quantity * price < 1: return False
    
    result = place_order(symbol, "BUY", quantity)
    if result:
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
    
    quantity = format_qty(coin, qty)
    if quantity * price < 1: return False
    
    result = place_order(symbol, "SELL", quantity)
    if result and coin in positions:
        entry = positions[coin]['entry']
        pnl = (price - entry) / entry * 100
        log(f"撞球卖出{coin}: {reason} 盈亏{pnl:+.2f}%", "TRADE")
        del positions[coin]
        return True
    return False

# ============ G35撞球主循环 ============
def run():
    global scan_count, positions
    
    log("=" * 60, "INFO")
    log("G35 Pool Strategy 撞球策略启动", "INFO")
    log("核心理念: 享受完当前币种回报周期后自然切换", "INFO")
    if GOCORE_AVAILABLE:
        log("✅ go-core v2.0 已加载", "INFO")
        log("✅ go-quantum 已加载", "INFO")
        log("✅ go-thermo 已加载", "INFO")
        log("✅ go-contrarian 已加载", "INFO")
        log("✅ go-detect 已加载", "INFO")
        log("✅ go-orderbook 已加载", "INFO")
        log("✅ go-liquidation 已加载", "INFO")
    else:
        log("⚠️ go-core不可用，使用独立分析", "INFO")
    log("=" * 60, "INFO")
    
    start_value = get_total_value(get_account())
    log(f"初始资产: ${start_value:.2f}", "INFO")
    
    while True:
        try:
            scan_count += 1
            ts = datetime.now().strftime("%H:%M:%S")
            log(f"\n{'='*60}", "INFO")
            log(f"撞球扫描 #{scan_count} ({ts})", "INFO")
            
            balances = get_account()
            total_value = get_total_value(balances)
            usdt = balances['usdt']
            log(f"资产: USDT={usdt:.2f} 总计=${total_value:.2f}", "INFO")
            
            # 1. 检查持仓状态 (撞球检查)
            for coin in list(positions.keys()):
                entry_info = positions[coin]
                should_exit, pnl, reason = should_exit_coin(coin, entry_info['entry'])
                
                # 更新最高价
                current_price = get_price(f"{coin}USDT")
                if current_price > entry_info['high']:
                    positions[coin]['high'] = current_price
                
                if should_exit:
                    sell_coin(coin, reason)
            
            # 2. 扫描候选币种 (整合go-core)
            candidates = []
            for coin in ALL_COINS:
                if coin in positions: continue
                if coin in balances['coins']: continue
                
                # 撞球周期分析
                should_enter, score, phase = should_enter_coin(coin)
                
                # 整合go-core预测
                if GOCORE_AVAILABLE:
                    try:
                        if not hasattr(run, '_go_core'):
                            run._go_core = GoCore(num_agents=100)
                        
                        gocore_result = run._go_core.predict(coin, interval='1h', period='7d')
                        
                        # 融合评分
                        if gocore_result['confidence'] > 0.5:
                            # go-core信号加强
                            if gocore_result['signal'] == 'buy':
                                score = score * 0.7 + gocore_result['score'] * 0.3
                                phase = phase + "+go"
                            elif gocore_result['signal'] == 'sell':
                                score = score * 0.5  # go-core卖出信号削弱
                    except:
                        pass
                
                if should_enter or score >= 70:
                    candidates.append({'coin': coin, 'score': score, 'phase': phase})
            
            # 3. 撞球切换决策
            if len(positions) < MAX_ACTIVE_COINS and candidates:
                candidates.sort(key=lambda x: -x['score'])
                best = candidates[0]
                
                # 检查冷却
                can_switch = True
                if best['coin'] in last_switch:
                    if time.time() - last_switch[best['coin']] < SWITCH_COOLDOWN:
                        can_switch = False
                
                if can_switch and usdt >= 5:
                    log(f"🎱 撞球进球: {best['coin']} ({best['phase']}期, 评分{best['score']})", "INFO")
                    buy_coin(best['coin'], total_value)
            
            # 4. 显示当前撞球状态
            log(f"当前撞球状态 ({len(positions)}/{MAX_ACTIVE_COINS}):", "INFO")
            for coin, info in positions.items():
                phase = detect_phase(coin)
                current_price = get_price(f"{coin}USDT")
                pnl = (current_price - info['entry']) / info['entry'] * 100
                log(f"  🎯 {coin}: {PHASE_NAMES[phase]}期 {pnl:+.1%}", "INFO")
            
            if not positions:
                log("  等待进球中...", "INFO")
            
            # 5. 本次收益
            if start_value > 0:
                pnl = (total_value - start_value) / start_value * 100
                log(f"累计收益: {pnl:+.2f}%", "INFO")
            
            log(f"等待60秒...", "INFO")
            time.sleep(60)
            
        except Exception as e:
            log(f"错误: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            time.sleep(10)

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║     G35 Pool Strategy - 撞球策略    ║
║   连续进球，周期轮转，收益最大化     ║
╚══════════════════════════════════════════════╝
    """)
    try:
        run()
    except KeyboardInterrupt:
        print("\n停止撞球策略...")
    except Exception as e:
        log(f"FATAL: {e}", "ERROR")
