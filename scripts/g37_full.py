#!/usr/bin/env python3
"""
G37 Full Control - 全账户交易系统
==================================
连接: 现货 + 全仓杠杆 + 逐仓杠杆 + USDT合约
功能: 资金调配 + 自主决策 + 自动交易
"""

import urllib.request, hmac, hashlib, time, json, sys, math, os
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g37_full.log"
STATE_FILE = "/home/goose/.openclaw/workspace/.g37_full_state.json"

TOP6_MEME = ['BOME', 'TURBO', 'BONK', 'FLOKI', 'PEPE', 'NEIRO']
TOP_MAJOR = ['BTC', 'ETH', 'XRP', 'SOL', 'ADA', 'DOT']
ALL_COINS = TOP6_MEME + TOP_MAJOR

MAX_ACTIVE = 3
KELLY_BASE = 0.30
STOP_LOSS = 0.05
TAKE_PROFIT = 0.20
SCAN_INTERVAL = 30

positions = {}
history = []

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")

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

def api_pub(url):
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return None

def get_price(symbol):
    data = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
    return float(data['price']) if data else 0

def get_klines(symbol, interval='1h', limit=100):
    data = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
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

def format_qty(coin, qty):
    if qty <= 0: return 0
    try:
        info = api_pub(f'https://api.binance.com/api/v3/exchangeInfo?symbol={coin}USDT')
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

# ============ 账户状态 ============

def get_spot_account():
    """现货账户"""
    data = api_signed("/api/v3/account")
    if not data or not isinstance(data, dict): return {'usdt': 0, 'coins': {}}
    result = {'usdt': 0, 'coins': {}}
    for b in data.get('balances', []):
        free = float(b.get('free', 0))
        if free > 0.0001:
            if b['asset'] == 'USDT':
                result['usdt'] = free
            else:
                result['coins'][b['asset']] = free
    return result

def get_cross_margin_account():
    """全仓杠杆账户"""
    data = api_signed("/sapi/v1/margin/account")
    if not data or not isinstance(data, dict) or 'userAssets' not in data: return {'total': 0, 'borrowed': 0, 'assets': {}}
    btc_price = get_price("BTCUSDT")
    total = 0
    result = {'total': 0, 'borrowed': 0, 'assets': {}}
    for a in data.get('userAssets', []):
        net = float(a.get('netAsset', 0))
        if net != 0:
            asset = a['asset']
            if asset == 'BTC':
                total += net * btc_price
            elif asset == 'USDT':
                total += net
            else:
                price = get_price(f"{asset}USDT")
                total += net * price if price > 0 else 0
            result['assets'][asset] = net
    result['total'] = total
    result['borrowed'] = float(data.get('totalLiabilityOfBtc', 0)) * btc_price
    return result

def get_isolated_margin_account():
    """逐仓杠杆账户"""
    data = api_signed("/sapi/v1/margin/isolated/account")
    if not data or not isinstance(data, dict) or 'assets' not in data: return {}
    result = {}
    for a in data.get('assets', []):
        sym = a.get('symbol', '')
        base = a.get('baseAsset', {})
        quote = a.get('quoteAsset', {})
        base_val = float(base.get('free', 0)) * get_price(f"{base.get('asset','USDT')}USDT")
        quote_val = float(quote.get('free', 0))
        if base_val + quote_val > 0.01:
            result[sym] = {'base': base_val, 'quote': quote_val, 'total': base_val + quote_val}
    return result

def get_futures_account():
    """U本位合约账户"""
    data = api_signed("/fapi/v2/account")
    if not data or isinstance(data, dict) and 'error' in data: return {'total': 0, 'positions': {}}
    if not isinstance(data, dict): return {'total': 0, 'positions': {}}
    total = float(data.get('totalMarginBalance', 0))
    positions = {}
    for p in data.get('positions', []):
        amt = float(p.get('positionAmt', 0))
        if abs(amt) > 0:
            symbol = p.get('symbol', '')
            upnl = float(p.get('unrealizedProfit', 0))
            positions[symbol] = {'amount': amt, 'upnl': upnl}
    return {'total': total, 'positions': positions}

