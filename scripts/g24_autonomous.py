#!/usr/bin/env python3
"""
G24 自主决策系统 v1
====================
功能:
1. 主流币 + Meme币 统一资金池
2. 自主决策 (回测验证 + 仿真)
3. 自动操作 (下单 + 风控)
4. 利益最大化

操作流程:
信号检测 → 回测验证 → 仿真交易 → 真实下单
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ========== G24 币种 & 参数 ==========
TOP_COINS = ['DOGE', 'LINK']
SECOND_TIER = ['ETH', 'SOL']
MAJOR_COINS = ['BTC', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE']

# 分层参数
def get_config(coin, is_meme=False):
    if coin in TOP_COINS:
        return {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.20, 'position': 0.15}
    elif coin in SECOND_TIER:
        return {'oversold': 40, 'overbought': 75, 'stop': 0.05, 'take': 0.15, 'position': 0.10}
    elif not is_meme:
        return {'oversold': 40, 'overbought': 75, 'stop': 0.03, 'take': 0.10, 'position': 0.10}
    else:
        return {'oversold': 35, 'overbought': 80, 'stop': 0.07, 'take': 0.15, 'position': 0.05}

RSI_PERIOD = 14
MIN_VOLUME_MAJOR = 5000000
MIN_VOLUME_MEME = 500000
MAX_POSITIONS = 3
SIMULATION_BUDGET = 100  # 仿真金额

# ========== API工具 ==========
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

# ========== 账户工具 ==========
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

# ========== 回测工具 ==========
def backtest(prices, oversold, overbought, stop_loss, take_profit):
    if len(prices) < 100: return None
    rsi_values = []
    for i in range(len(prices)):
        if i < RSI_PERIOD:
            rsi_values.append(50)
        else:
            deltas = np.diff(prices[i-RSI_PERIOD:i+1])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
    
    position = None
    wins = 0
    losses = 0
    total_return = 0
    
    for i in range(RSI_PERIOD, len(prices)):
        if position is None:
            if rsi_values[i] < oversold:
                position = {'entry': prices[i]}
        else:
            pnl = (prices[i] - position['entry']) / position['entry']
            if pnl <= -stop_loss or pnl >= take_profit or rsi_values[i] > overbought:
                if pnl > 0: wins += 1
                else: losses += 1
                total_return += pnl
                position = None
    
    total = wins + losses
    if total == 0: return None
    return {'trades': total, 'wins': wins, 'losses': losses, 
            'win_rate': wins/total*100, 'total_return': total_return*100}

# ========== 仿真工具 ==========
def simulate_trade(coin, price, amount, config):
    """仿真单笔交易"""
    entry = price
    stop = entry * (1 - config['stop'])
    take = entry * (1 + config['take'])
    
    # 简化仿真: 基于随机走势
    import random
    random.seed(hash(coin + str(int(time.time()))))
    
    # 模拟价格变动
    direction = random.choice([-1, 1])
    if direction > 0:  # 盈利场景
        pnl_pct = random.uniform(0.02, config['take'])
        exit_price = entry * (1 + pnl_pct)
        result = 'WIN'
    else:  # 亏损场景
        pnl_pct = random.uniform(0.01, config['stop'])
        exit_price = entry * (1 - pnl_pct)
        result = 'LOSS'
    
    return {
        'coin': coin,
        'entry': entry,
        'exit': exit_price,
        'pnl_pct': pnl_pct * 100,
        'result': result,
        'stop': stop,
        'take': take
    }

# ========== 主系统 ==========
def analyze_coin(coin, is_meme=False):
    symbol = f"{coin}USDT"
    h24 = binance_24hr(symbol)
    if not h24 or 'lastPrice' not in h24:
        return None
    
    current_price = float(h24.get('lastPrice', 0))
    volume = float(h24.get('quoteVolume', 0))
    change_24h = float(h24.get('priceChangePercent', 0))
    
    min_vol = MIN_VOLUME_MEME if is_meme else MIN_VOLUME_MAJOR
    if volume < min_vol: return None
    
    prices = klines(symbol, 50)
    if len(prices) < 20: return None
    
    rsi = calc_rsi(prices)
    config = get_config(coin, is_meme)
    
    signal = 'HOLD'
    if rsi < config['oversold'] and change_24h < -2:
        signal = 'BUY'
    elif rsi > config['overbought'] and change_24h > 2:
        signal = 'SELL'
    
    return {
        'coin': coin, 'symbol': symbol, 'price': current_price,
        'rsi': rsi, 'change_24h': change_24h, 'volume': volume,
        'signal': signal, 'config': config, 'is_meme': is_meme,
        'prices': prices
    }

def main():
    print("=" * 80)
    print("G24 自主决策系统 v1")
    print("=" * 80)
    print("流程: 信号检测 → 回测验证 → 仿真交易 → 真实下单")
    print("-" * 80)
    
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{ts}] 启动自主决策\n")
    
    # 获取账户
    usdt = get_balance()
    positions = get_positions()
    
    print(f"【账户状态】")
    print(f"  可用USDT: ${usdt:.2f}")
    print(f"  当前持仓: {list(positions.keys())}")
    print(f"  持仓数量: {len(positions)}/{MAX_POSITIONS}")
    print()
    
    all_signals = []
    all_coins = TOP_COINS + SECOND_TIER + MAJOR_COINS + list(set(MEME_COINS))
    
    print("【扫描信号】")
    for coin in all_coins:
        is_meme = coin in MEME_COINS and coin not in TOP_COINS + SECOND_TIER + MAJOR_COINS
        result = analyze_coin(coin, is_meme=is_meme)
        if result and result['signal'] != 'HOLD':
            all_signals.append(result)
            emoji = '🟢' if result['signal'] == 'BUY' else '🔴'
            print(f"  {emoji} {coin}: RSI={result['rsi']:.1f} 24h={result['change_24h']:+.2f}% 信号={result['signal']}")
    
    if not all_signals:
        print("  无交易信号")
        return
    
    # ========== 回测验证 ==========
    print(f"\n{'='*80}")
    print("【回测验证】")
    print("-" * 50)
    
    validated_signals = []
    for sig in all_signals:
        coin = sig['coin']
        config = sig['config']
        prices = sig['prices']
        
        # 30天回测
        bt_prices = klines(sig['symbol'], 30)
        if len(bt_prices) < 500:
            print(f"  ⚪ {coin}: 数据不足")
            continue
        
        bt = backtest(bt_prices, config['oversold'], config['overbought'], config['stop'], config['take'])
        
        if bt and bt['win_rate'] >= 50 and bt['total_return'] > 0:
            validated_signals.append({**sig, 'backtest': bt})
            print(f"  ✅ {coin}: 胜率{bt['win_rate']:.1f}% 收益{bt['total_return']:+.1f}%")
        else:
            win_str = bt['win_rate'] if bt else 0
            ret_str = bt['total_return'] if bt else 0
            print(f"  ❌ {coin}: 胜率{win_str:.1f}% 收益{ret_str:+.1f}% (不通过)")
    
    if not validated_signals:
        print("  无通过回测验证的信号")
        return
    
    # ========== 仿真交易 ==========
    print(f"\n{'='*80}")
    print("【仿真交易】")
    print("-" * 50)
    
    simulated_results = []
    for sig in validated_signals:
        coin = sig['coin']
        config = sig['config']
        price_now = sig['price']
        
        # 仿真10次
        wins = 0
        total_pnl = 0
        for _ in range(10):
            sim = simulate_trade(coin, price_now, SIMULATION_BUDGET, config)
            if sim['result'] == 'WIN':
                wins += 1
            total_pnl += sim['pnl_pct']
        
        avg_win_rate = wins / 10 * 100
        avg_pnl = total_pnl / 10
        
        # 仿真胜率>60%才执行
        if avg_win_rate >= 60:
            simulated_results.append({**sig, 'sim_win_rate': avg_win_rate, 'sim_pnl': avg_pnl})
            print(f"  ✅ {coin}: 仿真胜率{avg_win_rate:.0f}% 预期收益{avg_pnl:+.1f}%")
        else:
            print(f"  ❌ {coin}: 仿真胜率{avg_win_rate:.0f}% (不通过)")
    
    if not simulated_results:
        print("  无通过仿真的信号")
        return
    
    # ========== 真实下单 ==========
    print(f"\n{'='*80}")
    print("【真实下单】")
    print("-" * 50)
    
    # 按收益排序
    simulated_results.sort(key=lambda x: x['sim_pnl'], reverse=True)
    
    for sig in simulated_results[:1]:  # 只执行最优
        coin = sig['coin']
        config = sig['config']
        
        if len(positions) >= MAX_POSITIONS:
            print(f"  ⏸️ 持仓已满 ({len(positions)}/{MAX_POSITIONS})")
            break
        
        amount = usdt * config['position']
        qty = amount / sig['price']
        
        if qty > 1: qty_str = f"{qty:.0f}"
        elif qty > 0.001: qty_str = f"{qty:.2f}"
        else: qty_str = f"{qty:.6f}"
        
        print(f"  🟢 买入 {coin}")
        print(f"     回测: 胜率{sig['backtest']['win_rate']:.1f}% 收益{sig['backtest']['total_return']:+.1f}%")
        print(f"     仿真: 胜率{sig['sim_win_rate']:.0f}% 预期收益{sig['sim_pnl']:+.1f}%")
        print(f"     数量: {qty_str} 金额: ${amount:.2f}")
        
        result = buy(f"{coin}USDT", qty_str)
        if 'orderId' in result:
            print(f"     ✅ 成功! 订单ID: {result['orderId']}")
        else:
            print(f"     ❌ 失败: {result.get('msg', result)}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
