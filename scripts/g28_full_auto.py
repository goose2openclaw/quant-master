#!/usr/bin/env python3
"""
G28 全自动交易系统
===================
功能:
1. 默认开启自动交易
2. 账户间资金自动调配 (现货/全仓/合约)
3. 币种间智能分配
4. Oracle决策驱动
5. 动态仓位管理
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
SCAN_INTERVAL = 60
TRADE_LOG = "/home/goose/.openclaw/workspace/logs/g28_trades.log"
STATE_FILE = "/home/goose/.openclaw/workspace/logs/g28_state.json"

# ========== 配置 ==========
TRADE_CONFIG = {
    'BTC': {'type':'major','position_pct':0.15,'max_position':0.20,'stop_loss':0.02,'take_profit':0.15,'leverage':5},
    'ETH': {'type':'major','position_pct':0.12,'max_position':0.15,'stop_loss':0.03,'take_profit':0.15,'leverage':5},
    'BNB': {'type':'major','position_pct':0.10,'max_position':0.15,'stop_loss':0.03,'take_profit':0.15,'leverage':5},
    'LINK': {'type':'major','position_pct':0.10,'max_position':0.15,'stop_loss':0.03,'take_profit':0.15,'leverage':5},
    'SOL': {'type':'major','position_pct':0.10,'max_position':0.15,'stop_loss':0.03,'take_profit':0.20,'leverage':5},
    'UNI': {'type':'major','position_pct':0.10,'max_position':0.15,'stop_loss':0.03,'take_profit':0.20,'leverage':5},
    'BOME': {'type':'meme','position_pct':0.08,'max_position':0.10,'stop_loss':0.05,'take_profit':0.30,'leverage':3},
    'TURBO': {'type':'meme','position_pct':0.08,'max_position':0.10,'stop_loss':0.05,'take_profit':0.30,'leverage':3},
    'PUMP': {'type':'meme','position_pct':0.08,'max_position':0.10,'stop_loss':0.05,'take_profit':0.30,'leverage':3},
    'NEIRO': {'type':'meme','position_pct':0.08,'max_position':0.10,'stop_loss':0.05,'take_profit':0.30,'leverage':3},
}

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(TRADE_LOG, "a") as f:
        f.write(line + "\n")

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except: return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ========== API ==========
def signed_api(endpoint, params=None, method="GET"):
    ts = int(time.time() * 1000)
    base = {"timestamp": ts, "recvWindow": 5000}
    if params: base.update(params)
    q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        resp = urllib.request.build_opener(proxy_handler).open(req, timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def futures_signed(endpoint, params=None, method="GET"):
    ts = int(time.time() * 1000)
    base = {"timestamp": ts, "recvWindow": 5000}
    if params: base.update(params)
    q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        resp = urllib.request.build_opener(proxy_handler).open(req, timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try: return float(json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())['price'])
    except: return 0

def get_rsi(symbol, period=14):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=50'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        closes = [float(k[4]) for k in data]
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        if avg_loss == 0: return 100
        return 100-(100/(1+avg_gain/avg_loss))
    except: return 50

def get_momentum(symbol):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=25'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        data = json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
        if len(data) < 24: return 0
        return ((float(data[-1][4]) - float(data[-24][4])) / float(data[-24][4])) * 100
    except: return 0

# ========== 账户管理 ==========
def get_all_balances():
    """获取所有账户余额"""
    result = {
        'spot_usdt': 0, 'spot_coins': {},
        'margin_usdt': 0, 'margin_coins': {},
        'futures_usdt': 0
    }
    
    # 现货
    account = signed_api("/api/v3/account")
    if 'balances' in account:
        for b in account['balances']:
            free = float(b.get('free', 0))
            if free > 0.001:
                if b['asset'] == 'USDT':
                    result['spot_usdt'] = free
                else:
                    result['spot_coins'][b['asset']] = free
    
    # 合约
    fut = futures_signed("/fapi/v2/balance")
    if isinstance(fut, list):
        for b in fut:
            if b.get('asset') == 'USDT':
                result['futures_usdt'] = float(b.get('availableBalance', 0))
    
    return result

def transfer_funds(asset, amount, from_acc, to_acc):
    """账户间转账"""
    type_map = {'spot': 'MAIN', 'margin': 'CROSS', 'futures': 'USDT_FUTURE'}
    from_type = type_map.get(from_acc, 'MAIN')
    to_type = type_map.get(to_acc, 'CROSS')
    
    params = {"asset": asset, "amount": amount, "type": 1}  # 1 = 站内转账
    result = signed_api("/sapi/v1/asset/transfer", params, "POST")
    if 'error' in result:
        log(f"转账失败: {result['error']}")
        return False
    log(f"✅ 转账 {amount} {asset}: {from_acc} → {to_acc}")
    return True

def spot_buy(symbol, quantity):
    """现货买入"""
    params = {"symbol": f"{symbol}USDT", "side": "BUY", "type": "MARKET", "quantity": quantity}
    result = signed_api("/api/v3/order", params, "POST")
    if 'error' in result:
        log(f"买入失败: {result['error']}")
        return None
    log(f"✅ 现货买入 {quantity} {symbol}")
    return result

def spot_sell(symbol, quantity):
    """现货卖出"""
    params = {"symbol": f"{symbol}USDT", "side": "SELL", "type": "MARKET", "quantity": quantity}
    result = signed_api("/api/v3/order", params, "POST")
    if 'error' in result:
        log(f"卖出失败: {result['error']}")
        return None
    log(f"✅ 现货卖出 {quantity} {symbol}")
    return result

def futures_open(symbol, side, quantity, leverage=5):
    """合约开仓"""
    # 设置杠杆
    futures_signed("/fapi/v1/leverage", {"symbol": f"{symbol}USDT", "leverage": leverage}, "POST")
    # 开仓
    params = {"symbol": f"{symbol}USDT", "side": side, "type": "MARKET", "quantity": quantity}
    result = futures_signed("/fapi/v1/order", params, "POST")
    if 'error' in result:
        log(f"合约{'买入' if side=='BUY' else '卖出'}失败: {result['error']}")
        return None
    log(f"✅ 合约{'多' if side=='BUY' else '空'}开 {quantity} {symbol} @{leverage}x")
    return result

# ========== 核心逻辑 ==========
def oracle_decision(rsi, momentum, coin_type):
    """Oracle决策"""
    buy_thresh = 35 if coin_type == "meme" else 40
    sell_thresh = 75 if coin_type == "meme" else 70
    
    if rsi < buy_thresh and momentum < -2: return "STRONG_BUY"
    if rsi < buy_thresh: return "BUY"
    if rsi > sell_thresh and momentum > 3: return "STRONG_SELL"
    if rsi > sell_thresh - 5: return "SELL"
    return "HOLD"

def capital_allocation(balances, state):
    """智能资金分配"""
    total_capital = balances['spot_usdt'] + balances['futures_usdt']
    
    # 30%留作备用金
    reserve = total_capital * 0.3
    trade_capital = total_capital - reserve
    
    # 按潜力分配
    rankings = []
    for coin in TRADE_CONFIG:
        rsi = get_rsi(f"{coin}USDT")
        momentum = get_momentum(f"{coin}USDT")
        cfg = TRADE_CONFIG[coin]
        score = (75 - rsi) * 2 + momentum if rsi < 50 else (rsi - 50) * 0.5 - momentum
        rankings.append((coin, score, rsi, momentum))
    
    rankings.sort(key=lambda x: x[1], reverse=True)
    
    # 分配资金
    allocations = {}
    per_coin = trade_capital / min(len(rankings), 5)
    for coin, score, rsi, momentum in rankings[:5]:
        allocations[coin] = {
            'allocation': per_coin,
            'rsi': rsi,
            'momentum': momentum,
            'decision': oracle_decision(rsi, momentum, TRADE_CONFIG[coin]['type'])
        }
    
    return allocations, total_capital

def execute_strategy(balances, allocations, state):
    """执行策略"""
    executed = False
    
    for coin, data in allocations.items():
        cfg = TRADE_CONFIG[coin]
        price = get_price(f"{coin}USDT")
        current_qty = balances['spot_coins'].get(coin, 0)
        current_value = current_qty * price
        
        decision = data['decision']
        allocated = data['allocation']
        target_value = allocated * 0.8  # 目标仓位80%
        
        log(f"  {coin}: {decision} (RSI:{data['rsi']:.1f} 动量:{data['momentum']:+.2f}%)")
        
        if decision in ['STRONG_BUY', 'BUY'] and current_value < target_value:
            # 买入
            if balances['spot_usdt'] >= allocated * 0.2:
                buy_value = min(allocated * 0.5, balances['spot_usdt'])
                qty = buy_value / price
                if qty > get_min_qty(coin):
                    result = spot_buy(coin, qty)
                    if result:
                        balances['spot_usdt'] -= buy_value
                        balances['spot_coins'][coin] = balances['spot_coins'].get(coin, 0) + qty
                        state[coin] = {'action': 'BUY', 'price': price, 'time': time.time()}
                        executed = True
        
        elif decision in ['STRONG_SELL', 'SELL']:
            # 卖出
            if current_qty > 0:
                sell_qty = current_qty * 0.5
                if sell_qty > get_min_qty(coin):
                    result = spot_sell(coin, sell_qty)
                    if result:
                        balances['spot_usdt'] += sell_qty * price
                        balances['spot_coins'][coin] = current_qty - sell_qty
                        state[coin] = {'action': 'SELL', 'price': price, 'time': time.time()}
                        executed = True
        
        elif decision == 'HOLD' and current_value > allocated * 1.2:
            # 止盈
            sell_qty = current_qty * 0.3
            if sell_qty > get_min_qty(coin):
                spot_sell(coin, sell_qty)
                executed = True
    
    return executed

def get_min_qty(symbol):
    """最小下单量"""
    min_qty = {'BOME': 10000, 'TURBO': 1000, 'PUMP': 100, 'NEIRO': 10000}
    return min_qty.get(symbol, 1)

# ========== 主循环 ==========
def main():
    log("=" * 70)
    log("G28 全自动交易系统启动 ⚠️ AUTO MODE")
    log(f"扫描间隔: {SCAN_INTERVAL}秒")
    log("功能: 自动交易 + 账户调配 + 智能分配")
    log("=" * 70)
    
    state = load_state()
    balances = get_all_balances()
    
    log(f"初始余额: 现货${balances['spot_usdt']:.2f} 合约${balances['futures_usdt']:.2f}")
    
    while True:
        try:
            # 刷新余额
            balances = get_all_balances()
            total = balances['spot_usdt'] + balances['futures_usdt']
            
            log(f"\n{'='*50}")
            log(f"扫描 {datetime.now().strftime('%H:%M:%S')} | 总资本: ${total:.2f}")
            
            # 智能分配
            allocations, total_capital = capital_allocation(balances, state)
            
            # 执行
            executed = execute_strategy(balances, allocations, state)
            
            # 账户调配
            if balances['spot_usdt'] > 100:
                # 转入合约
                transfer_funds('USDT', balances['spot_usdt'] * 0.1, 'spot', 'futures')
            
            save_state(state)
            
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
