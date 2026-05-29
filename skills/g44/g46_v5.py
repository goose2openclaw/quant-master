#!/usr/bin/env python3
"""
G46 v5 - 横盘高频版
======================================
核心修复:
1. TP 0.8% → 0.15% (横盘中频繁触发)
2. 分批止盈: 50%在0.1%, 100%在0.15%
3. 动态TP: 横盘0.15%, 趋势0.4%
4. 更低信号阈值: 0.15 抓高频波动
"""
import json, time, urllib.request, hmac, hashlib, math
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g46_v5.log'

# === v5 横盘高频参数 ===
TP_RANGE = 0.0015     # 横盘止盈 0.15%
TP_TREND = 0.004     # 趋势止盈 0.4%
SL_RATE = 0.003      # 止损 0.3%
BUY_SIGNAL_T = 0.15  # 买入阈值 0.15
SELL_SIGNAL_T = -0.15
TRADE_BUDGET = 5
MIN_VALUE = 0.5
MAX_POSITIONS = 8
MAX_HOLD_TIME = 300   # 5分钟超时
COOLDOWN = 20         # 20秒冷却
TX_COST = 0.001

BLACKLIST = ['NEIRO', 'TURBO', 'PEPE', 'FLOKI', 'BOME', 'SHIB', 'DOGE']
POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08,'BNB':0.06,'AVAX':0.05,'ETC':0.04,'NEAR':0.03,'AI':0.03,'ARB':0.03}

running = True
INFO_CACHE = {}
position_entries = {}
position_partial = {}  # 分批止盈记录
last_trade_time = 0

def log(msg):
    ts = datetime.now().strftime('%m-%d %H:%M:%S')
    line = '[' + ts + '] ' + msg
    try:
        with open(LOG_FILE, 'a') as f: f.write(line + chr(10))
    except: pass
    print(line, flush=True)

def signed(endpoint, params=None, method='GET'):
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

def get_exchange_info(sym):
    global INFO_CACHE
    if sym in INFO_CACHE: return INFO_CACHE[sym]
    try:
        url = 'https://api.binance.com/api/v3/exchangeInfo?symbol=' + sym + 'USDT'
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        data = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        for s in data.get('symbols', []):
            if s.get('symbol') == sym + 'USDT':
                info = {'precision': s.get('quotePrecision', 8)}
                for f in s.get('filters', []):
                    if f.get('filterType') == 'LOT_SIZE':
                        info['minQty'] = float(f.get('minQty', 0))
                        info['stepSize'] = float(f.get('stepSize', 0))
                    elif f.get('filterType') == 'NOTIONAL':
                        info['minNotional'] = float(f.get('minNotional', 0))
                INFO_CACHE[sym] = info
                return info
    except: pass
    INFO_CACHE[sym] = {'minQty': 0.1, 'stepSize': 0.1, 'minNotional': 5, 'precision': 8}
    return INFO_CACHE[sym]

def round_to_step(qty, stepSize):
    if stepSize <= 0: return float(int(qty))
    return math.floor(qty / stepSize) * stepSize

def round_up_to_step(qty, stepSize):
    if stepSize <= 0: return float(int(qty))
    return math.ceil(qty / stepSize) * stepSize

def get_klines(sym, interval='5m', limit=100):
    for retry in range(3):
        try:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=' + interval + '&limit=' + str(limit)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            data = json.loads(opener.open(urllib.request.Request(url), timeout=15).read().decode())
            if not data or len(data) < 50: return []
            return data
        except: time.sleep(1)
    return []

def get_all_balances():
    spot_usdt = 0; spot_total = 0; spot_holdings = {}; cross_total = 0; cross_holdings = {}
    try:
        bal = signed('/api/v3/account')
        for a in bal.get('balances', []):
            free = float(a.get('free', 0)); locked = float(a.get('locked', 0))
            total = free + locked; asset = a.get('asset', '')
            if asset == 'USDT':
                spot_usdt = free; spot_total += free
            elif total > 0:
                price = get_price(asset)
                if price > 0:
                    val = total * price; spot_total += val
                    spot_holdings[asset] = {'amount': total, 'value': val, 'price': price, 'source': 'spot'}
    except Exception as e: log('现货账户查询失败: ' + str(e)[:50])
    try:
        cross = signed('/sapi/v1/margin/account')
        for a in cross.get('userAssets', []):
            asset = a.get('asset', ''); free = float(a.get('free', 0)); locked = float(a.get('locked', 0))
            borrowed = float(a.get('borrowed', 0)); interest = float(a.get('interest', 0))
            net = free + locked - borrowed - interest
            if abs(net) > 0.0001:
                price = get_price(asset) if asset != 'USDT' else 1
                val = net * price; cross_total += val
                if asset in spot_holdings:
                    spot_holdings[asset]['amount'] += net; spot_holdings[asset]['value'] += val; spot_holdings[asset]['source'] = 'both'
                else:
                    cross_holdings[asset] = {'amount': net, 'value': val, 'price': price, 'borrowed': borrowed}
    except Exception as e: log('全仓账户查询失败: ' + str(e)[:50])
    all_holdings = {}
    for asset, data in spot_holdings.items(): all_holdings[asset] = data
    for asset, data in cross_holdings.items():
        if asset in all_holdings:
            all_holdings[asset]['cross_net'] = data['amount']; all_holdings[asset]['cross_borrowed'] = data['borrowed']
        else:
            data['source'] = 'cross'; all_holdings[asset] = data
    return spot_usdt, spot_total + cross_total, all_holdings, cross_total

