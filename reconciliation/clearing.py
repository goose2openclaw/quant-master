"""
Reconciliation & Clearing - 对账清算系统
T+2清算跟踪
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class Trade:
    trade_id: str
    symbol: str
    side: str
    qty: float
    price: float
    value: float
    fee: float
    venue: str
    timestamp: float
    status: str

@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float
    market_value: float
    unrealized_pnl: float

class ReconciliationEngine:
    """
    对账引擎
    交易前后台核对
    """
    def __init__(self):
        self.internal_trades = {}  # 内部记录
        self.external_trades = {}  # 交易所确认
        self.positions_internal = {}  # 内部持仓
        self.positions_external = {}  # 交易所持仓
        self.breaks = []  # 差异记录
        self.clearing_pending = {}  # 待清算交易
    
    def add_internal_trade(self, trade: Trade):
        """添加内部交易"""
        self.internal_trades[trade.trade_id] = trade
        
        # 加入待清算
        self.clearing_pending[trade.trade_id] = {
            'trade': trade,
            'settlement_date': self._calc_settlement_date(trade),
            'status': 'pending'
        }
    
    def add_external_trade(self, trade: Trade):
        """添加交易所确认"""
        self.external_trades[trade.trade_id] = trade
    
    def _calc_settlement_date(self, trade: Trade) -> str:
        """计算结算日期 (T+2)"""
        trade_date = datetime.fromtimestamp(trade.timestamp)
        settlement = trade_date + timedelta(days=2)
        return settlement.strftime('%Y-%m-%d')
    
    def run_reconciliation(self) -> Dict:
        """运行对账"""
        breaks_found = []
        
        # 1. 匹配交易
        for trade_id, internal in self.internal_trades.items():
            external = self.external_trades.get(trade_id)
            
            if not external:
                breaks_found.append({
                    'type': 'MISSING_EXTERNAL',
                    'trade_id': trade_id,
                    'description': '内部有,交易所无'
                })
                continue
            
            # 检查差异
            if abs(internal.qty - external.qty) > 0.0001:
                breaks_found.append({
                    'type': 'QTY_MISMATCH',
                    'trade_id': trade_id,
                    'internal': internal.qty,
                    'external': external.qty,
                    'diff': internal.qty - external.qty
                })
            
            if abs(internal.price - external.price) > 0.01:
                breaks_found.append({
                    'type': 'PRICE_MISMATCH',
                    'trade_id': trade_id,
                    'internal': internal.price,
                    'external': external.price
                })
        
        # 2. 检查缺失
        for trade_id, external in self.external_trades.items():
            if trade_id not in self.internal_trades:
                breaks_found.append({
                    'type': 'MISSING_INTERNAL',
                    'trade_id': trade_id,
                    'description': '交易所有,内部无'
                })
        
        # 3. 持仓核对
        position_breaks = self._reconcile_positions()
        breaks_found.extend(position_breaks)
        
        self.breaks = breaks_found
        
        return {
            'total_internal': len(self.internal_trades),
            'total_external': len(self.external_trades),
            'breaks_count': len(breaks_found),
            'breaks': breaks_found,
            'reconciliation_time': datetime.now().isoformat()
        }
    
    def _reconcile_positions(self) -> List[Dict]:
        """核对持仓"""
        breaks = []
        
        all_symbols = set(self.positions_internal.keys()) | set(self.positions_external.keys())
        
        for symbol in all_symbols:
            internal = self.positions_internal.get(symbol, Position(symbol, 0, 0, 0, 0))
            external = self.positions_external.get(symbol, Position(symbol, 0, 0, 0, 0))
            
            if abs(internal.qty - external.qty) > 0.0001:
                breaks.append({
                    'type': 'POSITION_MISMATCH',
                    'symbol': symbol,
                    'internal_qty': internal.qty,
                    'external_qty': external.qty,
                    'diff': internal.qty - external.qty
                })
        
        return breaks
    
    def process_clearing(self, settlement_date: str) -> Dict:
        """处理清算"""
        to_cleared = []
        
        for trade_id, pending in self.clearing_pending.items():
            if pending['settlement_date'] <= settlement_date:
                pending['status'] = 'cleared'
                to_cleared.append(trade_id)
        
        return {
            'cleared_count': len(to_cleared),
            'cleared_trades': to_cleared,
            'remaining': len(self.clearing_pending) - len(to_cleared)
        }
    
    def generate_break_report(self) -> str:
        """生成差异报告"""
        if not self.breaks:
            return "对账无差异"
        
        report = ["=== 对账差异报告 ==="]
        report.append(f"差异数量: {len(self.breaks)}")
        
        by_type = {}
        for b in self.breaks:
            t = b['type']
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(b)
        
        for btype, items in by_type.items():
            report.append(f"\n{btype}: {len(items)}个")
            for item in items[:5]:
                report.append(f"  {item}")
        
        return '\n'.join(report)

class ClearingHouse:
    """清算所"""
    def __init__(self):
        self.settlements = {}  # 已结算记录
        self.net_positions = {}  # 净持仓
    
    def net_positions(self, trades: List[Trade]) -> Dict[str, float]:
        """计算净持仓"""
        net = {}
        
        for trade in trades:
            if trade.symbol not in net:
                net[trade.symbol] = 0
            
            qty = trade.qty if trade.side in ['buy', 'BUY'] else -trade.qty
            net[trade.symbol] += qty
        
        return net
    
    def calculate_net_value(self, positions: Dict[str, float], prices: Dict[str, float]) -> float:
        """计算净结算价值"""
        total = 0
        for symbol, qty in positions.items():
            price = prices.get(symbol, 0)
            total += qty * price
        return total
    
    def settle(self, trade_id: str, net_amount: float, accounts: Dict[str, float]) -> bool:
        """执行清算"""
        self.settlements[trade_id] = {
            'net_amount': net_amount,
            'accounts': accounts,
            'timestamp': time.time(),
            'status': 'settled'
        }
        return True

class Custodian:
    """托管银行"""
    def __init__(self):
        self.accounts = {}  # 托管账户
        self.holdings = {}  # 托管资产
    
    def hold_assets(self, client_id: str, assets: Dict[str, float]):
        """持有资产"""
        self.holdings[client_id] = assets
    
    def release_assets(self, client_id: str, assets: Dict[str, float]) -> bool:
        """释放资产"""
        if client_id in self.holdings:
            for asset, qty in assets.items():
                if asset in self.holdings[client_id]:
                    self.holdings[client_id][asset] -= qty
            return True
        return False
    
    def get_holdings(self, client_id: str) -> Dict[str, float]:
        """获取托管资产"""
        return self.holdings.get(client_id, {})

class SettlementMonitor:
    """清算监控"""
    def __init__(self):
        self.pending_settlements = {}
        self.settled_settlements = {}
        self.alerts = []
    
    def monitor_settlements(self):
        """监控清算状态"""
        now = time.time()
        alerts = []
        
        for settlement_id, pending in self.pending_settlements.items():
            # 检查超时
            elapsed = now - pending['created']
            if elapsed > 86400:  # 超过24小时
                alerts.append({
                    'type': 'SETTLEMENT_DELAY',
                    'settlement_id': settlement_id,
                    'elapsed_hours': elapsed / 3600
                })
        
        self.alerts = alerts
        return alerts
    
    def get_settlement_status(self) -> Dict:
        """获取清算状态"""
        return {
            'pending': len(self.pending_settlements),
            'settled_today': len(self.settled_settlements),
            'alerts': self.alerts
        }
