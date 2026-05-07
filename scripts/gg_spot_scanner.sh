#!/bin/bash
# 现货行情机会筛选评估 - 条件退出
LOG_FILE="/tmp/gg_spot_scanner.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "现货行情机会筛选 $(date)"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# 机会筛选条件
CONDITIONS = {
    'min_volume': 10000000,      # 最小成交量10M
    'min_change': 2.0,           # 最小涨跌幅2%
    'rsi_oversold': 35,         # RSI超卖
    'rsi_overbought': 70,        # RSI超买
    'bollinger_position_buy': 20,  # 布林带位置买入
    'bollinger_position_sell': 80, # 布林带位置卖出
    'ma_cross_above': True,       # MA金叉
    'volume_spike': 2.0,          # 成交量放大倍数
}

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
            'price': float(d['lastPrice']),
            'chg': float(d['priceChangePercent']),
            'high': float(d['highPrice']),
            'low': float(d['lowPrice']),
            'volume': float(d['quoteVolume']),
            'priceChange': float(d['priceChange'])
        }
    except: return None

def get_klines(sym, interval='1h', limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{
            'open': float(k[1]), 'high': float(k[2]),
            'low': float(k[3]), 'close': float(k[4]),
            'volume': float(k[5])
        } for k in r.json()]
    except: return []

def get_all_symbols():
    try:
        r = requests.get('https://api.binance.com/api/v3/exchangeInfo', proxies=PROXIES, timeout=30)
        return [s['symbol'] for s in r.json()['symbols'] 
                if s['symbol'].endswith('USDT') and s['status'] == 'TRADING']
    except: return []

def bollinger_pos(price, high, low):
    return (price-low)/(high-low)*100 if high>low else 50

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def get_ma(prices, period=20):
    if len(prices) < period: return prices[-1] if prices else 0
    return np.mean(prices[-period:])

def evaluate_opportunity(symbol, d, klines):
    """评估机会"""
    price = d['price']
    chg = d['chg']
    high = d['high']
    low = d['low']
    volume = d['volume']
    
    # 布林带位置
    bb_pos = bollinger_pos(price, high, low)
    
    # RSI
    prices = [k['close'] for k in klines] if klines else [price]
    rsi = get_rsi(prices)
    
    # MA
    ma20 = get_ma(prices, 20)
    ma50 = get_ma(prices, 50)
    ma_cross = 'gold' if ma20 > ma50 else 'death' if ma20 < ma50 else 'none'
    
    # 成交量对比
    if len(klines) >= 2:
        avg_volume = np.mean([k['volume'] for k in klines[-20:]])
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
    else:
        volume_ratio = 1
    
    # 评分
    score = 0
    action = None
    reason = []
    
    # 买入信号
    buy_signals = 0
    if bb_pos < CONDITIONS['bollinger_position_buy']:
        score += 30
        buy_signals += 1
        reason.append(f'布林位置{bb_pos:.0f}%<{CONDITIONS["bollinger_position_buy"]}%')
    if rsi < CONDITIONS['rsi_oversold']:
        score += 25
        buy_signals += 1
        reason.append(f'RSI={rsi:.0f}<{CONDITIONS["rsi_oversold"]}')
    if chg < -CONDITIONS['min_change']:
        score += 20
        buy_signals += 1
        reason.append(f'跌幅{chg:.1f}%<-{CONDITIONS["min_change"]}%')
    if volume_ratio > CONDITIONS['volume_spike']:
        score += 15
        buy_signals += 1
        reason.append(f'量比{volume_ratio:.1f}x>{CONDITIONS["volume_spike"]}x')
    if ma_cross == 'gold':
        score += 10
        buy_signals += 1
        reason.append('MA金叉')
    
    if buy_signals >= 2:
        action = 'BUY'
    
    # 卖出信号
    sell_signals = 0
    if bb_pos > CONDITIONS['bollinger_position_sell']:
        score += 30
        sell_signals += 1
        reason.append(f'布林位置{bb_pos:.0f}%>{CONDITIONS["bollinger_position_sell"]}%')
    if rsi > CONDITIONS['rsi_overbought']:
        score += 25
        sell_signals += 1
        reason.append(f'RSI={rsi:.0f}>{CONDITIONS["rsi_overbought"]}')
    if chg > CONDITIONS['min_change']:
        score += 20
        sell_signals += 1
        reason.append(f'涨幅{chg:.1f}%>{CONDITIONS["min_change"]}%')
    if ma_cross == 'death':
        score += 10
        sell_signals += 1
        reason.append('MA死叉')
    
    if sell_signals >= 2:
        action = 'SELL'
    
    return {
        'symbol': symbol,
        'action': action,
        'score': score,
        'price': price,
        'chg': chg,
        'bb_pos': bb_pos,
        'rsi': rsi,
        'ma_cross': ma_cross,
        'volume_ratio': volume_ratio,
        'volume': volume,
        'reason': reason,
        'signals': buy_signals if action=='BUY' else sell_signals
    }

