#!/usr/bin/env python3
"""
G28 资金调配编排器
==================
功能:
1. 监控所有账户 (现货/全仓/逐仓/合约)
2. 智能调配资金到最高收益机会
3. 动态再平衡
4. 风险隔离
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g28_capital.log"
STATE_FILE = "/home/goose/.openclaw/workspace/logs/g28_capital_state.json"

# ========== 风险配置 ==========
RISK_CONFIG = {
    'max_position_per_coin': 0.15,      # 单币最大15%
    'reserve_ratio': 0.20,              # 备用金20%
    'margin_warning_ratio': 0.80,       # 预警强平线80%
    'stop_loss_ratio': 0.05,            # 止损5%
    'take_profit_ratio': 0.25,          # 止盈25%
}

# ========== 工具函数 ==========
def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except: return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

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
def get_all_accounts():
    """获取所有账户信息"""
    accounts = {
        'spot': {'usdt': 0, 'coins': {}},
        'margin_cross': {'usdt': 0, 'coins': {}, 'liability': 0},
        'margin_isolated': {'usdt': 0, 'coins': {}},
        'futures': {'usdt': 0, 'positions': {}},
    }
    
    # 现货账户
    spot = signed_api("/api/v3/account")
    if 'balances' in spot:
        for b in spot['balances']:
            free = float(b.get('free', 0))
            locked = float(b.get('locked', 0))
            if free > 0.001:
                if b['asset'] == 'USDT':
                    accounts['spot']['usdt'] = free
                else:
                    accounts['spot']['coins'][b['asset']] = {'free': free, 'locked': locked}
    
    # 全仓账户
    margin = signed_api("/sapi/v1/margin/account", {"recvWindow": 5000})
    if 'userAssets' in margin:
        for a in margin['userAssets']:
            net = float(a.get('netAsset', 0))
            if abs(net) > 0.001:
                if a['asset'] == 'USDT':
                    accounts['margin_cross']['usdt'] = net
                else:
                    accounts['margin_cross']['coins'][a['asset']] = net
    
    # 逐仓账户
    isolated = signed_api("/sapi/v1/margin/isolated/account", {"recvWindow": 5000})
    if 'assets' in isolated:
        for a in isolated['assets']:
            if float(a.get('baseAsset', {}).get('free', 0)) > 0:
                symbol = a['symbol']
                accounts['margin_isolated']['coins'][symbol] = {
                    'base': float(a.get('baseAsset', {}).get('free', 0)),
                    'quote': float(a.get('quoteAsset', {}).get('free', 0)),
                }
    
    # 合约账户
    fut = futures_signed("/fapi/v2/balance")
    if isinstance(fut, list):
        for b in fut:
            if b.get('asset') == 'USDT':
                accounts['futures']['usdt'] = float(b.get('availableBalance', 0))
    
    # 合约持仓
    positions = futures_signed("/fapi/v2/positionRisk", {"marginType": "cross"})
    if isinstance(positions, list):
        for p in positions:
            if float(p.get('positionAmt', 0)) != 0:
                accounts['futures']['positions'][p['symbol']] = {
                    'amount': float(p['positionAmt']),
                    'entryPrice': float(p['entryPrice']),
                    'unrealizedProfit': float(p['unRealizedProfit']),
                }
    
    return accounts

def transfer(asset, amount, from_account, to_account):
    """账户间转账"""
    type_map = {
        'spot': 'MAIN', 'margin_cross': 'CROSS', 
        'margin_isolated': 'ISOLATED', 'futures': 'USDT_FUTURE'
    }
    
    if from_account == 'futures' or to_account == 'futures':
        # 合约转账需要特殊处理
        return futures_transfer(asset, amount, from_account, to_account)
    
    # 现货/全仓/逐仓之间转账
    from_type = 1 if from_account == 'spot' else 2 if from_account == 'margin_cross' else 3
    to_type = 1 if to_account == 'spot' else 2 if to_account == 'margin_cross' else 3
    
    params = {"asset": asset, "amount": amount, "type": from_type}
    result = signed_api("/sapi/v1/asset/transfer", params, "POST")
    
    if 'error' in result:
        log(f"转账失败: {result['error']}")
        return False
    log(f"✅ 转账 {amount} {asset}: {from_account} → {to_account}")
    return True

def futures_transfer(asset, amount, from_account, to_account):
    """合约转账"""
    if from_account == 'spot' and to_account == 'futures':
        # 现货→合约
        params = {"asset": asset, "amount": amount, "type": 1}
    elif from_account == 'futures' and to_account == 'spot':
        # 合约→现货
        params = {"asset": asset, "amount": amount, "type": 2}
    else:
        return False
    
    result = signed_api("/sapi/v1/asset/transfer", params, "POST")
    if 'error' in result:
        log(f"合约转账失败: {result['error']}")
        return False
    log(f"✅ 合约转账 {amount} {asset}: {from_account} → {to_account}")
    return True

# ========== 资金调配策略 ==========
def calculate_total_assets(accounts):
    """计算总资产"""
    total = 0
    total += accounts['spot']['usdt']
    
    for coin, data in accounts['spot']['coins'].items():
        if coin != 'USDT':
            price = get_price(f"{coin}USDT")
            total += data['free'] * price
    
    total += accounts['margin_cross']['usdt']
    for coin, amount in accounts['margin_cross']['coins'].items():
        price = get_price(f"{coin}USDT")
        total += amount * price
    
    total += accounts['futures']['usdt']
    
    return total

def analyze_opportunities(accounts, total_assets):
    """分析各账户机会"""
    opportunities = []
    
    # 现货机会
    spot_value = accounts['spot']['usdt']
    spot_ratio = spot_value / total_assets if total_assets > 0 else 0
    opportunities.append(('spot', '现货', spot_ratio, 0.3))  # 现货稳定，权重0.3
    
    # 全仓机会 (有借贷成本)
    margin_value = accounts['margin_cross']['usdt']
    margin_ratio = margin_value / total_assets if total_assets > 0 else 0
    opportunities.append(('margin_cross', '全仓', margin_ratio, 0.2))
    
    # 合约机会 (高风险高收益)
    futures_value = accounts['futures']['usdt']
    futures_ratio = futures_value / total_assets if total_assets > 0 else 0
    
    # 检查合约是否有持仓
    has_futures_positions = len(accounts['futures']['positions']) > 0
    futures_score = 0.5 if has_futures_positions else 0.3
    opportunities.append(('futures', '合约', futures_ratio, futures_score))
    
    return opportunities

def rebalance_capital(accounts, total_assets):
    """再平衡资金"""
    decisions = []
    
    # 目标配置
    target_spot = 0.40      # 现货40%
    target_margin = 0.30    # 全仓30% (用于保证金)
    target_futures = 0.30   # 合约30% (高收益)
    
    current_spot = accounts['spot']['usdt']
    current_margin = accounts['margin_cross']['usdt']
    current_futures = accounts['futures']['usdt']
    
    # 计算偏差
    target_spot_val = total_assets * target_spot
    target_margin_val = total_assets * target_margin
    target_futures_val = total_assets * target_futures
    
    # 现货 → 合约 (如果合约资金不足)
    if current_futures < target_futures_val and current_spot > target_spot_val + 50:
        transfer_amount = min(current_spot - target_spot_val, 50)
        if transfer_amount > 10:
            if futures_transfer('USDT', transfer_amount, 'spot', 'futures'):
                decisions.append(f"调配 {transfer_amount:.2f} USDT → 合约")
    
    # 合约 → 现货 (如果合约资金过剩)
    elif current_futures > target_futures_val + 100:
        transfer_amount = (current_futures - target_futures_val) * 0.5
        if transfer_amount > 10:
            if futures_transfer('USDT', transfer_amount, 'futures', 'spot'):
                decisions.append(f"调配 {transfer_amount:.2f} USDT → 现货")
    
    # 全仓检查 (LINK抵押品)
    link_in_margin = accounts['margin_cross']['coins'].get('LINK', 0)
    if link_in_margin > 100:  # LINK太多在逐仓
        log(f"  全仓LINK: {link_in_margin:.2f} (建议减少)")
    
    return decisions

def execute_trades(accounts):
    """执行交易"""
    decisions = []
    coins = ['ETH', 'UNI', 'BOME', 'TURBO', 'PUMP', 'NEIRO', 'LINK', 'SOL', 'BNB']
    
    for coin in coins:
        rsi = get_rsi(f"{coin}USDT")
        momentum = get_momentum(f"{coin}USDT")
        
        # Oracle决策
        if rsi < 35 and momentum < -2: signal = 'BUY'
        elif rsi < 35: signal = 'ADD'
        elif rsi > 75: signal = 'SELL'
        elif rsi > 65: signal = 'REDUCE'
        else: signal = 'HOLD'
        
        # 现货持仓
        spot_amount = accounts['spot']['coins'].get(coin, {}).get('free', 0)
        spot_value = spot_amount * get_price(f"{coin}USDT")
        
        if signal == 'BUY' and accounts['spot']['usdt'] > 20:
            # 买入
            qty = accounts['spot']['usdt'] * 0.1 / get_price(f"{coin}USDT")
            if qty > get_min_qty(coin):
                params = {"symbol": f"{coin}USDT", "side": "BUY", "type": "MARKET", "quantity": qty}
                result = signed_api("/api/v3/order", params, "POST")
                if 'error' not in result:
                    decisions.append(f"买入 {coin} x {qty:.2f}")
        
        elif signal == 'SELL' and spot_amount > get_min_qty(coin):
            # 卖出
            qty = spot_amount * 0.5
            params = {"symbol": f"{coin}USDT", "side": "SELL", "type": "MARKET", "quantity": qty}
            result = signed_api("/api/v3/order", params, "POST")
            if 'error' not in result:
                decisions.append(f"卖出 {coin} x {qty:.2f}")
        
        log(f"  {coin}: {signal} (RSI:{rsi:.1f} 动量:{momentum:+.2f}%)")
    
    return decisions

def get_min_qty(symbol):
    min_qty = {'BOME': 10000, 'TURBO': 1000, 'PUMP': 100, 'NEIRO': 10000, 'LINK': 0.1}
    return min_qty.get(symbol, 1)

# ========== 主循环 ==========
def main():
    log("=" * 70)
    log("G28 资金调配编排器启动")
    log("=" * 70)
    
    state = load_state()
    
    while True:
        try:
            # 获取所有账户
            accounts = get_all_accounts()
            total_assets = calculate_total_assets(accounts)
            
            log(f"\n{'='*60}")
            log(f"⏰ {datetime.now().strftime('%H:%M:%S')} | 总资产: ${total_assets:.2f}")
            
            # 显示账户状态
            log(f"  📊 现货: ${accounts['spot']['usdt']:.2f}")
            log(f"  📈 全仓: ${accounts['margin_cross']['usdt']:.2f}")
            log(f"  📉 合约: ${accounts['futures']['usdt']:.2f}")
            
            # 分析机会
            opportunities = analyze_opportunities(accounts, total_assets)
            log(f"  🎯 机会分析:")
            for acc_id, acc_name, ratio, score in opportunities:
                log(f"     {acc_name}: 占比{ratio*100:.1f}% 评分{score:.2f}")
            
            # 资金再平衡
            rebalance_decisions = rebalance_capital(accounts, total_assets)
            for decision in rebalance_decisions:
                log(f"  🔄 {decision}")
            
            # 执行交易
            trade_decisions = execute_trades(accounts)
            for decision in trade_decisions:
                log(f"  📋 {decision}")
            
            save_state(state)
            time.sleep(60)
            
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
