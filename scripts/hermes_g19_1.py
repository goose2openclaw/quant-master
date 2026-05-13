#!/usr/bin/env python3
"""
G19.1 Hybrid - 混合版本
1. G19核心RSI策略
2. Vibe-Trading多因子选币
3. 动态止盈止损(仅对动量强币种)
"""
import requests, numpy as np, time, json
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

# 全部交易币种
ALL_COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK','AVAX','MATIC','ATOM']

# G19 原始参数 (1000智能体演化结果)
G19_PARAMS = {
    'BTC': {'rsi_buy': 45, 'rsi_sell': 79, 'tp': 0.092, 'sl': 0.034},
    'ETH': {'rsi_buy': 29, 'rsi_sell': 79, 'tp': 0.054, 'sl': 0.042},
    'SOL': {'rsi_buy': 45, 'rsi_sell': 76, 'tp': 0.082, 'sl': 0.054},
    'XRP': {'rsi_buy': 24, 'rsi_sell': 77, 'tp': 0.17, 'sl': 0.048},
    'ADA': {'rsi_buy': 43, 'rsi_sell': 63, 'tp': 0.079, 'sl': 0.025},
    'DOGE': {'rsi_buy': 45, 'rsi_sell': 80, 'tp': 0.07, 'sl': 0.03},
    'LINK': {'rsi_buy': 44, 'rsi_sell': 77, 'tp': 0.06, 'sl': 0.045},
}

# 扩展币种默认参数 (未单独优化的币种用BTC参数)
DEFAULT_PARAMS = {'rsi_buy': 45, 'rsi_sell': 75, 'tp': 0.08, 'sl': 0.035}

def sign(params):
    import hmac, hashlib
    params = dict(params)
    params['recvWindow'] = 5000
    params['timestamp'] = int(time.time()*1000)
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + '&signature=' + sig