def get_total_assets():
    """获取总资产"""
    spot = get_spot_account()
    cross = get_cross_margin_account()
    isolated = get_isolated_margin_account()
    futures = get_futures_account()
    
    # 计算现货总值
    spot_total = spot['usdt']
    for coin, qty in spot['coins'].items():
        price = get_price(f"{coin}USDT")
        if price > 0: spot_total += qty * price
    
    total = spot_total + cross['total'] + sum(a['total'] for a in isolated.values()) + futures['total']
    
    return {
        'spot': spot,
        'spot_total': spot_total,
        'cross': cross,
        'isolated': isolated,
        'futures': futures,
        'grand_total': total
    }

# ============ 交易操作 ============

def spot_buy(coin, qty):
    """现货买入"""
    try:
        params = {"symbol": f"{coin}USDT", "side": "BUY", "type": "MARKET", "quantity": str(qty)}
        result = api_signed("/api/v3/order", params, "POST")
        if result and 'orderId' in result:
            log(f"现货买入: {coin} {qty}", "TRADE")
            return True
    except Exception as e:
        log(f"现货买入失败: {e}", "ERROR")
    return False

def spot_sell(coin, qty):
    """现货卖出"""
    try:
        params = {"symbol": f"{coin}USDT", "side": "SELL", "type": "MARKET", "quantity": str(qty)}
        result = api_signed("/api/v3/order", params, "POST")
        if result and 'orderId' in result:
            log(f"现货卖出: {coin} {qty}", "TRADE")
            return True
    except Exception as e:
        log(f"现货卖出失败: {e}", "ERROR")
    return False

def cross_margin_transfer(asset, amount, direction):
    """全仓杠杆转账 (SPOT->CROSS or CROSS->SPOT)"""
    try:
        params = {
            "asset": asset, "amount": str(amount),
            "transFrom": "SPOT" if direction == "CROSS" else "CROSS_MARGIN",
            "transTo": "CROSS_MARGIN" if direction == "CROSS" else "SPOT"
        }
        result = api_signed("/sapi/v1/margin/transfer", params, "POST")
        if 'tranId' in result:
            log(f"全仓转账: {direction} {asset} {amount}", "TRADE")
            return True
    except Exception as e:
        log(f"全仓转账失败: {e}", "ERROR")
    return False

def cross_margin_borrow(asset, amount):
    """全仓杠杆借款"""
    try:
        params = {"asset": asset, "amount": str(amount)}
        result = api_signed("/sapi/v1/margin/loan", params, "POST")
        if 'tranId' in result:
            log(f"全仓借款: {asset} {amount}", "TRADE")
            return True
    except Exception as e:
        log(f"借款失败: {e}", "ERROR")
    return False

def margin_repay(asset, amount):
    """还款"""
    try:
        params = {"asset": asset, "amount": str(amount)}
        result = api_signed("/sapi/v1/margin/repay", params, "POST")
        if 'tranId' in result:
            log(f"还款: {asset} {amount}", "TRADE")
            return True
    except: return False

def isolated_margin_trade(symbol, side, qty):
    """逐仓杠杆交易"""
    try:
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": str(qty)}
        result = api_signed("/sapi/v1/margin/order", params, "POST")
        if 'orderId' in result:
            log(f"逐仓交易: {symbol} {side} {qty}", "TRADE")
            return True
    except Exception as e:
        log(f"逐仓交易失败: {e}", "ERROR")
    return False

