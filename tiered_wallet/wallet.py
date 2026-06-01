"""
Tiered Wallet - 多级钱包系统
每个会员等级独立钱包,隔离管理
"""
import sys, time, uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class Wallet:
    wallet_id: str
    user_id: str
    tier: str
    currency: str
    balance: float
    locked: float
    created_at: float
    updated_at: float

@dataclass
class Transaction:
    tx_id: str
    wallet_id: str
    type: str
    amount: float
    balance_before: float
    balance_after: float
    fee: float
    timestamp: float
    description: str

WALLET_LIMITS = {
    'FREE': {'max_balance': 1000, 'daily_withdraw': 100, 'max_transfer': 50},
    'BRONZE': {'max_balance': 5000, 'daily_withdraw': 500, 'max_transfer': 250},
    'SILVER': {'max_balance': 25000, 'daily_withdraw': 2500, 'max_transfer': 1000},
    'GOLD': {'max_balance': 100000, 'daily_withdraw': 10000, 'max_transfer': 5000},
    'PLATINUM': {'max_balance': 500000, 'daily_withdraw': 50000, 'max_transfer': 25000},
    'VIP': {'max_balance': 2000000, 'daily_withdraw': 250000, 'max_transfer': 100000},
    'SVIP': {'max_balance': -1, 'daily_withdraw': -1, 'max_transfer': -1},
}

