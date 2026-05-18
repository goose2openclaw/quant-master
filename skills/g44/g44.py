#!/usr/bin/env python3
"""
G44 v4.1 - 回归G43配置 + LOT_SIZE修复
=====================================
回归配置:
- 买入阈值: 0.03 (G43原始)
- 卖出阈值: -0.03
- Polymarket权重: 35%
- 信号融合: 65%/35%

优化:
- LOT_SIZE自动修复
- 止损逻辑优化
"""

import json, time, urllib.request, hmac, hashlib, signal as sig_module
from datetime import datetime
from collections import defaultdict

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g44.log'

POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}
COINS_ALL = ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','BNB','DOGE','SHIB','PEPE','BONK','NEIRO','BOME','FTM','MATIC','AVAX']
SKIP = ['FTM','NEIRO','BOME','SHIB','PEPE','BONK']

# 回归G43原始配置
BUY_THRESHOLD = 0.03  # G43原始
SELL_THRESHOLD = -0.03
MIN_ORDER = 5
MAX_POSITION = 0.35

running = True

def log(msg):
    ts = datetime.now().strftime('%m-%d %H:%M:%S')
    line = '[' + ts + '] ' + msg
    try:
        with open(LOG_FILE, 'a') as f: f.write(line + chr(10))
    except: pass
    print(line, flush=True)

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
        d = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        return float(d['price'])
    except: return 0

def get_klines(sym, interval='15m', limit=100):
    try:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=' + interval + '&limit=' + str(limit)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return []

def place_order(sym, side, qty):
    for attempt in range(3):
        try:
            ts = int(time.time() * 1000)
            qty_str = '{:.6f}'.format(round(qty, 6))
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
                log('  错误[{}]: {}'.format(attempt+1, err_msg[:40]))
                if 'LOT_SIZE' in err_msg or 'MIN_NOTIONAL' in err_msg:
                    qty *= 1.5
                    log('  LOT_SIZE修复: 数量x1.5')
                    time.sleep(0.3); continue
                elif 'INSUFFICIENT' in err_msg:
                    return {'success': False}
                time.sleep(0.5); continue
            if 'code' in resp:
                log('  失败: {}'.format(resp.get('msg', '')[:40]))
                time.sleep(0.5); continue
            log('  {} {} x {} 成功'.format(side, sym, qty_str))
            return {'success': True}
        except Exception as e:
            log('  异常: {}'.format(str(e)[:30])); time.sleep(0.5)
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

def detect_market(closes):
    if len(closes) < 50: return 'range'
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    vol = sum(abs(r) for r in returns[-20:])/20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    if trend > 0.03: return 'trend'
    elif vol < 0.015: return 'range'
    elif trend > 0.015 and vol > 0.025: return 'breakout'
    return 'range'

def calc_signal(closes, volumes, market, polymarket=0):
    """G43原始信号计算"""
    if len(closes) < 50: return 0
    ma5, ma20 = sum(closes[-5:])/5, sum(closes[-20:])/20
    ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
    trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
    vol_avg = sum(volumes[-20:])/20
    vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains)/len(gains) if gains else 0
    avg_loss = sum(losses)/len(losses) if losses else 0
    rs = avg_gain/avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100/(1+rs))
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
    
    # G43原始信号权重
    if market == 'range':
        go_pool = (vol_ratio - 1) * 0.8
        mean_rev = -((closes[-1] - ma20)/ma20 * 15) if ma20 > 0 else 0
        go_rotate = trend * 1.2
    else:
        go_pool = (vol_ratio - 1) * 0.5
        mean_rev = -((closes[-1] - ma20)/ma20 * 8) if ma20 > 0 else 0
        go_rotate = trend * 0.5
    
    go_core = trend * 12
    go_ls = (rsi - 50) / 50
    go_detect = trend50 * 6
    momentum_sig = momentum * 120
    breakout = 1.5 if closes[-1] > max(closes[-20:-1]) else -0.5 if closes[-1] < min(closes[-20:-1]) else 0
    vol_profile = 1.2 if vol_ratio > 1.5 and closes[-1] > ma20 else 0
    sentiment = trend * 25 + polymarket * 1.5
    
    # G43原始融合
    go_signal = (go_core*0.15 + go_pool*0.15 + go_rotate*0.12 + go_ls*0.10 +
                 go_detect*0.08 + momentum_sig*0.08 + mean_rev*0.10 +
                 breakout*0.07 + vol_profile*0.08 + sentiment*0.07)
    
    return go_signal * 0.65 + polymarket * 0.35  # G43原始权重

