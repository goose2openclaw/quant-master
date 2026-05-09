#!/usr/bin/env python3
"""
G12+ 机会监控 + 信号系统 v1.0
布林带收口突破 | 动能轮动 | 资金费率套利
每5分钟扫描,信号推送到指定位置
"""
import requests, time, json, numpy as np
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
BINANCE_API = "https://api.binance.com"
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
LOG = '/tmp/g12_plus_signals.json'
STATE = '/tmp/g12_plus_state.json'

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_klines(sym, limit=200):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'{BINANCE_API}/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]
    except: return []

def get_24hr(symbol):
    try:
        r = requests.get(f'{BINANCE_API}/api/v3/ticker/24hr?symbol={symbol}', proxies=PROXIES, timeout=5)
        d = r.json()
        return {
            'price': float(d['lastPrice']),
            'chg': float(d['priceChangePercent']),
            'high': float(d['highPrice']),
            'low': float(d['lowPrice'])
        }
    except: return None

def get_funding(symbol):
    try:
        r = requests.get(f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json().get('lastFundingRate', 0)) * 100
    except: return None

def analyze_bb(c, klines):
    if len(klines) < 50: return None
    closes = [k['close'] for k in klines]
    bb_now = np.std(closes[-20:]) / np.mean(closes[-20:]) * 100
    bb_hist = np.std(closes) / np.mean(closes) * 100
    ratio = bb_now / bb_hist if bb_hist > 0 else 1
    bb_high = np.mean(closes[-20:]) + 2*np.std(closes[-20:])
    bb_low = np.mean(closes[-20:]) - 2*np.std(closes[-20:])
    position = (closes[-1] - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50
    return {'coin': c, 'ratio': ratio, 'position': position, 'price': closes[-1], 'bb_now': bb_now, 'bb_hist': bb_hist}

def analyze_momentum():
    momenta = []
    for c in COINS:
        klines = get_klines(f'{c}USDT', 168)
        if klines and len(klines) >= 25:
            closes = [k['close'] for k in klines]
            chg_24h = (closes[-1] - closes[-25]) / closes[-25] * 100
            momenta.append({'coin': c, '24h': chg_24h, 'price': closes[-1]})
        time.sleep(0.05)
    return sorted(momenta, key=lambda x: -x['24h'])

def load_state():
    try:
        with open(STATE, 'r') as f: return json.load(f)
    except: return {'iter': 0, 'signals': [], 'alerts': []}

def save_state(s):
    with open(STATE, 'w') as f: json.dump(s, f, indent=2)

def main():
    log("="*50)
    log("G12+ 机会监控")
    log("="*50)
    
    state = load_state()
    state['iter'] += 1
    state['last_run'] = datetime.now().isoformat()
    
    signals = []
    
    # 1. 布林带收口检测
    log("\n📊 布林带收口:")
    bb_data = {}
    for c in ['BTC','ETH','SOL']:
        klines = get_klines(f'{c}USDT', 200)
        result = analyze_bb(c, klines)
        if result:
            bb_data[c] = result
            emoji = "🔴" if result['ratio'] < 0.3 else ("🟡" if result['ratio'] < 0.5 else "🟢")
            log(f"  {emoji} {c}: 比率{result['ratio']:.2f}x 位置{result['position']:.0f}% ${result['price']:.0f}")
            
            if result['ratio'] < 0.25:
                direction = "📈看涨" if result['position'] < 40 else ("📉看跌" if result['position'] > 60 else "⚖️中性")
                signals.append({
                    'type': 'BB_SQUEEZE',
                    'coin': c,
                    'action': 'LONG' if result['position'] < 40 else 'SHORT',
                    'score': (0.3 - result['ratio']) * 100,
                    'direction': direction,
                    'data': result
                })
        time.sleep(0.1)
    
    # 2. 动能排名
    log("\n📊 动能排名:")
    momenta = analyze_momentum()
    for i, m in enumerate(momenta[:5], 1):
        emoji = "🟢" if m['24h'] > 0 else "🔴"
        log(f"  {i}. {emoji} {m['coin']}: {m['24h']:+.2f}%")
    
    if len(momenta) >= 2 and momenta[-1]['24h'] < -2 and momenta[0]['24h'] > -1.5:
        weakest = momenta[-1]
        strongest = momenta[0]
        signals.append({
            'type': 'MOMENTUM',
            'coin': strongest['coin'],
            'action': 'ROTATE_TO',
            'score': 30,
            'from': weakest['coin'],
            'data': momenta
        })
    
    # 3. 资金费率
    log("\n📊 资金费率:")
    for c in ['BTC','ETH','SOL']:
        rate = get_funding(f'{c}USDT')
        if rate is not None:
            emoji = "🟢" if abs(rate) > 0.01 else "⚪"
            log(f"  {emoji} {c}: {rate:+.4f}%")
            if abs(rate) > 0.02:
                signals.append({
                    'type': 'FUNDING',
                    'coin': c,
                    'action': 'LONG' if rate < 0 else 'SHORT',
                    'score': abs(rate) * 200,
                    'data': {'rate': rate}
                })
        time.sleep(0.1)
    
    # 生成警报
    signals.sort(key=lambda x: -x['score'])
    state['signals'] = signals
    
    log("\n🎯 信号排名:")
    if signals:
        for i, s in enumerate(signals[:3], 1):
            emoji = "🟢" if "LONG" in s.get('action', "") or "ROTATE" in s.get('action', "") else "🔴"
            log(f"  {i}. {emoji} {s['type']}: {s['coin']} {s.get('action','N/A')} (评分:{s['score']:.0f})")
    else:
        log("  🟡 无高置信度信号")
    
    # 检查新信号
    new_alerts = []
    for s in signals[:1]:  # 只关注最强信号
        last = state.get('last_signal', {})
        if last.get('coin') != s['coin'] or last.get('type') != s['type']:
            new_alerts.append(s)
    
    if new_alerts:
        state['alerts'].append({
            'time': datetime.now().isoformat(),
            'signals': new_alerts
        })
        state['alerts'] = state['alerts'][-20:]
        log(f"\n⚡ 新信号触发: {new_alerts[0]['type']} {new_alerts[0]['coin']}")
    
    state['last_signal'] = signals[0] if signals else None
    save_state(state)
    
    # 保存信号日志
    with open(LOG, 'w') as f:
        json.dump(state, f, indent=2)
    
    log(f"\n迭代 #{state['iter']} 完成")
    log("="*50)
    return signals

if __name__ == '__main__':
    main()
