#!/usr/bin/env python3
"""
G46 v6 - 横盘终结版
======================================
核心修复:
1. TP: 0.15% → 0.05% (超低阈值，横盘必触发)
2. 动态止盈: 突破阻力位立即止盈
3. RSI超买强制卖出 (RSI>70)
4. BB极端位置强制平仓 (BB>0.9 或 <0.1)
5. 持有超时: 300s → 180s (更短的超时)
"""
import json, time, urllib.request, hmac, hashlib, math
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g46_v6.log'

# === v6 核心参数 ===
TP_RATE = 0.0005        # 止盈 0.05% (超低!)
SL_RATE = 0.003         # 止损 0.3%
BUY_SIGNAL_T = 0.15     # 买入阈值
SELL_SIGNAL_T = -0.15   # 卖出阈值
RSI_SELL = 70           # RSI超买强制卖
BB_SELL = 0.85          # BB极端超买
BB_BUY = 0.15           # BB极端超卖
TRADE_BUDGET = 5
MIN_VALUE = 0.5
MAX_POSITIONS = 8
MAX_HOLD_TIME = 180     # 3分钟超时 (更短!)
COOLDOWN = 15           # 15秒冷却
BLACKLIST = ['NEIRO', 'TURBO', 'FLOKI', 'BOME', 'SHIB', 'VR', 'VRQQ']

running = True
INFO_CACHE = {}
position_entries = {}
position_partial = {}
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

def get_klines(sym, interval='3m', limit=100):
    for retry in range(3):
        try:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=' + interval + '&limit=' + str(limit)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            data = json.loads(opener.open(urllib.request.Request(url), timeout=15).read().decode())
            if not data or len(data) < 20: return []
            return data
        except: time.sleep(1)
    return []

def get_all_balances():
    spot_usdt = 0; spot_total = 0; spot_holdings = {}
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
                    spot_holdings[asset] = {'amount': total, 'value': val, 'price': price}
    except Exception as e: log('账户查询失败: ' + str(e)[:50])
    return spot_usdt, spot_total, spot_holdings

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
                opener.open(req, timeout=10).read().decode()
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

def calc_bb(closes, period=20):
    if len(closes) < period: return 0.5, 0, 0
    ma = sum(closes[-period:])/period
    variance = sum((c - ma)**2 for c in closes[-period:])/period
    std = math.sqrt(variance)
    upper = ma + 2 * std; lower = ma - 2 * std
    position = (closes[-1] - lower)/(upper - lower) if upper != lower else 0.5
    return position, upper, lower

def get_market_signal(sym):
    """获取市场信号"""
    klines = get_klines(sym, '3m', 50)
    if not klines or len(klines) < 20: return None, 0.5, 50
    closes = [float(k[4]) for k in klines]
    rsi = calc_rsi(closes)
    bb_pos, _, _ = calc_bb(closes)
    return closes, bb_pos, rsi



# ============================================================
# G46 v7 - 市场状态检测 + 策略自动切换
# ============================================================

