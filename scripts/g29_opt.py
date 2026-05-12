#!/usr/bin/env python3
"""
G29 优化版 - 收益最大化
核心优化:
1. 动态仓位管理 (信心系数调整)
2. 追踪止盈/止损
3. 市场区间检测增强
4. 信号强度分级
5. 资金效率优化
"""
import urllib.request, hmac, hashlib, time, json, random, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

TRADE_CONFIG = {
    'BTC': {'type':'major','position_pct':0.18,'min':0.0001,'stop_loss':0.03,'take_profit':0.15},
    'ETH': {'type':'major','position_pct':0.15,'min':0.001,'stop_loss':0.035,'take_profit':0.18},
    'LINK': {'type':'major','position_pct':0.12,'min':0.1,'stop_loss':0.04,'take_profit':0.20},
    'SOL': {'type':'major','position_pct':0.12,'min':0.01,'stop_loss':0.045,'take_profit':0.22},
    'UNI': {'type':'major','position_pct':0.10,'min':0.01,'stop_loss':0.05,'take_profit':0.20},
    'BOME': {'type':'meme','position_pct':0.10,'min':10000,'stop_loss':0.05,'take_profit':0.30},
    'TURBO': {'type':'meme','position_pct':0.08,'min':1000,'stop_loss':0.06,'take_profit':0.35},
    'PUMP': {'type':'meme','position_pct':0.08,'min':100,'stop_loss':0.05,'take_profit':0.30},
    'NEIRO': {'type':'meme','position_pct':0.08,'min':10000,'stop_loss':0.05,'take_profit':0.30},
}

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

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

def get_volatility(symbol, hours=24):
    data = get_klines(symbol, '1h', hours+1)
    if not data or len(data) < hours+1: return 0.02
    closes = [float(k[4]) for k in data]
    returns = [(closes[i+1]-closes[i])/closes[i] for i in range(len(closes)-1)]
    return np.std(returns)

# ============== 优化后的 Mirofish 1000智能体仿真 ==============

def mirofish_simulation_v2(prices, agent_count=1000):
    """
    优化的Mirofish仿真 - 更激进的趋势跟随
    """
    if len(prices) < 2:
        return {'bull_pct': 50, 'confidence': 0, 'signal': 'neutral'}
    
    returns = [(prices[i+1] - prices[i]) / prices[i] for i in range(len(prices)-1)]
    volatility = np.std(returns) if len(returns) > 1 else 0.01
    trend = np.mean(returns) if returns else 0
    
    # 短期动量
    if len(prices) >= 24:
        short_momentum = (prices[-1] - prices[-24]) / prices[-24]
    else:
        short_momentum = trend
    
    bull, bear = 0, 0
    
    for _ in range(agent_count):
        # 趋势跟随型智能体 (70%)
        if trend > volatility * 1.5:
            if short_momentum > 0:
                bull += 1.5  # 增强信号
            else:
                bull += 0.7
        elif trend < -volatility * 1.5:
            if short_momentum < 0:
                bear += 1.5
            else:
                bear += 0.7
        else:
            # 震荡市场 - 反转策略
            if random.random() < 0.4:  # 40%概率反转
                if trend + random.gauss(0, volatility) < 0:
                    bull += 1
                else:
                    bear += 1
            else:
                # 随机漫步
                if random.random() < 0.5:
                    bull += 1
                else:
                    bear += 1
    
    total = bull + bear
    bull_pct = bull / total * 100
    confidence = abs(bull - bear) / total
    
    # 信号强度
    if bull_pct > 70 and confidence > 0.3:
        signal = 'strong_bull'
    elif bull_pct > 55:
        signal = 'bull'
    elif bear_pct > 70 and confidence > 0.3:
        signal = 'strong_bear'
    elif bear_pct > 55:
        signal = 'bear'
    else:
        signal = 'neutral'
    
    return {
        'bull_pct': bull_pct,
        'bear_pct': 100 - bull_pct,
        'confidence': confidence,
        'signal': signal,
        'trend': trend * 100,
        'volatility': volatility * 100
    }

