#!/usr/bin/env python3
"""
G12 自适应市场状态交易系统 v5.0
- 市场状态识别: 单边趋势 / 震荡回调
- 自动切换最优配置
- 收益自动校正
"""
import requests, numpy as np, time, json, hmac, hashlib, math
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== 配置矩阵 ==========
CONFIG = {
    '单边趋势': {
        'rsi_buy': 28, 'rsi_sell': 70,
        'bb_buy': 20, 'bb_sell': 80,
        'tp': 0.15, 'sl': 0.05,
        'position': 0.35, 'leverage': 5,
        'min_return': 184.0  # 最低收益要求
    },
    '震荡回调': {
        'rsi_buy': 35, 'rsi_sell': 65,
        'bb_buy': 30, 'bb_sell': 70,
        'tp': 0.08, 'sl': 0.04,
        'position': 0.25, 'leverage': 3,
        'min_return': 50.0
    }
}

# ========== 工具函数 ==========
def get_klines(sym, limit=200):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    r = requests.get(url, proxies=PROXIES, timeout=15)
    return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]

def calc_rsi(prices, period=7):
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 50

def calc_bb_pos(closes, highs, lows, period=20):
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    curr = closes[-1]
    return (curr - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def get_momentum(closes, period=24):
    if len(closes) < period: return 0
    return (closes[-1] - closes[-period]) / closes[-period] * 100

# ========== 市场状态识别 ==========
def detect_market_state(coin='BTC'):
    """识别市场状态: 单边趋势 / 震荡回调"""
    try:
        klines = get_klines(f'{coin}USDT', 500)
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        if len(closes) < 100:
            return '震荡回调', 0
        
        # 1. 计算RSI位置
        rsi = calc_rsi(closes)
        
        # 2. 计算动能耗散
        recent_mom = get_momentum(closes, 24)
        older_mom = get_momentum(closes[:-24], 24) if len(closes) > 48 else 0
        mom_acceleration = recent_mom - older_mom
        
        # 3. 计算布林带宽度(波动率)
        bb_widths = []
        for i in range(50, len(closes)):
            bb_high = np.mean(highs[i-20:i]) + 2*np.std(highs[i-20:i])
            bb_low = np.mean(lows[i-20:i]) - 2*np.std(lows[i-20:i])
            width = (bb_high - bb_low) / np.mean(closes[i-20:i]) * 100
            bb_widths.append(width)
        avg_bb_width = np.mean(bb_widths)
        
        # 4. 计算趋势强度
        trend_strength = abs(recent_mom)
        
        # 判断逻辑
        # 单边趋势: 动能耗散慢,RSI偏向极端,趋势强度高
        # 震荡回调: 波动率高,动能耗散快,RSI居中
        
        score = 0
        
        # RSI极端加分
        if rsi < 35 or rsi > 65:
            score += 1
        
        # 趋势强度高加分
        if trend_strength > 5:
            score += 1
        elif trend_strength < 2:
            score -= 1
        
        # 波动率适中(不太高不太低)
        if 3 < avg_bb_width < 8:
            score += 1
        elif avg_bb_width >= 8:
            score -= 1
        
        state = '单边趋势' if score >= 2 else '震荡回调'
        confidence = abs(score) / 4 * 100
        
        return state, confidence
    except Exception as e:
        return '震荡回调', 0

# ========== 配置校正 ==========
def auto_calibrate_config(state, current_return=None):
    """自动校正配置"""
    cfg = CONFIG[state].copy()
    
    if current_return is not None and current_return < cfg['min_return']:
        # 收益不达标,收紧止损提高胜率
        cfg['sl'] = max(0.02, cfg['sl'] * 0.8)
        cfg['tp'] = cfg['tp'] * 0.9
        cfg['position'] = min(0.4, cfg['position'] * 1.1)
    
    return cfg

# ========== 信号生成 ==========
def generate_signal(coin, state):
    """根据市场状态生成信号"""
    cfg = auto_calibrate_config(state)
    
    try:
        klines = get_klines(f'{coin}USDT', 200)
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        if len(closes) < 50:
            return None
        
        rsi = calc_rsi(closes[-50:])
        bb = calc_bb_pos(closes[-50:], highs[-50:], lows[-50:])
        mom = get_momentum(closes)
        
        # 买入信号
        if rsi < cfg['rsi_buy'] and bb < cfg['bb_buy']:
            return {'type': 'LONG', 'rsi': rsi, 'bb': bb, 'mom': mom, 'config': cfg}
        
        # 卖出信号
        if rsi > cfg['rsi_sell'] and bb > cfg['bb_sell']:
            return {'type': 'SHORT', 'rsi': rsi, 'bb': bb, 'mom': mom, 'config': cfg}
        
        return None
    except:
        return None

# ========== 回测 ==========
def backtest_adaptive():
    """回测自适应策略"""
    print("=" * 60)
    print("G12 自适应市场状态策略回测")
    print("=" * 60)
    
    # 获取数据
    print("\n获取数据...")
    data = {}
    for coin in COINS:
        klines = get_klines(f'{coin}USDT', 1000)
        if klines:
            data[coin] = klines
            print(f"  {coin}: {len(klines)}条")
    
    if not data:
        print("数据获取失败")
        return
    
    # 分别回测两种市场状态
    results = {}
    
    for state_name in ['单边趋势', '震荡回调']:
        cfg = CONFIG[state_name]
        valid = [c for c in COINS if c in data and len(data[c]) >= 100]
        min_d = min(len(data[c]) for c in valid)
        
        capital = 1000
        pos = {c: 0 for c in valid}
        entry = {c: 0 for c in valid}
        trades = wins = losses = 0
        
        for d in range(50, min_d):
            for c in valid:
                closes = [data[c][i]['close'] for i in range(max(0,d-50),d+1)]
                highs = [data[c][i]['high'] for i in range(max(0,d-19),d+1)]
                lows = [data[c][i]['low'] for i in range(max(0,d-19),d+1)]
                if len(closes) < 50: continue
                
                rsi = calc_rsi(closes)
                bb = calc_bb_pos(closes, highs, lows)
                
                if pos[c] == 0:
                    if rsi < cfg['rsi_buy'] and bb < cfg['bb_buy']:
                        pos[c] = 1; entry[c] = closes[-1]; trades += 1
                    elif rsi > cfg['rsi_sell'] and bb > cfg['bb_sell']:
                        pos[c] = -1; entry[c] = closes[-1]; trades += 1
                else:
                    pct = (closes[-1] - entry[c]) / entry[c] if pos[c] == 1 else (entry[c] - closes[-1]) / entry[c]
                    if pct >= cfg['tp'] or pct <= -cfg['sl']:
                        if pct > 0: wins += 1
                        else: losses += 1
                        capital *= (1 + cfg['position'] * pct * cfg['leverage'])
                        pos[c] = 0
        
        t = wins + losses
        results[state_name] = {
            'return': (capital - 1000) / 1000 * 100,
            'win_rate': wins / t * 100 if t > 0 else 0,
            'trades': t, 'wins': wins, 'losses': losses,
            'config': cfg
        }
    
    # 输出结果
    print("\n" + "=" * 60)
    print("回测结果对比:")
    print("=" * 60)
    print(f"{'市场状态':<12} {'收益':>10} {'胜率':>8} {'交易':>6} {'RSI买':>6} {'RSI卖':>6} {'TP':>6} {'SL':>6}")
    print("-" * 60)
    
    for state_name, r in results.items():
        cfg = r['config']
        print(f"{state_name:<12} {r['return']:>+10.2f}% {r['win_rate']:>7.1f}% {r['trades']:>6} {cfg['rsi_buy']:>6} {cfg['rsi_sell']:>6} {cfg['tp']*100:>5.1f}% {cfg['sl']*100:>5.1f}%")
    
    print("=" * 60)
    
    # 市场状态检测
    print("\n当前市场状态检测:")
    for coin in ['BTC', 'ETH', 'SOL']:
        state, conf = detect_market_state(coin)
        print(f"  {coin}: {state} (置信度: {conf:.0f}%)")
    
    return results

if __name__ == '__main__':
    backtest_adaptive()
