#!/usr/bin/env python3
"""
G29 - Mirofish智能仿真 + 市场趋势决策系统
- 21h/24h/7d Mirofish 1000智能体仿真
- 7天和24小时市场类型和趋势判断
- Oracle数据作为参考
"""
import urllib.request, hmac, hashlib, time, json, random, numpy as np
from datetime import datetime
from collections import Counter

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g29.log"

TRADE_CONFIG = {
    'BTC': {'type':'major','position_pct':0.15,'min':0.0001},
    'ETH': {'type':'major','position_pct':0.12,'min':0.001},
    'LINK': {'type':'major','position_pct':0.10,'min':0.1},
    'SOL': {'type':'major','position_pct':0.10,'min':0.01},
    'UNI': {'type':'major','position_pct':0.10,'min':0.01},
    'BOME': {'type':'meme','position_pct':0.08,'min':10000},
    'TURBO': {'type':'meme','position_pct':0.08,'min':1000},
    'PUMP': {'type':'meme','position_pct':0.08,'min':100},
    'NEIRO': {'type':'meme','position_pct':0.08,'min':10000},
}

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def proxy_get(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    return json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())

def signed_api(endpoint, params=None, method="GET"):
    ts = int(time.time() * 1000)
    base = {"timestamp": ts, "recvWindow": 5000}
    if params: base.update(params)
    q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try:
        resp = urllib.request.build_opener(proxy_handler).open(req, timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try: return float(json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())['price'])
    except: return 0

def get_klines(symbol, interval, limit):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    try: return json.loads(urllib.request.build_opener(proxy_handler).open(urllib.request.Request(url), timeout=10).read().decode())
    except: return []

def get_rsi(symbol, period=14):
    data = get_klines(symbol, '1h', 50)
    if not data: return 50
    closes = [float(k[4]) for k in data]
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period
    if avg_loss == 0: return 100
    return 100-(100/(1+avg_gain/avg_loss))

def get_momentum(symbol, hours=24):
    data = get_klines(symbol, '1h', hours+1)
    if not data or len(data) < hours+1: return 0
    old = float(data[0][4])
    new = float(data[-1][4])
    return ((new - old) / old) * 100

# ============== G29 核心: Mirofish 1000智能体仿真 ==============

def mirofish_simulation(prices, agent_count=1000, simulation_hours=24):
    """
    Mirofish 1000智能体仿真
    每个智能体根据市场状态和随机因素做决策
    """
    if len(prices) < 2:
        return {'bull_votes': 500, 'bear_votes': 500, 'avg_change': 0, 'confidence': 0}
    
    # 计算市场特征
    returns = [(prices[i+1] - prices[i]) / prices[i] for i in range(len(prices)-1)]
    volatility = np.std(returns) if len(returns) > 1 else 0.01
    trend = np.mean(returns) if returns else 0
    
    # 智能体决策模拟
    bull_votes = 0
    bear_votes = 0
    
    for _ in range(agent_count):
        # 每个智能体有不同的风险偏好
        risk_appetite = random.gauss(0.5, 0.2)
        risk_appetite = max(0, min(1, risk_appetite))
        
        # 基于市场特征的判断
        if trend > volatility * 2:
            # 明确上升趋势
            if risk_appetite > 0.3:
                bull_votes += 1
            else:
                bull_votes += 0.5
                bear_votes += 0.5
        elif trend < -volatility * 2:
            # 明确下降趋势
            if risk_appetite > 0.7:
                bull_votes += 0.5
                bear_votes += 0.5
            else:
                bear_votes += 1
        else:
            # 震荡市场，智能体分散决策
            noise = random.gauss(0, volatility)
            if trend + noise > 0:
                bull_votes += 1
            else:
                bear_votes += 1
    
    total = bull_votes + bear_votes
    avg_change = sum(returns) / len(returns) * 100
    confidence = abs(bull_votes - bear_votes) / total
    
    return {
        'bull_votes': int(bull_votes),
        'bear_votes': int(bear_votes),
        'bull_pct': bull_votes / total * 100,
        'bear_pct': bear_votes / total * 100,
        'avg_change': avg_change,
        'confidence': confidence,
        'volatility': volatility * 100,
        'trend': trend * 100
    }

def get_market_type_24h(symbol):
    """24小时市场类型判断"""
    data = get_klines(symbol, '1h', 24)
    if len(data) < 24: return None
    
    highs = [float(k[2]) for k in data]
    lows = [float(k[3]) for k in data]
    closes = [float(k[4]) for k in data]
    
    price_range = (max(highs) - min(lows)) / min(lows) * 100
    trend = ((closes[-1] - closes[0]) / closes[0]) * 100
    
    # 判断市场类型
    if price_range < 2 and abs(trend) < 1:
        return 'range'  # 震荡
    elif trend > 3:
        return 'bull'  # 强势上涨
    elif trend < -3:
        return 'bear'  # 强势下跌
    elif price_range > 5:
        return 'volatile'  # 高波动
    else:
        return 'neutral'