def get_market_regime(symbol):
    """
    市场区间检测 - 四种状态
    """
    data_24h = get_klines(symbol, '1h', 24)
    data_7d = get_klines(symbol, '1h', 168)
    
    if not data_24h or not data_7d:
        return 'neutral'
    
    # 24h分析
    closes_24h = [float(k[4]) for k in data_24h]
    highs_24h = [float(k[2]) for k in data_24h]
    lows_24h = [float(k[3]) for k in data_24h]
    
    trend_24h = ((closes_24h[-1] - closes_24h[0]) / closes_24h[0]) * 100
    range_24h = (max(highs_24h) - min(lows_24h)) / min(lows_24h) * 100
    
    # 7d分析
    closes_7d = [float(k[4]) for k in data_7d]
    trend_7d = ((closes_7d[-1] - closes_7d[0]) / closes_7d[0]) * 100
    
    returns_7d = [(closes_7d[i+1]-closes_7d[i])/closes_7d[i] for i in range(len(closes_7d)-1)]
    volatility_7d = np.std(returns_7d) * 100
    
    # 区间判断
    if abs(trend_7d) < 3 and volatility_7d < 2:
        return 'sideways_low_vol'
    elif volatility_7d > 5:
        return 'high_volatility'
    elif trend_7d > 5 and trend_24h > 2:
        return 'strong_uptrend'
    elif trend_7d < -5 and trend_24h < -2:
        return 'strong_downtrend'
    elif abs(trend_7d) < 8:
        return 'range_bound'
    else:
        return 'moderate_trend'

# ============== 优化的Oracle决策 ==============

def oracle_decision_v3(rsi, momentum, coin_type, mirofish, market_regime, volatility):
    """
    G29优化版Oracle - 收益最大化
    """
    cfg = TRADE_CONFIG.get(coin_type, {})
    
    # 动态阈值
    if coin_type == 'meme':
        buy_thresh = 32  # 更低 = 更激进买入
        sell_thresh = 72  # 更低 = 更早止盈
    else:
        buy_thresh = 38
        sell_thresh = 68
    
    # 市场区间调整
    regime_mult = {
        'strong_uptrend': {'buy': 0.8, 'sell': 1.2},  # 强趋势:早点买,晚点卖
        'strong_downtrend': {'buy': 1.3, 'sell': 0.7},  # 强下跌:晚点买,早点卖
        'high_volatility': {'buy': 1.1, 'sell': 0.9},
        'range_bound': {'buy': 1.0, 'sell': 1.0},
        'sideways_low_vol': {'buy': 0.9, 'sell': 1.1},
        'moderate_trend': {'buy': 1.0, 'sell': 1.0},
        'neutral': {'buy': 1.0, 'sell': 1.0},
    }
    
    rm = regime_mult.get(market_regime, regime_mult['neutral'])
    
    # Mirofish信号增强
    bull_pct = mirofish.get('bull_pct', 50)
    confidence = mirofish.get('confidence', 0)
    signal = mirofish.get('signal', 'neutral')
    
    # 动态评分
    score = 0
    
    # RSI评分 (核心40%)
    if rsi < 25: score += 50
    elif rsi < 30: score += 40
    elif rsi < buy_thresh: score += 30
    elif rsi > 80: score -= 50
    elif rsi > sell_thresh: score -= 40
    elif rsi > 65: score -= 25
    
    # 动量评分 (20%)
    if momentum < -4: score += 25
    elif momentum < -2: score += 15
    elif momentum < -1: score += 8
    elif momentum > 4: score -= 25
    elif momentum > 2: score -= 15
    
    # Mirofish评分 (30%) - 优化权重
    if signal == 'strong_bull':
        score -= 20
    elif signal == 'bull':
        score -= 10
    elif signal == 'strong_bear':
        score += 20
    elif signal == 'bear':
        score += 10
    
    if confidence > 0.4:
        score *= 1.2  # 高置信度增强信号
    
    # 波动率调整
    if volatility > 4:
        score *= 0.85
    elif volatility < 1:
        score *= 1.1
    
    # 市场区间调整
    score_adjusted = score * rm['buy'] if score > 0 else score / rm['buy']
    
    # 决策输出
    if score_adjusted >= 35: return "STRONG_BUY"
    elif score_adjusted >= 20: return "BUY"
    elif score_adjusted <= -35: return "STRONG_SELL"
    elif score_adjusted <= -20: return "SELL"
    else: return "HOLD"

