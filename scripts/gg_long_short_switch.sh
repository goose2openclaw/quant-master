#!/bin/bash
# GG 做空做多灵活转换系统 v1.0
# 根据市场条件自动切换做多/做空模式
# 日期: 2026-05-06

LOG_FILE="/tmp/gg_long_short_switch.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "📊 GG 做空做多灵活转换 $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

python3 << 'PYEOF'
import requests, hmac, hashlib, time, json
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# ================== 配置 ==================
MARGIN_MIN = 3.0
MARGIN_DANGER = 2.5

# RSI Extreme thresholds
RSI_SHORT = 75  # RSI>75 做空
RSI_LONG = 28   # RSI<28 做多

# 市场判定
BULL_THRESHOLD = 0.3  # BTC日涨>0.3% 牛市  
BEAR_THRESHOLD = -0.1  # BTC日跌>-0.1% 熊市  

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

def get_klines(symbol, interval='1h', limit=24):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}', proxies=PROXIES, timeout=10)
        return [(float(d[2]), float(d[3]), float(d[4])) for d in r.json()]  # high, low, close
    except: return None

def calc_rsi(closes, period=14):
    deltas=[closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains=[d if d>0 else 0 for d in deltas]
    losses=[-d if d<0 else 0 for d in deltas]
    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period
    rs=avg_gain/(avg_loss+0.0001)
    return 100-(100/(1+rs))

def calc_d(closes):
    if len(closes)<20: return 0
    ma5=sum(closes[-5:])/5
    ma20=sum(closes[-20:])/20
    trend=1 if ma5>ma20 else(-1 if ma5<ma20 else 0)
    change=(closes[-1]-closes[-24])/closes[-24]*100 if len(closes)>=24 else 0
    returns=[(closes[i]-closes[i-1])/closes[i-1] for i in range(1,len(closes))]
    vol=sum(abs(r) for r in returns[-24:])/24*100
    D=0.35*trend+0.3*(change/10)-0.1*vol
    return max(-1,min(1,D))

# ================== 市场判定 ==================
def get_market_regime():
    """判断市场状态"""
    # BTC价格
    btc_price=get_price('BTCUSDT')
    btc_klines=get_klines('BTCUSDT','1d',2)
    
    if not btc_klines:
        return 'NEUTRAL'
    
    # 日涨跌
    btc_change=(btc_klines[-1][2]-btc_klines[-2][2])/btc_klines[-2][2]*100
    
    # ETH走势
    eth_klines=get_klines('ETHUSDT','1d',5)
    eth_trend=0
    if eth_klines and len(eth_klines)>=5:
        eth_trend=(eth_klines[-1][2]-eth_klines[-5][2])/eth_klines[-5][2]*100
    
    # 判断
    if btc_change>BULL_THRESHOLD and eth_trend>0:
        return 'BULL'  # 牛市
    elif btc_change<BEAR_THRESHOLD and eth_trend<0:
        return 'BEAR'  # 熊市
    else:
        return 'NEUTRAL'  # 震荡

# ================== 信号分析 ==================
def analyze_signal(coin, regime):
    """分析交易信号"""
    sym=f"{coin}USDT"
    
    klines_1h=get_klines(sym,'1h',50)
    klines_1m=get_klines(sym,'1m',30)
    
    if not klines_1h or not klines_1m:
        return None
    
    closes_1h=[k[2] for k in klines_1h]
    closes_1m=[k[2] for k in klines_1m]
    highs_1m=[k[0] for k in klines_1m]
    lows_1m=[k[1] for k in klines_1m]
    
    rsi_14h=calc_rsi(closes_1h,14)
    rsi_14m=calc_rsi(closes_1m,14)
    D=calc_d(closes_1h)
    
    # 布林带
    ma20=sum(closes_1h[-20:])/20
    std=(sum((c-ma20)**2 for c in closes_1h[-20:])/20)**0.5
    bb_upper=ma20+2*std
    bb_lower=ma20-2*std
    
    current=closes_1m[-1]
    
    signals={'long':[],'short':[],'hold':[]}
    
    # ================== 做多信号 ==================
    # RSI超卖
    if rsi_14m<30:
        signals['long'].append(f"RSI超卖({rsi_14m:.0f})")
    
    # RSI<40 + 金叉
    if rsi_14h<40:
        signals['long'].append(f"RSI偏低({rsi_14h:.0f})")
    
    # 向下插针
    recent_low=min(lows_1m[-5:])
    if recent_low<bb_lower*0.99:
        signals['long'].append(f"向下插针")
    
    # 牛市+RSI适中
    if regime=='BULL' and 40<rsi_14m<70:
        signals['long'].append(f"牛市+RSI适中")
    
    # D分数>0.5
    if D>0.5:
        signals['long'].append(f"D强势({D:.2f})")
    
    # 支撑反弹
    if current>ma20*0.98 and rsi_14m<60:
        signals['long'].append(f"MA20支撑")
    
    # ================== 做空信号 ==================
    # RSI超买
    if rsi_14m>70:
        signals['short'].append(f"RSI超买({rsi_14m:.0f})")
    
    # RSI>60 + 死叉
    if rsi_14h>60:
        signals['short'].append(f"RSI偏高({rsi_14h:.0f})")
    
    # 向上插针
    recent_high=max(highs_1m[-5:])
    if recent_high>bb_upper*1.01:
        signals['short'].append(f"向上插针")
    
    # 熊市+RSI偏高
    if regime=='BEAR' and rsi_14m>40:
        signals['short'].append(f"熊市+RSI偏高")
    
    # D分数< -0.3
    if D<-0.3:
        signals['short'].append(f"D弱势({D:.2f})")
    
    # 压力位受阻
    if current<ma20*1.02 and rsi_14m>50:
        signals['short'].append(f"MA20压力")
    
    return {
        'rsi_1m': rsi_14m,
        'rsi_1h': rsi_14h,
        'D': D,
        'price': current,
        'ma20': ma20,
        'bb_upper': bb_upper,
        'bb_lower': bb_lower,
        'regime': regime,
        'long_signals': signals['long'],
        'short_signals': signals['short'],
        'hold_signals': signals['hold']
    }

# ================== 决策引擎 ==================
def make_decision(signals, margin_level):
    """做出交易决策"""
    
    long_score=len(signals['long_signals'])
    short_score=len(signals['short_signals'])
    
    # 基础决策
    if signals['regime']=='BULL':
        # 牛市: 做多优先
        if long_score>=2 and short_score==0:
            return 'LONG'
        elif long_score>=short_score and long_score>=2:
            return 'LONG'
        elif short_score>long_score and short_score>=3:
            return 'SHORT'
        else:
            return 'HOLD'
    
    elif signals['regime']=='BEAR':
        # 熊市: 做空优先
        if short_score>=2 and long_score==0:
            return 'SHORT'
        elif short_score>=long_score and short_score>=2:
            return 'SHORT'
        elif long_score>short_score and long_score>=3:
            return 'LONG'
        else:
            return 'HOLD'
    
    else:
        # 震荡: RSI极端信号
        if signals['rsi_1m']<30:
            return 'LONG'
        elif signals['rsi_1m']>70:
            return 'SHORT'
        else:
            return 'HOLD'

# ================== 主程序 ==================
print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

ml=get_margin()
regime=get_market_regime()
btc_price=get_price('BTCUSDT')
eth_price=get_price('ETHUSDT')

print(f"\n【市场状态】")
print(f"保证金率: {ml:.3f} {'✅' if ml>=MARGIN_MIN else '⚠️'}")
print(f"BTC: ${btc_price:.2f}")
print(f"ETH: ${eth_price:.2f}")
print(f"市场格局: {'🟢牛市' if regime=='BULL' else ('🔴熊市' if regime=='BEAR' else '🟡震荡')}")

# 扫描币种
coins=['LINK','BTC','ETH','BNB','SOL','XRP','ADA','DOGE']
results=[]

print(f"\n{'='*60}")
print(f"📊 币种信号分析")
print(f"{'='*60}")

for coin in coins:
    sig=analyze_signal(coin, regime)
    if not sig:
        continue
    
    decision=make_decision(sig, ml)
    
    # 评分
    confidence=max(len(sig['long_signals']),len(sig['short_signals']))
    
    results.append({
        'coin': coin,
        'signal': sig,
        'decision': decision,
        'confidence': confidence
    })
    
    # 显示
    decision_icon='🟢做多' if decision=='LONG' else('🔴做空' if decision=='SHORT' else '⬜观望')
    print(f"\n{coin}: {decision_icon} (置信度{confidence})")
    print(f"  RSI: {sig['rsi_1m']:.0f}/{sig['rsi_1h']:.0f} | D: {sig['D']:.2f} | {sig['regime']}")
    
    if sig['long_signals']:
        print(f"  做多: {' + '.join(sig['long_signals'][:3])}")
    if sig['short_signals']:
        print(f"  做空: {' + '.join(sig['short_signals'][:3])}")

# 最佳决策
print(f"\n{'='*60}")
print(f"🎯 最佳决策")
print(f"{'='*60}")

# 按置信度排序
results.sort(key=lambda x: x['confidence'], reverse=True)
best=results[0] if results else None

if best:
    print(f"币种: {best['coin']}")
    print(f"决策: {best['decision']}")
    print(f"置信度: {best['confidence']}")
    
    # 资金配置
    if ml<MARGIN_DANGER:
        print(f"\n⚠️ 保证金率过低，禁止开仓")
    elif ml<MARGIN_MIN:
        print(f"\n⚠️ 保证金率预警，减少仓位")
        if best['decision']=='LONG':
            print(f"建议: 观望或极小仓位")
    else:
        # 根据置信度配置
        if best['confidence']>=3:
            position_pct=0.20
            leverage=4
        elif best['confidence']>=2:
            position_pct=0.15
            leverage=3
        else:
            position_pct=0.10
            leverage=2
        
        print(f"\n💰 资金配置:")
        print(f"  仓位: {position_pct*100:.0f}%")
        print(f"  杠杆: {leverage}x")
        print(f"  止损: 2%")
        print(f"  止盈: 5-8%")

# 模式汇总
long_count=sum(1 for r in results if r['decision']=='LONG')
short_count=sum(1 for r in results if r['decision']=='SHORT')
hold_count=sum(1 for r in results if r['decision']=='HOLD')

print(f"\n{'='*60}")
print(f"📈 模式汇总")
print(f"{'='*60}")
print(f"🟢做多: {long_count}个币种")
print(f"🔴做空: {short_count}个币种")
print(f"⬜观望: {hold_count}个币种")

if regime=='BULL':
    print(f"\n🟢 牛市格局: 优先做多")
elif regime=='BEAR':
    print(f"\n🔴 熊市格局: 优先做空")
else:
    print(f"\n🟡 震荡格局: RSI极端信号操作")

print(f"\n✅ 检测完成")
PYEOF
