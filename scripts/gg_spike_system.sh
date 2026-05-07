#!/bin/bash
# GG 插针全套系统 v1.0
# 功能: 抓获插针 + 做空机制 + 做多机制
# 日期: 2026-05-06

echo "=========================================="
echo "📌 GG 插针全套系统"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# ================== 配置 ==================
SPIKE_THRESHOLD = 0.015  # 1.5% 波动阈值
REVERSAL_CONFIRM = 0.005  # 0.5% 反转确认
STOP_LOSS_PCT = 0.01  # 1% 止损
TAKE_PROFIT_PCT = 0.02  # 2% 止盈
MIN_MARGIN_LEVEL = 3.0  # 最低保证金率
TRADE_QTY = 10  # 每次10 USDT等值

# ================== 工具函数 ==================
def get_margin():
    ts=int(time.time()*1000)
    params='timestamp=%d&recvWindow=5000' % ts
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get('https://api.binance.com/sapi/v1/margin/account?%s&signature=%s' % (params,sig), headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10).json()
    return float(r.get('marginLevel',999))

def get_price(symbol):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines_1m(symbol, limit=60):
    """获取1分钟K线(最近60分钟)"""
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit={limit}', proxies=PROXIES, timeout=10)
        data=r.json()
        return [{
            'high': float(d[2]),
            'low': float(d[3]),
            'close': float(d[4]),
            'vol': float(d[5])
        } for d in data]
    except: return []

def get_order_book(symbol, limit=10):
    """获取订单簿"""
    try:
        r=requests.get(f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}', proxies=PROXIES, timeout=5)
        d=r.json()
        return {
            'bids': [(float(p), float(q)) for p,q in d.get('bids',[])],
            'asks': [(float(p), float(q)) for p,q in d.get('asks',[])]
        }
    except: return {'bids':[], 'asks':[]}

# ================== 插针检测 ==================
def detect_spike(coin):
    """检测插针模式"""
    sym = f"{coin}USDT"
    klines = get_klines_1m(sym, 60)
    if len(klines) < 10: return None
    
    closes = [k['close'] for k in klines]
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]
    
    # 计算布林带
    ma20 = sum(closes[-20:])/20
    std = (sum((c-ma20)**2 for c in closes[-20:])/20)**0.5
    bb_upper = ma20 + 2*std
    bb_lower = ma20 - 2*std
    
    # 检测最近5分钟内的极端波动
    recent_5min = klines[-5:]
    recent_high = max(k['high'] for k in recent_5min)
    recent_low = min(k['low'] for k in recent_5min)
    current_price = closes[-1]
    
    # 插针类型1: 向上插针 (涨破布林上轨)
    if recent_high > bb_upper * 1.01:
        spike_up_pct = (recent_high - bb_upper) / bb_upper
        drop_back = (recent_high - current_price) / recent_high
        return {
            'type': 'SPIKE_UP',
            'spike_pct': spike_up_pct,
            'drop_back': drop_back,
            'spike_high': recent_high,
            'current': current_price,
            'action': 'SHORT',
            'reason': f'向上插针+{spike_up_pct*100:.1f}%，回落中'
        }
    
    # 插针类型2: 向下插针 (跌破布林下轨)
    if recent_low < bb_lower * 0.99:
        spike_down_pct = (bb_lower - recent_low) / bb_lower
        bounce_back = (current_price - recent_low) / recent_low
        return {
            'type': 'SPIKE_DOWN',
            'spike_pct': spike_down_pct,
            'bounce_back': bounce_back,
            'spike_low': recent_low,
            'current': current_price,
            'action': 'LONG',
            'reason': f'向下插针-{spike_down_pct*100:.1f}%，反弹中'
        }
    
    # 检测近期是否有插针历史
    hourly_volatility = [(klines[i]['high'] - klines[i]['low'])/klines[i]['low'] for i in range(len(klines))]
    avg_vol = sum(hourly_volatility)/len(hourly_volatility)
    max_vol = max(hourly_volatility)
    
    if max_vol > avg_vol * 3:
        return {
            'type': 'HIGH_VOLATILITY',
            'vol_ratio': max_vol/avg_vol,
            'current': current_price,
            'action': 'WATCH',
            'reason': f'波动率异常 {max_vol/avg_vol:.1f}x'
        }
    
    return None