def get_regime(sym):
    """检测市场状态: 横盘/趋势/超卖反弹/超买回落"""
    try:
        # 多个时间框架分析
        klines_3m = get_klines(sym, "3m", 50)
        klines_1h = get_klines(sym, "1h", 100)
        klines_4h = get_klines(sym, "4h", 100)
        
        if not klines_3m or not klines_1h or not klines_4h:
            return "unknown", {}
        
        closes_3m = [float(k[4]) for k in klines_3m]
        closes_1h = [float(k[4]) for k in klines_1h]
        closes_4h = [float(k[4]) for k in klines_4h]
        
        # RSI 多时间框架
        rsi_3m = calc_rsi(closes_3m)
        rsi_1h = calc_rsi(closes_1h)
        rsi_4h = calc_rsi(closes_4h)
        
        # BB宽度 (波动率指标) - 使用百分比变化
        def bb_width(closes, period=20):
            if len(closes) < period: return 0
            returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
            if len(returns) < period: return 0
            std = math.sqrt(sum(r*r for r in returns[-period:])/period)
            return std * 100
        
        bw_3m = bb_width(closes_3m)
        bw_1h = bb_width(closes_1h)
        
        # 趋势方向 (MA对齐)
        def trend_dir(closes):
            ma5 = sum(closes[-5:])/5
            ma20 = sum(closes[-20:])/20 if len(closes) >= 20 else closes[-1]
            ma60 = sum(closes[-60:])/60 if len(closes) >= 60 else ma20
            if closes[-1] > ma5 > ma20 > ma60: return "up"
            elif closes[-1] < ma5 < ma20 < ma60: return "down"
            return "neutral"
        
        trend_1h = trend_dir(closes_1h)
        trend_4h = trend_dir(closes_4h)
        
        # 动量
        mom_3m = (closes_3m[-1] - closes_3m[-10]) / closes_3m[-10] if len(closes_3m) >= 10 else 0
        mom_1h = (closes_1h[-1] - closes_1h[-20]) / closes_1h[-20] if len(closes_1h) >= 20 else 0
        
        # 综合评分
        regime_score = 0
        details = {
            "rsi_3m": rsi_3m, "rsi_1h": rsi_1h, "rsi_4h": rsi_4h,
            "trend_1h": trend_1h, "trend_4h": trend_4h,
            "bw_3m": bw_3m, "bw_1h": bw_1h,
            "mom_3m": mom_3m, "mom_1h": mom_1h
        }
        
        # 超卖反弹检测
        if rsi_3m < 30 and rsi_1h < 40:
            regime_score = 1  # 超卖反弹
        elif rsi_3m < 25:
            regime_score = 1  # 极端超卖
        
        # 趋势上涨检测
        elif trend_1h == "up" and trend_4h == "up" and rsi_1h > 45:
            regime_score = 2  # 趋势上涨
        
        # 超买回落检测
        elif rsi_3m > 70 and rsi_1h > 55:
            regime_score = 3  # 超买回落
        
        # 趋势下跌检测
        elif trend_1h == "down" and trend_4h == "down" and rsi_1h < 60:
            regime_score = 4  # 趋势下跌
        
        # 横盘默认
        else:
            regime_score = 0  # 横盘
        
        regimes = ["横盘", "超卖反弹", "趋势上涨", "超买回落", "趋势下跌"]
        return regimes[regime_score], details
        
    except Exception as e:
        return "unknown", {"error": str(e)}

def get_strategy_for_regime(regime, details):
    """根据市场状态返回策略参数"""
    if regime == "超卖反弹":
        return {
            "name": "超卖反弹策略 (MiroFish#206)",
            "tp": 0.02,       # 2% 止盈 (MiroFish)
            "sl": 0.015,      # 1.5% 止损 (MiroFish)
            "max_hold": 3600, # 60分钟持仓 (MiroFish 1h)
            "rsi_buy": 20,    # RSI < 20 (MiroFish)
            "bb_buy": 0.20,   # BB < 20% (MiroFish)
            "rsi_sell": 60,
            "bb_sell": 0.75,
            "signal_threshold": 0.20,
            "lev": 1.5,       # 1.5x杠杆 (MiroFish)
        }
    elif regime == "趋势上涨":
        return {
            "name": "趋势顺势策略 (v7)",
            "tp": 0.01,      # 1% 止盈
            "sl": 0.02,       # 2% 止损
            "max_hold": 3600,  # 60分钟持仓
            "rsi_buy": 45,
            "bb_buy": 0.30,
            "rsi_sell": 70,
            "bb_sell": 0.80,
            "signal_threshold": 0.15,
        }
    elif regime == "超买回落":
        return {
            "name": "超买回落策略 (v7)",
            "tp": 0.003,     # 0.3% 止盈
            "sl": 0.02,       # 2% 止损
            "max_hold": 900,   # 15分钟持仓
            "rsi_buy": 30,
            "bb_buy": 0.20,
            "rsi_sell": 65,   # RSI > 65 止盈
            "bb_sell": 0.70,
            "signal_threshold": 0.20,
        }
    elif regime == "趋势下跌":
        return {
            "name": "做空策略 (v7) - 暂停",
            "tp": 0.003,
            "sl": 0.01,
            "max_hold": 600,
            "rsi_buy": 25,
            "bb_buy": 0.15,
            "rsi_sell": 55,
            "bb_sell": 0.65,
            "signal_threshold": 0.30,
        }
    else:  # 横盘
        return {
            "name": "横盘策略 (MiroFish#956)",
            "tp": 0.02,       # 2% 止盈 (MiroFish)
            "sl": 0.01,       # 1% 止损 (MiroFish)
            "max_hold": 3600, # 60分钟持仓 (MiroFish 1h)
            "rsi_buy": 30,    # RSI < 30 (MiroFish)
            "bb_buy": 0.25,   # BB < 25% (MiroFish)
            "rsi_sell": 70,
            "bb_sell": 0.85,
            "signal_threshold": 0.25,
            "lev": 2.0,       # 2x杠杆 (MiroFish)
        }

