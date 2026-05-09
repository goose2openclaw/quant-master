#!/usr/bin/env python3
"""
G16 量化交易系统 v2.0 (正式版)
基于+52%优化的最优配置
"""
import requests, numpy as np, time, json
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== G16 v2.0 正式配置 ==========
CONFIG = {
    'version': 'G16-v2.0',
    'mode': 'optimized',
    'rsi_buy': 35,
    'rsi_sell': 65,
    'bb_buy': 30,
    'bb_sell': 70,
    'tp': 0.12,
    'sl': 0.04,
    'position': 0.35,
    'leverage': 5,
    'bb_threshold': 0.35,
    'min_days': 15,
    'target_return': 52.0
}

# ========== 工具函数 ==========
def get_klines(sym, limit=200):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    r = requests.get(url, proxies=PROXIES, timeout=15)
    return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3]),'volume':float(k[5])} for k in r.json()]

def calc_rsi(prices):
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-7:])
    avg_loss = np.mean(loss[-7:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 50

def calc_bb(closes):
    std = np.std(closes[-20:])
    mean = np.mean(closes[-20:])
    upper, lower = mean + 2*std, mean - 2*std
    pos = (closes[-1] - lower) / (upper - lower) * 100 if upper > lower else 50
    ratio = std / mean * 100 if mean > 0 else 0
    return pos, ratio

def get_momentum(closes):
    return (closes[-1] - closes[-24]) / closes[-24] * 100 if len(closes) >= 24 else 0

def get_volume_profile(klines):
    if len(klines) < 20: return 1.0
    vols = [k['volume'] for k in klines[-20:]]
    return np.mean(vols[-5:]) / np.mean(vols) if np.mean(vols) > 0 else 1.0

# ========== 市场检测 ==========
def detect_market():
    """检测市场状态"""
    try:
        klines = get_klines('BTCUSDT', 100)
        closes = [k['close'] for k in klines]
        rsi = calc_rsi(closes)
        mom = get_momentum(closes)
        
        score = 0
        if rsi < 35 or rsi > 65: score += 1
        if abs(mom) > 5: score += 1
        
        if score >= 2:
            return '趋势市场'
        return '震荡市场'
    except:
        return '震荡市场'

# ========== 信号生成 ==========
def generate_signal(coin):
    """生成交易信号"""
    try:
        klines = get_klines(f'{coin}USDT', 200)
        closes = [k['close'] for k in klines]
        
        if len(closes) < 50: return None
        
        rsi = calc_rsi(closes)
        bb_pos, ratio = calc_bb(closes)
        mom = get_momentum(closes)
        vol = get_volume_profile(klines)
        
        cfg = CONFIG
        score = 0
        signals = []
        
        # 布林带收口
        if ratio < cfg['bb_threshold']:
            if rsi < cfg['rsi_buy'] and bb_pos < cfg['bb_buy']:
                score += 3
                signals.append(f'BB低位({bb_pos:.0f}%)')
            elif rsi > cfg['rsi_sell'] and bb_pos >= cfg['bb_sell']:
                score += 3
                signals.append(f'BB高位({bb_pos:.0f}%)')
        
        # RSI极端
        if rsi < 30 or rsi > 70:
            score += 1
            signals.append(f'RSI极端({rsi:.1f})')
        
        # 成交量
        if vol > 1.5:
            score += 1
            signals.append(f'放量({vol:.2f}x)')
        
        if score >= 4:
            return {
                'type': 'LONG' if rsi < cfg['rsi_buy'] else 'SHORT',
                'coin': coin,
                'score': score,
                'signals': signals,
                'rsi': rsi,
                'bb': bb_pos,
                'mom': mom,
                'price': closes[-1]
            }
        return None
    except:
        return None

# ========== 主程序 ==========
def main():
    print("=" * 60)
    print("G16 v2.0 量化交易系统 (正式版)")
    print("=" * 60)
    
    market = detect_market()
    print(f"\n市场状态: {market}")
    print(f"配置: RSI {CONFIG['rsi_buy']}/{CONFIG['rsi_sell']} TP {CONFIG['tp']*100:.0f}% SL {CONFIG['sl']*100:.0f}%")
    
    # 扫描信号
    signals = []
    for c in COINS:
        sig = generate_signal(c)
        if sig:
            signals.append(sig)
    
    if signals:
        print(f"\n信号 ({len(signals)}个):")
        for s in sorted(signals, key=lambda x: -x['score'])[:3]:
            print(f"  {s['type']} {s['coin']} @ ${s['price']:.2f} (评分:{s['score']})")
    else:
        print("\n无高置信度信号")
    
    return signals

if __name__ == '__main__':
    main()
