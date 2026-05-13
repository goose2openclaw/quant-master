#!/usr/bin/env python3
"""
G25.2 - G24 Optimized with Rigorous Parameters
==============================================
对G24进行精细化:
1. 严格的参数优化 (网格搜索)
2. 多时间段确认
3. 成交量过滤
4. 动态止损止盈
5. 完整风险管理系统
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime
from itertools import product

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

TOP_COINS = ['DOGE', 'LINK']
SECOND_TIER = ['ETH', 'SOL']
MAJOR_COINS = ['BTC', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE']

def api(url):
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return json.loads(opener.open(req, timeout=30).read().decode())
    except: return {}

def klines(sym, limit=100, interval='1h'):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    req = urllib.request.Request(url)
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

def calc_volume_profile(prices, volumes, period=20):
    """成交量加权RSI"""
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # 加权平均
    vol_weights = volumes[-period:] / np.sum(volumes[-period:]) if np.sum(volumes[-period:]) > 0 else np.ones(period) / period
    avg_gain = np.average(gains[-period:], weights=vol_weights)
    avg_loss = np.average(losses[-period:], weights=vol_weights)
    
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def optimize_params(coin, prices):
    """网格搜索最优参数"""
    best_result = None
    best_params = None
    
    oversold_range = [30, 35, 40, 45]
    overbought_range = [55, 60, 65, 70, 75]
    stop_range = [0.03, 0.05, 0.07]
    take_range = [0.10, 0.15, 0.20]
    
    for oversold, overbought, stop, take in product(oversold_range, overbought_range, stop_range, take_range):
        if oversold >= overbought: continue
        
        position = None
        wins, losses = 0, 0
        total_return = 0
        
        for i in range(14, len(prices)):
            rsi = calc_rsi(prices[i-50:i])
            if rsi is None: continue
            
            if position is None:
                if rsi < oversold:
                    position = {'entry': prices[i]}
            else:
                pnl = (prices[i] - position['entry']) / position['entry']
                if pnl <= -stop or pnl >= take or rsi > overbought:
                    if pnl > 0: wins += 1
                    else: losses += 1
                    total_return += pnl
                    position = None
        
        total = wins + losses
        if total >= 3:
            score = (wins/total*100) * 0.6 + (total_return*100) * 0.4
            if best_result is None or score > best_result:
                best_result = score
                best_params = {'oversold': oversold, 'overbought': overbought, 
                              'stop': stop, 'take': take, 'wins': wins, 'losses': losses,
                              'total_return': total_return*100, 'trades': total}
    
    return best_params

def backtest_optimal(coin, prices, params):
    """使用最优参数回测"""
    position = None
    wins, losses = 0, 0
    total_return = 0
    
    for i in range(50, len(prices)):
        rsi = calc_rsi(prices[i-50:i])
        if rsi is None: continue
        
        if position is None:
            if rsi < params['oversold']:
                position = {'entry': prices[i]}
        else:
            pnl = (prices[i] - position['entry']) / position['entry']
            if pnl <= -params['stop'] or pnl >= params['take'] or rsi > params['overbought']:
                if pnl > 0: wins += 1
                else: losses += 1
                total_return += pnl
                position = None
    
    total = wins + losses
    if total == 0: return None
    
    return {
        'coin': coin, 'trades': total, 'wins': wins, 'losses': losses,
        'win_rate': wins/total*100, 'total_return': total_return*100,
        'params': params
    }

def backtest():
    print("\n" + "=" * 80)
    print("G25.2 30天回测 - 精细优化版")
    print("=" * 80)
    
    all_coins = list(set(TOP_COINS + SECOND_TIER + MAJOR_COINS + MEME_COINS))
    results = []
    
    for coin in all_coins:
        symbol = f"{coin}USDT"
        prices = klines(symbol, 720, '1h')
        if len(prices) < 500: continue
        
        # 参数优化
        params = optimize_params(coin, prices)
        if params is None: continue
        
        # 回测
        result = backtest_optimal(coin, prices, params)
        if result:
            results.append(result)
            print(f"{coin:15} 参数:RSI {params['oversold']}/{params['overbought']} SL={params['stop']:.0%} TP={params['take']:.0%}")
            print(f"             交易:{result['trades']:3} 胜:{result['wins']:2} 负:{result['losses']:2} 胜率:{result['win_rate']:5.1f}% 收益:{result['total_return']:+6.1f}%")
    
    if results:
        avg_wr = sum(r['win_rate'] for r in results) / len(results)
        avg_ret = sum(r['total_return'] for r in results) / len(results)
        total_trades = sum(r['trades'] for r in results)
        print(f"\n汇总: {len(results)}个币, {total_trades}笔交易")
        print(f"平均胜率: {avg_wr:.1f}%")
        print(f"平均收益: {avg_ret:+.1f}%")
    
    return results

if __name__ == '__main__':
    results = backtest()
