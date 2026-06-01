"""
Portfolio Dashboard - 财产总览
多账户卡片/盈亏统计/资产分布
"""
import sys
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class AccountCard:
    account_id: str
    name: str
    account_type: str  # EXCHANGE/WALLET/STRATEGY
    balance: float
    pnl_day: float
    pnl_day_pct: float
    pnl_total: float
    pnl_total_pct: float
    allocation_pct: float
    status: str  # ACTIVE/PAUSED/CLOSED
    color: str  # UI color

class PortfolioDashboard:
    """
    资产组合仪表板
    - 多账户卡片
    - 盈亏追踪
    - 资产分布
    """
    
    def __init__(self):
        self.name = "Portfolio Dashboard"
        self.accounts: Dict[str, AccountCard] = {}
    
    def add_account(self, name: str, balance: float, 
                   account_type: str = 'EXCHANGE',
                   color: str = '#4A90D9') -> AccountCard:
        """添加账户"""
        account_id = f"ACC_{name.upper()[:4]}"
        
        account = AccountCard(
            account_id=account_id,
            name=name,
            account_type=account_type,
            balance=balance,
            pnl_day=0,
            pnl_day_pct=0,
            pnl_total=0,
            pnl_total_pct=0,
            allocation_pct=0,
            status='ACTIVE',
            color=color
        )
        
        self.accounts[account_id] = account
        self._recalculate_allocations()
        return account
    
    def update_pnl(self, account_id: str, price_change_pct: float):
        """更新盈亏"""
        if account_id not in self.accounts:
            return
        
        account = self.accounts[account_id]
        
        # 日盈亏
        account.pnl_day = account.balance * price_change_pct / 100
        account.pnl_day_pct = price_change_pct
        
        # 总盈亏 (假设初始投资为余额的80%)
        initial = account.balance * 0.8
        if initial > 0:
            account.pnl_total = account.balance - initial
            account.pnl_total_pct = (account.balance - initial) / initial * 100
    
    def _recalculate_allocations(self):
        """重新计算分配比例"""
        total = self.get_total_balance()
        
        if total <= 0:
            return
        
        for account in self.accounts.values():
            account.allocation_pct = account.balance / total * 100
    
    def get_total_balance(self) -> float:
        """获取总余额"""
        return sum(a.balance for a in self.accounts.values())
    
    def get_total_pnl_day(self) -> float:
        """获取日盈亏总额"""
        return sum(a.pnl_day for a in self.accounts.values())
    
    def get_total_pnl_day_pct(self) -> float:
        """获取日盈亏百分比"""
        total = self.get_total_balance()
        if total <= 0:
            return 0
        return self.get_total_pnl_day() / total * 100
    
    def get_portfolio_summary(self) -> Dict:
        """获取组合摘要"""
        total = self.get_total_balance()
        total_pnl_day = self.get_total_pnl_day()
        total_pnl_day_pct = self.get_total_pnl_day_pct()
        
        # 按余额排序
        sorted_accounts = sorted(
            self.accounts.values(),
            key=lambda x: x.balance,
            reverse=True
        )
        
        return {
            'total_balance': total,
            'total_pnl_day': total_pnl_day,
            'total_pnl_day_pct': total_pnl_day_pct,
            'account_count': len(self.accounts),
            'active_accounts': sum(1 for a in self.accounts.values() if a.status == 'ACTIVE'),
            'accounts': [{
                'id': a.account_id,
                'name': a.name,
                'balance': a.balance,
                'pnl_day': a.pnl_day,
                'pnl_day_pct': a.pnl_day_pct,
                'allocation': a.allocation_pct,
                'status': a.status,
                'color': a.color
            } for a in sorted_accounts],
            'timestamp': time.time()
        }
    
    def get_allocation_chart(self) -> List[Dict]:
        """获取分配图表数据"""
        summary = self.get_portfolio_summary()
        
        return [{
            'name': a['name'],
            'value': a['balance'],
            'percentage': a['allocation'],
            'color': self.accounts[f"ACC_{a['name'].upper()[:4]}"].color
        } for a in summary['accounts']]
    
    def simulate_daily_update(self):
        """模拟每日更新"""
        for account in self.accounts.values():
            # 随机价格变动
            change_pct = random.uniform(-5, 5)
            self.update_pnl(account.account_id, change_pct)
    
    def get_top_performers(self, limit: int = 3) -> List[AccountCard]:
        """获取最佳表现账户"""
        return sorted(
            self.accounts.values(),
            key=lambda x: x.pnl_day_pct,
            reverse=True
        )[:limit]
    
    def get_worst_performers(self, limit: int = 3) -> List[AccountCard]:
        """获取最差表现账户"""
        return sorted(
            self.accounts.values(),
            key=lambda x: x.pnl_day_pct
        )[:limit]

if __name__ == '__main__':
    dash = PortfolioDashboard()
    
    print("=== Portfolio Dashboard ===\n")
    
    # 添加账户 (像描述中的Benne/Bona/zen/axe)
    dash.add_account('Benne', 10000, 'EXCHANGE', '#4A90D9')
    dash.add_account('Bona', 25000, 'EXCHANGE', '#50C878')
    dash.add_account('zen', 15000, 'STRATEGY', '#9B59B6')
    dash.add_account('axe', 15000, 'WALLET', '#E74C3C')
    dash.add_account('Vault', 858, 'WALLET', '#F39C12')
    dash.add_account('Reserve', 255, 'WALLET', '#1ABC9C')
    
    # 模拟更新
    dash.simulate_daily_update()
    
    # 组合摘要
    summary = dash.get_portfolio_summary()
    
    print(f"Total Balance: ${summary['total_balance']:,.2f}")
    print(f"Day P&L: ${summary['total_pnl_day']:+.2f} ({summary['total_pnl_day_pct']:+.2f}%)")
    print(f"\nAccounts:")
    
    for acc in summary['accounts']:
        pnl_emoji = '🟢' if acc['pnl_day'] >= 0 else '🔴'
        print(f"  {acc['name']:10} ${acc['balance']:>10,.2f} {pnl_emoji} {acc['pnl_day']:+>10.2f} ({acc['pnl_day_pct']:+.1f}%)  {acc['allocation']:>5.1f}%")
    
    # Top performers
    print("\nTop Performers:")
    for acc in dash.get_top_performers():
        print(f"  {acc.name}: {acc.pnl_day_pct:+.1f}%")
    
    # Allocation chart
    print("\nAllocation:")
    for item in dash.get_allocation_chart():
        bar = '█' * int(item['percentage'] / 5)
        print(f"  {item['name']:10} {bar:20} {item['percentage']:.1f}%")
