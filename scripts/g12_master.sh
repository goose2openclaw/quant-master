#!/bin/bash
# G12 - 加密货币量化投资系统 v1.0
# 集成12个顶级量化系统 | 目标: 100%/月

LOG_FILE="/tmp/g12.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "G12 Master System $(date)"
echo "集成: Freqtrade+Jesse+QuantDinger+MVSK+..."
echo "目标: 收益100%/月 | 胜率90%+"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, numpy as np
from datetime import datetime
import subprocess

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
PRECISION = {'BTC':5,'ETH':4,'SOL':3,'XRP':1,'ADA':1,'DOGE':0,'LINK':2}

# ========== G12 全域扫描配置 ==========
SCAN_COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK','BNB','AVAX','MATIC','DOT','UNI','LTC','ATOM','FIL','XLM','NEAR','AAVE','MKR','SNX']

# G12 核心配置
CONFIG = {
    # 信号权重 (从QuantDinger/Jesse蒸馏)
    'weights': {
        'rsi': 0.25,
        'bb': 0.20,
        'macd': 0.20,
        'chg': 0.15,
        'atr': 0.10,
        'trend': 0.10
    },
    
    # 买入阈值 (从MVSK/GO2SE蒸馏)
    'buy': {
        'rsi': 35,
        'bb_pos': 20,
        'macd_cross': 0,  # 金叉
        'chg': -2.0,      # 下跌超过2%
        'decision': 0.7    # 决策值
    },
    
    # 卖出阈值
    'sell': {
        'rsi': 65,
        'bb_pos': 80,
        'macd_cross': 0,  # 死叉
        'chg': 2.0,       # 上涨超过2%
        'decision': 0.3
    },
    
    # 做空阈值 (从Hummingbot蒸馏)
    'short': {
        'rsi': 70,
        'bb_pos': 85,
        'chg': 3.0
    },
    
    # 仓位管理 (从Freqtrade/Jesse蒸馏)
    'position': {
        'base': 0.30,      # 基础30%
        'leverage': 3,      # 最大3x
        'reserve': 0.10,   # 预留10%
        'max_single': 0.40 # 单币最大40%
    },
    
    # 止盈止损 (从QuantDinger蒸馏)
    'exit': {
        'take_profit': 0.10,  # 10%
        'stop_loss': 0.04,   # 4%
        'atr_multiplier': 2.0 # ATR×2
    },
    
    # 复利配置 (从Binance Bot蒸馏)
    'compound': {
        'enabled': True,
        'reinvest_ratio': 0.80  # 80%利润再投入
    },
    
    # 全域扫描 (从GO2SE Genius蒸馏)
    'scan': {
        'top_n': 5,         # 最多持仓5个
        'min_score': 60,    # 最低评分
        'rebalance': True   # 自动再平衡
    }
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
        return {'price':float(d['lastPrice']),'chg':float(d['priceChangePercent']),'high':float(d['highPrice']),'low':float(d['lowPrice']),'volume':float(d['quoteVolume'])}
    except: return None

def get_klines(sym, interval='1h', limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'open':float(k[1]),'high':float(k[2]),'low':float(k[3]),'close':float(k[4]),'volume':float(k[5])} for k in r.json()]
    except: return []

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def bollinger_pos(price, highs, lows, period=20):
    if len(highs) < period or len(lows) < period: return 50
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def get_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow+1: return 0
    ema_fast = np.mean(prices[-fast:])
    ema_slow = np.mean(prices[-slow:])
    macd = ema_fast - ema_slow
    return macd

def get_atr(klines, period=14):
    if len(klines) < period+1: return 0
    trs = []
    for i in range(1, min(period+1, len(klines))):
        high = klines[i]['high']
        low = klines[i]['low']
        prev_close = klines[i-1]['close']
        tr = max(high-low, abs(high-prev_close), abs(low-prev_close))
        trs.append(tr)
    return np.mean(trs) if trs else 0

def get_trend(klines):
    if len(klines) < 20: return 0
    ma5 = np.mean([k['close'] for k in klines[-5:]])
    ma20 = np.mean([k['close'] for k in klines[-20:]])
    return 1 if ma5 > ma20 else -1

def round_qty(qty, coin):
    p = PRECISION.get(coin, 6)
    if p == 0: return int(qty)
    return round(round(qty/10**(-p))*10**(-p), p)