def futures_trade(symbol, side, qty, leverage=5):
    """合约交易"""
    try:
        # 设置杠杆
        api_signed("/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage}, "POST")
        # 下单
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": str(qty)}
        result = api_signed("/fapi/v1/order", params, "POST")
        if 'orderId' in result:
            log(f"合约{'做多' if side=='BUY' else '做空'}: {symbol} {qty}", "TRADE")
            return True
    except Exception as e:
        log(f"合约交易失败: {e}", "ERROR")
    return False

# ============ 策略分析 ============

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

def get_score(coin):
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
    
    return max(0, min(100, score))

# ============ 主策略 ============

def allocate_assets():
    """资金调配决策"""
    accounts = get_total_assets()
    log(f"\n{'='*60}", "INFO")
    log(f"📊 全账户状态", "INFO")
    log(f"{'='*60}", "INFO")
    log(f"现货: ${accounts['spot_total']:.2f} (USDT ${accounts['spot']['usdt']:.2f})", "INFO")
    log(f"全仓杠杆: ${accounts['cross']['total']:.2f}", "INFO")
    log(f"逐仓杠杆: ${sum(a['total'] for a in accounts['isolated'].values()):.2f}", "INFO")
    log(f"合约: ${accounts['futures']['total']:.2f}", "INFO")
    log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
    log(f"总资产: ${accounts['grand_total']:.2f}", "INFO")
    return accounts

def auto_trade():
    """自主交易主循环"""
    global positions
    
    accounts = allocate_assets()
    spot = accounts['spot']
    total = accounts['grand_total']
    usdt = spot['usdt']
    
    # 扫描候选币种
    candidates = []
    for coin in ALL_COINS:
        phase = detect_phase(coin)
        score = get_score(coin)
        if phase in [1, 2] and score >= 65:
            candidates.append({'coin': coin, 'phase': phase, 'score': score})
    
    candidates.sort(key=lambda x: -x['score'])
    
    # 买入决策
    if candidates and usdt >= 10:
        best = candidates[0]
        # 优先Top6 Meme
        top6 = [c for c in candidates if c['coin'] in TOP6_MEME]
        if top6: best = top6[0]
        
        # 使用30%仓位
        position_value = total * KELLY_BASE
        price = get_price(f"{best['coin']}USDT")
        if price > 0:
            qty = format_qty(best['coin'], position_value / price)
            if qty * price >= 1:
                if spot_buy(best['coin'], qty):
                    positions[best['coin']] = {'entry': price, 'time': time.time()}
                    log(f"🎯买入: {best['coin']} @ ${price} (评分{best['score']:.0f})", "INFO")
    
    # 卖出决策 (止损/止盈)
    for coin in list(positions.keys()):
        info = positions[coin]
        current = get_price(f"{coin}USDT")
        if current > 0:
            pnl = (current - info['entry']) / info['entry']
            phase = detect_phase(coin)
            
            if pnl <= -STOP_LOSS:
                log(f"🛑止损: {coin} {pnl:.1%}", "INFO")
                balances = get_spot_account()
                qty = balances['coins'].get(coin, 0)
                if qty > 0: spot_sell(coin, format_qty(coin, qty))
                del positions[coin]
            elif pnl >= TAKE_PROFIT or phase == 3:
                log(f"💰止盈: {coin} {pnl:.1%}", "INFO")
                balances = get_spot_account()
                qty = balances['coins'].get(coin, 0)
                if qty > 0: spot_sell(coin, format_qty(coin, qty))
                del positions[coin]
            elif phase == 4:
                log(f"📤衰退卖出: {coin}", "INFO")
                balances = get_spot_account()
                qty = balances['coins'].get(coin, 0)
                if qty > 0: spot_sell(coin, format_qty(coin, qty))
                del positions[coin]
    
    # 显示持仓
    log(f"\n📈 持仓状态:", "INFO")
    balances = get_spot_account()
    for coin, info in positions.items():
        current = get_price(f"{coin}USDT")
        pnl = (current - info['entry']) / info['entry'] if info['entry'] > 0 else 0
        phase = detect_phase(coin)
        log(f"  {coin}: {['盘整','启动','加速','高峰','衰退'][phase]} {pnl:+.1%}", "INFO")
    
    if not positions:
        log("  无持仓", "INFO")
    
    log(f"\n⏱️ 下次扫描: {SCAN_INTERVAL}秒", "INFO")

def save_state():
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({'positions': positions, 'time': time.time()}, f)
    except: pass

def load_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f:
                return json.load(f)
    except: pass
    return {'positions': {}}

def run():
    global positions
    
    log("=" * 60, "INFO")
    log("G37 FULL CONTROL 启动", "INFO")
    log("全账户: 现货 + 全仓杠杆 + 逐仓杠杆 + 合约", "INFO")
    log("=" * 60, "INFO")
    
    # 加载状态
    state = load_state()
    positions.update(state.get('positions', {}))
    
    while True:
        try:
            auto_trade()
            save_state()
            time.sleep(SCAN_INTERVAL)
        except Exception as e:
            log(f"错误: {e}", "ERROR")
            import traceback; traceback.print_exc()
            time.sleep(10)

if __name__ == '__main__':
    try: run()
    except KeyboardInterrupt: print("\n停止")
