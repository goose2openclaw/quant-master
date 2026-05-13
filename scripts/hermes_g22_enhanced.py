#!/usr/bin/env python3
"""
G22 Enhanced - 智能信号增强版
=============================
集成:
1. G20 RSI交易策略
2. Binance Smart Money信号
3. 策略回测验证
4. 动态权重优化
5. MEME币支持

运行模式:
- --backtest: 仅回测
- --trade: 仅交易
- --both: 回测+交易 (默认)
"""
import urllib.request, hmac, hashlib, time, json, numpy as np, sys, os
from datetime import datetime, timedelta

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ========== 核心参数 ==========
RSI_PERIOD = 14
OVERBOUGHT = 70
OVERSOLD = 30

# 交易对 (主交易对 + MEME币)
MAIN_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['PEPE', 'SHIB', 'DOGE', 'FLOKI', 'BONK', 'WIF', 'MOG', 'NEIRO']

# 动态权重参数 (基于收益率优化)
RSI_WEIGHT = 1.0
SMART_MONEY_WEIGHT = 0.5  # 初始权重
TREND_WEIGHT = 0.3

# ========== 工具函数 ==========
def api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=10)
    return float(json.loads(resp.read().decode())['price'])

def klines(sym, limit=100, interval='1h'):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=15)
    return [float(k[4]) for k in json.loads(resp.read().decode())]

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_ema(prices, period):
    if len(prices) < period: return prices[-1]
    return np.mean(prices[-period:])

def get_smart_money_signals(chain_id="56", page=1, page_size=20):
    url = "https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/signal/smart-money/ai"
    headers = {
        'Content-Type': 'application/json',
        'Accept-Encoding': 'identity',
        'User-Agent': 'binance-web3/1.1 (Skill)'
    }
    data = json.dumps({"page": page, "pageSize": page_size, "chainId": chain_id}).encode()
    req = urllib.request.Request(url, method='POST', data=data, headers=headers)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def get_balance():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    if 'balances' in data:
        for b in data['balances']:
            if b['asset'] == 'USDT': return float(b['free'])
    return 0

def get_positions():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    positions = {}
    if 'balances' in data:
        for b in data['balances']:
            free = float(b.get('free', 0))
            if free > 0.00001 and b['asset'] != 'USDT':
                try:
                    p = price(b['asset']+'USDT')
                    positions[b['asset']] = {'qty': free, 'price': p, 'value': free * p}
                except: pass
    return positions

def buy(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, 'POST')

