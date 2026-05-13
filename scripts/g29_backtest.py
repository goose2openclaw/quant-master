#!/usr/bin/env python3
"""
G29 30天回测 - 主流币 vs Meme币
"""
import urllib.request, json, time, numpy as np
from datetime import datetime, timedelta

PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC', 'ETH', 'LINK', 'SOL', 'UNI', 'BNB', 'ADA']
MEME_COINS = ['BOME', 'TURBO', 'PUMP', 'NEIRO', 'DOGE', 'SHIB', 'PEPE']

def proxy_get(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    return json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=15).read().decode())

def get_klines(symbol, interval, limit=720):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    try:
        return proxy_get(url)
    except:
        return []

def get_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def get_momentum(prices, hours=24):
    if len(prices) < hours + 1:
        return 0
    return ((prices[-1] - prices[-hours]) / prices[-hours]) * 100

def mirofish_vote(prices, agent_count=1000):
    if len(prices) < 2:
        return {'bull_pct': 50, 'confidence': 0}
    
    returns = [(prices[i+1] - prices[i]) / prices[i] for i in range(len(prices)-1)]
    volatility = np.std(returns) if len(returns) > 1 else 0.01
    trend = np.mean(returns) if returns else 0
    
    bull, bear = 0, 0
    for _ in range(agent_count):
        risk = max(0, min(1, np.random.normal(0.5, 0.2)))
        if trend > volatility * 2:
            bull += 1 if risk > 0.3 else 0.5
            bear += 0.5 if risk <= 0.3 else 0
        elif trend < -volatility * 2:
            bull += 0.5 if risk > 0.7 else 0
            bear += 1 if risk <= 0.7 else 0.5
        else:
            if trend + np.random.normal(0, volatility) > 0:
                bull += 1
            else:
                bear += 1
    
    total = bull + bear
    return {
        'bull_pct': bull / total * 100,
        'confidence': abs(bull - bear) / total
    }

def get_market_type(prices, hours=24):
    if len(prices) < hours:
        return 'neutral'
    highs = [float(k[2]) if isinstance(k, list) else k.get('high', 0) for k in prices[-hours:]]
    lows = [float(k[3]) if isinstance(k, list) else k.get('low', 0) for k in prices[-hours:]]
    closes = [float(k[4]) if isinstance(k, list) else k.get('close', 0) for k in prices[-hours:]]
    
    price_range = (max(highs) - min(lows)) / min(lows) * 100
    trend = ((closes[-1] - closes[0]) / closes[0]) * 100
    
    if price_range < 2 and abs(trend) < 1:
        return 'range'
    elif trend > 3:
        return 'bull'
    elif trend < -3:
        return 'bear'
    elif price_range > 5:
        return 'volatile'
    return 'neutral'

def oracle_decision(rsi, momentum, coin_type, bull_24h, market_type):
    buy_thresh = 35 if coin_type == "meme" else 40
    sell_thresh = 75 if coin_type == "meme" else 70
    
    market_mult = 1.0
    if market_type == 'bear':
        market_mult = 0.7
    elif market_type == 'bull':
        market_mult = 1.3
    elif market_type == 'volatile':
        market_mult = 0.8
    
    score = 0
    if rsi < 25: score += 40
    elif rsi < 30: score += 30
    elif rsi < 35: score += 20
    elif rsi < 40: score += 10
    elif rsi > 75: score -= 40
    elif rsi > 70: score -= 30
    elif rsi > 65: score -= 20
    
    if momentum < -3: score += 20
    elif momentum < -1: score += 10
    elif momentum > 3: score -= 20
    elif momentum > 1: score -= 10
    
    if bull_24h > 70: score -= 15
    elif bull_24h < 30: score += 15
    
    score *= market_mult
    
    if score >= 30: return "STRONG_BUY"
    elif score >= 15: return "BUY"
    elif score <= -30: return "STRONG_SELL"
    elif score <= -15: return "SELL"
    return "HOLD"

