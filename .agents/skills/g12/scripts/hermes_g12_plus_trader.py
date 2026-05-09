#!/usr/bin/env python3
"""
G12+ 实盘交易系统 v4.0 (最终版)
布林带收口突破 + 动能轮动
API签名+数量修正已完善
"""
import requests, time, json, numpy as np, hmac, hashlib, math, math
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
BINANCE_API = "https://api.binance.com"
API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"

TRADE_MODE = "AUTO"
POSITION_PCT = 0.35  # 优化后35%  # 降至20%
LEVERAGE = 5  # 提升到5x
LOG_FILE = '/tmp/g12_plus_trades.json'

# 缓存交易规则
RULES_CACHE = {'loaded': False}
NOTIONAL_MIN = 5  # 最小订单金额

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def sign_params(params):
    ts = int(time.time() * 1000)
    params['timestamp'] = ts
    params['recvWindow'] = 5000
    query_parts = []
    for k in sorted(params.keys()):
        if k != 'signature':
            query_parts.append(f"{k}={params[k]}")
    query = '&'.join(query_parts)
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query, sig

def load_rules():
    if RULES_CACHE['loaded']:
        return
    try:
        r = requests.get(f'{BINANCE_API}/api/v3/exchangeInfo', proxies=PROXIES, timeout=10)
        for s in r.json()['symbols']:
            RULES_CACHE[s['symbol']] = {}
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    RULES_CACHE[s['symbol']]['stepSize'] = float(f['stepSize'])
                    RULES_CACHE[s['symbol']]['minQty'] = float(f['minQty'])
                elif f['filterType'] == 'MIN_NOTIONAL':
                    RULES_CACHE[s['symbol']]['minNotional'] = float(f['minNotional'])
        RULES_CACHE['loaded'] = True
    except: pass

def get_price(symbol):
    try:
        r = requests.get(f'{BINANCE_API}/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(sym, limit=200):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'{BINANCE_API}/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'close':float(k[4])} for k in r.json()]
    except: return []

