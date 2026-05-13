#!/usr/bin/env python3
"""
G20 Pro Max - 动能增强版
目标: 利益最大化
特点:
1. 多策略共振信号
2. 多时间框架确认
3. 动态仓位管理
4. 自主机会扫描
5. 科学决策引擎
"""
import urllib.request, urllib.parse, hmac, hashlib, time, json, numpy as np
from datetime import datetime

PROXY = "http://172.29.144.1:7897"
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

def api_request(url, method='GET'):
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    return float(api_request(url)['price'])

def get_klines(sym, limit=200, interval='1h'):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    data = api_request(url)
    return [float(k[4]) for k in data] if isinstance(data, list) else []

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_ema(prices, period):
    if len(prices) < period: return prices[-1]
    return np.mean(prices[-period:])

def calc_macd(prices):
    ema12 = calc_ema(prices, 12)
    ema26 = calc_ema(prices, 26)
    return ema12 - ema26

def calc_momentum(prices, period=10):
    if len(prices) < period + 1: return 0
    return (prices[-1] - prices[-period-1]) / prices[-period-1] * 100

def get_spot_balance():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api_request(url)
    if 'balances' in data:
        for b in data['balances']:
            if b['asset'] == 'USDT':
                return float(b['free'])
    return 0

def buy_spot(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api_request(url, 'POST')

# 监控币种
COINS = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'LINK', 'AVAX', 'DOT', 'UNI']

def analyze_coin(coin):
    """多策略综合分析"""
    prices_1h = get_klines(f'{coin}USDT', 100, '1h')
    prices_4h = get_klines(f'{coin}USDT', 100, '4h')
    prices_15m = get_klines(f'{coin}USDT', 100, '15m')
    
    if len(prices_1h) < 50:
        return None
    
    # RSI
    rsi_1h = calc_rsi(prices_1h)
    rsi_4h = calc_rsi(prices_4h) if len(prices_4h) >= 50 else 50
    rsi_15m = calc_rsi(prices_15m) if len(prices_15m) >= 50 else 50
    
    # MACD
    macd_1h = calc_macd(prices_1h)
    macd_4h = calc_macd(prices_4h) if len(prices_4h) >= 50 else 0
    
    # 动量
    mom_1h = calc_momentum(prices_1h, 10)
    mom_4h = calc_momentum(prices_4h, 10) if len(prices_4h) >= 50 else 0
    
    # 趋势
    ema20 = calc_ema(prices_1h, 20)
    ema50 = calc_ema(prices_1h, 50)
    trend = 'bullish' if ema20 > ema50 else 'bearish'
    
    # ====== 多策略共振评分 ======
    score = 50  # 基础分
    
    # 策略1: RSI超卖
    if rsi_1h < 30: score += 25
    elif rsi_1h < 40: score += 15
    elif rsi_1h < 45: score += 10
    
    # 策略2: 多时间框架共振
    if rsi_1h < 40 and rsi_4h < 40: score += 15
    if rsi_1h < 40 and rsi_15m < 40: score += 10
    
    # 策略3: MACD金叉
    if macd_1h > 0: score += 10
    if macd_1h > 0 and macd_4h > 0: score += 10
    
    # 策略4: 动量正向
    if mom_1h > 0: score += 10
    if mom_1h > 0 and mom_4h > 0: score += 10
    
    # 策略5: 趋势确认
    if trend == 'bullish': score += 10
    
    # 风险调整
    if rsi_1h > 70: score -= 20
    if macd_1h < 0 and macd_4h < 0: score -= 15
    
    score = max(0, min(100, score))
    
    return {
        'coin': coin,
        'rsi_1h': rsi_1h,
        'rsi_4h': rsi_4h,
        'rsi_15m': rsi_15m,
        'macd_1h': macd_1h,
        'trend': trend,
        'momentum': mom_1h,
        'score': score,
        'signal': 'BUY' if score >= 70 else 'HOLD'
    }

def execute_trade(coin, usdt_amount):
    """执行交易"""
    price = get_price(f'{coin}USDT')
    qty = round(usdt_amount / price, 4)
    
    print(f"  买入 {coin}: ${usdt_amount:.2f} -> {qty} @ ${price:.4f}")
    result = buy_spot(f'{coin}USDT', qty)
    
    if 'orderId' in result:
        print(f"    ✅ 成功! 订单ID: {result['orderId']}")
        return True
    else:
        print(f"    ❌ 失败: {result.get('msg', result)}")
        return False

def main():
    print("=" * 80)
    print("G20 Pro Max - 动能增强版")
    print("=" * 80)
    
    # 1. 获取余额
    usdt = get_spot_balance()
    print(f"\n[资金] USDT: ${usdt:.2f}")
    
    # 2. 扫描所有币种
    print("\n[扫描] 多策略共振分析...")
    opportunities = []
    
    for coin in COINS:
        result = analyze_coin(coin)
        if result:
            opportunities.append(result)
            emoji = '🟢' if result['signal'] == 'BUY' else '🟡'
            print(f"  {emoji} {coin}: RSI={result['rsi_1h']:.0f}/{result['rsi_4h']:.0f} MACD={result['macd_1h']:.2f} 评分={result['score']:.0f} -> {result['signal']}")
    
    # 3. 排序选择最佳机会
    opportunities.sort(key=lambda x: -x['score'])
    
    # 4. 执行交易
    print("\n[决策] 信号排序:")
    buy_list = [o for o in opportunities if o['signal'] == 'BUY']
    
    for i, o in enumerate(buy_list[:5]):
        print(f"  {i+1}. {o['coin']}: 评分={o['score']:.0f} RSI={o['rsi_1h']:.0f}")
    
    if buy_list and usdt > 20:
        # 分配资金: 强信号多分配
        total_score = sum(o['score'] for o in buy_list[:3])
        
        print(f"\n[执行] 分配${usdt*0.9:.2f}到Top3信号:")
        
        for o in buy_list[:3]:
            weight = o['score'] / total_score
            amount = usdt * 0.9 * weight
            execute_trade(o['coin'], amount)
            time.sleep(1)
    else:
        print("\n[状态] 无买入信号或资金不足")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
