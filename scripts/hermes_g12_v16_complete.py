#!/usr/bin/env python3
"""
Hermes G12 v16 - 完整版 (集成Hermes/GO2SE全部功能)
增强: 插针捕捉 | 波动率预警 | 多时间周期 | 动态止盈 | 资金费率 | 情绪分析
"""
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== G12 v16 核心配置 ==========
CONFIG = {
    'version': 'v16-G12完整版',
    'rsi_buy': 43, 'rsi_sell': 53,
    'bb_buy': 25, 'bb_sell': 75,
    'take_profit': 0.08, 'stop_loss': 0.035,
    'position': 0.35, 'leverage': 3,
    'short_rsi': 70, 'short_bb': 85,
    'decision_threshold': 0.70,
    'rsi_period': 7,
    # ========== 新增功能开关 ==========
    'enable_spike_catch': True,      # 插针捕捉
    'enable_volatility_alert': True, # 波动率预警
    'enable_multi_tf': True,         # 多时间周期确认
    'enable_dynamic_tp': True,        # 动态止盈
    'enable_funding_alert': True,    # 资金费率预警
    'enable_sentiment': True,        # 情绪分析
    'enable_correlation': True,      # 相关性分析
}

# ========== 工具函数 ==========
def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_24hr(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', proxies=PROXIES, timeout=5)
        d = r.json()
        return {
            'price':float(d['lastPrice']),'chg':float(d['priceChangePercent']),
            'high':float(d['highPrice']),'low':float(d['lowPrice']),
            'volume':float(d['quoteVolume']),' trades':int(d['trades'])
        }
    except: return None

def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3]),'open':float(k[1]),'volume':float(k[5])} for k in r.json()]
    except: return []

def get_funding_rate(symbol):
    try:
        url = f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}'
        r = requests.get(url, proxies=PROXIES, timeout=5)
        data = r.json()
        return float(data.get('lastFundingRate', 0)) * 100  # 转为百分比
    except: return None

def get_rsi(prices, period=7):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def bollinger_pos(price, highs, lows, period=20):
    if len(highs) < period: return 50
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def get_macd(prices):
    if len(prices) < 26: return 0
    return np.mean(prices[-12:]) - np.mean(prices[-26:])

def volatility(closes, period=20):
    """计算波动率"""
    if len(closes) < period: return 0
    returns = np.diff(closes[-period:]) / closes[-period:-1]
    return np.std(returns) * 100

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    return round(round(qty/10**(-p))*10**(-p), p)

# ========== 功能1: 多时间周期确认 ==========
def multi_timeframe_confirm(c, price_data):
    """多时间周期信号确认: 1h + 4h + 1d"""
    if not CONFIG.get('enable_multi_tf', True):
        return 1.0
    
    result = {'1h': 0, '4h': 0, '1d': 0}
    
    # 1小时
    klines_1h = price_data.get(c, [])
    if len(klines_1h) >= 20:
        closes = [k['close'] for k in klines_1h]
        highs = [k['high'] for k in klines_1h]
        lows = [k['low'] for k in klines_1h]
        rsi_1h = get_rsi(closes, 7)
        bb_1h = bollinger_pos(closes[-1], highs, lows, 20)
        if rsi_1h < 40 and bb_1h < 25: result['1h'] = 1
        elif rsi_1h > 60 and bb_1h > 75: result['1h'] = -1
    
    # 4小时 (模拟)
    if len(klines_1h) >= 96:
        closes_4h = [k['close'] for k in klines_1h[::4]]
        rsi_4h = get_rsi(closes_4h[-24:], 7)
        if rsi_4h < 40: result['4h'] = 1
        elif rsi_4h > 60: result['4h'] = -1
    
    # 1天 (模拟)
    if len(klines_1h) >= 168:
        closes_1d = [k['close'] for k in klines_1h[::24]]
        rsi_1d = get_rsi(closes_1d[-7:], 7)
        if rsi_1d < 45: result['1d'] = 1
        elif rsi_1d > 55: result['1d'] = -1
    
    # 综合评分
    score = (result['1h'] * 0.5 + result['4h'] * 0.3 + result['1d'] * 0.2)
    return score

