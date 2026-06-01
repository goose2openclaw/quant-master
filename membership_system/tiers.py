"""
分级会员体系
Tiers: Free → Bronze → Silver → Gold → Platinum → VIP → SVIP
"""
import sys, time
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class TierConfig:
    name: str
    level: int
    min_deposit: float
    max_daily_trades: int
    max_position_size: float
    leverage: int
    fee_discount: float
    api_access: bool
    features: List[str]
    monthly_fee: float

TIERS = {
    'FREE': TierConfig('Free', 0, 0, 3, 100, 1, 0.0, False,
        ['basic_signals', 'paper_trading'], 0),
    'BRONZE': TierConfig('Bronze', 1, 100, 10, 500, 2, 0.05, False,
        ['basic_signals', 'paper_trading', 'alerts'], 9.99),
    'SILVER': TierConfig('Silver', 2, 500, 50, 2000, 3, 0.15, True,
        ['basic_signals', 'alerts', 'backtest', 'prediction'], 29.99),
    'GOLD': TierConfig('Gold', 3, 2000, 200, 10000, 5, 0.25, True,
        ['all_silver', 'auto_trading', 'multi_strategy'], 79.99),
    'PLATINUM': TierConfig('Platinum', 4, 10000, 500, 50000, 10, 0.40, True,
        ['all_gold', 'api_access', 'custom_strategies'], 199.99),
    'VIP': TierConfig('VIP', 5, 50000, 2000, 250000, 20, 0.60, True,
        ['all_platinum', 'dedicated_support', 'whale_tracking'], 499.99),
    'SVIP': TierConfig('SVIP', 6, 200000, -1, -1, 50, 0.80, True,
        ['all_vip', 'institutional_api', '定制服务', '专属经理'], 999.99),
}

@dataclass
class Member:
    user_id: str
    username: str
    tier: str
    deposit_total: float
    trading_volume_30d: float
    join_date: float
    last_active: float
    referrals: int
    bonus_balance: float
    used_features: List[str] = field(default_factory=list)

class MembershipSystem:
    """
    分级会员管理系统
    """
    
    def __init__(self):
        self.members: Dict[str, Member] = {}
        self.tier_thresholds = {
            'BRONZE': {'deposit': 100, 'volume': 1000},
            'SILVER': {'deposit': 500, 'volume': 5000},
            'GOLD': {'deposit': 2000, 'volume': 20000},
            'PLATINUM': {'deposit': 10000, 'volume': 100000},
            'VIP': {'deposit': 50000, 'volume': 500000},
            'SVIP': {'deposit': 200000, 'volume': 2000000},
        }
    
    def register_member(self, user_id: str, username: str) -> Member:
        """注册新会员"""
        member = Member(
            user_id=user_id,
            username=username,
            tier='FREE',
            deposit_total=0,
            trading_volume_30d=0,
            join_date=time.time(),
            last_active=time.time(),
            referrals=0,
            bonus_balance=0
        )
        self.members[user_id] = member
        return member
    
    def get_member(self, user_id: str) -> Optional[Member]:
        return self.members.get(user_id)
    
    def deposit(self, user_id: str, amount: float) -> Member:
        """入金"""
        if user_id not in self.members:
            self.register_member(user_id, f"user_{user_id}")
        
        member = self.members[user_id]
        member.deposit_total += amount
        member.last_active = time.time()
        self._check_tier_upgrade(member)
        return member
    
    def add_trading_volume(self, user_id: str, volume: float):
        """增加交易量"""
        if user_id in self.members:
            self.members[user_id].trading_volume_30d += volume
            self._check_tier_upgrade(self.members[user_id])
    
    def _check_tier_upgrade(self, member: Member):
        """检查是否升级"""
        current_level = TIERS[member.tier].level
        
        for tier_name in sorted(TIERS.keys(), key=lambda x: TIERS[x].level, reverse=True):
            if TIERS[tier_name].level <= current_level:
                continue
            
            thresh = self.tier_thresholds.get(tier_name, {})
            deposit_ok = member.deposit_total >= thresh.get('deposit', float('inf'))
            volume_ok = member.trading_volume_30d >= thresh.get('volume', float('inf'))
            
            if deposit_ok or volume_ok:
                member.tier = tier_name
                break
    
    def check_permission(self, user_id: str, feature: str) -> bool:
        """检查功能权限"""
        if user_id not in self.members:
            return feature in TIERS['FREE'].features
        
        member = self.members[user_id]
        tier_config = TIERS[member.tier]
        
        if feature in tier_config.features:
            return True
        
        if 'all_' in feature:
            base_tier = feature.replace('all_', '').upper()
            if TIERS[member.tier].level >= TIERS.get(base_tier, TIERS['FREE']).level:
                return True
        
        return False
    
    def get_member_status(self, user_id: str) -> Dict:
        """获取会员状态"""
        member = self.get_member(user_id)
        if not member:
            return {'error': 'Member not found'}
        
        tier = TIERS[member.tier]
        next_tier = self._get_next_tier(member.tier)
        
        return {
            'user_id': member.user_id,
            'username': member.username,
            'tier': member.tier,
            'level': tier.level,
            'deposit_total': member.deposit_total,
            'trading_volume_30d': member.trading_volume_30d,
            'join_date': member.join_date,
            'last_active': member.last_active,
            'referrals': member.referrals,
            'bonus_balance': member.bonus_balance,
            'max_daily_trades': tier.max_daily_trades,
            'max_position_size': tier.max_position_size,
            'leverage': tier.leverage,
            'fee_discount': tier.fee_discount,
            'next_tier': next_tier,
            'progress': self._get_tier_progress(member)
        }
    
    def _get_next_tier(self, current_tier: str) -> Optional[str]:
        tiers_sorted = sorted(TIERS.keys(), key=lambda x: TIERS[x].level)
        idx = tiers_sorted.index(current_tier)
        if idx < len(tiers_sorted) - 1:
            return tiers_sorted[idx + 1]
        return None
    
    def _get_tier_progress(self, member: Member) -> float:
        next_tier = self._get_next_tier(member.tier)
        if not next_tier:
            return 100.0
        
        thresh = self.tier_thresholds.get(next_tier, {})
        deposit_req = thresh.get('deposit', 0)
        
        if deposit_req == 0:
            return 100.0
        
        progress = min(100, (member.deposit_total / deposit_req) * 100)
        return progress

if __name__ == '__main__':
    ms = MembershipSystem()
    
    # Test members
    ms.deposit('user001', 150)
    ms.deposit('user002', 2500)
    ms.add_trading_volume('user002', 30000)
    
    for uid in ['user001', 'user002']:
        status = ms.get_member_status(uid)
        print(f"\n{status['username']} ({status['tier']}):")
        print(f"  Deposit: ${status['deposit_total']}")
        print(f"  30d Volume: ${status['trading_volume_30d']}")
        print(f"  Progress: {status['progress']:.1f}%")
        print(f"  Next Tier: {status['next_tier']}")
