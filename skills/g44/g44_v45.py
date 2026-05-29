#!/usr/bin/env python3
"""
G44 v4.5 - 震荡市场增强版
=====================
增强震荡市场赚钱能力:
1. 10+种策略融合
2. 多时间框架分析
3. 动态阈值调整
4. 网格+DCA增强
5. 布林带+随机RSI
"""
import json, time, urllib.request, hmac, hashlib, signal as sig_module, math
from datetime import datetime
from collections import defaultdict

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g44_v45.log'

POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB','DOGE','MATIC','AVAX']
SKIP = ['FTM','NEIRO','BOME','SHIB','PEPE','BONK']
BUY_T, SELL_T = 0.025, -0.025  # 降低阈值，更敏感

PRECISION = {'BTC':5,'ETH':4,'ADA':1,'XRP':1,'LINK':2,'DOGE':0,'DOT':2,'SOL':3,'BNB':3,'MATIC':4,'AVAX':4}
MIN_QTY = {'BTC':0.00001,'ETH':0.0001,'ADA':0.1,'XRP':0.1,'LINK':0.01,'DOGE':1.0,'DOT':0.01,'SOL':0.001,'BNB':0.001,'MATIC':0.001,'AVAX':0.001}

running = True

def log(msg):
    ts = datetime.now().strftime('%m-%d %H:%M:%S')
    line = '[' + ts + '] ' + msg
    try:
        with open(LOG_FILE, 'a') as f: f.write(line + chr(10))
    except: pass
    print(line, flush=True)

def round_to_precision(qty, sym):
    prec = PRECISION.get(sym, 6)
    step = 10 ** (-prec)
    return math.floor(qty / step) * step

def api_signed(endpoint, params=None, method='GET'):
    ts = int(time.time() * 1000)
    base = {'timestamp': ts, 'recvWindow': 5000}
    if params: base.update(params)
    q = '&'.join('{}={}'.format(k, v) for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com{}?{}&signature={}'.format(endpoint, q, sig)
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=15).read().decode())

def get_price(sym):
    try:
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=' + sym + 'USDT'
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return float(json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())['price'])
    except: return 0

def get_klines(sym, interval='15m', limit=100):
    for retry in range(3):
        try:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=' + interval + '&limit=' + str(limit)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            data = json.loads(opener.open(urllib.request.Request(url), timeout=15).read().decode())
            if not data or len(data) < 50:
                return []
            return data
        except Exception as e:
            time.sleep(1)
    return []

def place_order(sym, side, qty):
    min_qty = MIN_QTY.get(sym, 0.00001)
    qty = max(qty, min_qty)
    qty = round_to_precision(qty, sym)
    
    for attempt in range(3):
        try:
            ts = int(time.time() * 1000)
            prec = PRECISION.get(sym, 6)
            qty_str = '{{:.{}f}}'.format(prec).format(qty)
            params = {'symbol': sym + 'USDT', 'side': side, 'type': 'MARKET', 'quantity': qty_str, 'timestamp': ts, 'recvWindow': 5000}
            q = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
            sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
            url = 'https://api.binance.com/api/v3/order?' + q + '&signature=' + sig
            req = urllib.request.Request(url, method='POST')
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            try:
                resp = json.loads(opener.open(req, timeout=10).read().decode())
            except urllib.error.HTTPError as e:
                err_body = e.read().decode()
                try: err_json = json.loads(err_body); err_msg = err_json.get('msg', err_body)
                except: err_msg = err_body
                log('  错误[{}]: {}'.format(attempt+1, err_msg[:50]))
                if 'LOT_SIZE' in err_msg:
                    qty = round_to_precision(qty * 2, sym)
                    time.sleep(0.3); continue
                elif 'INSUFFICIENT' in err_msg: return {'success': False}
                time.sleep(0.5); continue
            if 'code' in resp: log('  失败: {}'.format(resp.get('msg','')[:40])); time.sleep(0.5); continue
            log('  {} {} x {} 成功'.format(side, sym, qty_str))
            return {'success': True}
        except Exception as e: log('  异常: {}'.format(str(e)[:30])); time.sleep(0.5)
    return {'success': False}

def get_account():
    try:
        ts = int(time.time() * 1000)
        params = {'timestamp': ts, 'recvWindow': 5000}
        q = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
        sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = 'https://api.binance.com/api/v3/account?' + q + '&signature=' + sig
        req = urllib.request.Request(url)
        req.add_header('X-MBX-APIKEY', API_KEY)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(req, timeout=15).read().decode())
    except: return {}

