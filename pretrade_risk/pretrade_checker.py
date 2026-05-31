"""
Pre-trade Risk - 下单前风险检查
"""
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class RiskCheckResult:
    allowed: bool
    reason: str
    risk_score: float  # 0-100
    warnings: list

class PreTradeRiskChecker:
    """
    下单前风控检查
    全面检查订单风险
    """
    def __init__(self):
        # 风控参数
        self.max_order_value = 10000      # 单笔最大金额
        self.max_position_pct = 0.2        # 单持仓最大比例
        self.max_daily_trades = 100         # 日交易次数上限
        self.max_daily_loss_pct = 0.05     # 日最大亏损比例
        self.blocked_symbols = set()         # 禁止交易的标的
        self.price_deviation_limit = 0.05   # 价格偏离限制
        
        # 统计
        self.daily_trades = 0
        self.daily_loss = 0
        self.daily_start_equity = 0
    
    def check_order(self, order, account, positions, current_price) -> RiskCheckResult:
        """
        检查订单风险
        """
        warnings = []
        risk_score = 0
        
        # 1. 金额检查
        order_value = order.qty * current_price
        if order_value > self.max_order_value:
            return RiskCheckResult(
                allowed=False,
                reason=f"订单金额 ${order_value:.2f} 超过限制 ${self.max_order_value}",
                risk_score=100,
                warnings=[]
            )
        risk_score += min(order_value / self.max_order_value * 30, 30)
        
        # 2. 持仓限制
        symbol = order.symbol
        current_pos = positions.get(symbol, {})
        pos_value = current_pos.get('qty', 0) * current_price
        new_pos_value = pos_value + order_value if order.side == 'BUY' else pos_value - order_value
        pos_pct = new_pos_value / account.get('equity', 1)
        
        if pos_pct > self.max_position_pct:
            return RiskCheckResult(
                allowed=False,
                reason=f"持仓比例 {pos_pct*100:.1f}% 超过限制 {self.max_position_pct*100:.1f}%",
                risk_score=100,
                warnings=[]
            )
        risk_score += min(pos_pct / self.max_position_pct * 25, 25)
        
        # 3. 价格偏离检查
        if current_pos:
            avg_price = current_pos.get('avg_price', current_price)
            deviation = abs(current_price - avg_price) / avg_price
            if deviation > self.price_deviation_limit:
                warnings.append(f"价格偏离 {(deviation-0.05)*100:.1f}%")
                risk_score += 20
        
        # 4. 黑名单检查
        if symbol in self.blocked_symbols:
            return RiskCheckResult(
                allowed=False,
                reason=f"{symbol} 在禁止交易名单",
                risk_score=100,
                warnings=[]
            )
        
        # 5. 日交易次数检查
        if self.daily_trades >= self.max_daily_trades:
            return RiskCheckResult(
                allowed=False,
                reason=f"日交易次数 {self.daily_trades} 达到上限",
                risk_score=100,
                warnings=[]
            )
        risk_score += self.daily_trades / self.max_daily_trades * 15
        
        # 6. 亏损检查
        if self.daily_loss < -account.get('equity', 1) * self.max_daily_loss_pct:
            return RiskCheckResult(
                allowed=False,
                reason=f"日亏损超过 {self.max_daily_loss_pct*100:.1f}%",
                risk_score=100,
                warnings=[]
            )
        risk_score += min(abs(self.daily_loss) / (account.get('equity', 1) * self.max_daily_loss_pct) * 10, 10)
        
        # 7. 关联交易检查 (同标的同向短时间内重复下单)
        # 简化: 通过时间窗口检查
        
        allowed = risk_score < 70
        
        return RiskCheckResult(
            allowed=allowed,
            reason="通过" if allowed else f"风险评分 {risk_score:.0f} 过高",
            risk_score=risk_score,
            warnings=warnings
        )
    
    def add_blocked_symbol(self, symbol):
        self.blocked_symbols.add(symbol)
    
    def remove_blocked_symbol(self, symbol):
        self.blocked_symbols.discard(symbol)
    
    def set_limits(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def reset_daily(self):
        self.daily_trades = 0
        self.daily_loss = 0
    
    def on_trade(self, trade):
        self.daily_trades += 1
        self.daily_loss += trade.get('pnl', 0)
