"""
市场数据模块
"""
import requests, json, time
from .config import PROXY

def get_price(symbol):
    """获取单个币种价格"""
    try:
        url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT'
        r = requests.get(url, proxies=PROXY, timeout=5)
        return float(r.json()['price'])
    except:
        return 0

def get_prices(symbols):
    """批量获取价格"""
    prices = {}
    for s in set(symbols):
        prices[s] = get_price(s)
    return prices

def get_klines(symbol, interval='3m', limit=100):
    """获取K线数据"""
    try:
        url = f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}'
        r = requests.get(url, proxies=PROXY, timeout=10)
        data = r.json()
        closes = [float(k[4]) for k in data]
        volumes = [float(k[5]) for k in data]
        return closes, volumes
    except:
        return None, None

def calc_rsi(closes, period=14):
    """计算RSI"""
    if len(closes) < period + 1:
        return 50
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d for d in deltas[-period:] if d > 0]
    losses = [-d for d in deltas[-period:] if d < 0]
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_bb(closes, period=20):
    """计算布林带位置 (0=下轨, 1=中轨, 2=上轨)"""
    if len(closes) < period:
        return 0.5
    ma = sum(closes[-period:]) / period
    std = (sum([(c - ma) ** 2 for c in closes[-period:]]) / period) ** 0.5
    if std == 0:
        return 0.5
    bb_pos = (closes[-1] - ma) / (2 * std)
    return (bb_pos + 2) / 4  # 归一化到0-1

def get_market_signal(symbol):
    """获取市场信号 (RSI, BB, 动量)"""
    closes, _ = get_klines(symbol, '3m', 100)
    if closes is None:
        return None, None, None, None
    rsi = calc_rsi(closes)
    bb_pos = calc_bb(closes)
    momentum = (closes[-1] - closes[-6]) / closes[-6] if len(closes) >= 6 else 0
    return closes[-1], rsi, bb_pos, momentum

def get_24h_stats(symbol):
    """获取24h统计数据"""
    try:
        url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT'
        r = requests.get(url, proxies=PROXY, timeout=5)
        d = r.json()
        return {
            'price': float(d['lastPrice']),
            'change': float(d['priceChangePercent']),
            'volume': float(d['quoteVolume'])
        }
    except:
        return None

def get_all_balances():
    """获取账户余额"""
    import hashlib, hmac, time
    from .config import API_KEY, API_SECRET
    
    ts = int(time.time() * 1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    
    try:
        r = requests.get(
            f'https://api.binance.com/api/v3/account?{params}&signature={sig}',
            headers={'X-MBX-APIKEY': API_KEY},
            proxies=PROXY, timeout=15
        )
        data = r.json()
        balances = {}
        for b in data['balances']:
            if float(b['free']) > 0 or float(b['locked']) > 0:
                balances[b['asset']] = {
                    'free': float(b['free']),
                    'locked': float(b['locked'])
                }
        return balances
    except:
        return {}