# ================== 做空机制 ==================
def execute_short(coin, entry_price, stop_loss, take_profit):
    """
    做空机制:
    1. 确认向上插针
    2. 入场做空 (卖出现货/借币做空)
    3. 止损: 插针高点上方1%
    4. 止盈: 入场价下方2%
    """
    sym = f"{coin}USDT"
    qty = TRADE_QTY / entry_price
    
    print(f"\n{'='*50}")
    print(f"🔴 做空机制启动")
    print(f"{'='*50}")
    print(f"币种: {coin}")
    print(f"入场价: ${entry_price:.4f}")
    print(f"止损价: ${stop_loss:.4f} (+{((stop_loss-entry_price)/entry_price)*100:.1f}%)")
    print(f"止盈价: ${take_profit:.4f} ({((entry_price-take_profit)/entry_price)*100:.1f}%)")
    print(f"数量: {qty:.4f} 个")
    print(f"{'='*50}")
    print(f"逻辑:")
    print(f"1. 向上插针触发空头止损")
    print(f"2. 价格反转回落，开空单")
    print(f"3. 等待价格回归正常")
    print(f"4. 止盈或者止损")
    
    return {
        'action': 'SHORT',
        'coin': coin,
        'entry': entry_price,
        'stop': stop_loss,
        'tp': take_profit,
        'qty': qty
    }

# ================== 做多机制 ==================
def execute_long(coin, entry_price, stop_loss, take_profit):
    """
    做多机制:
    1. 确认向下插针
    2. 入场做多 (买入)
    3. 止损: 插针低点下方1%
    4. 止盈: 入场价上方2%
    """
    sym = f"{coin}USDT"
    qty = TRADE_QTY / entry_price
    
    print(f"\n{'='*50}")
    print(f"🟢 做多机制启动")
    print(f"{'='*50}")
    print(f"币种: {coin}")
    print(f"入场价: ${entry_price:.4f}")
    print(f"止损价: ${stop_loss:.4f} ({((stop_loss-entry_price)/entry_price)*100:.1f}%)")
    print(f"止盈价: ${take_profit:.4f} (+{((take_profit-entry_price)/entry_price)*100:.1f}%)")
    print(f"数量: {qty:.4f} 个")
    print(f"{'='*50}")
    print(f"逻辑:")
    print(f"1. 向下插针触发多头止损")
    print(f"2. 价格反弹确认，买入")
    print(f"3. 等待价格回归正常")
    print(f"4. 止盈或者止损")
    
    return {
        'action': 'LONG',
        'coin': coin,
        'entry': entry_price,
        'stop': stop_loss,
        'tp': take_profit,
        'qty': qty
    }

# ================== 主程序 ==================
print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

ml = get_margin()
print(f"保证金率: {ml:.3f}")

if ml < MIN_MARGIN_LEVEL:
    print(f"⚠️ 保证金率低于{MIN_MARGIN_LEVEL}，暂停所有交易")
    exit()

print(f"\n{'='*50}")
print(f"📊 插针检测扫描")
print(f"{'='*50}")

coins = ['LINK','BTC','ETH','BNB','SOL','XRP','ADA','DOGE','ORDI']
signals = []

for coin in coins:
    result = detect_spike(coin)
    if result:
        print(f"\n{coin}: {result['reason']}")
        print(f"  当前价: ${result['current']:.4f}")
        
        if result['action'] == 'SHORT':
            stop_loss = result['spike_high'] * 1.01
            take_profit = result['current'] * 0.98
            signals.append(('SHORT', result['spike_pct'], execute_short(coin, result['current'], stop_loss, take_profit)))
        
        elif result['action'] == 'LONG':
            stop_loss = result['spike_low'] * 0.99
            take_profit = result['current'] * 1.02
            signals.append(('LONG', result['spike_pct'], execute_long(coin, result['current'], stop_loss, take_profit)))
        
        elif result['action'] == 'WATCH':
            print(f"  → 观望，持续监控")
    else:
        print(f"{coin}: 无插针 ✓")

# 按插针幅度排序
if signals:
    signals.sort(key=lambda x: x[1], reverse=True)
    print(f"\n{'='*50}")
    print(f"🎯 信号汇总")
    print(f"{'='*50}")
    for sig_type, spike_pct, trade in signals[:3]:
        print(f"{sig_type}: {trade['coin']} 插针{spike_pct*100:.1f}%")
        print(f"  入场 ${trade['entry']:.4f} | 止损 ${trade['stop']:.4f} | 止盈 ${trade['tp']:.4f}")
else:
    print(f"\n✅ 无插针机会，持续监控...")

print(f"\n{'='*50}")
print(f"📌 操作手册")
print(f"{'='*50}")
print(f"""
【做空机制 - 向上插针】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
信号: 价格突然上涨突破布林上轨
操作: 等待回落确认后做空
止损: 插针高点上方1%
止盈: 入场价下方2%
例子: 价格插针到$10.50布林上轨$10.20
     → 做空，入场$10.30，止损$10.61，止盈$10.09

【做多机制 - 向下插针】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
信号: 价格突然下跌突破布林下轨  
操作: 等待反弹确认后买入
止损: 插针低点下方1%
止盈: 入场价上方2%
例子: 价格插针到$9.80布林下轨$10.00
     → 做多，入场$9.90，止损$9.70，止盈$10.10

【安全规则】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 保证金率 < 3.0 禁止开新仓
2. 单笔不超过总仓位20%
3. 止损必须执行，不扛单
4. 每天最多3笔插针交易
""")
PYEOF
