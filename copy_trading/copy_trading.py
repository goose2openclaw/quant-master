"""
跟单交易系统 - 跟随高手策略
"""
import time, json
from datetime import datetime
from threading import Thread, Lock

class SignalProvider:
    """信号提供者"""
    def __init__(self, id, name, strategy_type, win_rate=0, total_trades=0):
        self.id = id
        self.name = name
        self.strategy_type = strategy_type
        self.win_rate = win_rate
        self.total_trades = total_trades
        self.followers = 0
        self.total_aum = 0  # 管理资产
        self.performance = []  # 历史表现
        self.subscribers = []  # 订阅者
        self.is_active = True
        self.min_follow_amount = 100  # 最低跟单金额
    
    def add_performance(self, pnl_pct, equity):
        self.performance.append({
            'time': datetime.now().isoformat(),
            'pnl_pct': pnl_pct,
            'equity': equity
        })
        self.performance = self.performance[-100:]  # 保留最近100条
    
    def get_stats(self):
        if not self.performance:
            return {'win_rate': 0, 'avg_pnl': 0, 'max_drawdown': 0}
        
        pnls = [p['pnl_pct'] for p in self.performance]
        wins = [p for p in pnls if p > 0]
        
        peak = self.performance[0]['equity']
        max_dd = 0
        for p in self.performance:
            if p['equity'] > peak:
                peak = p['equity']
            dd = (peak - p['equity']) / peak * 100
            max_dd = max(max_dd, dd)
        
        return {
            'win_rate': len(wins) / len(pnls) * 100 if pnls else 0,
            'avg_pnl': sum(pnls) / len(pnls) if pnls else 0,
            'max_drawdown': max_dd,
            'total_trades': self.total_trades,
            'followers': self.followers,
            'aum': self.total_aum
        }

class Follower:
    """跟单者"""
    def __init__(self, id, name, capital, provider_id, copy_ratio=1.0):
        self.id = id
        self.name = name
        self.capital = capital
        self.provider_id = provider_id
        self.copy_ratio = copy_ratio  # 复制比例
        self.allocated_capital = capital * copy_ratio
        self.positions = {}
        self.trades = []
        self.pnl = 0
        self.is_active = True

