#!/usr/bin/env python3
"""
G23 Meme币全景扫描器
====================
功能:
1. CoinGecko搜索所有meme相关币
2. Binance搜索meme交易对
3. 按市值/热度/趋势排序
4. 筛选有真实交易量的币种
5. 输出可交易信号
"""
import urllib.request, json, numpy as np
from datetime import datetime

PROXY = "http://172.29.144.1:7897"

def api(url):
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=15)
        return json.loads(resp.read().decode())
    except: return {}

def coingecko_price(ids):
    """获取CoinGecko价格数据"""
    if not ids: return {}
    ids_str = ','.join(ids[:100])  # 限制100个
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usdt&include_market_cap=true&include_24hr_vol=true"
    return api(url)

def binance_price(symbol):
    """获取Binance价格"""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    data = api(url)
    if 'price' in data:
        return float(data['price'])
    return 0

def binance_24hr(symbol):
    """获取Binance 24小时数据"""
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    return api(url)

def main():
    print("=" * 80)
    print("G23 Meme币全景扫描器")
    print("=" * 80)
    
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] 扫描中...\n")
    
    # 1. CoinGecko Meme币搜索
    print("[1] CoinGecko搜索meme币...")
    cg_data = api("https://api.coingecko.com/api/v3/search?query=meme")
    cg_coins = cg_data.get('coins', [])[:50]  # 前50个
    
    print(f"    找到 {len(cg_coins)} 个meme币")
    
    # 2. 获取价格和市值
    print("\n[2] 获取实时价格...")
    coin_ids = [c['id'] for c in cg_coins]
    prices = coingecko_price(coin_ids)
    
    # 3. 收集Binance可交易的币
    print("\n[3] 筛选Binance可交易币种...")
    
    meme_opportunities = []
    
    for coin in cg_coins:
        symbol = coin.get('symbol', '').upper()
        name = coin.get('name', '')
        coin_id = coin.get('id', '')
        
        # 尝试Binance交易对
        binance_symbols = [
            f"{symbol}USDT",
            f"{symbol}BTC", 
            f"{symbol}BNB"
        ]
        
        for bs in binance_symbols:
            price_data = binance_24hr(bs)
            if 'symbol' in price_data:
                current_price = float(price_data.get('lastPrice', 0))
                volume = float(price_data.get('quoteVolume', 0))
                price_change = float(price_data.get('priceChangePercent', 0))
                
                if volume > 10000:  # 24小时成交量>$10k
                    cg_price = prices.get(coin_id, {}).get('usdt', 0)
                    
                    meme_opportunities.append({
                        'symbol': symbol,
                        'name': name,
                        'binance_pair': bs,
                        'price': current_price,
                        'volume': volume,
                        'change_24h': price_change,
                        'market_cap': coin.get('market_cap', 0),
                        'thumb': coin.get('thumb', '')
                    })
                    break  # 找到一个交易对就停止
    
    # 4. 按成交量排序
    meme_opportunities.sort(key=lambda x: x['volume'], reverse=True)
    
    # 5. 显示结果
    print(f"\n[4] 发现 {len(meme_opportunities)} 个可交易的Meme币\n")
    
    if meme_opportunities:
        print(f"{'排名':>4} {'币种':12} {'名称':25} {'价格':>15} {'24h成交量':>15} {'24h涨跌':>10}")
        print("-" * 85)
        
        for i, m in enumerate(meme_opportunities[:30], 1):
            emoji = "🟢" if m['change_24h'] > 0 else "🔴" if m['change_24h'] < 0 else "⚪"
            print(f"{i:>4} {emoji} {m['symbol']:10} {m['name'][:25]:25} ${m['price']:>14.6f} ${m['volume']:>14,.0f} {m['change_24h']:>+9.2f}%")
        
        # 6. 信号分析
        print("\n[5] 信号分析")
        print("-" * 50)
        
        hot_meme = [m for m in meme_opportunities if m['change_24h'] > 10 and m['volume'] > 100000]
        if hot_meme:
            print(f"\n🔥 热门Meme (涨幅>10% 且 成交量>$100k):")
            for m in hot_meme[:5]:
                print(f"   {m['symbol']}: {m['change_24h']:+.1f}% 成交量${m['volume']/1000:.1f}k")
        
        volume_leaders = meme_opportunities[:5]
        print(f"\n📊 成交量排行 (可能有主力关注):")
        for m in volume_leaders:
            print(f"   {m['symbol']}: ${m['volume']/1000000:.2f}M 成交量")
    
    else:
        print("未发现可交易的Meme币")
    
    print("\n" + "=" * 80)
    return meme_opportunities

if __name__ == '__main__':
    main()
