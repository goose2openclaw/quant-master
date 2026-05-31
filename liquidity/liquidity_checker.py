"""
流动性检测 - 订单簿深度、市场深度分析
"""
import requests, time
from collections import defaultdict

class OrderBookLevel:
    def __init__(self, price, quantity, orders_count):
        self.price = price
        self.quantity = quantity
        self.orders_count = orders_count

class LiquidityChecker:
    """
    流动性检测器
    功能: 订单簿深度、市场深度、滑点估算、冲击成本
    """
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.order_books = {}  # {symbol: {'bids': [], 'asks': []}}
        self.price_cache = {}
    
    def fetch_order_book(self, symbol, limit=100):
        """获取订单簿"""
        try:
            r = requests.get(
                "https://api.binance.com/api/v3/depth",
                params={'symbol': symbol, 'limit': limit},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                self.order_books[symbol] = {
                    'bids': [(float(p), float(q)) for p, q in data.get('bids', [])],
                    'asks': [(float(p), float(q)) for p, q in data.get('asks', [])],
                    'timestamp': time.time()
                }
                return self.order_books[symbol]
        except Exception as e:
            print(f"[Liquidity] Fetch error: {e}")
        return None
    
    def get_depth(self, symbol, side='both', levels=10):
        """获取深度"""
        book = self.order_books.get(symbol)
        if not book:
            book = self.fetch_order_book(symbol)
            if not book:
                return None
        
        result = {'symbol': symbol}
        
        if side in ['both', 'bid']:
            bids = book['bids'][:levels]
            total_bid = sum(q for _, q in bids)
            result['bid_depth'] = {
                'levels': [{'price': p, 'quantity': q} for p, q in bids],
                'total_quantity': total_bid,
                'weighted_price': sum(p*q for p,q in bids) / total_bid if total_bid > 0 else 0
            }
        
        if side in ['both', 'ask']:
            asks = book['asks'][:levels]
            total_ask = sum(q for _, q in asks)
            result['ask_depth'] = {
                'levels': [{'price': p, 'quantity': q} for p, q in asks],
                'total_quantity': total_ask,
                'weighted_price': sum(p*q for p,q in asks) / total_ask if total_ask > 0 else 0
            }
        
        # 计算买卖价差
        if 'bid' in result and 'ask' in result:
            best_bid = result['bid_depth']['levels'][0]['price']
            best_ask = result['ask_depth']['levels'][0]['price']
            spread = best_ask - best_bid
            spread_pct = spread / best_bid * 100 if best_bid > 0 else 0
            result['spread'] = {'absolute': spread, 'percentage': spread_pct}
        
        return result
    
    def estimate_slippage(self, symbol, side, quantity):
        """估算滑点"""
        book = self.order_books.get(symbol)
        if not book:
            book = self.fetch_order_book(symbol)
            if not book:
                return None
        
        levels = book['asks'] if side == 'BUY' else book['bids']
        
        remaining_qty = quantity
        total_cost = 0
        filled_qty = 0
        
        for price, qty in levels:
            if remaining_qty <= 0:
                break
            fill = min(remaining_qty, qty)
            total_cost += fill * price
            filled_qty += fill
            remaining_qty -= fill
        
        if filled_qty == 0:
            return None
        
        avg_fill_price = total_cost / filled_qty
        best_price = levels[0][0]
        
        slippage = (avg_fill_price - best_price) / best_price * 100
        if side == 'SELL':
            slippage = -slippage
        
        return {
            'side': side,
            'quantity': quantity,
            'filled_quantity': filled_qty,
            'avg_fill_price': avg_fill_price,
            'best_price': best_price,
            'slippage_pct': slippage,
            'execution_rate': filled_qty / quantity * 100 if quantity > 0 else 0
        }
    
    def estimate_market_impact(self, symbol, side, quantity):
        """估算市场冲击"""
        # 简化模型: 冲击 ~ (order_size / ADV)^0.6
        book = self.order_books.get(symbol)
        if not book:
            return None
        
        # 假设每日成交量是订单簿总量的100倍
        levels = book['asks'] if side == 'BUY' else book['bids']
        book_volume = sum(q for _, q in levels[:20])
        adv = book_volume * 100
        
        participation_rate = quantity / adv if adv > 0 else 0
        market_impact = 0.1 * (participation_rate ** 0.6) * 100  # %影响
        
        return {
            'order_size': quantity,
            'estimated_adv': adv,
            'participation_rate': participation_rate * 100,
            'market_impact_pct': market_impact,
            'severity': 'low' if market_impact < 0.5 else ('medium' if market_impact < 2 else 'high')
        }
    
    def get_liquidity_score(self, symbol):
        """获取流动性评分 (0-100)"""
        book = self.fetch_order_book(symbol, limit=50)
        if not book:
            return 0
        
        bid_depth = sum(q for _, q in book['bids'][:10])
        ask_depth = sum(q for _, q in book['asks'][:10])
        
        spread = book['asks'][0][0] - book['bids'][0][0] if book['asks'] and book['bids'] else 0
        mid_price = (book['asks'][0][0] + book['bids'][0][0]) / 2 if book['asks'] and book['bids'] else 0
        spread_pct = spread / mid_price * 100 if mid_price > 0 else 0
        
        # 评分
        depth_score = min((bid_depth + ask_depth) / 1000 * 10, 40)  # 最多40分
        spread_score = max(20 - spread_pct * 10, 0)  # 最多20分
        level_score = min(len(book['bids']) + len(book['asks']), 40)  # 最多40分
        
        return depth_score + spread_score + level_score
    
    def get_execution_quality(self, symbol):
        """获取执行质量评估"""
        score = self.get_liquidity_score(symbol)
        
        if score >= 80:
            quality = 'Excellent'
        elif score >= 60:
            quality = 'Good'
        elif score >= 40:
            quality = 'Fair'
        else:
            quality = 'Poor'
        
        return {
            'symbol': symbol,
            'liquidity_score': score,
            'quality': quality,
            'recommendation': 'Market order recommended' if score >= 60 else 'Limit order recommended'
        }
