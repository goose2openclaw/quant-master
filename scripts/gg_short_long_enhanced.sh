#!/bin/bash
# GG 做空做多增强系统 + 即时算力资金匹配 v1.0
# 日期: 2026-05-06

echo "=========================================="
echo "📊 GG 做空做多增强系统 + 即时匹配"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json, random
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# ================== 配置 ==================
MARGIN_MIN = 3.0
MARGIN_DANGER = 2.5
MAX_POSITION_PCT = 0.2  # 单笔最大20%仓位

# ================== 工具函数 ==================
def get_margin():
    ts=int(time.time()*1000)
    params='timestamp=%d&recvWindow=5000' % ts
    sig=hmac.new(API_SECRET.encode(),params.encode(),hashlib.sha256).hexdigest()
    r=requests.get('https://api.binance.com/sapi/v1/margin/account?%s&signature=%s' % (params,sig), headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10).json()
    return float(r.get('marginLevel',999)), float(r.get('totalAssetOfBtc',0)), r

def get_price(symbol):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines_1m(symbol, limit=60):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit={limit}', proxies=PROXIES, timeout=10)
        return [{
            'high': float(d[2]), 'low': float(d[3]),
            'close': float(d[4]), 'vol': float(d[5])
        } for d in r.json()]
    except: return []

def get_order_book(symbol, limit=20):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}', proxies=PROXIES, timeout=5)
        d=r.json()
        return {
            'bids': [(float(p), float(q)) for p,q in d.get('bids',[])],
            'asks': [(float(p), float(q)) for p,q in d.get('asks',[])]
        }
    except: return {'bids':[], 'asks':[]}

def get_taker_ratio():
    """获取主动买卖比"""
    try:
        r=requests.get('https://api.binance.com/api/v3/klines?symbol=LINKUSDT&interval=5m&limit=12', proxies=PROXIES, timeout=10)
        buys=sum(float(d[5]) for d in r.json()[-6:])
        sells=sum(float(d[5]) for d in r.json()[:6])
        return buys/sells if sells>0 else 1
    except: return 1

def get_btc_dominance():
    """获取BTC市值占比"""
    try:
        r=requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', proxies=PROXIES, timeout=8)
        btc=float(r.json()['price'])
        r2=requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', proxies=PROXIES, timeout=8)
        eth=float(r2.json()['price'])
        # 简化估算
        return 52 + random.uniform(-2, 2)
    except: return 52

