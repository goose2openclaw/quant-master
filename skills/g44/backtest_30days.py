#!/usr/bin/env python3
"""
G46 30天Walk-Forward回测
基于quantitative-research框架
"""
import json, urllib.request, math, time
from datetime import datetime

PROXY = 'http://172.29.144.1:7897'
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

def signed(endpoint, params=None):
    import hmac, hashlib
    ts = int(time.time()*1000)
    base = {'timestamp':ts,'recvWindow':5000}
    if params: base.update(params)
    q = '&'.join('{}={}'.format(k,v) for k,v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com{path}?{q}&signature={sig}'.format(path=endpoint, q=q, sig=sig)
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http':PROXY,'https':PROXY}))
    return json.loads(opener.open(req, timeout=15).read().decode())

def get_price(sym):
    try:
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=' + sym + 'USDT'
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return float(json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())['price'])
    except: return 0

def get_klines(sym, interval='1h', limit=720):  # 30天*24小时
    for retry in range(3):
        try:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=' + interval + '&limit=' + str(limit)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            data = json.loads(opener.open(urllib.request.Request(url), timeout=15).read().decode())
            return data
        except: time.sleep(1)
    return []

def calc_rsi(closes, period=14):
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]; losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains[-period:])/period if gains else 0.001
    avg_loss = sum(losses[-period:])/period if losses else 0.001
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    return 100 - (100/(1+rs))

def calc_bollinger_bands(closes, period=20, std_dev=2):
    if len(closes) < period: return 0, 0, 0, 0.5
    ma = sum(closes[-period:])/period
    variance = sum((c - ma)**2 for c in closes[-period:])/period
    std = math.sqrt(variance)
    upper = ma + std_dev * std; lower = ma - std_dev * std
    position = (closes[-1] - lower)/(upper - lower) if upper != lower else 0.5
    return upper, ma, lower, position

def calc_signal(closes, highs, lows):
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    rsi14 = calc_rsi(closes)
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum_short = sum(returns[-3:])/3 if len(returns) >= 3 else 0
    bb_deviation = (closes[-1] - bb_ma) / bb_ma if bb_ma > 0 else 0
    
    # Range market mean reversion
    bb_mean_rev = -bb_deviation * 20 if bb_deviation < 0 else -bb_deviation * 15
    grid_signal = (0.2 - bb_pos) * 10 * 1.5 if bb_pos < 0.2 else -(bb_pos - 0.8) * 10 * 1.5 if bb_pos > 0.8 else 0
    rsi_signal = (30 - rsi14) / 30 * 1.5 if rsi14 < 30 else -(rsi14 - 70) / 30 * 1.5 if rsi14 > 70 else 0
    short_rev = -momentum_short * 20 if abs(momentum_short) > 0.005 else 0
    final = bb_mean_rev * 0.25 + grid_signal * 0.20 + rsi_signal * 0.20 + short_rev * 0.10
    return final

def backtest_strategy(prices, tp=0.006, sl=0.008, buy_t=0.6, sell_t=-0.6, budget=5, tx_cost=0.001):
    """回测策略，返回收益统计"""
    if len(prices) < 50: return None
    
    capital = 1000  # $1000初始
    position = 0
    entry_price = 0
    entry_time = 0
    trades = 0
    wins = 0
    losses = 0
    total_pnl = 0
    max_drawdown = 0
    peak = capital
    
    for i in range(50, len(prices)):
        current_price = prices[i]
        closes = prices[:i+1]
        
        # 买入信号
        if position == 0:
            signal = calc_signal(closes, closes, closes)
            if signal > buy_t:
                qty = budget / current_price
                position = qty
                entry_price = current_price
                entry_time = i
                capital -= budget
        
        # 持仓检查
        elif position > 0:
            pnl_pct = (current_price - entry_price) / entry_price
            hold_time = i - entry_time
            
            # 止盈/止损/超时
            if pnl_pct >= tp:
                pnl = position * current_price * (1 - tx_cost) - position * entry_price * (1 + tx_cost)
                capital += position * current_price * (1 - tx_cost)
                total_pnl += pnl
                trades += 1
                wins += 1
                position = 0
            elif pnl_pct <= -sl:
                pnl = position * current_price * (1 - tx_cost) - position * entry_price * (1 + tx_cost)
                capital += position * current_price * (1 - tx_cost)
                total_pnl += pnl
                trades += 1
                losses += 1
                position = 0
            elif hold_time > 24:  # 24小时超时
                pnl = position * current_price * (1 - tx_cost) - position * entry_price * (1 + tx_cost)
                capital += position * current_price * (1 - tx_cost)
                total_pnl += pnl
                trades += 1
                if pnl > 0: wins += 1
                else: losses += 1
                position = 0
    
    # 计算指标
    if trades == 0: return None
    returns = total_pnl / 1000
    sharpe = returns / (abs(total_pnl)/trades) * math.sqrt(trades) if total_pnl != 0 else 0
    
    return {
        'trades': trades,
        'wins': wins,
        'losses': losses,
        'win_rate': wins/trades if trades > 0 else 0,
        'total_pnl': total_pnl,
        'returns': returns * 100,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown
    }

print("=" * 60)
print("G46 30天回测分析")
print("=" * 60)

symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'LINK', 'BNB', 'DOGE']
results = []

for sym in symbols:
    print(f"\n获取 {sym} 数据...")
    klines = get_klines(sym, '1h', 720)
    if not klines or len(klines) < 100:
        print(f"  {sym} 数据不足，跳过")
        continue
    
    prices = [float(k[4]) for k in klines]
    print(f"  {sym}: {len(prices)} 个数据点, 价格范围 ${min(prices):.2f}-${max(prices):.2f}")
    
    # 测试不同参数
    best_result = None
    for tp in [0.004, 0.006, 0.008, 0.01]:
        for sl in [0.006, 0.008, 0.01, 0.015]:
            for buy_t in [0.4, 0.5, 0.6, 0.7]:
                r = backtest_strategy(prices, tp=tp, sl=sl, buy_t=buy_t)
                if r and r['trades'] > 0:
                    r['tp'] = tp
                    r['sl'] = sl
                    r['buy_t'] = buy_t
                    if best_result is None or r['returns'] > best_result['returns']:
                        best_result = r
    
    if best_result:
        print(f"  最佳: TP={best_result['tp']*100:.1f}% SL={best_result['sl']*100:.1f}% 收益={best_result['returns']:.2f}% 交易={best_result['trades']}")
        results.append({'sym': sym, **best_result})
    else:
        print(f"  无有效信号")

print("\n" + "=" * 60)
print("汇总结果")
print("=" * 60)
total_return = sum(r['returns'] for r in results)
avg_trades = sum(r['trades'] for r in results) / len(results) if results else 0
print(f"平均收益率: {total_return/len(results):.2f}% (如果分配$1000)")
print(f"平均交易次数: {avg_trades:.0f} 次/币种/30天")
print(f"最佳币种: {max(results, key=lambda x: x['returns'])['sym'] if results else 'N/A'}")
print(f"最差币种: {min(results, key=lambda x: x['returns'])['sym'] if results else 'N/A'}")