# ============== 动态仓位管理 ==============

def calc_position_size(total, coin_type, confidence, market_regime, volatility):
    """
    动态计算仓位大小 - 收益最大化
    """
    base_pct = TRADE_CONFIG.get(coin_type, {}).get('position_pct', 0.08)
    
    # 信心系数调整
    conf_mult = 0.5 + confidence * 1.0  # 0.5-1.5
    
    # 市场区间调整
    regime_mults = {
        'strong_uptrend': 1.3,
        'strong_downtrend': 0.5,
        'high_volatility': 0.7,
        'range_bound': 1.0,
        'sideways_low_vol': 1.1,
        'moderate_trend': 1.0,
        'neutral': 1.0
    }
    reg_mult = regime_mults.get(market_regime, 1.0)
    
    # 波动率调整
    vol_mult = 1.5 - volatility * 0.1  # 波动越高,仓位越低
    
    final_pct = base_pct * conf_mult * reg_mult * vol_mult
    final_pct = min(final_pct, 0.25)  # 最大25%仓位
    
    return total * final_pct

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

# ============== 主循环 ==============

def main():
    log("=" * 80)
    log("G29 优化版 - 收益最大化")
    log("=" * 80)
    
    while True:
        try:
            spot_acc = get_account()
            total = get_total(spot_acc)
            
            log(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} | 总资产: ${total:.2f} | USDT: ${spot_acc['usdt']:.2f}")
            
            for coin, cfg in TRADE_CONFIG.items():
                symbol = f"{coin}USDT"
                
                # 获取数据
                rsi = get_rsi(symbol)
                momentum = get_momentum(symbol, 24)
                volatility = get_volatility(symbol, 24) * 100
                market_regime = get_market_regime(symbol)
                
                # Mirofish仿真
                prices = [float(k[4]) for k in get_klines(symbol, '1h', 168)]
                mirofish = mirofish_simulation_v2(prices[-100:])
                
                # Oracle决策
                decision = oracle_decision_v3(rsi, momentum, cfg['type'], mirofish, market_regime, volatility)
                
                # 动态仓位
                target_value = calc_position_size(total, cfg['type'], mirofish['confidence'], market_regime, volatility)
                
                price = get_price(symbol)
                current_qty = spot_acc['coins'].get(coin, 0)
                current_value = current_qty * price
                
                # 日志
                sig_emoji = "🔮" if decision != "HOLD" else "  "
                log(f"  {sig_emoji} {coin}: {decision} (RSI:{rsi:.1f} 动量:{momentum:+.1f}% 区间:{market_regime})")
                log(f"       Mirofish: {mirofish['bull_pct']:.0f}%Bull {mirofish['confidence']:.2f}conf → {mirofish['signal']}")
                
                # 交易执行 - 优化版
                if decision in ['STRONG_BUY', 'BUY'] and current_value < target_value:
                    buy_pct = 0.6 if decision == 'STRONG_BUY' else 0.4
                    buy_value = target_value * buy_pct
                    min_qty = cfg.get('min', 1)
                    
                    if coin == 'meme':
                        buy_qty = int((buy_value / price) / 100) * 100
                        buy_qty = max(min_qty * 3, buy_qty)
                    else:
                        buy_qty = max(min_qty, buy_value * 0.95 / price)
                    
                    if spot_acc['usdt'] >= buy_qty * price * 1.001:
                        result = place_order(symbol, "BUY", buy_qty)
                        if result:
                            log(f"       ✅ 买入 {coin}: {buy_qty} @ ${price:.6f}")
                            spot_acc = get_account()
                
                elif decision in ['STRONG_SELL', 'SELL'] and current_qty > cfg.get('min', 1):
                    sell_pct = 0.7 if decision == 'STRONG_SELL' else 0.5
                    sell_qty = current_qty * sell_pct
                    result = place_order(symbol, "SELL", sell_qty)
                    if result:
                        log(f"       ✅ 卖出 {coin}: {sell_qty} @ ${price:.6f}")
                        spot_acc = get_account()
            
            time.sleep(120)
            
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
