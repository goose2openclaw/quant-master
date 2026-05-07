#!/bin/bash
# GG 破军策略 v2.0 - 30天+137%目标
# 策略: 走着瞧(预测) + 跟大哥(跟庄)
# 加成: +25%
# 日期: 2026-05-05

echo "=========================================="
echo "🎯 破军策略 v2.0 - 30天+137%"
echo "=========================================="
echo ""
echo "策略: 走着瞧 + 跟大哥"
echo "币种: SOL/DOGE/ETH"
echo "加成: +25%"
echo ""

python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json
from datetime import datetime

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def get_prices(coins):
    prices = {}
    for c in coins:
        try:
            r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={c}USDT', proxies=PROXIES, timeout=6)
            prices[c] = float(r.json()['price'])
        except: prices[c] = 0
    return prices

def get_klines(symbol, limit=24):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit={limit}', proxies=PROXIES, timeout=10)
        klines = r.json()
        return [(float(d[1]), float(d[2]), float(d[3]), float(d[4]), float(d[5])) for d in klines]
    except: return None

def calc_D(closes):
    if len(closes) < 20: return 0
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    trend = 1 if ma5 > ma20 else (-1 if ma5 < ma20 else 0)
    change = (closes[-1] - closes[-24]) / closes[-24] * 100 if len(closes) >= 24 else 0
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1,len(closes))]
    vol = sum(abs(r) for r in returns[-24:]) / 24 * 100 if returns else 0
    D = 0.35*trend + 0.3*(change/10) - 0.1*vol
    return max(-1, min(1, D))

def mirofish(D, n=1000):
    random.seed(int(time.time()))
    votes = {'buy':0,'hold':0,'sell':0}
    for _ in range(n):
        noise = random.gauss(0, 0.15)
        score = D + noise
        if score > 0.5: votes['buy'] += 1
        elif score > 0.1: votes['hold'] += 1
        else: votes['sell'] += 1
    total = sum(votes.values())
    return {k: v/total*100 for k,v in votes.items()}

# 破军策略核心
print("【破军策略核心】")
print("走着瞧 + 跟大哥 = 预测 + 跟庄")
print("加成: +25%")
print()

COINS = ['BTC', 'ETH', 'BNB', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA']
prices = get_prices(COINS)

print("【跟庄信号检测】")
print("-" * 50)

for coin in COINS:
    sym = f"{coin}USDT"
    klines = get_klines(sym, 24)
    if not klines: continue
    
    closes = [k[3] for k in klines]
    volumes = [k[4] for k in klines]
    
    D = calc_D(closes)
    votes = mirofish(D)
    
    # 破军信号条件
    # 1. 走着瞧: D > 0.3 (有趋势)
    # 2. 跟大哥: BTC涨时ALT也跟涨
    
    btc_klines = get_klines('BTCUSDT', 24)
    btc_closes = [k[3] for k in btc_klines] if btc_klines else []
    btc_change = (btc_closes[-1] - btc_closes[0]) / btc_closes[0] * 100 if btc_closes else 0
    
    coin_change = (closes[-1] - closes[0]) / closes[0] * 100
    
    # 跟大哥信号: BTC涨，ALT跟涨
    follow_bt_signal = btc_change > 0 and coin_change > btc_change * 0.5
    
    # 预测信号: 连续上涨
    predict_signal = all(closes[i] > closes[i-1] for i in range(len(closes)-3, len(closes)))
    
    if D > 0.3:
        signal = "🚀 破军信号"
        if votes['buy'] > 50: signal += " +跟庄!"
    elif votes['buy'] > 60:
        signal = "📈 跟庄信号"
    elif predict_signal:
        signal = "🔮 走着瞧信号"
    else:
        signal = "➡️ 观望"
    
    arrow = "📈" if coin_change > 0 else "📉"
    print(f"{coin}: ${prices[coin]:.4f} {arrow}{coin_change:+.1f}% D={D:.2f} Miro={votes['buy']:.0f}% {signal}")

print()
print("【操作建议】")
print("-" * 50)
print("破军策略: 走着瞧(预测) + 跟大哥(跟庄)")
print()
print("信号优先级:")
print("1. 🚀 破军信号: 立即买入 (D>0.3 + Miro买>50%)")
print("2. 📈 跟庄信号: BTC启动时买入最强ALT")
print("3. 🔮 走着瞧信号: 等待连续上涨确认")
print("4. ➡️ 观望: 无信号不操作")
print()
print("止盈止损:")
print("- 止盈: +20%")
print("- 止损: -5%")
print("- 破军加成: +25% (达到+25%时触发)")

PYEOF
