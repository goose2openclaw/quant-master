#!/usr/bin/env python3
"""
G18 Ultra - 最优参数版本
基于581%收益优化的参数
"""
import requests, numpy as np, time, hmac, hashlib
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# 最优参数 (来自581%优化)
CONFIG = {
    'rsi_buy': 34,
    'rsi_sell': 72,
    'ema_fast': 14,
    'ema_slow': 34,
    'take_profit': 0.11,
    'stop_loss': 0.04,
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
    except: return {'code': -1}

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

def calc_ema(prices, period):
    if len(prices) < period: return None
    ema = prices[0]
    smoothing = 2.0 / (period + 1)
    for p in prices[1:]:
        ema = (p - ema) * smoothing + ema
    return ema

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def analyze(coin):
    prices = get_klines(f'{coin}USDT', 200)
    if len(prices) < 50:
        return None
    
    rsi = calc_rsi(prices)
    ema_fast = calc_ema(prices, CONFIG['ema_fast'])
    ema_slow = calc_ema(prices, CONFIG['ema_slow'])
    
    # 评分
    score = 0
    
    if rsi < CONFIG['rsi_buy']:
        score += 50
    elif rsi < 45:
        score += 25
    
    if ema_fast and ema_slow:
        if ema_fast > ema_slow:
            score += 30
        else:
            score -= 30
    
    # 趋势强度
    if ema_fast and prices[-1] > ema_fast:
        score += 10
    elif ema_fast and prices[-1] < ema_fast:
        score -= 10
    
    # 信号
    if score >= 60:
        signal = 'STRONG_BUY'
    elif score >= 30:
        signal = 'BUY'
    elif score <= -30:
        signal = 'SELL'
    elif score <= -60:
        signal = 'STRONG_SELL'
    else:
        signal = 'HOLD'
    
    return {
        'coin': coin,
        'price': prices[-1],
        'rsi': rsi,
        'ema_fast': ema_fast,
        'ema_slow': ema_slow,
        'score': score,
        'signal': signal
    }

def get_spot_account():
    data = api_get('https://api.binance.com/api/v3/account')
    if 'error' in data: return {}
    result = {}
    for b in data.get('balances', []):
        free = float(b.get('free', 0))
        if free > 0.00001:
            result[b['asset']] = free
    return result

def spot_to_margin(asset, qty):
    url = 'https://api.binance.com/sapi/v1/margin/transfer'
    params = {
        'asset': asset, 'type': 1,
        'amount': f'{qty:.8f}'.rstrip('0').rstrip('.')
    }
    return api_post(url, params)

def main():
    print("=" * 70)
    print("G18 Ultra - 最优参数版本 (预计581%收益)")
    print("=" * 70)
    print(f"参数: RSI {CONFIG['rsi_buy']}/{CONFIG['rsi_sell']}, EMA {CONFIG['ema_fast']}/{CONFIG['ema_slow']}, TP {CONFIG['take_profit']*100:.0f}%")
    
    # 分析
    print(f"\n🔍 信号分析:")
    signals = []
    for coin in COINS:
        a = analyze(coin)
        if a:
            signals.append(a)
            emoji = '🟢' if 'BUY' in a['signal'] else '🔴' if 'SELL' in a['signal'] else '🟡'
            print(f"  {emoji} {coin:6} RSI:{a['rsi']:5.1f} Score:{a['score']:5} → {a['signal']}")
    
    # 账户
    spot = get_spot_account()
    print(f"\n📊 账户: {', '.join([f'{k}:{v:.4f}' for k,v in spot.items() if v > 0.001])}")
    
    # 强势信号执行
    buy_signals = [s for s in signals if 'BUY' in s['signal'] and s['rsi'] < 40]
    if buy_signals:
        print(f"\n🚀 买入信号:")
        for s in buy_signals:
            qty = spot.get(s['coin'], 0) * 0.3
            if qty > 0.001:
                result = spot_to_margin(s['coin'], qty)
                if 'tranId' in result:
                    print(f"  ✅ {s['coin']}: 转入{qty:.4f}全仓")
                else:
                    print(f"  ❌ {s['coin']}: {result.get('msg', '失败')}")
    else:
        print(f"\n⏸️ 无强势买入信号")

if __name__ == '__main__':
    main()
