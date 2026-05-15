#!/usr/bin/env python3
"""
go-liquidation - 清算地图预测引擎
"""
import math, json, urllib.request
from datetime import datetime

PROXY = "http://172.29.144.1:7897"

def api_get(url):
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=5).read().decode())
    except: return None

class LiquidationPredictor:
    """清算预测"""
    
    def __init__(self):
        self.funding_cache = {}
    
    def predict(self, coin, entry_price, position_type='long', leverage=1):
        """预测清算价格"""
        if position_type == 'long':
            liquidation_price = entry_price * (1 - 0.8 / leverage)
        else:
            liquidation_price = entry_price * (1 + 0.8 / leverage)
        
        # 获取当前价格
        try:
            current_price = float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={coin}USDT')['price'])
        except:
            current_price = entry_price
        
        distance_pct = abs(current_price - liquidation_price) / current_price * 100
        
        if distance_pct < 5:
            danger = 'EXTREME'
        elif distance_pct < 10:
            danger = 'HIGH'
        elif distance_pct < 20:
            danger = 'MEDIUM'
        else:
            danger = 'LOW'
        
        return {
            'liquidation_price': liquidation_price,
            'current_price': current_price,
            'distance_pct': distance_pct,
            'danger_level': danger,
            'position_type': position_type,
            'leverage': leverage,
            'confidence': 0.8 if distance_pct > 10 else 0.6
        }
    
    def get_funding_rate(self, coin):
        """获取资金费率"""
        cache_key = f"{coin}_funding"
        if cache_key in self.funding_cache:
            return self.funding_cache[cache_key]
        
        try:
            data = api_get(f'https://api.binance.com/fapi/v1/fundingRate?symbol={coin}USDT&limit=1')
            if data:
                funding = float(data[0]['fundingRate'])
                self.funding_cache[cache_key] = funding
                return funding
        except:
            pass
        return 0.0001
    
    def analyze_full(self, coin, entry_price, position_type='long', leverage=1):
        """完整清算分析"""
        pred = self.predict(coin, entry_price, position_type, leverage)
        funding = self.get_funding_rate(coin)
        
        # 8小时资金费率影响
        funding_impact = funding * leverage * 3  # 3个周期
        
        return {
            **pred,
            'funding_rate': funding,
            'funding_impact_pct': funding_impact * 100,
            'net_liquidation_distance': pred['distance_pct'] - funding_impact * 100
        }
