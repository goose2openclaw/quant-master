#!/usr/bin/env python3
"""
G26 自主迭代版 - 实盘操作
==========================
基于G26_autonomous.py, 增加实盘交易功能

Heremes指令 (2026-05-11):
- 同步到G26自主迭代版
- 进行实盘操作
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime
import random

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI']
MEME_COINS = ['DOGE', 'PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO']

PARAMS = {
    'major': {
        'BTC': {'oversold': 30, 'overbought': 75, 'stop': 0.02, 'take': 0.15, 'leverage': 5, 'position': 0.15},
        'ETH': {'oversold': 40, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.12},
        'SOL': {'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.20, 'leverage': 5, 'position': 0.10},
        'DOGE': {'oversold': 40, 'overbought': 70, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.15},
        'LINK': {'oversold': 35, 'overbought': 70, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.15},
        'XRP': {'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10},
        'ADA': {'oversold': 30, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10},
        'AVAX': {'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10},
        'DOT': {'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10},
        'UNI': {'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.20, 'leverage': 5, 'position': 0.12},
    },
    'meme': {
        'DOGE': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'PEPE': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'PENGU': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'BONK': {'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'SHIB': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'TRUMP': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'PUMP': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'WIF': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'FLOKI': {'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'NEIRO': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'VANA': {'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'PNUT': {'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'BOME': {'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.35, 'leverage': 10, 'position': 0.08},
        'TURBO': {'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'MEME': {'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
        'KAITO': {'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08},
    }
}

MONTE_CARLO_AGENTS = 500
SIGNAL_THRESHOLD = 60
CONFIDENCE_THRESHOLD = 75

def api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return json.loads(opener.open(req, timeout=30).read().decode())
    except: return {}

def signed_api(endpoint, params=None):
    """带签名的API请求"""
    ts = int(time.time() * 1000)
    base_params = {"timestamp": ts}
    if params: base_params.update(params)
    
    q = "&".join(f"{k}={v}" for k, v in base_params.items())
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    return api(url)

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url)
    try: return float(json.loads(opener.open(req, timeout=10).read().decode())['price'])
    except: return 0

def get_account():
    """获取账户信息"""
    return signed_api("/api/v3/account")

def get_open_orders(symbol=None):
    """获取未完成订单"""
    params = {}
    if symbol: params['symbol'] = symbol
    return signed_api("/api/v3/openOrders", params)

def place_order(symbol, side, order_type, quantity, price=None, stop_price=None):
    """下单"""
    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }
    if price: params["price"] = price
    if stop_price: params["stopPrice"] = stop_price
    
    return signed_api("/api/v3/order", params)

def klines(sym, limit=720):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url)
    try: return [float(k[4]) for k in json.loads(opener.open(req, timeout=30).read().decode())]
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

def backtest_coin(coin, params, days=30):
    prices = klines(f"{coin}USDT", days * 24)
    if len(prices) < days * 20: return None
    
    oversold = params['oversold']
    overbought = params['overbought']
    stop = params['stop']
    take = params['take']
    
    position = None
    entry_price = 0
    trades = []
    
    for i in range(14, len(prices)):
        rsi = calc_rsi(prices[i-50:i]) if i >= 50 else 50
        
        if position is None:
            if rsi < oversold:
                position = True
                entry_price = prices[i]
        else:
            pnl = (prices[i] - entry_price) / entry_price
            if pnl <= -stop or pnl >= take or rsi > overbought:
                trades.append(pnl)
                position = None
    
    if not trades: return None
    
    wins = sum(1 for t in trades if t > 0)
    total_return = sum(trades) * 100
    win_rate = wins / len(trades) * 100 if trades else 0
    
    return {
        'coin': coin,
        'trades': len(trades),
        'wins': wins,
        'win_rate': win_rate,
        'total_return': total_return,
    }

def generate_top5():
    print("\n" + "=" * 70)
    print("【步骤1: 扫描所有币种, 生成TOP5】")
    print("=" * 70)
    
    all_results = []
    
    for coin in MAJOR_COINS:
        cfg = PARAMS['major'].get(coin)
        if not cfg: continue
        r = backtest_coin(coin, cfg, 30)
        if r:
            r['type'] = 'major'
            all_results.append(r)
            print(f"  {coin}: 收益{r['total_return']:+.1f}%, 胜率{r['win_rate']:.1f}%")
    
    for coin in MEME_COINS:
        cfg = PARAMS['meme'].get(coin)
        if not cfg: continue
        r = backtest_coin(coin, cfg, 30)
        if r:
            r['type'] = 'meme'
            all_results.append(r)
            print(f"  {coin}: 收益{r['total_return']:+.1f}%, 胜率{r['win_rate']:.1f}%")
    
    if not all_results:
        print("  ⚠️ 无数据")
        return []
    
    all_results.sort(key=lambda x: x['total_return'], reverse=True)
    top5 = all_results[:5]
    
    print(f"\n🏆 TOP5 收益币种:")
    for i, r in enumerate(top5, 1):
        print(f"  {i}. {r['coin']} ({r['type']}) 收益{r['total_return']:+.1f}%, 胜率{r['win_rate']:.1f}%")
    
    return top5

def review_and_simulate(top5):
    print(f"\n{'='*70}")
    print(f"【步骤2: 复盘 + Mirofish {MONTE_CARLO_AGENTS}智能体仿真】")
    print("=" * 70)
    
    decisions = []
    
    for coin_data in top5:
        coin = coin_data['coin']
        print(f"\n📊 {coin} 仿真中...")
        
        prices = klines(f"{coin}USDT", 720)
        if len(prices) < 500:
            print(f"  ⚠️ 数据不足")
            continue
        
        rsi_vals = [calc_rsi(prices[i-50:i]) if i >= 50 else 50 for i in range(len(prices))]
        current_rsi = rsi_vals[-1]
        
        momentum_1h = (prices[-1] / prices[-2] - 1) * 100 if len(prices) >= 2 else 0
        momentum_24h = (prices[-1] / prices[-24] - 1) * 100 if len(prices) >= 24 else 0
        
        print(f"  RSI: {current_rsi:.1f}, 1h动量: {momentum_1h:+.2f}%, 24h动量: {momentum_24h:+.2f}%")
        
        wins = 0
        total_return = 0
        simulation_results = []
        
        for agent in range(MONTE_CARLO_AGENTS):
            rsi_buy = random.randint(25, 40)
            rsi_sell = random.randint(65, 80)
            stop_loss = random.uniform(0.02, 0.08)
            take_profit = random.uniform(0.10, 0.40)
            
            position = None
            agent_return = 0
            agent_trades = 0
            
            for i in range(100, len(prices)):
                rsi = rsi_vals[i]
                
                if position is None:
                    if rsi < rsi_buy:
                        position = prices[i]
                else:
                    pnl = (prices[i] - position) / position
                    if pnl <= -stop_loss or pnl >= take_profit or rsi > rsi_sell:
                        agent_return += pnl
                        agent_trades += 1
                        position = None
            
            if agent_trades > 0:
                wins += 1 if agent_return > 0 else 0
                total_return += agent_return
                simulation_results.append(agent_return)
        
        win_rate_sim = wins / MONTE_CARLO_AGENTS * 100
        avg_return_sim = total_return / MONTE_CARLO_AGENTS * 100
        
        simulation_results.sort()
        percentile_95 = simulation_results[int(len(simulation_results) * 0.95)] * 100 if simulation_results else 0
        
        print(f"  仿真: {MONTE_CARLO_AGENTS}智能体, 胜率{win_rate_sim:.1f}%, 平均收益{avg_return_sim:+.2f}%, 95%分位{percentile_95:+.2f}%")
        
        signal_strength = win_rate_sim
        confidence = percentile_95 if percentile_95 > 0 else avg_return_sim
        
        if signal_strength >= SIGNAL_THRESHOLD and confidence >= 0:
            decision = 'BUY'
        elif signal_strength < 40 or confidence < -5:
            decision = 'SELL'
        else:
            decision = 'HOLD'
        
        print(f"  决策: {decision} (信号强度:{signal_strength:.1f}%, 置信度:{confidence:+.2f}%)")
        
        decisions.append({
            'coin': coin,
            'decision': decision,
            'signal_strength': signal_strength,
            'confidence': confidence,
            'rsi': current_rsi,
            'momentum_24h': momentum_24h,
            'win_rate': coin_data['win_rate'],
            'total_return': coin_data['total_return'],
        })
    
    return decisions

def auto_execute(decisions):
    """自动执行实盘交易"""
    print(f"\n{'='*70}")
    print("【步骤3: 实盘执行】")
    print("=" * 70)
    
    account = get_account()
    usdt = 0
    positions = {}
    if 'balances' in account:
        for b in account['balances']:
            free = float(b.get('free', 0))
            if free > 0.01:
                asset = b['asset']
                if asset == 'USDT':
                    usdt = free
                else:
                    positions[asset] = free
    
    print(f"\n账户: USDT=${usdt:.2f}")
    print(f"现货持仓: {list(positions.keys())}")
    
    buy_signals = [d for d in decisions if d['decision'] == 'BUY']
    sell_signals = [d for d in decisions if d['decision'] == 'SELL']
    
    executed = []
    
    # 执行买入
    if buy_signals and usdt > 10:
        print(f"\n📈 买入信号 ({len(buy_signals)}个):")
        
        # 分配资金: 最多同时持有3个币
        max_positions = 3
        buy_count = min(len(buy_signals), max_positions)
        allocation = usdt / buy_count
        
        for sig in buy_signals[:buy_count]:
            coin = sig['coin']
            symbol = f"{coin}USDT"
            
            # 获取当前价格
            current_price = get_price(symbol)
            if current_price == 0: continue
            
            # 计算数量 (现货买入)
            quantity = allocation / current_price
            
            # 保留精度
            if coin in ['BTC', 'ETH']:
                quantity = round(quantity, 4)
            else:
                quantity = round(quantity, 0)
            
            if quantity < 10:  # 最低下单量
                print(f"  ⚠️ {coin}: 数量{quantity}太少, 跳过")
                continue
            
            # 获取参数
            is_meme = coin in MEME_COINS
            cfg = PARAMS['meme'].get(coin, PARAMS['major'].get(coin))
            
            print(f"\n  买入 {coin}:")
            print(f"    数量: {quantity}")
            print(f"    价格: ${current_price}")
            print(f"    金额: ${allocation:.2f}")
            print(f"    RSI: {sig['rsi']:.1f}")
            print(f"    信号强度: {sig['signal_strength']:.1f}%")
            
            # 实际下单
            try:
                order = place_order(symbol, 'BUY', 'MARKET', quantity)
                if 'orderId' in order:
                    print(f"    ✅ 下单成功! OrderID: {order['orderId']}")
                    executed.append({'coin': coin, 'side': 'BUY', 'quantity': quantity, 'price': current_price})
                else:
                    print(f"    ❌ 下单失败: {order}")
            except Exception as e:
                print(f"    ❌ 错误: {e}")
    
    # 执行卖出
    if sell_signals:
        print(f"\n📉 卖出信号 ({len(sell_signals)}个):")
        for sig in sell_signals:
            coin = sig['coin']
            if coin not in positions:
                print(f"  ⚠️ {coin}: 无持仓, 跳过")
                continue
            
            symbol = f"{coin}USDT"
            quantity = positions[coin]
            current_price = get_price(symbol)
            
            if current_price == 0: continue
            
            print(f"\n  卖出 {coin}:")
            print(f"    数量: {quantity}")
            print(f"    价格: ${current_price}")
            print(f"    价值: ${quantity * current_price:.2f}")
            
            try:
                order = place_order(symbol, 'SELL', 'MARKET', quantity)
                if 'orderId' in order:
                    print(f"    ✅ 下单成功! OrderID: {order['orderId']}")
                    executed.append({'coin': coin, 'side': 'SELL', 'quantity': quantity, 'price': current_price})
                else:
                    print(f"    ❌ 下单失败: {order}")
            except Exception as e:
                print(f"    ❌ 错误: {e}")
    
    if not buy_signals and not sell_signals:
        print(f"\n⏸️ 无操作信号, 观望")
    
    # 汇总
    print(f"\n{'='*70}")
    print("【执行汇总】")
    print("=" * 70)
    if executed:
        for e in executed:
            print(f"  {e['side']} {e['coin']}: {e['quantity']} @ ${e['price']}")
    else:
        print("  无执行")
    
    return executed

def run_cycle():
    """运行完整周期"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*70}")
    print(f"🌟 G26 自主迭代 - 实盘操作 [{ts}]")
    print(f"{'='*70}")
    
    top5 = generate_top5()
    if not top5:
        print("⚠️ 无TOP5数据")
        return []
    
    decisions = review_and_simulate(top5)
    executed = auto_execute(decisions)
    
    return executed

def main():
    print("G26 自主迭代 - 实盘操作版启动")
    print("⚠️ 风险提示: 实盘交易, 请确保风险可控")
    
    executed = run_cycle()
    
    print(f"\n最终执行: {len(executed)}笔交易")

if __name__ == '__main__':
    main()
