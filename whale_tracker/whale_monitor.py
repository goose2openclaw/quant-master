"""
Whale Tracker - 加密货币巨鲸追踪
"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class WhaleTransaction:
    timestamp: float
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    amount_usd: float
    token: str

class WhaleTracker:
    """
    巨鲸追踪
    监控大额转账和聪明钱
    """
    def __init__(self):
        self.transactions = []
        self.whale_addresses = {}  # 已知的鲸鱼地址
        self.exchange_addresses = set()  # 交易所地址
        self.alerts = []
    
    def add_whale_address(self, label: str, address: str):
        """添加鲸鱼地址"""
        self.whale_addresses[address] = label
    
    def add_exchange_address(self, address: str):
        """添加交易所地址"""
        self.exchange_addresses.add(address)
    
    def record_transaction(self, tx: WhaleTransaction):
        """记录交易"""
        self.transactions.append(tx)
        
        # 检查是否是巨鲸
        if tx.amount_usd > 1_000_000:  # 100万以上
            direction = self._classify_movement(tx.from_address, tx.to_address)
            
            self.alerts.append({
                'type': 'WHALE_MOVE',
                'tx_hash': tx.tx_hash,
                'amount_usd': tx.amount_usd,
                'token': tx.token,
                'direction': direction,  # TO_EXCHANGE, FROM_EXCHANGE, BETWEEN_WHALES
                'timestamp': tx.timestamp
            })
    
    def _classify_movement(self, from_addr: str, to_addr: str) -> str:
        """分类转账方向"""
        from_exchange = from_addr in self.exchange_addresses
        to_exchange = to_addr in self.exchange_addresses
        
        if to_exchange and not from_exchange:
            return 'TO_EXCHANGE'  # 可能是卖出
        elif from_exchange and not to_exchange:
            return 'FROM_EXCHANGE'  # 可能是买入
        else:
            return 'BETWEEN_WALLETS'  # 可能是积累
    
    def get_whale_sentiment(self, token: str, window_hours: int = 24) -> Dict:
        """获取鲸鱼情绪"""
        cutoff = time.time() - window_hours * 3600
        recent = [t for t in self.transactions 
                  if t.token == token and t.timestamp > cutoff]
        
        to_exchange = sum(t.amount_usd for t in recent if 
                         self._classify_movement(t.from_address, t.to_address) == 'TO_EXCHANGE')
        from_exchange = sum(t.amount_usd for t in recent if 
                           self._classify_movement(t.from_address, t.to_address) == 'FROM_EXCHANGE')
        
        return {
            'token': token,
            'window_hours': window_hours,
            'total_whale_volume': sum(t.amount_usd for t in recent),
            'to_exchange_flow': to_exchange,
            'from_exchange_flow': from_exchange,
            'net_flow': from_exchange - to_exchange,
            'sentiment': 'BULLISH' if from_exchange > to_exchange * 1.5 else
                        'BEARISH' if to_exchange > from_exchange * 1.5 else 'NEUTRAL'
        }
    
    def find_ accumulation_zones(self, token: str) -> List[Dict]:
        """寻找积累区间"""
        # 简化: 基于最近成交价格分布
        recent = [t for t in self.transactions if t.token == token]
        
        if len(recent) < 10:
            return []
        
        prices = [t.amount_usd / t.amount for t in recent]
        avg_price = sum(prices) / len(prices)
        
        return [
            {'zone': 'HIGH_ACCUMULATION', 'price_range': (avg_price * 0.95, avg_price * 1.05)},
            {'zone': 'MEDIUM_ACCUMULATION', 'price_range': (avg_price * 0.90, avg_price * 1.10)}
        ]
