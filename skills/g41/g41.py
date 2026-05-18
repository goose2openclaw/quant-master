#!/usr/bin/env python3
"""
G41 v1.2 - Active Skill Management
================================
- 动态技能激活
- 表现追踪学习
- 自适应权重调整
- 实时迭代优化
"""

import json, time, urllib.request, hmac, hashlib
from datetime import datetime
from collections import defaultdict

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g41.log'

POLYMARKET = {'BTC':0.42,'ETH':0.35,'SOL':0.28,'DOGE':0.22,'XRP':0.15,'ADA':0.12,'DOT':0.10,'LINK':0.08}

# ============ Active Skill Manager ============

class ActiveSkillManager:
    """
    活跃技能管理器
    - 技能表现追踪
    - 动态权重调整
    - 自适应激活/休眠
    """
    
    def __init__(self):
        # 技能定义
        self.skills = {
            'go-core': {'base': 0.20, 'desc': '趋势核心', 'active': True, 'wins': 0, 'losses': 0},
            'go-pool': {'base': 0.15, 'desc': '流动性', 'active': True, 'wins': 0, 'losses': 0},
            'go-rotate': {'base': 0.12, 'desc': '轮转', 'active': True, 'wins': 0, 'losses': 0},
            'go-long-short': {'base': 0.12, 'desc': '多空', 'active': True, 'wins': 0, 'losses': 0},
            'go-detect': {'base': 0.10, 'desc': '机构检测', 'active': True, 'wins': 0, 'losses': 0},
            'go-etf': {'base': 0.08, 'desc': 'ETF', 'active': True, 'wins': 0, 'losses': 0},
            'go-contrarian': {'base': 0.08, 'desc': '反向', 'active': True, 'wins': 0, 'losses': 0},
            'go-noise': {'base': 0.05, 'desc': '噪音', 'active': True, 'wins': 0, 'losses': 0},
            'go-fit': {'base': 0.05, 'desc': '拟合', 'active': True, 'wins': 0, 'losses': 0},
            'go-thermo': {'base': 0.05, 'desc': '热力', 'active': True, 'wins': 0, 'losses': 0},
        }
        
        # 技能历史
        self.history = defaultdict(list)
        self.cycle = 0
        
    def update_performance(self, skill: str, pnl: float):
        """更新技能表现"""
        if skill not in self.skills:
            return
        
        if pnl > 0:
            self.skills[skill]['wins'] += 1
        else:
            self.skills[skill]['losses'] += 1
        
        # 记录历史
        self.history[skill].append({'pnl': pnl, 'time': time.time()})
        
        # 保持最近20条记录
        if len(self.history[skill]) > 20:
            self.history[skill] = self.history[skill][-20:]
    
    def adjust_weights(self, market: str) -> dict:
        """根据表现和市场调整权重"""
        self.cycle += 1
        
        # 计算每个技能的胜率
        weights = {}
        total_adjust = 0
        
        for skill, data in self.skills.items():
            wins = data['wins']
            losses = data['losses']
            total = wins + losses
            
            # 计算胜率
            win_rate = wins / total if total > 0 else 0.5
            
            # 根据胜率调整权重
            if total >= 5:  # 至少5次交易才调整
                if win_rate > 0.6:
                    adjust = 1.2  # +20%
                elif win_rate < 0.4:
                    adjust = 0.8  # -20%
                else:
                    adjust = 1.0
            else:
                adjust = 1.0
            
            # 市场类型调整
            if market == 'trend':
                if skill in ['go-core', 'go-long-short']:
                    adjust *= 1.2
                elif skill in ['go-pool', 'go-noise']:
                    adjust *= 0.9
            elif market == 'range':
                if skill in ['go-pool', 'go-rotate']:
                    adjust *= 1.2
                elif skill in ['go-core']:
                    adjust *= 0.9
            elif market == 'breakout':
                if skill in ['go-detect', 'go-core']:
                    adjust *= 1.3
            
            # 动态激活/休眠
            if total >= 10:
                if win_rate < 0.3:
                    data['active'] = False
                    adjust *= 0.5
                elif win_rate > 0.5:
                    data['active'] = True
            
            adjusted = data['base'] * adjust
            weights[skill] = adjusted
            total_adjust += adjusted
        
        # 归一化
        if total_adjust > 0:
            weights = {k: v/total_adjust for k, v in weights.items()}
        
        return weights
    
    def get_skill_status(self) -> list:
        """获取技能状态"""
        status = []
        for skill, data in self.skills.items():
            wins = data['wins']
            losses = data['losses']
            total = wins + losses
            win_rate = wins / total * 100 if total > 0 else 0
            
            status.append({
                'skill': skill,
                'desc': data['desc'],
                'base': data['base'],
                'wins': wins,
                'losses': losses,
                'total': total,
                'win_rate': win_rate,
                'active': data['active']
            })
        
        # 按胜率排序
        status.sort(key=lambda x: -x['win_rate'])
        return status

