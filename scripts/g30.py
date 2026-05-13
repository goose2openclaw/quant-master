#!/usr/bin/env python3
"""
G30 - 全域智能扫描自动交易系统
G27全部功能 + G29自动交易 + 全域币种扫描
"""
import urllib.request, hmac, hashlib, time, json
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g30.log"

# 扫描币种列表
MAJOR_COINS = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','DOT','LINK','UNI','AVAX','MATIC','ATOM','LTC','ETC','AAVE','APT','NEAR','FIL','ICP','INJ','TIA','SEI','SUI','OP','ARB','LDO','CRV','RDNT','ENS']
MEME_COINS = ['PEPE','SHIB','FLOKI','WIF','BABYDOGE','COOKIE','AI','NEIRO','BOME','TURBO','PUMP','BONK']
MIN_TRADE_USD = 5
MIN_NEW_COIN_VALUE = 10

def log(msg):
    ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def api_get(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())

def api_signed_get(endpoint, params=None):
    ts = int(time.time() * 1000)
    base = {"timestamp": ts, "recvWindow": 5000}
    if params: base.update(params)
    q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=15).read().decode())

def api_signed_post(endpoint, params=None):
    ts = int(time.time() * 1000)
    base = {"timestamp": ts, "recvWindow": 5000}
    if params: base.update(params)
    q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
    req = urllib.request.Request(url, method="POST")
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=15).read().decode())

def get_price(symbol):
    try:
        return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

def get_klines(symbol, interval, limit):
    try:
        return api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    except: return []

def get_rsi(symbol):
    data = get_klines(symbol, '1h', 50)
    if len(data) < 15: return 50
    closes = [float(k[4]) for k in data]
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d if d>0 else 0 for d in deltas[-14:]]
    losses = [-d if d<0 else 0 for d in deltas[-14:]]
    avg_gain = sum(gains)/14
    avg_loss = sum(losses)/14
    if avg_loss == 0: return 100
    return 100-(100/(1+avg_gain/avg_loss))

def get_momentum(symbol):
    data = get_klines(symbol, '1h', 25)
    if len(data) < 24: return 0
    return ((float(data[-1][4]) - float(data[-24][4])) / float(data[-24][4])) * 100

def oracle_score(rsi, momentum, coin_type='major'):
    """Oracle评分系统 - 主流币和Meme币不同阈值"""
    score = 0
    
    # RSI评分 (Meme币更敏感)
    if coin_type == 'meme':
        if rsi < 25: score += 50
        elif rsi < 30: score += 40
        elif rsi < 35: score += 25
        elif rsi < 40: score += 10
        elif rsi > 75: score -= 50
        elif rsi > 70: score -= 35
        elif rsi > 65: score -= 20
        elif rsi > 60: score -= 10
    else:  # major
        if rsi < 30: score += 50
        elif rsi < 35: score += 35
        elif rsi < 40: score += 20
        elif rsi < 45: score += 10
        elif rsi > 70: score -= 50
        elif rsi > 65: score -= 35
        elif rsi > 60: score -= 20
        elif rsi > 55: score -= 10
    
    # 动量评分
    if momentum < -5: score += 35
    elif momentum < -3: score += 25
    elif momentum < -1: score += 15
    elif momentum > 5: score -= 35
    elif momentum > 3: score -= 25
    elif momentum > 1: score -= 15
    
    return score

def get_account():
    data = api_signed_get("/api/v3/account")
    result = {'usdt': 0, 'coins': {}}
    for b in data.get('balances', []):
        free = float(b.get('free', 0))
        if free > 0.0001:
            if b['asset'] == 'USDT':
                result['usdt'] = free
            else:
                result['coins'][b['asset']] = free
    return result

def place_order(symbol, side, quantity):
    params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
    return api_signed_post("/api/v3/order", params)

def get_total_value(balances):
    total = balances['usdt']
    for coin, qty in balances['coins'].items():
        price = get_price(f"{coin}USDT")
        if price > 0:
            total += qty * price
    return total

def format_qty(coin, qty):
    """根据币种格式化数量"""
    if coin in ['BOME', 'NEIRO']:
        return int(qty / 100) * 100
    elif coin in ['PUMP', 'PEPE', 'SHIB', 'FLOKI', 'WIF', 'BONK', 'AI', 'COOKIE', 'BABYDOGE']:
        return int(qty / 1000) * 1000
    elif coin == 'TURBO':
        return int(qty / 1000) * 1000
    else:
        return int(qty * 100) / 100

