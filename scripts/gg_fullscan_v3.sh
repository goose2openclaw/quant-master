#!/bin/bash
# 全域扫描v3 - 扫描所有432个USDT交易对
echo "【全域扫描v3 $(date)】"

python3 << 'PYEOF'
import requests, time
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# 获取所有USDT交易对
print("获取交易对列表...")
r = requests.get('https://api.binance.com/api/v3/exchangeInfo', proxies=PROXIES, timeout=30)
symbols = [s['symbol'] for s in r.json()['symbols'] if s['symbol'].endswith('USDT') and s['status'] == 'TRADING']
print(f"总交易对: {len(symbols)}")

# 扫描所有币种
print("扫描中...")
opportunities = []
for i, sym in enumerate(symbols):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', proxies=PROXIES, timeout=5)
        d = r.json()
        chg = float(d['priceChangePercent'])
        price = float(d['lastPrice'])
        high = float(d['highPrice'])
        low = float(d['lowPrice'])
        volume = float(d['quoteVolume'])
        
        if price <= 0: continue
        
        # 布林带位置
        band = high - low
        position = (price - low) / band * 100 if band > 0 else 50
        
        # 筛选机会
        if position < 20 or chg < -3:  # 超卖抄底
            opportunities.append({'coin': sym.replace('USDT',''), 'type': '抄底', 'chg': chg, 'pos': position, 'vol': volume})
        elif position > 80 or chg > 5:  # 超买卖出
            opportunities.append({'coin': sym.replace('USDT',''), 'type': '止盈', 'chg': chg, 'pos': position, 'vol': volume})
        
    except: pass
    
    if (i+1) % 100 == 0:
        print(f"  已扫描 {i+1}/{len(symbols)}...")
    
    time.sleep(0.02)  # 避免限流

# 按涨跌幅排序
opportunities.sort(key=lambda x: -abs(x['chg']))

print(f"\n发现 {len(opportunities)} 个机会:\n")
print("="*60)

# Top 20
for i, op in enumerate(opportunities[:20]):
    emoji = "📈" if op['chg'] > 0 else "📉"
    vol = op['vol'] / 1000000
    print(f"{i+1:2d}. {emoji} {op['coin']:10} {op['type']:4} {op['chg']:>+7.2f}% 位置:{op['pos']:>5.1f}% 量:{vol:>6.1f}M")

print("="*60)
PYEOF