# ========== 功能2: 插针捕捉 ==========
def detect_spike(c, price_data):
    """检测插针 (wicks) - 极端价格波动"""
    if not CONFIG.get('enable_spike_catch', True):
        return None
    
    klines = price_data.get(c, [])
    if len(klines) < 10:
        return None
    
    current = klines[-1]
    price = current['close']
    
    # 计算上下影线长度
    upper_wick = current['high'] - max(price, current['open'])
    lower_wick = min(price, current['open']) - current['low']
    body = abs(price - current['open'])
    
    # 影线/Body比例
    if body > 0:
        upper_ratio = upper_wick / body
        lower_ratio = lower_wick / body
    else:
        return None
    
    # 检测插针
    spike = None
    if upper_ratio > 3 and lower_ratio < 0.3:
        # 上插针 (可能反转下跌)
        spike = {'type': 'upper_wick', 'strength': upper_ratio, 'action': 'short'}
    elif lower_ratio > 3 and upper_ratio < 0.3:
        # 下插针 (可能反弹上涨)
        spike = {'type': 'lower_wick', 'strength': lower_ratio, 'action': 'long'}
    
    return spike

# ========== 功能3: 波动率预警 ==========
def volatility_alert(c, price_data):
    """波动率异常检测"""
    if not CONFIG.get('enable_volatility_alert', True):
        return None
    
    klines = price_data.get(c, [])
    if len(klines) < 60:
        return None
    
    closes = [k['close'] for k in klines]
    
    # 当前波动率 vs 历史平均
    current_vol = volatility(closes[-20:], 20)
    historical_vol = volatility(closes, 60)
    
    if historical_vol > 0 and current_vol > historical_vol * 2:
        return {
            'current': current_vol,
            'historical': historical_vol,
            'ratio': current_vol / historical_vol,
            'alert': 'HIGH_VOLATILITY'
        }
    
    return None

# ========== 功能4: 动态止盈 ==========
def dynamic_take_profit(c, price_data, entry_price, current_price, position_type='long'):
    """根据波动率动态调整止盈"""
    if not CONFIG.get('enable_dynamic_tp', True):
        return CONFIG['take_profit']
    
    klines = price_data.get(c, [])
    if len(klines) < 20:
        return CONFIG['take_profit']
    
    closes = [k['close'] for k in klines]
    vol = volatility(closes[-30:], 20)
    
    # 波动率高时,扩大止盈目标
    base_tp = CONFIG['take_profit']
    
    if vol > 3:
        # 高波动,止盈提高20%
        return base_tp * 1.2
    elif vol < 1:
        # 低波动,止盈降低
        return base_tp * 0.8
    else:
        return base_tp

# ========== 功能5: 资金费率预警 ==========
def funding_alert(c):
    """资金费率预警"""
    if not CONFIG.get('enable_funding_alert', True):
        return None
    
    rate = get_funding_rate(f'{c}USDT')
    if rate is None:
        return None
    
    if abs(rate) > 0.1:  # 超过0.1%预警
        return {
            'rate': rate,
            'action': 'long' if rate < 0 else 'short'
        }
    return None

# ========== 功能6: 情绪分析 ==========
def sentiment_analysis(c, price_data):
    """简单情绪分析"""
    if not CONFIG.get('enable_sentiment', True):
        return None
    
    d = get_24hr(f'{c}USDT')
    if not d:
        return None
    
    klines = price_data.get(c, [])
    if len(klines) < 100:
        return None
    
    closes = [k['close'] for k in klines[-100:]]
    
    # 短期vs长期趋势
    sma_20 = np.mean(closes[-20:])
    sma_50 = np.mean(closes[-50:])
    
    if d['price'] > sma_20 and sma_20 > sma_50:
        sentiment = 'BULLISH'
    elif d['price'] < sma_20 and sma_20 < sma_50:
        sentiment = 'BEARISH'
    else:
        sentiment = 'NEUTRAL'
    
    return {
        'sentiment': sentiment,
        'price_vs_sma20': (d['price'] - sma_20) / sma_20 * 100,
        'chg_24h': d['chg']
    }

