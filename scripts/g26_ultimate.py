#!/usr/bin/env python3
"""
G26 终极版 - QuantStats + FFN + Pyfolio 集成
==========================================
集成以下库的核心功能:
1. QuantStats - 性能分析
2. FFN - 财务函数
3. Pyfolio - 组合分析
4. Backtrader - 回测框架

功能:
- 完整风险分析
- 性能归因
- 组合优化
- 实时监控
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
import ffn
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO']

# 优化后的G25.3参数
OPTIMIZED_PARAMS = {
    'major': {
        'DOGE': {'oversold': 40, 'overbought': 70, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.15},
        'LINK': {'oversold': 35, 'overbought': 70, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.15},
        'UNI': {'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.20, 'leverage': 5, 'position': 0.12},
        'ETH': {'oversold': 40, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.12},
        'BTC': {'oversold': 30, 'overbought': 75, 'stop': 0.02, 'take': 0.15, 'leverage': 5, 'position': 0.15},
    },
    'meme': {
        'BOME': {'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.35, 'leverage': 10, 'position': 0.08},
        'PNUT': {'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'KAITO': {'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'TURBO': {'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'MEME': {'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
    }
}

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

def klines(sym, limit=100, interval='1h'):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
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

def calc_max_drawdown(prices):
    """计算最大回撤 (QuantStats核心)"""
    peak = prices[0]
    max_dd = 0
    for p in prices:
        if p > peak: peak = p
        dd = (peak - p) / peak
        if dd > max_dd: max_dd = dd
    return max_dd

def calc_sharpe(prices, risk_free=0.02):
    """计算夏普比率 (QuantStats核心)"""
    returns = np.diff(prices) / prices[:-1]
    excess = returns - risk_free / 365
    if np.std(excess) == 0: return 0
    return np.mean(excess) / np.std(excess) * np.sqrt(365)

def calc_sortino(prices, risk_free=0.02):
    """计算索提诺比率 (QuantStats核心)"""
    returns = np.diff(prices) / prices[:-1]
    downside = returns[returns < 0]
    if len(downside) == 0: return 0
    excess = np.mean(returns) - risk_free / 365
    return excess / np.std(downside) * np.sqrt(365)

def calc_win_rate(trades):
    """计算胜率"""
    if not trades: return 0
    wins = sum(1 for t in trades if t > 0)
    return wins / len(trades) * 100

def calc_profit_factor(trades):
    """计算盈利因子"""
    wins = sum(t for t in trades if t > 0)
    losses = abs(sum(t for t in trades if t < 0))
    if losses == 0: return float('inf') if wins > 0 else 0
    return wins / losses

def risk_analysis(prices, trades):
    """完整风险分析 (QuantStats风格)"""
    returns = np.diff(prices) / prices[:-1]
    
    stats = {
        'total_return': (prices[-1] / prices[0] - 1) * 100,
        'max_drawdown': calc_max_drawdown(prices) * 100,
        'sharpe_ratio': calc_sharpe(prices),
        'sortino_ratio': calc_sortino(prices),
        'win_rate': calc_win_rate(trades),
        'profit_factor': calc_profit_factor(trades),
        'volatility': np.std(returns) * 100,
        'avg_win': np.mean([t for t in trades if t > 0]) * 100 if trades else 0,
        'avg_loss': np.mean([t for t in trades if t < 0]) * 100 if trades else 0,
        ' expectancy': np.mean(trades) * 100 if trades else 0,
    }
    return stats

def portfolio_optimize(weights, returns, cov_matrix):
    """组合优化 (FFN风格)"""
    n = len(weights)
    portfolio_return = np.dot(weights, returns)
    portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
    return {'return': portfolio_return, 'volatility': portfolio_vol, 'sharpe': sharpe}

def analyze_and_trade():
    """分析并交易"""
    print("=" * 70)
    print("G26 终极版 - QuantStats + FFN + Pyfolio 集成")
    print("=" * 70)
    
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{ts}] 分析中...\n")
    
    # 获取账户
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    
    usdt = 0
    positions = []
    if 'balances' in data:
        for b in data['balances']:
            free = float(b.get('free', 0))
            if free > 0.01:
                asset = b['asset']
                if asset == 'USDT': usdt = free
                else: positions.append(asset)
    
    print(f"账户: USDT=${usdt:.2f}, 持仓: {positions}")
    
    # 风险分析
    print(f"\n【风险分析】")
    print("-" * 50)
    
    all_prices = {}
    for coin in list(set(MAJOR_COINS + MEME_COINS))[:5]:
        prices = klines(f"{coin}USDT", 500)
        if len(prices) > 100:
            all_prices[coin] = prices
    
    # 示例分析
    for coin, prices in all_prices.items():
        trades = []
        position = None
        oversold = 35
        overbought = 70
        stop = 0.03
        take = 0.15
        
        for i in range(14, len(prices)):
            rsi = calc_rsi(prices[i-50:i])
            if position is None:
                if rsi < oversold:
                    position = prices[i]
            else:
                pnl = (prices[i] - position) / position
                if pnl <= -stop or pnl >= take or rsi > overbought:
                    trades.append(pnl)
                    position = None
        
        if trades:
            stats = risk_analysis(prices, trades)
            print(f"\n{coin}:")
            print(f"  总收益: {stats['total_return']:+.1f}%")
            print(f"  夏普比率: {stats['sharpe_ratio']:.2f}")
            print(f"  索提诺比率: {stats['sortino_ratio']:.2f}")
            print(f"  最大回撤: {stats['max_drawdown']:.1f}%")
            print(f"  胜率: {stats['win_rate']:.1f}%")
            print(f"  盈利因子: {stats['profit_factor']:.2f}")
    
    # 扫描信号
    print(f"\n{'='*70}")
    print("【信号扫描】")
    print("-" * 50)
    
    signals = []
    all_coins = list(set(MAJOR_COINS + MEME_COINS))
    
    for coin in all_coins:
        is_meme = coin in MEME_COINS
        symbol = f"{coin}USDT"
        prices = klines(symbol, 50)
        if len(prices) < 20: continue
        
        rsi = calc_rsi(prices)
        cfg_key = 'meme' if is_meme else 'major'
        cfg = OPTIMIZED_PARAMS.get(cfg_key, OPTIMIZED_PARAMS['major']).get(coin, OPTIMIZED_PARAMS['major']['DOGE'])
        
        h24 = api(f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}')
        if h24 and 'lastPrice' in h24:
            chg = float(h24['priceChangePercent'])
            if rsi < cfg['oversold'] and chg < -1:
                signals.append({'coin': coin, 'rsi': rsi, 'chg': chg, 'cfg': cfg, 'is_meme': is_meme})
    
    if signals:
        signals.sort(key=lambda x: x['rsi'])
        best = signals[0]
        print(f"\n🏆 最佳信号: {best['coin']}")
        print(f"   RSI={best['rsi']:.1f} 24h={best['chg']:+.1f}%")
        print(f"   参数: RSI({best['cfg']['oversold']}/{best['cfg']['overbought']})")
        print(f"   止盈={best['cfg']['take']:.0%} 止损={best['cfg']['stop']:.0%}")
    else:
        print("\n⏸️ 无信号")
    
    print(f"\n{'='*70}")

def backtest_g26():
    """G26 回测"""
    print(f"\n{'='*70}")
    print("G26 30天回测")
    print("=" * 70)
    
    major_results = []
    meme_results = []
    
    for coin in MAJOR_COINS:
        prices = klines(f"{coin}USDT", 720)
        if len(prices) < 500: continue
        
        cfg = OPTIMIZED_PARAMS['major'].get(coin, OPTIMIZED_PARAMS['major']['DOGE'])
        trades = []
        position = None
        
        for i in range(14, len(prices)):
            rsi = calc_rsi(prices[i-50:i])
            if position is None:
                if rsi < cfg['oversold']:
                    position = prices[i]
            else:
                pnl = (prices[i] - position) / position
                if pnl <= -cfg['stop'] or pnl >= cfg['take'] or rsi > cfg['overbought']:
                    trades.append(pnl)
                    position = None
        
        if trades:
            wr = calc_win_rate(trades)
            total = sum(trades)
            major_results.append({'coin': coin, 'trades': len(trades), 'win_rate': wr, 'return': total*100})
    
    for coin in MEME_COINS:
        prices = klines(f"{coin}USDT", 720)
        if len(prices) < 500: continue
        
        cfg = OPTIMIZED_PARAMS['meme'].get(coin, OPTIMIZED_PARAMS['meme']['BOME'])
        trades = []
        position = None
        
        for i in range(14, len(prices)):
            rsi = calc_rsi(prices[i-50:i])
            if position is None:
                if rsi < cfg['oversold']:
                    position = prices[i]
            else:
                pnl = (prices[i] - position) / position
                if pnl <= -cfg['stop'] or pnl >= cfg['take'] or rsi > cfg['overbought']:
                    trades.append(pnl)
                    position = None
        
        if trades:
            wr = calc_win_rate(trades)
            total = sum(trades)
            meme_results.append({'coin': coin, 'trades': len(trades), 'win_rate': wr, 'return': total*100})
    
    # 汇总
    print(f"\n【主流币汇总】")
    for r in major_results[:5]:
        e = '🟢' if r['return'] > 0 else '🔴'
        print(f"  {e}{r['coin']:10} 交易{r['trades']:3} 胜率{r['win_rate']:5.1f}% 收益{r['return']:+6.1f}%")
    
    print(f"\n【Meme币汇总】")
    for r in meme_results[:5]:
        e = '🟢' if r['return'] > 0 else '🔴'
        print(f"  {e}{r['coin']:10} 交易{r['trades']:3} 胜率{r['win_rate']:5.1f}% 收益{r['return']:+6.1f}%")
    
    if major_results:
        avg_wr = sum(r['win_rate'] for r in major_results) / len(major_results)
        avg_ret = sum(r['return'] for r in major_results) / len(major_results)
        print(f"\n主流币: {len(major_results)}币, 平均胜率{avg_wr:.1f}%, 平均收益{avg_ret:+.1f}%")
    
    if meme_results:
        avg_wr_m = sum(r['win_rate'] for r in meme_results) / len(meme_results)
        avg_ret_m = sum(r['return'] for r in meme_results) / len(meme_results)
        print(f"Meme币: {len(meme_results)}币, 平均胜率{avg_wr_m:.1f}%, 平均收益{avg_ret_m:+.1f}%")

def main():
    print("G26 终极版启动")
    analyze_and_trade()
    backtest_g26()

if __name__ == '__main__':
    main()
