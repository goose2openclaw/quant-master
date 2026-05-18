#!/usr/bin/env python3
"""
G41 Enhanced - go技能调度 + Polymarket
======================================
集成所有go系列技能 + Polymarket预测市场

版本: 1.1 Enhanced
日期: 2026-05-18
"""

import json, time, urllib.request, hmac, hashlib
from datetime import datetime
from collections import defaultdict

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g41.log'

# Polymarket信号
POLYMARKET_SIGNALS = {
    'BTC': 0.42, 'ETH': 0.35, 'SOL': 0.28, 'DOGE': 0.22,
    'XRP': 0.15, 'ADA': 0.12, 'DOT': 0.10, 'LINK': 0.08
}

# ============ go技能调度器 ============

class GoSkillDispatcher:
    """go技能统一调度器"""
    
    def __init__(self):
        # go技能权重配置
        self.skills = {
            'go-core': {'weight': 0.20, 'desc': '趋势核心'},
            'go-pool': {'weight': 0.15, 'desc': '流动性分析'},
            'go-rotate': {'weight': 0.12, 'desc': '轮转策略'},
            'go-long-short': {'weight': 0.12, 'desc': '多空策略'},
            'go-detect': {'weight': 0.10, 'desc': '机构检测'},
            'go-etf': {'weight': 0.08, 'desc': 'ETF分析'},
            'go-contrarian': {'weight': 0.08, 'desc': '反向分析'},
            'go-noise': {'weight': 0.05, 'desc': '噪音过滤'},
            'go-fit': {'weight': 0.05, 'desc': '趋势拟合'},
            'go-thermo': {'weight': 0.05, 'desc': '热力学分析'},
        }
        
        # 技能表现追踪
        self.performance = defaultdict(list)
        
    def calculate_go_signals(self, closes: list, volumes: list, market_type: str) -> dict:
        """计算所有go技能信号"""
        if len(closes) < 20:
            return {}
        
        signals = {}
        
        # === go-core: 趋势核心 ===
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
        trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
        trend50 = (ma20 - ma50) / ma50 if ma50 > 0 else 0
        signals['go-core'] = trend * 10
        
        # === go-pool: 流动性分析 ===
        vol_avg = sum(volumes[-20:]) / 20
        vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
        signals['go-pool'] = (vol_ratio - 1) * 0.5
        
        # === go-rotate: 轮转策略 ===
        signals['go-rotate'] = trend * 0.8 if market_type == 'range' else trend * 0.3
        
        # === go-long-short: 多空策略 ===
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        signals['go-long-short'] = (rsi - 50) / 50
        
        # === go-detect: 机构检测 ===
        signals['go-detect'] = trend50 * 5
        
        # === go-etf: ETF分析 ===
        signals['go-etf'] = signals['go-pool'] * 0.5
        
        # === go-contrarian: 反向分析 ===
        signals['go-contrarian'] = -(rsi - 50) / 100
        
        # === go-noise: 噪音过滤 ===
        signals['go-noise'] = 0 if signals['go-pool'] > 0.5 else -abs(signals['go-pool'])
        
        # === go-fit: 趋势拟合 ===
        signals['go-fit'] = 1 - abs(ma5 - ma20) / ma20 if ma20 > 0 else 0
        
        # === go-thermo: 热力学 ===
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = sum(abs(r) for r in returns[-20:]) / 20
        signals['go-thermo'] = (0.5 - volatility) * 0.4
        
        return signals
    
    def fuse_signals(self, signals: dict, weights: dict, pm_signal: float = 0) -> float:
        """融合go技能信号 + Polymarket"""
        if not signals:
            return 0
        
        # go技能加权
        go_signal = 0
        weight_sum = 0
        
        for skill, weight in weights.items():
            if skill in signals:
                go_signal += signals[skill] * weight
                weight_sum += weight
        
        if weight_sum > 0:
            go_signal /= weight_sum
        
        # Polymarket权重 30%
        combined = go_signal * 0.7 + pm_signal * 0.3
        
        return combined
    
    def detect_market(self, closes: list) -> str:
        """检测市场类型"""
        if len(closes) < 50:
            return 'neutral'
        
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
        
        trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = sum(abs(r) for r in returns[-20:]) / 20
        
        if trend > 0.03:
            return 'trend'
        elif volatility < 0.02:
            return 'range'
        elif trend > 0.015 and volatility > 0.03:
            return 'breakout'
        return 'neutral'
    
    def adjust_weights(self, market_type: str) -> dict:
        """根据市场类型调整权重"""
        weights = {k: v['weight'] for k, v in self.skills.items()}
        
        if market_type == 'trend':
            weights['go-core'] *= 1.3
            weights['go-long-short'] *= 1.2
            weights['go-detect'] *= 0.9
        elif market_type == 'range':
            weights['go-pool'] *= 1.3
            weights['go-rotate'] *= 1.2
            weights['go-noise'] *= 0.8
        elif market_type == 'breakout':
            weights['go-detect'] *= 1.4
            weights['go-core'] *= 1.2
            weights['go-contrarian'] *= 0.8
        
        # 归一化
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}

# ============ API函数 ============

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