def backtest_coin(symbol, coin_type, days=30):
    """回测单个币种"""
    interval = '1h'
    limit = days * 24 + 50
    
    data = get_klines(symbol, interval, limit)
    if len(data) < days * 20:
        return None
    
    closes = [float(k[4]) for k in data]
    
    # 模拟交易
    initial_capital = 1000  # 起始$1000
    capital = initial_capital
    position = 0
    position_entry = 0
    trades = []
    wins, losses = 0, 0
    
    # 从第168个小时开始(有足够的历史数据计算7天指标)
    for i in range(168, len(closes) - 24, 24):  # 每天一个决策
        prices_window = closes[max(0, i-168):i+1]
        prices_24h = closes[max(0, i-24):i+1]
        
        rsi = get_rsi(closes[:i])
        momentum = get_momentum(closes[:i], 24)
        bull = mirofish_vote(prices_24h)
        market = get_market_type(closes[:i], 24)
        decision = oracle_decision(rsi, momentum, coin_type, bull['bull_pct'], market)
        
        price = closes[i]
        
        # 买入
        if decision in ['STRONG_BUY', 'BUY'] and position == 0 and capital >= 50:
            shares = capital / price * 0.95  # 留5%手续费
            position = shares
            position_entry = price
            capital -= shares * price
            trades.append({'action': 'BUY', 'price': price, 'day': i//24})
        
        # 卖出
        elif decision in ['STRONG_SELL', 'SELL'] and position > 0:
            sell_value = position * price
            pnl = sell_value - (position * position_entry)
            pnl_pct = pnl / (position * position_entry) * 100
            
            if pnl > 0:
                wins += 1
            else:
                losses += 1
            
            trades.append({
                'action': 'SELL', 
                'price': price, 
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'day': i//24
            })
            capital += sell_value
            position = 0
    
    # 平仓
    if position > 0:
        final_price = closes[-1]
        pnl = position * (final_price - position_entry)
        if pnl > 0:
            wins += 1
        else:
            losses += 1
        capital += position * final_price
        position = 0
    
    total_trades = wins + losses
    win_rate = wins / total_trades * 100 if total_trades > 0 else 0
    total_return = (capital - initial_capital) / initial_capital * 100
    
    return {
        'coin': symbol.replace('USDT', ''),
        'type': coin_type,
        'initial': initial_capital,
        'final': capital,
        'return': total_return,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'avg_win': np.mean([t['pnl_pct'] for t in trades if t['action'] == 'SELL' and t.get('pnl_pct', 0) > 0]) if wins > 0 else 0,
        'avg_loss': np.mean([t['pnl_pct'] for t in trades if t['action'] == 'SELL' and t.get('pnl_pct', 0) < 0]) if losses > 0 else 0,
    }

def main():
    print("=" * 80)
    print("G29 30天回测 - 主流币 vs Meme币")
    print("=" * 80)
    
    results = []
    
    print("\n📊 回测中...\n")
    
    # 主流币
    print("【主流币】")
    for coin in MAJOR_COINS:
        symbol = f"{coin}USDT"
        print(f"  回测 {coin}...", end=" ", flush=True)
        result = backtest_coin(symbol, 'major', 30)
        if result:
            results.append(result)
            print(f"收益:{result['return']:+.1f}% 胜率:{result['win_rate']:.0f}%")
        else:
            print("数据不足")
    
    # Meme币
    print("\n【Meme币】")
    for coin in MEME_COINS:
        symbol = f"{coin}USDT"
        print(f"  回测 {coin}...", end=" ", flush=True)
        result = backtest_coin(symbol, 'meme', 30)
        if result:
            results.append(result)
            print(f"收益:{result['return']:+.1f}% 胜率:{result['win_rate']:.0f}%")
        else:
            print("数据不足")
    
    # 汇总
    print("\n" + "=" * 80)
    print("【30天回测数据矩阵】")
    print("=" * 80)
    
    major_results = [r for r in results if r['type'] == 'major']
    meme_results = [r for r in results if r['type'] == 'meme']
    
    # 表格
    print(f"\n{'币种':<10} {'类型':<8} {'收益':<10} {'胜率':<8} {'交易次数':<10} {'盈亏比':<10}")
    print("-" * 60)
    for r in sorted(results, key=lambda x: x['return'], reverse=True):
        print(f"{r['coin']:<10} {r['type']:<8} {r['return']:>+8.1f}% {r['win_rate']:>5.1f}% {r['total_trades']:>8} {r['avg_win']/-r['avg_loss'] if r['avg_loss'] != 0 else 0:>8.2f}")
    
    # 分组汇总
    if major_results:
        avg_return_major = sum(r['return'] for r in major_results) / len(major_results)
        avg_winrate_major = sum(r['win_rate'] for r in major_results) / len(major_results)
        total_trades_major = sum(r['total_trades'] for r in major_results)
        print(f"\n【主流币汇总】")
        print(f"  平均收益: {avg_return_major:+.1f}%")
        print(f"  平均胜率: {avg_winrate_major:.1f}%")
        print(f"  总交易次数: {total_trades_major}")
    
    if meme_results:
        avg_return_meme = sum(r['return'] for r in meme_results) / len(meme_results)
        avg_winrate_meme = sum(r['win_rate'] for r in meme_results) / len(meme_results)
        total_trades_meme = sum(r['total_trades'] for r in meme_results)
        print(f"\n【Meme币汇总】")
        print(f"  平均收益: {avg_return_meme:+.1f}%")
        print(f"  平均胜率: {avg_winrate_meme:.1f}%")
        print(f"  总交易次数: {total_trades_meme}")
    
    # 总体
    if results:
        avg_return_all = sum(r['return'] for r in results) / len(results)
        avg_winrate_all = sum(r['win_rate'] for r in results) / len(results)
        print(f"\n【总体汇总】")
        print(f"  平均收益: {avg_return_all:+.1f}%")
        print(f"  平均胜率: {avg_winrate_all:.1f}%")
        print(f"  总交易次数: {sum(r['total_trades'] for r in results)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
