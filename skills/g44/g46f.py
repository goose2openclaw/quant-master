#!/usr/bin/env python3
"""
G46F - USDT合约交易版 v8
======================================
Hedge Mode + 止盈止损 + 最小订单$20
"""
import json, time, urllib.request, signal as sig_module, math
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g46f.log'

TP_RATE = 0.03
SL_RATE = 0.02
BUY_SIGNAL_T = 0.25
SELL_SIGNAL_T = -0.25
MIN_ORDER = 20
LEVERAGE = 3

running = True

def log(msg):
    ts = datetime.now().strftime('%m-%d %H:%M:%S')
    line = '[' + ts + '] ' + msg
    try:
        with open(LOG_FILE, 'a') as f: f.write(line + chr(10))
    except: pass
    print(line, flush=True)

def fut_signed(endpoint, params=None):
    import hmac, hashlib
    ts = int(time.time() * 1000)
    base = {'timestamp': ts, 'recvWindow': 5000}
    if params: base.update(params)
    q = '&'.join('{}={}'.format(k, v) for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://fapi.binance.com{}?{}&signature={}'.format(endpoint, q, sig)
    req = urllib.request.Request(url)
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

def get_futures_balance():
    try:
        bal = fut_signed('/fapi/v2/balance')
        for b in bal:
            if b.get('asset') == 'USDT':
                return float(b.get('availableBalance', 0))
    except: pass
    return 0

def get_positions():
    try:
        pos = fut_signed('/fapi/v2/positionRisk')
        result = []
        for p in pos:
            amt = float(p.get('positionAmt', 0))
            if amt != 0:
                sym = p.get('symbol').replace('USDT', '')
                entry = float(p.get('entryPrice', 0))
                pnl = float(p.get('unrealizedProfit', 0))
                mark = float(p.get('markPrice', 0))
                result.append({'symbol': sym, 'amount': abs(amt), 'entry': entry, 'pnl': pnl, 'mark': mark, 'side': 'LONG' if amt > 0 else 'SHORT'})
        return result
    except: return []

def set_leverage(sym):
    try:
        fut_signed('/fapi/v1/leverage', {'symbol': sym + 'USDT', 'leverage': LEVERAGE})
    except: pass

def place_order(sym, side, qty, pos_side='BOTH'):
    # 四舍五入后再检查
    qty = round(qty, 3)
    if qty <= 0: return {'success': False, 'error': 'qty<=0 after round'}
    for attempt in range(3):
        try:
            ts = int(time.time() * 1000)
            params = {
                'symbol': sym + 'USDT', 
                'side': side.upper(),
                'positionSide': pos_side,
                'type': 'MARKET', 
                'quantity': str(round(qty, 3)),  # 使用round保留小数
                'timestamp': ts, 
                'recvWindow': 5000
            }
            q_str = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
            import hmac, hashlib
            sig = hmac.new(API_SECRET.encode(), q_str.encode(), hashlib.sha256).hexdigest()
            url = 'https://fapi.binance.com/fapi/v1/order?' + q_str + '&signature=' + sig
            req = urllib.request.Request(url, method='POST')
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            try:
                resp = opener.open(req, timeout=10).read().decode()
                log('  ✅ {} {} {} [{}] 成功 | 订单号:{}'.format(sym, side.upper(), qty, pos_side, resp.get('orderId', 'N/A')))
                return {'success': True}
            except urllib.error.HTTPError as e:
                err_body = e.read().decode()
                try: err_json = json.loads(err_body); err_msg = err_json.get('msg', err_body)
                except: err_msg = err_body
                log('  ❌ 合约错误[{}]: {} | qty={}'.format(attempt+1, err_msg[:80], qty))
                time.sleep(0.5); continue
        except Exception as e: log('  异常: {}'.format(str(e)[:30])); time.sleep(0.5)
    return {'success': False}

def get_avg_price(sym):
    klines = get_klines(sym, '1h', 48)
    if not klines: return get_price(sym)
    closes = [float(k[4]) for k in klines]
    return sum(closes) / len(closes)

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

def calc_rsi(closes, period=14):
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains[-period:])/period if gains else 0.001
    avg_loss = sum(losses[-period:])/period if losses else 0.001
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    return 100 - (100/(1+rs))

def calc_bollinger_bands(closes, period=20, std_dev=2):
    if len(closes) < period: return 0, 0, 0, 0.5
    ma = sum(closes[-period:])/period
    variance = sum((c - ma)**2 for c in closes[-period:])/period
    std = math.sqrt(variance)
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    position = (closes[-1] - lower)/(upper - lower) if upper != lower else 0.5
    return upper, ma, lower, position

POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08,'BNB':0.06,'AVAX':0.05,'ETC':0.04,'NEAR':0.03,'AI':0.03,'FLOKI':0.02,'ARB':0.03}

def calc_signal(closes, highs, lows, volumes, polymarket=0):
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    rsi = calc_rsi(closes)
    bb_upper, bb_ma, bb_lower, bb_pos = calc_bollinger_bands(closes)
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-3:])/3 if len(returns) >= 3 else 0
    
    bb_deviation = (closes[-1] - bb_ma) / bb_ma if bb_ma > 0 else 0
    bb_signal = -bb_deviation * 20
    rsi_signal = (30 - rsi) / 30 if rsi < 30 else -(rsi - 70) / 30 if rsi > 70 else 0
    trend_signal = trend * 15
    momentum_signal = momentum * 50
    
    final = bb_signal * 0.25 + rsi_signal * 0.20 + trend_signal * 0.25 + momentum_signal * 0.15 + polymarket * 0.15
    return final

