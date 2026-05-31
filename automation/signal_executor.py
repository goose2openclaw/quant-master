"""
信号自动执行器
信号 → 下单 全自动化
"""
import time
from threading import Thread, Lock
from datetime import datetime, timedelta

class ExecutionRule:
    """执行规则"""
    def __init__(self, name, strategy_name, symbols, actions):
        self.name = name
        self.strategy_name = strategy_name
        self.symbols = symbols  # 允许的交易对
        self.actions = actions  # BUY, SELL, CLOSE
        self.enabled = True
        self.max_qty_pct = 0.1  # 最大仓位比例
        self.max_orders_per_day = 10
        self.daily_orders = 0
        self.last_reset = datetime.now()
    
    def check(self, symbol, action):
        if not self.enabled:
            return False, "规则已禁用"
        
        if symbol not in self.symbols:
            return False, f"{symbol} 不在规则中"
        
        if action not in self.actions:
            return False, f"{action} 不在允许列表"
        
        # 日订单限制
        now = datetime.now()
        if (now - self.last_reset) > timedelta(days=1):
            self.daily_orders = 0
            self.last_reset = now
        
        if self.daily_orders >= self.max_orders_per_day:
            return False, f"日订单超限 ({self.daily_orders}/{self.max_orders_per_day})"
        
        return True, None
    
    def on_executed(self):
        self.daily_orders += 1

class SignalExecutor:
    """
    信号自动执行器
    完整流程: 接收信号 → 风控检查 → 下单 → 记录 → 回报
    """
    def __init__(self, order_manager, risk_manager):
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.rules = {}  # {strategy_name: ExecutionRule}
        self.signal_buffer = []
        self.executed_trades = []
        self.pending_signals = []
        self.running = False
        self.lock = Lock()
        self.thread = None
        
        # 配置
        self.auto_execute = True
        self.confirmation_required = False
        self.max_slippage_pct = 1.0
    
    def add_rule(self, rule):
        self.rules[rule.strategy_name] = rule
        print(f"[Executor] 添加规则: {rule.name}")
    
    def enable_auto_execute(self):
        self.auto_execute = True
        if not self.running:
            self.start()
    
    def disable_auto_execute(self):
        self.auto_execute = False
    
    def receive_signal(self, signal):
        """接收信号"""
        with self.lock:
            # 规则检查
            rule = self.rules.get(signal.source)
            if rule:
                allowed, reason = rule.check(signal.symbol, signal.action)
                if not allowed:
                    print(f"[Executor] 信号被拦截: {reason}")
                    return {'accepted': False, 'reason': reason}
            
            self.pending_signals.append({
                'signal': signal,
                'received_at': datetime.now().isoformat(),
                'status': 'pending'
            })
            
            if self.auto_execute:
                return self._execute_signal(signal)
            else:
                return {'accepted': True, 'status': 'waiting_confirmation'}
    
    def _execute_signal(self, signal):
        """执行信号"""
        try:
            # 下单
            result = self.order_manager.send_order(
                symbol=signal.symbol,
                side=signal.action,
                qty=signal.qty,
                price=signal.price if signal.price else None
            )
            
            if result.get('success'):
                # 更新规则计数
                rule = self.rules.get(signal.source)
                if rule:
                    rule.on_executed()
                
                # 记录
                trade = {
                    'signal_id': signal.id,
                    'symbol': signal.symbol,
                    'action': signal.action,
                    'qty': signal.qty,
                    'price': result.get('price', signal.price),
                    'order_id': result.get('order_id'),
                    'executed_at': datetime.now().isoformat(),
                    'status': 'executed'
                }
                self.executed_trades.append(trade)
                
                return {'accepted': True, 'status': 'executed', 'trade': trade}
            else:
                return {'accepted': True, 'status': 'failed', 'error': result.get('msg')}
        
        except Exception as e:
            return {'accepted': True, 'status': 'error', 'error': str(e)}
    
    def start(self):
        self.running = True
        self.thread = Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        print("[Executor] 启动")
    
    def stop(self):
        self.running = False
        print("[Executor] 停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 检查待处理信号
                with self.lock:
                    for item in self.pending_signals[:]:
                        if item['status'] == 'pending' and self.auto_execute:
                            result = self._execute_signal(item['signal'])
                            item['status'] = result.get('status')
                            item['result'] = result
                
                time.sleep(1)
            except Exception as e:
                print(f"[Executor] Monitor error: {e}")
                time.sleep(5)
    
    def get_status(self):
        return {
            'running': self.running,
            'auto_execute': self.auto_execute,
            'pending_signals': len(self.pending_signals),
            'executed_today': len([t for t in self.executed_trades if datetime.now().strftime('%Y-%m-%d') in t['executed_at']]),
            'total_executed': len(self.executed_trades)
        }
    
    def get_executed_trades(self, limit=50):
        return self.executed_trades[-limit:]