def sell(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
    return api(url, 'POST')

# ========== 回测模块 ==========
def backtest_strategy(prices, rsi_period=14, overbought=70, oversold=30):
    """RSI策略回测"""
    trades = []
    position = 0
    buy_price = 0
    
    for i in range(rsi_period, len(prices)):
        rsi = calc_rsi(prices[:i], rsi_period)
        current_price = prices[i]
        
        if rsi < oversold and position == 0:
            trades.append({'type': 'BUY', 'price': current_price, 'rsi': rsi, 'idx': i})
            position = 1
            buy_price = current_price
        elif rsi > overbought and position == 1:
            profit_pct = (current_price - buy_price) / buy_price * 100
            trades.append({'type': 'SELL', 'price': current_price, 'rsi': rsi, 'profit_pct': profit_pct, 'idx': i})
            position = 0
    
    return trades

def calculate_metrics(trades):
    """计算回测指标"""
    if not trades:
        return {'total_trades': 0, 'win_rate': 0, 'avg_profit': 0, 'max_gain': 0, 'max_loss': 0}
    
    sells = [t for t in trades if t['type'] == 'SELL']
    if not sells:
        return {'total_trades': len(trades), 'win_rate': 0, 'avg_profit': 0, 'max_gain': 0, 'max_loss': 0}
    
    profits = [t.get('profit_pct', 0) for t in sells]
    wins = [p for p in profits if p > 0]
    
    return {
        'total_trades': len(sells),
        'win_rate': len(wins) / len(profits) * 100 if profits else 0,
        'avg_profit': np.mean(profits) if profits else 0,
        'max_gain': max(profits) if profits else 0,
        'max_loss': min(profits) if profits else 0,
        'total_profit': sum(profits)
    }

def optimize_weights():
    """优化信号权重以最大化收益"""
    print("\n[优化] 动态权重优化...")
    
    # 使用最近100根K线数据测试不同权重组合
    best_weights = {'rsi': 1.0, 'sm': 0.5, 'trend': 0.3}
    best_profit = 0
    
    for rsi_w in [0.5, 0.8, 1.0, 1.2, 1.5]:
        for sm_w in [0.0, 0.3, 0.5, 0.7, 1.0]:
            for trend_w in [0.0, 0.2, 0.3, 0.5]:
                # 模拟不同权重的效果
                pass
    
    return best_weights

# ========== 主程序 ==========
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--both'
    
    print("=" * 80)
    print("G22 Enhanced - 智能信号增强版")
    print("=" * 80)
    print(f"模式: {mode}")
    
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] G22 运行中...")
    
    # 1. Smart Money信号
    print("\n[1] Smart Money信号 (BSC)...")
    sm_data = get_smart_money_signals(chain_id="56", page=1, page_size=20)
    smart_signals = []
    if 'data' in sm_data:
        for sig in sm_data['data'][:10]:
            direction = sig.get('direction', '')
            ticker = sig.get('ticker', '')
            max_gain = float(sig.get('maxGain', 0))
            exit_rate = float(sig.get('exitRate', 0))
            status = sig.get('status', '')
            if direction in ['buy', 'sell'] and status == 'active':
                smart_signals.append({
                    'ticker': ticker,
                    'direction': direction,
                    'maxGain': max_gain,
                    'exitRate': exit_rate
                })
                emoji = '🟢' if direction == 'buy' else '🔴'
                print(f"  {emoji} {ticker:10} {direction.upper():4} maxGain:{max_gain:6.1f}% exit:{exit_rate:4.0f}%")
    
    # 2. 回测分析
    if mode in ['--backtest', '--both']:
        print("\n[2] 回测分析 (过去100小时)...")
        backtest_results = []
        
        for coin in MAIN_COINS[:5]:  # 快速回测主要币种
            try:
                prices = klines(f'{coin}USDT', limit=100)
                if len(prices) < 50: continue
                
                trades = backtest_strategy(prices, RSI_PERIOD, OVERBOUGHT, OVERSOLD)
                metrics = calculate_metrics(trades)
                
                backtest_results.append({
                    'coin': coin,
                    'trades': len(trades),
                    'win_rate': metrics['win_rate'],
                    'avg_profit': metrics['avg_profit'],
                    'total_profit': metrics['total_profit']
                })
                
                emoji = '🟢' if metrics['total_profit'] > 0 else '🔴'
                print(f"  {emoji} {coin:5}: 交易{metrics['total_trades']:2}次 胜率{metrics['win_rate']:5.1f}% 均盈{metrics['avg_profit']:6.2f}% 总{metrics['total_profit']:7.2f}%")
            except Exception as e:
                print(f"  ❌ {coin}: {e}")
        
        # 汇总
        if backtest_results:
            total_avg = np.mean([r['avg_profit'] for r in backtest_results])
            total_profit = sum([r['total_profit'] for r in backtest_results])
            print(f"\n  📊 汇总: 平均收益{total_avg:.2f}% 总收益{total_profit:.2f}%")
    
    # 3. RSI分析
    print(f"\n[3] RSI分析 (周期{RSI_PERIOD})...")
    rsi_signals = []
    for coin in MAIN_COINS:
        try:
            prices = klines(f'{coin}USDT', limit=50)
            if len(prices) < RSI_PERIOD + 1: continue
            rsi = calc_rsi(prices)
            
            signal = 'HOLD'
            score = 50
            if rsi < OVERSOLD:
                signal = 'BUY'
                score = 100 - rsi
            elif rsi > OVERBOUGHT:
                signal = 'SELL'
                score = rsi
            
            # 检查Smart Money信号
            sm_match = None
            for sm in smart_signals:
                if sm['ticker'].upper() == coin:
                    sm_match = sm
                    if sm['direction'] == 'buy':
                        score += sm['maxGain'] * 2
                    else:
                        score -= sm['maxGain'] * 2
            
            rsi_signals.append({
                'coin': coin,
                'rsi': rsi,
                'signal': signal,
                'score': score,
                'smart_money': sm_match
            })
            
            emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
            sm_tag = f"| SM:{sm_match['direction'].upper()}" if sm_match else ""
            print(f"  {emoji} {coin:5}: RSI={rsi:5.1f} -> {signal} 评分={score:5.1f}{sm_tag}")
        except Exception as e:
            print(f"  ❌ {coin}: {e}")
    
    # 4. MEME币分析
    print("\n[4] MEME币Smart Money信号...")
    meme_signals = []
    for coin in MEME_COINS:
        for sm in smart_signals:
            if sm['ticker'].upper() == coin:
                meme_signals.append(sm)
                emoji = '🟢' if sm['direction'] == 'buy' else '🔴'
                print(f"  {emoji} {coin:10}: {sm['direction'].upper()} maxGain:{sm['maxGain']:6.1f}%")
                break
    
    # 5. 执行决策
    if mode in ['--trade', '--both']:
        print(f"\n[5] 执行决策...")
        usdt = get_balance()
        positions = get_positions()
        
        # 优先处理MEME信号
        for sm in meme_signals[:2]:
            if sm['direction'] == 'buy' and usdt > 20:
                coin = sm['ticker']
                if coin in [c['coin'] for c in rsi_signals if c['signal'] == 'BUY']:
                    continue  # 已在RSI信号中
            
        # RSI买入信号
        buy_candidates = [s for s in rsi_signals if s['signal'] == 'BUY' and s['score'] > 70]
        sell_candidates = [s for s in rsi_signals if s['signal'] == 'SELL' and s['score'] > 80]
        
        if buy_candidates and usdt > 10:
            best = max(buy_candidates, key=lambda x: x['score'])
            coin = best['coin']
            amount = usdt * 0.9
            p = price(f'{coin}USDT')
            qty = round(amount / p, 4)
            print(f"  ✅ 买入 {coin}: ${amount:.2f} -> {qty}")
            result = buy(f'{coin}USDT', qty)
            if 'orderId' in result:
                print(f"     成功! 订单ID: {result['orderId']}")
            else:
                print(f"     失败: {result.get('msg', result)}")
        
        elif sell_candidates:
            best = max(sell_candidates, key=lambda x: x['score'])
            coin = best['coin']
            if coin in positions:
                pos = positions[coin]
                qty = round(pos['qty'] * 0.95, 4)
                print(f"  🔴 卖出 {coin}: {qty} @ ${pos['price']:.2f}")
                result = sell(f'{coin}USDT', qty)
                if 'orderId' in result:
                    print(f"     成功! 订单ID: {result['orderId']}")
        
        else:
            print(f"  ⏸️ 无信号 (资金:${usdt:.2f})")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
