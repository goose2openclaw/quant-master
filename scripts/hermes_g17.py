#!/usr/bin/env python3
"""
G17 - 融合Lean EMA Cross + G16策略
Lean成分: EMA Cross双确认
G16成分: RSI/BB指标、全仓转移、杠杆增强
"""
import requests, numpy as np, time, json, hmac, hashlib
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# G17配置 - Lean EMA Cross + G16增强
CONFIG = {
    # Lean EMA Cross参数
    'ema_fast': 12,
    'ema_slow': 26,
    # G16参数
    'rsi_buy': 35, 'rsi_sell': 65,
    'bb_buy': 30, 'bb_sell': 70,
    # 交易参数
    'tp': 0.12, 'sl': 0.04,
    'position': 0.35, 'leverage': 5,
    'margin_leverage': 3,
}

def sign(params):
    params['recvWindow'] = 5000
    params['timestamp'] = int(time.time()*1000)
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + '&signature=' + sig

def api_get(url, params=None):
    try:
        params = params or {}
        r = requests.get(url + '?' + sign(params), headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return {}

def api_post(url, params):
    try:
        r = requests.post(url + '?' + sign(params), headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return {'code': -1, 'msg': '网络错误'}

def get_price(symbol):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
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

# ========== Lean EMA Cross指标 ==========
def calc_ema(prices, period):
    """计算EMA - 来自Lean的ExponentialMovingAverage"""
    if len(prices) < period:
        return None
    ema = prices[0]
    smoothing = 2.0 / (period + 1)
    for p in prices[1:]:
        ema = (p - ema) * smoothing + ema
    return ema

def get_ema_cross_signal(prices):
    """Lean EMA Cross信号 - 核心来自EmaCrossAlphaModel"""
    fast = calc_ema(prices, CONFIG['ema_fast'])
    slow = calc_ema(prices, CONFIG['ema_slow'])
    
    if fast is None or slow is None:
        return 'HOLD', 0
    
    # 交叉判断
    prev_fast = calc_ema(prices[:-1], CONFIG['ema_fast'])
    prev_slow = calc_ema(prices[:-1], CONFIG['ema_slow'])
    
    if prev_fast is None or prev_slow is None:
        return 'HOLD', 0
    
    # 金叉 (fast上穿slow) → 买入
    if prev_fast <= prev_slow and fast > slow:
        return 'BUY', (fast - slow) / slow * 100
    
    # 死叉 (fast下穿slow) → 卖出
    elif prev_fast >= prev_slow and fast < slow:
        return 'SELL', (slow - fast) / slow * 100
    
    # 持续状态
    if fast > slow:
        return 'UP', (fast - slow) / slow * 100
    else:
        return 'DOWN', (slow - fast) / slow * 100

# ========== G16指标 ==========
def calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_bb_pos(prices, period=20):
    if len(prices) < period:
        return 50
    recent = prices[-period:]
    sma = np.mean(recent)
    std = np.std(recent)
    if std == 0:
        return 50
    return (prices[-1] - sma) / (2 * std) * 100 + 50

# ========== G17综合分析 ==========
def analyze_coin(coin):
    """融合Lean EMA Cross + G16 RSI/BB"""
    prices = get_klines(f'{coin}USDT')
    if len(prices) < 50:
        return None
    
    # Lean信号
    ema_signal, ema_strength = get_ema_cross_signal(prices)
    
    # G16信号
    rsi = calc_rsi(prices)
    bb = calc_bb_pos(prices)
    
    # 综合评分 (Lean占40%, G16占60%)
    score = 0
    
    # Lean EMA Cross贡献
    if ema_signal == 'BUY':
        score += 40
    elif ema_signal == 'SELL':
        score -= 40
    
    # G16 RSI贡献
    if rsi < CONFIG['rsi_buy']:
        score += 30
    elif rsi < 45:
        score += 15
    elif rsi > CONFIG['rsi_sell']:
        score -= 30
    elif rsi > 55:
        score -= 15
    
    # G16 BB贡献
    if bb < CONFIG['bb_buy']:
        score += 15
    elif bb > CONFIG['bb_sell']:
        score -= 15
    
    # 信号确定
    if score >= 50:
        signal = 'STRONG_BUY'
    elif score >= 25:
        signal = 'BUY'
    elif score <= -50:
        signal = 'STRONG_SELL'
    elif score <= -25:
        signal = 'SELL'
    else:
        signal = 'NEUTRAL'
    
    return {
        'coin': coin,
        'ema_signal': ema_signal,
        'ema_strength': ema_strength,
        'rsi': rsi,
        'bb': bb,
        'score': score,
        'signal': signal,
        'price': prices[-1]
    }

# ========== 账户查询 ==========
def get_spot_account():
    data = api_get('https://api.binance.com/api/v3/account')
    if 'error' in data:
        return {}
    result = {}
    for b in data.get('balances', []):
        free = float(b.get('free', 0))
        if free > 0.00001:
            result[b['asset']] = {'qty': free, 'price': get_price(b['asset'] + 'USDT')}
    return result

def get_cross_margin_account():
    data = api_get('https://api.binance.com/sapi/v1/margin/account')
    if 'error' in data:
        return {}
    result = {}
    for b in data.get('userAssets', []):
        net = float(b.get('net', 0))
        if net > 0.00001:
            result[b['asset']] = {'qty': net, 'price': get_price(b['asset'] + 'USDT')}
    return result

def spot_to_margin(asset, qty):
    url = 'https://api.binance.com/sapi/v1/margin/transfer'
    params = {
        'asset': asset, 'type': 1,
        'amount': f'{qty:.8f}'.rstrip('0').rstrip('.')
    }
    return api_post(url, params)

def margin_to_spot(asset, qty):
    url = 'https://api.binance.com/sapi/v1/margin/transfer'
    params = {
        'asset': asset, 'type': 2,
        'amount': f'{qty:.8f}'.rstrip('0').rstrip('.')
    }
    return api_post(url, params)

# ========== G17调仓决策 ==========
def make_decisions(spot, margin, analyses):
    decisions = []
    for a in analyses:
        if a is None:
            continue
        coin = a['coin']
        score = a['score']
        signal = a['signal']
        
        spot_qty = spot.get(coin, {}).get('qty', 0)
        margin_qty = margin.get(coin, {}).get('qty', 0)
        
        # 强势信号: 现货→全仓
        if signal in ['STRONG_BUY', 'BUY'] and spot_qty > 0.001:
            pct = 0.35 if signal == 'STRONG_BUY' else 0.2
            qty = spot_qty * pct
            if qty > 0.0001:
                decisions.append({
                    'type': 'SPOT_TO_MARGIN', 'coin': coin, 'qty': qty,
                    'reason': f"{signal} EMA:{a['ema_signal']} RSI:{a['rsi']:.0f} BB:{a['bb']:.0f} Score:{score}"
                })
        
        # 弱势信号: 全仓→现货
        elif signal in ['STRONG_SELL', 'SELL'] and margin_qty > 0.0001:
            decisions.append({
                'type': 'MARGIN_TO_SPOT', 'coin': coin, 'qty': margin_qty,
                'reason': f"{signal} EMA:{a['ema_signal']} RSI:{a['rsi']:.0f} BB:{a['bb']:.0f} Score:{score}"
            })
    
    return decisions

def execute_transfers(decisions):
    for d in decisions:
        if d['type'] == 'SPOT_TO_MARGIN':
            result = spot_to_margin(d['coin'], d['qty'])
            if 'tranId' in result:
                print(f"  ✅ {d['coin']}: 现货→全仓 {d['qty']:.6f}")
            else:
                print(f"  ❌ {d['coin']}: {result.get('msg', result)}")
        elif d['type'] == 'MARGIN_TO_SPOT':
            result = margin_to_spot(d['coin'], d['qty'])
            if 'tranId' in result:
                print(f"  ✅ {d['coin']}: 全仓→现货 {d['qty']:.6f}")
            else:
                print(f"  ❌ {d['coin']}: {result.get('msg', result)}")

# ========== 主程序 ==========
def main():
    print("=" * 70)
    print("G17 v1.0 - Lean EMA Cross + G16 融合策略")
    print("=" * 70)
    
    # 账户
    spot = get_spot_account()
    margin = get_cross_margin_account()
    spot_total = sum(v['qty'] * v['price'] for v in spot.values())
    margin_total = sum(v['qty'] * v['price'] for v in margin.values())
    
    print(f"\n📊 账户概览")
    print(f"  现货: ${spot_total:.2f}")
    print(f"  全仓: ${margin_total:.2f}")
    
    # 分析
    print(f"\n🔍 G17信号分析 (Lean EMA + G16 RSI/BB)")
    analyses = []
    for coin in COINS:
        a = analyze_coin(coin)
        if a:
            analyses.append(a)
            emoji = '🟢' if 'BUY' in a['signal'] else '🔴' if 'SELL' in a['signal'] else '🟡'
            print(f"  {emoji} {coin:6} EMA:{a['ema_signal']:6} RSI:{a['rsi']:5.1f} BB:{a['bb']:5.1f}% Score:{a['score']:4} → {a['signal']}")
    
    # 决策
    print(f"\n⚖️ 调仓决策")
    decisions = make_decisions(spot, margin, analyses)
    if not decisions:
        print("  ⏸️ 无需调仓")
    else:
        for d in decisions:
            direction = '📈→' if d['type'] == 'SPOT_TO_MARGIN' else '📉←'
            print(f"  {direction} {d['coin']}: {d['reason']}")
    
    # 执行
    if decisions:
        print("\n🚀 执行转移")
        execute_transfers(decisions)

if __name__ == '__main__':
    main()
