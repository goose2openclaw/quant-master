#!/usr/bin/env python3
"""
G18 Pro - 高级自适应策略
目标: 收益100%+
优化: 多周期共振 + 动态止损 + 趋势跟踪
"""
import requests, numpy as np, time, json, hmac, hashlib, random
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

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

def get_price(symbol):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(sym, limit=720):
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

def calc_macd(prices):
    if len(prices) < 26: return 0, 0, 0
    ema12 = calc_ema(prices, 12)
    ema26 = calc_ema(prices, 26)
    if ema12 is None or ema26 is None: return 0, 0, 0
    macd = ema12 - ema26
    signal = calc_ema([macd] * 9, 9) if macd != 0 else 0
    histogram = macd - signal if signal else 0
    return macd, signal, histogram

def calc_atr(highs, lows, closes, period=14):
    if len(highs) < period + 1: return 10
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], 
                  abs(highs[i] - closes[i-1]),
                  abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return np.mean(trs[-period:]) if trs else 10

# ========== 高级回测引擎 ==========
def advanced_backtest(prices_data, params):
    """高级回测 - 多指标确认"""
    capital = 100
    position = None
    entry_price = 0
    trades = []
    equity_curve = [100]
    
    for coin, prices in prices_data.items():
        if len(prices) < 200:
            continue
        
        # 多周期确认
        for i in range(100, len(prices)-1):
            p = prices[:i+1]
            p_short = prices[max(0,i-50):i+1]  # 短期
            p_mid = prices[max(0,i-200):i+1] if i > 200 else p  # 中期
            
            # 指标计算
            rsi = calc_rsi(p)
            rsi_short = calc_rsi(p_short)
            
            ema_fast = calc_ema(p, params.get('ema_fast', 12))
            ema_slow = calc_ema(p, params.get('ema_slow', 26))
            ema_trend = calc_ema(p_mid, 50)
            
            macd, signal, hist = calc_macd(p)
            
            # 趋势判断
            current_price = prices[i]
            uptrend = ema_trend and current_price > ema_trend
            downtrend = ema_trend and current_price < ema_trend
            
            # 买入信号 - 多重确认
            buy_signal = (
                rsi < params.get('rsi_buy', 35) and
                rsi_short < 40 and
                macd > signal and
                hist > 0 and
                uptrend
            )
            
            # 卖出信号
            sell_signal = (
                (rsi > params.get('rsi_sell', 70) or rsi_short > 65) and
                (macd < signal or hist < 0)
            ) or (
                position and (current_price - entry_price) / entry_price >= params.get('take_profit', 0.15)
            )
            
            # 止损
            stop_loss = position and (entry_price - current_price) / entry_price >= params.get('stop_loss', 0.05)
            
            # 执行交易
            if position is None and buy_signal:
                position = current_price
                entry_price = current_price
            elif position and (sell_signal or stop_loss):
                pnl = (current_price - position) / position * 100
                capital *= (1 + pnl/100)
                trades.append({'coin': coin, 'pnl': pnl, 'type': 'LONG'})
                equity_curve.append(capital)
                position = None
    
    return {
        'return': capital - 100,
        'trades': len(trades),
        'wins': sum(1 for t in trades if t['pnl'] > 0),
        'losses': sum(1 for t in trades if t['pnl'] <= 0),
        'equity_curve': equity_curve
    }

# ========== 参数优化器 ==========
class Optimizer:
    def __init__(self, prices_data):
        self.prices_data = prices_data
        self.best_return = -999
        self.best_params = None
        self.history = []
    
    def optimize(self, iterations=100):
        """快速随机优化"""
        print(f"🔬 开始优化 ({iterations}次迭代)...")
        
        for i in range(iterations):
            params = self.generate_params()
            result = advanced_backtest(self.prices_data, params)
            ret = result['return']
            
            if ret > self.best_return:
                self.best_return = ret
                self.best_params = params
                print(f"  迭代{i+1}: 新最佳 {ret:+.2f}%")
            
            self.history.append({'params': params, 'return': ret})
        
        return self.best_params, self.best_return
    
    def generate_params(self):
        """生成随机参数组合"""
        return {
            'rsi_buy': random.randint(25, 40),
            'rsi_sell': random.randint(60, 80),
            'ema_fast': random.randint(8, 20),
            'ema_slow': random.randint(20, 50),
            'take_profit': round(random.uniform(0.08, 0.20), 2),
            'stop_loss': round(random.uniform(0.03, 0.08), 2),
            'macd_weight': round(random.uniform(0.1, 0.3), 2),
            'rsi_weight': round(random.uniform(0.2, 0.4), 2),
            'trend_weight': round(random.uniform(0.1, 0.3), 2),
        }

# ========== 主程序 ==========
def main():
    print("=" * 70)
    print("G18 Pro - 高级自适应策略")
    print("=" * 70)
    
    # 加载数据
    print("\n📊 加载数据...")
    prices_data = {}
    for coin in COINS:
        prices = get_klines(f'{coin}USDT', 720)
        if prices:
            prices_data[coin] = prices
            print(f"  {coin}: {len(prices)}条")
    
    # 优化
    optimizer = Optimizer(prices_data)
    best_params, best_return = optimizer.optimize(100)
    
    print(f"\n🏆 最佳参数:")
    print(f"  RSI: {best_params['rsi_buy']}/{best_params['rsi_sell']}")
    print(f"  EMA: {best_params['ema_fast']}/{best_params['ema_slow']}")
    print(f"  止盈: {best_params['take_profit']*100:.0f}%")
    print(f"  止损: {best_params['stop_loss']*100:.0f}%")
    print(f"\n📈 预计收益: {best_return:.2f}%")
    
    # 展示当前信号
    print(f"\n🔍 当前信号:")
    for coin, prices in prices_data.items():
        rsi = calc_rsi(prices)
        macd, signal, hist = calc_macd(prices)
        ema_fast = calc_ema(prices, best_params['ema_fast'])
        ema_slow = calc_ema(prices, best_params['ema_slow'])
        
        score = 0
        if rsi < best_params['rsi_buy']:
            score += 30
        elif rsi > best_params['rsi_sell']:
            score -= 30
        
        if ema_fast and ema_fast > ema_slow:
            score += 20
        elif ema_fast and ema_fast < ema_slow:
            score -= 20
        
        if macd > signal:
            score += 15
        else:
            score -= 15
        
        if hist > 0:
            score += 10
        
        signal = 'BUY' if score > 40 else 'SELL' if score < -20 else 'HOLD'
        emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
        print(f"  {emoji} {coin:6} RSI:{rsi:5.1f} MACD:{'+' if macd>signal else '-'}{abs(macd-signal):.2f} Signal:{signal}")

if __name__ == '__main__':
    main()
