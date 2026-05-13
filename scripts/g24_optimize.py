#!/usr/bin/env python3
"""
G24 参数优化
============
目标: 找到最优RSI参数,收益最大化
"""
import urllib.request, json, time
import numpy as np
from itertools import product

PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE']

def api(url):
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except: return None

def get_klines(symbol, days=30, interval='1h'):
    end = int(time.time() * 1000)
    start = end - days * 24 * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start}&endTime={end}&limit=1000'
    data = api(url)
    if data:
        return [float(k[4]) for k in data]
    return []

def calc_rsi(prices, period=14):
    if len(prices) < period + 2: return [50] * len(prices)
    rsi_values = []
    for i in range(len(prices)):
        if i < period:
            rsi_values.append(50)
        else:
            deltas = np.diff(prices[i-period:i+1])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
    return rsi_values

def backtest(prices, oversold, overbought, stop_loss, take_profit):
    if len(prices) < 100: return None
    rsi_values = calc_rsi(prices)
    position = None
    wins = 0
    losses = 0
    total_return = 0
    
    for i in range(50, len(prices)):
        price = prices[i]
        rsi = rsi_values[i]
        
        if position is None:
            if rsi < oversold:
                position = {'entry': price, 'index': i}
        else:
            pnl = (price - position['entry']) / position['entry']
            if pnl <= -stop_loss or pnl >= take_profit or rsi > overbought:
                if pnl > 0: wins += 1
                else: losses += 1
                total_return += pnl
                position = None
    
    if position:
        pnl = (prices[-1] - position['entry']) / position['entry']
        total_return += pnl
        if pnl > 0: wins += 1
        else: losses += 1
    
    total = wins + losses
    if total == 0: return None
    
    return {
        'trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': wins / total * 100,
        'total_return': total_return * 100
    }

def optimize_major():
    print("=" * 80)
    print("优化主流币参数...")
    print("=" * 80)
    
    # 加载数据
    all_prices = {}
    for coin in MAJOR_COINS:
        prices = get_klines(f"{coin}USDT", 30)
        if len(prices) >= 500:
            all_prices[coin] = prices
    
    print(f"加载了 {len(all_prices)} 个币种数据\n")
    
    best_result = None
    best_params = None
    
    # 参数网格
    oversold_range = [25, 30, 35, 40]
    overbought_range = [60, 65, 70, 75]
    stop_range = [0.03, 0.05, 0.07]
    take_range = [0.10, 0.15, 0.20]
    
    total = len(oversold_range) * len(overbought_range) * len(stop_range) * len(take_range)
    print(f"测试 {total} 种组合...\n")
    
    for oversold, overbought, stop, take in product(oversold_range, overbought_range, stop_range, take_range):
        if oversold >= overbought:
            continue
        
        total_return = 0
        total_trades = 0
        valid_coins = 0
        
        for coin, prices in all_prices.items():
            result = backtest(prices, oversold, overbought, stop, take)
            if result and result['trades'] >= 3:
                total_return += result['total_return']
                total_trades += result['trades']
                valid_coins += 1
        
        if valid_coins >= 5:
            avg_return = total_return / valid_coins
            if best_result is None or avg_return > best_result:
                best_result = avg_return
                best_params = (oversold, overbought, stop, take)
                print(f"🟢 新最优: RSI {oversold}/{overbought} SL={stop:.0%} TP={take:.0%} -> 收益{avg_return:+.1f}%")
    
    print(f"\n主流币最优参数:")
    print(f"  RSI超卖: {best_params[0]}")
    print(f"  RSI超买: {best_params[1]}")
    print(f"  止损: {best_params[2]:.0%}")
    print(f"  止盈: {best_params[3]:.0%}")
    print(f"  预期收益: {best_result:+.1f}%")
    
    return best_params, best_result

def optimize_meme():
    print("\n" + "=" * 80)
    print("优化Meme币参数...")
    print("=" * 80)
    
    # 加载数据
    all_prices = {}
    for coin in set(MEME_COINS):
        prices = get_klines(f"{coin}USDT", 30)
        if len(prices) >= 500:
            all_prices[coin] = prices
    
    print(f"加载了 {len(all_prices)} 个币种数据\n")
    
    best_result = None
    best_params = None
    
    # Meme币更激进的参数
    oversold_range = [20, 25, 30, 35]
    overbought_range = [65, 70, 75, 80]
    stop_range = [0.05, 0.07, 0.10]
    take_range = [0.15, 0.20, 0.25, 0.30]
    
    total = len(oversold_range) * len(overbought_range) * len(stop_range) * len(take_range)
    print(f"测试 {total} 种组合...\n")
    
    for oversold, overbought, stop, take in product(oversold_range, overbought_range, stop_range, take_range):
        if oversold >= overbought:
            continue
        
        total_return = 0
        total_trades = 0
        valid_coins = 0
        
        for coin, prices in all_prices.items():
            result = backtest(prices, oversold, overbought, stop, take)
            if result and result['trades'] >= 3:
                total_return += result['total_return']
                total_trades += result['trades']
                valid_coins += 1
        
        if valid_coins >= 8:
            avg_return = total_return / valid_coins
            if best_result is None or avg_return > best_result:
                best_result = avg_return
                best_params = (oversold, overbought, stop, take)
                print(f"🟢 新最优: RSI {oversold}/{overbought} SL={stop:.0%} TP={take:.0%} -> 收益{avg_return:+.1f}%")
    
    print(f"\nMeme币最优参数:")
    print(f"  RSI超卖: {best_params[0]}")
    print(f"  RSI超买: {best_params[1]}")
    print(f"  止损: {best_params[2]:.0%}")
    print(f"  止盈: {best_params[3]:.0%}")
    print(f"  预期收益: {best_result:+.1f}%")
    
    return best_params, best_result

def main():
    print("G24 参数优化")
    print("=" * 80)
    
    major_params, major_result = optimize_major()
    meme_params, meme_result = optimize_meme()
    
    print("\n" + "=" * 80)
    print("优化结果汇总")
    print("=" * 80)
    
    print(f"""
【主流币最优参数】
  RSI超卖: {major_params[0]}
  RSI超买: {major_params[1]}
  止损: {major_params[2]:.0%}
  止盈: {major_params[3]:.0%}

【Meme币最优参数】
  RSI超卖: {meme_params[0]}
  RSI超买: {meme_params[1]}
  止损: {meme_params[2]:.0%}
  止盈: {meme_params[3]:.0%}

预期收益提升:
  主流币: {major_result:+.1f}% (原+5.3%)
  Meme币: {meme_result:+.1f}% (原+15.2%)
""")

if __name__ == '__main__':
    main()
