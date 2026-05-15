#!/usr/bin/env python3
"""
go-orderbook - 实时订单簿分析引擎
"""
import math, json, urllib.request, time
from datetime import datetime

PROXY = "http://172.29.144.1:7897"

def api_get(url):
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=5).read().decode())
    except: return None

class OrderbookAnalyzer:
    """订单簿分析"""
    
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_ttl = 5  # 5秒
    
    def get_depth(self, symbol, limit=20):
        """获取订单簿深度"""
        cache_key = f"{symbol}_depth"
        now = time.time()
        
        if cache_key in self.cache and now - self.cache_time.get(cache_key, 0) < self.cache_ttl:
            return self.cache[cache_key]
        
        data = api_get(f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}')
        if not data:
            return self._default()
        
        bids = [[float(p), float(q)] for p, q in data.get('bids', [])]
        asks = [[float(p), float(q)] for p, q in data.get('asks', [])]
        
        result = {
            'bid_total': sum(q for _, q in bids),
            'ask_total': sum(q for _, q in asks),
            'bid_density': sum(q for _, q in bids[:5]) / 5,
            'ask_density': sum(q for _, q in asks[:5]) / 5,
            'imbalance': (sum(q for _, q in bids) - sum(q for _, q in asks)) / (sum(q for _, q in bids) + sum(q for _, q in asks) + 1e-10),
            'spread': (asks[0][0] - bids[0][0]) / bids[0][0] if bids and asks else 0,
            'bids': bids[:10],
            'asks': asks[:10]
        }
        
        self.cache[cache_key] = result
        self.cache_time[cache_key] = now
        return result
    
    def analyze(self, coin, limit=20):
        """分析订单簿"""
        symbol = f"{coin}USDT"
        depth = self.get_depth(symbol, limit)
        
        # 大单检测 (超过平均5倍)
        large_bids = [q for p, q in depth['bids'] if q > depth['bid_density'] * 5]
        large_asks = [q for p, q in depth['asks'] if q > depth['ask_density'] * 5]
        
        # 支撑阻力墙
        bid_walls = [p for p, q in depth['bids'] if q > depth['bid_density'] * 10]
        ask_walls = [p for p, q in depth['asks'] if q > depth['ask_density'] * 10]
        
        # 信号
        if depth['imbalance'] > 0.3:
            signal = 'bullish'
        elif depth['imbalance'] < -0.3:
            signal = 'bearish'
        else:
            signal = 'neutral'
        
        return {
            'symbol': symbol,
            'signal': signal,
            'imbalance': depth['imbalance'],
            'spread_pct': depth['spread'] * 100,
            'bid_density': depth['bid_density'],
            'ask_density': depth['ask_density'],
            'large_bid_count': len(large_bids),
            'large_ask_count': len(large_asks),
            'bid_walls': bid_walls[:3],
            'ask_walls': ask_walls[:3],
            'confidence': min(abs(depth['imbalance']) + 0.3, 1.0)
        }
    
    def _default(self):
        return {
            'bid_total': 0, 'ask_total': 0, 'bid_density': 0, 'ask_density': 0,
            'imbalance': 0, 'spread': 0, 'bids': [], 'asks': []
        }
