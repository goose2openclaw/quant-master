#!/bin/bash
# GG Crypto Monitor v2.3.1 - 全域扫描D分数修复版
# 版本: v2.3.1 - 2026-05-05

LOG_DIR="/tmp/gg_monitor"
MODE="${1:-scan}"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_DIR/gg_monitor_$(date +%Y%m%d).log"
}

scan_all() {
    log "🔍 [10min] 全域强信号扫描 v2.3.1"
    python3 << 'PYEOF'
import requests, hmac, hashlib, time, random, json
API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

KEY_COINS = ['BTC','ETH','BNB','SOL','LINK','XRP','ADA','DOGE','ORDI','AVAX','DOT','UNI']

def get_prices():
    prices = {}
    for c in KEY_COINS:
        try:
            r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={c}USDT', proxies=PROXIES, timeout=6)
            prices[c] = float(r.json()['price'])
        except: prices[c] = 0
    return prices

def get_klines(symbol, limit=72):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit={limit}', proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def calc_D(closes, volumes):
    """修复版D分数计算 - 归一化到-1到1范围"""
    if len(closes) < 60: return 0
    
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    ma60 = sum(closes[-60:]) / 60
    
    # 趋势: -1到1
    if ma5 > ma20 > ma60: trend = 0.8
    elif ma5 < ma20 < ma60: trend = -0.8
    else: trend = 0.0
    
    # 24h涨跌: 归一化到 -1到1 (假设日波动±10%为极端)
    change_24h = (closes[-1] - closes[-24]) / closes[-24] * 100 if len(closes) >= 24 else 0
    change_norm = max(-1, min(1, change_24h / 10))
    
    # 量比: 归一化
    vol_ratio = volumes[-1] / (sum(volumes[-24:]) / 24) if volumes else 1
    vol_norm = max(-1, min(1, (vol_ratio - 1) * 2))  # ±0.5为极端
    
    # 波动率: 使用24h收益率的标准差
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, min(25, len(closes)))]
    vol = (max(returns) - min(returns)) if returns else 0  # 简单波动率估算
    vol_norm = max(-1, min(1, vol * 10))  # 归一化
    
    # D分数: 加权组合
    D = 0.35*trend + 0.30*change_norm + 0.25*vol_norm - 0.10*vol_norm*0.5
    
    return max(-1, min(1, D))  # 限制在-1到1

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

def check_rsi(closes, period=14):
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

prices = get_prices()
strong_signals = []
观望 = []

print("\n" + "="*60)
print("🔍 全域强信号扫描 v2.3.1")
print("="*60)

for coin in KEY_COINS:
    sym = f"{coin}USDT"
    klines = get_klines(sym, 72)
    if not klines: continue
    
    closes = [float(k[4]) for k in klines]
    volumes = [float(k[5]) for k in klines]
    
    price = prices.get(coin, 0)
    change_24h = float(requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', proxies=PROXIES, timeout=6).json()['priceChangePercent'])
    
    D = calc_D(closes, volumes)
    votes = mirofish(D)
    rsi = check_rsi(closes)
    
    buy_pct = votes['buy']
    sell_pct = votes['sell']
    net_power = buy_pct - sell_pct
    
    # 信号判定
    signal = None
    strength = None
    emoji = None
    
    if D > 0.5 and buy_pct > 60:
        signal, strength, emoji = "🚀 强势买入", "STRONG_BUY", "📈"
    elif D > 0.3 and buy_pct > 40:
        signal, strength, emoji = "📈 中等买入", "MEDIUM_BUY", "📈"
    elif D > 0.1:
        signal, strength, emoji = "👀 轻微买入", "WEAK_BUY", "➡️"
    elif D < -0.5 and sell_pct > 60:
        signal, strength, emoji = "🔴 强势卖出", "STRONG_SELL", "📉"
    elif D < -0.3 and sell_pct > 40:
        signal, strength, emoji = "⚠️ 中等卖出", "MEDIUM_SELL", "📉"
    elif D < -0.1:
        signal, strength, emoji = "👀 轻微卖出", "WEAK_SELL", "➡️"
    else:
        signal, strength, emoji = "➡️ 观望", "WATCH", "➡️"
        观望.append(coin)
    
    # RSI状态
    if rsi > 70: rsi_status = "超买"
    elif rsi < 30: rsi_status = "超卖"
    else: rsi_status = "中性"
    
    arrow = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
    
    print(f"\n{coin}: ${price:.4f} {arrow}{change_24h:+.2f}%")
    print(f"  D={D:.3f} RSI={rsi:.0f}({rsi_status}) Miro={buy_pct:.0f}%/{sell_pct:.0f}%")
    print(f"  {signal}")
    
    if strength in ['STRONG_BUY', 'STRONG_SELL', 'MEDIUM_BUY', 'MEDIUM_SELL']:
        strong_signals.append({
            'coin': coin, 'price': price, 'change': change_24h,
            'D': D, 'rsi': rsi, 'buy_pct': buy_pct, 'sell_pct': sell_pct,
            'signal': signal, 'strength': strength
        })

print("\n" + "="*60)
print("📊 扫描结果汇总")
print("="*60)

print(f"\n强信号 ({len(strong_signals)}个):")
for s in strong_signals:
    print(f"  {s['coin']}: {s['signal']} D={s['D']:.2f} RSI={s['rsi']:.0f}")

print(f"\n观望 ({len(观望)}个): {', '.join(观望) if 观望 else '无'}")

# 保存
with open('/tmp/gg_scan_latest.json', 'w') as f:
    json.dump({'signals': strong_signals, 'watch': 观望, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}, f)

print("\n✅ 扫描完成")
PYEOF
}

case $MODE in
    scan) scan_all ;;
    *) echo "Usage: $0 scan" ;;
esac