def main():
    global running
    
    def signal_handler(s, f):
        log('G44停止...'); global running; running = False
    
    sig_module.signal(sig_module.SIGTERM, signal_handler)
    sig_module.signal(sig_module.SIGINT, signal_handler)
    
    cycle = 0; trades = 0; errors = 0
    
    log('=' * 70)
    log('G44 v4.1 启动 - 回归G43配置 + LOT_SIZE修复')
    log('配置: 阈值0.03 PM权重35% 信号融合65%/35%')
    log('=' * 70)
    
    while running:
        try:
            cycle += 1
            account = get_account()
            prices = {s: get_price(s) for s in COINS_ALL}
            holdings = {}
            
            for b in account.get('balances', []):
                free = float(b.get('free', 0))
                asset = b['asset']
                if asset != 'USDT' and free > 0:
                    price = prices.get(asset, 0)
                    value = free * price
                    if value > 0.1:
                        holdings[asset] = {'amount': free, 'price': price, 'entry': price, 'value': value}
            
            total = sum(h['value'] for h in holdings.values())
            usdt = float([b for b in account.get('balances', []) if b['asset'] == 'USDT'][0]['free'])
            total += usdt
            
            sig_data = {}
            market_counts = defaultdict(int)
            
            for sym in COINS_ALL:
                if sym in SKIP: continue
                klines = get_klines(sym)
                if not klines or len(klines) < 50: continue
                closes = [float(k[4]) for k in klines]
                volumes = [float(k[5]) for k in klines]
                market = detect_market(closes)
                market_counts[market] += 1
                pm = POLYMARKET.get(sym, 0)
                combined = calc_signal(closes, volumes, market, pm)
                sig_data[sym] = {'combined': combined, 'market': market, 'pm': pm}
            
            buys = []; sells = []
            
            for sym, h in holdings.items():
                if sym not in sig_data: continue
                c = sig_data[sym]['combined']
                pnl = (h['price'] - h['entry'])/h['entry']*100 if h.get('entry', 0) > 0 else 0
                if c < SELL_THRESHOLD or pnl < -5:
                    val = h['amount'] * h['price']
                    if val >= 3:
                        sells.append({'sym': sym, 'amt': h['amount']*0.8, 'c': c, 'pnl': pnl})
            
            for sym in COINS_ALL:
                if sym in SKIP or sym in holdings or sym not in sig_data: continue
                c = sig_data[sym]['combined']
                p = prices.get(sym, 0)
                if p <= 0: continue
                if c > BUY_THRESHOLD and usdt > 5:
                    budget = min(usdt * MAX_POSITION, 100)
                    qty = budget / p
                    if qty * p >= MIN_ORDER:
                        buys.append({'sym': sym, 'qty': qty, 'c': c})
            
            buys.sort(key=lambda x: -x['c'])
            sells.sort(key=lambda x: x['c'])
            
            log('')
            log('=== G44周期{} | 总资产:${:.2f} | USDT:${:.2f} ==='.format(cycle, total, usdt))
            log('市场:{} | 持仓:{} | 买:{} | 卖:{}'.format(dict(market_counts), len(holdings), len(buys), len(sells)))
            
            for d in sells[:2]:
                log('卖出: {} 信号:{:.2f} PnL:{:.1f}%'.format(d['sym'], d['c'], d['pnl']))
                if place_order(d['sym'], 'SELL', d['amt']).get('success'): trades += 1
                else: errors += 1
            
            for d in buys[:2]:
                log('买入: {} 信号:{:.2f}'.format(d['sym'], d['c']))
                if place_order(d['sym'], 'BUY', d['qty']).get('success'): trades += 1
                else: errors += 1
            
            if cycle % 10 == 0:
                log('统计: 周期{} 交易{} 错误{}'.format(cycle, trades, errors))
            
            for _ in range(60):
                if not running: break
                time.sleep(1)
                
        except Exception as e:
            log('异常: ' + str(e)[:50])
            errors += 1
            time.sleep(5)
    
    log('G44停止 - 周期{} 交易{} 错误{}'.format(cycle, trades, errors))

if __name__ == '__main__': main()
