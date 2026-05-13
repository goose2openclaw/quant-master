#!/usr/bin/env python3
"""
G28 自主迭代版 - 收益最大化 + 资产流转管理
============================================
核心升级:
1. 收益最大化优先
2. 持仓币种间流动性管理
3. 智能资产转换
4. 动态仓位优化
5. 收益再投资

G28 = G27 + 收益最大化 + 资产流转
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime
import random

API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

MAJOR_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX', 'DOT', 'UNI', 'BNB']
MEME_COINS = ['PEPE', 'PENGU', 'BONK', 'SHIB', 'TRUMP', 'PUMP', 'WIF',
              'FLOKI', 'NEIRO', 'VANA', 'PNUT', 'BOME', 'TURBO', 'MEME', 'KAITO']

# G28 个性化策略
COIN_STRATEGIES = {
    'BTC': {'type': 'major', 'oversold': 30, 'overbought': 75, 'stop': 0.02, 'take': 0.15, 'leverage': 5, 'position': 0.15, 'max_position': 0.20, 'liquidity_score': 10},
    'ETH': {'type': 'major', 'oversold': 40, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.12, 'max_position': 0.15, 'liquidity_score': 9},
    'SOL': {'type': 'major', 'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.20, 'leverage': 5, 'position': 0.10, 'max_position': 0.15, 'liquidity_score': 8},
    'DOGE': {'type': 'major', 'oversold': 40, 'overbought': 70, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.15, 'max_position': 0.20, 'liquidity_score': 7},
    'LINK': {'type': 'major', 'oversold': 35, 'overbought': 70, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.15, 'max_position': 0.15, 'liquidity_score': 7},
    'BNB': {'type': 'major', 'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.15, 'leverage': 5, 'position': 0.10, 'max_position': 0.15, 'liquidity_score': 6},
    'UNI': {'type': 'major', 'oversold': 35, 'overbought': 75, 'stop': 0.03, 'take': 0.20, 'leverage': 5, 'position': 0.12, 'max_position': 0.15, 'liquidity_score': 6},
    'PEPE': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 5},
    'PUMP': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 4},
    'WIF': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 4},
    'FLOKI': {'type': 'meme', 'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 4},
    'NEIRO': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 3},
    'VANA': {'type': 'meme', 'oversold': 35, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 3},
    'PNUT': {'type': 'meme', 'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 3},
    'BOME': {'type': 'meme', 'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.35, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 3},
    'TURBO': {'type': 'meme', 'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 3},
    'MEME': {'type': 'meme', 'oversold': 30, 'overbought': 75, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 3},
    'KAITO': {'type': 'meme', 'oversold': 35, 'overbought': 70, 'stop': 0.05, 'take': 0.30, 'leverage': 10, 'position': 0.08, 'max_position': 0.10, 'liquidity_score': 3},
}

MONTE_CARLO_AGENTS = 500

def api(url):
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: return json.loads(opener.open(req, timeout=30).read().decode())
    except: return {}

def signed_api_post(endpoint, params=None):
    ts = int(time.time() * 1000)
    base_params = {"timestamp": ts}
    if params: base_params.update(params)
    q = "&".join(f"{k}={v}" for k, v in base_params.items())
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url, method='POST')
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try: 
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except Exception as e: return {"error": str(e)}

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url)
    try: return float(json.loads(opener.open(req, timeout=10).read().decode())['price'])
    except: return 0

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

def get_account():
    ts = int(time.time() * 1000)
    params = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except: return {}

def get_holdings():
    account = get_account()
    holdings = {}
    if 'balances' in account:
        for b in account['balances']:
            free = float(b.get('free', 0))
            if free > 0.001:
                holdings[b['asset']] = free
    return holdings

def analyze_coins():
    """分析所有币种,返回收益潜力排名"""
    all_coins = list(set(MAJOR_COINS + MEME_COINS))
    coin_scores = []
    
    for coin in all_coins:
        if coin == 'USDT': continue
        
        strategy = COIN_STRATEGIES.get(coin)
        if not strategy: continue
        
        prices = klines(f"{coin}USDT", 720)
        if len(prices) < 500: continue
        
        # RSI分析
        rsi_vals = [calc_rsi(prices[i-50:i]) if i >= 50 else 50 for i in range(len(prices))]
        current_rsi = rsi_vals[-1]
        
        # 动量
        momentum_24h = (prices[-1] / prices[-24] - 1) * 100 if len(prices) >= 24 else 0
        
        # 价格位置
        price_high_30d = max(prices[-720:])
        price_low_30d = min(prices[-720:])
        price_position = (prices[-1] - price_low_30d) / (price_high_30d - price_low_30d) * 100 if price_high_30d != price_low_30d else 50
        
        # 收益潜力评分
        potential_score = 0
        if current_rsi < strategy['oversold']:
            potential_score += 50  # 超卖加分
        if momentum_24h > 0:
            potential_score += 20  # 正动量加分
        if price_position < 30:
            potential_score += 30  # 低位加分
        
        coin_scores.append({
            'coin': coin,
            'rsi': current_rsi,
            'momentum_24h': momentum_24h,
            'price_position': price_position,
            'potential_score': potential_score,
            'strategy': strategy,
        })
    
    # 按收益潜力排序
    coin_scores.sort(key=lambda x: x['potential_score'], reverse=True)
    return coin_scores

def liquidity_management(holdings, prices):
    """流动性管理 - 决定持仓比例"""
    total_value = 0
    holdings_detail = []
    
    for coin, amount in holdings.items():
        if coin == 'USDT':
            total_value += amount
            holdings_detail.append({
                'coin': coin,
                'amount': amount,
                'value': amount,
                'liquidity_score': 10,
                'type': 'cash'
            })
        else:
            price = prices.get(coin, 0)
            if price > 0:
                value = amount * price
                total_value += value
                strategy = COIN_STRATEGIES.get(coin, {})
                holdings_detail.append({
                    'coin': coin,
                    'amount': amount,
                    'value': value,
                    'liquidity_score': strategy.get('liquidity_score', 5),
                    'type': strategy.get('type', 'unknown')
                })
    
    # 计算最优配置
    optimal_allocation = []
    for h in holdings_detail:
        pct = (h['value'] / total_value * 100) if total_value > 0 else 0
        h['pct'] = pct
        optimal_allocation.append(h)
    
    return {
        'total_value': total_value,
        'holdings': optimal_allocation,
    }

def execute_trade(coin, side, quantity):
    """执行交易"""
    symbol = f"{coin}USDT"
    order = signed_api_post("/api/v3/order", {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantity
    })
    return order

def run_cycle():
    """运行完整G28周期"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*70}")
    print(f"🌟 G28 收益最大化 + 资产流转管理 [{ts}]")
    print(f"{'='*70}")
    
    # 1. 获取持仓
    holdings = get_holdings()
    print(f"\n当前持仓: {list(holdings.keys())}")
    
    usdt = holdings.get('USDT', 0)
    print(f"USDT: ${usdt:.2f}")
    
    # 2. 获取价格
    prices = {}
    for coin in holdings.keys():
        if coin != 'USDT':
            prices[coin] = get_price(f"{coin}USDT")
    
    # 3. 流动性管理
    print(f"\n{'='*70}")
    print("【流动性管理分析】")
    print("=" * 70)
    
    liq = liquidity_management(holdings, prices)
    print(f"\n总资产: ${liq['total_value']:.2f}")
    print(f"\n持仓详情:")
    for h in sorted(liq['holdings'], key=lambda x: x['value'], reverse=True):
        coin_type = '💰' if h['type'] == 'cash' else ('📈' if h['type'] == 'major' else '🟣')
        print(f"  {coin_type}{h['coin']:>8}: {h['amount']:.4f} = ${h['value']:.2f} ({h['pct']:.1f}%) [流动性:{h['liquidity_score']}]")
    
    # 4. 收益潜力分析
    print(f"\n{'='*70}")
    print("【收益潜力排名 TOP5】")
    print("=" * 70)
    
    top_coins = analyze_coins()[:5]
    for i, c in enumerate(top_coins, 1):
        emoji = '📈' if c['strategy']['type'] == 'major' else '🟣'
        print(f"  {i}. {emoji}{c['coin']:>8} 潜力:{c['potential_score']:>3} RSI:{c['rsi']:>5.1f} 动量:{c['momentum_24h']:>+6.2f}%")
    
    # 5. 资产流转决策
    print(f"\n{'='*70}")
    print("【资产流转决策】")
    print("=" * 70)
    
    # 卖出低潜力持仓,买入高潜力
    actions = []
    
    # 检查是否需要变现弱势币
    for h in liq['holdings']:
        if h['coin'] == 'USDT' or h['coin'] == 'BTC': continue
        
        strategy = COIN_STRATEGIES.get(h['coin'])
        if not strategy: continue
        
        # RSI过高 -> 考虑卖出
        if h['coin'] in prices:
            rsi = calc_rsi(klines(f"{h['coin']}USDT", 100))
            if rsi > strategy['overbought'] + 10 and h['value'] > 10:
                actions.append({
                    'action': 'SELL',
                    'coin': h['coin'],
                    'amount': h['amount'],
                    'value': h['value'],
                    'reason': f'RSI过高({rsi:.1f})'
                })
    
    # 执行流转
    total_sell_value = sum(a['value'] for a in actions if a['action'] == 'SELL')
    print(f"\n计划变现: ${total_sell_value:.2f}")
    
    for a in actions:
        print(f"  🔴 卖出 {a['coin']}: {a['amount']:.4f} = ${a['value']:.2f} ({a['reason']})")
        
        # 实际卖出
        try:
            result = execute_trade(a['coin'], 'SELL', a['amount'])
            if 'orderId' in result:
                print(f"     ✅ 成功卖出 {a['coin']}")
            else:
                print(f"     ❌ 失败: {result.get('error', result)}")
        except Exception as e:
            print(f"     ❌ 错误: {e}")
    
    # 6. 买入高潜力币种
    if total_sell_value > 5:
        print(f"\n计划投资: ${total_sell_value * 0.8:.2f} -> TOP潜力币")
        
        for c in top_coins[:2]:
            coin = c['coin']
            if coin in holdings and holdings[coin] > 1: continue  # 已有持仓
            
            allocation = total_sell_value * 0.4  # 40%到第一潜力币
            price = get_price(f"{coin}USDT")
            if price > 0:
                quantity = allocation / price
                
                print(f"  🟢 买入 {coin}: ${allocation:.2f} @ ${price}")
                
                try:
                    result = execute_trade(coin, 'BUY', quantity)
                    if 'orderId' in result:
                        print(f"     ✅ 成功买入 {quantity:.2f} {coin}")
                    else:
                        print(f"     ❌ 失败: {result.get('error', result)}")
                except Exception as e:
                    print(f"     ❌ 错误: {e}")
    
    print(f"\n{'='*70}")
    print("【G28 周期完成】")
    print("=" * 70)

def main():
    print("G28 收益最大化 + 资产流转管理系统启动")
    run_cycle()

if __name__ == '__main__':
    main()
