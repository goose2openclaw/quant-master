#!/usr/bin/env python3
"""
G25 - Event-Driven Modular Trading System
=========================================
基于Nautilus Trader架构灵感:
1. 事件驱动架构
2. 模块化策略组件
3. 多数据源融合
4. 订单簿分析
5. 实时风控

结合G24的RSI策略优化
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime
from collections import defaultdict

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ========== 币种 & 参数 ==========
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

RSI_PERIOD = 14
MIN_VOLUME_MAJOR = 5000000
MIN_VOLUME_MEME = 500000
MAX_POSITIONS = 3

# ========== API工具 ==========
def api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except: return {}

def price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return float(json.loads(opener.open(req, timeout=10).read().decode())['price'])
    except: return 0

def binance_24hr(symbol):
    url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return json.loads(opener.open(req, timeout=10).read().decode())
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

def klines_15m(sym, limit=100):
    return klines(sym, limit, '15m')

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_bollinger(prices, period=20):
    if len(prices) < period: return 50, 50, 50
    avg = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    return avg - 2*std, avg, avg + 2*std

def calc_momentum(prices, period=10):
    if len(prices) < period + 1: return 0
    return (prices[-1] / prices[-period-1] - 1) * 100

# ========== 事件系统 ==========
class Event:
    SIGNAL_GENERATED = "SIGNAL_GENERATED"
    ORDER_EXECUTED = "ORDER_EXECUTED"
    ORDER_CANCELLED = "ORDER_CANCELLED"

class Signal:
    def __init__(self, coin, direction, price, rsi, bb_pos, momentum, strength):
        self.coin = coin
        self.direction = direction  # BUY/SELL
        self.price = price
        self.rsi = rsi
        self.bb_pos = bb_pos
        self.momentum = momentum
        self.strength = strength
        self.timestamp = datetime.now()

class TradingEngine:
    def __init__(self):
        self.signals = []
        self.orders = []
        self.events = defaultdict(list)
    
    def generate_signal(self, coin, direction, price, rsi, bb_pos, momentum, strength):
        sig = Signal(coin, direction, price, rsi, bb_pos, momentum, strength)
        self.signals.append(sig)
        self.events[Event.SIGNAL_GENERATED].append(sig)
        return sig
    
    def emit_order(self, order):
        self.orders.append(order)
        self.events[Event.ORDER_EXECUTED].append(order)

# ========== G25 策略 ==========
class G25Strategy:
    def __init__(self):
        self.engine = TradingEngine()
        self.positions = {}
    
    def analyze_coin(self, coin, is_meme=False):
        symbol = f"{coin}USDT"
        h24 = binance_24hr(symbol)
        if not h24 or 'lastPrice' not in h24: return None
        
        p = float(h24['lastPrice'])
        v = float(h24['quoteVolume'])
        chg = float(h24['priceChangePercent'])
        
        min_vol = MIN_VOLUME_MEME if is_meme else MIN_VOLUME_MAJOR
        if v < min_vol: return None
        
        # 多 timeframe 分析
        prices_1h = klines(symbol, 50, '1h')
        prices_15m = klines_15m(symbol, 50)
        
        if len(prices_1h) < 20 or len(prices_15m) < 20: return None
        
        # 指标计算
        rsi_1h = calc_rsi(prices_1h)
        rsi_15m = calc_rsi(prices_15m)
        rsi_avg = (rsi_1h + rsi_15m) / 2
        
        bb_low, bb_mid, bb_high = calc_bollinger(prices_1h)
        bb_pos = (p - bb_low) / (bb_high - bb_low) if bb_high > bb_low else 0.5
        
        mom_1h = calc_momentum(prices_1h)
        mom_15m = calc_momentum(prices_15m)
        mom_avg = (mom_1h + mom_15m) / 2
        
        # 强度评分
        strength = 0
        config = get_config(coin, is_meme)
        
        # RSI信号
        rsi_score = 0
        if rsi_avg < config['oversold']: rsi_score = 50 - rsi_avg
        elif rsi_avg > config['overbought']: rsi_score = rsi_avg - 50
        
        # 布林带信号
        bb_score = 0
        if bb_pos < 0.2: bb_score = 30
        elif bb_pos > 0.8: bb_score = -30
        
        # 动量信号
        mom_score = mom_avg * 5
        
        strength = rsi_score + bb_score + mom_score
        
        return {
            'coin': coin, 'symbol': symbol, 'price': p,
            'rsi': rsi_avg, 'bb_pos': bb_pos, 'momentum': mom_avg,
            'strength': strength, 'change_24h': chg, 'volume': v,
            'config': config, 'is_meme': is_meme
        }
    
    def should_buy(self, analysis):
        cfg = analysis['config']
        return (analysis['rsi'] < cfg['oversold'] and 
                analysis['change_24h'] < -2 and 
                analysis['strength'] > 20)
    
    def should_sell(self, analysis):
        cfg = analysis['config']
        return (analysis['rsi'] > cfg['overbought'] and 
                analysis['change_24h'] > 2 and 
                analysis['strength'] < -20)
    
    def calculate_position_size(self, analysis, total_capital):
        return total_capital * analysis['config']['position']

def main():
    print("=" * 80)
    print("G25 Event-Driven Modular Trading System")
    print("=" * 80)
    
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{ts}] G25分析\n")
    
    strategy = G25Strategy()
    all_coins = list(set(TOP_COINS + SECOND_TIER + MAJOR_COINS + MEME_COINS))
    
    signals = []
    for coin in all_coins:
        is_meme = coin not in TOP_COINS + SECOND_TIER + MAJOR_COINS
        result = strategy.analyze_coin(coin, is_meme)
        if result:
            if strategy.should_buy(result):
                signals.append(('BUY', result))
            elif strategy.should_sell(result):
                signals.append(('SELL', result))
    
    print(f"发现 {len(signals)} 个信号")
    for sig_type, sig in signals[:5]:
        print(f"  {sig_type}: {sig['coin']} RSI={sig['rsi']:.1f} 强度={sig['strength']:.1f}")
    
    print("\n" + "=" * 80)
    return len(signals)

def backtest():
    """G25 回测"""
    print("\n" + "=" * 80)
    print("G25 30天回测")
    print("=" * 80)
    
    all_coins = list(set(TOP_COINS + SECOND_TIER + MAJOR_COINS))
    results = []
    
    for coin in all_coins:
        symbol = f"{coin}USDT"
        prices = klines(symbol, 720, '1h')  # 30天
        if len(prices) < 500: continue
        
        cfg = get_config(coin)
        oversold, overbought = cfg['oversold'], cfg['overbought']
        stop, take = cfg['stop'], cfg['take']
        
        position = None
        wins, losses = 0, 0
        total_return = 0
        
        for i in range(RSI_PERIOD, len(prices)):
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
        if total > 0:
            wr = wins / total * 100
            ret = total_return * 100
            results.append({'coin': coin, 'trades': total, 'wins': wins, 'losses': losses, 
                          'win_rate': wr, 'total_return': ret})
            print(f"{coin:10} 交易:{total:3} 胜:{wins:2} 负:{losses:2} 胜率:{wr:5.1f}% 收益:{ret:+6.1f}%")
    
    if results:
        avg_wr = sum(r['win_rate'] for r in results) / len(results)
        avg_ret = sum(r['total_return'] for r in results) / len(results)
        total_trades = sum(r['trades'] for r in results)
        print(f"\n汇总: {len(results)}个币, {total_trades}笔交易")
        print(f"平均胜率: {avg_wr:.1f}%")
        print(f"平均收益: {avg_ret:+.1f}%")
    
    return results

if __name__ == '__main__':
    main()
    results = backtest()
