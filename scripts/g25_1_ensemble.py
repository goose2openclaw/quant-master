#!/usr/bin/env python3
"""
G25.1 - Multi-Strategy Ensemble System
=======================================
Nautilus-inspired 多策略集成:
1. RSI策略 (G24核心)
2. MACD策略
3. Bollinger Bands策略
4. 动量策略

投票机制: 多数策略确认才下单
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

TOP_COINS = ['DOGE', 'LINK']
SECOND_TIER = ['ETH', 'SOL']
MAJOR_COINS = ['BTC', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO', '1MBABYDOGE']

def get_config(coin, is_meme=False):
    if coin in TOP_COINS:
        return {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.20, 'position': 0.15}
    elif coin in SECOND_TIER:
        return {'oversold': 40, 'overbought': 75, 'stop': 0.05, 'take': 0.15, 'position': 0.10}
    elif not is_meme:
        return {'oversold': 40, 'overbought': 75, 'stop': 0.03, 'take': 0.10, 'position': 0.10}
    else:
        return {'oversold': 35, 'overbought': 80, 'stop': 0.07, 'take': 0.15, 'position': 0.05}

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

def calc_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow + signal: return 0, 0, 0
    ema_fast = np.mean(prices[-fast:])
    ema_slow = np.mean(prices[-slow:])
    macd = ema_fast - ema_slow
    signal_line = macd  # 简化
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calc_bollinger(prices, period=20):
    if len(prices) < period: return 50, 0
    avg = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    upper = avg + 2*std
    lower = avg - 2*std
    pos = (prices[-1] - lower) / (upper - lower) if upper > lower else 0.5
    return pos, std

def calc_momentum(prices, period=10):
    if len(prices) < period + 1: return 0
    return (prices[-1] / prices[-period-1] - 1) * 100

class EnsembleStrategy:
    def __init__(self):
        self.strategies = ['RSI', 'MACD', 'BB', 'MOM']
        self.weights = {'RSI': 0.35, 'MACD': 0.25, 'BB': 0.20, 'MOM': 0.20}
    
    def vote(self, signals):
        """投票机制: 多数策略确认"""
        buy_votes = sum(1 for s in signals if s == 'BUY')
        sell_votes = sum(1 for s in signals if s == 'SELL')
        
        if buy_votes >= 3: return 'BUY'
        if sell_votes >= 3: return 'SELL'
        if buy_votes == 2 and sell_votes == 0: return 'BUY'
        if sell_votes == 2 and buy_votes == 0: return 'SELL'
        return 'HOLD'
    
    def analyze(self, coin, prices):
        cfg = get_config(coin)
        
        # 各策略信号
        rsi = calc_rsi(prices)
        macd, signal, hist = calc_macd(prices)
        bb_pos, bb_std = calc_bollinger(prices)
        mom = calc_momentum(prices)
        
        signals = []
        
        # RSI信号
        if rsi < cfg['oversold']: signals.append('BUY')
        elif rsi > cfg['overbought']: signals.append('SELL')
        else: signals.append('HOLD')
        
        # MACD信号
        if macd > signal and hist > 0: signals.append('BUY')
        elif macd < signal and hist < 0: signals.append('SELL')
        else: signals.append('HOLD')
        
        # BB信号
        if bb_pos < 0.2: signals.append('BUY')
        elif bb_pos > 0.8: signals.append('SELL')
        else: signals.append('HOLD')
        
        # 动量信号
        if mom > 2: signals.append('BUY')
        elif mom < -2: signals.append('SELL')
        else: signals.append('HOLD')
        
        # 投票
        vote = self.vote(signals)
        confidence = max(buy_votes := sum(1 for s in signals if s == 'BUY'), 
                         sell_votes := sum(1 for s in signals if s == 'SELL')) / 4 * 100
        
        return {
            'coin': coin, 'rsi': rsi, 'macd': macd, 'bb_pos': bb_pos, 'momentum': mom,
            'signals': signals, 'vote': vote, 'confidence': confidence
        }

def backtest():
    print("\n" + "=" * 80)
    print("G25.1 30天回测 - 多策略集成")
    print("=" * 80)
    
    ensemble = EnsembleStrategy()
    all_coins = list(set(TOP_COINS + SECOND_TIER + MAJOR_COINS))
    results = []
    
    for coin in all_coins:
        symbol = f"{coin}USDT"
        prices = klines(symbol, 720, '1h')
        if len(prices) < 500: continue
        
        cfg = get_config(coin)
        position = None
        wins, losses = 0, 0
        total_return = 0
        
        for i in range(50, len(prices)):
            analysis = ensemble.analyze(coin, prices[i-50:i])
            cfg = get_config(coin)
            
            if position is None:
                if analysis['vote'] == 'BUY' and analysis['confidence'] >= 50:
                    position = {'entry': prices[i]}
            else:
                pnl = (prices[i] - position['entry']) / position['entry']
                if pnl <= -cfg['stop'] or pnl >= cfg['take'] or analysis['vote'] == 'SELL':
                    if pnl > 0: wins += 1
                    else: losses += 1
                    total_return += pnl
                    position = None
        
        total = wins + losses
        if total > 0:
            results.append({
                'coin': coin, 'trades': total, 'wins': wins, 'losses': losses,
                'win_rate': wins/total*100, 'total_return': total_return*100
            })
            print(f"{coin:10} 交易:{total:3} 胜:{wins:2} 负:{losses:2} 胜率:{wins/total*100:5.1f}% 收益:{total_return*100:+6.1f}%")
    
    if results:
        avg_wr = sum(r['win_rate'] for r in results) / len(results)
        avg_ret = sum(r['total_return'] for r in results) / len(results)
        print(f"\n汇总: {len(results)}个币, 平均胜率:{avg_wr:.1f}%, 平均收益:{avg_ret:+.1f}%")
    
    return results

if __name__ == '__main__':
    results = backtest()
