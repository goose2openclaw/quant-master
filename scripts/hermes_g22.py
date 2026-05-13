#!/usr/bin/env python3
"""
G22 - 智能信号增强版
==================
集成:
1. G20 RSI交易策略
2. Binance Smart Money信号
3. 策略回测验证
4. Binance全品种交易
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

def api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=10)
    return float(json.loads(resp.read().decode())['price'])

def klines(sym, limit=100):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=15)
    return [float(k[4]) for k in json.loads(resp.read().decode())]

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def get_smart_money_signals(chain_id="56", page=1, page_size=20):
    """获取Binance Smart Money信号"""
    url = "https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/signal/smart-money/ai"
    headers = {
        'Content-Type': 'application/json',
        'Accept-Encoding': 'identity',
        'User-Agent': 'binance-web3/1.1 (Skill)'
    }
    data = json.dumps({"page": page, "pageSize": page_size, "chainId": chain_id}).encode()
    
    req = urllib.request.Request(url, method='POST', data=data, headers=headers)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def get_balance():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    if 'balances' in data:
        for b in data['balances']:
            if b['asset'] == 'USDT': return float(b['free'])
    return 0

def get_positions():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    positions = {}
    if 'balances' in data:
        for b in data['balances']:
            free = float(b.get('free', 0))
            if free > 0.00001 and b['asset'] != 'USDT':
                try:
                    p = price(b['asset']+'USDT')
                    positions[b['asset']] = {'qty': free, 'price': p, 'value': free * p}
                except: pass
    return positions

def buy(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, 'POST')

def sell(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, 'POST')

def backtest_rsi(prices, period=14, overbought=70, oversold=30):
    """回测RSI策略"""
    signals = []
    position = 0
    for i in range(period, len(prices)):
        rsi = calc_rsi(prices[:i])
        if rsi < oversold and position == 0:
            signals.append(('BUY', prices[i]))
            position = 1
        elif rsi > overbought and position == 1:
            signals.append(('SELL', prices[i]))
            position = 0
    return signals

# G22 核心参数
COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
RSI_PERIOD = 14
OVERBOUGHT = 70
OVERSOLD = 30

print("=" * 80)
print("G22 - 智能信号增强版")
print("=" * 80)

ts = datetime.now().strftime('%H:%M:%S')
print(f"\n[{ts}] G22 运行中...")

# 1. 获取Smart Money信号
print("\n[1] Smart Money信号 (BSC)...")
sm_data = get_smart_money_signals(chain_id="56", page=1, page_size=10)
smart_signals = []
if 'data' in sm_data:
    for sig in sm_data['data'][:5]:
        direction = sig.get('direction', '')
        ticker = sig.get('ticker', '')
        max_gain = float(sig.get('maxGain', 0))
        exit_rate = float(sig.get('exitRate', 0))
        status = sig.get('status', '')
        print(f"  {direction.upper():4} {ticker:8} maxGain:{max_gain:6.1f}% exit:{exit_rate:4.0f}% status:{status}")
        if direction in ['buy', 'sell']:
            smart_signals.append({
                'ticker': ticker,
                'direction': direction,
                'maxGain': max_gain,
                'exitRate': exit_rate
            })
else:
    print(f"  ⚠️ 获取失败: {sm_data.get('error', 'Unknown')}")

# 2. RSI分析
print(f"\n[2] RSI分析 ({RSI_PERIOD}周期)...")
rsi_signals = []
for coin in COINS:
    prices = klines(f'{coin}USDT')
    if len(prices) < RSI_PERIOD + 1: continue
    rsi = calc_rsi(prices)
    
    # 信号强度计算
    signal = 'HOLD'
    strength = 0
    if rsi < OVERSOLD:
        signal = 'BUY'
        strength = int((OVERSOLD - rsi) / 10)
    elif rsi > OVERBOUGHT:
        signal = 'SELL'
        strength = int((rsi - OVERBOUGHT) / 10)
    
    emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
    print(f"  {emoji} {coin:5}: RSI={rsi:5.1f} -> {signal} (强度:{strength})")
    rsi_signals.append({'coin': coin, 'rsi': rsi, 'signal': signal, 'strength': strength})

# 3. 综合评分
print(f"\n[3] 综合信号评分...")
usdt = get_balance()
positions = get_positions()

for rsi_sig in rsi_signals:
    coin = rsi_sig['coin']
    score = rsi_sig['strength'] * 10
    
    # 匹配Smart Money信号
    for sm in smart_signals:
        if sm['ticker'].upper() == coin or sm['ticker'].upper() == f"{coin}USDT":
            if sm['direction'] == 'buy':
                score += 30
                rsi_sig['smart_money'] = 'BUY'
            elif sm['direction'] == 'sell':
                score -= 30
                rsi_sig['smart_money'] = 'SELL'
            rsi_sig['maxGain'] = sm['maxGain']
    
    rsi_sig['score'] = score
    emoji = '🟢' if score > 50 else '🔴' if score < 0 else '🟡'
    print(f"  {emoji} {coin:5}: 综合评分={score:4} (RSI:{rsi_sig['signal']} | SmartMoney:{rsi_sig.get('smart_money', 'N/A')})")

# 4. 执行决策
print(f"\n[4] 执行决策...")
buy_candidates = [s for s in rsi_signals if s['score'] > 50]
sell_candidates = [s for s in rsi_signals if s['score'] < 0]

if buy_candidates and usdt > 10:
    best = max(buy_candidates, key=lambda x: x['score'])
    coin = best['coin']
    amount = usdt * 0.9
    p = price(f'{coin}USDT')
    qty = round(amount / p, 4)
    print(f"  ✅ 买入 {coin}: ${amount:.2f} -> {qty}")
    result = buy(f'{coin}USDT', qty)
    if 'orderId' in result:
        print(f"     成功! 订单ID: {result['orderId']}")
    else:
        print(f"     失败: {result.get('msg', result)}")

elif sell_candidates:
    best = max(sell_candidates, key=lambda x: abs(x['score']))
    coin = best['coin']
    if coin in positions:
        pos = positions[coin]
        qty = round(pos['qty'] * 0.95, 4)
        print(f"  🔴 卖出 {coin}: {qty} @ ${pos['price']:.2f}")
        result = sell(f'{coin}USDT', qty)
        if 'orderId' in result:
            print(f"     成功! 订单ID: {result['orderId']}")
        else:
            print(f"     失败: {result.get('msg', result)}")
    else:
        print(f"  ⏸️ {coin}无持仓")

else:
    print(f"  ⏸️ 无信号 (资金:${usdt:.2f})")

print("\n" + "=" * 80)
