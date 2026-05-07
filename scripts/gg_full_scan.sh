#!/bin/bash
# 全域扫描 v2 - 1000+币种
echo "【全域扫描 v2 $(date)】"

python3 << 'INNER'
import requests, hmac, hashlib, time, json
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def get_all_symbols():
    """获取所有USDT交易对"""
    try:
        r = requests.get('https://api.binance.com/api/v3/exchangeInfo', proxies=PROXIES, timeout=30)
        symbols = [s['symbol'] for s in r.json()['symbols'] if s['symbol'].endswith('USDT') and s['status'] == 'TRADING']
        return symbols
    except:
        return []

def get_24hr(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', proxies=PROXIES, timeout=5)
        d = r.json()
        return {
            'price': float(d['lastPrice']),
            'chg': float(d['priceChangePercent']),
            'high': float(d['highPrice']),
            'low': float(d['lowPrice']),
            'volume': float(d['quoteVolume'])
        }
    except:
        return None

def get_spot_usdt():
    try:
        ts = int(time.time()*1000)
        params = f'timestamp={ts}&recvWindow=5000'
        sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
        r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return float([b for b in r.json()['balances'] if b['asset']=='USDT'][0]['free'])
    except:
        return 0

print("="*60)
print(f"全域扫描 v2 - 1000+币种")
print("="*60)

# 获取所有币种
symbols = get_all_symbols()
print(f"\n获取到 {len(symbols)} 个USDT交易对...")

# 扫描前200个 (避免超时)
scan_symbols = symbols[:200]
print(f"扫描 {len(scan_symbols)} 个币种...\n")

opportunities = []

for i, sym in enumerate(scan_symbols):
    d = get_24hr(sym)
    if not d: continue
    
    coin = sym.replace('USDT','')
    price = d['price']
    chg = d['chg']
    high = d['high']
    low = d['low']
    volume = d['volume']
    
    if price <= 0: continue
    
    # 布林带位置
    band = high - low
    position = (price - low) / band * 100 if band > 0 else 50
    
    # 筛选机会
    if position < 20 or chg < -3:  # 超卖抄底
        opportunities.append({
            'coin': coin,
            'type': '抄底买入',
            'price': price,
            'chg': chg,
            'position': position,
            'volume': volume,
            'score': abs(chg) * 10 + (50 - position)
        })
    elif position > 80 or chg > 5:  # 超买卖出
        opportunities.append({
            'coin': coin,
            'type': '止盈卖出',
            'price': price,
            'chg': chg,
            'position': position,
            'volume': volume,
            'score': chg * 10 + (position - 50)
        })
    elif volume > 50000000 and abs(chg) > 2:  # 高波动
        opportunities.append({
            'coin': coin,
            'type': '波动机会',
            'price': price,
            'chg': chg,
            'position': position,
            'volume': volume,
            'score': volume / 10000000 + abs(chg) * 20
        })
    
    if (i+1) % 50 == 0:
        print(f"  已扫描 {i+1}/{len(scan_symbols)}...")
    
    time.sleep(0.05)

# 排序
opportunities.sort(key=lambda x: -x['score'])

print(f"\n发现 {len(opportunities)} 个机会:\n")

# 显示Top 20
print("Top 20 机会:")
print("-"*60)
for i, op in enumerate(opportunities[:20]):
    emoji = "📈" if op['chg'] > 0 else "📉"
    vol = op['volume'] / 1000000
    print(f"{i+1:2d}. {emoji} {op['coin']:10} {op['type']:8} | ${op['price']:>12.4f} | {op['chg']:>+6.2f}% | 位置:{op['position']:>5.1f}% | 量:{vol:>6.1f}M")

# 账户
print("\n" + "="*60)
spot_usdt = get_spot_usdt()
print(f"SPOT USDT: ${spot_usdt:.2f}")
print(f"扫描币种: {len(symbols)}")
print("="*60)
INNER
