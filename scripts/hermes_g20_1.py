#!/usr/bin/env python3
"""
G20.1 - 蒸馏HAA多因子版
G19 + 蒸馏Hyper Alpha Arena多因子 (RSI+趋势+动量+波动率)
"""
import requests, numpy as np, time, json
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def get_klines(sym, limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [float(k[4]) for k in r.json()]
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

def calc_volatility(prices, period=20):
    if len(prices) < period: return 0.05
    returns = np.diff(prices[-period:]) / prices[-period:-1]
    return np.std(returns)

def calc_trend(prices, period=20):
    if len(prices) < period: return 0
    ma20 = np.mean(prices[-20:])
    ma50 = np.mean(prices[-50:]) if len(prices) >= 50 else ma20
    return (ma20 - ma50) / ma50 * 100

def calc_momentum(prices, period=72):
    if len(prices) < period + 1: return 0
    return (prices[-1] - prices[-period-1]) / prices[-period-1] * 100

G19_PARAMS = {
    'BTC': {'rsi_buy': 45, 'rsi_sell': 79, 'tp': 0.092, 'sl': 0.034},
    'ETH': {'rsi_buy': 29, 'rsi_sell': 79, 'tp': 0.054, 'sl': 0.042},
    'SOL': {'rsi_buy': 45, 'rsi_sell': 76, 'tp': 0.082, 'sl': 0.054},
    'XRP': {'rsi_buy': 24, 'rsi_sell': 77, 'tp': 0.17, 'sl': 0.048},
    'ADA': {'rsi_buy': 43, 'rsi_sell': 63, 'tp': 0.079, 'sl': 0.025},
    'DOGE': {'rsi_buy': 45, 'rsi_sell': 80, 'tp': 0.07, 'sl': 0.03},
    'LINK': {'rsi_buy': 44, 'rsi_sell': 77, 'tp': 0.06, 'sl': 0.045},
}

def main():
    print("=" * 70)
    print("G20.1 - 蒸馏HAA多因子版")
    print("=" * 70)
    
    signals = []
    
    for coin, params in G19_PARAMS.items():
        prices = get_klines(f'{coin}USDT', 168)
        if len(prices) < 50: continue
        
        rsi = calc_rsi(prices)
        vol = calc_volatility(prices)
        trend = calc_trend(prices)
        mom = calc_momentum(prices)
        
        # 多因子评分
        factor_score = 0
        
        if rsi < 30: factor_score += 30
        elif rsi < 40: factor_score += 20
        elif rsi < params['rsi_buy']: factor_score += 10
        
        if trend > 0: factor_score += 20
        elif trend > 2: factor_score += 10
        
        if mom > 0: factor_score += 15
        if mom > 5: factor_score += 10
        
        if vol < 0.03: factor_score += 15
        elif vol < 0.05: factor_score += 10
        
        # 动态风控
        vol_factor = min(2.0, max(0.5, vol / 0.02))
        dyn_tp = params['tp'] * vol_factor
        dyn_sl = params['sl'] * vol_factor
        
        if trend > 2 and mom > 3:
            dyn_tp *= 1.3
            dyn_sl *= 0.8
        
        if factor_score > 50 and rsi < params['rsi_buy']:
            signal = 'BUY'
        elif rsi > params['rsi_sell']:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        signals.append({
            'coin': coin,
            'rsi': rsi,
            'signal': signal,
            'factor_score': factor_score,
            'tp': dyn_tp,
            'sl': dyn_sl,
            'trend': trend,
            'momentum': mom
        })
        
        emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
        print(f"  {emoji} {coin}: RSI={rsi:.1f}, 因子分={factor_score:.0f}, TP={dyn_tp*100:.1f}%, 趋势={trend:.2f}%, 动量={mom:.2f}%")
    
    with open('/home/goose/.openclaw/workspace/logs/g20_1_signals.json', 'w') as f:
        json.dump({'timestamp': datetime.now().isoformat(), 'signals': signals}, f, indent=2)

if __name__ == '__main__':
    main()
