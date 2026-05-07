#!/usr/bin/env python3
"""
GO2SE Genius (GG) 自主循环系统
版本: v1.0
日期: 2026-05-03
"""

import requests
import hmac
import hashlib
import time
import json
import random
from datetime import datetime

API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"
PROXIES = {"http": "http://172.29.144.1:7897", "https": "http://172.29.144.1:7897"}

FOCUS = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'LINK', 'DOGE', 'AVAX', 'DOT']

def get_account():
    ts = int(time.time() * 1000)
    params = f"timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    resp = requests.get(f"https://api.binance.com/api/v3/account?{params}&signature={sig}", headers={"X-MBX-APIKEY": API_KEY}, proxies=PROXIES, timeout=10)
    return {b["asset"]: float(b["free"]) for b in resp.json()["balances"]}

def get_prices(coins):
    sym = json.dumps([f"{c}USDT" for c in coins])
    resp = requests.get("https://api.binance.com/api/v3/ticker/24hr", params={"symbols": sym}, proxies=PROXIES, timeout=10)
    return {p["symbol"].replace("USDT", ""): float(p["lastPrice"]) for p in resp.json()}

def get_klines(symbol, interval='1h', limit=100):
    resp = requests.get("https://api.binance.com/api/v3/klines",
                      params={"symbol": symbol, "interval": interval, "limit": limit},
                      proxies=PROXIES, timeout=10)
    return resp.json() if resp.status_code == 200 else []

def scan_all():
    """全域扫描"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 全域扫描...")
    
    prices = get_prices(FOCUS)
    
    results = {}
    for coin in FOCUS:
        klines = get_klines(f"{coin}USDT")
        if not klines:
            continue
        
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        # MA
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else sum(closes) / len(closes)
        
        # 变化
        change_24h = (closes[-1] - closes[-24]) / closes[-24] * 100 if len(closes) >= 24 else 0
        
        # 波动
        returns = [(closes[i] - closes[i-1]) / closes[i-1] * 100 for i in range(1, len(closes))]
        volatility = sum(abs(r) for r in returns) / len(returns) if returns else 0
        
        # 量比
        avg_vol = sum(volumes[-24:]) / 24
        vol_ratio = volumes[-1] / avg_vol if avg_vol > 0 else 1
        
        # 胜率 (30天)
        wins = sum(1 for i in range(24, len(closes)) if closes[i] > closes[i-4])
        win_rate = wins / (len(closes) - 24) * 100 if len(closes) > 24 else 50
        
        results[coin] = {
            'price': closes[-1],
            'ma5': ma5,
            'ma20': ma20,
            'ma60': ma60,
            'change_24h': change_24h,
            'volatility': volatility,
            'vol_ratio': vol_ratio,
            'win_rate': win_rate,
            'trend': 'up' if ma5 > ma20 > ma60 else 'down'
        }
    
    return results

def decision_mirofish(score, iterations=1000):
    """Mirofish仿真"""
    random.seed(int(time.time()))
    
    votes = {'buy': 0, 'hold': 0, 'sell': 0}
    
    for _ in range(iterations):
        noise = random.gauss(0, 0.2)
        final = score + noise
        
        if final > 0.6:
            votes['buy'] += 1
        elif final > 0.3:
            votes['hold'] += 1
        else:
            votes['sell'] += 1
    
    total = sum(votes.values())
    return {
        'buy_pct': votes['buy'] / total * 100,
        'hold_pct': votes['hold'] / total * 100,
        'sell_pct': votes['sell'] / total * 100,
        'decision': max(votes, key=votes.get)
    }

def run_cycle():
    """运行一个完整周期"""
    print("\n" + "=" * 60)
    print("🧠 GG 自主循环")
    print("=" * 60)
    
    # 1. 全域扫描
    data = scan_all()
    
    # 2. 策略分析
    print("\n策略信号:")
    
    for coin, d in sorted(data.items(), key=lambda x: abs(x[1]['change_24h']), reverse=True)[:5]:
        # 打兔子分数
        trend_score = 1 if d['trend'] == 'up' else -1
        rabbit_d = 0.35 * trend_score + 0.3 * (d['change_24h'] / 10) + 0.25 * (d['vol_ratio'] - 1) - 0.1 * d['volatility']
        
        # 跟大哥分数
        follow_d = 0.4 * min(d['vol_ratio'] / 2, 1) + 0.3 * (1 if d['trend'] == 'up' else 0) + 0.3 * (d['change_24h'] / 10)
        
        # Mirofish仿真
        miro = decision_mirofish(rabbit_d)
        
        print(f"\n{coin}:")
        print(f"  价格: ${d['price']:.4f}")
        print(f"  趋势: {d['trend']} | 24h: {d['change_24h']:+.2f}%")
        print(f"  打兔子: {rabbit_d:.3f} | 跟大哥: {follow_d:.3f}")
        print(f"  Mirofish: {miro['decision']} ({miro['buy_pct']:.0f}%买入)")
    
    # 3. 检查持仓
    balances = get_account()
    prices = get_prices(['DOGE', 'ORDI', 'ORCA', 'LINK'])
    
    print("\n持仓状态:")
    total = 0
    for asset, qty in balances.items():
        if qty > 0 and asset in prices:
            value = qty * prices[asset]
            total += value
            print(f"  {asset}: {qty:.4f} @ ${prices[asset]:.4f} = ${value:.2f}")
    
    print(f"\n总价值: ${total:.2f}")
    
    # 4. 决策输出
    print("\n决策建议:")
    print("  - 市场平稳，继续监控")
    print("  - 等待激活信号")
    
    print("\n" + "=" * 60)

def main():
    print("🧠 GG 自主循环启动...")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n=== 周期 {cycle} ===")
        
        try:
            run_cycle()
        except Exception as e:
            print(f"错误: {e}")
        
        # 5分钟一个周期
        print("\n等待5分钟...")
        time.sleep(300)

if __name__ == "__main__":
    main()