def conditional_exit(entry_price, current_price, entry_time, conditions):
    """条件退出评估"""
    pnl_pct = (current_price - entry_price) / entry_price * 100
    
    exits = []
    
    # 止盈
    if pnl_pct >= conditions.get('take_profit', 8):
        exits.append({'type': 'TAKE_PROFIT', 'pnl': pnl_pct, 'reason': f'达到止盈{conditions["take_profit"]}%'})
    
    # 止损
    if pnl_pct <= -conditions.get('stop_loss', 2):
        exits.append({'type': 'STOP_LOSS', 'pnl': pnl_pct, 'reason': f'达到止损{conditions["stop_loss"]}%'})
    
    # RSI超买退出
    if conditions.get('rsi_exit', 75) and conditions.get('current_rsi', 50) > conditions['rsi_exit']:
        exits.append({'type': 'RSI_EXIT', 'pnl': pnl_pct, 'reason': f'RSI超买{conditions["current_rsi"]:.0f}'})
    
    # 布林上轨退出
    if conditions.get('bb_exit', 85) and conditions.get('bb_pos', 50) > conditions['bb_exit']:
        exits.append({'type': 'BB_EXIT', 'pnl': pnl_pct, 'reason': f'布林位置{conditions["bb_pos"]:.0f}%超买'})
    
    # 时间退出
    if conditions.get('max_hours', 24):
        hours_held = (time.time() - entry_time) / 3600
        if hours_held >= conditions['max_hours']:
            exits.append({'type': 'TIME_EXIT', 'pnl': pnl_pct, 'reason': f'持仓{hours_held:.0f}h超时'})
    
    # 最佳退出
    if exits:
        exits.sort(key=lambda x: x['pnl'], reverse=True)
        return exits[0]
    
    return None

# === MAIN ===
print("\n【1. 获取全市场现货列表】")
symbols = get_all_symbols()
print(f"  总USDT交易对: {len(symbols)}")

# 扫描前200个高交易量币种
scan_symbols = symbols[:200]
print(f"  扫描: {len(scan_symbols)}个")

print("\n【2. 行情扫描评估】")
opportunities = []

for i, symbol in enumerate(scan_symbols):
    d = get_24hr(symbol)
    if not d: continue
    
    # 基础过滤
    if d['volume'] < CONDITIONS['min_volume']:
        continue
    if abs(d['chg']) < CONDITIONS['min_change']:
        continue
    
    # 获取K线
    klines = get_klines(symbol, '1h', 100)
    
    # 评估
    eval_result = evaluate_opportunity(symbol, d, klines)
    
    if eval_result['action']:
        opportunities.append(eval_result)
        emoji = '📈' if eval_result['action'] == 'BUY' else '📉'
        print(f"  {emoji} {symbol:12} {eval_result['action']:4} 评分:{eval_result['score']:3.0f} {d['chg']:>+6.2f}% RSI:{eval_result['rsi']:.0f} 位置:{eval_result['bb_pos']:.0f}%")
    
    if (i+1) % 50 == 0:
        print(f"  进度: {i+1}/{len(scan_symbols)}")
    
    time.sleep(0.02)

opportunities.sort(key=lambda x: -x['score'])

print(f"\n【3. 机会汇总】")
print(f"  发现机会: {len(opportunities)}个")

if opportunities:
    print("\n  Top 10 机会:")
    print(f"  {'币种':12} {'信号':4} {'评分':6} {'价格':12} {'涨跌':8} {'RSI':6} {'位置':6} {'信号数':6}")
    print("  " + "-"*70)
    
    for opp in opportunities[:10]:
        print(f"  {opp['symbol']:12} {opp['action']:4} {opp['score']:5.0f} ${opp['price']:>10.4f} {opp['chg']:>+7.2f}% {opp['rsi']:5.0f} {opp['bb_pos']:5.0f}% {opp['signals']:5d}")
        if opp['reason']:
            print(f"    原因: {', '.join(opp['reason'][:3])}")

print("\n【4. 条件退出检查】")
# 示例持仓检查
example_positions = [
    {'symbol': 'DOGEUSDT', 'entry': 0.11, 'entry_time': time.time() - 3600 * 6, 'conditions': {'take_profit': 8, 'stop_loss': 2, 'rsi_exit': 75, 'bb_exit': 85, 'max_hours': 24}},
    {'symbol': 'XRPUSDT', 'entry': 1.40, 'entry_time': time.time() - 3600 * 12, 'conditions': {'take_profit': 5, 'stop_loss': 3, 'rsi_exit': 70, 'bb_exit': 80, 'max_hours': 12}},
]

for pos in example_positions:
    current = get_price(pos['symbol'])
    klines = get_klines(pos['symbol'], '1h', 100)
    prices = [k['close'] for k in klines] if klines else [current]
    rsi = get_rsi(prices)
    d = get_24hr(pos['symbol'])
    bb_pos = bollinger_pos(current, d['high'], d['low']) if d else 50
    
    pos['conditions']['current_rsi'] = rsi
    pos['conditions']['bb_pos'] = bb_pos
    
    exit_result = conditional_exit(pos['entry'], current, pos['entry_time'], pos['conditions'])
    
    pnl = (current - pos['entry']) / pos['entry'] * 100
    print(f"  {pos['symbol']}: 进场${pos['entry']:.4f} 当前${current:.4f} {pnl:+.2f}%")
    
    if exit_result:
        print(f"    🚨 退出信号: {exit_result['type']} | {exit_result['reason']} | PnL:{exit_result['pnl']:+.2f}%")
    else:
        print(f"    ✅ 继续持有")

# 保存结果
result_data = {
    'timestamp': datetime.now().isoformat(),
    'opportunities': opportunities[:20],
    'conditions': CONDITIONS
}

with open('/tmp/spot_opportunities.json', 'w') as f:
    json.dump(result_data, f, indent=2)

print(f"\n✅ 扫描完成! 发现{len(opportunities)}个机会")
PYEOF
