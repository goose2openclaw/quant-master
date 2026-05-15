#!/usr/bin/env python3
"""
Top6 Meme 动态交易策略
========================
专注Top6 Meme币: BOME, TURBO, BONK, FLOKI, PEPE, NEIRO
动态抓取和退出

特点:
1. 实时追踪Top6币种
2. 动态入场 (RSI超卖 + 动量确认)
3. 动态退出 (追踪止盈 + RSI超买)
4. 自动再平衡
"""

import urllib.request, hmac, hashlib, time, json, sys, math
from datetime import datetime
from collections import deque

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/top6_meme.log"

# Top6 Meme币
TOP6_MEME = ['BOME', 'TURBO', 'BONK', 'FLOKI', 'PEPE', 'NEIRO']

# 策略参数
INITIAL_INVESTMENT = 100  # 初始每币种投资
MAX_POSITION_PCT = 0.20   # 最大仓位20%
STOP_LOSS = 0.05          # 5%止损
TAKE_PROFIT = 0.20        # 20%止盈
TRAILING_STOP = 0.08      # 8%追踪止盈
RSI_OVERSOLD = 35         # 入场RSI阈值
RSI_OVERBOUGHT = 70      # 出场RSI阈值
SCAN_INTERVAL = 30        # 30秒扫描

# 全局状态
positions = {}  # {coin: {'entry': price, 'qty': qty, 'high': price, 'buy_rsi': rsi}}
_g_account = {'usdt': 0, 'coins': {}, 'time': 0}
history = deque(maxlen=100)

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")

def api_get(url, retries=2):
    for i in range(retries):
        try:
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        except:
            if i < retries - 1: time.sleep(0.3)
    return None

def api_signed(endpoint, params=None, method="GET", retries=3):
    for i in range(retries):
        try:
            ts = int(time.time() * 1000)
            base = {"timestamp": ts, "recvWindow": 5000}
            if params: base.update(params)
            q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
            sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
            url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
            req = urllib.request.Request(url, method=method)
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(req, timeout=15).read().decode())
        except:
            if i < retries - 1: time.sleep(0.5)
    return None

def get_price(symbol):
    try:
        return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=100):
    data = api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    if not data: return []
    return [{'close': float(k[4]), 'high': float(k[2]), 'low': float(k[3]), 'volume': float(k[5])} for k in data]

def get_rsi(closes, period=14):
    if len(closes) < period+1: return 50
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period
    if avg_loss==0: return 100
    return 100-(100/(1+avg_gain/(avg_loss+1e-10)))

def get_momentum(closes, period=12):
    if len(closes)<period+1: return 0
    return (closes[-1]-closes[-period])/closes[-period]

def get_volatility(closes, period=20):
    if len(closes)<period+1: return 0.02
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1,len(closes))]
    mean = sum(returns[-period:])/len(returns[-period:])
    variance = sum((r-mean)**2 for r in returns[-period:])/len(returns[-period:])
    return math.sqrt(variance)

def get_coin_analysis(coin):
    """获取币种分析数据"""
    data = get_klines(f"{coin}USDT", '1h', 100)
    if not data: return None
    
    closes = [d['close'] for d in data]
    rsi = get_rsi(closes)
    mom = get_momentum(closes, 12)
    vol = get_volatility(closes)
    
    # 短期趋势
    ma5 = sum(closes[-5:])/5
    ma20 = sum(closes[-20:])/20 if len(closes) >= 20 else ma5
    trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
    
    # 成交量变化
    vol_now = data[-1]['volume']
    vol_avg = sum(d['volume'] for d in data[-20:])/20 if len(data) >= 20 else vol_now
    vol_ratio = vol_now / vol_avg if vol_avg > 0 else 1
    
    return {
        'coin': coin,
        'price': closes[-1],
        'rsi': rsi,
        'momentum': mom,
        'volatility': vol,
        'trend': trend,
        'volume_ratio': vol_ratio,
        'closes': closes
    }

