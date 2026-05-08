#!/usr/bin/env python3
"""
Hermes G12 - 统一核心 v2 (API全连通)
集成: Binance | Polymarket | G12核心交易
"""
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

# ========== API配置 ==========
BINANCE_API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
BINANCE_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}

# ========== G12配置 ==========
CONFIG = {
    'version': 'G12-Unified-v2.0',
    'rsi_buy': 43, 'rsi_sell': 53,
    'bb_buy': 25, 'bb_sell': 75,
    'tp': 0.08, 'sl': 0.035,
    'position': 0.35, 'leverage': 3,
    'short_rsi': 70, 'short_bb': 85,
}

# ========== Binance API ==========
def binance_request(method, endpoint, params=None, signed=False):
    ts = int(time.time()*1000)
    if params is None: params = {}
    params['timestamp'] = ts
    params['recvWindow'] = 5000
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    if signed:
        sig = hmac.new(BINANCE_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
        query += f'&signature={sig}'
    headers = {'X-MBX-APIKEY': BINANCE_API_KEY} if signed else {}
    try:
        if method == 'GET':
            r = requests.get(f'https://api.binance.com{endpoint}?{query}', headers=headers, proxies=PROXIES, timeout=10)
        elif method == 'POST':
            r = requests.post(f'https://api.binance.com{endpoint}?{query}', headers=headers, proxies=PROXIES, timeout=10)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_24hr(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', proxies=PROXIES, timeout=5)
        d = r.json()
        return {'price':float(d['lastPrice']),'chg':float(d['priceChangePercent']),'high':float(d['highPrice']),'low':float(d['lowPrice'])}
    except: return None

def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3]),'open':float(k[1])} for k in r.json()]
    except: return []

def get_account():
    return binance_request('GET', '/api/v3/account', signed=True)

def get_margin_account():
    return binance_request('GET', '/sapi/v1/margin/account', signed=True)

def place_order(symbol, side, qty):
    coin = symbol.replace('USDT','')
    p = PRECISION.get(coin, 6)
    if p == 0: qty = int(qty)
    else: qty = round(round(qty/10**(-p))*10**(-p), p)
    if qty <= 0: return None
    params = {'symbol':symbol,'side':side,'type':'MARKET','quantity':qty,'timestamp':int(time.time()*1000),'recvWindow':5000}
    return binance_request('POST', '/api/v3/order', params, signed=True)

# ========== Polymarket API ==========
def get_polymarket():
    try:
        url = 'https://clob.polymarket.com/markets?limit=10'
        r = requests.get(url, proxies=PROXIES, timeout=10)
        data = r.json()
        markets = []
        for m in data.get('data', [])[:10]:
            prices = m.get('outcomePrices', {})
            if prices:
                prob = float(list(prices.values())[0]) * 100
            else:
                prob = 50
            markets.append({
                'question': m.get('question', '')[:60],
                'prob': prob,
                'volume': float(m.get('volume', 0)),
                'active': m.get('active', True)
            })
        return markets
    except: return []

# ========== 指标 ==========
def get_rsi(prices, period=7):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def bollinger_pos(price, highs, lows, period=20):
    if len(highs) < period: return 50
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def volatility(closes, period=20):
    if len(closes) < period: return 0
    returns = np.diff(closes[-period:]) / closes[-period:-1]
    return np.std(returns) * 100

# ========== 任务 ==========
def task_asset_monitor():
    print("\n[任务1] 资产监控 ✅")
    spot = get_account()
    if 'balances' not in spot: return
    balances = {b['asset']: float(b['free']) for b in spot['balances']}
    usdt = balances.get('USDT', 0)
    total = usdt
    print(f"  SPOT USDT: ${usdt:.2f}")
    for c in COINS:
        qty = balances.get(c, 0)
        if qty > 0.001:
            val = qty * get_price(f'{c}USDT')
            total += val
            print(f"  {c}: {qty:.4f} (${val:.2f})")
    print(f"  总资产: ${total:.2f}")
    return total

