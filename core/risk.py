"""
风控管理器 - QMT核心功能 + vnpy风控
"""

class RiskRule:
    """风控规则"""
    def __init__(self, name, check_func):
        self.name = name
        self.check_func = check_func
        self.enabled = True

class RiskManager:
    """
    风控管理 - QMT完整风控体系
    """
    def __init__(self):
        self.rules = []
        self.enabled = True
        self.daily_trades = 0
        self.daily_buy = 0
        self.daily_sell = 0
        self.max_daily_trades = 100
        self.max_position_pct = 0.1  # 单持仓最大10%
        self.max_loss_pct = 0.05    # 日最大亏损5%
    
    def add_rule(self, rule):
        """添加风控规则"""
        self.rules.append(rule)
        print(f"[RiskManager] 已添加规则: {rule.name}")
    
    def check_order(self, order, account, positions):
        """
        订单风控检查 - QMT核心
        返回: (allowed, reason)
        """
        if not self.enabled:
            return True, None
        
        # 规则1: 日交易次数限制
        if self.daily_trades >= self.max_daily_trades:
            return False, f"日交易次数超限({self.daily_trades}/{self.max_daily_trades})"
        
        # 规则2: 单持仓比例限制
        position_value = positions.get(order.symbol, {}).get('value', 0)
        account_value = account.get('total', 1)
        position_pct = position_value / account_value if account_value > 0 else 0
        
        if order.side == 'BUY':
            new_pct = (position_value + order.qty * order.price) / account_value
            if new_pct > self.max_position_pct:
                return False, f"持仓比例超限({new_pct*100:.1f}%>{self.max_position_pct*100:.1f}%)"
        
        # 规则3: 自定义规则
        for rule in self.rules:
            if rule.enabled:
                allowed, reason = rule.check_func(order, account, positions)
                if not allowed:
                    return False, reason
        
        return True, None
    
    def on_trade(self, trade):
        """成交回调"""
        self.daily_trades += 1
        if trade['side'] == 'BUY':
            self.daily_buy += 1
        else:
            self.daily_sell += 1
    
    def reset_daily(self):
        """重置日统计"""
        self.daily_trades = 0
        self.daily_buy = 0
        self.daily_sell = 0
    
    def get_status(self):
        """获取风控状态"""
        return {
            'daily_trades': self.daily_trades,
            'daily_buy': self.daily_buy,
            'daily_sell': self.daily_sell,
            'enabled': self.enabled
        }
