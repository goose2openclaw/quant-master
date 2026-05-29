#!/usr/bin/env python3
"""
G46 v4 - 高收益优化版
======================================
优化:
1. TP 0.4% → 0.8% (让利润奔跑)
2. 添加分批止盈 (30%仓位在0.3%止盈)
3. 追踪止损 (锁定50%利润)
4. 信号强度加权仓位
"""
import json, time, urllib.request, hmac, hashlib, math
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g46_v4.log'

# === v4 高收益参数 ===
TP_RATE = 0.008       # 止盈 0.8% (原0.4%)
TP_PARTIAL = 0.003   # 分批止盈 0.3%
SL_RATE = 0.006       # 止损 0.6%
BUY_SIGNAL_T = 0.25  # 买入阈值 0.25 (更低)
SELL_SIGNAL_T = -0.25 # 卖出阈值 -0.25
TRADE_BUDGET = 5
MIN_VALUE = 1
MAX_POSITIONS = 6
MAX_HOLD_TIME = 600
COOLDOWN = 45
TX_COST = 0.001

BLACKLIST = ['NEIRO', 'TURBO', 'PEPE', 'FLOKI', 'BOME', 'SHIB', 'DOGE']
POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08,'BNB':0.06,'AVAX':0.05,'ETC':0.04,'NEAR':0.03,'AI':0.03,'ARB':0.03}

running = True
INFO_CACHE = {}
position_entries = {}
position_high = {}  # 追踪最高价
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

def get_klines(sym, interval='15m', limit=100):
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
    if trend > 0.03: return 'trend', range_conf
    elif trend < -0.03: return 'downtrend', range_conf
    elif range_conf > 0.6: return 'range', range_conf
    return 'range', 0.5

def calc_signal_v4(closes, highs, lows, volumes, market, polymarket=0):
    """
    v4信号 - 高收益优化
    """
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    rsi14 = calc_rsi(closes)
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum_short = sum(returns[-3:])/3 if len(returns) >= 3 else 0
    bb_deviation = (closes[-1] - bb_ma) / bb_ma if bb_ma > 0 else 0
    
    if market == 'range':
        bb_mean_rev = -bb_deviation * 35 if bb_deviation < 0 else -bb_deviation * 25
        grid_signal = (0.2 - bb_pos) * 18 if bb_pos < 0.2 else -(bb_pos - 0.8) * 18 if bb_pos > 0.8 else 0
        rsi_signal = (32 - rsi14) / 32 * 2 if rsi14 < 32 else -(rsi14 - 68) / 32 * 2 if rsi14 > 68 else 0
        short_rev = -momentum_short * 30 if abs(momentum_short) > 0.004 else 0
        final = (bb_mean_rev * 0.35 + grid_signal * 0.25 + rsi_signal * 0.25 + short_rev * 0.15)
    else:
        final = trend * 30 + momentum_short * 70
    return final

