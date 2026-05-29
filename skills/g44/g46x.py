#!/usr/bin/env python3
"""
G46X - 增强版现货管家
新增功能:
1. 震荡行情 - 高卖低买
2. 多空趋势 - 趋势跟随
3. 市场筛选 - 过滤小币
4. 自主策略切换
"""
import urllib.request, urllib.parse, hmac, hashlib, time, json, os, math
from collections import deque

os.environ['http_proxy'] = 'http://172.29.144.1:7897'
os.environ['https_proxy'] = 'http://172.29.144.1:7897'

PROXY = 'http://172.29.144.1:7897'
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

# 策略参数
BUY_THRESHOLD = 0.5     # 买入阈值提高
SELL_THRESHOLD = -0.5   # 卖出阈值降低
BUDGET = 10             # 交易预算
MIN_NOTIONAL = 10       # 最小订单金额

# 黑名单 - 小币种过滤
BLACKLIST = ['NEIRO', 'TURBO', 'PEPE', 'FLOKI', 'BOME', 'SHIB', 'DOGE']

# 策略模式
MODE = 'auto'  # auto, trend, volatility, sideways

INFO_CACHE = {}
price_history = {}

def log(msg):
    print(f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}")

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    with opener.open(req, timeout=5) as r:
        return float(json.loads(r.read())['price'])

def get_exchange_info(symbol):
    if symbol in INFO_CACHE:
        return INFO_CACHE[symbol]
    url = f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}USDT'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    with opener.open(req, timeout=5) as r:
        data = json.loads(r.read())
    for s in data['symbols']:
        if s['symbol'] == symbol + 'USDT':
            info = {}
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    info['minQty'] = float(f['minQty'])
                    info['stepSize'] = float(f['stepSize'])
                elif f['filterType'] == 'MIN_NOTIONAL':
                    info['minNotional'] = float(f['minNotional'])
            INFO_CACHE[symbol] = info
            return info
    return {'minQty': 0.1, 'stepSize': 0.1, 'minNotional': 10}

def round_to_step(qty, step):
    if step >= 1:
        return int(qty / step) * step
    decimals = len(str(step).split('.')[-1].rstrip('0'))
    return float(f"{int(qty / step) * step:.{decimals}f}")

def get_spot_balance():
    ts = int(time.time() * 1000)
    params = f'timestamp={ts}&recvWindow=5000'
    q = '&'.join('{}={}'.format(k,v) for k,v in [('timestamp',ts),('recvWindow',5000)])
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f'https://api.binance.com/api/v3/account?' + q + '&signature=' + sig
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    with opener.open(req, timeout=10) as r:
        data = json.loads(r.read())
    
    balances = {}
    for b in data['balances']:
        free = float(b['free'])
        if free > 0:
            balances[b['asset']] = {'free': free, 'locked': float(b['locked'])}
    return balances

def place_order(sym, side, qty, price):
    if sym in BLACKLIST:
        log(f'  ⛔ {sym}在黑名单，跳过')
        return {'success': False}
    info = get_exchange_info(sym)
    stepSize = info.get('stepSize', 0.1)
    minNotional = info.get('minNotional', 10)
    qty = round_to_step(qty, stepSize)
    order_value = qty * price
    if qty <= 0 or order_value < minNotional:
        log(f'  ⚠️ {sym}订单金额${order_value:.2f}小于最小${minNotional}')
        return {'success': False}
    prec = max(0, -int(math.log10(stepSize)) if stepSize < 1 else int(math.log10(1/stepSize)) if stepSize > 1 else 0)
    qty_str = f"{qty:.{prec}f}"
    for attempt in range(3):
        try:
            ts = int(time.time() * 1000)
            params = {
                'symbol': sym + 'USDT', 'side': side.upper(), 'type': 'MARKET',
                'quantity': qty_str, 'timestamp': ts, 'recvWindow': 5000
            }
            q_str = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
            sig = hmac.new(API_SECRET.encode(), q_str.encode(), hashlib.sha256).hexdigest()
            url = 'https://api.binance.com/api/v3/order?' + q_str + '&signature=' + sig
            req = urllib.request.Request(url, method='POST')
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            resp = opener.open(req, timeout=10).read().decode()
            log(f'  📤 {sym} {side.upper()} {qty_str} 成功')
            return {'success': True}
        except Exception as e:
            log(f'  错误: {str(e)[:60]}')
            time.sleep(0.5)
    return {'success': False}

def calculate_volatility(symbol, prices):
    """计算波动率"""
    if symbol not in price_history:
        price_history[symbol] = deque(maxlen=20)
    price_history[symbol].append(prices[symbol])
    if len(price_history[symbol]) < 10:
        return 0
    arr = list(price_history[symbol])
    mean = sum(arr) / len(arr)
    variance = sum((x - mean) ** 2 for x in arr) / len(arr)
    return variance / mean if mean > 0 else 0

