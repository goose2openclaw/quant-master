"""
执行引擎模块 - 统一下单
"""
import requests, hashlib, hmac, time, math
from .config import API_KEY, API_SECRET, PROXY

def get_exchange_info(symbol):
    """获取交易对精度信息"""
    try:
        r = requests.get(f'https://api.binance.com/api/v3/exchangeInfo', proxies=PROXY, timeout=10)
        for s in r.json()['symbols']:
            if s['symbol'] == symbol + 'USDT':
                for f in s['filters']:
                    if f['filterType'] == 'LOT_SIZE':
                        return {'stepSize': float(f['stepSize']), 'minQty': float(f['minQty'])}
                    if f['filterType'] == 'MIN_NOTIONAL':
                        return {'minNotional': float(f['minNotional'])}
        return {'stepSize': 0.1, 'minQty': 0.1, 'minNotional': 5}
    except:
        return {'stepSize': 0.1, 'minQty': 0.1, 'minNotional': 5}

def round_to_step(qty, step):
    """按步长取整"""
    if step >= 1:
        return math.floor(qty)
    decimals = len(str(step).rstrip('0').split('.')[-1])
    return round(qty, decimals)

def place_order(symbol, side, qty, price=None):
    """下单"""
    info = get_exchange_info(symbol)
    step_size = info.get('stepSize', 0.1)
    min_notional = info.get('minNotional', 5)
    
    qty = round_to_step(qty, step_size)
    
    if qty <= 0:
        return {'success': False, 'reason': 'qty<=0'}
    
    params = {
        'symbol': symbol + 'USDT',
        'side': side.upper(),
        'type': 'MARKET',
        'quantity': f'{qty:.{len(str(step_size).rstrip("0").split(".")[-1])}f}',
        'timestamp': int(time.time() * 1000),
        'recvWindow': 5000
    }
    
    q_str = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
    sig = hmac.new(API_SECRET.encode(), q_str.encode(), hashlib.sha256).hexdigest()
    url = f'https://api.binance.com/api/v3/order?{q_str}&signature={sig}'
    
    for attempt in range(3):
        try:
            r = requests.post(url, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXY, timeout=10)
            result = r.json()
            if 'orderId' in result:
                return {'success': True, 'orderId': result['orderId'], 'qty': qty}
            elif 'code' in result:
                return {'success': False, 'reason': result.get('msg', 'Unknown')}
        except Exception as e:
            time.sleep(0.5)
    
    return {'success': False, 'reason': 'Network error'}

def execute_buy(sym, budget, price, tp_rate, sl_rate):
    """执行买入"""
    qty = budget / price
    result = place_order(sym, 'BUY', qty)
    if result['success']:
        return {
            'success': True,
            'sym': sym,
            'qty': result['qty'],
            'price': price,
            'tp': price * (1 + tp_rate),
            'sl': price * (1 - sl_rate),
            'entry_time': time.time()
        }
    return {'success': False, 'reason': result.get('reason', 'Unknown')}

def execute_sell(sym, qty):
    """执行卖出"""
    result = place_order(sym, 'SELL', qty)
    return result
