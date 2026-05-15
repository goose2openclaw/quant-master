#!/usr/bin/env python3
"""
go-cross-exchange - 跨交易所套利引擎
"""
import math, json, urllib.request, time
from datetime import datetime

PROXY = "http://172.29.144.1:7897"

EXCHANGES = {
    'binance': 'https://api.binance.com',
    'okx': 'https://www.okx.com/api/v5',
    'bybit': 'https://api.bybit.com',
    'gate': 'https://api.gateio.tv'
}

def api_get(url):
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=5).read().decode())
    except: return None

class CrossExchangeAnalyzer:
    """跨交易所分析"""
    
    def __init__(self):
        self.price_cache = {}
        self.cache_ttl = 3
    
    def get_price(self, exchange, coin):
        """获取单个交易所价格"""
        cache_key = f"{exchange}_{coin}"
        now = time.time()
        
        if cache_key in self.price_cache and now - self.price_cache.get(f"{cache_key}_time", 0) < self.cache_ttl:
            return self.price_cache[cache_key]
        
        try:
            if exchange == 'binance':
                data = api_get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin}USDT")
                price = float(data['price']) if data else None
            elif exchange == 'okx':
                data = api_get(f"https://www.okx.com/api/v5/market/ticker?instId={coin}-USDT")
                price = float(data['data'][0]['last']) if data and data.get('data') else None
            elif exchange == 'bybit':
                data = api_get(f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={coin}USDT")
                price = float(data['list'][0]['lastPrice']) if data and data.get('list') else None
            elif exchange == 'gate':
                data = api_get(f"https://api.gateio.tv/api/v4/spot/tickers?currency_pair={coin}_USDT")
                price = float(data[0]['last']) if data and data else None
            else:
                price = None
            
            if price:
                self.price_cache[cache_key] = price
                self.price_cache[f"{cache_key}_time"] = now
            return price
        except:
            return None
    
    def get_all_prices(self, coin):
        """获取所有交易所价格"""
        prices = {}
        for exchange in EXCHANGES:
            p = self.get_price(exchange, coin)
            if p:
                prices[exchange] = p
        
        if not prices:
            return {'error': 'No prices available'}
        
        price_list = list(prices.values())
        avg_price = sum(price_list) / len(price_list)
        max_price = max(price_list)
        min_price = min(price_list)
        spread_pct = (max_price - min_price) / avg_price * 100
        
        return {
            'prices': prices,
            'average': avg_price,
            'max': max_price,
            'min': min_price,
            'spread_pct': spread_pct,
            'arbitrage_opportunity': spread_pct > 0.1,  # >0.1% 价差
            'best_buy': min(prices, key=prices.get),
            'best_sell': max(prices, key=prices.get)
        }
    
    def analyze_triangular(self, coins=['BTC', 'ETH', 'USDT']):
        """三角套利分析 (简化版)"""
        # 实际需要完整的交易对数据
        return {'opportunity': False, 'profit_pct': 0}
