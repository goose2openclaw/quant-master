#!/usr/bin/env python3
"""
🧠 GG 增强杠杆引擎 v2.1
动态杠杆 + 资金复用 + 自主决策 + 安全保障
日期: 2026-05-04
"""

import requests, hmac, hashlib, time, json, random, math, os
from datetime import datetime

API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"
PROXIES = {"http": "http://172.29.144.1:7897", "https": "http://172.29.144.1:7897"}

KEY_COINS = ['LINK', 'DOGE', 'BTC', 'ETH', 'SOL', 'BNB', 'ORDI', 'ADA', 'XRP']
CONFIG_FILE = "/tmp/gg_leverage_config.json"
LOG_FILE = "/tmp/gg_leverage.log"

# ============ 配置 ============
LEV_THRESHOLDS = {
    'strong_buy': {'D': 0.8, 'miro_buy': 60, 'lev': 5, 'action': 'ADD_5x'},
    'medium_buy': {'D': 0.5, 'miro_buy': 40, 'lev': 3, 'action': 'ADD_3x'},
    'normal_buy': {'D': 0.15, 'miro_buy': 30, 'lev': 2, 'action': 'ADD_2x'},
    'hold': {'D': 0.0, 'miro_buy': 0, 'lev': 0, 'action': 'HOLD'},
    'sell': {'D': -0.1, 'miro_sell': 60, 'lev': 0, 'action': 'CLOSE_PARTIAL'},
    'strong_sell': {'D': -0.3, 'miro_sell': 80, 'lev': 0, 'action': 'CLOSE_ALL'},
}

MARGIN_SAFETY = {'min_margin_level': 2.5, 'warn_margin_level': 3.0}
TAKE_PROFIT_TARGET = 0.15  # 15% 止盈
STOP_LOSS_TARGET = 0.05     # 5% 止损
RECYCLE_PROFIT_PCT = 0.30   # 盈利的30%套现再投入

# ============ 日志 ============
def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ============ API 工具 ============
def binance_get(endpoint, params=""):
    url = f"https://api.binance.com{endpoint}"
    if params: url += "?" + params
    r = requests.get(url, proxies=PROXIES, timeout=10)
    return r.json()

def binance_post(endpoint, params=""):
    url = f"https://api.binance.com{endpoint}"
    if params: url += "?" + params
    r = requests.post(url, proxies=PROXIES, timeout=10)
    return r.json()