def get_account():
    try:
        params = {'timestamp': int(time.time()*1000), 'recvWindow': 5000}
        query, sig = sign_params(params)
        r = requests.get(f'{BINANCE_API}/api/v3/account?{query}&signature={sig}',
                        headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def round_qty(qty, symbol):
    """修正订单数量到正确的stepSize"""
    load_rules()
    sym_rules = RULES_CACHE.get(symbol, {})
    step = sym_rules.get('stepSize', 0.001)
    # 向下取整到step的倍数
    qty = float(qty)
    decimals = len(str(step).split('.')[-1])
    qty = (int(qty / step) * step)
    return round(qty, decimals)

def ensure_notional(qty, symbol):
    """确保订单金额满足最小notional要求"""
    load_rules()
    price = get_price(symbol)
    sym_rules = RULES_CACHE.get(symbol, {})
    min_notional = sym_rules.get('minNotional', NOTIONAL_MIN)
    
    if qty * price < min_notional:
        qty = min_notional / price
        qty = round_qty(qty, symbol)
    return qty

def place_order(symbol, side, qty, usdt_balance=999):
    if TRADE_MODE == "SIMULATE" or usdt_balance < 5:
        log(f"[AUTO-SIM] 余额${usdt_balance:.2f} < $5，自动切换模拟模式")
        log(f"[SIM] {side} {symbol} {qty}")
        return {'orderId': 'sim_' + str(int(time.time())), 'status': 'SIMULATE'}
    try:
        # 修正数量
        qty = round_qty(qty, symbol)
        qty = ensure_notional(qty, symbol)
        
        params = {'symbol': symbol, 'side': side, 'type': 'MARKET', 'quantity': qty}
        query, sig = sign_params(params)
        r = requests.post(f'{BINANCE_API}/api/v3/order?{query}&signature={sig}',
                         headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        result = r.json()
        
        if 'orderId' in result:
            log(f"  ✅ 成交: {result['executedQty']} @ ${float(result.get('fills',[{'price':0}])[0]['price']):.4f}")
        return result
    except Exception as e:
        log(f"  ❌ 下单失败: {e}")
        return None

def analyze_bb(c, klines):
    if len(klines) < 50: return None
    closes = [k['close'] for k in klines]
    bb_now = np.std(closes[-20:]) / np.mean(closes[-20:]) * 100
    bb_hist = np.std(closes) / np.mean(closes) * 100
    ratio = bb_now / bb_hist if bb_hist > 0 else 1
    bb_high = np.mean(closes[-20:]) + 2*np.std(closes[-20:])
    bb_low = np.mean(closes[-20:]) - 2*np.std(closes[-20:])
    position = (closes[-1] - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50
    return {'coin': c, 'ratio': ratio, 'position': position, 'price': closes[-1]}

def analyze_momentum():
    momenta = []
    for c in ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']:
        klines = get_klines(f'{c}USDT', 168)
        if klines and len(klines) >= 25:
            closes = [k['close'] for k in klines]
            chg_24h = (closes[-1] - closes[-25]) / closes[-25] * 100
            momenta.append({'coin': c, '24h': chg_24h, 'price': closes[-1]})
        time.sleep(0.05)
    return sorted(momenta, key=lambda x: -x['24h'])



def validate_trade(coin, price, balance):
    """验证交易可行性"""
    try:
        symbol = f"{coin}USDT"
        load_rules()
        rules = RULES_CACHE.get(symbol, {})
        step = float(rules.get('stepSize', 0.001))
        min_notional = float(rules.get('minNotional', 5))
        
        position_size = balance * POSITION_PCT * LEVERAGE
        fees = position_size * 0.001 * 2
        available = balance - (fees / LEVERAGE)
        if available <= 0:
            return None, "余额不足"
        
        raw_qty = available * POSITION_PCT * LEVERAGE / price
        decimals = max(0, -int(math.log10(step)) if step < 1 else 0)
        qty = round(raw_qty, decimals)
        
        notional = qty * price
        if notional < min_notional:
            return None, f"订单${notional:.2f}<最低${min_notional}"
        
        if qty <= 0:
            return None, "数量<=0"
        
        return qty, "OK"
    except Exception as e:
        return None, str(e)


def validate_trade(coin, price, balance):
    try:
        symbol = f"{coin}USDT"
        load_rules()
        rules = RULES_CACHE.get(symbol, {})
        step = float(rules.get('stepSize', 0.001))
        min_notional = float(rules.get('minNotional', 5))
        position_size = balance * POSITION_PCT * LEVERAGE
        fees = position_size * 0.001 * 2
        available = balance - (fees / LEVERAGE)
        if available <= 0:
            return None, "余额不足"
        raw_qty = available * POSITION_PCT * LEVERAGE / price
        decimals = max(0, -int(math.log10(step)) if step < 1 else 0)
        qty = round(raw_qty, decimals)
        notional = qty * price
        if notional < min_notional:
            return None, f"订单${notional:.2f}<${min_notional}"
        if qty <= 0:
            return None, "数量<=0"
        return qty, "OK"
    except Exception as e:
        return None, str(e)


def main():
    log("="*60)
    log("G12+ Trader [LIVE模式] v4.0")
    log("="*60)
    
    load_rules()  # 预加载交易规则
    
    acc = get_account()
    if acc and 'balances' in acc:
        usdt_balance = 0
        balances = {}
        for b in acc['balances']:
            free = float(b.get('free', 0))
            balances[b['asset']] = free
            if b['asset'] == 'USDT':
                usdt_balance = free
        log(f"\n📊 账户余额 (USDT: {usdt_balance:.2f})")
    else:
        log("❌ 账户获取失败")
        return
    
    log("\n📊 布林带收口检测:")
    bb_signals = {}
    for c in ['BTC','ETH','SOL']:
        klines = get_klines(f'{c}USDT', 200)
        result = analyze_bb(c, klines)
        if result:
            bb_signals[c] = result
            emoji = "🔴" if result['ratio'] < 0.3 else ("🟡" if result['ratio'] < 0.5 else "🟢")
            log(f"  {emoji} {c}: 比率{result['ratio']:.2f}x 位置{result['position']:.0f}% ${result['price']:.2f}")
        time.sleep(0.1)
    
    log("\n📊 动能排名:")
    momenta = analyze_momentum()
    for i, m in enumerate(momenta[:5], 1):
        emoji = "🟢" if m['24h'] > 0 else "🔴"
        log(f"  {i}. {emoji} {m['coin']}: {m['24h']:+.2f}%")
    
    log("\n🎯 交易信号:")
    trades = []
    
    for c, sig in bb_signals.items():
        if sig['ratio'] < 0.20:
            if sig['position'] < 20:
                trades.append({'type': 'LONG', 'coin': c, 'price': sig['price'], 'reason': f"收口{sig['ratio']:.2f}x+低位{sig['position']:.0f}%"})
            elif sig['position'] >= 80:
                trades.append({'type': 'SHORT', 'coin': c, 'price': sig['price'], 'reason': f"收口{sig['ratio']:.2f}x+高位{sig['position']:.0f}%"})
    
    if len(momenta) >= 2 and momenta[-1]['24h'] < -2 and momenta[0]['24h'] > -1.5:
        trades.append({'type': 'LONG', 'coin': momenta[0]['coin'], 'price': momenta[0]['price'], 'reason': f"轮动{momenta[-1]['coin']}→{momenta[0]['coin']}"})
    
    executed = []
    if trades:
        for t in trades:
            log(f"\n⚡ {t['type']}: {t['coin']} @ ${t['price']:.2f}")
            log(f"   原因: {t['reason']}")
            
            amount = usdt_balance * POSITION_PCT * LEVERAGE / t['price']
            side = "BUY" if t['type'] == 'LONG' else "SELL"
            symbol = f"{t['coin']}USDT"
            
            # 验证交易可行性
            qty, status = validate_trade(t['coin'], t['price'], usdt_balance)
            if qty is None:
                log(f"  ⚠️ 跳过 {t['coin']}: {status}")
                continue
            
            result = place_order(symbol, side, qty, usdt_balance)
            
            if result and 'orderId' in result:
                executed.append({'type': t['type'], 'coin': t['coin'], 'result': result})
    else:
        log("  🟡 无高置信度信号")
    
    # 保存记录
    try:
        with open(LOG_FILE, 'r') as f:
            history = json.load(f)
    except:
        history = []
    history.append({
        'time': datetime.now().isoformat(),
        'mode': TRADE_MODE,
        'signals': trades,
        'executed': executed,
        'balance': usdt_balance
    })
    history[-100:]
    with open(LOG_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    log(f"\n{'='*60}")
    log(f"执行: {len(executed)}笔 | 信号: {len(trades)}个 | 余额: ${usdt_balance:.2f}")
    log("="*60)

if __name__ == '__main__':
    main()
