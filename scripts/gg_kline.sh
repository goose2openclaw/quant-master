#!/bin/bash
# 实时K线图生成器
# 显示持仓币种K线图

LOG_FILE="/tmp/gg_kline.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "实时K线图 $(date)"
echo "=========================================="

python3 << 'INNER'
import requests, time
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def get_klines(symbol, interval='1h', limit=24):
    """获取K线数据"""
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        r = requests.get(url, proxies=PROXIES, timeout=10)
        return r.json()
    except:
        return []

def get_price(symbol):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except:
        return 0

def draw_candlestick(opens, highs, lows, closes, symbol, timeframe):
    """绘制简易K线图"""
    print(f"\n{'='*60}")
    print(f"{symbol} {timeframe} K线图")
    print(f"{'='*60}")
    
    # 计算布林带
    avg = sum(closes) / len(closes)
    max_p = max(highs)
    min_p = min(lows)
    
    # 绘制价格
    print(f"当前价格: ${closes[-1]:.6f}")
    print(f"区间最高: ${max_p:.6f}")
    print(f"区间最低: ${min_p:.6f}")
    print(f"均价: ${avg:.6f}")
    
    # 简化K线: 用字符表示涨跌
    print(f"\nK线 (24周期):")
    for i in range(len(opens)):
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]
        if c >= o:
            print(f"  周期{i+1:2d}: 📈 开${o:.2f} 高${h:.2f} 低${l:.2f} 收${c:.2f}")
        else:
            print(f"  周期{i+1:2d}: 📉 开${o:.2f} 高${h:.2f} 低${l:.2f} 收${c:.2f}")

# 持仓币种
coins = [
    ('BTCUSDT', 'BTC'),
    ('ETHUSDT', 'ETH'),
    ('SOLUSDT', 'SOL'),
    ('XRPUSDT', 'XRP'),
    ('ADAUSDT', 'ADA'),
    ('DOGEUSDT', 'DOGE'),
    ('LINKUSDT', 'LINK'),
]

for symbol, name in coins:
    klines = get_klines(symbol, '1h', 24)
    if klines:
        opens = [float(k[1]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        draw_candlestick(opens, highs, lows, closes, name, '1H')
    time.sleep(0.5)

print(f"\n更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)
INNER
