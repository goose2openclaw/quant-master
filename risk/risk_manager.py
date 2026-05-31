"""
风控管理器 - VAR、止损止盈、风险敞口
"""
import numpy as np
from datetime import datetime, timedelta
from collections import deque

class VaR:
    """Value at Risk 计算"""
    def __init__(self, confidence=0.95, horizon=1):
        self.confidence = confidence
        self.horizon = horizon  # 天
        self.returns = deque(maxlen=252)  # 一年日收益
    
    def update(self, return_value):
        self.returns.append(return_value)
    
    def calculate(self):
        """计算VAR"""
        if len(self.returns) < 30:
            return 0
        arr = np.array(list(self.returns))
        percentile = (1 - self.confidence) * 100
        var = np.percentile(arr, percentile) * np.sqrt(self.horizon)
        return abs(var)
    
    def expected_shortfall(self):
        """Expected Shortfall (CVAR)"""
        if len(self.returns) < 30:
            return 0
        var = self.calculate()
        arr = np.array(list(self.returns))
        return abs(np.mean(arr[arr <= -var]))

class StopLoss:
    """止损管理器"""
    def __init__(self):
        self.stops = {}  # {symbol: {'entry': price, 'stop_loss': price, 'take_profit': price}}
    
    def set_stop(self, symbol, entry_price, stop_loss_pct=2, take_profit_pct=6):
        """设置止损止盈"""
        self.stops[symbol] = {
            'entry': entry_price,
            'stop_loss': entry_price * (1 - stop_loss_pct/100),
            'take_profit': entry_price * (1 + take_profit_pct/100),
            'stop_loss_pct': stop_loss_pct,
            'take_profit_pct': take_profit_pct
        }
    
    def check_stop(self, symbol, current_price):
        """检查是否触发止损"""
        if symbol not in self.stops:
            return None
        
        stop = self.stops[symbol]
        
        # 止损
        if current_price <= stop['stop_loss']:
            del self.stops[symbol]
            return {'action': 'STOP_LOSS', 'price': stop['stop_loss'], 'pnl_pct': -stop['stop_loss_pct']}
        
        # 止盈
        if current_price >= stop['take_profit']:
            del self.stops[symbol]
            return {'action': 'TAKE_PROFIT', 'price': stop['take_profit'], 'pnl_pct': stop['take_profit_pct']}
        
        return None
    
    def trailing_stop(self, symbol, current_price, trail_pct=1.5):
        """移动止损"""
        if symbol not in self.stops:
            return None
        
        stop = self.stops[symbol]
        peak_price = stop.get('peak', stop['entry'])
        
        # 更新峰值
        if current_price > peak_price:
            stop['peak'] = current_price
            stop['trail_stop'] = current_price * (1 - trail_pct/100)
            return None
        
        # 检查移动止损
        if 'trail_stop' in stop and current_price <= stop['trail_stop']:
            pnl_pct = (current_price - stop['entry']) / stop['entry'] * 100
            del self.stops[symbol]
            return {'action': 'TRAILING_STOP', 'price': current_price, 'pnl_pct': pnl_pct}
        
        return None
    
    def remove(self, symbol):
        if symbol in self.stops:
            del self.stops[symbol]

class RiskManager:
    """
    完整风控系统
    """
    def __init__(self):
        # 风控参数
        self.max_position_pct = 0.1      # 单持仓最大比例
        self.max_total_leverage = 3      # 最大总杠杆
        self.max_daily_loss_pct = 5      # 日最大亏损比例
        self.max_var_pct = 10            # 最大VAR
        
        # 状态
        self.daily_pnl = 0
        self.daily_trades = 0
        self.daily_start_equity = 0
        self.var = VaR(confidence=0.95)
        self.stop_loss = StopLoss()
        self.risk_events = []
        self.blocked_symbols = set()
    
    def set_daily_start(self, equity):
        self.daily_start_equity = equity
    
    def check_position(self, symbol, qty, price, total_equity):
        """检查仓位是否合规"""
        position_value = qty * price
        position_pct = position_value / total_equity if total_equity > 0 else 0
        
        # 单持仓限制
        if position_pct > self.max_position_pct:
            self.risk_events.append({
                'time': datetime.now().isoformat(),
                'type': 'POSITION_LIMIT',
                'symbol': symbol,
                'pct': position_pct * 100
            })
            return False, f"持仓比例超限 {position_pct*100:.1f}% > {self.max_position_pct*100:.1f}%"
        
        # 黑名单
        if symbol in self.blocked_symbols:
            return False, f"{symbol} 在黑名单中"
        
        return True, None
    
    def check_daily_loss(self, current_equity):
        """检查日亏损"""
        if self.daily_start_equity == 0:
            return True
        
        daily_loss_pct = (self.daily_start_equity - current_equity) / self.daily_start_equity * 100
        
        if daily_loss_pct > self.max_daily_loss_pct:
            self.risk_events.append({
                'time': datetime.now().isoformat(),
                'type': 'DAILY_LOSS_LIMIT',
                'loss_pct': daily_loss_pct
            })
            return False, f"日亏损超限 {daily_loss_pct:.1f}% > {self.max_daily_loss_pct}%"
        
        return True, None
    
    def check_var(self, position_value):
        """检查VAR风险"""
        var = self.var.calculate()
        if var > self.max_var_pct / 100:
            self.risk_events.append({
                'time': datetime.now().isoformat(),
                'type': 'VAR_LIMIT',
                'var': var * 100
            })
            return False, f"VAR超限 {var*100:.1f}% > {self.max_var_pct}%"
        return True, None
    
    def add_to_blacklist(self, symbol, reason=""):
        """加入黑名单"""
        self.blocked_symbols.add(symbol)
        self.risk_events.append({
            'time': datetime.now().isoformat(),
            'type': 'BLACKLIST',
            'symbol': symbol,
            'reason': reason
        })
    
    def remove_from_blacklist(self, symbol):
        self.blocked_symbols.discard(symbol)
    
    def on_trade(self, trade):
        """成交回调"""
        self.daily_trades += 1
        self.daily_pnl += trade.get('pnl', 0)
        
        # 更新VAR
        ret = trade.get('return', 0)
        if ret != 0:
            self.var.update(ret)
    
    def reset_daily(self):
        """重置日统计"""
        self.daily_pnl = 0
        self.daily_trades = 0
    
    def get_risk_status(self):
        """获取风控状态"""
        return {
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'var': self.var.calculate() * 100 if hasattr(self.var, 'calculate') else 0,
            'blocked_symbols': list(self.blocked_symbols),
            'risk_events_count': len(self.risk_events),
            'recent_events': self.risk_events[-5:] if self.risk_events else []
        }