class TieredWallet:
    """
    分级钱包系统
    - 独立钱包隔离
    - 等级决定额度
    - 实时风控
    """
    
    def __init__(self, membership_system=None):
        self.wallets: Dict[str, Wallet] = {}
        self.transactions: List[Transaction] = []
        self.user_wallets: Dict[str, List[str]] = {}
        self.membership = membership_system
    
    def create_wallet(self, user_id: str, tier: str = 'FREE',
                     currency: str = 'USDT') -> Wallet:
        """创建钱包"""
        wallet_id = f"WALLET_{uuid.uuid4().hex[:12].upper()}"
        
        wallet = Wallet(
            wallet_id=wallet_id,
            user_id=user_id,
            tier=tier,
            currency=currency,
            balance=0,
            locked=0,
            created_at=time.time(),
            updated_at=time.time()
        )
        
        self.wallets[wallet_id] = wallet
        
        if user_id not in self.user_wallets:
            self.user_wallets[user_id] = []
        self.user_wallets[user_id].append(wallet_id)
        
        return wallet
    
    def deposit(self, wallet_id: str, amount: float,
               description: str = '') -> Transaction:
        """入金"""
        if wallet_id not in self.wallets:
            raise ValueError(f"Wallet {wallet_id} not found")
        
        wallet = self.wallets[wallet_id]
        limits = WALLET_LIMITS.get(wallet.tier, WALLET_LIMITS['FREE'])
        
        # 检查额度
        new_balance = wallet.balance + amount
        if limits['max_balance'] > 0 and new_balance > limits['max_balance']:
            raise ValueError(f"Balance limit exceeded: {limits['max_balance']}")
        
        balance_before = wallet.balance
        wallet.balance = new_balance
        wallet.updated_at = time.time()
        
        tx = Transaction(
            tx_id=f"TX_{uuid.uuid4().hex[:12].upper()}",
            wallet_id=wallet_id,
            type='DEPOSIT',
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            fee=0,
            timestamp=time.time(),
            description=description or 'Deposit'
        )
        self.transactions.append(tx)
        return tx
    
    def withdraw(self, wallet_id: str, amount: float,
                description: str = '') -> Transaction:
        """出金"""
        if wallet_id not in self.wallets:
            raise ValueError(f"Wallet {wallet_id} not found")
        
        wallet = self.wallets[wallet_id]
        limits = WALLET_LIMITS.get(wallet.tier, WALLET_LIMITS['FREE'])
        
        # 检查余额
        available = wallet.balance - wallet.locked
        if amount > available:
            raise ValueError(f"Insufficient balance: {available}")
        
        # 检查日限额
        today_start = int(time.time() / 86400) * 86400
        today_withdraw = sum(
            t.amount for t in self.transactions
            if t.wallet_id == wallet_id and t.type == 'WITHDRAW'
            and t.timestamp >= today_start
        )
        
        if limits['daily_withdraw'] > 0:
            if today_withdraw + amount > limits['daily_withdraw']:
                raise ValueError(f"Daily withdrawal limit exceeded: {limits['daily_withdraw']}")
        
        balance_before = wallet.balance
        wallet.balance -= amount
        wallet.updated_at = time.time()
        
        fee = amount * 0.001  # 0.1% fee
        wallet.balance -= fee
        
        tx = Transaction(
            tx_id=f"TX_{uuid.uuid4().hex[:12].upper()}",
            wallet_id=wallet_id,
            type='WITHDRAW',
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            fee=fee,
            timestamp=time.time(),
            description=description or 'Withdrawal'
        )
        self.transactions.append(tx)
        return tx
    
    def transfer(self, from_wallet_id: str, to_wallet_id: str,
                amount: float, description: str = '') -> tuple:
        """转账"""
        if from_wallet_id not in self.wallets or to_wallet_id not in self.wallets:
            raise ValueError("Wallet not found")
        
        from_wallet = self.wallets[from_wallet_id]
        to_wallet = self.wallets[to_wallet_id]
        limits = WALLET_LIMITS.get(from_wallet.tier, WALLET_LIMITS['FREE'])
        
        # 检查限额
        if limits['max_transfer'] > 0 and amount > limits['max_transfer']:
            raise ValueError(f"Transfer limit exceeded: {limits['max_transfer']}")
        
        # 检查余额
        available = from_wallet.balance - from_wallet.locked
        if amount > available:
            raise ValueError(f"Insufficient balance: {available}")
        
        fee = amount * 0.001
        actual_amount = amount - fee
        
        from_balance_before = from_wallet.balance
        from_wallet.balance -= amount
        from_wallet.updated_at = time.time()
        
        to_balance_before = to_wallet.balance
        to_wallet.balance += actual_amount
        to_wallet.updated_at = time.time()
        
        tx_from = Transaction(
            tx_id=f"TX_{uuid.uuid4().hex[:12].upper()}",
            wallet_id=from_wallet_id,
            type='TRANSFER_OUT',
            amount=amount,
            balance_before=from_balance_before,
            balance_after=from_wallet.balance,
            fee=fee,
            timestamp=time.time(),
            description=description or f'Transfer to {to_wallet_id}'
        )
        
        tx_to = Transaction(
            tx_id=f"TX_{uuid.uuid4().hex[:12].upper()}",
            wallet_id=to_wallet_id,
            type='TRANSFER_IN',
            amount=actual_amount,
            balance_before=to_balance_before,
            balance_after=to_wallet.balance,
            fee=0,
            timestamp=time.time(),
            description=description or f'Transfer from {from_wallet_id}'
        )
        
        self.transactions.append(tx_from)
        self.transactions.append(tx_to)
        
        return tx_from, tx_to
    
    def lock_funds(self, wallet_id: str, amount: float) -> bool:
        """锁定资金"""
        if wallet_id not in self.wallets:
            return False
        
        wallet = self.wallets[wallet_id]
        available = wallet.balance - wallet.locked
        
        if amount > available:
            return False
        
        wallet.locked += amount
        wallet.updated_at = time.time()
        return True
    
    def unlock_funds(self, wallet_id: str, amount: float) -> bool:
        """解锁资金"""
        if wallet_id not in self.wallets:
            return False
        
        wallet = self.wallets[wallet_id]
        
        if amount > wallet.locked:
            return False
        
        wallet.locked -= amount
        wallet.updated_at = time.time()
        return True
    
    def get_wallet_status(self, wallet_id: str) -> Dict:
        """获取钱包状态"""
        if wallet_id not in self.wallets:
            return {'error': 'Wallet not found'}
        
        wallet = self.wallets[wallet_id]
        limits = WALLET_LIMITS.get(wallet.tier, WALLET_LIMITS['FREE'])
        
        # 日内已提
        today_start = int(time.time() / 86400) * 86400
        today_withdraw = sum(
            t.amount for t in self.transactions
            if t.wallet_id == wallet_id and t.type == 'WITHDRAW'
            and t.timestamp >= today_start
        )
        
        return {
            'wallet_id': wallet.wallet_id,
            'user_id': wallet.user_id,
            'tier': wallet.tier,
            'currency': wallet.currency,
            'balance': wallet.balance,
            'locked': wallet.locked,
            'available': wallet.balance - wallet.locked,
            'max_balance': limits['max_balance'],
            'daily_withdraw_limit': limits['daily_withdraw'],
            'daily_withdraw_used': today_withdraw,
            'daily_withdraw_remaining': max(0, limits['daily_withdraw'] - today_withdraw) if limits['daily_withdraw'] > 0 else -1,
            'max_transfer': limits['max_transfer'],
            'created_at': wallet.created_at,
            'updated_at': wallet.updated_at
        }
    
    def get_user_portfolio(self, user_id: str) -> Dict:
        """获取用户投资组合"""
        if user_id not in self.user_wallets:
            return {'wallets': [], 'total_balance': 0}
        
        wallets = []
        total = 0
        
        for wid in self.user_wallets[user_id]:
            status = self.get_wallet_status(wid)
            if 'error' not in status:
                wallets.append(status)
                total += status['balance']
        
        return {
            'user_id': user_id,
            'wallets': wallets,
            'total_balance': total,
            'wallet_count': len(wallets)
        }

if __name__ == '__main__':
    from membership_system.tiers import MembershipSystem
    
    ms = MembershipSystem()
    ms.deposit('user001', 500)
    
    wallet = TieredWallet(ms)
    
    # Create wallet for user
    w = wallet.create_wallet('user001', 'BRONZE', 'USDT')
    print(f"Created wallet: {w.wallet_id}")
    
    # Deposit
    tx = wallet.deposit(w.wallet_id, 1000, 'Initial deposit')
    print(f"Deposit: ${tx.amount}, Balance: ${tx.balance_after}")
    
    # Withdraw
    try:
        tx = wallet.withdraw(w.wallet_id, 200)
        print(f"Withdraw: ${tx.amount}, Fee: ${tx.fee}, Balance: ${tx.balance_after}")
    except ValueError as e:
        print(f"Withdraw failed: {e}")
    
    # Status
    status = wallet.get_wallet_status(w.wallet_id)
    print(f"\nWallet Status:")
    print(f"  Tier: {status['tier']}")
    print(f"  Balance: ${status['balance']}")
    print(f"  Available: ${status['available']}")
    print(f"  Daily Withdraw: ${status['daily_withdraw_used']}/${status['daily_withdraw_limit']}")