def main():
    global running
    def signal_handler(s, f): log('G46F 停止...'); global running; running = False
    sig_module.signal(sig_module.SIGTERM, signal_handler)
    sig_module.signal(sig_module.SIGINT, signal_handler)
    
    cycle = 0; trades = 0; tp_count = 0; sl_count = 0
    
    log('=' * 70)
    log('G46F v8 - USDT合约 (最小订单$20)')
    log('止盈: {}% | 止损: {}% | 杠杆: {}x | 最小订单: ${}'.format(TP_RATE*100, SL_RATE*100, LEVERAGE, MIN_ORDER))
    log('=' * 70)
    
    while running:
        try:
            cycle += 1
            bal = get_futures_balance()
            positions = get_positions()
            
            log('')
            log('=== G46F周期{} | USDT:\${:.2f} ==='.format(cycle, bal))
            
            # 监控持仓
            for p in positions:
                price = get_price(p['symbol'])
                cost = abs(p['amount']) * p['entry']
                pnl_pct = (float(p.get('markPrice', price)) - p['entry']) / p['entry'] if p['entry'] > 0 else 0
                if p['side'] == 'SHORT': pnl_pct = -pnl_pct
                
                log('  {} {} | 成本:{:+.2f}% | 当前\${} | 预估\${:.2f}'.format(
                    p['symbol'], p['side'], pnl_pct*100, price, ((float(p.get('markPrice', price)) - p['entry']) * abs(p['amount']))))
                
                # 检查止盈止损 - 每次检查前重新获取最新持仓
                if pnl_pct >= TP_RATE and p["amount"] > 0:
                    log('  🎯 {} 止盈! ({:+.2f}%)'.format(p['symbol'], pnl_pct*100))
                    # 平仓前重新获取持仓确认数量
                    fresh_positions = get_positions()
                    fresh_pos = next((x for x in fresh_positions if x['symbol'] == p['symbol']), None)
                    if fresh_pos and fresh_pos['amount'] > 0:
                        result = place_order(p['symbol'], 'SELL' if p['side'] == 'LONG' else 'BUY', fresh_pos['amount'], 'LONG' if p['side'] == 'LONG' else 'SHORT')
                        tp_count += 1; trades += 1
                        if result.get('success'):
                            log('  📋 平仓完成，刷新持仓...')
                            positions = get_positions()  # 立即刷新
                    else:
                        log('  {} 已无持仓，跳过平仓'.format(p['symbol']))
                elif pnl_pct <= -SL_RATE and p["amount"] > 0:
                    log('  🛑 {} 止损! ({:+.2f}%)'.format(p['symbol'], pnl_pct*100))
                    # 平仓前重新获取持仓确认数量
                    fresh_positions = get_positions()
                    fresh_pos = next((x for x in fresh_positions if x['symbol'] == p['symbol']), None)
                    if fresh_pos and fresh_pos['amount'] > 0:
                        result = place_order(p['symbol'], 'SELL' if p['side'] == 'LONG' else 'BUY', fresh_pos['amount'], 'LONG' if p['side'] == 'LONG' else 'SHORT')
                        sl_count += 1; trades += 1
                        if result.get('success'):
                            log('  📋 平仓完成，刷新持仓...')
                            positions = get_positions()  # 立即刷新
                    else:
                        log('  {} 已无持仓，跳过平仓'.format(p['symbol']))
            
            # 信号扫描
            prices = {s: get_price(s) for s in ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB','DOGE','AVAX','ETC','NEAR','AI','ARB']}
            strong_buys = []
            strong_sells = []
            
            for sym, price in prices.items():
                klines = get_klines(sym)
                if not klines or len(klines) < 50: continue
                closes = [float(k[4]) for k in klines]
                pm = POLYMARKET.get(sym, 0)
                sig = calc_signal(closes, None, None, None, pm)
                
                if sig > BUY_SIGNAL_T: strong_buys.append({'sym': sym, 'signal': sig, 'price': price})
                elif sig < SELL_SIGNAL_T: strong_sells.append({'sym': sym, 'signal': sig, 'price': price})
            
            strong_buys.sort(key=lambda x: -x['signal'])
            strong_sells.sort(key=lambda x: x['signal'])
            
            buy_signals = len(strong_buys)
            sell_signals = len(strong_sells)
            
            # 执行交易 - 确保最小订单$20
            for d in strong_buys[:2]:
                sym = d['sym']
                price = d['price']
                sig = d['signal']
                
                # 计算合约数量 (保证金约$10, 2倍杠杆, 合约价值=$20)
                contract_qty = int(MIN_ORDER / price)
                if contract_qty < 1: contract_qty = 1
                
                log('  📥 开多: {} 信号:{:.2f}'.format(sym, sig))
                set_leverage(sym)
                place_order(sym, 'BUY', contract_qty, 'LONG')
                trades += 1
            
            for d in strong_sells[:2]:
                sym = d['sym']
                sig = d['signal']
                
                contract_qty = int(MIN_ORDER / d['price'])
                if contract_qty < 1: contract_qty = 1
                
                log('  📤 开空: {} 信号:{:.2f}'.format(sym, sig))
                set_leverage(sym)
                place_order(sym, 'SELL', contract_qty, 'SHORT')
                trades += 1
            
            log('买:{} | 卖:{} | 止盈:{} | 止损:{}'.format(buy_signals, sell_signals, tp_count, sl_count))
            
            if cycle % 10 == 0:
                log('统计: 周期{} 交易{} 止盈{} 止损{}'.format(cycle, trades, tp_count, sl_count))
            
            for _ in range(60):
                if not running: break
                time.sleep(1)
        except Exception as e:
            log('异常: ' + str(e)[:80]); time.sleep(5)
    log('G46F停止 - 周期{} 交易{} 止盈{} 止损{}'.format(cycle, trades, tp_count, sl_count))

if __name__ == '__main__': main()