def get_price(symbol):
    try:
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=' + symbol + 'USDT'
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        d = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        return float(d['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=100):
    try:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + symbol + 'USDT&interval=' + interval + '&limit=' + str(limit)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return []

def place_order(symbol, side, quantity):
    try:
        ts = int(time.time() * 1000)
        qty_str = str(int(quantity)) if quantity >= 1 else '{:.6f}'.format(quantity)
        params = {'symbol': symbol + 'USDT', 'side': side, 'type': 'MARKET', 'quantity': qty_str, 'timestamp': ts, 'recvWindow': 5000}
        q = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
        sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = 'https://api.binance.com/api/v3/order?' + q + '&signature=' + sig
        req = urllib.request.Request(url, method='POST')
        req.add_header('X-MBX-APIKEY', API_KEY)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        resp = json.loads(opener.open(req, timeout=10).read().decode())
        if 'code' in resp: return {'success': False, 'error': resp['msg']}
        return {'success': True, 'symbol': symbol}
    except Exception as e: return {'success': False, 'error': str(e)}

def log(msg):
    ts = datetime.now().strftime('%m-%d %H:%M:%S')
    line = '[' + ts + '] ' + msg
    try:
        with open(LOG_FILE, 'a') as f: f.write(line + chr(10))
    except: pass
    print(line, flush=True)

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

# ============ 主程序 ============

def main():
    dispatcher = GoSkillDispatcher()
    
    log('=' * 60)
    log('G41 Enhanced - go技能调度系统启动')
    log('=' * 60)
    
    # 获取账户
    account = get_account()
    prices = {s: get_price(s) for s in ['BTC','ETH','BNB','XRP','ADA','SOL','DOT','LINK','DOGE','SHIB','NEIRO','BOME']}
    holdings = {}
    for b in account.get('balances', []):
        free = float(b.get('free', 0))
        asset = b['asset']
        if asset != 'USDT' and free > 0:
            price = prices.get(asset, 0)
            value = free * price
            if value > 0.1: holdings[asset] = {'amount': free, 'price': price, 'value': value}
    
    total = sum(h['value'] for h in holdings.values())
    usdt_bal = float([b for b in account.get('balances', []) if b['asset'] == 'USDT'][0]['free'])
    total += usdt_bal
    
    log('总资产: $' + str(round(total, 2)))
    log('USDT: $' + str(round(usdt_bal, 2)))
    
    # Polymarket信号
    log('')
    log('Polymarket信号:')
    for sym, sig in sorted(POLYMARKET_SIGNALS.items()): log('  ' + sym + ': ' + ('+' if sig > 0 else '') + str(round(sig, 2)))
    
    # go技能状态
    log('')
    log('go技能调度:')
    for skill, info in sorted(dispatcher.skills.items()): log('  ' + skill + ' (' + info['desc'] + '): ' + str(round(info['weight']*100, 1)) + '%')
    
    # 分析
    log('')
    log('综合分析:')
    
    decisions = []
    symbols = ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','DOGE','NEIRO','BOME']
    
    for sym in symbols:
        klines = get_klines(sym)
        if not klines or len(klines) < 50: continue
        
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        # 市场检测
        market = dispatcher.detect_market(closes)
        weights = dispatcher.adjust_weights(market)
        
        # go技能信号
        go_signals = dispatcher.calculate_go_signals(closes, volumes, market)
        
        # Polymarket信号
        pm_signal = POLYMARKET_SIGNALS.get(sym, 0)
        
        # 融合信号
        combined = dispatcher.fuse_signals(go_signals, weights, pm_signal)
        
        # 行动决策
        if combined > 0.15: action = 'buy'
        elif combined < -0.08: action = 'sell'
        else: action = 'hold'
        
        log('  ' + sym + ' [' + market + '] go:' + str(round(sum(go_signals.values())/len(go_signals),2)) + ' pm:' + str(round(pm_signal,2)) + ' => ' + action)
        
        # 交易决策
        if action == 'sell' and sym in holdings and holdings[sym]['value'] > 1:
            decisions.append({'action': 'sell', 'symbol': sym, 'amount': holdings[sym]['amount'] * 0.5})
        elif action == 'buy' and sym not in holdings and usdt_bal > 5:
            decisions.append({'action': 'buy', 'symbol': sym, 'budget': usdt_bal * 0.1})
    
    # 执行
    log('')
    log('执行决策:')
    for d in decisions[:3]:
        log('  ' + d['action'].upper() + ' ' + d['symbol'])
        if d['action'] == 'sell':
            result = place_order(d['symbol'], 'SELL', d['amount'])
            log('    结果: ' + ('成功' if result.get('success') else '失败:' + str(result.get('error', ''))))
        elif d['action'] == 'buy':
            price = prices.get(d['symbol'], 0)
            if price > 0:
                qty = d['budget'] / price
                if qty > 0.0001:
                    result = place_order(d['symbol'], 'BUY', qty)
                    log('    结果: ' + ('成功' if result.get('success') else '失败:' + str(result.get('error', ''))))
    
    log('')
    log('G41 Enhanced 启动完成!')

if __name__ == '__main__': main()
