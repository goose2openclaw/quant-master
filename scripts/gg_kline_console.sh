#!/bin/bash
# K线控制台版本 - 适合常驻显示

while true; do
    clear
    echo "=========================================="
    echo "实时K线图 $(date)"
    echo "=========================================="
    
    python3 << 'INNER'
import requests, time
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=24):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        r = requests.get(url, proxies=PROXIES, timeout=10)
        return r.json()
    except: return []

coins = [
    ('BTCUSDT', 'BTC', 0),
    ('ETHUSDT', 'ETH', 0),
    ('SOLUSDT', 'SOL', 0),
    ('XRPUSDT', 'XRP', 0),
    ('ADAUSDT', 'ADA', 0),
    ('DOGEUSDT', 'DOGE', 0),
    ('LINKUSDT', 'LINK', 0),
]

for symbol, name, _ in coins:
    klines = get_klines(symbol, '1h', 24)
    price = get_price(symbol)
    
    if klines and price > 0:
        opens = [float(k[1]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        
        # 计算布林带
        avg = sum(closes) / len(closes)
        max_p = max(highs)
        min_p = min(lows)
        
        # 位置计算
        band = max_p - min_p
        position = (price - min_p) / band * 100 if band > 0 else 50
        
        # 涨跌
        chg = (price - opens[-1]) / opens[-1] * 100
        
        # 简单K线图
        print()
        print(f"  {name:6} ${price:>12.4f}  {chg:>+6.2f}%  位置:{position:>5.1f}%")
        print(f"         区间: ${min_p:.4f} - ${max_p:.4f}")
        
        # 绘制迷你图
        bars = ""
        for i in range(min(12, len(closes))):
            idx = i * 2
            if idx < len(closes):
                c = closes[idx]
                if c >= opens[idx]:
                    bars += "█"
                else:
                    bars += "▄"
        print(f"         {bars}")

print()
print(f"更新时间: {time.strftime('%H:%M:%S')}")
print("==========================================")
INNER
    
    sleep 30
done