def api_get(url, params=None):
    params = params or {}
    r = requests.get(url + '?' + sign(params), headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
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
    if len(prices) < period: return 0.8
    returns = np.diff(prices[-period:]) / prices[-period:-1]
    return np.std(returns) * np.sqrt(365)

def calc_momentum(prices, period=72):
    if len(prices) < period + 1: return 0
    return (prices[-1] - prices[-period-1]) / prices[-period-1] * 100

def calc_trend(prices, period=20):
    if len(prices) < period: return 0
    ma = np.mean(prices[-period:])
    return (prices[-1] - ma) / ma * 100

def multi_factor_rank(coins):
    """Vibe-Trading风格: 多因子选币"""
    rankings = []
    
    for coin in coins:
        prices = get_klines(f'{coin}USDT', 168)  # 7天数据
        if len(prices) < 100: continue
        
        rsi = calc_rsi(prices)
        vol = calc_volatility(prices)
        mom = calc_momentum(prices)
        trend = calc_trend(prices)
        
        # 因子评分
        mom_score = min(100, max(0, 50 + mom * 10))
        trend_score = min(100, max(0, 50 + trend * 5))
        
        if 40 <= rsi <= 60:
            rsi_score = 100
        elif rsi < 40:
            rsi_score = rsi * 2
        else:
            rsi_score = max(0, 100 - (rsi - 60) * 2.5)
        
        vol_score = max(0, 100 - abs(vol - 0.8) * 200) if vol > 0 else 50
        
        total_score = mom_score * 0.4 + trend_score * 0.3 + rsi_score * 0.2 + vol_score * 0.1
        
        # 判断是否高动量 (用于动态止盈止损)
        is_high_momentum = mom > 3 and trend > 0
        
        rankings.append({
            'coin': coin,
            'rsi': rsi,
            'momentum': mom,
            'trend': trend,
            'volatility': vol,
            'total_score': total_score,
            'is_high_momentum': is_high_momentum,
        })
    
    rankings.sort(key=lambda x: x['total_score'], reverse=True)
    return rankings

def dynamic_tp_sl(base_tp, base_sl, momentum, trend):
    """动态止盈止损 - 仅对高动量币种"""
    if momentum > 5 and trend > 0.5:
        # 强趋势: 宽止盈紧止损
        return base_tp * 1.4, base_sl * 0.8
    elif momentum > 2:
        # 中强趋势: 适度调整
        return base_tp * 1.15, base_sl * 0.9
    else:
        # 弱趋势: 保持原参数
        return base_tp, base_sl

def get_coin_params(coin):
    """获取币种参数 (G19优化或默认)"""
    return G19_PARAMS.get(coin, DEFAULT_PARAMS)

def execute_g19_1():
    """执行G19.1混合策略"""
    print("=" * 70)
    print("G19.1 Hybrid - Vibe-Trading增强版")
    print("=" * 70)
    
    # 1. 多因子选币
    rankings = multi_factor_rank(ALL_COINS)
    
    print("\n【多因子选币排名】")
    print(f"{'排名':<4} {'币种':<8} {'总分':<8} {'动量':<8} {'趋势':<8} {'高动量':<8}")
    print("-" * 48)
    for i, r in enumerate(rankings[:7]):
        high_mom = "✅" if r['is_high_momentum'] else "❌"
        print(f"{i+1:<4} {r['coin']:<8} {r['total_score']:<8.1f} {r['momentum']:<+8.2f} {r['trend']:<+8.2f} {high_mom:<8}")
    
    # 2. 生成交易信号
    print("\n【G19.1交易信号】")
    signals = []
    
    for r in rankings[:7]:  # 只交易前7
        coin = r['coin']
        prices = get_klines(f'{coin}USDT', 100)
        if len(prices) < 50: continue
        
        rsi = calc_rsi(prices)
        params = get_coin_params(coin)
        
        # RSI信号
        if rsi < params['rsi_buy']:
            signal = 'BUY'
        elif rsi > params['rsi_sell']:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        # 获取动态止盈止损
        dyn_tp, dyn_sl = dynamic_tp_sl(params['tp'], params['sl'], r['momentum'], r['trend'])
        
        signals.append({
            'coin': coin,
            'rsi': rsi,
            'signal': signal,
            'score': r['total_score'],
            'momentum': r['momentum'],
            'is_high_momentum': bool(r['is_high_momentum']),
            'tp': dyn_tp,
            'sl': dyn_sl,
            'tp_adjusted': abs(dyn_tp - params['tp']) > 0.001,
        })
        
        emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
        tp_emoji = "⚡" if abs(dyn_tp - params['tp']) > 0.001 else ""
        print(f"  {emoji} {coin:<6} RSI:{rsi:5.1f} Signal:{signal:<5} TP:{dyn_tp*100:.1f}% SL:{dyn_sl*100:.1f}% {tp_emoji}")
    
    # 3. 执行交易
    print("\n【执行交易】")
    for s in signals:
        if s['signal'] == 'BUY':
            print(f"  ✅ 买入 {s['coin']} (RSI={s['rsi']:.1f}, TP={s['tp']*100:.1f}%, SL={s['sl']*100:.1f}%)")
        elif s['signal'] == 'SELL':
            print(f"  🔴 卖出 {s['coin']}")
        else:
            print(f"  ⏸️ 观望 {s['coin']}")
    
    # 4. 保存信号
    signal_file = '/home/goose/.openclaw/workspace/logs/g19_1_signals.json'
    # Convert numpy types for JSON serialization
    rankings_json = []
    for r in rankings[:7]:
        rankings_json.append({
            'coin': str(r['coin']),
            'total_score': float(r['total_score']),
            'momentum': float(r['momentum']),
            'trend': float(r['trend']),
            'is_high_momentum': bool(r['is_high_momentum'])
        })
    signals_json = []
    for s in signals:
        signals_json.append({
            'coin': str(s['coin']),
            'rsi': float(s['rsi']),
            'signal': str(s['signal']),
            'score': float(s['score']),
            'momentum': float(s['momentum']),
            'is_high_momentum': bool(s['is_high_momentum']),
            'tp': float(s['tp']),
            'sl': float(s['sl']),
            'tp_adjusted': bool(s['tp_adjusted'])
        })
    with open(signal_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'rankings': rankings_json,
            'signals': signals_json
        }, f, indent=2)
    
    print(f"\n✅ 信号已保存: {signal_file}")
    return signals

if __name__ == '__main__':
    execute_g19_1()