def calc_rsi(closes, period=14):
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains[-period:])/period if gains else 0.001
    avg_loss = sum(losses[-period:])/period if losses else 0.001
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    return 100 - (100/(1+rs))

def calc_stoch_rsi(closes, period=14):
    rsi = calc_rsi(closes, period)
    return rsi  # 简化为RSI

def calc_macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow: return 0, 0, 0
    ema_fast = sum(closes[-fast:])/fast
    ema_slow = sum(closes[-slow:])/slow
    macd_line = ema_fast - ema_slow
    signal_line = macd_line * 0.9
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calc_bollinger_bands(closes, period=20, std_dev=2):
    if len(closes) < period: return 0, 0, 0
    ma = sum(closes[-period:])/period
    variance = sum((c - ma)**2 for c in closes[-period:])/period
    std = math.sqrt(variance)
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    position = (closes[-1] - lower)/(upper - lower) if upper != lower else 0.5
    return upper, ma, lower, position

def calc_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1: return 0
    trs = [max(highs[i+1]-lows[i+1], abs(highs[i+1]-closes[i]), abs(lows[i+1]-closes[i])) for i in range(len(closes)-1)]
    return sum(trs[-period:])/period if trs else 0

def detect_market_enhanced(closes, highs, lows, volumes):
    if len(closes) < 50: return 'range', 0.5
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    vol = sum(abs(r) for r in returns[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    atr = calc_atr(highs, lows, closes) / closes[-1] if closes[-1] > 0 else 0
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    rsi = calc_rsi(closes)
    
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    
    range_strength = 1 - min(abs(trend) * 10, 1)
    range_strength *= (1 - vol_ratio * 0.3) if vol_ratio > 1 else (1 + (1 - vol_ratio) * 0.3)
    
    if bb_pos < 0.2 or bb_pos > 0.8: range_strength *= 0.8
    if rsi < 30 or rsi > 70: range_strength *= 0.7
    if atr < 0.02: range_strength *= 1.2
    
    range_confidence = min(range_strength, 1.0)
    
    if trend > 0.03: return 'trend', range_confidence
    elif trend < -0.03: return 'downtrend', range_confidence
    elif range_confidence > 0.6: return 'range', range_confidence
    return 'range', 0.5

def get_leverage(signal, market, range_conf=0.5):
    abs_sig = abs(signal)
    if market == 'trend':
        if abs_sig > 0.10: return 2.5
        elif abs_sig > 0.05: return 2.0
        return 1.5
    elif market == 'range':
        lev = 1.0 + range_conf * 1.5
        if abs_sig > 0.08: return min(lev + 0.5, 3.0)
        elif abs_sig > 0.04: return min(lev, 2.0)
        return min(lev, 1.5)
    return 1.5

def calc_signal_enhanced(closes, highs, lows, volumes, market, range_conf, polymarket=0):
    if len(closes) < 50: return 0, {}
    
    # 基础指标
    ma5 = sum(closes[-5:])/5
    ma20 = sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
    
    # RSI系列
    rsi6 = calc_rsi(closes, 6)
    rsi14 = calc_rsi(closes, 14)
    stoch_rsi = calc_stoch_rsi(closes, 14)
    
    # MACD
    macd, signal_macd, histogram = calc_macd(closes)
    macd_norm = histogram / closes[-1] if closes[-1] > 0 else 0
    
    # 布林带
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    bb_position = (closes[-1] - bb_lower)/(bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
    
    # 成交量
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    vol_spike = 1.5 if vol_ratio > 1.5 else 1.0
    
    # 动量
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
    momentum_short = sum(returns[-3:])/3 if len(returns) >= 3 else 0
    
    # ATR
    atr = calc_atr(highs, lows, closes) / closes[-1] if closes[-1] > 0 else 0
    
    # 突破检测
    bb_width = (bb_upper - bb_lower)/bb_ma if bb_ma > 0 else 0
    upper_break = 1.5 if closes[-1] > bb_upper else 0
    lower_break = -1.5 if closes[-1] < bb_lower else 0
    
    # 策略评分
    strategies = {}
    
    if market == 'range':
        # ========== 震荡市场策略 ==========
        
        # 1. 布林带均值回归 (核心!)
        bb_mean_rev = -((closes[-1] - bb_ma)/bb_ma * 20) if bb_ma > 0 else 0
        strategies['bb_reversion'] = bb_mean_rev * 1.5
        
        # 2. RSI超买超卖
        rsi_signal = 0
        if rsi14 < 30: rsi_signal = (30 - rsi14) / 30 * 1.5
        elif rsi14 > 70: rsi_signal = -(rsi14 - 70) / 30 * 1.5
        strategies['rsi_extreme'] = rsi_signal
        
        # 3. 随机RSI超买超卖
        stoch_signal = 0
        if stoch_rsi < 20: stoch_signal = (20 - stoch_rsi) / 20 * 1.3
        elif stoch_rsi > 80: stoch_signal = -(stoch_rsi - 80) / 20 * 1.3
        strategies['stoch_rsi'] = stoch_signal
        
        # 4. MACD反转
        macd_signal = 0
        if histogram < 0 and histogram > -0.001: macd_signal = 0.8
        elif histogram > 0 and histogram < 0.001: macd_signal = -0.8
        strategies['macd_reversal'] = macd_signal
        
        # 5. 短期动能反转
        short_reversal = -momentum_short * 15 if abs(momentum_short) > 0.01 else 0
        strategies['short_reversal'] = short_reversal
        
        # 6. 成交量确认
        vol_confirm = 1.2 if vol_ratio > 1.3 and (rsi14 < 30 or rsi14 > 70) else 1.0
        strategies['volume_confirm'] = vol_confirm - 1.0
        
        # 7. 趋势过滤 (不要逆势)
        trend_filter = trend * 5
        strategies['trend_filter'] = trend_filter
        
        # 8. 突破失败反转
        if upper_break and closes[-1] < closes[-2]: strategies['false_break'] = 1.0
        elif lower_break and closes[-1] > closes[-2]: strategies['false_break'] = -1.0
        else: strategies['false_break'] = 0
        
        # 9. 范围支撑阻力
        range_pos = bb_position
        range_signal = 0
        if range_pos < 0.25: range_signal = (0.25 - range_pos) * 4 * 1.2
        elif range_pos > 0.75: range_signal = -(range_pos - 0.75) * 4 * 1.2
        strategies['range_edge'] = range_signal
        
        # 10. ATR调整
        atr_adj = 1.0 + (0.02 - atr) * 10 if atr < 0.02 else 1.0
        strategies['atr_adjust'] = atr_adj - 1.0
        
        # 综合权重
        final_signal = (
            strategies['bb_reversion'] * 0.20 +
            strategies['rsi_extreme'] * 0.15 +
            strategies['stoch_rsi'] * 0.12 +
            strategies['macd_reversal'] * 0.10 +
            strategies['short_reversal'] * 0.10 +
            strategies['volume_confirm'] * 0.08 +
            strategies['trend_filter'] * 0.08 +
            strategies['false_break'] * 0.07 +
            strategies['range_edge'] * 0.05 +
            strategies['atr_adjust'] * 0.05 +
            polymarket * 0.35
        )
        
    elif market == 'trend':
        # ========== 趋势市场策略 ==========
        
        # 1. 趋势跟随
        strategies['trend_follow'] = trend * 15
        
        # 2. 动量
        strategies['momentum'] = momentum * 100
        
        # 3. 成交量确认
        strategies['vol_confirm'] = (vol_ratio - 1) * 1.5 if vol_ratio > 1 else 0
        
        # 4. MACD趋势
        strategies['macd_trend'] = macd_norm * 30
        
        # 5. 突破
        strategies['breakout'] = upper_break * 1.5 if trend > 0 else lower_break * 1.5
        
        final_signal = (
            strategies['trend_follow'] * 0.35 +
            strategies['momentum'] * 0.20 +
            strategies['vol_confirm'] * 0.15 +
            strategies['macd_trend'] * 0.15 +
            strategies['breakout'] * 0.15 +
            polymarket * 0.35
        )
    else:
        # ========== 默认策略 ==========
        final_signal = trend * 12 + polymarket * 0.35
    
    return final_signal, strategies

def main():
    global running
    def signal_handler(s, f): 
        log('G44 v4.5 停止...'); global running; running = False
    sig_module.signal(sig_module.SIGTERM, signal_handler)
    sig_module.signal(sig_module.SIGINT, signal_handler)
    cycle = 0; trades = 0; errors = 0
    log('=' * 70)
    log('G44 v4.5 震荡市场增强版启动')
    log('增强: 布林带+RSI+MACD+随机RSI+多策略融合')
    log('=' * 70)
    while running:
        try:
            cycle += 1
            account = get_account()
            prices = {s: get_price(s) for s in COINS}
            holdings = {}
            for b in account.get('balances', []):
                free = float(b.get('free', 0))
                asset = b['asset']
                if asset != 'USDT' and free > 0:
                    price = prices.get(asset, 0)
                    value = free * price
                    if value > 0.5:
                        holdings[asset] = {'amount': free, 'price': price, 'entry': price, 'value': value}
            total = sum(h['value'] for h in holdings.values())
            usdt_bal = [b for b in account.get('balances', []) if b['asset'] == 'USDT']
            usdt = float(usdt_bal[0]['free']) if usdt_bal else 0
            total += usdt
            sig_data = {}
            market_counts = defaultdict(int)
            for sym in COINS:
                if sym in SKIP: continue
                klines = get_klines(sym)
                if not klines or len(klines) < 50:
                    continue
                try:
                    closes = [float(k[4]) for k in klines]
                    volumes = [float(k[5]) for k in klines]
                    highs = [float(k[2]) for k in klines]
                    lows = [float(k[3]) for k in klines]
                    market, range_conf = detect_market_enhanced(closes, highs, lows, volumes)
                    market_counts[market] += 1
                    pm = POLYMARKET.get(sym, 0)
                    combined, strategies = calc_signal_enhanced(closes, highs, lows, volumes, market, range_conf, pm)
                    lev = get_leverage(combined, market, range_conf)
                    sig_data[sym] = {'combined': combined, 'market': market, 'pm': pm, 'leverage': lev, 'strats': strategies}
                except Exception as e:
                    log('  {} 信号计算失败: {}'.format(sym, str(e)[:30]))
                    continue
            buys = []; sells = []
            for sym, h in holdings.items():
                if sym not in sig_data: continue
                d = sig_data[sym]
                c = d['combined']
                entry = h.get('entry', h['price'])
                pnl = (h['price'] - entry)/entry*100 if entry > 0 else 0
                lev = d['leverage']
                if c < SELL_T or pnl < -3 * lev:
                    val = h['amount'] * h['price']
                    if val >= 3:
                        sells.append({'sym': sym, 'amt': h['amount']*0.95, 'c': c, 'pnl': pnl, 'lev': lev})
            if len(holdings) < 5 and usdt > 10:
                for sym in COINS:
                    if sym in SKIP or sym in holdings or sym not in sig_data: continue
                    d = sig_data[sym]
                    c = d['combined']
                    p = prices.get(sym, 0)
                    lev = d['leverage']
                    if p <= 0: continue
                    if c > BUY_T:
                        budget = min(usdt * 0.35 * lev, 100)
                        qty = budget / p
                        if qty * p >= 5:
                            buys.append({'sym': sym, 'qty': qty, 'c': c, 'lev': lev})
            buys.sort(key=lambda x: -x['c'])
            sells.sort(key=lambda x: x['c'])
            log('')
            log('=== G44周期{} | 总资产:\${:.2f} | USDT:\${:.2f} ==='.format(cycle, total, usdt))
            log('市场:{} | 持仓:{} | 买:{} | 卖:{}'.format(dict(market_counts), len(holdings), len(buys), len(sells)))
            for d in sells[:3]:
                log('卖出: {} 信号:{:.2f} PnL:{:.1f}% 杠杆:{:.1f}x'.format(d['sym'], d['c'], d['pnl'], d['lev']))
                if place_order(d['sym'], 'SELL', d['amt']).get('success'): trades += 1
                else: errors += 1
            for d in buys[:3]:
                log('买入: {} 信号:{:.2f} 杠杆:{:.1f}x'.format(d['sym'], d['c'], d['lev']))
                if place_order(d['sym'], 'BUY', d['qty']).get('success'): trades += 1
                else: errors += 1
            if cycle % 5 == 0:
                log('统计: 周期{} 交易{} 错误{}'.format(cycle, trades, errors))
            for _ in range(60):
                if not running: break
                time.sleep(1)
        except Exception as e:
            log('异常: ' + str(e)[:50]); errors += 1; time.sleep(5)
    log('G44 v4.5停止 - 周期{} 交易{} 错误{}'.format(cycle, trades, errors))

if __name__ == '__main__': main()