def main():
    global running, last_trade_time, position_entries, position_high
    import signal as sig_module
    def signal_handler(s, f): log('G46v4 停止...'); global running; running = False
    sig_module.signal(sig_module.SIGTERM, signal_handler)
    sig_module.signal(sig_module.SIGINT, signal_handler)
    cycle = 0; trades = 0; tp_count = 0; sl_count = 0; buy_count = 0; sell_count = 0; time_count = 0; partial_count = 0
    total_pnl = 0.0
    
    log('=' * 70)
    log('G46 v4 高收益版')
    log('TP: {}% | 分批TP: {}% | SL: {}% | 信号阈值: {}'.format(TP_RATE*100, TP_PARTIAL*100, SL_RATE*100, BUY_SIGNAL_T))
    log('最大持仓: {} | 超时: {}s | 冷却: {}s'.format(MAX_POSITIONS, MAX_HOLD_TIME, COOLDOWN))
    log('=' * 70)
    
    while running:
        try:
            cycle += 1
            spot_usdt, total_asset, all_holdings, cross_total = get_all_balances()
            log('')
            log('=== G46v4周期{} | 总资产:\${:.2f} | USDT:\${:.2f} ==='.format(cycle, total_asset, spot_usdt))
            
            for sym in list(position_entries.keys()):
                if sym not in all_holdings:
                    del position_entries[sym]
                    if sym in position_high: del position_high[sym]
            
            # 检查持仓退出 - 带追踪止损
            for sym, data in sorted(all_holdings.items(), key=lambda x: -x[1]['value']):
                current = data.get('price', 0)
                avg_cost = current
                free = data.get('amount', 0); value = data.get('value', 0)
                if value < MIN_VALUE: continue
                entry_time = position_entries.get(sym, time.time())
                hold_time = time.time() - entry_time
                pnl_pct = (current - avg_cost) / avg_cost if avg_cost > 0 else 0
                
                # 追踪最高价
                if sym not in position_high: position_high[sym] = current
                else: position_high[sym] = max(position_high[sym], current)
                
                # 追踪止损 (价格从最高点回撤0.4%则退出)
                trail_triggered = False
                if position_high[sym] > current:
                    drawdown = (position_high[sym] - current) / position_high[sym]
                    if drawdown > 0.004 and hold_time > 60:  # 回撤超过0.4%且持仓超过1分钟
                        log('  🛡️ {} 追踪止损! (回撤{:+.2f}%)'.format(sym, drawdown*100))
                        trail_triggered = True
                
                # 超时检查
                if hold_time > MAX_HOLD_TIME:
                    log('  ⏰ {} 超时退出 ({:.0f}s) ({:+.2f}%)'.format(sym, hold_time, pnl_pct*100))
                    if place_order(sym, 'SELL', free, current).get('success'):
                        time_count += 1; trades += 1; sell_count += 1
                        if sym in position_entries: del position_entries[sym]
                        if sym in position_high: del position_high[sym]
                
                # 止盈检查
                elif pnl_pct >= TP_RATE:
                    log('  🎯 {} 止盈! ({:+.2f}%)'.format(sym, pnl_pct*100))
                    if place_order(sym, 'SELL', free, current).get('success'):
                        tp_count += 1; trades += 1; sell_count += 1
                        if sym in position_entries: del position_entries[sym]
                        if sym in position_high: del position_high[sym]
                
                # 分批止盈 (0.3%)
                elif pnl_pct >= TP_PARTIAL and not hasattr(place_order, '_partial_done_'+sym):
                    log('  🎚️ {} 分批止盈30% ({:+.2f}%)'.format(sym, pnl_pct*100))
                    partial_qty = round_to_step(free * 0.3, 0.001)
                    if partial_qty > 0.001:
                        if place_order(sym, 'SELL', partial_qty, current).get('success'):
                            partial_count += 1
                            log('  🎚️ 分批卖出 {} 数量:{:.4f}'.format(sym, partial_qty))
                
                # 止损
                elif pnl_pct <= -SL_RATE:
                    log('  🛑 {} 止损! ({:+.2f}%)'.format(sym, pnl_pct*100))
                    if place_order(sym, 'SELL', free, current).get('success'):
                        sl_count += 1; trades += 1; sell_count += 1
                        if sym in position_entries: del position_entries[sym]
                        if sym in position_high: del position_high[sym]
                
                # 追踪止损触发
                elif trail_triggered:
                    if place_order(sym, 'SELL', free, current).get('success'):
                        trades += 1; sell_count += 1
                        if sym in position_entries: del position_entries[sym]
                        if sym in position_high: del position_high[sym]
            
            # 冷却期检查
            if time.time() - last_trade_time < COOLDOWN:
                log('  ⏳ 冷却中 ({:.0f}s)'.format(COOLDOWN - (time.time() - last_trade_time)))
                time.sleep(5); continue
            
            # 扫描信号
            scan_syms = list(all_holdings.keys()) + ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB','AVAX','ETC','NEAR','AI','ARB']
            prices = {s: get_price(s) for s in set(scan_syms)}
            strong_buys = []; strong_sells = []
            for sym in prices.keys():
                if sym == 'USDT': continue
                klines = get_klines(sym)
                if not klines or len(klines) < 50: continue
                try:
                    closes = [float(k[4]) for k in klines]; volumes = [float(k[5]) for k in klines]
                    highs = [float(k[2]) for k in klines]; lows = [float(k[3]) for k in klines]
                    market, range_conf = detect_market(closes, volumes)
                    pm = POLYMARKET.get(sym, 0)
                    combined = calc_signal_v4(closes, highs, lows, volumes, market, pm)
                    if combined > BUY_SIGNAL_T: strong_buys.append({'sym': sym, 'signal': combined, 'price': prices[sym], 'market': market})
                    elif combined < SELL_SIGNAL_T: strong_sells.append({'sym': sym, 'signal': combined, 'price': prices[sym], 'market': market})
                except: continue
            strong_buys.sort(key=lambda x: -x['signal']); strong_sells.sort(key=lambda x: x['signal'])
            
            # 买入
            open_positions = len([s for s in all_holdings.keys() if all_holdings[s].get('value', 0) >= MIN_VALUE])
            for d in strong_buys[:3]:
                sym = d['sym']; price = d['price']; sig = d['signal']
                if sym in BLACKLIST: log('  ⛔ {} 黑名单'.format(sym)); continue
                if open_positions >= MAX_POSITIONS: log('  ⚠️ 满仓'); break
                if spot_usdt < TRADE_BUDGET: log('  ⚠️ USDT不足'); break
                budget = min(TRADE_BUDGET, spot_usdt * 0.9)
                info = get_exchange_info(sym); min_notional = info.get('minNotional', 5); step_size = info.get('stepSize', 0.1)
                qty = max(budget / price, min_notional / price); qty = round_up_to_step(qty, step_size)
                order_value = qty * price
                if order_value < min_notional - 0.001: log('  ⚠️ {} 金额不足'.format(sym)); continue
                if qty <= 0: continue
                log('  📥 买入 {} 信号:{:.2f} 金额:\${:.2f}'.format(sym, sig, order_value))
                if place_order(sym, 'BUY', qty, price).get('success'):
                    buy_count += 1; trades += 1; spot_usdt -= budget; open_positions += 1
                    position_entries[sym] = time.time()
                    position_high[sym] = price
            
            # 卖出
            for d in strong_sells[:2]:
                sym = d['sym']; sig = d['signal']
                if sym in all_holdings:
                    info = get_exchange_info(sym); free = all_holdings[sym]['amount']
                    min_qty = info.get('minQty', 0.1); min_notional = info.get('minNotional', 5); step_size = info.get('stepSize', 0.1)
                    qty = round_to_step(free, step_size); value = qty * prices.get(sym, 0)
                    if qty >= min_qty and value >= min_notional:
                        log('  📤 卖出 {} 信号:{:.2f}'.format(sym, sig))
                        if place_order(sym, 'SELL', qty, prices.get(sym, 0)).get('success'):
                            sell_count += 1; trades += 1
                            if sym in position_entries: del position_entries[sym]
                            if sym in position_high: del position_high[sym]
            
            if strong_buys or strong_sells: log('【信号】买:{} 卖:{}'.format(len(strong_buys), len(strong_sells)))
            if cycle % 5 == 0:
                log('统计: 周期{} 交易{} 买{} 卖{} 止盈{} 止损{} 超时{} 分批{}'.format(cycle, trades, buy_count, sell_count, tp_count, sl_count, time_count, partial_count))
            for _ in range(30):
                if not running: break
                time.sleep(1)
        except Exception as e:
            log('异常: ' + str(e)[:80]); time.sleep(5)
    log('G46v4停止 - 周期{} 交易{} 买{} 卖{} 止盈{} 止损{} 超时{} 分批{}'.format(cycle, trades, buy_count, sell_count, tp_count, sl_count, time_count, partial_count))

if __name__ == '__main__':
    main()