def main():
    log("=" * 80)
    log("🌟 G30 - 全域智能扫描自动交易系统")
    log("=" * 80)
    
    while True:
        try:
            balances = get_account()
            total = get_total_value(balances)
            usdt = balances['usdt']
            
            log(f"\n💰 总资产: ${total:.2f} | USDT: ${usdt:.2f}")
            
            # ==================== 全域扫描 ====================
            log(f"\n🔍 全域扫描中 ({len(MAJOR_COINS)+len(MEME_COINS)} 个币种)...")
            
            major_signals = []
            meme_signals = []
            current_holdings = set(balances['coins'].keys())
            
            # 扫描主流币
            for coin in MAJOR_COINS:
                price = get_price(f"{coin}USDT")
                if price <= 0: continue
                rsi = get_rsi(f"{coin}USDT")
                momentum = get_momentum(f"{coin}USDT")
                score = oracle_score(rsi, momentum, 'major')
                
                in_portfolio = coin in current_holdings
                qty = balances['coins'].get(coin, 0)
                value = qty * price if in_portfolio else 0
                
                major_signals.append({
                    'coin': coin, 'price': price, 'rsi': rsi, 'momentum': momentum,
                    'score': score, 'type': 'major', 'in_portfolio': in_portfolio,
                    'qty': qty, 'value': value
                })
                time.sleep(0.05)
            
            # 扫描Meme币
            for coin in MEME_COINS:
                price = get_price(f"{coin}USDT")
                if price <= 0: continue
                rsi = get_rsi(f"{coin}USDT")
                momentum = get_momentum(f"{coin}USDT")
                score = oracle_score(rsi, momentum, 'meme')
                
                in_portfolio = coin in current_holdings
                qty = balances['coins'].get(coin, 0)
                value = qty * price if in_portfolio else 0
                
                meme_signals.append({
                    'coin': coin, 'price': price, 'rsi': rsi, 'momentum': momentum,
                    'score': score, 'type': 'meme', 'in_portfolio': in_portfolio,
                    'qty': qty, 'value': value
                })
                time.sleep(0.05)
            
            # ==================== 排序输出 ====================
            major_signals.sort(key=lambda x: x['score'], reverse=True)
            meme_signals.sort(key=lambda x: x['score'], reverse=True)
            
            log(f"\n📊 【主流币信号榜】")
            log(f"{'币种':<8} {'RSI':<6} {'动量':<8} {'评分':<6} {'持仓':<12} {'操作'}")
            log("-" * 60)
            for s in major_signals[:10]:
                status = f"${s['value']:.2f}" if s['in_portfolio'] else "未持仓"
                if s['score'] >= 50: op = "🚀 强烈买入"
                elif s['score'] >= 30: op = "🟢 买入"
                elif s['score'] >= 10: op = "🟡 观察"
                elif s['score'] >= -10: op = "⚪ 持有"
                elif s['score'] >= -30: op = "🟡 减仓"
                else: op = "🔴 卖出"
                flag = "👉" if not s['in_portfolio'] and s['score'] >= 30 else ""
                log(f"{s['coin']:<8} {s['rsi']:>5.1f} {s['momentum']:>+7.1f}% {s['score']:>+5} {status:<12} {op}{flag}")
            
            log(f"\n📊 【Meme币信号榜】")
            log(f"{'币种':<8} {'RSI':<6} {'动量':<8} {'评分':<6} {'持仓':<12} {'操作'}")
            log("-" * 60)
            for s in meme_signals[:10]:
                status = f"${s['value']:.2f}" if s['in_portfolio'] else "未持仓"
                if s['score'] >= 50: op = "🚀 强烈买入"
                elif s['score'] >= 30: op = "🟢 买入"
                elif s['score'] >= 10: op = "🟡 观察"
                elif s['score'] >= -10: op = "⚪ 持有"
                elif s['score'] >= -30: op = "🟡 减仓"
                else: op = "🔴 卖出"
                flag = "👉" if not s['in_portfolio'] and s['score'] >= 30 else ""
                log(f"{s['coin']:<8} {s['rsi']:>5.1f} {s['momentum']:>+7.1f}% {s['score']:>+5} {status:<12} {op}{flag}")
            
            # ==================== 自主决策执行 ====================
            log(f"\n🤖 自主决策中...")
            
            # 1. 卖出低分持仓 (主流币 < -20, Meme币 < -30)
            for s in major_signals + meme_signals:
                if not s['in_portfolio']: continue
                if s['type'] == 'major' and s['score'] < -20 and s['value'] > MIN_TRADE_USD:
                    log(f"\n📤 卖出 {s['coin']} (评分:{s['score']}, 价值:${s['value']:.2f})")
                    sell_qty = format_qty(s['coin'], s['qty'] * 0.5)  # 卖出一半
                    if sell_qty > 0:
                        result = place_order(f"{s['coin']}USDT", "SELL", sell_qty)
                        if result and 'orderId' in result:
                            log(f"   ✅ 卖出 {sell_qty} {s['coin']} @ ${s['price']:.6f}")
                            balances = get_account()
                            usdt = balances['usdt']
                        else:
                            log(f"   ❌ 失败")
            
            # 2. 买入高评分未持仓币种
            if usdt < 30:
                # 资金不足，卖出评分最低的持仓
                for s in sorted(major_signals + meme_signals, key=lambda x: x['score']):
                    if s['in_portfolio'] and s['value'] > MIN_NEW_COIN_VALUE * 2:
                        log(f"\n💱 调配资金: 卖出 {s['coin']} 获取USDT")
                        sell_qty = format_qty(s['coin'], s['qty'] * 0.3)  # 卖出30%
                        if sell_qty > 0:
                            result = place_order(f"{s['coin']}USDT", "SELL", sell_qty)
                            if result and 'orderId' in result:
                                log(f"   ✅ 卖出 {sell_qty} {s['coin']} @ ${s['price']:.6f}")
                                balances = get_account()
                                usdt = balances['usdt']
                                if usdt >= 30: break
            
            # 3. 买入新币种 (评分>=40)
            if usdt > MIN_NEW_COIN_VALUE:
                # 优先买入主流币
                for s in major_signals:
                    if not s['in_portfolio'] and s['score'] >= 40:
                        buy_value = min(usdt * 0.4, 50)  # 最多投入40%或$50
                        buy_qty = format_qty(s['coin'], buy_value / s['price'])
                        min_qty = 0.001 if s['coin'] not in ['BOME','TURBO','PUMP'] else 1000
                        if buy_qty >= min_qty:
                            log(f"\n📥 买入 {s['coin']} (评分:{s['score']}, 新增)")
                            result = place_order(f"{s['coin']}USDT", "BUY", buy_qty)
                            if result and 'orderId' in result:
                                log(f"   ✅ 买入 {buy_qty} {s['coin']} @ ${s['price']:.6f} = ${buy_value:.2f}")
                                balances = get_account()
                                usdt = balances['usdt']
                                break
                
                # Meme币 (评分>=50)
                for s in meme_signals:
                    if not s['in_portfolio'] and s['score'] >= 50:
                        buy_value = min(usdt * 0.3, 30)  # 最多投入30%或$30
                        buy_qty = format_qty(s['coin'], buy_value / s['price'])
                        min_qty = 1000
                        if buy_qty >= min_qty:
                            log(f"\n📥 买入 {s['coin']} (评分:{s['score']}, Meme)")
                            result = place_order(f"{s['coin']}USDT", "BUY", buy_qty)
                            if result and 'orderId' in result:
                                log(f"   ✅ 买入 {buy_qty} {s['coin']} @ ${s['price']:.6f} = ${buy_value:.2f}")
                                balances = get_account()
                                usdt = balances['usdt']
                                break
            
            # 4. 增持已有高分持仓
            if usdt > MIN_TRADE_USD:
                for s in major_signals:
                    if s['in_portfolio'] and s['score'] >= 50 and s['value'] < total * 0.15:
                        buy_value = usdt * 0.3
                        buy_qty = format_qty(s['coin'], buy_value / s['price'])
                        if buy_qty >= 0.001:
                            log(f"\n📥 增持 {s['coin']} (评分:{s['score']})")
                            result = place_order(f"{s['coin']}USDT", "BUY", buy_qty)
                            if result and 'orderId' in result:
                                log(f"   ✅ 增持 {buy_qty} {s['coin']} @ ${s['price']:.6f}")
                                break
            
            log(f"\n⏱️ 等待30秒...")
            time.sleep(30)
            
        except Exception as e:
            log(f"❌ 错误: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