def should_buy(analysis):
    """动态入场条件"""
    if not analysis: return False, 0
    
    score = 0
    
    # RSI超卖加分
    if analysis['rsi'] < RSI_OVERSOLD:
        score += 40
    elif analysis['rsi'] < 40:
        score += 25
    
    # 正动量加分
    if analysis['momentum'] > 0.05:
        score += 25
    elif analysis['momentum'] > 0.02:
        score += 15
    
    # 上涨趋势加分
    if analysis['trend'] > 0.03:
        score += 20
    elif analysis['trend'] > 0:
        score += 10
    
    # 成交量放大加分
    if analysis['volume_ratio'] > 1.5:
        score += 15
    
    return score >= 60, score

def should_sell(coin, position):
    """动态出场条件"""
    data = get_klines(f"{coin}USDT", '1h', 50)
    if not data: return False, "", 0
    
    closes = [d['close'] for d in data]
    rsi = get_rsi(closes)
    current = closes[-1]
    
    entry = position['entry']
    high = position['high']
    pnl = (current - entry) / entry
    
    # 1. 止损
    if pnl <= -STOP_LOSS:
        return True, f"止损({pnl:.1%})", pnl
    
    # 2. 止盈
    if pnl >= TAKE_PROFIT:
        return True, f"止盈({pnl:.1%})", pnl
    
    # 3. 追踪止盈
    if pnl > 0.10:
        drawdown = (high - current) / high
        if drawdown >= TRAILING_STOP:
            return True, f"追踪止盈({pnl:.1%})", pnl
    
    # 4. RSI超买
    if rsi > RSI_OVERBOUGHT and pnl > 0.03:
        return True, f"RSI超买({rsi:.0f})", pnl
    
    # 5. 动量转负且盈利
    mom = get_momentum(closes, 12)
    if mom < -0.03 and pnl > 0.05:
        return True, f"动量转负({mom:.1%})", pnl
    
    return False, f"持有({pnl:+.1%})", pnl

def get_account():
    global _g_account
    now = time.time()
    if _g_account['time'] > 0 and now - _g_account['time'] < 3:
        return _g_account
    try:
        data = api_signed("/api/v3/account")
        result = {'usdt': 0, 'coins': {}}
        if data and 'balances' in data:
            for b in data.get('balances', []):
                free = float(b.get('free', 0))
                if free > 0.0001:
                    if b['asset'] == 'USDT': result['usdt'] = free
                    else: result['coins'][b['asset']] = free
        _g_account = result
        _g_account['time'] = now
        return result
    except Exception as e:
        log(f"账户失败: {e}", "ERROR")
        if _g_account['time'] > 0: return _g_account
        return {'usdt': 0, 'coins': {}, 'time': now}

def get_total_value(balances):
    total = balances['usdt']
    for coin, qty in balances['coins'].items():
        price = get_price(f"{coin}USDT")
        if price > 0: total += qty * price
    return total

def format_qty(coin, qty):
    if qty <= 0: return 0
    symbol = f"{coin}USDT"
    try:
        info = api_get(f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}')
        if info and 'symbols' in info:
            sym = info['symbols'][0]
            filters = {f['filterType']: f for f in sym['filters']}
            lot_size = filters.get('LOT_SIZE', {})
            step = float(lot_size.get('stepSize', 1.0))
            min_q = float(lot_size.get('minQty', 0))
            prec = 0
            if step < 1: prec = len(str(step).split('.')[-1].rstrip('0'))
            formatted = math.floor(qty / step) * step
            formatted = round(formatted, prec) if prec > 0 else int(formatted)
            if formatted < min_q: return 0
            return formatted
    except: pass
    return math.floor(qty)

def place_order(symbol, side, quantity):
    try:
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
        result = api_signed("/api/v3/order", params, "POST")
        if result and 'orderId' in result:
            log(f"订单成功: {side} {quantity} {symbol}", "TRADE")
            return result
    except Exception as e:
        log(f"订单失败: {e}", "ERROR")
    return None

def buy_coin(coin, total_value):
    global positions
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0: return False
    
    # 计算买入数量 (等权分配)
    max_per_coin = total_value * MAX_POSITION_PCT
    qty = max_per_coin / price
    qty = format_qty(coin, qty)
    
    if qty * price < 1: return False
    
    result = place_order(symbol, "BUY", qty)
    if result:
        positions[coin] = {
            'entry': price,
            'qty': qty,
            'high': price,
            'buy_time': time.time()
        }
        history.append({'coin': coin, 'action': 'BUY', 'price': price, 'time': time.time()})
        return True
    return False

