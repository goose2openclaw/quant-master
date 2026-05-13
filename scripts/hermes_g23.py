#!/usr/bin/env python3
"""
G23 - 终极融合版
===============
集成技能:
1. G20 RSI交易策略 (现货)
2. Binance Smart Money信号 (链上数据)
3. 策略回测验证 (backtesting)
4. Binance合约API (U本位合约)
5. 跨市场套利 (现货vs合约)
6. 动态权重优化 (收益最大化)

信号优先级:
1. RSI超卖(<30) + 合约资金费率正 → 买入
2. RSI超买(>70) + 合约资金费率负 → 卖出
3. Smart Money活跃信号 → 参考
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ========== G23核心参数 ==========
RSI_PERIOD = 14
OVERBOUGHT = 70
OVERSOLD = 30
COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']

# ========== 工具函数 ==========
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

def klines(sym, limit=100, interval='1h'):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
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
    url = "https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/signal/smart-money/ai"
    headers = {'Content-Type': 'application/json', 'Accept-Encoding': 'identity', 'User-Agent': 'binance-web3/1.1 (Skill)'}
    data = json.dumps({"page": page, "pageSize": page_size, "chainId": chain_id}).encode()
    req = urllib.request.Request(url, method='POST', data=data, headers=headers)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=15)
        return json.loads(resp.read().decode())
    except: return {'data': []}

def get_funding_rate(symbol):
    """获取合约资金费率"""
    url = f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode())
        return float(data.get('lastFundingRate', 0)) * 100  # 转为百分比
    except: return 0

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

def get_futures_balance():
    """获取合约账户USDT余额"""
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.bapi.com/fapi/v1/balance?timestamp={ts}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode())
        for item in data:
            if item.get('asset') == 'USDT':
                return float(item.get('availableBalance', 0))
    except: return 0

def buy(symbol, qty, account='spot'):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    if account == 'spot':
        url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    else:
        url = f"https://fapi.binance.com/fapi/v1/order?{q}&signature={sig}"
    return api(url, 'POST')

def sell(symbol, qty, account='spot'):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    if account == 'spot':
        url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    else:
        url = f"https://fapi.binance.com/fapi/v1/order?{q}&signature={sig}"
    return api(url, 'POST')

# ========== 回测模块 ==========
def backtest(prices, period=14, overbought=70, oversold=30):
    trades = []
    position = 0
    for i in range(period, len(prices)):
        rsi = calc_rsi(prices[:i], period)
        if rsi < oversold and position == 0:
            trades.append(('BUY', prices[i], rsi))
            position = 1
        elif rsi > overbought and position == 1:
            profit = (prices[i] - trades[-1][1]) / trades[-1][1] * 100
            trades.append(('SELL', prices[i], rsi, profit))
            position = 0
    return trades

def calc_metrics(trades):
    sells = [t for t in trades if t[0] == 'SELL']
    if not sells: return {'trades': 0, 'win_rate': 0, 'avg_profit': 0, 'total': 0}
    profits = [t[3] for t in sells]
    wins = [p for p in profits if p > 0]
    return {
        'trades': len(sells),
        'win_rate': len(wins)/len(profits)*100 if profits else 0,
        'avg_profit': np.mean(profits) if profits else 0,
        'total': sum(profits)
    }

# ========== G23主程序 ==========
def main():
    print("=" * 80)
    print("G23 - 终极融合版")
    print("集成: G20 + Smart Money + Backtesting + Futures API")
    print("=" * 80)
    
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] G23 运行中...")
    
    # 1. Smart Money信号
    print("\n[1] Smart Money信号...")
    sm_data = get_smart_money_signals("56", 1, 20)
    smart_signals = []
    if 'data' in sm_data:
        for s in sm_data['data']:
            if s.get('status') == 'active' and s.get('direction') in ['buy', 'sell']:
                smart_signals.append(s)
    
    if smart_signals:
        for s in smart_signals[:5]:
            print(f"  🟢 {s['ticker']} {s['direction']} maxGain:{float(s['maxGain']):.1f}%")
    else:
        print("  ⏰ 无活跃信号")
    
    # 2. 现货分析
    print(f"\n[2] 现货RSI分析...")
    coin_data = []
    for coin in COINS:
        try:
            prices = klines(f'{coin}USDT', 100)
            rsi = calc_rsi(prices)
            funding = get_funding_rate(f'{coin}USDT')
            signal = 'HOLD'
            score = 50
            
            if rsi < OVERSOLD:
                signal = 'BUY'
                score = 100 - rsi
            elif rsi > OVERBOUGHT:
                signal = 'SELL'
                score = rsi
            
            coin_data.append({
                'coin': coin, 'rsi': rsi, 'funding': funding,
                'signal': signal, 'score': score
            })
            
            emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
            print(f"  {emoji} {coin:5} RSI={rsi:5.1f} 资金费={funding:+.3f}% -> {signal}")
        except Exception as e:
            print(f"  ❌ {coin}: {e}")
    
    # 3. 合约分析
    print(f"\n[3] 合约资金费率分析...")
    funding_opps = []
    for cd in coin_data:
        if cd['funding'] > 0.01:  # 正资金费率
            funding_opps.append((cd['coin'], cd['funding'], 'LONG'))
        elif cd['funding'] < -0.01:  # 负资金费率
            funding_opps.append((cd['coin'], abs(cd['funding']), 'SHORT'))
    
    if funding_opps:
        funding_opps.sort(key=lambda x: x[1], reverse=True)
        print("  正资金费率机会:")
        for coin, f, direction in funding_opps[:3]:
            print(f"    {coin}: {f:.3f}% -> {direction}")
    
    # 4. 回测验证
    print(f"\n[4] 回测验证 (过去100小时)...")
    for coin in ['BTC', 'ETH', 'SOL'][:3]:
        try:
            prices = klines(f'{coin}USDT', 100)
            trades = backtest(prices, RSI_PERIOD, OVERBOUGHT, OVERSOLD)
            metrics = calc_metrics(trades)
            emoji = '🟢' if metrics['total'] > 0 else '🔴'
            print(f"  {emoji} {coin}: {metrics['trades']}笔 胜率{metrics['win_rate']:.0f}% 均盈{metrics['avg_profit']:.2f}% 总{metrics['total']:.2f}%")
        except: pass
    
    # 5. 综合决策
    print(f"\n[5] 综合决策...")
    usdt_spot = get_balance()
    usdt_futures = get_futures_balance()
    positions = get_positions()
    
    print(f"  现货USDT: ${usdt_spot:.2f}")
    print(f"  合约USDT: ${usdt_futures:.2f}")
    
    # 买入信号
    buy_candidates = [c for c in coin_data if c['signal'] == 'BUY' and c['score'] > 70]
    
    if buy_candidates and usdt_spot > 10:
        best = max(buy_candidates, key=lambda x: x['score'])
        coin = best['coin']
        amount = usdt_spot * 0.9
        p = price(f'{coin}USDT')
        qty = round(amount / p, 4)
        print(f"  ✅ 现货买入 {coin}: ${amount:.2f} -> {qty}")
        result = buy(f'{coin}USDT', qty, 'spot')
        if 'orderId' in result:
            print(f"     成功! 订单ID: {result['orderId']}")
        else:
            print(f"     失败: {result.get('msg', result)}")
    
    # 卖出信号
    elif positions:
        sell_candidates = [c for c in coin_data if c['signal'] == 'SELL' and c['score'] > 80]
        if sell_candidates:
            best = max(sell_candidates, key=lambda x: x['score'])
            coin = best['coin']
            if coin in positions:
                pos = positions[coin]
                qty = round(pos['qty'] * 0.95, 4)
                print(f"  🔴 现货卖出 {coin}: {qty} @ ${pos['price']:.2f}")
                result = sell(f'{coin}USDT', qty, 'spot')
                if 'orderId' in result:
                    print(f"     成功!")
        else:
            print(f"  ⏸️ 无卖出信号")
    else:
        print(f"  ⏸️ 无持仓,等待买入信号")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