# ========== 功能7: 相关性分析 ==========
def correlation_analysis(c, price_data):
    """币种相关性分析,避免过度集中"""
    if not CONFIG.get('enable_correlation', True):
        return {}
    
    correlations = {}
    base_closes = [k['close'] for k in price_data.get(c, [])[-50:]]
    
    for other in COINS:
        if other == c or other not in price_data:
            continue
        other_closes = [k['close'] for k in price_data[other][-50:]]
        
        if len(base_closes) == len(other_closes) and len(base_closes) > 10:
            corr = np.corrcoef(base_closes, other_closes)[0, 1]
            correlations[other] = corr
    
    return correlations

# ========== 综合信号评估 ==========
def comprehensive_signal(c, price_data):
    """综合所有指标计算最终信号"""
    klines = price_data.get(c, [])
    if len(klines) < 50:
        return None
    
    d = get_24hr(f'{c}USDT')
    if not d:
        return None
    
    closes = [k['close'] for k in klines]
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]
    
    # 基础指标
    rsi = get_rsi(closes, 7)
    bb_pos = bollinger_pos(d['price'], highs, lows, 20)
    macd = get_macd(closes)
    
    # 决策评分
    decision = 0
    decision += 0.30 * (50 - min(rsi, 50)) / 50
    decision += 0.25 * (100 - bb_pos) / 100
    decision += 0.20 * min(macd / (d['price'] * 0.005), 1)
    
    # 多时间周期
    tf_score = multi_timeframe_confirm(c, price_data)
    
    # 插针检测
    spike = detect_spike(c, price_data)
    
    # 波动率
    vol_alert = volatility_alert(c, price_data)
    
    # 情绪
    sentiment = sentiment_analysis(c, price_data)
    
    # 资金费率
    funding = funding_alert(c)
    
    # 相关性
    correlations = correlation_analysis(c, price_data)
    
    # ========== 最终信号 ==========
    score = 0
    signals = []
    
    # 基础信号
    if rsi < CONFIG['rsi_buy'] and bb_pos < CONFIG['bb_buy']:
        score += 30
        signals.append(f"RSI:{rsi:.0f} BB:{bb_pos:.0f}%")
    
    if decision > CONFIG['decision_threshold']:
        score += 10
        signals.append("决策确认")
    
    # 多时间周期加成
    if tf_score > 0.5:
        score += 20
        signals.append("多周期看涨")
    elif tf_score < -0.5:
        score -= 20
        signals.append("多周期看跌")
    
    # 插针信号
    if spike:
        if spike['action'] == 'long':
            score += 15 * min(spike['strength'] / 3, 1)
            signals.append(f"下插针捕捉({spike['strength']:.1f}x)")
        else:
            score -= 15 * min(spike['strength'] / 3, 1)
            signals.append(f"上插针({spike['strength']:.1f}x)")
    
    # 波动率信号
    if vol_alert:
        if vol_alert['ratio'] > 3:
            score -= 10  # 高波动降低信号强度
            signals.append("高波动预警")
    
    # 情绪信号
    if sentiment:
        if sentiment['sentiment'] == 'BULLISH':
            score += 10
            signals.append("情绪看涨")
        elif sentiment['sentiment'] == 'BEARISH':
            score -= 10
            signals.append("情绪看跌")
    
    return {
        'coin': c,
        'price': d['price'],
        'chg': d['chg'],
        'rsi': rsi,
        'bb_pos': bb_pos,
        'score': score,
        'decision': decision,
        'tf_score': tf_score,
        'spike': spike,
        'vol_alert': vol_alert,
        'sentiment': sentiment,
        'funding': funding,
        'correlations': correlations,
        'signals': signals
    }