def sell_coin(coin, reason=""):
    global positions
    symbol = f"{coin}USDT"
    price = get_price(symbol)
    if price <= 0: return False
    
    balances = get_account()
    qty = balances['coins'].get(coin, 0)
    if qty <= 0: return False
    
    qty = format_qty(coin, qty)
    if qty * price < 1: return False
    
    result = place_order(symbol, "SELL", qty)
    if result and coin in positions:
        entry = positions[coin]['entry']
        pnl = (price - entry) / entry * 100
        log(f"卖出 {coin}: {reason} {pnl:+.2f}%", "TRADE")
        history.append({'coin': coin, 'action': 'SELL', 'price': price, 'pnl': pnl, 'reason': reason, 'time': time.time()})
        del positions[coin]
        return True
    return False

def run():
    global positions
    
    log("=" * 60, "INFO")
    log("Top6 Meme 动态交易策略启动", "INFO")
    log(f"币种: {', '.join(TOP6_MEME)}", "INFO")
    log("动态入场: RSI<35 + 动量确认", "INFO")
    log("动态出场: 追踪止盈 + RSI超买", "INFO")
    log("=" * 60, "INFO")
    
    start_value = get_total_value(get_account())
    log(f"初始资产: ${start_value:.2f}", "INFO")
    
    while True:
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            log(f"\n{'='*60}", "INFO")
            log(f"Top6 Meme 扫描 ({ts})", "INFO")
            
            balances = get_account()
            total = get_total_value(balances)
            usdt = balances['usdt']
            log(f"资产: USDT={usdt:.2f} 总计=${total:.2f}", "INFO")
            
            # 1. 获取所有币种分析
            analyses = {}
            for coin in TOP6_MEME:
                analysis = get_coin_analysis(coin)
                if analysis:
                    analyses[coin] = analysis
            
            # 2. 检查持仓
            log("持仓状态:", "INFO")
            for coin in list(positions.keys()):
                info = positions[coin]
                should_exit, reason, pnl = should_sell(coin, info)
                
                # 更新最高价
                current = get_price(f"{coin}USDT")
                if current > info['high']:
                    positions[coin]['high'] = current
                
                if should_exit:
                    sell_coin(coin, reason)
                else:
                    log(f"  {coin}: 持仓 {pnl:+.1%} (RSI:{analyses.get(coin, {}).get('rsi', 0):.0f})", "INFO")
            
            # 3. 扫描买入机会
            if len(positions) < len(TOP6_MEME) and usdt >= 5:
                buy_candidates = []
                
                for coin in TOP6_MEME:
                    if coin in positions: continue
                    if coin in balances['coins']: continue
                    
                    analysis = analyses.get(coin)
                    if not analysis: continue
                    
                    should_buy_signal, score = should_buy(analysis)
                    if should_buy_signal:
                        buy_candidates.append({
                            'coin': coin,
                            'score': score,
                            'rsi': analysis['rsi'],
                            'momentum': analysis['momentum']
                        })
                
                if buy_candidates:
                    buy_candidates.sort(key=lambda x: -x['score'])
                    best = buy_candidates[0]
                    log(f"买入信号: {best['coin']} (评分:{best['score']}, RSI:{best['rsi']:.0f}, 动量:{best['momentum']:.2%})", "INFO")
                    buy_coin(best['coin'], total)
            
            # 4. 统计
            if start_value > 0:
                pnl = (total - start_value) / start_value * 100
                log(f"累计收益: {pnl:+.2f}%", "INFO")
            
            log(f"扫描间隔: {SCAN_INTERVAL}秒", "INFO")
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            log(f"错误: {e}", "ERROR")
            import traceback; traceback.print_exc()
            time.sleep(10)

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║     Top6 Meme 动态交易策略        ║
║   BOME, TURBO, BONK, FLOKI      ║
║   PEPE, NEIRO                    ║
╚══════════════════════════════════════════════╝
    """)
    try: run()
    except KeyboardInterrupt: print("\n停止...")
    except Exception as e: log(f"FATAL: {e}", "ERROR")
