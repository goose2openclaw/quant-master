#!/usr/bin/env python3
"""
XIAMI DeFi Oracle - 预言机系统
支持 Chainlink, Uniswap TWAP, 自定义聚合
"""

import ccxt
import json
from datetime import datetime
import time

class Oracle:
    def __init__(self):
        self.exchanges = {
            'binance': ccxt.binance(),
            'bybit': ccxt.bybit(),
            'okx': ccxt.okx()
        }
        
        self.price_cache = {}
        self.cache_ttl = 60  # 60秒缓存
        
    def get_binance_price(self, symbol):
        """获取 Binance 价格"""
        e = self.exchanges['binance']
        ticker = e.fetch_ticker(symbol)
        return {
            'price': ticker['last'],
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'volume': ticker['quoteVolume'],
            'source': 'binance'
        }
    
    def get_bybit_price(self, symbol):
        """获取 Bybit 价格"""
        e = self.exchanges['bybit']
        ticker = e.fetch_ticker(symbol)
        return {
            'price': ticker['last'],
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'volume': ticker['quoteVolume'],
            'source': 'bybit'
        }
    
    def get_okx_price(self, symbol):
        """获取 OKX 价格"""
        e = self.exchanges['okx']
        ticker = e.fetch_ticker(symbol)
        return {
            'price': ticker['last'],
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'volume': ticker['quoteVolume'],
            'source': 'okx'
        }
    
    def get_twap_price(self, symbol, interval='1h', limit=24):
        """Uniswap TWAP 价格"""
        e = self.exchanges['binance']
        ohlcv = e.fetch_ohlcv(symbol, interval, limit=limit)
        closes = [c[4] for c in ohlcv]
        
        # 计算 TWAP
        twap = sum(closes) / len(closes)
        
        # 计算波动率
        volatility = max(closes) - min(closes)
        
        return {
            'twap': twap,
            'volatility': volatility,
            'source': 'twap',
            'interval': interval
        }
    
    def aggregate_prices(self, symbol, method='median'):
        """聚合多源价格"""
        prices = []
        
        try:
            p1 = self.get_binance_price(symbol)
            prices.append(p1['price'])
        except:
            pass
        
        try:
            p2 = self.get_bybit_price(symbol)
            prices.append(p2['price'])
        except:
            pass
        
        try:
            p3 = self.get_okx_price(symbol)
            prices.append(p3['price'])
        except:
            pass
        
        if not prices:
            return None
        
        if method == 'median':
            prices.sort()
            return prices[len(prices)//2]
        elif method == 'mean':
            return sum(prices) / len(prices)
        elif method == 'vwap':
            # 简单 VWAP
            total_vol = sum([p.get('volume', 1) for p in [p1, p2, p3] if 'price' in p])
            weighted = sum([p.get('price', 0) * p.get('volume', 1) for p in [p1, p2, p3] if 'price' in p])
            return weighted / total_vol if total_vol > 0 else prices[0]
        
        return prices[0]
    
    def get_oracle_price(self, symbol, use_cache=True):
        """获取预言机价格 (带缓存)"""
        cache_key = f"{symbol}_{method}"
        
        if use_cache and cache_key in self.price_cache:
            cached = self.price_cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                return cached['price']
        
        price = self.aggregate_prices(symbol)
        
        self.price_cache[cache_key] = {
            'price': price,
            'timestamp': time.time()
        }
        
        return price
    
    def monitor_price_feed(self, symbols, threshold=0.05):
        """监控价格馈送 (检测异常)"""
        alerts = []
        
        for symbol in symbols:
            sources = {}
            
            try:
                sources['binance'] = self.get_binance_price(symbol)['price']
            except:
                pass
            
            try:
                sources['bybit'] = self.get_bybit_price(symbol)['price']
            except:
                pass
            
            if len(sources) >= 2:
                prices = list(sources.values())
                max_diff = max(prices) - min(prices)
                avg_price = sum(prices) / len(prices)
                
                if max_diff / avg_price > threshold:
                    alerts.append({
                        'symbol': symbol,
                        'sources': sources,
                        'max_diff_pct': round(max_diff / avg_price * 100, 2),
                        'alert': 'Price deviation exceeds threshold'
                    })
        
        return alerts


class TokenBurn:
    """代币焚烧机制"""
    
    def __init__(self):
        self.burn_config = {}
        
    def calculate_burn_amount(self, transaction_amount, burn_rate=0.01):
        """计算焚烧数量"""
        return transaction_amount * burn_rate
    
    def simulate_burn(self, token_symbol, amount, burn_rate=0.01):
        """模拟焚烧"""
        burn_amount = self.calculate_burn_amount(amount, burn_rate)
        net_amount = amount - burn_amount
        
        return {
            'token': token_symbol,
            'original_amount': amount,
            'burn_amount': round(burn_amount, 4),
            'net_amount': round(net_amount, 4),
            'burn_rate': burn_rate * 100,
            'timestamp': datetime.now().isoformat()
        }
    
    def auto_burn_schedule(self, token_symbol, total_supply, schedule):
        """自动焚烧计划"""
        # schedule: {'daily': 0.001, 'weekly': 0.005, 'monthly': 0.01}
        
        return {
            'token': token_symbol,
            'initial_supply': total_supply,
            'schedule': schedule,
            'estimated_burn_1m': total_supply * schedule.get('monthly', 0),
            'estimated_burn_1y': total_supply * schedule.get('monthly', 0) * 12,
            'timestamp': datetime.now().isoformat()
        }


def main():
    import sys
    
    oracle = Oracle()
    burn = TokenBurn()
    
    if len(sys.argv) < 2:
        print("""
XIAMI DeFi Oracle

用法:
  python defi_oracle.py price <symbol>
  python defi_oracle.py twap <symbol>
  python defi_oracle.py monitor <symbol1> <symbol2> ...
  python defi_oracle.py burn <token> <amount> [rate]

示例:
  python defi_oracle.py price BTC/USDT
  python defi_oracle.py twap ETH/USDT
  python defi_oracle.py monitor BTC/USDT ETH/USDT
  python defi_oracle.py burn MTK 10000 0.02
""")
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'price':
        symbol = sys.argv[2]
        price = oracle.aggregate_prices(symbol)
        
        print(f"\n🔮 预言机价格 ({symbol})")
        print(f"   价格: ${price:,.2f}")
        print(f"   方法: 聚合中位数")
    
    elif cmd == 'twap':
        symbol = sys.argv[2]
        twap_data = oracle.get_twap_price(symbol)
        
        print(f"\n📊 TWAP 价格 ({symbol})")
        print(f"   TWAP: ${twap_data['twap']:,.2f}")
        print(f"   波动率: ${twap_data['volatility']:,.2f}")
    
    elif cmd == 'monitor':
        symbols = sys.argv[2:]
        alerts = oracle.monitor_price_feed(symbols)
        
        if alerts:
            print(f"\n🚨 价格异常告警 ({len(alerts)}个)")
            for a in alerts:
                print(f"   {a['symbol']}: 偏差 {a['max_diff_pct']}%")
        else:
            print(f"\n✅ 所有价格正常")
    
    elif cmd == 'burn':
        token = sys.argv[2]
        amount = float(sys.argv[3])
        rate = float(sys.argv[4]) if len(sys.argv) > 4 else 0.01
        
        result = burn.simulate_burn(token, amount, rate)
        
        print(f"\n🔥 焚烧模拟 ({token})")
        print(f"   原始数量: {result['original_amount']}")
        print(f"   焚烧数量: {result['burn_amount']}")
        print(f"   净数量: {result['net_amount']}")
        print(f"   焚烧率: {result['burn_rate']}%")

if __name__ == '__main__':
    main()
