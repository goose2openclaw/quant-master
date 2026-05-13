#!/usr/bin/env python3
"""
G25.4 快速自主优化版
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime
import random

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO']

def api(url):
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return json.loads(opener.open(req, timeout=30).read().decode())
    except: return {}

def price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return float(json.loads(opener.open(req, timeout=10).read().decode())['price'])
    except: return 0

def klines(sym, limit=100):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return [float(k[4]) for k in json.loads(opener.open(req, timeout=15).read().decode())]
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

def backtest(prices, oversold, overbought, stop, take):
    if len(prices) < 100: return 0
    rsi_vals = [calc_rsi(prices[i-50:i]) if i >= 50 else 50 for i in range(len(prices))]
    position = None
    wins, losses = 0, 0
    total = 0
    for i in range(14, len(prices)):
        if position is None:
            if rsi_vals[i] < oversold:
                position = prices[i]
        else:
            pnl = (prices[i] - position) / position
            if pnl <= -stop or pnl >= take or rsi_vals[i] > overbought:
                if pnl > 0: wins += 1
                else: losses += 1
                total += pnl
                position = None
    t = wins + losses
    if t == 0: return 0
    return (wins/t * 0.4 + total/t * 10)

def quick_optimize(coin, is_meme):
    """快速优化"""
    prices = klines(f"{coin}USDT", 500)
    if len(prices) < 300: return None
    
    best_score = 0
    best_params = None
    
    # 网格搜索
    for oversold in [25, 30, 35, 40, 45]:
        for overbought in [55, 60, 65, 70, 75, 80]:
            if oversold >= overbought: continue
            for stop in [0.02, 0.03, 0.05]:
                for take in [0.08, 0.10, 0.15, 0.20, 0.25]:
                    score = backtest(prices, oversold, overbought, stop, take)
                    if score > best_score:
                        best_score = score
                        best_params = {'oversold': oversold, 'overbought': overbought, 'stop': stop, 'take': take}
    
    return best_params, best_score

def main():
    print("=" * 70)
    print("G25.4 快速自主优化")
    print("=" * 70)
    
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] 优化中...\n")
    
    results = {}
    
    # 主流币
    print("[主流币优化]")
    for coin in MAJOR_COINS:
        r = quick_optimize(coin, False)
        if r:
            params, score = r
            results[f"{coin}_major"] = {'params': params, 'score': score}
            print(f"  {coin}: 适应度={score:.3f} RSI({params['oversold']}/{params['overbought']}) SL={params['stop']:.0%} TP={params['take']:.0%}")
    
    # Meme币
    print("\n[Meme币优化]")
    for coin in MEME_COINS[:10]:  # 限制数量加速
        r = quick_optimize(coin, True)
        if r:
            params, score = r
            results[f"{coin}_meme"] = {'params': params, 'score': score}
            print(f"  {coin}: 适应度={score:.3f} RSI({params['oversold']}/{params['overbought']}) SL={params['stop']:.0%} TP={params['take']:.0%}")
    
    # 分析 & 交易
    print(f"\n{'='*70}")
    print("【实时分析】")
    print("=" * 70)
    
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    
    usdt = 0
    if 'balances' in data:
        for b in data['balances']:
            if b['asset'] == 'USDT': usdt = float(b['free'])
    
    print(f"\n账户: USDT=${usdt:.2f}")
    
    # 扫描
    signals = []
    all_coins = list(set(MAJOR_COINS + MEME_COINS[:10]))
    
    for coin in all_coins:
        is_meme = coin in MEME_COINS
        key = f"{coin}_{'meme' if is_meme else 'major'}"
        if key not in results: continue
        
        params = results[key]['params']
        prices = klines(f"{coin}USDT", 50)
        if len(prices) < 20: continue
        
        rsi = calc_rsi(prices)
        h24 = api(f'https://api.binance.com/api/v3/ticker/24hr?symbol={coin}USDT')
        if not h24 or 'lastPrice' not in h24: continue
        
        p = float(h24['lastPrice'])
        chg = float(h24['priceChangePercent'])
        
        if rsi < params['oversold'] and chg < -1:
            signals.append({'coin': coin, 'rsi': rsi, 'chg': chg, 'price': p, 'params': params, 'score': results[key]['score']})
    
    if signals:
        signals.sort(key=lambda x: (x['score'], x['rsi']), reverse=True)
        best = signals[0]
        print(f"\n🏆 最佳信号: {best['coin']}")
        print(f"   RSI={best['rsi']:.1f} 24h={best['chg']:+.1f}%")
        print(f"   参数: RSI({best['params']['oversold']}/{best['params']['overbought']})")
        print(f"   止盈={best['params']['take']:.0%} 止损={best['params']['stop']:.0%}")
        print(f"   适应度: {best['score']:.3f}")
    else:
        print("\n⏸️ 无信号")
    
    print(f"\n{'='*70}")

if __name__ == '__main__':
    main()
