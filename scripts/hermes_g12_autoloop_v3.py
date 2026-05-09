#!/usr/bin/env python3
"""
G12 自主迭代系统 v3
🌟 自主学习 → 科学评估 → 持续优化 → 循环进化
"""
import requests, time, json, numpy as np, hmac, hashlib, random
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
BINANCE_API = "https://api.binance.com"
API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"

ITER_LOG = '/tmp/g12_autoloop_v3.json'

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_klines(sym, limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'{BINANCE_API}/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4])} for k in r.json()]
    except: return []

def get_rsi(prices, period=7):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 50

def simulate(initial, data, cfg):
    valid = [c for c in ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK'] if c in data]
    if not valid: return None
    min_d = min(len(data[c]) for c in valid)
    
    cap = initial
    pos = {c: 0.0 for c in valid}
    entry = {c: 0.0 for c in valid}
    trades = []
    
    lev = cfg.get('leverage', 3)
    pr = cfg.get('position', 0.30)
    
    for d in range(min_d):
        for c in valid:
            k = data[c][d]
            cs = [data[c][i]['close'] for i in range(max(0,d-30),d+1)]
            if len(cs) < 30: continue
            
            rsi = get_rsi(cs[-14:], 7)
            buy = rsi < cfg['rsi_buy']
            sell = rsi > cfg['rsi_sell']
            
            if buy and pos[c] == 0 and cap > 10:
                invest = cap * pr * lev
                qty = invest / k['close']
                cap -= invest * 0.001
                pos[c] = qty
                entry[c] = k['close']
                trades.append({'t':'LONG','c':c})
            
            if pos[c] > 0:
                pnl = (k['close'] - entry[c]) / entry[c] * lev
                if pnl >= cfg.get('tp', 0.08) or pnl <= -cfg.get('sl', 0.035) or sell:
                    cap += (k['close'] - entry[c]) * pos[c] * lev - pos[c] * k['close'] * 0.001
                    trades.append({'t':'CLOSE','c':c,'p':pnl})
                    pos[c] = 0
    
    fin = cap
    for c in valid:
        fin += pos[c] * data[c][-1]['close']
    
    closed = [t for t in trades if t['t'] == 'CLOSE']
    wins = sum(1 for t in closed if t.get('p',0) > 0)
    
    return {'return': (fin-initial)/initial*100, 'win_rate': wins/len(closed)*100 if closed else 0, 'trades': len(closed)}

def load_state():
    try:
        with open(ITER_LOG, 'r') as f:
            return json.load(f)
    except:
        return {'iter': 0, 'best': None, 'history': [], 'params': {}}

def save_state(state):
    with open(ITER_LOG, 'w') as f:
        json.dump(state, f, indent=2)

def mutate_params(params):
    new_params = params.copy()
    if random.random() < 0.5:
        new_params['rsi_buy'] = max(30, min(50, new_params.get('rsi_buy', 43) + random.choice([-3, -2, -1, 1, 2, 3])))
    if random.random() < 0.5:
        new_params['rsi_sell'] = max(50, min(70, new_params.get('rsi_sell', 53) + random.choice([-3, -2, -1, 1, 2, 3])))
    if random.random() < 0.5:
        new_params['tp'] = max(0.05, min(0.15, new_params.get('tp', 0.08) + random.choice([-0.01, -0.005, 0.005, 0.01])))
    if random.random() < 0.5:
        new_params['sl'] = max(0.02, min(0.05, new_params.get('sl', 0.035) + random.choice([-0.005, -0.0025, 0.0025, 0.005])))
    if random.random() < 0.5:
        new_params['position'] = max(0.20, min(0.40, new_params.get('position', 0.30) + random.choice([-0.05, -0.025, 0.025, 0.05])))
    return new_params

def main():
    log("="*60)
    log("🌟 G12 自主迭代 v3")
    log("="*60)
    
    state = load_state()
    state['iter'] += 1
    iter_num = state['iter']
    
    baseline = state.get('params') or {
        'rsi_buy': 43, 'rsi_sell': 53,
        'tp': 0.08, 'sl': 0.035,
        'position': 0.30, 'leverage': 3
    }
    
    best_return = (state.get('best') or {}).get('return', 0) or 0
    log(f"\n📊 第{iter_num}次迭代 | 最优: {best_return:+.1f}%")
    
    log("\n📥 获取数据...")
    data = {}
    for c in ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']:
        d = get_klines(f'{c}USDT', 720)
        if d: data[c] = d
        time.sleep(0.05)
    log(f"   数据: {len(data)}币种")
    
    result = simulate(1000, data, baseline)
    if not result:
        log("数据不足")
        return
    
    log(f"   基线: {result['return']:+.1f}% | 胜率:{result['win_rate']:.1f}% | 交易:{result['trades']}")
    
    # 变体测试
    variants = []
    for i in range(5):
        new_params = mutate_params(baseline)
        r = simulate(1000, data, new_params)
        if r:
            variants.append({'params': new_params, 'result': r})
    
    variants.sort(key=lambda x: -x['result']['return'])
    
    log("\n🔄 变体测试:")
    for i, v in enumerate(variants[:3], 1):
        log(f"   {i}. {v['result']['return']:+.1f}%")
    
    best_variant = variants[0]
    improved = False
    
    if result['return'] >= best_variant['result']['return']:
        log(f"\n⚠️ 基线最优,保持参数")
    else:
        baseline = best_variant['params']
        state['best'] = {'return': best_variant['result']['return'], 'params': baseline}
        improved = True
        log(f"\n✅ 新最优: {best_variant['result']['return']:+.1f}%")
    
    state['history'].append({'iter': iter_num, 'time': datetime.now().isoformat(), 'improved': improved})
    state['history'] = state['history'][-50:]
    state['params'] = baseline
    save_state(state)
    
    log(f"\n🏆 最优: {state.get('best', {}).get('return', 0):+.1f}%")
    log("="*60)

if __name__ == '__main__':
    main()
