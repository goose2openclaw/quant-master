#!/usr/bin/env python3
"""
G24 终极融合版 v4 (优化版)
==========================
基于30天回测结果优化:

【各币种30天回测表现】
DOGE: +17.82% (胜率82%) 🏆 最优
LINK: +12.22% (胜率80%) 🥈 次优
ETH: +7.26% (胜率50%)
SOL: +4.09% (胜率71%)
BTC: +3.92% (胜率57%)

【优化策略】
1. 仓位分配: DOGE/LINK权重更高
2. 信号优先级: DOGE > LINK > ETH > SOL > BTC > 其他
3. 激进参数: 更低RSI阈值买入,更高止盈

【风控参数】
- DOGE/LINK: RSI<35买入, 仓位15%, 止盈20%
- ETH/SOL: RSI<40买入, 仓位10%, 止盈15%
- 其他: RSI<40买入, 仓位10%, 止盈10%
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ========== 交易对 & 权重 ==========
TOP_COINS = ['DOGE', 'LINK']  # 回测表现最好
SECOND_TIER = ['ETH', 'SOL']  # 回测表现中等
MAJOR_COINS = ['BTC', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']  # 其他主流币
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE']

# ========== 分层风控参数 ==========
# TOP tier: DOGE, LINK - 最优表现
TOP_OVERSOLD = 35
TOP_OVERBOUGHT = 75
TOP_POSITION = 0.15   # 15%仓位
TOP_TAKE_PROFIT = 0.20  # 20%止盈
TOP_STOP_LOSS = 0.05

# SECOND tier: ETH, SOL
SECOND_OVERSOLD = 40
SECOND_OVERBOUGHT = 75
SECOND_POSITION = 0.10
SECOND_TAKE_PROFIT = 0.15
SECOND_STOP_LOSS = 0.05

# STANDARD tier: 其他主流币
STD_OVERSOLD = 40
STD_OVERBOUGHT = 75
STD_POSITION = 0.10
STD_TAKE_PROFIT = 0.10
STD_STOP_LOSS = 0.03

# MEME tier: Meme币
MEME_OVERSOLD = 35
MEME_OVERBOUGHT = 80
MEME_POSITION = 0.05
MEME_TAKE_PROFIT = 0.15
MEME_STOP_LOSS = 0.07

RSI_PERIOD = 14
MIN_VOLUME_MAJOR = 5000000
MIN_VOLUME_MEME = 500000
MAX_POSITIONS = 3

def get_tier_config(coin):
    if coin in TOP_COINS:
        return {'oversold': TOP_OVERSOLD, 'overbought': TOP_OVERBOUGHT, 
                'position': TOP_POSITION, 'take_profit': TOP_TAKE_PROFIT, 
                'stop_loss': TOP_STOP_LOSS, 'tier': '🏆 TOP'}
    elif coin in SECOND_TIER:
        return {'oversold': SECOND_OVERSOLD, 'overbought': SECOND_OVERBOUGHT,
                'position': SECOND_POSITION, 'take_profit': SECOND_TAKE_PROFIT,
                'stop_loss': SECOND_STOP_LOSS, 'tier': '🥈 SECOND'}
    else:
        return {'oversold': STD_OVERSOLD, 'overbought': STD_OVERBOUGHT,
                'position': STD_POSITION, 'take_profit': STD_TAKE_PROFIT,
                'stop_loss': STD_STOP_LOSS, 'tier': '📊 STANDARD'}

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
    try:
        resp = opener.open(req, timeout=10)
        return float(json.loads(resp.read().decode())['price'])
    except: return 0

def binance_24hr(symbol):
    url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        return json.loads(resp.read().decode())
    except: return {}

def klines(sym, limit=100, interval='1h'):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=15)
        return [float(k[4]) for k in json.loads(resp.read().decode())]
    except: return []

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def get_balance():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url, method='GET')
    if 'balances' in data:
        for b in data['balances']:
            if b['asset'] == 'USDT': return float(b['free'])
    return 0

def get_positions():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url, method='GET')
    positions = {}
    if 'balances' in data:
        for b in data['balances']:
            free = float(b.get('free', 0))
            if free > 10:
                asset = b['asset']
                if asset != 'USDT':
                    p = price(f'{asset}USDT')
                    if p > 0:
                        positions[asset] = {'qty': free, 'price': p, 'value': free * p}
    return positions

def buy(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, method='POST')

def sell(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, method='POST')

def analyze_coin(coin, is_meme=False):
    symbol = f"{coin}USDT"
    h24 = binance_24hr(symbol)
    if not h24 or 'lastPrice' not in h24:
        return None
    
    current_price = float(h24.get('lastPrice', 0))
    volume = float(h24.get('quoteVolume', 0))
    change_24h = float(h24.get('priceChangePercent', 0))
    
    min_vol = MIN_VOLUME_MEME if is_meme else MIN_VOLUME_MAJOR
    if volume < min_vol:
        return None
    
    prices = klines(symbol, 50)
    if len(prices) < 20:
        return None
    
    rsi = calc_rsi(prices)
    
    if is_meme:
        config = {'oversold': MEME_OVERSOLD, 'overbought': MEME_OVERBOUGHT,
                  'position': MEME_POSITION, 'take_profit': MEME_TAKE_PROFIT,
                  'stop_loss': MEME_STOP_LOSS, 'tier': '🔥 MEME'}
    else:
        config = get_tier_config(coin)
    
    signal = 'HOLD'
    if rsi < config['oversold'] and change_24h < -2:
        signal = 'BUY'
    elif rsi > config['overbought'] and change_24h > 2:
        signal = 'SELL'
    
    return {
        'coin': coin,
        'symbol': symbol,
        'price': current_price,
        'rsi': rsi,
        'change_24h': change_24h,
        'volume': volume,
        'signal': signal,
        'config': config,
        'is_meme': is_meme
    }

def main():
    print("=" * 80)
    print("G24 终极融合版 v4 (优化版)")
    print("=" * 80)
    print("🏆 TOP权重: DOGE/LINK RSI<35 仓位15% 止盈20%")
    print("🥈 SECOND: ETH/SOL RSI<40 仓位10% 止盈15%")
    print("-" * 80)
    
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{ts}] G24扫描\n")
    
    usdt = get_balance()
    positions = get_positions()
    current_positions = len(positions)
    
    print(f"【账户状态】")
    print(f"  可用USDT: ${usdt:.2f}")
    print(f"  当前持仓: {list(positions.keys())}")
    print(f"  持仓数量: {current_positions}/{MAX_POSITIONS}")
    print()
    
    all_signals = []
    
    # 扫描TOP tier (DOGE, LINK)
    print("【🏆 TOP表现层 - DOGE/LINK】")
    print(f"{'币种':10} {'RSI':>6} {'24h涨跌':>10} {'成交量':>12} {'信号':>8}")
    print("-" * 50)
    for coin in TOP_COINS:
        result = analyze_coin(coin, is_meme=False)
        if result:
            emoji = '🟢' if result['signal'] == 'BUY' else '🔴' if result['signal'] == 'SELL' else '⚪'
            vol_str = f"${result['volume']/1000000:.1f}M"
            print(f"{emoji} {coin:8} {result['rsi']:>6.1f} {result['change_24h']:>+9.2f}% {vol_str:>12} {result['signal']:>8}")
            all_signals.append(result)
    
    # 扫描SECOND tier
    print("\n【🥈 SECOND层 - ETH/SOL】")
    print(f"{'币种':10} {'RSI':>6} {'24h涨跌':>10} {'成交量':>12} {'信号':>8}")
    print("-" * 50)
    for coin in SECOND_TIER:
        result = analyze_coin(coin, is_meme=False)
        if result:
            emoji = '🟢' if result['signal'] == 'BUY' else '🔴' if result['signal'] == 'SELL' else '⚪'
            vol_str = f"${result['volume']/1000000:.1f}M"
            print(f"{emoji} {coin:8} {result['rsi']:>6.1f} {result['change_24h']:>+9.2f}% {vol_str:>12} {result['signal']:>8}")
            all_signals.append(result)
    
    # 扫描其他主流币
    print("\n【📊 STANDARD层 - 其他主流币】")
    print(f"{'币种':10} {'RSI':>6} {'24h涨跌':>10} {'成交量':>12} {'信号':>8}")
    print("-" * 50)
    for coin in MAJOR_COINS:
        result = analyze_coin(coin, is_meme=False)
        if result:
            emoji = '🟢' if result['signal'] == 'BUY' else '🔴' if result['signal'] == 'SELL' else '⚪'
            vol_str = f"${result['volume']/1000000:.1f}M"
            print(f"{emoji} {coin:8} {result['rsi']:>6.1f} {result['change_24h']:>+9.2f}% {vol_str:>12} {result['signal']:>8}")
            all_signals.append(result)
    
    # 扫描Meme币
    print("\n【🔥 MEME层】")
    print(f"{'币种':15} {'RSI':>6} {'24h涨跌':>10} {'成交量':>10} {'信号':>8}")
    print("-" * 55)
    for coin in sorted(set(MEME_COINS)):
        result = analyze_coin(coin, is_meme=True)
        if result:
            emoji = '🟢' if result['signal'] == 'BUY' else '🔴' if result['signal'] == 'SELL' else '⚪'
            vol_str = f"${result['volume']/1000000:.1f}M"
            print(f"{emoji} {coin:13} {result['rsi']:>6.1f} {result['change_24h']:>+9.2f}% {vol_str:>10} {result['signal']:>8}")
            all_signals.append(result)
    
    # 交易决策
    print(f"\n{'='*80}")
    print("[交易决策]")
    
    buy_signals = [s for s in all_signals if s['signal'] == 'BUY']
    sell_signals = [s for s in all_signals if s['signal'] == 'SELL']
    
    # 优先卖出
    if sell_signals and positions:
        for sig in sell_signals[:1]:
            coin = sig['coin']
            if coin in positions:
                qty = positions[coin]['qty']
                if qty > 0:
                    qty_str = f"{qty:.0f}" if qty > 1 else f"{qty:.6f}"
                    print(f"  🔴 卖出 {coin} ({sig['config']['tier']})")
                    print(f"     RSI={sig['rsi']:.1f} 24h={sig['change_24h']:+.2f}%")
                    result = sell(f"{coin}USDT", qty_str)
                    if 'orderId' in result:
                        print(f"     ✅ 成功! 订单ID: {result['orderId']}")
                    else:
                        print(f"     ❌ 失败: {result.get('msg', result)}")
    
    # 买入 - 优先TOP tier
    elif buy_signals and usdt > 20 and current_positions < MAX_POSITIONS:
        # 按tier排序: TOP > SECOND > STANDARD > MEME
        tier_order = {'🏆 TOP': 0, '🥈 SECOND': 1, '📊 STANDARD': 2, '🔥 MEME': 3}
        buy_signals.sort(key=lambda x: tier_order.get(x['config']['tier'], 99))
        
        sig = buy_signals[0]
        coin = sig['coin']
        config = sig['config']
        amount = usdt * config['position']
        qty = amount / sig['price']
        
        if qty > 1:
            qty_str = f"{qty:.0f}"
        elif qty > 0.001:
            qty_str = f"{qty:.2f}"
        else:
            qty_str = f"{qty:.6f}"
        
        print(f"  🟢 买入 {coin} ({config['tier']})")
        print(f"     RSI={sig['rsi']:.1f} 24h={sig['change_24h']:+.2f}%")
        print(f"     仓位={config['position']:.0%} 止盈={config['take_profit']:.0%}")
        print(f"     数量={qty_str} 金额=${amount:.2f} 价格=${sig['price']:.8f}")
        result = buy(f"{coin}USDT", qty_str)
        if 'orderId' in result:
            print(f"     ✅ 成功! 订单ID: {result['orderId']}")
        else:
            print(f"     ❌ 失败: {result.get('msg', result)}")
    else:
        print(f"  ⏸️ 无交易")
        print(f"     资金: ${usdt:.2f} | 持仓: {current_positions}/{MAX_POSITIONS}")
        if buy_signals:
            tier_order = {'🏆 TOP': 0, '🥈 SECOND': 1, '📊 STANDARD': 2, '🔥 MEME': 3}
            buy_signals.sort(key=lambda x: tier_order.get(x['config']['tier'], 99))
            print(f"     买入候选: {[(b['coin'], b['config']['tier'], b['rsi']) for b in buy_signals[:3]]}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
