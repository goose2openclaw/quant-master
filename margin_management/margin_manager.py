"""
Margin/Collateral Management - 保证金管理
跨保证金模式
"""
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class MarginPosition:
    symbol: str
    qty: float
    entry_price: float
    leverage: float
    margin_used: float
    unrealized_pnl: float
    liquidation_price: float

class MarginManager:
    """
    保证金管理系统
    支持: 逐仓/全仓/跨保证金
    """
    def __init__(self):
        self.positions = {}  # {symbol: MarginPosition}
        self.total_equity = 0
        self.available_margin = 0
        self.used_margin = 0
        self.margin_ratio = 0  # 保证金率
        self.liquidation_ratio = 0.8  # 强平比例
        
        # 维持保证金率
        self.maintenance_margin_rate = 0.005  # 0.5%
    
    def open_position(self, symbol, qty, entry_price, leverage, margin_mode='ISOLATED'):
        """开仓"""
        margin_required = qty * entry_price / leverage
        
        if margin_required > self.available_margin:
            return {'success': False, 'error': 'Insufficient margin'}
        
        position = MarginPosition(
            symbol=symbol,
            qty=qty,
            entry_price=entry_price,
            leverage=leverage,
            margin_used=margin_required,
            unrealized_pnl=0,
            liquidation_price=self._calc_liquidation(entry_price, leverage, 'LONG' if qty > 0 else 'SHORT')
        )
        
        self.positions[symbol] = position
        self._update_margin()
        
        return {'success': True, 'position': position}
    
    def close_position(self, symbol, qty=None, close_price=None):
        """平仓"""
        pos = self.positions.get(symbol)
        if not pos:
            return {'success': False, 'error': 'Position not found'}
        
        close_qty = qty or abs(pos.qty)
        close_pr = close_price or pos.entry_price
        
        # 计算盈亏
        if pos.qty > 0:  # 多头
            pnl = (close_pr - pos.entry_price) * close_qty
        else:  # 空头
            pnl = (pos.entry_price - close_pr) * close_qty
        
        # 释放保证金
        released_margin = pos.margin_used * (close_qty / abs(pos.qty))
        
        # 更新持仓
        if qty and abs(qty) < abs(pos.qty):
            pos.qty -= qty
            pos.margin_used -= released_margin
        else:
            del self.positions[symbol]
        
        self._update_margin()
        
        return {
            'success': True,
            'pnl': pnl,
            'released_margin': released_margin
        }
    
    def add_margin(self, symbol, amount):
        """追加保证金"""
        pos = self.positions.get(symbol)
        if not pos:
            return {'success': False, 'error': 'Position not found'}
        
        pos.margin_used += amount
        pos.liquidation_price = self._calc_liquidation(pos.entry_price, pos.leverage, 'LONG' if pos.qty > 0 else 'SHORT')
        
        self._update_margin()
        return {'success': True}
    
    def get_margin_ratio(self, symbol):
        """获取保证金率"""
        pos = self.positions.get(symbol)
        if not pos:
            return 0
        
        if pos.unrealized_pnl >= 0:
            effective_margin = pos.margin_used + pos.unrealized_pnl
        else:
            effective_margin = pos.margin_used + pos.unrealized_pnl
        
        position_value = abs(pos.qty * pos.entry_price)
        
        if position_value == 0:
            return 0
        
        return effective_margin / position_value
    
    def check_liquidation(self, symbol, current_price):
        """检查是否触发强平"""
        pos = self.positions.get(symbol)
        if not pos:
            return False
        
        # 计算未实现盈亏
        if pos.qty > 0:
            pos.unrealized_pnl = (current_price - pos.entry_price) * pos.qty
        else:
            pos.unrealized_pnl = (pos.entry_price - current_price) * abs(pos.qty)
        
        # 检查强平
        margin_ratio = self.get_margin_ratio(symbol)
        
        if margin_ratio <= self.maintenance_margin_rate:
            return True
        
        if current_price <= pos.liquidation_price:
            return True
        
        return False
    
    def liquidate_position(self, symbol, current_price):
        """执行强平"""
        pos = self.positions.get(symbol)
        if not pos:
            return None
        
        result = self.close_position(symbol, close_price=current_price)
        result['liquidation'] = True
        return result
    
    def cross_margin_transfer(self, amount):
        """跨保证金转账"""
        if amount > 0:  # 转入
            if amount <= self.available_margin:
                self.total_equity += amount
                self._update_margin()
                return {'success': True}
        else:  # 转出
            # 检查转出后是否触发强平
            if self._can_withdraw(-amount):
                self.total_equity += amount  # amount是负数
                self._update_margin()
                return {'success': True}
        return {'success': False, 'error': 'Transfer failed'}
    
    def _calc_liquidation(self, entry_price, leverage, side):
        """计算强平价格"""
        # 逐仓: 强平价 = 开仓价 * (1 - 1/杠杆)
        if side == 'LONG':
            return entry_price * (1 - 1/leverage)
        else:
            return entry_price * (1 + 1/leverage)
    
    def _update_margin(self):
        """更新保证金状态"""
        self.used_margin = sum(p.margin_used for p in self.positions.values())
        self.available_margin = self.total_equity - self.used_margin
        self.margin_ratio = self.used_margin / self.total_equity if self.total_equity > 0 else 0
    
    def _can_withdraw(self, amount):
        """检查是否可以转出"""
        for pos in self.positions.values():
            margin_ratio = (pos.margin_used - amount) / (abs(pos.qty) * pos.entry_price)
            if margin_ratio <= self.maintenance_margin_rate * 1.5:  # 留5%缓冲
                return False
        return True
    
    def get_portfolio_margin(self):
        """获取组合保证金状态"""
        return {
            'total_equity': self.total_equity,
            'used_margin': self.used_margin,
            'available_margin': self.available_margin,
            'margin_ratio': self.margin_ratio,
            'positions': {
                symbol: {
                    'qty': pos.qty,
                    'margin_used': pos.margin_used,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'margin_ratio': self.get_margin_ratio(symbol),
                    'liquidation_price': pos.liquidation_price
                }
                for symbol, pos in self.positions.items()
            }
        }