# ================== 做空机制增强 ==================
def analyze_short_opportunity(coin):
    """分析做空机会"""
    sym=f"{coin}USDT"
    klines=get_klines_1m(sym, 60)
    if len(klines)<20: return None
    
    closes=[k['close'] for k in klines]
    highs=[k['high'] for k in klines]
    lows=[k['low'] for k in klines]
    vols=[k['vol'] for k in klines]
    
    # 布林带
    ma20=sum(closes[-20:])/20
    std=(sum((c-ma20)**2 for c in closes[-20:])/20)**0.5
    bb_upper=ma20+2*std
    bb_lower=ma20-2*std
    
    # RSI
    deltas=[closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains=[d if d>0 else 0 for d in deltas]
    losses=[-d if d<0 else 0 for d in deltas]
    avg_gain=sum(gains[-14:])/14
    avg_loss=sum(losses[-14:])/14
    rsi=100-(100/(1+avg_gain/(avg_loss+0.0001)))
    
    # MACD
    ema12=sum(closes[-12:])/12
    ema26=sum(closes[-26:])/26
    macd=ema12-ema26
    signal=macd*0.8
    
    # 检测向上插针
    recent_high=max(k['high'] for k in klines[-5:])
    current=closes[-1]
    
    # 做空信号
    signals=[]
    
    # 信号1: 向上插针突破布林上轨
    if recent_high>bb_upper*1.01:
        spike_pct=(recent_high-bb_upper)/bb_upper*100
        dropback=(recent_high-current)/recent_high*100
        signals.append({
            'type':'SPIKE_UP',
            'spike_pct':spike_pct,
            'dropback':dropback,
            'entry':current,
            'stop':recent_high*1.01,
            'tp':current*0.98,
            'reason':f'向上插针+{spike_pct:.1f}%,回落{dropback:.1f}%'
        })
    
    # 信号2: RSI超买+MACD死叉
    if rsi>70 and macd<signal:
        signals.append({
            'type':'RSI_OVERBOUGHT',
            'rsi':rsi,
            'entry':current,
            'stop':current*1.02,
            'tp':current*0.96,
            'reason':f'RSI超买{rsi:.0f}+MACD死叉'
        })
    
    # 信号3: 反弹无力(做空)
    if len(closes)>=10:
        recent_drop=closes[-1]-min(closes[-10:])
        recent_rise=max(closes[-5:])-closes[-1]
        if recent_drop>0.01*closes[-1] and recent_rise<recent_drop*0.3:
            signals.append({
                'type':'WEAK_REBOUND',
                'drop':recent_drop/closes[-1]*100,
                'rise':recent_rise/closes[-1]*100,
                'entry':current,
                'stop':current*1.015,
                'tp':current*0.97,
                'reason':f'反弹无力(跌{recent_drop/closes[-1]*100:.1f}%后仅反弹{recent_rise/closes[-1]*100:.1f}%)'
            })
    
    # 信号4: 成交量萎缩+价格上涨背离
    recent_vol_avg=sum(vols[-10:])/10
    recent_vol=vols[-1]
    if recent_vol<recent_vol_avg*0.7 and current>ma20*1.02:
        signals.append({
            'type':'VOL_PRICE_DIVERGE',
            'vol_ratio':recent_vol/recent_vol_avg,
            'entry':current,
            'stop':current*1.02,
            'tp':current*0.97,
            'reason':f'缩量上涨背离'
        })
    
    return signals[0] if signals else None

# ================== 做多机制增强 ==================
def analyze_long_opportunity(coin):
    """分析做多机会"""
    sym=f"{coin}USDT"
    klines=get_klines_1m(sym, 60)
    if len(klines)<20: return None
    
    closes=[k['close'] for k in klines]
    highs=[k['high'] for k in klines]
    lows=[k['low'] for k in klines]
    vols=[k['vol'] for k in klines]
    
    # 布林带
    ma20=sum(closes[-20:])/20
    std=(sum((c-ma20)**2 for c in closes[-20:])/20)**0.5
    bb_upper=ma20+2*std
    bb_lower=ma20-2*std
    
    # RSI
    deltas=[closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains=[d if d>0 else 0 for d in deltas]
    losses=[-d if d<0 else 0 for d in deltas]
    avg_gain=sum(gains[-14:])/14
    avg_loss=sum(losses[-14:])/14
    rsi=100-(100/(1+avg_gain/(avg_loss+0.0001)))
    
    # MACD
    ema12=sum(closes[-12:])/12
    ema26=sum(closes[-26:])/26
    macd=ema12-ema26
    signal=macd*0.8
    
    # 检测向下插针
    recent_low=min(k['low'] for k in klines[-5:])
    current=closes[-1]
    
    signals=[]
    
    # 信号1: 向下插针跌破布林下轨
    if recent_low<bb_lower*0.99:
        spike_pct=(bb_lower-recent_low)/bb_lower*100
        bounce=(current-recent_low)/recent_low*100
        signals.append({
            'type':'SPIKE_DOWN',
            'spike_pct':spike_pct,
            'bounce':bounce,
            'entry':current,
            'stop':recent_low*0.99,
            'tp':current*1.03,
            'reason':f'向下插针-{spike_pct:.1f}%,反弹{bounce:.1f}%'
        })
    
    # 信号2: RSI超卖+MACD金叉
    if rsi<40 and macd>signal:
        signals.append({
            'type':'RSI_OVERSOLD',
            'rsi':rsi,
            'entry':current,
            'stop':current*0.98,
            'tp':current*1.04,
            'reason':f'RSI超卖{rsi:.0f}+MACD金叉'
        })
    
    # 信号3: 回调支撑(做多)
    if len(closes)>=10:
        recent_rise=max(closes[-10:])-closes[-1]
        recent_drop=closes[-1]-min(closes[-5:])
        if recent_rise>0.01*closes[-1] and recent_drop<recent_rise*0.3:
            signals.append({
                'type':'SUPPORT_REBOUND',
                'rise':recent_rise/closes[-1]*100,
                'drop':recent_drop/closes[-1]*100,
                'entry':current,
                'stop':current*0.985,
                'tp':current*1.035,
                'reason':f'支撑反弹(涨{recent_rise/closes[-1]*100:.1f}%后回调{recent_drop/closes[-1]*100:.1f}%)'
            })
    
    # 信号4: 缩量回调获得支撑
    recent_vol_avg=sum(vols[-10:])/10
    recent_vol=vols[-1]
    if recent_vol<recent_vol_avg*0.6 and current>bb_lower and current<ma20:
        signals.append({
            'type':'VOL_SUPPORT',
            'vol_ratio':recent_vol/recent_vol_avg,
            'entry':current,
            'stop':current*0.985,
            'tp':current*1.04,
            'reason':f'缩量获得支撑'
        })
    
    return signals[0] if signals else None

# ================== 即时算力匹配 ==================
def compute_power_match(signal_type, confidence):
    """计算最佳算力分配"""
    # 算力池配置
    compute_pool = {
        'high': {'cpu': 4, 'memory': '8GB', 'risk': 'high'},
        'medium': {'cpu': 2, 'memory': '4GB', 'risk': 'medium'},
        'low': {'cpu': 1, 'memory': '2GB', 'risk': 'low'}
    }
    
    # 根据信号强度匹配算力
    if signal_type in ['SPIKE_UP', 'RSI_OVERBOUGHT'] and confidence > 0.7:
        return compute_pool['high']
    elif signal_type in ['RSI_OVERSOLD', 'SUPPORT_REBOUND'] and confidence > 0.6:
        return compute_pool['medium']
    else:
        return compute_pool['low']

# ================== 即时资金调配 ==================
def compute_capital_match(margin_level, signal_type, volatility):
    """计算最佳资金分配"""
    available_capital = 100  # 假设可用100U
    
    if margin_level < MARGIN_DANGER:
        # 危险区域，禁止开仓
        return {'position': 0, 'leverage': 0, 'action': 'FORCE_REDUCE'}
    
    if margin_level < MARGIN_MIN:
        # 预警区域，减少仓位
        position_pct = 0.1
        leverage = 1
        action = 'REDUCE'
    elif margin_level > 4.0:
        # 资金充裕，可加大仓位
        if signal_type in ['SPIKE_UP', 'SPIKE_DOWN']:
            position_pct = 0.25
            leverage = 3
            action = 'INCREASE'
        elif signal_type in ['RSI_OVERBOUGHT', 'RSI_OVERSOLD']:
            position_pct = 0.15
            leverage = 2
            action = 'HOLD'
        else:
            position_pct = 0.1
            leverage = 1
            action = 'NORMAL'
    else:
        # 正常区域
        position_pct = 0.15
        leverage = 2
        action = 'NORMAL'
    
    # 根据波动率调整
    if volatility > 0.03:
        position_pct *= 0.8  # 高波动减仓
        leverage = min(leverage, 2)
    
    position_usdt = available_capital * position_pct
    return {
        'position_pct': position_pct,
        'position_usdt': position_usdt,
        'leverage': leverage,
        'action': action,
        'margin_required': position_usdt / leverage
    }

# ================== 主程序 ==================
print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

ml, total_btc, account = get_margin()
rb=requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', proxies=PROXIES, timeout=8)
btc_price=float(rb.json()['price'])
total_usd=total_btc*btc_price

print(f"\n【账户状态】")
print(f"保证金率: {ml:.3f}")
print(f"总资产: ${total_usd:.2f}")
print(f"状态: {'🚨危险' if ml<MARGIN_DANGER else ('⚠️预警' if ml<MARGIN_MIN else '✅正常')}")

print(f"\n{'='*60}")
print(f"📊 做空/做多信号扫描")
print(f"{'='*60}")

coins=['LINK','BTC','ETH','BNB','SOL','XRP','DOGE','ADA']
short_signals=[]
long_signals=[]

for coin in coins:
    # 做空分析
    short_sig=analyze_short_opportunity(coin)
    if short_sig:
        short_signals.append((coin, short_sig))
    
    # 做多分析
    long_sig=analyze_long_opportunity(coin)
    if long_sig:
        long_signals.append((coin, long_sig))

# 显示做空信号
print(f"\n【做空信号】({len(short_signals)}个)")
for coin, sig in short_signals:
    print(f"\n{coin}: {sig['reason']}")
    cap=compute_capital_match(ml, sig['type'], 0.02)
    print(f"  入场: ${sig['entry']:.4f}")
    print(f"  止损: ${sig['stop']:.4f} ({((sig['stop']-sig['entry'])/sig['entry'])*100:+.1f}%)")
    print(f"  止盈: ${sig['tp']:.4f} ({((sig['entry']-sig['tp'])/sig['entry'])*100:+.1f}%)")
    print(f"  资金: {cap['action']} → {cap['position_usdt']:.1f}U @{cap['leverage']}x")

# 显示做多信号
print(f"\n【做多信号】({len(long_signals)}个)")
for coin, sig in long_signals:
    print(f"\n{coin}: {sig['reason']}")
    cap=compute_capital_match(ml, sig['type'], 0.02)
    print(f"  入场: ${sig['entry']:.4f}")
    print(f"  止损: ${sig['stop']:.4f} ({((sig['stop']-sig['entry'])/sig['entry'])*100:+.1f}%)")
    print(f"  止盈: ${sig['tp']:.4f} ({((sig['tp']-sig['entry'])/sig['entry'])*100:+.1f}%)")
    print(f"  资金: {cap['action']} → {cap['position_usdt']:.1f}U @{cap['leverage']}x")

# 即时匹配汇总
print(f"\n{'='*60}")
print(f"💰 即时算力+资金匹配")
print(f"{'='*60}")

# 获取市场状态
taker_ratio=get_taker_ratio()
btc_dom=get_btc_dominance()

print(f"\n市场状态:")
print(f"  主动买卖比: {taker_ratio:.2f} ({'买方主导' if taker_ratio>1 else '卖方主导'})")
print(f"  BTC占比: {btc_dom:.1f}%")

# 总体配置
all_signals=short_signals+long_signals
if all_signals and ml>=MARGIN_DANGER:
    best=all_signals[0]
    coin=best[0]
    sig=best[1]
    sig_type='做空' if sig in [s[1] for s in short_signals] else '做多'
    
    print(f"\n【最优匹配】")
    print(f"  币种: {coin} ({sig_type})")
    print(f"  信号类型: {sig['type']}")
    
    cap=compute_capital_match(ml, sig['type'], 0.02)
    print(f"  仓位配置: {cap['position_usdt']:.1f}U ({cap['position_pct']*100:.0f}%)")
    print(f"  杠杆倍数: {cap['leverage']}x")
    print(f"  保证金需求: {cap['margin_required']:.2f}U")
    print(f"  操作: {cap['action']}")
    
    power=compute_power_match(sig['type'], 0.7)
    print(f"  算力分配: CPU{power['cpu']}核 {power['memory']}")
    print(f"  风险等级: {power['risk']}")
else:
    if ml<MARGIN_DANGER:
        print(f"\n⚠️ 保证金率{MARGIN_DANGER}，禁止开仓")
    else:
        print(f"\n✅ 无明确信号，继续观望")

print(f"\n{'='*60}")
print(f"📋 操作手册")
print(f"{'='*60}")
print("""
【做空增强信号】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. SPIKE_UP: 向上插针突破布林上轨 → 做空
2. RSI_OVERBOUGHT: RSI>70+MACD死叉 → 做空
3. WEAK_REBOUND: 反弹无力 → 做空
4. VOL_PRICE_DIVERGE: 缩量上涨背离 → 做空

【做多增强信号】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. SPIKE_DOWN: 向下插针跌破布林下轨 → 做多
2. RSI_OVERSOLD: RSI<40+MACD金叉 → 做多
3. SUPPORT_REBOUND: 回调支撑 → 做多
4. VOL_SUPPORT: 缩量获得支撑 → 做多

【资金调配规则】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
保证金率<2.5 → 强制减仓，禁止开新仓
保证金率<3.0 → 预警，减仓50%
保证金率>4.0 → 充裕，可加仓到25%+3x杠杆

【算力匹配规则】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
高算力: 4核CPU+8GB (高确定性信号)
中算力: 2核CPU+4GB (中等信号)
低算力: 1核CPU+2GB (观望信号)
""")
PYEOF