def margin_request(method, endpoint, params=""):
    ts = int(time.time() * 1000)
    full_params = f"{params}&timestamp={ts}&recvWindow=5000" if params else f"timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), full_params.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{full_params}&signature={sig}"
    r = requests.request(method, url, headers={"X-MBX-APIKEY": API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

# ============ 账户状态 ============
def get_account():
    r = margin_request("GET", "/api/v3/account", "")
    spot = {b['asset']: float(b['free']) for b in r['balances'] if float(b['free']) > 0.0001}
    r2 = margin_request("GET", "/sapi/v1/margin/account", "")
    cross = {}
    for a in r2.get('userAssets', []):
        free = float(a.get('free', 0))
        borrowed = float(a.get('borrowed', 0))
        if free > 0 or borrowed > 0:
            cross[a['asset']] = {'free': free, 'borrowed': borrowed}
    margin_level = float(r2.get('marginLevel', 999))
    total_btc = float(r2['totalAssetOfBtc'])
    liab_btc = float(r2['totalLiabilityOfBtc'])
    btc_price = float(binance_get("/api/v3/ticker/price?symbol=BTCUSDT")['price'])
    return {
        'spot': spot, 'cross': cross,
        'margin_level': margin_level,
        'total_usd': total_btc * btc_price,
        'liability_usd': liab_btc * btc_price
    }

def get_prices(coins):
    prices = {}
    for c in coins:
        try:
            r = binance_get(f"/api/v3/ticker/price?symbol={c}USDT")
            prices[c] = float(r['price'])
        except:
            prices[c] = 0
    prices['USDT'] = 1
    return prices

# ============ Mirofish 仿真 ============
def mirofish_sim(coin, price):
    sym = f"{coin}USDT"
    try:
        klines = binance_get(f"/api/v3/klines?symbol={sym}&interval=1h&limit=72")
        closes = [float(d[4]) for d in klines]
        volumes = [float(d[5]) for d in klines]
        t24 = binance_get(f"/api/v3/ticker/24hr?symbol={sym}")
        change24 = float(t24['priceChangePercent'])
        
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma60 = sum(closes[-60:]) / 60
        trend = 1 if ma5 > ma20 > ma60 else (-1 if ma5 < ma20 < ma60 else 0)
        
        returns = [(closes[i]-closes[i-1])/closes[i-1]*100 for i in range(1, len(closes))]
        volatility = sum(abs(r) for r in returns) / len(returns)
        vol_ratio = volumes[-1] / (sum(volumes[-24:]) / 24)
        
        # 打兔子 D 分数
        D = 0.35 * trend + 0.3 * (change24 / 10) + 0.25 * (vol_ratio - 1) - 0.1 * volatility
        
        # Mirofish 1000 智能体
        N = 1000
        random.seed(int(time.time()) + hash(coin) % 1000)
        votes = {'buy': 0, 'hold': 0, 'sell': 0}
        for _ in range(N):
            noise = random.gauss(0, 0.2)
            score = D + noise
            if score > 0.6: votes['buy'] += 1
            elif score > 0.3: votes['hold'] += 1
            else: votes['sell'] += 1
        total = sum(votes.values())
        
        return {
            'D': D, 'change24': change24,
            'trend': trend, 'volatility': volatility,
            'buy_pct': votes['buy'] / total * 100,
            'hold_pct': votes['hold'] / total * 100,
            'sell_pct': votes['sell'] / total * 100,
            'decision': max(votes, key=votes.get),
            'price': price
        }
    except Exception as e:
        return {'D': 0, 'change24': 0, 'error': str(e)}

# ============ 决策引擎 ============
def decide_action(signal, margin_level, current_position_value, available_usdt):
    D = signal['D']
    buy_pct = signal['buy_pct']
    sell_pct = signal['sell_pct']
    decision = signal['decision']
    price = signal['price']
    
    log(f"决策分析: D={D:.3f} buy={buy_pct:.1f}% sell={sell_pct:.1f}% margin={margin_level:.2f}")
    
    # 保证金安全检查
    if margin_level < MARGIN_SAFETY['min_margin_level']:
        log("⚠️ 保证金率危险! 强制减仓", "WARN")
        return {'action': 'FORCE_REDUCE', 'reason': 'margin_danger'}
    
    if margin_level < MARGIN_SAFETY['warn_margin_level']:
        log(f"⚠️ 保证金率预警: {margin_level:.2f}", "WARN")
    
    # 强势买入信号
    if D > 0.8 and buy_pct > 60:
        lev = 5
        needed = available_usdt * 4  # 5x杠杆
        qty = needed / price
        log(f"🚀 强势信号 → 5x做多 需要{qty:.4f}个")
        return {'action': 'BUY_5x', 'lev': 5, 'qty': qty, 'D': D}
    
    elif D > 0.5 and buy_pct > 40:
        lev = 3
        needed = available_usdt * 2
        qty = needed / price
        log(f"📈 中等信号 → 3x做多 需要{qty:.4f}个")
        return {'action': 'BUY_3x', 'lev': 3, 'qty': qty, 'D': D}
    
    elif D > 0.15:
        lev = 2
        log(f"📊 普通信号 → 2x做多")
        return {'action': 'BUY_2x', 'lev': 2, 'qty': 0, 'D': D}
    
    # 卖出信号 - 套现
    elif D < -0.3 or sell_pct > 80:
        log(f"🔴 强势卖出信号 → 全仓平仓")
        return {'action': 'CLOSE_ALL', 'D': D}
    
    elif D < -0.1 or sell_pct > 60:
        log(f"⚠️ 卖出信号 → 部分套现")
        return {'action': 'CLOSE_PARTIAL', 'pct': RECYCLE_PROFIT_PCT, 'D': D}
    
    else:
        log(f"⏸️ 持有观望")
        return {'action': 'HOLD', 'D': D}

# ============ 交易执行 ============
def execute_trade(coin, action, qty=0, lev=2):
    sym = f"{coin}USDT"
    try:
        if action == 'BUY_5x' or action == 'BUY_3x' or action == 'BUY_2x':
            # 借入 USDT
            borrow_qty = qty * 0.8  # 预留手续费
            ts = int(time.time() * 1000)
            params = f"asset=USDT&amount={borrow_qty:.2f}&timestamp={ts}&recvWindow=5000"
            sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
            r = requests.post(f"https://api.binance.com/sapi/v1/margin/loan?{params}&signature={sig}",
                           headers={"X-MBX-APIKEY": API_KEY}, proxies=PROXIES, timeout=10)
            if 'tranId' not in r.json():
                log(f"借入失败: {r.json()}", "ERROR")
                return False
            
            # 全仓市价买入
            ts = int(time.time() * 1000)
            params = f"symbol={sym}&side=BUY&type=MARKET&quantity={qty:.4f}&isIsolated=false&timestamp={ts}&recvWindow=5000"
            sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
            r = requests.post(f"https://api.binance.com/sapi/v1/margin/order?{params}&signature={sig}",
                           headers={"X-MBX-APIKEY": API_KEY}, proxies=PROXIES, timeout=10)
            if 'orderId' in r.json():
                log(f"✅ {action} {coin}: {r.json().get('executedQty', qty)}个")
                return True
            else:
                log(f"❌ 买入失败: {r.json()}", "ERROR")
                return False
        
        elif action == 'CLOSE_ALL':
            # 全仓市价卖出全部
            acc = get_account()
            qty = acc['cross'].get(coin, {}).get('free', 0)
            if qty < 0.0001:
                log(f"{coin} 无持仓可卖")
                return False
            ts = int(time.time() * 1000)
            params = f"symbol={sym}&side=SELL&type=MARKET&quantity={qty:.4f}&isIsolated=false&timestamp={ts}&recvWindow=5000"
            sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
            r = requests.post(f"https://api.binance.com/sapi/v1/margin/order?{params}&signature={sig}",
                           headers={"X-MBX-APIKEY": API_KEY}, proxies=PROXIES, timeout=10)
            if 'orderId' in r.json():
                log(f"✅ 全仓平仓 {coin}: {r.json().get('executedQty', qty)}个")
                return True
            else:
                log(f"❌ 平仓失败: {r.json()}", "ERROR")
                return False
        
        elif action == 'CLOSE_PARTIAL':
            acc = get_account()
            current = acc['cross'].get(coin, {}).get('free', 0)
            sell_qty = current * RECYCLE_PROFIT_PCT
            if sell_qty < 0.0001:
                return False
            ts = int(time.time() * 1000)
            params = f"symbol={sym}&side=SELL&type=MARKET&quantity={sell_qty:.4f}&isIsolated=false&timestamp={ts}&recvWindow=5000"
            sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
            r = requests.post(f"https://api.binance.com/sapi/v1/margin/order?{params}&signature={sig}",
                           headers={"X-MBX-APIKEY": API_KEY}, proxies=PROXIES, timeout=10)
            if 'orderId' in r.json():
                log(f"✅ 部分套现 {coin}: {sell_qty:.4f}个 ({RECYCLE_PROFIT_PCT*100:.0f}%)")
                return True
            else:
                log(f"❌ 部分套现失败: {r.json()}", "ERROR")
                return False
    except Exception as e:
        log(f"交易异常: {e}", "ERROR")
        return False

# ============ 自主循环主函数 ============
def run_autonomous_cycle(target_coin=None):
    log("=" * 50)
    log("🧠 GG 增强杠杆引擎 v2.1 启动")
    
    acc = get_account()
    prices = get_prices(KEY_COINS)
    margin_level = acc['margin_level']
    
    log(f"保证金率: {margin_level:.3f} | 总资产: ${acc['total_usd']:.2f} | 负债: ${acc['liability_usd']:.2f}")
    
    # 确定扫描范围
    coins_to_scan = [target_coin] if target_coin else KEY_COINS
    
    decisions = {}
    for coin in coins_to_scan:
        price = prices.get(coin, 0)
        if price == 0: continue
        
        signal = mirofish_sim(coin, price)
        if 'error' in signal:
            log(f"{coin} 仿真失败: {signal['error']}", "WARN")
            continue
        
        log(f"📊 {coin}: D={signal['D']:.3f} change={signal['change24']:+.2f}% trend={signal['trend']} Mirofish={signal['decision']}({signal['buy_pct']:.0f}%/{signal['sell_pct']:.0f}%)")
        
        # 当前持仓
        current_pos = acc['cross'].get(coin, {}).get('free', 0)
        available_usdt = acc['cross'].get('USDT', {}).get('free', 0) + acc['spot'].get('USDT', 0)
        
        action_decision = decide_action(signal, margin_level, current_pos * price, available_usdt)
        decisions[coin] = {'signal': signal, 'action': action_decision}
        
        log(f"🤖 决策: {action_decision['action']}")
        
        # 执行交易
        if action_decision['action'] in ['BUY_5x', 'BUY_3x', 'BUY_2x']:
            if action_decision.get('qty', 0) > 0:
                execute_trade(coin, action_decision['action'], action_decision['qty'], action_decision['lev'])
        elif action_decision['action'] in ['CLOSE_ALL', 'CLOSE_PARTIAL']:
            execute_trade(coin, action_decision['action'])
    
    # 保存状态
    state = {
        'timestamp': datetime.now().isoformat(),
        'margin_level': margin_level,
        'decisions': {c: {'D': d['signal']['D'], 'action': d['action']['action']} for c, d in decisions.items()}
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    log("🧠 循环完成")
    return decisions

# ============ CLI ============
if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run_autonomous_cycle(target)