# ========== 模拟交易 ==========
def simulate_v16(initial_capital, price_data, cfg):
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 100]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    entry_prices = {c: 0 for c in valid_coins}
    short_qtys = {c: 0 for c in valid_coins}
    short_entries = {c: 0 for c in valid_coins}
    trades = []
    equity_curve = [initial_capital]
    
    leverage = cfg.get('leverage', 3)
    position_ratio = cfg.get('position', 0.35)
    
    decisions = {'long':0,'short':0,'sell':0,'cover':0,'spike_catch':0}
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        # 获取所有信号
        signals = {}
        for c in valid_coins:
            sig = comprehensive_signal(c, price_data)
            if sig:
                signals[c] = sig
        
        for c in valid_coins:
            if c not in signals: continue
            s = signals[c]
            d = day_data[c]
            
            # ========== 插针捕捉优先 ==========
            if s['spike'] and cfg.get('enable_spike_catch', True):
                if s['spike']['action'] == 'long' and capital > cfg.get('min_notional', 10) and positions[c] == 0:
                    # 下插针,买入
                    invest = capital * position_ratio * leverage * 1.5  # 插针加码
                    qty = invest / d['close']
                    capital -= invest * 0.001
                    positions[c] = qty
                    entry_prices[c] = d['close']
                    trades.append({'type':'LONG_OPEN','coin':c,'reason':'spike_catch','price':d['close']})
                    decisions['spike_catch'] += 1
                    decisions['long'] += 1
                    continue
                elif s['spike']['action'] == 'short' and capital > 20 and short_qtys[c] == 0:
                    qty = (capital * position_ratio * leverage * 1.5) / d['close']
                    capital -= qty * d['close'] * 0.001
                    short_qtys[c] = qty
                    short_entries[c] = d['close']
                    trades.append({'type':'SHORT_OPEN','coin':c,'reason':'spike_catch','price':d['close']})
                    decisions['spike_catch'] += 1
                    decisions['short'] += 1
                    continue
            
            # ========== 标准G12信号 ==========
            # 做多
            buy_signal = (s['rsi'] < cfg.get('rsi_buy', 43) and s['bb_pos'] < cfg.get('bb_buy', 25))
            buy_signal = buy_signal and s['decision'] > cfg.get('decision_threshold', 0.70)
            
            if buy_signal and capital > cfg.get('min_notional', 10) and positions[c] == 0 and short_qtys[c] == 0:
                invest = capital * position_ratio * leverage
                qty = invest / d['close']
                capital -= invest * 0.001
                positions[c] = qty
                entry_prices[c] = d['close']
                trades.append({'type':'LONG_OPEN','coin':c,'reason':'g12_signal','price':d['close']})
                decisions['long'] += 1
            
            # 平多
            if positions[c] > 0:
                pnl_ratio = (d['close'] - entry_prices[c]) / entry_prices[c] * leverage
                
                # 动态止盈
                tp = dynamic_take_profit(c, price_data, entry_prices[c], d['close'], 'long')
                
                sell = (s['rsi'] > cfg.get('rsi_sell', 53) and s['bb_pos'] > cfg.get('bb_sell', 75))
                sell = sell or pnl_ratio >= tp
                sell = sell or pnl_ratio <= -cfg.get('stop_loss', 0.035)
                
                # 高波动预警,缩小止损
                if s['vol_alert'] and pnl_ratio < 0:
                    sell = sell or pnl_ratio <= -cfg.get('stop_loss', 0.035) * 0.7
                
                if sell:
                    pnl = (d['close'] - entry_prices[c]) * positions[c] * leverage
                    capital += pnl - positions[c] * d['close'] * 0.001
                    positions[c] = 0
                    entry_prices[c] = 0
                    trades.append({'type':'LONG_CLOSE','coin':c,'pnl_ratio':pnl_ratio,'reason':'g12_close'})
                    decisions['sell'] += 1
            
            # 做空
            short_signal = (s['rsi'] > cfg.get('short_rsi', 70) and s['bb_pos'] > cfg.get('short_bb', 85))
            
            if short_signal and capital > 20 and short_qtys[c] == 0 and positions[c] == 0:
                qty = (capital * position_ratio * leverage) / d['close']
                capital -= qty * d['close'] * 0.001
                short_qtys[c] = qty
                short_entries[c] = d['close']
                trades.append({'type':'SHORT_OPEN','coin':c,'reason':'g12_signal','price':d['close']})
                decisions['short'] += 1
            
            # 平空
            if short_qtys[c] > 0:
                pnl_ratio = (short_entries[c] - d['close']) / short_entries[c] * leverage
                
                cover = (s['rsi'] < cfg.get('rsi_buy', 43) or s['bb_pos'] < cfg.get('bb_buy', 25))
                cover = cover or pnl_ratio >= cfg.get('take_profit', 0.08)
                cover = cover or pnl_ratio <= -cfg.get('stop_loss', 0.035)
                
                if cover:
                    pnl = (short_entries[c] - d['close']) * short_qtys[c] * leverage
                    capital += pnl - short_qtys[c] * d['close'] * 0.001
                    short_qtys[c] = 0
                    short_entries[c] = 0
                    trades.append({'type':'SHORT_CLOSE','coin':c,'pnl_ratio':pnl_ratio,'reason':'g12_close'})
                    decisions['cover'] += 1
        
        # 权益记录
        day_value = capital
        for c in valid_coins:
            day_value += positions[c] * day_data[c]['close']
            day_value += short_qtys[c] * (short_entries[c] - day_data[c]['close'])
        equity_curve.append(day_value)
    
    # 统计
    final_value = capital
    for c in valid_coins:
        final_value += positions[c] * price_data[c][-1]['close']
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    closed = [t for t in trades if t['type'] in ['LONG_CLOSE','SHORT_CLOSE']]
    wins = sum(1 for t in closed if t.get('pnl_ratio', 0) > 0)
    win_rate = wins / len(closed) * 100 if closed else 0
    
    peak = initial_capital
    max_dd = 0
    for v in equity_curve:
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak * 100)
    
    return {
        'return': total_return,
        'win_rate': win_rate,
        'trades': len(trades),
        'wins': wins,
        'losses': len(closed) - wins,
        'decisions': decisions,
        'max_drawdown': max_dd,
        'equity_curve': equity_curve[-30:]
    }