def get_market_type_7d(symbol):
    """7天市场类型判断"""
    data = get_klines(symbol, '1h', 168)  # 7天*24小时
    if len(data) < 100: return None
    
    highs = [float(k[2]) for k in data]
    lows = [float(k[3]) for k in data]
    closes = [float(k[4]) for k in data]
    volumes = [float(k[5]) for k in data]
    
    # 计算各种指标
    price_range = (max(highs) - min(lows)) / min(lows) * 100
    trend_7d = ((closes[-1] - closes[0]) / closes[0]) * 100
    
    # 波动率
    returns = [(closes[i+1]-closes[i])/closes[i] for i in range(len(closes)-1)]
    volatility = np.std(returns) * 100
    
    # 成交量趋势
    vol_early = np.mean(volumes[:len(volumes)//3])
    vol_late = np.mean(volumes[-len(volumes)//3:])
    vol_trend = (vol_late - vol_early) / vol_early * 100 if vol_early > 0 else 0
    
    return {
        'trend': trend_7d,
        'volatility': volatility,
        'range': price_range,
        'volume_trend': vol_trend,
        'type': classify_market(trend_7d, volatility, price_range)
    }

def classify_market(trend, volatility, price_range):
    """分类市场类型"""
    if volatility > 5:
        return 'high_volatility'
    elif abs(trend) > 15:
        return 'strong_trend'
    elif abs(trend) > 5:
        return 'moderate_trend'
    elif price_range > 20:
        return 'wide_range'
    else:
        return 'sideways'

# ============== Oracle 决策矩阵 ==============

def oracle_decision_v2(rsi, momentum, coin_type, mirofish_24h, mirofish_7d, market_type):
    """
    G29 Oracle决策 - 整合Mirofish仿真和市场类型
    """
    # 基础RSI阈值
    buy_thresh = 35 if coin_type == "meme" else 40
    sell_thresh = 75 if coin_type == "meme" else 70
    
    # Mirofish信号权重
    bull_24h = mirofish_24h.get('bull_pct', 50) if mirofish_24h else 50
    bull_7d = mirofish_7d.get('bull_pct', 50) if mirofish_7d else 50
    confidence = mirofish_24h.get('confidence', 0) if mirofish_24h else 0
    
    # 市场类型调整
    market_multiplier = 1.0
    if market_type == 'bear':
        market_multiplier = 0.7  # 熊市降低买入
    elif market_type == 'bull':
        market_multiplier = 1.3  # 牛市提高买入
    elif market_type == 'high_volatility':
        market_multiplier = 0.8  # 高波动降低
    
    # 综合评分
    score = 0
    # RSI评分 (40%)
    if rsi < 25: score += 40
    elif rsi < 30: score += 30
    elif rsi < 35: score += 20
    elif rsi < 40: score += 10
    elif rsi > 75: score -= 40
    elif rsi > 70: score -= 30
    elif rsi > 65: score -= 20
    
    # 动量评分 (20%)
    if momentum < -3: score += 20
    elif momentum < -1: score += 10
    elif momentum > 3: score -= 20
    elif momentum > 1: score -= 10
    
    # Mirofish 24h评分 (20%)
    if bull_24h > 70: score -= 15
    elif bull_24h > 60: score -= 10
    elif bull_24h < 30: score += 15
    elif bull_24h < 40: score += 10
    
    # Mirofish 7d评分 (20%)
    if bull_7d > 65: score -= 10
    elif bull_7d < 35: score += 10
    
    score = score * market_multiplier
    
    # 决策输出
    if score >= 30: return "STRONG_BUY"
    elif score >= 15: return "BUY"
    elif score <= -30: return "STRONG_SELL"
    elif score <= -15: return "SELL"
    else: return "HOLD"

# ============== 账户管理 ==============

def get_account():
    account = signed_api("/api/v3/account")
    result = {'usdt': 0, 'coins': {}}
    if 'balances' in account:
        for b in account['balances']:
            free = float(b.get('free', 0))
            if free > 0.001:
                if b['asset'] == 'USDT':
                    result['usdt'] = free
                else:
                    result['coins'][b['asset']] = free
    return result

def place_order(symbol, side, quantity):
    params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
    result = signed_api("/api/v3/order", params, "POST")
    if 'error' in str(result): return None
    return result

def get_total(spot_acc):
    total = spot_acc['usdt']
    for coin, qty in spot_acc['coins'].items():
        total += qty * get_price(f"{coin}USDT")
    return total

def auto_convert_for_funds(spot_acc, target_coin, target_qty):
    """自动卖出其他币种获取USDT"""
    price = get_price(f"{target_coin}USDT")
    needed_usdt = target_qty * price * 1.001
    
    if spot_acc['usdt'] >= needed_usdt:
        return True
    
    needed = needed_usdt - spot_acc['usdt']
    candidates = []
    for coin, qty in spot_acc['coins'].items():
        if coin == target_coin or coin not in TRADE_CONFIG: continue
        rsi = get_rsi(f"{coin}USDT")
        coin_price = get_price(f"{coin}USDT")
        value = qty * coin_price
        if value > needed * 1.5:
            candidates.append((coin, qty, value, rsi, coin_price))
    
    candidates.sort(key=lambda x: x[3], reverse=True)
    for coin, qty, value, rsi, coin_price in candidates:
        sell_qty = min(qty * 0.5, (needed / coin_price) * 1.1)
        sell_qty = int(sell_qty / 100) * 100
        if sell_qty >= TRADE_CONFIG.get(coin, {}).get('min', 1):
            result = place_order(f"{coin}USDT", "SELL", sell_qty)
            if result:
                log(f"  💱 自动转换 {coin}: {sell_qty} → +${sell_qty * coin_price:.2f}")
                return True
    return False

# ============== 主循环 ==============

def main():
    log("=" * 80)
    log("G29 Mirofish智能仿真 + 市场趋势决策系统")
    log("=" * 80)
    
    while True:
        try:
            spot_acc = get_account()
            total = get_total(spot_acc)
            
            log(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} | 总资产: ${total:.2f} | USDT: ${spot_acc['usdt']:.2f}")
            
            for coin, cfg in TRADE_CONFIG.items():
                symbol = f"{coin}USDT"
                
                # 获取基础数据
                rsi = get_rsi(symbol)
                momentum_24h = get_momentum(symbol, 24)
                momentum_7d = get_momentum(symbol, 168)
                
                # 市场类型判断
                market_type_24h = get_market_type_24h(symbol)
                market_7d = get_market_type_7d(symbol)
                
                # Mirofish 1000智能体仿真
                prices_24h = [float(k[4]) for k in get_klines(symbol, '1h', 25)]
                prices_7d = [float(k[4]) for k in get_klines(symbol, '1h', 169)]
                
                mirofish_24h = mirofish_simulation(prices_24h, agent_count=1000, simulation_hours=24)
                mirofish_7d = mirofish_simulation(prices_7d[-100:], agent_count=1000, simulation_hours=168)
                
                # Oracle决策 v2
                decision = oracle_decision_v2(rsi, momentum_24h, cfg['type'], mirofish_24h, mirofish_7d, market_type_24h)
                
                # 详细日志输出
                log(f"\n{'='*60}")
                log(f"📊 {coin} 分析报告")
                log(f"{'='*60}")
                log(f"  RSI: {rsi:.1f} | 24h动量: {momentum_24h:+.2f}% | 7d动量: {momentum_7d:+.2f}%")
                log(f"  市场24h: {market_type_24h} | 7天类型: {market_7d.get('type','N/A')}")
                log(f"  📈 Mirofish 24h: 牛市{int(mirofish_24h['bull_pct'])}% | 熊市{int(mirofish_24h['bear_pct'])}% | 置信度:{mirofish_24h['confidence']:.2f}")
                log(f"  📈 Mirofish 7d:  牛市{int(mirofish_7d['bull_pct'])}% | 熊市{int(mirofish_7d['bear_pct'])}% | 置信度:{mirofish_7d['confidence']:.2f}")
                log(f"  🎯 Oracle决策: {decision}")
                
                # 交易执行
                price = get_price(symbol)
                current_qty = spot_acc['coins'].get(coin, 0)
                current_value = current_qty * price
                target_value = total * cfg['position_pct']
                
                if decision in ['STRONG_BUY', 'BUY'] and current_value < target_value:
                    min_qty = cfg.get('min', 1)
                    buy_qty = max(min_qty * 3, target_value * 0.5 / price)
                    buy_qty = int(buy_qty / 100) * 100 if cfg['type'] == 'meme' else buy_qty
                    
                    if spot_acc['usdt'] < buy_qty * price:
                        log(f"  💡 USDT不足，启动自动转换...")
                        auto_convert_for_funds(spot_acc, coin, buy_qty)
                        spot_acc = get_account()
                    
                    if spot_acc['usdt'] >= buy_qty * price * 1.001:
                        result = place_order(symbol, "BUY", buy_qty)
                        if result:
                            log(f"  ✅ 执行买入 {coin}: {buy_qty}")
                            spot_acc = get_account()
                
                elif decision in ['STRONG_SELL', 'SELL'] and current_qty > cfg.get('min', 1):
                    sell_qty = current_qty * 0.5
                    result = place_order(symbol, "SELL", sell_qty)
                    if result:
                        log(f"  ✅ 执行卖出 {coin}: {sell_qty}")
                        spot_acc = get_account()
            
            log(f"\n{'='*60}")
            time.sleep(120)  # 每2分钟运行一次
            
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
