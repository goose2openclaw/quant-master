"""
Paper Trading Simulator - 模拟交易系统
实时模拟真实交易环境
"""
import sys, time, random, json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class PaperPosition:
    symbol: str
    side: str
    qty: float
    entry_price: float
    current_price: float
    pnl: float
    entry_time: float
    
@dataclass
class PaperOrder:
    order_id: str
    symbol: str
    side: str
    qty: float
    order_type: str
    price: float
    status: str
    filled_price: float
    filled_time: float

class PaperTradingSimulator:
    """
    模拟交易系统
    完全模拟真实交易所行为
    """
    
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = {}
        self.orders = []
        self.trade_history = []
        self.order_count = 0
        
        # Market simulation
        self.prices = {
            'BTC': 67000, 'ETH': 3500, 'BNB': 580,
            'SOL': 145, 'XRP': 0.52, 'ADA': 0.45,
            'DOGE': 0.12, 'AVAX': 35, 'DOT': 7.2
        }
        
        self.pending_orders = []
        
    def get_balance(self) -> float:
        return self.balance
    
    def get_equity(self) -> float:
        """总权益"""
        position_value = sum(
            p.current_price * p.qty if p.side == 'LONG'
            else 0 for p in self.positions.values()
        )
        return self.balance + position_value
    
    def get_positions(self) -> List[PaperPosition]:
        return list(self.positions.values())
    
    def place_order(self, symbol: str, side: str, qty: float,
                   order_type: str = 'MARKET', price: float = None) -> PaperOrder:
        """下单"""
        self.order_count += 1
        order_id = f"PAPER_{self.order_count}"
        
        # 模拟滑点
        slippage = 0.001 if order_type == 'MARKET' else 0
        fill_price = self.prices.get(symbol, price or 100) * (1 + slippage if side == 'BUY' else 1 - slippage)
        
        order = PaperOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            qty=qty,
            order_type=order_type,
            price=price or self.prices.get(symbol, 100),
            status='FILLED',
            filled_price=fill_price,
            filled_time=time.time()
        )
        
        self.orders.append(order)
        self._execute_order(order)
        
        return order
    
    def _execute_order(self, order: PaperOrder):
        """执行订单"""
        if order.side == 'BUY':
            cost = order.filled_price * order.qty
            if cost <= self.balance:
                self.balance -= cost
                pos_key = f"{order.symbol}_LONG"
                self.positions[pos_key] = PaperPosition(
                    symbol=order.symbol,
                    side='LONG',
                    qty=order.qty,
                    entry_price=order.filled_price,
                    current_price=order.filled_price,
                    pnl=0,
                    entry_time=time.time()
                )
                self.trade_history.append({
                    'time': order.filled_time,
                    'action': 'BUY',
                    'symbol': order.symbol,
                    'qty': order.qty,
                    'price': order.filled_price,
                    'pnl': 0
                })
        
        elif order.side == 'SELL':
            pos_key = f"{order.symbol}_LONG"
            if pos_key in self.positions:
                pos = self.positions[pos_key]
                pnl = (order.filled_price - pos.entry_price) * pos.qty
                self.balance += order.filled_price * order.qty + pnl
                self.trade_history.append({
                    'time': order.filled_time,
                    'action': 'SELL',
                    'symbol': order.symbol,
                    'qty': order.qty,
                    'price': order.filled_price,
                    'pnl': pnl
                })
                del self.positions[pos_key]
    
    def update_prices(self):
        """更新模拟价格"""
        for symbol in self.prices:
            change = random.uniform(-0.02, 0.02)
            self.prices[symbol] *= (1 + change)
            
            # 更新持仓盈亏
            pos_key = f"{symbol}_LONG"
            if pos_key in self.positions:
                pos = self.positions[pos_key]
                pos.current_price = self.prices[symbol]
                pos.pnl = (pos.current_price - pos.entry_price) * pos.qty
    
    def get_performance(self) -> Dict:
        """获取表现统计"""
        total_pnl = sum(t['pnl'] for t in self.trade_history)
        trades = [t for t in self.trade_history if t['action'] == 'SELL']
        wins = [t for t in trades if t['pnl'] > 0]
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_equity': self.get_equity(),
            'total_pnl': total_pnl,
            'pnl_pct': (total_pnl / self.initial_balance) * 100,
            'total_trades': len(trades),
            'win_rate': len(wins) / len(trades) * 100 if trades else 0,
            'open_positions': len(self.positions),
            'current_prices': self.prices.copy()
        }
    
    def run_simulation(self, duration_seconds: int = 60,
                     signal_fn=None):
        """运行模拟交易"""
        print(f"\n{'='*60}")
        print(f"📊 PAPER TRADING SIMULATION")
        print(f"{'='*60}")
        print(f"Initial Balance: ${self.initial_balance:.2f}")
        print(f"Duration: {duration_seconds}s")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        cycle = 0
        
        while time.time() - start_time < duration_seconds:
            cycle += 1
            self.update_prices()
            
            # 模拟信号
            if signal_fn and cycle % 10 == 0:
                signal = signal_fn(self.prices)
                if signal:
                    symbol, side, qty = signal
                    order = self.place_order(symbol, side, qty)
                    print(f"  📝 {side} {qty} {symbol} @ ${order.filled_price:.2f}")
            
            # 输出状态
            if cycle % 5 == 0:
                perf = self.get_performance()
                print(f"\n⏱ {(time.time()-start_time):.0f}s | "
                      f"Equity: ${perf['current_equity']:.2f} | "
                      f"P&L: ${perf['total_pnl']:.2f} | "
                      f"Positions: {perf['open_positions']}")
            
            time.sleep(1)
        
        # 最终报告
        perf = self.get_performance()
        print(f"\n{'='*60}")
        print(f"📊 SIMULATION COMPLETE")
        print(f"{'='*60}")
        print(f"Final Equity: ${perf['current_equity']:.2f}")
        print(f"Total P&L: ${perf['total_pnl']:.2f} ({perf['pnl_pct']:+.2f}%)")
        print(f"Win Rate: {perf['win_rate']:.1f}%")
        print(f"Total Trades: {perf['total_trades']}")
        print(f"{'='*60}\n")
        
        return perf

def simple_signal_generator(prices: Dict) -> Optional[Tuple]:
    """简单信号生成器"""
    signals = []
    
    for symbol, price in prices.items():
        if random.random() < 0.1:  # 10%概率信号
            side = 'BUY' if random.random() > 0.5 else 'SELL'
            qty = random.uniform(0.01, 0.1)
            signals.append((symbol, side, qty))
    
    return signals[0] if signals else None

if __name__ == '__main__':
    sim = PaperTradingSimulator(initial_balance=10000)
    sim.run_simulation(duration_seconds=30, signal_fn=simple_signal_generator)