# ========== 极限测试 ==========
def stress_test(initial_capital, price_data, cfg):
    """极限测试: 高波动/单边行情/突发情况"""
    print("\n" + "="*70)
    print("【极限测试】")
    print("="*70)
    
    results = {}
    
    # 测试1: 模拟2020年3月式暴跌 (30天内跌60%)
    print("\n📉 测试1: 模拟极端下跌 (-60%)")
    stress_data = {}
    for c in COINS:
        if c in price_data and len(price_data[c]) > 100:
            klines = price_data[c][-200:]
            # 模拟最后30天跌60%
            for i in range(30):
                idx = len(klines) - 30 + i
                if idx >= 0 and idx < len(klines):
                    klines[idx]['close'] *= (1 - 0.03 * i)  # 每天跌3%
            stress_data[c] = klines
    
    stats = simulate_v16(initial_capital, stress_data, cfg)
    results['extreme_drop'] = stats['return']
    print(f"  极端下跌收益: {stats['return']:+.2f}%")
    
    # 测试2: 模拟2021年5月式反弹 (+50%)
    print("\n📈 测试2: 模拟极端反弹 (+50%)")
    stress_data = {}
    for c in COINS:
        if c in price_data and len(price_data[c]) > 100:
            klines = price_data[c][-200:]
            for i in range(30):
                idx = len(klines) - 30 + i
                if idx >= 0 and idx < len(klines):
                    klines[idx]['close'] *= (1 + 0.025 * i)  # 每天涨2.5%
            stress_data[c] = klines
    
    stats = simulate_v16(initial_capital, stress_data, cfg)
    results['extreme_rise'] = stats['return']
    print(f"  极端反弹收益: {stats['return']:+.2f}%")
    
    # 测试3: 高波动震荡
    print("\n⚡ 测试3: 高波动震荡")
    stress_data = {}
    for c in COINS:
        if c in price_data and len(price_data[c]) > 100:
            klines = price_data[c][-200:]
            for i in range(100):
                idx = len(klines) - 100 + i
                if idx >= 0 and idx < len(klines):
                    # 大幅震荡
                    klines[idx]['close'] *= (1 + np.random.uniform(-0.1, 0.1))
            stress_data[c] = klines
    
    stats = simulate_v16(initial_capital, stress_data, cfg)
    results['high_volatility'] = stats['return']
    print(f"  高波动震荡收益: {stats['return']:+.2f}%")
    
    # 测试4: 长时间横盘
    print("\n➡️ 测试4: 长时间横盘 (无趋势)")
    stress_data = {}
    for c in COINS:
        if c in price_data and len(price_data[c]) > 100:
            klines = price_data[c][-200:]
            base = klines[-100]['close']
            for i in range(100):
                idx = len(klines) - 100 + i
                if idx >= 0 and idx < len(klines):
                    # 原地踏步
                    klines[idx]['close'] = base * (1 + np.random.uniform(-0.02, 0.02))
            stress_data[c] = klines
    
    stats = simulate_v16(initial_capital, stress_data, cfg)
    results['sideways'] = stats['return']
    print(f"  横盘收益: {stats['return']:+.2f}%")
    
    return results