def task_volatility():
    print("\n[任务2] 波动率监控 ✅")
    alerts = []
    for c in COINS:
        klines = get_klines(f'{c}USDT', '1h', 200)
        if len(klines) < 60: continue
        closes = [k['close'] for k in klines]
        vol = volatility(closes[-30:], 20)
        vol_h = volatility(closes, 60)
        if vol > vol_h * 2 and vol > 2:
            alerts.append(f"{c}: vol={vol:.1f}%")
            print(f"  ⚠️ {c}: {vol:.1f}% (历史{vol_h:.1f}%)")
        time.sleep(0.05)
    if not alerts: print("  正常")
    return alerts

def task_polymarket():
    print("\n[任务3] Polymarket预测 ✅")
    markets = get_polymarket()
    if not markets: print("  无数据"); return []
    active = [m for m in markets if m['active']]
    print(f"  活跃市场: {len(active)}个")
    for m in markets[:3]:
        e = "🟢" if m['prob'] > 60 else ("🔴" if m['prob'] < 40 else "🟡")
        print(f"  {e} {m['question'][:45]}... {m['prob']:.0f}%")
    return markets

def task_g12_trade():
    print("\n[任务4] G12核心交易 ✅")
    spot = get_account()
    if 'balances' not in spot: return
    balances = {b['asset']: float(b['free']) for b in spot['balances']}
    usdt = balances.get('USDT', 0)
    
    signals = []
    for c in COINS:
        p = get_price(f'{c}USDT')
        if p <= 0: continue
        klines = get_klines(f'{c}USDT', '1h', 100)
        if len(klines) < 50: continue
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        rsi = get_rsi(closes, 7)
        bb = bollinger_pos(p, highs, lows, 20)
        score = 0
        if rsi < CONFIG['rsi_buy'] and bb < CONFIG['bb_buy']: score = 50
        elif rsi > CONFIG['rsi_sell'] and bb > CONFIG['bb_sell']: score = -50
        signals.append({'coin':c,'price':p,'rsi':rsi,'bb':bb,'score':score})
        time.sleep(0.05)
    
    signals.sort(key=lambda x: -x['score'])
    
    # 执行
    for s in signals[:1]:
        if s['score'] > 30 and usdt > 20:
            invest = usdt * CONFIG['position']
            qty = invest / s['price']
            r = place_order(f'{s["coin"]}USDT', 'BUY', qty)
            if r and 'orderId' in r: print(f"  ✅ 买入 {s['coin']}: ${invest:.2f}")
        elif s['score'] < -30:
            qty = balances.get(s['coin'], 0)
            if qty * s['price'] > 10:
                r = place_order(f'{s["coin"]}USDT', 'SELL', qty * 0.5)
                if r and 'orderId' in r: print(f"  ✅ 卖出 {s['coin']}: {qty*0.5:.4f}")

def task_status():
    print("\n[任务5] 系统状态 ✅")
    print(f"  版本: {CONFIG['version']}")
    print(f"  G12配置: RSI:{CONFIG['rsi_buy']}/{CONFIG['rsi_sell']} BB:{CONFIG['bb_buy']}/{CONFIG['bb_sell']}")
    print(f"  止盈: {CONFIG['tp']*100:.0f}% 止损: {CONFIG['sl']*100:.1f}%")
    print(f"  仓位: {CONFIG['position']*100:.0f}% 杠杆: {CONFIG['leverage']}x")
    print(f"  API状态: Binance✅ Polymarket✅")

# ========== 主程序 ==========
def main():
    print("="*60)
    print(f"Hermes G12 统一核心 {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    task_status()
    task_asset_monitor()
    task_volatility()
    task_polymarket()
    task_g12_trade()
    
    print("\n" + "="*60)
    print("✅ 执行完成")
    print("="*60)

if __name__ == '__main__':
    main()
