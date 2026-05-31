"""
Auction Scheduler - 荷兰式拍卖调度
"""
from typing import Dict

class AuctionScheduler:
    """
    荷兰式拍卖调度
    从高价开始递减直到成交
    """
    def __init__(self):
        self.auctions = {}
    
    def create_auction(self, item_id: str, start_price: float, 
                      min_price: float, duration_sec: int) -> Dict:
        """创建拍卖"""
        auction_id = f"AUCTION_{item_id}"
        
        self.auctions[auction_id] = {
            'auction_id': auction_id,
            'item_id': item_id,
            'start_price': start_price,
            'min_price': min_price,
            'current_price': start_price,
            'duration_sec': duration_sec,
            'start_time': __import__('time').time(),
            'status': 'ACTIVE'
        }
        
        return self.auctions[auction_id]
    
    def get_current_price(self, auction_id: str) -> float:
        """获取当前价格"""
        auction = self.auctions.get(auction_id)
        if not auction:
            return 0
        
        elapsed = __import__('time').time() - auction['start_time']
        progress = elapsed / auction['duration_sec']
        
        price_range = auction['start_price'] - auction['min_price']
        current_price = auction['start_price'] - (price_range * progress)
        
        return max(auction['min_price'], current_price)
    
    def place_bid(self, auction_id: str, bidder: str, price: float) -> Dict:
        """竞拍"""
        current = self.get_current_price(auction_id)
        
        if price >= current:
            return {
                'auction_id': auction_id,
                'bidder': bidder,
                'price': price,
                'status': 'WON',
                'auction_end': __import__('time').time()
            }
        
        return {'status': 'REJECTED', 'reason': 'Price too low'}