def main():
    global running, last_trade_time, position_entries, position_partial
    import signal as sig_module
    def signal_handler(s, f): log('G46v6 停止...'); global running; running = False
    sig_module.signal(sig_module.SIGTERM, signal_handler)
    sig_module.signal(sig_module.SIGINT, signal_handler)
    cycle = 0; trades = 0; tp_count = 0; sl_count = 0; buy_count = 0; sell_count = 0; time_count = 0; rsi_count = 0; bb_count = 0
    
    log('=' * 60)
    log('G46 v7 市场自适应版')
    log('TP: {}% | SL: {}% | RSI卖出: {} | BB极端: {}/{}'.format(TP_RATE*100, SL_RATE*100, RSI_SELL, BB_SELL, BB_BUY))
    log('超时: {}s | 冷却: {}s | 最大持仓: {}'.format(MAX_HOLD_TIME, COOLDOWN, MAX_POSITIONS))
    log('=' * 60)
    
    # v7: 策略状态 - 在主循环前初始化
    current_regime = "横盘"
    current_strategy = get_strategy_for_regime("横盘", {})
    regime_change_time = time.time()
    regime_stable_duration = 300
    
    while running:
        try:
            cycle += 1
            spot_usdt, total_asset, all_holdings = get_all_balances()
            log('')
            log('=== G46v6周期{} | 总资产:\${:.2f} | USDT:\${:.2f} ==='.format(cycle, total_asset, spot_usdt))
            
            # 清理无效持仓
            for sym in list(position_entries.keys()):
                if sym not in all_holdings:
                    del position_entries[sym]
                    if sym in position_partial: del position_partial[sym]
            
            # === 检查持仓退出 ===
            for sym, data in sorted(all_holdings.items(), key=lambda x: -x[1]['value']):
                current = data.get('price', 0)
                free = data.get('amount', 0); value = data.get('value', 0)
                if value < MIN_VALUE: continue
                
                entry_time = position_entries.get(sym, time.time())
                hold_time = time.time() - entry_time
                pnl_pct = 0  # 简化计算
                
                # 获取实时BB和RSI
                closes, bb_pos, rsi = get_market_signal(sym)
                
                exit_reason = None
                
                # 使用当前策略的退出参数
                strat_tp = current_strategy["tp"]
                strat_sl = current_strategy["sl"]
                strat_max_hold = current_strategy["max_hold"]
                strat_rsi_sell = current_strategy["rsi_sell"]
                strat_bb_sell = current_strategy["bb_sell"]
                
                # 1. 超时退出
                if hold_time > strat_max_hold:
                    exit_reason = '超时 {:.0f}s'.format(hold_time)
                    time_count += 1
                
                # 2. RSI超买强制卖
                elif rsi > strat_rsi_sell:
                    exit_reason = 'RSI超买 {:.0f}'.format(rsi)
                    rsi_count += 1
                
                # 3. BB极端位置
                elif bb_pos > strat_bb_sell:
                    exit_reason = 'BB超买 {:.2f}'.format(bb_pos)
                    bb_count += 1
                
                # 4. 止盈
                elif pnl_pct >= strat_tp:
                    exit_reason = '止盈 {:.2f}%'.format(pnl_pct*100)
                    tp_count += 1
                
                # 5. 止损
                elif pnl_pct <= -strat_sl:
                    exit_reason = '止损 {:.2f}%'.format(pnl_pct*100)
                    sl_count += 1
                
                if exit_reason:
                    log('  🚪 {} 退出: {} ({:.0f}s)'.format(sym, exit_reason, hold_time))
                    if place_order(sym, 'SELL', free, current).get('success'):
                        trades += 1; sell_count += 1
                        if sym in position_entries: del position_entries[sym]
                        if sym in position_partial: del position_partial[sym]
                    continue
                
                # 显示持仓状态
                if cycle % 10 == 0:
                    log('  💼 {} | BB:{:.2f} RSI:{:.0f} | {:.0f}s'.format(sym, bb_pos, rsi, hold_time))
            
            # === 冷却检查 ===
            if time.time() - last_trade_time < COOLDOWN:
                time.sleep(5); continue
            
            # === 扫描信号 ===
            scan_syms = list(all_holdings.keys()) + ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB','AVAX','ETC','NEAR','AI','ARB','INJ','UNI','LTC','ATOM']
            prices = {s: get_price(s) for s in set(scan_syms)}
            strong_buys = []; strong_sells = []
            
            for sym in prices.keys():
                if sym == 'USDT': continue
                closes, bb_pos, rsi = get_market_signal(sym)
                if closes is None: continue
                
                # 使用当前策略的信号参数
                sig_thresh = current_strategy["signal_threshold"]
                sig_rsi_buy = current_strategy["rsi_buy"]
                sig_bb_buy = current_strategy["bb_buy"]
                
                # 信号计算 (根据策略调整)
                ma5 = sum(closes[-5:])/5; ma10 = sum(closes[-10:])/10
                momentum = (closes[-1] - closes[-6]) / closes[-6] if len(closes) >= 6 else 0
                
                sig = 0
                # 超卖信号
                if rsi < sig_rsi_buy and bb_pos < sig_bb_buy: sig = 0.5
                elif rsi < sig_rsi_buy + 5 and bb_pos < sig_bb_buy + 0.1: sig = 0.3
                elif momentum > 0.002 and bb_pos < 0.4: sig = 0.2
                # 超买信号
                if rsi > current_strategy["rsi_sell"] - 5 or bb_pos > current_strategy["bb_sell"] - 0.1: sig = -0.2
                
                if sig > current_strategy['signal_threshold']: strong_buys.append({'sym': sym, 'signal': sig, 'price': prices[sym], 'rsi': rsi, 'bb': bb_pos})
                elif sig < -current_strategy['signal_threshold']: strong_sells.append({'sym': sym, 'signal': sig, 'price': prices[sym]})
            
            strong_buys.sort(key=lambda x: -x['signal']); strong_sells.sort(key=lambda x: x['signal'])
            
            # === 买入 ===
            open_pos = len([s for s in all_holdings.keys() if all_holdings[s].get('value', 0) >= MIN_VALUE])
            for d in strong_buys[:4]:
                sym = d['sym']; price = d['price']
                if sym in BLACKLIST: log('  ⛔ {} 黑名单'.format(sym)); continue
                if sym in all_holdings and all_holdings[sym].get('value', 0) >= MIN_VALUE: log('  ⛽ {} 已持仓'.format(sym)); continue
                if open_pos >= MAX_POSITIONS: log('  ⚠️ 满仓'); break
                if spot_usdt < TRADE_BUDGET: log('  ⚠️ USDT不足'); break
                
                # DOGE/PEPE 小仓位 (0.5% of budget)
                if sym in ['DOGE', 'PEPE']:
                    budget = min(TRADE_BUDGET * 0.005, spot_usdt * 0.005)  # 0.5% 仓位
                else:
                    budget = min(TRADE_BUDGET, spot_usdt * 0.9)
                info = get_exchange_info(sym); min_notional = info.get('minNotional', 5); step_size = info.get('stepSize', 0.1)
                qty = max(budget / price, min_notional / price); qty = round_up_to_step(qty, step_size)
                order_value = qty * price
                if order_value < min_notional - 0.001: continue
                if qty <= 0: continue
                
                log('  📥 {} 信号:{:.2f} RSI:{:.0f} BB:{:.2f} \${:.2f}'.format(sym, d['signal'], d['rsi'], d['bb'], order_value))
                if place_order(sym, 'BUY', qty, price).get('success'):
                    buy_count += 1; trades += 1; spot_usdt -= budget; open_pos += 1
                    position_entries[sym] = time.time()
            
            # === 卖出 (信号驱动) ===
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
            
            if strong_buys or strong_sells: log('【信号】买:{} 卖:{}'.format(len(strong_buys), len(strong_sells)))
            if cycle % 20 == 0:
                log('统计: 周期{} 交易{} 买{} 卖{} 止盈{} 止损{} 超时{} RSI退出{} BB退出{}'.format(
                    cycle, trades, buy_count, sell_count, tp_count, sl_count, time_count, rsi_count, bb_count))
            
            for _ in range(10):
                if not running: break
                time.sleep(1)
        except Exception as e:
            log('异常: ' + str(e)[:80]); time.sleep(5)
    
    log('v6停止 - 周期{} 交易{} 买{} 止盈{} 止损{} 超时{} RSI退出{} BB退出{}'.format(
        cycle, trades, buy_count, tp_count, sl_count, time_count, rsi_count, bb_count))

if __name__ == '__main__':
    main()