def place_order(sym, side, qty, price):
    global last_trade_time
    info = get_exchange_info(sym)
    stepSize = info.get('stepSize', 0.1); minQty = info.get('minQty', 0.1); minNotional = info.get('minNotional', 5)
    qty = round_to_step(qty, stepSize); order_value = qty * price
    if qty < minQty: return {'success': False}
    if order_value < minNotional - 0.001: return {'success': False}
    prec = max(0, -int(math.log10(stepSize)) if stepSize < 1 else int(math.log10(1/stepSize)) if stepSize > 1 else 0)
    qty_str = ('{:.%df}' % prec).format(qty)
    for attempt in range(3):
        try:
            ts = int(time.time() * 1000)
            params = {'symbol': sym + 'USDT', 'side': side.upper(), 'type': 'MARKET', 'quantity': qty_str, 'timestamp': ts, 'recvWindow': 5000}
            q_str = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
            sig = hmac.new(API_SECRET.encode(), q_str.encode(), hashlib.sha256).hexdigest()
            url = 'https://api.binance.com/api/v3/order?' + q_str + '&signature=' + sig
            req = urllib.request.Request(url, method='POST')
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            try:
                resp = opener.open(req, timeout=10).read().decode()
                last_trade_time = time.time()
                log('  📤 {} {} {} 成功'.format(sym, side.upper(), qty_str))
                return {'success': True}
            except urllib.error.HTTPError as e:
                err_body = e.read().decode()
                try: err_json = json.loads(err_body); err_msg = err_json.get('msg', err_body)
                except: err_msg = err_body
                log('  {} 错误: {}'.format(sym, err_msg[:80]))
                if 'LOT_SIZE' in err_body or 'NOTIONAL' in err_body: INFO_CACHE.pop(sym, None); return {'success': False}
                time.sleep(0.5); continue
        except Exception as e: time.sleep(0.5)
    return {'success': False}

def calc_rsi(closes, period=14):
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]; losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains[-period:])/period if gains else 0.001; avg_loss = sum(losses[-period:])/period if losses else 0.001
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    return 100 - (100/(1+rs))

def calc_bollinger_bands(closes, period=20, std_dev=2):
    if len(closes) < period: return 0, 0, 0, 0.5
    ma = sum(closes[-period:])/period; variance = sum((c - ma)**2 for c in closes[-period:])/period
    std = math.sqrt(variance); upper = ma + std_dev * std; lower = ma - std_dev * std
    position = (closes[-1] - lower)/(upper - lower) if upper != lower else 0.5
    return upper, ma, lower, position

def detect_market(closes, volumes):
    if len(closes) < 50: return 'range', 0.5
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    rsi = calc_rsi(closes)
    range_strength = 1 - min(abs(trend) * 10, 1)
    if bb_pos < 0.2 or bb_pos > 0.8: range_strength *= 0.8
    if rsi < 30 or rsi > 70: range_strength *= 0.7
    range_conf = min(range_strength, 1.0)
    if trend > 0.02: return 'trend', range_conf
    elif trend < -0.02: return 'downtrend', range_conf
    elif range_conf > 0.5: return 'range', range_conf
    return 'range', 0.5