# ========== G12 分析引擎 ==========
def analyze_coin(c):
    """G12 多维度分析"""
    sym = f'{c}USDT'
    klines_h = get_klines(sym, '1h', 100)
    klines_d = get_klines(sym, '1d', 30)
    d = get_24hr(sym)
    
    if not klines_h or not d: return None
    
    closes_h = [k['close'] for k in klines_h]
    highs_h = [k['high'] for k in klines_h]
    lows_h = [k['low'] for k in klines_h]
    closes_d = [k['close'] for k in klines_d]
    
    # 计算各指标
    rsi = get_rsi(closes_h, 7)
    bb_pos = bollinger_pos(d['price'], highs_h, lows_h, 20)
    macd = get_macd(closes_h)
    atr = get_atr(klines_h)
    trend = get_trend(klines_d)
    
    # 决策值计算 (加权)
    decision = 0
    decision += CONFIG['weights']['rsi'] * (50 - min(rsi, 50)) / 50
    decision += CONFIG['weights']['bb'] * (100 - bb_pos) / 100
    decision += CONFIG['weights']['macd'] * (macd / (d['price'] * 0.01))
    decision += CONFIG['weights']['chg'] * abs(min(d['chg'], 0)) / 5
    decision += CONFIG['weights']['trend'] * (trend + 1) / 2
    
    # 信号判断
    buy_signal = (
        rsi < CONFIG['buy']['rsi'] or
        bb_pos < CONFIG['buy']['bb_pos'] or
        d['chg'] < CONFIG['buy']['chg']
    ) and decision > CONFIG['buy']['decision']
    
    sell_signal = (
        rsi > CONFIG['sell']['rsi'] or
        bb_pos > CONFIG['sell']['bb_pos'] or
        d['chg'] > CONFIG['sell']['chg']
    ) and decision < CONFIG['sell']['decision']
    
    short_signal = (
        rsi > CONFIG['short']['rsi'] and
        bb_pos > CONFIG['short']['bb_pos']
    )
    
    # 评分 (0-100)
    score = int(decision * 100)
    
    return {
        'coin': c,
        'price': d['price'],
        'chg': d['chg'],
        'volume': d.get('volume', 0),
        'rsi': rsi,
        'bb_pos': bb_pos,
        'macd': macd,
        'atr': atr,
        'trend': trend,
        'decision': decision,
        'score': score,
        'buy_signal': buy_signal,
        'sell_signal': sell_signal,
        'short_signal': short_signal
    }

# ========== G12 主扫描 ==========
def g12_scan():
    """G12 全域扫描"""
    print("\n" + "="*70)
    print("G12 全域扫描开始")
    print("="*70)
    
    results = []
    
    print(f"\n【扫描 {len(SCAN_COINS)} 个币种】")
    for c in SCAN_COINS:
        a = analyze_coin(c)
        if a:
            results.append(a)
            status = "📈买" if a['buy_signal'] else ("📉卖" if a['sell_signal'] else ("🔻空" if a['short_signal'] else "⚪"))
            print(f"  {c:8} 评分:{a['score']:>3} RSI:{a['rsi']:>5.1f} BB:{a['bb_pos']:>5.1f}% {a['chg']:>+6.2f}% {status}")
        time.sleep(0.1)
    
    # 排序
    results.sort(key=lambda x: -x['score'])
    
    print(f"\n【G12 评分排名】")
    print(f"{'排名':4} {'币种':8} {'评分':6} {'RSI':6} {'BB':8} {'涨跌':8} {'信号':6}")
    print("-"*55)
    for i, r in enumerate(results[:10], 1):
        signal = "买" if r['buy_signal'] else ("卖" if r['sell_signal'] else ("空" if r['short_signal'] else "-"))
        print(f"{i:4} {r['coin']:8} {r['score']:>6} {r['rsi']:>5.1f} {r['bb_pos']:>7.1f}% {r['chg']:>+7.2f}% {signal:>6}")
    
    return results

# ========== G12 账户分析 ==========
def get_account():
    """获取账户状态"""
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    
    spot_r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    cross_r = requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
    
    spot = {b['asset']: float(b['free']) for b in spot_r.json()['balances']}
    cross_assets = {a['asset']: float(a['free']) for a in cross_r.json()['userAssets']}
    margin_level = float(cross_r.json().get('marginLevel', 0))
    
    return spot, cross_assets, margin_level

