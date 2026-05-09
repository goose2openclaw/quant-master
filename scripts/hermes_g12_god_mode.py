#!/usr/bin/env python3
"""
G12 上帝视角 v2.0
🌟 主动全域扫码 → 科学评估 → 自主决策 → 自动实施
全账户/全币种/全市场 统一监控
"""
import requests, time, json, numpy as np, hmac, hashlib
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
BINANCE_API = "https://api.binance.com"
API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"

LOG_FILE = '/tmp/g12_god_mode.json'
STATE_FILE = '/tmp/g12_god_state.json'

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

def get_price(symbol):
    try:
        r = requests.get(f'{BINANCE_API}/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(sym, limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'{BINANCE_API}/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [float(k[4]) for k in r.json()]
    except: return []

def get_spot_account():
    try:
        params = {'timestamp': int(time.time()*1000), 'recvWindow': 5000}
        query, sig = sign_params(params)
        r = requests.get(f'{BINANCE_API}/api/v3/account?{query}&signature={sig}',
                        headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def get_futures_account():
    try:
        params = {'timestamp': int(time.time()*1000), 'recvWindow': 5000}
        query, sig = sign_params(params)
        r = requests.get(f'https://fapi.binance.com/fapi/v2/account?{query}&signature={sig}',
                        headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        if r.status_code == 200:
            return r.json()
    except: pass
    return None

def place_order(symbol, side, qty):
    try:
        params = {'symbol': symbol, 'side': side, 'type': 'MARKET', 'quantity': qty}
        query, sig = sign_params(params)
        r = requests.post(f'{BINANCE_API}/api/v3/order?{query}&signature={sig}',
                         headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e:
        log(f"下单失败: {e}")
        return None

def round_qty(qty, symbol):
    step_sizes = {'SOLUSDT': 0.001, 'BTCUSDT': 0.00001, 'ETHUSDT': 0.0001,
                  'XRPUSDT': 0.01, 'ADAUSDT': 0.01, 'DOGEUSDT': 1, 'LINKUSDT': 0.001}
    step = step_sizes.get(symbol, 0.001)
    decimals = len(str(step).split('.')[-1])
    qty = int(float(qty) / step) * step
    return round(qty, decimals)

def scan_all_coins():
    """🌟 全域扫描: 扫描所有持仓币种"""
    coins_data = []
    acc = get_spot_account()
    if acc and 'balances' in acc:
        for b in acc['balances']:
            free = float(b.get('free', 0))
            if free > 0.0001 and b['asset'] != 'USDT':
                price = get_price(b['asset'] + 'USDT')
                val = free * price
                if val > 0.5:  # 只扫描有价值持仓
                    coins_data.append({'asset': b['asset'], 'qty': free, 'price': price, 'val': val})
    return coins_data

def analyze_coin_full(coin, qty, price):
    """🔬 科学评估: 多维度分析"""
    klines = get_klines(f'{coin}USDT', 100)
    if len(klines) < 20:
        return None
    
    # 1. 动能指标
    chg_1h = (klines[-1] - klines[-2]) / klines[-2] * 100 if len(klines) >= 2 else 0
    chg_24h = (klines[-1] - klines[-25]) / klines[-25] * 100 if len(klines) >= 25 else 0
    chg_7d = (klines[-1] - klines[-169]) / klines[-169] * 100 if len(klines) >= 169 else 0
    
    # 2. RSI
    deltas = np.diff(klines[-15:])
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-7:])
    avg_loss = np.mean(loss[-7:])
    rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss != 0 else 50
    
    # 3. 布林带
    bb_now = np.std(klines[-20:]) / np.mean(klines[-20:]) * 100
    bb_hist = np.std(klines) / np.mean(klines) * 100
    bb_ratio = bb_now / bb_hist if bb_hist > 0 else 1
    
    # 4. 波动率
    vol_7d = np.std(np.diff(klines[-169:]) / klines[-169:-1]) * 100 if len(klines) >= 169 else 0
    
    # 综合评分 (0-100)
    momentum_score = (50 - rsi) / 50 * 40 + abs(chg_24h) * 2 if rsi < 50 else (rsi - 50) / 50 * 40 + abs(chg_24h) * 2
    volatility_score = (1 - min(bb_ratio, 1)) * 30 if bb_ratio < 1 else 0
    trend_score = (50 - rsi) / 50 * 30 if rsi < 50 else 0
    
    total_score = momentum_score + volatility_score + trend_score
    
    return {
        'coin': coin,
        'qty': qty,
        'price': price,
        'val': qty * price,
        'rsi': rsi,
        'chg_24h': chg_24h,
        'bb_ratio': bb_ratio,
        'vol_7d': vol_7d,
        'score': total_score,
        'signal': 'STRONG_BUY' if rsi < 30 else 'BUY' if rsi < 43 else 'HOLD' if rsi < 57 else 'SELL' if rsi > 70 else 'STRONG_SELL'
    }

def evaluate_decision(analysis):
    """📊 评估决策: 计算预期收益和风险"""
    if not analysis:
        return None
    
    val = analysis['val']
    rsi = analysis['rsi']
    bb_ratio = analysis['bb_ratio']
    
    # 变现评估
    slippage = val * 0.001
    fee = val * 0.001
    net_proceeds = val - slippage - fee
    
    # 持有潜力
    if rsi < 35:
        potential_gain = val * 0.1  # 低RSI可能有10%反弹
    elif rsi > 65:
        potential_gain = -val * 0.05  # 高RSI可能下跌
    else:
        potential_gain = val * 0.02
    
    # 风险评估
    if bb_ratio < 0.3:
        risk = 'HIGH'  # 低波动率可能突破
    elif rsi > 70:
        risk = 'HIGH'
    else:
        risk = 'MEDIUM'
    
    return {
        'net_proceeds': net_proceeds,
        'potential_gain': potential_gain,
        'risk': risk,
        'recommend_convert': potential_gain < net_proceeds * 0.05,  # 5%阈值
        'reason': f"RSI:{rsi:.0f} BB:{bb_ratio:.2f} 风险:{risk}"
    }

def simulate_trade(coin, side, qty, price):
    """🎮 仿真测试"""
    slippage = qty * price * 0.001
    fee = qty * price * 0.001
    gross_pnl = qty * price * 0.02  # 假设2%波动
    net_pnl = gross_pnl - slippage - fee
    return {'slippage': slippage, 'fee': fee, 'net_pnl': net_pnl, 'success': net_pnl > 0}

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except: return {'iter': 0, 'decisions': [], 'executions': []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def main():
    log("="*60)
    log("🌟 G12 上帝视角 v2.0")
    log("   主动全域扫码 → 科学评估 → 自主决策 → 自动实施")
    log("="*60)
    
    state = load_state()
    state['iter'] += 1
    state['last_run'] = datetime.now().isoformat()
    
    # ========== 1. 🌟 主动全域扫码 ==========
    log("\n🌟 【全域扫描】")
    coins = scan_all_coins()
    total_spot = sum(c['val'] for c in coins)
    usdt_balance = next((c['val'] for c in coins if c['asset'] == 'USDT'), 0)
    
    log(f"  现货总资产: ${total_spot:.2f}")
    log(f"  USDT现金: ${usdt_balance:.2f}")
    
    # 合约账户
    futures = get_futures_account()
    total_futures = 0
    if futures:
        total_futures = float(futures.get('totalMarginBalance', 0))
        log(f"  合约总资产: ${total_futures:.2f}")
    else:
        log("  合约总资产: ❌ 未连接")
    
    # ========== 2. 🔬 科学评估 ==========
    log("\n🔬 【科学评估】")
    analyses = []
    for c in coins:
        if c['asset'] != 'USDT':
            analysis = analyze_coin_full(c['asset'], c['qty'], c['price'])
            if analysis:
                analyses.append(analysis)
    
    # 按评分排序
    analyses.sort(key=lambda x: -x['score'])
    
    log("  币种评分排名:")
    for i, a in enumerate(analyses[:5], 1):
        emoji = "🟢" if a['signal'] in ['STRONG_BUY','BUY'] else "🔴" if a['signal'] in ['SELL','STRONG_SELL'] else "🟡"
        log(f"    {i}. {emoji} {a['coin']}: {a['signal']} RSI:{a['rsi']:.0f} 评分:{a['score']:.1f} ${a['val']:.2f}")
    
    # ========== 3. 📊 决策评估 ==========
    log("\n📊 【决策评估】")
    decisions = []
    for a in analyses:
        eval_result = evaluate_decision(a)
        if eval_result:
            decisions.append({**a, **eval_result})
    
    # 变现建议
    convert_candidates = [d for d in decisions if d['recommend_convert'] and d['val'] > 10]
    convert_candidates.sort(key=lambda x: -x['score'])
    
    if convert_candidates:
        best = convert_candidates[0]
        log(f"  建议变现: {best['coin']} (${best['val']:.2f})")
        log(f"    原因: {best['reason']}")
        log(f"    净变现: ${best['net_proceeds']:.2f}")
        log(f"    持有潜力: ${best['potential_gain']:.2f}")
    else:
        log("  无需变现,保持观望")
    
    # ========== 4. 🤖 自主决策 ==========
    log("\n🤖 【自主决策】")
    
    actions = []
    
    # 决策1: USDT不足,变现弱势币
    if usdt_balance < 20 and convert_candidates:
        best = convert_candidates[0]
        actions.append({
            'type': 'CONVERT',
            'coin': best['coin'],
            'qty': best['qty'] * 0.5,
            'reason': f"USDT不足(${usdt_balance:.2f}),变现{best['coin']}",
            'priority': 1
        })
    
    # 决策2: 合约空闲,有资金
    if total_futures < 10 and usdt_balance > 50:
        actions.append({
            'type': 'TRANSFER',
            'amount': usdt_balance * 0.8,
            'reason': "合约空闲,转入资金",
            'priority': 2
        })
    
    # 决策3: 低RSI强势币加仓机会
    low_rsi = [a for a in analyses if a['rsi'] < 40 and a['val'] > 20]
    if low_rsi and usdt_balance > 30:
        best = low_rsi[0]
        actions.append({
            'type': 'ADD_POSITION',
            'coin': best['coin'],
            'amount': usdt_balance * 0.3,
            'reason': f"{best['coin']}低RSI({best['rsi']:.0f}),加仓",
            'priority': 3
        })
    
    actions.sort(key=lambda x: x['priority'])
    
    # ========== 5. ⚡ 自动实施 ==========
    log("\n⚡ 【自动实施】")
    executed = []
    
    for action in actions[:2]:  # 最多执行2个
        log(f"  执行: {action['type']}")
        log(f"    原因: {action['reason']}")
        
        if action['type'] == 'CONVERT':
            coin = action['coin']
            qty = round_qty(action['qty'], f'{coin}USDT')
            if qty > 0:
                # 仿真
                sim = simulate_trade(coin, 'SELL', qty, get_price(f'{coin}USDT'))
                log(f"    仿真: 卖出 {qty:.4f} {coin}")
                log(f"    费用: ${sim['fee']:.2f} 滑点: ${sim['slippage']:.2f}")
                
                # 执行
                result = place_order(f'{coin}USDT', 'SELL', qty)
                if result and 'orderId' in result:
                    log(f"    ✅ 成功! OrderId: {result['orderId']}")
                    executed.append({'action': action, 'result': 'success'})
                    state.setdefault('executions', []).append({
                        'time': datetime.now().isoformat(),
                        'type': 'CONVERT',
                        'coin': coin,
                        'qty': qty
                    })
                else:
                    log(f"    ❌ 失败")
                    executed.append({'action': action, 'result': 'failed'})
        
        elif action['type'] == 'ADD_POSITION':
            log(f"    ⚠️ 需要先变现获得USDT")
    
    if not actions:
        log("  🟡 暂无最佳行动,保持观望")
    
    # ========== 6. 保存状态 ==========
    state['decisions'] = actions[-10:]
    save_state(state)
    
    with open(LOG_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    log(f"\n迭代 #{state['iter']} 完成 | 执行: {len(executed)}个")
    log("="*60)

if __name__ == '__main__':
    main()
