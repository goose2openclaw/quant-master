"""
Backtest Engine - 从QuantConnect Lean精细克隆
专业级回测引擎，支持多种策略和风险管理

来源: QuantConnect Lean Backtesting Engine
"""
import time
import json
import math
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import random


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float = 0
    entry_time: float = 0
    pnl: float = 0
    pnl_pct: float = 0
    
    def update(self, current_price: float):
        """更新持仓"""
        self.current_price = current_price
        self.pnl = (current_price - self.entry_price) * self.quantity
        self.pnl_pct = (current_price - self.entry_price) / self.entry_price * 100


@dataclass
class Order:
    """订单"""
    id: str
    symbol: str
    side: str  # BUY/SELL
    quantity: float
    order_type: str  # MARKET/LIMIT
    price: float = 0
    status: str = "PENDING"
    fill_price: float = 0
    timestamp: float = 0
    
    def fill(self, price: float):
        """订单成交"""
        self.status = "FILLED"
        self.fill_price = price


@dataclass
class TradeStats:
    """交易统计"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0
    total_fees: float = 0
    max_drawdown: float = 0
    max_drawdown_pct: float = 0
    sharpe_ratio: float = 0
    sortino_ratio: float = 0
    win_rate: float = 0
    avg_win: float = 0
    avg_loss: float = 0
    profit_factor: float = 0
    largest_win: float = 0
    largest_loss: float = 0
    
    def calculate(self):
        """计算统计"""
        if self.total_trades == 0:
            return
        
        self.win_rate = self.winning_trades / self.total_trades * 100
        
        if self.winning_trades > 0:
            self.avg_win = sum(t['pnl'] for t in self.trades if t['pnl'] > 0) / self.winning_trades
        if self.losing_trades > 0:
            self.avg_loss = sum(t['pnl'] for t in self.trades if t['pnl'] < 0) / self.losing_trades
        
        if self.avg_loss != 0:
            self.profit_factor = abs(sum(t['pnl'] for t in self.trades if t['pnl'] > 0) / 
                                    sum(t['pnl'] for t in self.trades if t['pnl'] < 0))
        
        # Sharpe Ratio (simplified)
        if len(self.trades) > 1:
            returns = [t['pnl_pct'] / 100 for t in self.trades]
            avg_return = sum(returns) / len(returns)
            std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns))
            self.sharpe_ratio = avg_return / std_return * math.sqrt(252) if std_return > 0 else 0
        
        # Max Drawdown
        equity = 10000
        peak = equity
        for trade in self.trades:
            equity += trade['pnl']
            if equity > peak:
                peak = equity
            drawdown = peak - equity
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
                self.max_drawdown_pct = drawdown / peak * 100 if peak > 0 else 0


@dataclass
class BacktestResult:
    """回测结果"""
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 0
    final_capital: float = 0
    total_return: float = 0
    total_return_pct: float = 0
    stats: TradeStats = field(default_factory=TradeStats)
    trades: List = field(default_factory=list)
    equity_curve: List = field(default_factory=list)
    drawdown_curve: List = field(default_factory=list)
    
    def summary(self) -> str:
        """生成摘要"""
        return f"""
=== Backtest Summary ===
Period: {self.start_date} - {self.end_date}
Initial Capital: ${self.initial_capital:,.2f}
Final Capital: ${self.final_capital:,.2f}
Total Return: ${self.total_return:+,.2f} ({self.total_return_pct:+.2f}%)

Trades: {self.stats.total_trades}
Win Rate: {self.stats.win_rate:.1f}%
Profit Factor: {self.stats.profit_factor:.2f}
 Sharpe Ratio: {self.stats.sharpe_ratio:.2f}
Max Drawdown: ${self.stats.max_drawdown:,.2f} ({self.stats.max_drawdown_pct:.1f}%)

