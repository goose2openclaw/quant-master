#!/usr/bin/env python3
"""
G12+ 机会策略Cron版 v1.0
每15分钟执行,持续迭代优化
"""
import requests, time, numpy as np, json
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
LOG = '/tmp/g12_plus_opportunities.json'
ITER_LOG = '/tmp/g12_plus_iterations.json'

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")

def get_klines(sym, limit=168):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [float(k[4]) for k in r.json()]
    except: return []

def get_funding_rate(sym):
    try:
        url = f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={sym}'
        r = requests.get(url, proxies=PROXIES, timeout=5)
        return float(r.json().get('lastFundingRate', 0)) * 100
    except: return None

def get_rsi(prices, period=7):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def scan_opportunities():
    """扫描所有机会"""
    opportunities = []
    
    # 1. 布林带收口突破
    for c in ['BTC','ETH','SOL']:
        closes = get_klines(f'{c}USDT', 200)
        if len(closes) >= 50:
            bb_now = np.std(closes[-20:]) / np.mean(closes[-20:]) * 100
            bb_hist = np.std(closes) / np.mean(closes) * 100
            ratio = bb_now / bb_hist if bb_hist > 0 else 1
            
            if ratio < 0.5:  # 收口
                opportunities.append({
                    'type': 'BB_SQUEEZE',
                    'coin': c,
                    'score': (1 - ratio) * 50,
                    'expected': bb_hist * 2,
                    'data': {'ratio': ratio, 'bb_now': bb_now, 'bb_hist': bb_hist}
                })
    
    # 2. 资金费率套利
    for c in ['BTC','ETH','SOL']:
        rate = get_funding_rate(f'{c}USDT')
        if rate is not None and abs(rate) > 0.005:
            opportunities.append({
                'type': 'FUNDING_ARB',
                'coin': c,
                'score': abs(rate) * 500,
                'expected': abs(rate) * 3 * 4,
                'data': {'rate': rate}
            })
        time.sleep(0.1)
    
    # 3. 动能排名
    momenta = []
    for c in COINS:
        closes = get_klines(f'{c}USDT', 168)
        if len(closes) >= 25:
            chg = (closes[-1] - closes[-25]) / closes[-25] * 100
            momenta.append({'coin': c, 'chg': chg})
        time.sleep(0.05)
    
    if momenta:
        momenta.sort(key=lambda x: -x['chg'])
        if len(momenta) >= 2:
            weakest = momenta[-1]
            strongest = momenta[0]
            if weakest['chg'] < -1 and strongest['chg'] > -1:
                opportunities.append({
                    'type': 'MOMENTUM_ROTATION',
                    'coin': f"{weakest['coin']}→{strongest['coin']}",
                    'score': abs(strongest['chg'] - weakest['chg']) * 5,
                    'expected': abs(strongest['chg'] - weakest['chg']) * 0.3,
                    'data': momenta
                })
    
    return opportunities

def load_iterations():
    try:
        with open(ITER_LOG, 'r') as f:
            return json.load(f)
    except: return {'iter': 0, 'best': None, 'history': []}

def save_iterations(data):
    with open(ITER_LOG, 'w') as f:
        json.dump(data, f, indent=2)

def iterate():
    """迭代优化"""
    state = load_iterations()
    state['iter'] += 1
    iter_num = state['iter']
    
    log(f"G12+ 迭代 #{iter_num}")
    
    # 获取当前机会
    opps = scan_opportunities()
    opps.sort(key=lambda x: -x['score'])
    
    if opps:
        best = opps[0]
        log(f"最优机会: {best['type']} {best['coin']} 评分:{best['score']:.1f} 预期:{best['expected']:.2f}%")
        
        # 更新最优
        if state['best'] is None or best['score'] > state['best'].get('score', 0):
            state['best'] = best
            log(f"🆕 新最优!")
        
        # 记录历史
        state['history'].append({
            'iter': iter_num,
            'time': datetime.now().isoformat(),
            'opportunity': best['type'],
            'coin': best['coin'],
            'score': best['score'],
            'expected': best['expected']
        })
        state['history'] = state['history'][-50:]
    else:
        log("无高置信度机会")
    
    save_iterations(state)
    return state

def main():
    log("="*50)
    log("G12+ 机会策略Cron")
    state = iterate()
    log(f"累计迭代: {state['iter']}次")
    if state['best']:
        log(f"最优: {state['best']['type']} {state['best']['coin']}")
    log("="*50)

if __name__ == '__main__':
    main()