def calc_signals(closes, volumes, market):
    """计算go技能信号"""
    if len(closes) < 20:
        return {}
    
    signals = {}
    
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
    trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
    trend50 = (ma20 - ma50) / ma50 if ma50 > 0 else 0
    
    vol_avg = sum(volumes[-20:]) / 20
    vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
    
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    rs = avg_gain / avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100 / (1 + rs))
    
    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
    volatility = sum(abs(r) for r in returns[-20:]) / 20
    
    signals['go-core'] = trend * 10
    signals['go-pool'] = (vol_ratio - 1) * 0.5
    signals['go-rotate'] = trend * (0.8 if market == 'range' else 0.3)
    signals['go-long-short'] = (rsi - 50) / 50
    signals['go-detect'] = trend50 * 5
    signals['go-etf'] = signals['go-pool'] * 0.5
    signals['go-contrarian'] = -(rsi - 50) / 100
    signals['go-noise'] = 0 if signals['go-pool'] > 0.5 else -abs(signals['go-pool'])
    signals['go-fit'] = 1 - abs(ma5 - ma20) / ma20 if ma20 > 0 else 0
    signals['go-thermo'] = (0.5 - volatility) * 0.4
    
    return signals

def detect_market(closes):
    if len(closes) < 50: return 'neutral'
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
    volatility = sum(abs(r) for r in returns[-20:]) / 20
    trend = (ma5 - ma20) / ma20 if ma20 > 0 else 0
    if trend > 0.03: return 'trend'
    elif volatility < 0.02: return 'range'
    elif trend > 0.015 and volatility > 0.03: return 'breakout'
    return 'neutral'

# API functions
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

def get_klines(sym, interval='1h', limit=100):
    try:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=' + interval + '&limit=' + str(limit)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return []

def place_order(sym, side, qty):
    try:
        ts = int(time.time() * 1000)
        qty_str = str(int(qty)) if qty >= 1 else '{:.6f}'.format(qty)
        params = {'symbol': sym + 'USDT', 'side': side, 'type': 'MARKET', 'quantity': qty_str, 'timestamp': ts, 'recvWindow': 5000}
        q = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
        sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = 'https://api.binance.com/api/v3/order?' + q + '&signature=' + sig
        req = urllib.request.Request(url, method='POST')
        req.add_header('X-MBX-APIKEY', API_KEY)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        resp = json.loads(opener.open(req, timeout=10).read().decode())
        if 'code' in resp: return {'success': False, 'error': resp['msg']}
        return {'success': True, 'symbol': sym}
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

def main():
    manager = ActiveSkillManager()
    
    log('=' * 60)
    log('G41 v1.2 Active Skill Management 启动')
    log('=' * 60)
    
    # 账户
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
    
    log('总资产: $' + str(round(total, 2)) + ' USDT: $' + str(round(usdt_bal, 2)))
    
    # Polymarket
    log('')
    log('Polymarket信号:')
    for sym, sig in sorted(POLYMARKET.items()): log('  ' + sym + ': +' + str(round(sig, 2)))
    
    # 技能状态
    log('')
    log('技能状态 (动态):')
    for s in manager.get_skill_status()[:5]:
        status = 'ON' if s['active'] else 'OFF'
        log('  ' + s['skill'] + ' [' + status + '] ' + str(round(s['win_rate'], 0)) + '% (' + str(s['wins']) + 'W/' + str(s['losses']) + 'L)')
    
    # 分析
    log('')
    log('综合分析:')
    decisions = []
    
    for sym in ['BTC','ETH','SOL','XRP','ADA','DOT','LINK','DOGE','NEIRO','BOME']:
        klines = get_klines(sym)
        if not klines or len(klines) < 50: continue
        
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        market = detect_market(closes)
        
        weights = manager.adjust_weights(market)
        signals = calc_signals(closes, volumes, market)
        
        # 融合
        go_signal = sum(signals.get(s, 0) * weights.get(s, 0) for s in weights)
        pm = POLYMARKET.get(sym, 0)
        combined = go_signal * 0.7 + pm * 0.3
        
        action = 'buy' if combined > 0.12 else 'sell' if combined < -0.08 else 'hold'
        
        log('  ' + sym + ' [' + market + '] go:' + str(round(go_signal, 2)) + ' pm:' + str(round(pm, 2)) + ' => ' + action)
        
        if action == 'sell' and sym in holdings and holdings[sym]['value'] > 1:
            decisions.append({'action': 'sell', 'symbol': sym, 'amount': holdings[sym]['amount'] * 0.5})
        elif action == 'buy' and sym not in holdings and usdt_bal > 5:
            decisions.append({'action': 'buy', 'symbol': sym, 'budget': usdt_bal * 0.1})
    
    # 执行
    log('')
    log('执行决策:')
    if not decisions:
        log('  无需交易')
    for d in decisions[:2]:
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
    log('G41 v1.2 Active Skill Management 完成!')

if __name__ == '__main__': main()