# ========== 主程序 ==========
def main():
    print("="*70)
    print("Hermes G12 v16 - 完整版 (集成Hermes/GO2SE全部功能)")
    print("="*70)
    
    print("\n📥 获取数据...")
    price_data = {}
    for c in COINS:
        data = get_klines(f'{c}USDT', '1h', 720)
        if data and len(data) > 100:
            price_data[c] = data
            print(f"  {c}: {len(data)}条")
        time.sleep(0.1)
    
    if len(price_data) < 3:
        print("❌ 数据不足")
        return
    
    # ========== 功能展示 ==========
    print("\n" + "="*70)
    print("【新增功能检测】")
    print("="*70)
    
    for c in COINS[:3]:
        if c not in price_data: continue
        
        print(f"\n📊 {c}:")
        
        # 多时间周期
        tf = multi_timeframe_confirm(c, price_data)
        print(f"  多周期确认: {tf:+.2f}")
        
        # 插针检测
        spike = detect_spike(c, price_data)
        if spike:
            print(f"  插针捕捉: {spike['type']} {spike['strength']:.1f}x")
        else:
            print(f"  插针捕捉: 无")
        
        # 波动率
        vol = volatility_alert(c, price_data)
        if vol:
            print(f"  波动率预警: {vol['ratio']:.1f}x (当前{vol['current']:.2f}% vs 历史{vol['historical']:.2f}%)")
        else:
            print(f"  波动率: 正常")
        
        # 情绪
        sent = sentiment_analysis(c, price_data)
        if sent:
            print(f"  情绪: {sent['sentiment']} (价格vsSMA20: {sent['price_vs_sma20']:+.2f}%)")
        
        # 资金费率
        fund = funding_alert(c)
        if fund:
            print(f"  资金费率: {fund['rate']:+.4f}%")
        else:
            print(f"  资金费率: 正常")
        
        time.sleep(0.1)
    
    # ========== 30天回测 ==========
    print("\n" + "="*70)
    print("【30天回测】")
    print("="*70)
    
    stats = simulate_v16(1000, price_data, CONFIG)
    
    print(f"\n📊 核心指标")
    print(f"  总收益: {stats['return']:>+.2f}%")
    print(f"  胜率: {stats['win_rate']:.1f}%")
    print(f"  交易次数: {stats['trades']}笔")
    print(f"  盈利: {stats['wins']}笔 | 亏损: {stats['losses']}笔")
    print(f"  最大回撤: {stats['max_drawdown']:.1f}%")
    
    print(f"\n📈 决策统计")
    print(f"  做多: {stats['decisions']['long']}次")
    print(f"  做空: {stats['decisions']['short']}次")
    print(f"  插针捕捉: {stats['decisions']['spike_catch']}次")
    
    # ========== 极限测试 ==========
    stress_results = stress_test(1000, price_data, CONFIG)
    
    print("\n" + "="*70)
    print("【极限测试汇总】")
    print("="*70)
    print(f"\n{'场景':20} {'收益':15}")
    print("-"*40)
    print(f"{'极端下跌(-60%)':20} {stress_results['extreme_drop']:>+14.2f}%")
    print(f"{'极端反弹(+50%)':20} {stress_results['extreme_rise']:>+14.2f}%")
    print(f"{'高波动震荡':20} {stress_results['high_volatility']:>+14.2f}%")
    print(f"{'长时间横盘':20} {stress_results['sideways']:>+14.2f}%")
    
    # 保存
    with open('/tmp/g12_v16_results.json', 'w') as f:
        json.dump({
            'config': CONFIG,
            'backtest': stats,
            'stress_test': stress_results,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2, default=str)
    
    print("\n" + "="*70)
    print("✅ G12 v16 完整版测试完成!")
    print("="*70)

if __name__ == '__main__':
    main()