def detect_market_mode(prices):
    """检测市场模式"""
    btc_price = prices.get('BTC', 0)
    eth_price = prices.get('ETH', 0)
    if btc_price == 0:
        return 'unknown'
    
    # 计算20周期涨跌
    btc_history = price_history.get('BTC', deque(maxlen=20))
    if len(btc_history) < 10:
        return 'sideways'
    
    btc_arr = list(btc_history)
    change = (btc_arr[-1] - btc_arr[0]) / btc_arr[0] if btc_arr[0] > 0 else 0
    volatility = calculate_volatility('BTC', prices)
    
    if abs(change) > 0.02:  # >2%变化
        return 'trend_up' if change > 0 else 'trend_down'
    elif volatility > 0.0001:  # 高波动
        return 'volatility'
    else:
        return 'sideways'

def get_signal(symbols, prices, mode):
    """根据模式计算信号"""
    strong_buys = []
    strong_sells = []
    signals = {}
    
    for sym in symbols:
        if sym in BLACKLIST:
            continue
        try:
            price = prices[sym]
            history = price_history.get(sym, deque(maxlen=20))
            if len(history) < 5:
                signals[sym] = 0
                continue
            
            arr = list(history)
            
            if mode == 'trend' or mode == 'auto':
                # 趋势策略: 均线交叉
                ma5 = sum(arr[-5:]) / 5
                ma10 = sum(arr[-10:]) / 10 if len(arr) >= 10 else ma5
                signal = (ma5 - ma10) / ma10 if ma10 > 0 else 0
            elif mode == 'volatility' or mode == 'sideways':
                # 震荡策略: RSI类指标
                change = (arr[-1] - arr[0]) / arr[0] if arr[0] > 0 else 0
                signal = -change * 2  # 反向操作，高卖低买
            else:
                signal = 0
            
            signals[sym] = signal
            
            if signal > BUY_THRESHOLD:
                strong_buys.append({'sym': sym, 'signal': signal, 'price': price})
            elif signal < SELL_THRESHOLD:
                strong_sells.append({'sym': sym, 'signal': signal, 'price': price})
        except:
            signals[sym] = 0
    
    return strong_buys, strong_sells, signals

def main():
    log('=' * 60)
    log('G46X - 增强版现货管家启动')
    log('=' * 60)
    
    symbols = ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB','AVAX','ETC','NEAR']
    cycle = 0
    trades = 0
    
    while True:
        cycle += 1
        try:
            prices = {}
            for sym in symbols:
                try:
                    prices[sym] = get_price(sym)
                except:
                    prices[sym] = 0
            
            # 检测市场模式
            mode = detect_market_mode(prices)
            log(f'=== G46X周期{cycle} | 模式:{mode.upper()} ===')
            
            # 获取信号
            strong_buys, strong_sells, signals = get_signal(symbols, prices, mode)
            
            log(f'  买入信号: {len(strong_buys)} | 卖出信号: {len(strong_sells)}')
            
            # 获取持仓
            balances = get_spot_balance()
            spot_usdt = balances.get('USDT', {}).get('free', 0)
            log(f'  现货USDT: ${spot_usdt:.2f}')
            
            # 执行卖出(优先)
            for d in strong_sells[:2]:
                sym = d['sym']
                if sym in balances:
                    free = balances[sym]['free']
                    info = get_exchange_info(sym)
                    min_qty = info.get('minQty', 0.1)
                    min_notional = info.get('minNotional', 10)
                    qty = round_to_step(free, info.get('stepSize', 0.1))
                    value = qty * prices.get(sym, 0)
                    if qty >= min_qty and value >= min_notional:
                        log(f'  📤 卖出 {sym} 信号:{d["signal"]:.2f}')
                        if place_order(sym, 'SELL', qty, prices.get(sym, 0)).get('success'):
                            trades += 1
                        balances = get_spot_balance()
            
            # 执行买入
            if strong_buys and spot_usdt >= BUDGET:
                for d in strong_buys[:2]:
                    sym = d['sym']
                    if sym in BLACKLIST:
                        continue
                    price = prices.get(sym, 0)
                    if price > 0:
                        qty = BUDGET / price
                        log(f'  📥 买入 {sym} 信号:{d["signal"]:.2f} 数量:{qty:.4f}')
                        if place_order(sym, 'BUY', qty, price).get('success'):
                            trades += 1
                            spot_usdt -= BUDGET
                        if spot_usdt < BUDGET:
                            break
            
            log(f'  统计: 周期{cycle} 交易{trades}')
            log('')
            
            for _ in range(60):
                time.sleep(1)
                
        except Exception as e:
            log(f'异常: {str(e)[:80]}')
            time.sleep(5)

if __name__ == '__main__':
    main()