class CopyTradingSystem:
    """
    跟单交易系统
    完整功能: 信号提供者管理、跟单分配、盈亏分摊
    """
    def __init__(self):
        self.providers = {}  # {id: SignalProvider}
        self.followers = {}  # {id: Follower}
        self.trades = []    # 跟单交易记录
        self.pending_orders = []
        self.running = False
        self.lock = Lock()
        self.commission_rate = 0.05  # 平台佣金 5%
        self.profit_share = 0.20     # 利润分成 20%
    
    def register_provider(self, name, strategy_type):
        """注册信号提供者"""
        provider_id = f"PRO_{len(self.providers) + 1:04d}"
        provider = SignalProvider(provider_id, name, strategy_type)
        self.providers[provider_id] = provider
        print(f"[CopyTrading] 注册提供者: {name} ({provider_id})")
        return provider_id
    
    def register_follower(self, name, capital, provider_id, copy_ratio=1.0):
        """注册跟单者"""
        if provider_id not in self.providers:
            return None
        
        follower_id = f"FOL_{len(self.followers) + 1:04d}"
        follower = Follower(follower_id, name, capital, provider_id, copy_ratio)
        self.followers[follower_id] = follower
        
        # 更新提供者
        provider = self.providers[provider_id]
        provider.followers += 1
        provider.total_aum += follower.allocated_capital
        
        print(f"[CopyTrading] {name} 跟单 {provider.name}, 金额 ${capital}")
        return follower_id
    
    def execute_signal(self, provider_id, symbol, side, qty, price, reason=""):
        """执行信号"""
        provider = self.providers.get(provider_id)
        if not provider or not provider.is_active:
            return []
        
        executed_trades = []
        
        with self.lock:
            for follower_id, follower in self.followers.items():
                if follower.provider_id != provider_id or not follower.is_active:
                    continue
                
                # 检查跟单金额
                if follower.allocated_capital < provider.min_follow_amount:
                    continue
                
                # 计算跟单数量
                copy_qty = qty * follower.copy_ratio * (follower.allocated_capital / provider.total_aum)
                copy_qty = max(copy_qty, 0.0001)  # 最小下单量
                
                # 下单
                trade = {
                    'time': datetime.now().isoformat(),
                    'provider_id': provider_id,
                    'follower_id': follower_id,
                    'symbol': symbol,
                    'side': side,
                    'qty': copy_qty,
                    'price': price,
                    'provider_signal': reason,
                    'status': 'executed'
                }
                
                self.trades.append(trade)
                executed_trades.append(trade)
                
                # 更新跟单者持仓
                if symbol not in follower.positions:
                    follower.positions[symbol] = {'qty': 0, 'avg_price': 0}
                
                pos = follower.positions[symbol]
                if side == 'BUY':
                    cost = pos['qty'] * pos['avg_price'] + copy_qty * price
                    pos['qty'] += copy_qty
                    pos['avg_price'] = cost / pos['qty'] if pos['qty'] > 0 else 0
                else:
                    pos['qty'] -= copy_qty
                    if pos['qty'] <= 0:
                        del follower.positions[symbol]
        
        # 更新提供者交易数
        provider.total_trades += 1
        
        return executed_trades
    
    def sync_positions(self, provider_id, positions):
        """同步持仓"""
        provider = self.providers.get(provider_id)
        if not provider:
            return
        
        with self.lock:
            for follower_id, follower in self.followers.items():
                if follower.provider_id != provider_id or not follower.is_active:
                    continue
                
                # 同步持仓
                for sym, pos in positions.items():
                    if sym not in follower.positions:
                        follower.positions[sym] = {'qty': 0, 'avg_price': pos['avg_price']}
                    
                    fol_pos = follower.positions[sym]
                    ratio = follower.allocated_capital / provider.total_aum
                    
                    # 调整持仓
                    target_qty = pos['qty'] * ratio
                    diff = target_qty - fol_pos['qty']
                    
                    if abs(diff) > 0.0001:
                        # 需要调仓
                        pass  # 实际执行由订单系统处理
    
    def calculate_pnl(self, follower_id):
        """计算跟单者盈亏"""
        follower = self.followers.get(follower_id)
        if not follower:
            return 0
        
        provider = self.providers.get(follower.provider_id)
        if not provider or not provider.performance:
            return 0
        
        # 按提供者的表现计算
        latest_perf = provider.performance[-1]
        follower_pnl = (latest_perf['pnl_pct'] / 100) * follower.capital
        
        # 扣除分成
        if follower_pnl > 0:
            follower_pnl = follower_pnl * (1 - self.profit_share)
        
        follower.pnl = follower_pnl
        return follower_pnl
    
    def get_provider_ranking(self):
        """获取提供者排名"""
        providers = list(self.providers.values())
        rankings = []
        
        for p in providers:
            stats = p.get_stats()
            rankings.append({
                'id': p.id,
                'name': p.name,
                'strategy': p.strategy_type,
                'win_rate': stats['win_rate'],
                'avg_pnl': stats['avg_pnl'],
                'max_drawdown': stats['max_drawdown'],
                'followers': stats['followers'],
                'aum': stats['aum']
            })
        
        # 按综合评分排序
        rankings.sort(key=lambda x: (
            x['win_rate'] * 0.3 + 
            x['avg_pnl'] * 0.4 - 
            x['max_drawdown'] * 0.3
        ), reverse=True)
        
        return rankings
    
    def get_follower_portfolio(self, follower_id):
        """获取跟单者组合"""
        follower = self.followers.get(follower_id)
        if not follower:
            return None
        
        return {
            'id': follower.id,
            'name': follower.name,
            'capital': follower.capital,
            'allocated': follower.allocated_capital,
            'positions': follower.positions,
            'pnl': follower.pnl,
            'provider': self.providers.get(follower.provider_id, {}).name if follower.provider_id else None
        }