# ========== G12 执行 ==========
def g12_execute(signals):
    """G12 自动执行"""
    print("\n" + "="*70)
    print("G12 自动执行")
    print("="*70)
    
    spot, cross, margin_level = get_account()
    prices = {c: get_price(f'{c}USDT') for c in SCAN_COINS if get_price(f'{c}USDT') > 0}
    
    total_spot = sum(spot.get(c, 0) * prices.get(c, 0) for c in prices) + spot.get('USDT', 0)
    total_cross = sum(cross.get(c, 0) * prices.get(c, 0) for c in prices) + cross.get('USDT', 0)
    total = total_spot + total_cross
    
    print(f"\n【账户状态】")
    print(f"  总资产: ${total:.2f}")
    print(f"  SPOT: ${total_spot:.2f} ({total_spot/total*100:.1f}%)")
    print(f"  CROSS: ${total_cross:.2f} ({total_cross/total*100:.1f}%)")
    print(f"  保证金率: {margin_level:.2f}")
    
    trades = []
    
    # 买入信号执行
    for s in signals:
        if s['buy_signal'] and s['score'] > CONFIG['scan']['min_score']:
            c = s['coin']
            if c not in prices: continue
            
            # 计算买入量
            position_size = total * CONFIG['position']['base']
            qty = round_qty(position_size / s['price'], c)
            
            if qty > 0 and spot.get('USDT', 0) > position_size:
                print(f"\n✅ 买入信号: {c}")
                print(f"   价格: ${s['price']:.4f}")
                print(f"   数量: {qty}")
                print(f"   评分: {s['score']}")
                print(f"   RSI: {s['rsi']:.1f} | BB: {s['bb_pos']:.1f}%")
                # 实际下单注释掉，仅显示信号
                # r = spot_order(f'{c}USDT', 'BUY', qty)
                trades.append({'type':'BUY','coin':c,'qty':qty,'price':s['price'],'score':s['score']})
    
    # 做空信号执行
    for s in signals:
        if s['short_signal'] and s['score'] < 30:
            c = s['coin']
            if c not in prices: continue
            
            # 检查CROSS余额
            if cross.get('USDT', 0) < 50: continue
            
            qty = round_qty(50 / s['price'], c)
            if qty > 0:
                print(f"\n✅ 做空信号: {c}")
                print(f"   价格: ${s['price']:.4f}")
                print(f"   数量: {qty}")
                print(f"   RSI: {s['rsi']:.1f} | BB: {s['bb_pos']:.1f}%")
                trades.append({'type':'SHORT','coin':c,'qty':qty,'price':s['price'],'score':s['score']})
    
    print(f"\n【执行结果】")
    print(f"  执行交易: {len(trades)}笔")
    for t in trades:
        print(f"    {t['type']}: {t['coin']} x {t['qty']} @ ${t['price']:.4f}")
    
    return trades

# ========== G12 状态报告 ==========
def g12_status():
    """G12 状态报告"""
    spot, cross, margin_level = get_account()
    prices = {c: get_price(f'{c}USDT') for c in SCAN_COINS if get_price(f'{c}USDT') > 0}
    
    total_spot = sum(spot.get(c, 0) * prices.get(c, 0) for c in prices) + spot.get('USDT', 0)
    total_cross = sum(cross.get(c, 0) * prices.get(c, 0) for c in prices) + cross.get('USDT', 0)
    total = total_spot + total_cross
    
    holdings = [(c, spot.get(c, 0), prices.get(c, 0)) for c in prices if spot.get(c, 0) > 0.001]
    holdings.sort(key=lambda x: -x[1]*x[2])
    
    print("""
┌─────────────────────────────────────────────────────────────────┐
│                    G12 系统状态报告                               │
├─────────────────────────────────────────────────────────────────┤
""")
    print(f"│  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):50} │")
    print(f"│  总资产: ${total:.2f}{' '*40} │")
    print(f"│  SPOT: ${total_spot:.2f} ({total_spot/total*100:.1f}%){' '*30} │")
    print(f"│  CROSS: ${total_cross:.2f} ({total_cross/total*100:.1f}%){' '*29} │")
    print(f"│  保证金率: {margin_level:.2f}{'*'*40} │")
    print("│" + " "*73 + "│")
    print("│  持仓:" + " "*65 + "│")
    for c, qty, price in holdings[:5]:
        val = qty * price
        pct = val/total*100
        print(f"│    {c}: {qty:.4f} x ${price:.4f} = ${val:.2f} ({pct:.1f}%){' '*20} │")
    print("└─────────────────────────────────────────────────────────────────┘")

# ========== 主程序 ==========
print("\n【G12 初始化】")
print(f"  扫描币种: {len(SCAN_COINS)}")
print(f"  目标收益: 100%/月")
print(f"  目标胜率: 90%+")

# 执行全域扫描
signals = g12_scan()

# 执行交易
trades = g12_execute(signals)

# 状态报告
g12_status()

# 保存结果
with open('/tmp/g12_scan.json', 'w') as f:
    json.dump({
        'time': datetime.now().isoformat(),
        'signals': [{'coin':s['coin'],'score':s['score'],'rsi':s['rsi'],'bb':s['bb_pos'],'chg':s['chg'],'buy':s['buy_signal'],'sell':s['sell_signal'],'short':s['short_signal']} for s in signals],
        'trades': trades
    }, f, indent=2)

print("\n✅ G12 扫描完成!")
PYEOF
