"""
Liquidations Tracking - 强制平仓追踪
"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class LiquidationEvent:
    timestamp: float
    symbol: str
    side: str  # LONG/SHORT
    size: float  # USD value
    price: float

class LiquidationTracker:
    """
    强平追踪
    检测多空挤压
    """
    def __init__(self):
        self.events = []
        self.thresholds = {
            'whale': 1_000_000,  # 100万以上
            'cluster': 5_000_000,  # 集群
            'cascade': 10_000_000  # 级联
        }
    
    def record_liquidation(self, symbol: str, side: str, size: float, price: float):
        """记录强平事件"""
        event = LiquidationEvent(
            timestamp=time.time(),
            symbol=symbol,
            side=side,
            size=size,
            price=price
        )
        self.events.append(event)
        
        # 检查是否是鲸鱼
        if size > self.thresholds['whale']:
            self.alerts.append({
                'type': 'WHALE_LIQUIDATION',
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price
            })
    
    def detect_squeeze(self, symbol: str, window_minutes: int = 60) -> Dict:
        """检测多空挤压"""
        cutoff = time.time() - window_minutes * 60
        recent = [e for e in self.events if e.symbol == symbol and e.timestamp > cutoff]
        
        long_liq = sum(e.size for e in recent if e.side == 'LONG')
        short_liq = sum(e.size for e in recent if e.side == 'SHORT')
        
        total = long_liq + short_liq
        
        return {
            'symbol': symbol,
            'window_minutes': window_minutes,
            'long_liquidations': long_liq,
            'short_liquidations': short_liq,
            'total_liquidations': total,
            'dominance': 'LONG' if long_liq > short_liq * 1.5 else
                        'SHORT' if short_liq > long_liq * 1.5 else 'BALANCED',
            'squeeze_score': abs(long_liq - short_liq) / total if total > 0 else 0,
            'cascade_risk': 'HIGH' if total > self.thresholds['cascade'] else
                           'MEDIUM' if total > self.thresholds['cluster'] else 'LOW'
        }
    
    def find_liquidation_walls(self, symbol: str, price_levels: int = 20) -> List[Dict]:
        """寻找强平墙"""
        # 简化: 生成假想的强平墙
        walls = []
        base_price = 65000
        
        for i in range(1, price_levels + 1):
            up_price = base_price * (1 + i * 0.005)
            down_price = base_price * (1 - i * 0.005)
            walls.append({
                'level': i,
                'up_wall_price': up_price,
                'up_wall_size': 50_000_000 * i,  # 逐级增加
                'down_wall_price': down_price,
                'down_wall_size': 50_000_000 * i
            })
        
        return walls