Best Trade: ${self.stats.largest_win:+,.2f}
Worst Trade: ${self.stats.largest_loss:+,.2f}
"""


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 10000, fee_rate: float = 0.001):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[Dict] = []
        self.equity_curve = []
        
        self.stats = TradeStats()
        
        # Settings
        self.max_positions = 5
        self.max_position_size = 0.2  # 20% of capital per position
        self.stop_loss = 0.02  # 2%
        self.take_profit = 0.08  # 8%
        
        self._order_id = 0
    
    def _new_order_id(self) -> str:
        """生成订单ID"""
        self._order_id += 1
        return f"order_{self._order_id}"
    
    def buy(self, symbol: str, quantity: float, price: float = 0, order_type: str = "MARKET") -> Order:
        """买入"""
        order = Order(
            id=self._new_order_id(),
            symbol=symbol,
            side="BUY",
            quantity=quantity,
            order_type=order_type,
            price=price,
            timestamp=time.time()
        )
        
        # Calculate fee
        cost = quantity * (price or 0) * (1 + self.fee_rate)
        
        if order_type == "MARKET":
            order.status = "FILLED"
            order.fill_price = price
            self._fill_order(order)
        
        self.orders.append(order)
        return order
    
    def sell(self, symbol: str, quantity: float, price: float = 0, order_type: str = "MARKET") -> Order:
        """卖出"""
        if symbol not in self.positions:
            return None
        
        order = Order(
            id=self._new_order_id(),
            symbol=symbol,
            side="SELL",
            quantity=quantity,
            order_type=order_type,
            price=price,
            timestamp=time.time()
        )
        
        if order_type == "MARKET":
            order.status = "FILLED"
            order.fill_price = price
            self._fill_order(order)
        
        self.orders.append(order)
        return order
    
    def _fill_order(self, order: Order):
        """执行订单"""
        if order.side == "BUY":
            cost = order.quantity * order.fill_price * (1 + self.fee_rate)
            if cost > self.cash:
                order.status = "REJECTED"
                return
            
            self.cash -= cost
            
            if order.symbol in self.positions:
                pos = self.positions[order.symbol]
                total_qty = pos.quantity + order.quantity
                pos.entry_price = (pos.entry_price * pos.quantity + order.fill_price * order.quantity) / total_qty
                pos.quantity = total_qty
            else:
                self.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    entry_price=order.fill_price,
                    current_price=order.fill_price,
                    entry_time=order.timestamp
                )
            
            self.trades.append({
                'id': order.id,
                'symbol': order.symbol,
                'side': 'BUY',
                'quantity': order.quantity,
                'price': order.fill_price,
                'cost': cost,
                'fee': cost * self.fee_rate,
                'timestamp': order.timestamp,
                'pnl': 0,
                'pnl_pct': 0
            })
            
            self.stats.total_trades += 1
        
        elif order.side == "SELL":
            if order.symbol not in self.positions:
                return
            
            pos = self.positions[order.symbol]
            revenue = order.quantity * order.fill_price * (1 - self.fee_rate)
            
            pnl = (order.fill_price - pos.entry_price) * order.quantity
            pnl_pct = (order.fill_price - pos.entry_price) / pos.entry_price * 100
            
            self.cash += revenue
            
            self.trades.append({
                'id': order.id,
                'symbol': order.symbol,
                'side': 'SELL',
                'quantity': order.quantity,
                'price': order.fill_price,
                'revenue': revenue,
                'fee': revenue * self.fee_rate,
                'timestamp': order.timestamp,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'entry_price': pos.entry_price
            })
            
            if pnl > 0:
                self.stats.winning_trades += 1
                self.stats.largest_win = max(self.stats.largest_win, pnl)
            else:
                self.stats.losing_trades += 1
                self.stats.largest_loss = min(self.stats.largest_loss, pnl)
            
            self.stats.total_pnl += pnl
            self.stats.total_fees += revenue * self.fee_rate
            
            pos.quantity -= order.quantity
            if pos.quantity <= 0:
                del self.positions[order.symbol]
    
    def update_prices(self, prices: Dict[str, float]):
        """更新价格"""
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update(prices[symbol])
        
        # Record equity
        equity = self.cash + sum(p.quantity * p.current_price for p in self.positions.values())
        self.equity_curve.append({
            'timestamp': time.time(),
            'equity': equity,
            'cash': self.cash,
            'positions': len(self.positions)
        })
    
    def check_stops(self, prices: Dict[str, float]) -> List[str]:
        """检查止损/止盈"""
        triggered = []
        
        for symbol, position in list(self.positions.items()):
            if symbol not in prices:
                continue
            
            pnl_pct = (prices[symbol] - position.entry_price) / position.entry_price * 100
            
            # Stop loss
            if pnl_pct <= -self.stop_loss * 100:
                self.sell(symbol, position.quantity, prices[symbol])
                triggered.append(f"STOP_LOSS:{symbol}")
            
            # Take profit
            elif pnl_pct >= self.take_profit * 100:
                self.sell(symbol, position.quantity, prices[symbol])
                triggered.append(f"TAKE_PROFIT:{symbol}")
        
        return triggered
    
    def run(self, data: List[Dict], strategy_fn: Callable) -> BacktestResult:
        """运行回测
        
        Args:
            data: K线数据 [{'timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol'}]
            strategy_fn: 策略函数 (data, engine) -> None
        """
        
        # Group data by symbol
        symbol_data = defaultdict(list)
        for kline in data:
            symbol_data[kline['symbol']].append(kline)
        
        # Sort each symbol's data
        for symbol in symbol_data:
            symbol_data[symbol].sort(key=lambda x: x['timestamp'])
        
        # Get all timestamps
        all_times = sorted(set(k['timestamp'] for k in data))
        
        # Run backtest
        for ts in all_times:
            # Update prices
            prices = {}
            for symbol, klines in symbol_data.items():
                for kline in klines:
                    if kline['timestamp'] == ts:
                        prices[symbol] = kline['close']
                        break
            
            if prices:
                self.update_prices(prices)
                self.check_stops(prices)
                
                # Run strategy
                current_data = {symbol: [k for k in klines if k['timestamp'] <= ts] 
                              for symbol, klines in symbol_data.items()}
                strategy_fn(current_data, self)
        
        # Close all positions
        for symbol, position in list(self.positions.items()):
            if symbol in prices:
                self.sell(symbol, position.quantity, prices[symbol])
        
        # Calculate stats
        self.stats.trades = self.trades
        self.stats.calculate()
        
        # Build result
        final_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.initial_capital
        
        result = BacktestResult(
            start_date=datetime.fromtimestamp(all_times[0]).strftime('%Y-%m-%d') if all_times else "",
            end_date=datetime.fromtimestamp(all_times[-1]).strftime('%Y-%m-%d') if all_times else "",
            initial_capital=self.initial_capital,
            final_capital=final_equity,
            total_return=final_equity - self.initial_capital,
            total_return_pct=(final_equity - self.initial_capital) / self.initial_capital * 100,
            stats=self.stats,
            trades=self.trades,
            equity_curve=self.equity_curve
        )
        
        return result


class StrategyLibrary:
    """策略库 - 来自Lean"""
    
    @staticmethod
    def mean_reversion(data: Dict, engine: BacktestEngine):
        """均值回归策略"""
        for symbol, klines in data.items():
            if len(klines) < 20:
                continue
            
            closes = [k['close'] for k in klines]
            sma20 = sum(closes[-20:]) / 20
            current = closes[-1]
            
            # RSI
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas[-14:]]
            losses = [-d if d < 0 else 0 for d in deltas[-14:]]
            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs)) if rs > 0 else 50
            
            # Buy if price below SMA and RSI oversold
            if current < sma20 * 0.95 and rsi < 35:
                if symbol not in engine.positions and len(engine.positions) < engine.max_positions:
                    quantity = (engine.cash * 0.1) / current
                    engine.buy(symbol, quantity, current)
            
            # Sell if price above SMA or RSI overbought
            elif symbol in engine.positions:
                if current > sma20 * 1.05 or rsi > 65:
                    engine.sell(symbol, engine.positions[symbol].quantity, current)
    
    @staticmethod
    def momentum(data: Dict, engine: BacktestEngine):
        """动量策略"""
        for symbol, klines in data.items():
            if len(klines) < 20:
                continue
            
            closes = [k['close'] for k in klines]
            
            # Momentum
            momentum = (closes[-1] - closes[-10]) / closes[-10] * 100
            
            # Buy on strong momentum
            if momentum > 5:
                if symbol not in engine.positions and len(engine.positions) < engine.max_positions:
                    quantity = (engine.cash * 0.1) / closes[-1]
                    engine.buy(symbol, quantity, closes[-1])
            
            # Sell on reversal
            elif symbol in engine.positions and momentum < -3:
                engine.sell(symbol, engine.positions[symbol].quantity, closes[-1])
    
    @staticmethod
    def bollinger_band(data: Dict, engine: BacktestEngine):
        """布林带策略"""
        for symbol, klines in data.items():
            if len(klines) < 20:
                continue
            
            closes = [k['close'] for k in klines][-20:]
            sma = sum(closes) / 20
            variance = sum((c - sma) ** 2 for c in closes) / 20
            std = variance ** 0.5
            
            upper = sma + 2 * std
            lower = sma - 2 * std
            current = closes[-1]
            
            # Buy at lower band
            if current < lower:
                if symbol not in engine.positions and len(engine.positions) < engine.max_positions:
                    quantity = (engine.cash * 0.1) / current
                    engine.buy(symbol, quantity, current)
            
            # Sell at upper band
            elif symbol in engine.positions:
                if current > upper:
                    engine.sell(symbol, engine.positions[symbol].quantity, current)


if __name__ == "__main__":
    # Generate test data
    print("=== Backtest Engine Test ===")
    
    data = []
    price = 100
    for i in range(200):
        price += random.uniform(-2, 2)
        data.append({
            'timestamp': 1000000 + i * 3600,
            'symbol': 'BTCUSDT',
            'open': price - 1,
            'high': price + 2,
            'low': price - 3,
            'close': price,
            'volume': random.uniform(100, 1000)
        })
    
    # Run backtest
    engine = BacktestEngine(initial_capital=10000)
    result = engine.run(data, StrategyLibrary.momentum)
    
    print(result.summary())