def calc_signal(closes, highs, lows, volumes, market, polymarket=0):
    if len(closes) < 20: return 0
    ma5 = sum(closes[-5:])/5; ma10 = sum(closes[-10:])/10
    trend = (ma5 - ma10)/ma10 if ma10 > 0 else 0
    rsi = calc_rsi(closes)
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-3:])/3 if len(returns) >= 3 else 0
    bb_dev = (closes[-1] - bb_ma) / bb_ma if bb_ma > 0 else 0
    
    # 横盘高频信号
    if market == 'range':
        bb_rev = -bb_dev * 40 if bb_dev < 0 else -bb_dev * 30
        rsi_sig = (35 - rsi) / 35 * 2 if rsi < 35 else -(rsi - 65) / 35 * 2 if rsi > 65 else 0
        mom_rev = -momentum * 40 if abs(momentum) > 0.002 else 0
        return bb_rev * 0.3 + rsi_sig * 0.3 + mom_rev * 0.2 + polymarket * 0.2
    else:
        return trend * 50 + momentum * 80

def main():
    global running, last_trade_time, position_entries, position_partial
    import signal as sig_module
    def signal_handler(s, f): log('G46v5 停止...'); global running; running = False
    sig_module.signal(sig_module.SIGTERM, signal_handler)
    sig_module.signal(sig_module.SIGINT, signal_handler)
    cycle = 0; trades = 0; tp_count = 0; sl_count = 0; buy_count = 0; sell_count = 0; time_count = 0; partial1_count = 0; partial2_count = 0
    total_pnl = 0.0
    
    log('=' * 70)
    log('G46 v5 横盘高频版')
    log('TP: {}%(横盘)/{}%(趋势) | SL: {}% | 信号: {}'.format(TP_RANGE*100, TP_TREND*100, SL_RATE*100, BUY_SIGNAL_T))
    log('最大持仓: {} | 超时: {}s | 冷却: {}s'.format(MAX_POSITIONS, MAX_HOLD_TIME, COOLDOWN))
    log('=' * 70)
    
    while running:
        try:
            cycle += 1
            spot_usdt, total_asset, all_holdings, cross_total = get_all_balances()
            log('')
            log('=== G46v5周期{} | 总资产:\${:.2f} | USDT:\${:.2f} ==='.format(cycle, total_asset, spot_usdt))
            
            for sym in list(position_entries.keys()):
                if sym not in all_holdings:
                    del position_entries[sym]
                    if sym in position_partial: del position_partial[sym]
            
            # 检查持仓退出
            for sym, data in sorted(all_holdings.items(), key=lambda x: -x[1]['value']):
                current = data.get('price', 0)
                avg_cost = current
                free = data.get('amount', 0); value = data.get('value', 0)
                if value < MIN_VALUE: continue
                entry_time = position_entries.get(sym, time.time())
                hold_time = time.time() - entry_time
                pnl_pct = (current - avg_cost) / avg_cost if avg_cost > 0 else 0
                
                # 确定当前TP
                klines = get_klines(sym, '1h', 50)
                if klines:
                    closes = [float(k[4]) for k in klines]
                    market, _ = detect_market(closes, [0]*len(closes))
                    tp_rate = TP_TREND if market == 'trend' else TP_RANGE
                else:
                    tp_rate = TP_RANGE
                
                # 超时退出
                if hold_time > MAX_HOLD_TIME:
                    log('  ⏰ {} 超时退出 ({:.0f}s) ({:+.2f}%)'.format(sym, hold_time, pnl_pct*100))
                    if place_order(sym, 'SELL', free, current).get('success'):
                        time_count += 1; trades += 1; sell_count += 1
                        if sym in position_entries: del position_entries[sym]
                        if sym in position_partial: del position_partial[sym]
                
                # 分批止盈1: 50%在0.1%
                elif pnl_pct >= 0.001 and position_partial.get(sym, 0) < 1:
                    partial_qty = round_to_step(free * 0.5, 0.001)
                    if partial_qty > 0.001:
                        log('  🎚️ {} 分批止盈50%@0.1% ({:+.2f}%)'.format(sym, pnl_pct*100))
                        if place_order(sym, 'SELL', partial_qty, current).get('success'):
                            partial1_count += 1
                            position_partial[sym] = 1
                            trades += 1; sell_count += 1
                
                # 全止盈
                elif pnl_pct >= tp_rate:
                    log('  🎯 {} 止盈! ({:+.2f}%)'.format(sym, pnl_pct*100))
                    if place_order(sym, 'SELL', free, current).get('success'):
                        tp_count += 1; trades += 1; sell_count += 1
                        if sym in position_entries: del position_entries[sym]
                        if sym in position_partial: del position_partial[sym]
                
                # 止损
                elif pnl_pct <= -SL_RATE:
                    log('  🛑 {} 止损! ({:+.2f}%)'.format(sym, pnl_pct*100))
                    if place_order(sym, 'SELL', free, current).get('success'):
                        sl_count += 1; trades += 1; sell_count += 1
                        if sym in position_entries: del position_entries[sym]
                        if sym in position_partial: del position_partial[sym]
            
            # 冷却期
            if time.time() - last_trade_time < COOLDOWN:
                time.sleep(5); continue
            
            # 扫描
            scan_syms = list(all_holdings.keys()) + ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB','AVAX','ETC','NEAR','AI','ARB']
            prices = {s: get_price(s) for s in set(scan_syms)}
            strong_buys = []; strong_sells = []
            for sym in prices.keys():
                if sym == 'USDT': continue
                klines = get_klines(sym, '5m', 50)
                if not klines or len(klines) < 20: continue
                try:
                    closes = [float(k[4]) for k in klines]; volumes = [float(k[5]) for k in klines]
                    highs = [float(k[2]) for k in klines]; lows = [float(k[3]) for k in klines]
                    market, _ = detect_market(closes, volumes)
                    pm = POLYMARKET.get(sym, 0)
                    sig = calc_signal(closes, highs, lows, volumes, market, pm)
                    if sig > BUY_SIGNAL_T: strong_buys.append({'sym': sym, 'signal': sig, 'price': prices[sym]})
                    elif sig < -BUY_SIGNAL_T: strong_sells.append({'sym': sym, 'signal': sig, 'price': prices[sym]})
                except: continue
            strong_buys.sort(key=lambda x: -x['signal']); strong_sells.sort(key=lambda x: x['signal'])
            
            # 买入
            open_pos = len([s for s in all_holdings.keys() if all_holdings[s].get('value', 0) >= MIN_VALUE])
            for d in strong_buys[:4]:
                sym = d['sym']; price = d['price']; sig = d['signal']
                if sym in BLACKLIST: log("  ⛔ {} 黑名单".format(sym)); continue
                if sym in all_holdings and all_holdings[sym].get("value", 0) >= MIN_VALUE: log("  ⛽ {} 已持仓，跳过".format(sym)); continue
                if open_pos >= MAX_POSITIONS: log("  ⚠️ 满仓"); break
                if spot_usdt < TRADE_BUDGET: break
                budget = min(TRADE_BUDGET, spot_usdt * 0.9)
                info = get_exchange_info(sym); min_notional = info.get('minNotional', 5); step_size = info.get('stepSize', 0.1)
                qty = max(budget / price, min_notional / price); qty = round_up_to_step(qty, step_size)
                order_value = qty * price
                if order_value < min_notional - 0.001: continue
                if qty <= 0: continue
                log('  📥 {} 信号:{:.2f} \${:.2f}'.format(sym, sig, order_value))
                if place_order(sym, 'BUY', qty, price).get('success'):
                    buy_count += 1; trades += 1; spot_usdt -= budget; open_pos += 1
                    position_entries[sym] = time.time()
            
            # 卖出
            for d in strong_sells[:2]:
                sym = d['sym']
                if sym in all_holdings and all_holdings[sym].get('value', 0) >= MIN_VALUE:
                    info = get_exchange_info(sym); free = all_holdings[sym]['amount']
                    min_qty = info.get('minQty', 0.1); min_notional = info.get('minNotional', 5); step_size = info.get('stepSize', 0.1)
                    qty = round_to_step(free, step_size); value = qty * prices.get(sym, 0)
                    if qty >= min_qty and value >= min_notional:
                        log('  📤 {} 信号:{:.2f}'.format(sym, d['signal']))
                        if place_order(sym, 'SELL', qty, prices.get(sym, 0)).get('success'):
                            sell_count += 1; trades += 1
                            if sym in position_entries: del position_entries[sym]
                            if sym in position_partial: del position_partial[sym]
            
            if strong_buys or strong_sells: log('【信号】买:{} 卖:{}'.format(len(strong_buys), len(strong_sells)))
            if cycle % 10 == 0:
                log('统计: 周期{} 交易{} 买{} 卖{} 止盈{} 止损{} 超时{} 分批{}'.format(cycle, trades, buy_count, sell_count, tp_count, sl_count, time_count, partial1_count))
            for _ in range(15):
                if not running: break
                time.sleep(1)
        except Exception as e:
            log('异常: ' + str(e)[:80]); time.sleep(5)
    log('v5停止 - 周期{} 交易{} 买{} 止盈{} 止损{} 超时{} 分批{}'.format(cycle, trades, buy_count, tp_count, sl_count, time_count, partial1_count))

if __name__ == '__main__':
    main()
