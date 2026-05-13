#!/usr/bin/env python3
"""
G16 v2.0 智能调仓系统
- 现货与全仓综合考虑
- 强势信号: 现货 → 全仓加杠杆
- 弱势信号: 全仓 → 现货
"""
import requests, numpy as np, time, json, hmac, hashlib
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# G16 v2.0 正式配置
CONFIG = {
    'rsi_buy': 35, 'rsi_sell': 65,
    'bb_buy': 30, 'bb_sell': 70,
    'tp': 0.12, 'sl': 0.04,
    'position': 0.35, 'leverage': 5,
    'margin_leverage': 3,  # 全仓杠杆倍数
    'transfer_threshold': 15,  # 信号强度阈值
}

# ========== API基础函数 ==========
def sign(params):
    params['recvWindow'] = 5000
    params['timestamp'] = int(time.time()*1000)
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + '&signature=' + sig

def api_get(url, params=None):
    try:
        params = params or {}
        r = requests.get(url + '?' + sign(params),
                        headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return {}

def api_post(url, params):
    try:
        r = requests.post(url + '?' + sign(params),
                        headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return {'code': -1, 'msg': '网络错误'}

def get_price(symbol):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', 
                       proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(sym, limit=200):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [float(k[4]) for k in r.json()]
    except: return []

# ========== 账户查询 ==========
def get_spot_account():
    """现货账户"""
    data = api_get('https://api.binance.com/api/v3/account')
    if 'error' in data: return {}
    result = {}
    for b in data.get('balances', []):
        free = float(b.get('free', 0))
        if free > 0.00001:
            price = get_price(b['asset'] + 'USDT')
            result[b['asset']] = {'qty': free, 'price': price, 'value': free * price}
    return result

def get_cross_margin_account():
    """全仓杠杆账户"""
    data = api_get('https://api.binance.com/sapi/v1/margin/account')
    if 'error' in data: return {}
    result = {}
    for b in data.get('userAssets', []):
        net = float(b.get('net', 0))
        if net > 0.00001:
            price = get_price(b['asset'] + 'USDT')
            result[b['asset']] = {'qty': net, 'price': price, 'value': net * price}
    return result

def get_futures_account():
    """合约账户"""
    data = api_get('https://fapi.binance.com/fapi/v2/account')
    if 'error' in data: return {}
    return {
        'total': float(data.get('totalMarginBalance', 0)),
        'available': float(data.get('availableBalance', 0)),
    }

def get_futures_positions():
    """合约持仓"""
    data = api_get('https://fapi.binance.com/fapi/v2/positionRisk')
    if 'error' in data: return []
    return [p for p in data if float(p.get('positionAmt', 0)) != 0]

# ========== 转移功能 ==========
def spot_to_margin(asset, qty):
    """现货转入全仓"""
    url = 'https://api.binance.com/sapi/v1/margin/transfer'
    params = {
        'asset': asset,
        'type': 1,  # 现货到全仓
        'amount': f'{qty:.8f}'.rstrip('0').rstrip('.')  # 去除尾部0
    }
    result = api_post(url, params)
    return result

def margin_to_spot(asset, qty):
    """全仓转入现货"""
    url = 'https://api.binance.com/sapi/v1/margin/transfer'
    params = {
        'asset': asset,
        'type': 2,  # 全仓到现货
        'amount': f'{qty:.8f}'.rstrip('0').rstrip('.')
    }
    result = api_post(url, params)
    return result

# ========== 技术指标 ==========
def calc_rsi(prices):
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-7:])
    avg_loss = np.mean(loss[-7:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 50

def calc_bb(closes):
    std = np.std(closes[-20:])
    mean = np.mean(closes[-20:])
    upper, lower = mean + 2*std, mean - 2*std
    pos = (closes[-1] - lower) / (upper - lower) * 100 if upper > lower else 50
    ratio = std / mean * 100 if mean > 0 else 0
    return pos, ratio

def calc_momentum(closes):
    if len(closes) < 24: return 0
    return (closes[-1] - closes[-24]) / closes[-24] * 100

# ========== 信号分析 ==========
def analyze_coin(coin):
    """全面分析币种"""
    klines = get_klines(f'{coin}USDT', 200)
    if len(klines) < 50: return None
    
    rsi = calc_rsi(klines)
    bb_pos, ratio = calc_bb(klines)
    mom = calc_momentum(klines)
    
    # 信号评分 (0-100)
    score = 0
    
    # RSI评分 (超卖=高分数买入信号)
    if rsi < 25: score += 40
    elif rsi < 35: score += 30
    elif rsi < 45: score += 15
    elif rsi > 75: score -= 40
    elif rsi > 65: score -= 30
    elif rsi > 55: score -= 15
    
    # 布林带评分
    if bb_pos < 20: score += 20  # 超卖
    elif bb_pos > 80: score -= 20  # 超买
    
    # 动量评分
    if mom > 10: score += 20
    elif mom > 5: score += 10
    elif mom < -10: score -= 20
    elif mom < -5: score -= 10
    
    # 波动率
    if ratio < 0.3: score += 10  # 低波动可能是盘整
    elif ratio > 0.8: score -= 10  # 高波动
    
    return {
        'coin': coin,
        'rsi': rsi,
        'bb': bb_pos,
        'mom': mom,
        'ratio': ratio,
        'score': score,
        'signal': 'STRONG_BUY' if score >= 50 else 'BUY' if score >= 20 else
                  'STRONG_SELL' if score <= -50 else 'SELL' if score <= -20 else 'NEUTRAL'
    }

# ========== 调仓决策 ==========
def make_transfer_decisions(spot_assets, margin_assets, analyses):
    """生成转移决策"""
    decisions = []
    
    for analysis in analyses:
        coin = analysis['coin']
        score = analysis['score']
        signal = analysis['signal']
        
        spot_qty = spot_assets.get(coin, {}).get('qty', 0)
        margin_qty = margin_assets.get(coin, {}).get('qty', 0)
        
        # 强势买入信号: 从现货转入全仓
        if signal in ['STRONG_BUY', 'BUY'] and spot_qty > 0.001:
            transfer_pct = 0.3 if signal == 'STRONG_BUY' else 0.2
            transfer_qty = spot_qty * transfer_pct
            if transfer_qty > 0.0001:
                decisions.append({
                    'type': 'SPOT_TO_MARGIN',
                    'coin': coin,
                    'qty': transfer_qty,
                    'reason': f'{signal} RSI:{analysis["rsi"]:.1f} MOM:{analysis["mom"]:.1f}%'
                })
        
        # 弱势卖出信号: 从全仓转回现货
        elif signal in ['STRONG_SELL', 'SELL'] and margin_qty > 0.0001:
            decisions.append({
                'type': 'MARGIN_TO_SPOT',
                'coin': coin,
                'qty': margin_qty,
                'reason': f'{signal} RSI:{analysis["rsi"]:.1f} MOM:{analysis["mom"]:.1f}%'
            })
    
    return decisions

# ========== 执行转移 ==========
def execute_transfers(decisions):
    """执行转移"""
    results = []
    for d in decisions:
        if d['type'] == 'SPOT_TO_MARGIN':
            result = spot_to_margin(d['coin'], d['qty'])
            # 检查是否有tranId (成功)或code (失败)
            if 'tranId' in result:
                print(f"  ✅ {d['coin']}: 现货→全仓 {d['qty']:.6f}")
                print(f"      交易ID: {result['tranId']}")
            else:
                print(f"  ❌ {d['coin']}: 现货→全仓 {d['qty']:.6f}")
                print(f"      错误: {result.get('msg', result)}")
            results.append({'decision': d, 'result': result})
        elif d['type'] == 'MARGIN_TO_SPOT':
            result = margin_to_spot(d['coin'], d['qty'])
            if 'tranId' in result:
                print(f"  ✅ {d['coin']}: 全仓→现货 {d['qty']:.6f}")
                print(f"      交易ID: {result['tranId']}")
            else:
                print(f"  ❌ {d['coin']}: 全仓→现货 {d['qty']:.6f}")
                print(f"      错误: {result.get('msg', result)}")
            results.append({'decision': d, 'result': result})
    return results

# ========== 主程序 ==========
def main():
    print("=" * 70)
    print("G16 v2.0 智能调仓系统")
    print("现货 ↔ 全仓 自主转移")
    print("=" * 70)
    
    # 1. 获取账户
    print("\n📊 账户概览")
    spot = get_spot_account()
    margin = get_cross_margin_account()
    futures = get_futures_account()
    
    spot_total = sum(v['value'] for v in spot.values())
    margin_total = sum(v['value'] for v in margin.values())
    
    print(f"  现货: ${spot_total:.2f}")
    print(f"  全仓: ${margin_total:.2f}")
    print(f"  合约: ${futures.get('total', 0):.2f}")
    
    # 2. 分析所有币种
    print("\n🔍 信号分析")
    analyses = []
    for c in COINS:
        a = analyze_coin(c)
        if a:
            analyses.append(a)
            emoji = '🟢' if a['signal'] in ['STRONG_BUY','BUY'] else '🔴' if a['signal'] in ['STRONG_SELL','SELL'] else '🟡'
            print(f"  {emoji} {c:6} RSI:{a['rsi']:5.1f} MOM:{a['mom']:>+6.1f}% BB:{a['bb']:5.0f}% 评分:{a['score']:>+4} {a['signal']}")
    
    # 3. 生成调仓决策
    print("\n⚖️ 调仓决策")
    decisions = make_transfer_decisions(spot, margin, analyses)
    
    if not decisions:
        print("  ⏸️ 无需调仓")
    else:
        for d in decisions:
            direction = '📈→' if d['type'] == 'SPOT_TO_MARGIN' else '📉←'
            print(f"  {direction} {d['coin']}: {d['type'].replace('_','→')} {d['qty']:.6f}")
            print(f"      原因: {d['reason']}")
    
    # 4. 执行转移
    if decisions:
        print("\n🚀 执行转移")
        execute_transfers(decisions)
    
    # 5. 合约信号
    print("\n📈 合约信号")
    fut_positions = get_futures_positions()
    if fut_positions:
        for p in fut_positions:
            print(f"  {p['symbol']}: {p['positionAmt']}")
    else:
        print("  ⏸️ 无合约持仓")
    
    return decisions

if __name__ == '__main__':
    main()
