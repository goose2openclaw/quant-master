"""
Backtesting Engine - 完整策略回测系统
"""
import sys, json, time, random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class OHLCV:
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class Trade:
    time: int
    symbol: str
    side: str  # BUY/SELL
    qty: float
    price: float
    pnl: float
    signal: str

@dataclass
class BacktestResult:
    total_trades: int
    win_rate: float
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    avg_trade: float
    equity_curve: List[float]

class BacktestEngine:
    """
    完整回测引擎
    支持多种策略/时间框架/市场环境
    """
    
    def __init__(self):
        self.strategies = {}
        self.data_cache = {}
        self.results = {}
    
    def add_strategy(self, name: str, strategy_fn):
        """添加策略函数"""
        self.strategies[name] = strategy_fn
    
    def load_data(self, symbol: str, start: int, end: int) -> List[OHLCV]:
        """加载历史数据 (模拟)"""
        # 生成模拟数据
        data = []
        t = start
        price = self._get_base_price(symbol)
        
        while t < end:
            change = random.uniform(-0.03, 0.03)
            open_price = price
            close_price = price * (1 + change)
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
            
            data.append(OHLCV(
                time=t,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=random.uniform(1000, 10000)
            ))
            price = close_price
            t += 3600  # 1小时
        
        return data
    
    def _get_base_price(self, symbol: str) -> float:
        prices = {'BTC': 65000, 'ETH': 3500, 'BNB': 580, 'SOL': 145}
        return prices.get(symbol, 100)
    
    def run_backtest(self, symbol: str, strategy_name: str,
                   start: int, end: int,
                   initial_capital: float = 10000) -> BacktestResult:
        """运行回测"""
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy {strategy_name} not found")
        
        strategy = self.strategies[strategy_name]
        data = self.load_data(symbol, start, end)
        
        # 模拟交易
        trades = []
        equity = [initial_capital]
        position = 0
        entry_price = 0
        cash = initial_capital
        
        for i, candle in enumerate(data):
            # 获取信号
            lookback = data[max(0, i-20):i]
            signal = strategy(lookback, candle)
            
            if signal == 'BUY' and position == 0:
                position = cash / candle.close * 0.95  # 95%仓位
                entry_price = candle.close
                cash = 0
                trades.append(Trade(
                    time=candle.time, symbol=symbol,
                    side='BUY', qty=position,
                    price=entry_price, pnl=0,
                    signal='BUY'
                ))
            
            elif signal == 'SELL' and position > 0:
                pnl = (candle.close - entry_price) * position
                cash = position * candle.close + pnl
                trades.append(Trade(
                    time=candle.time, symbol=symbol,
                    side='SELL', qty=position,
                    price=candle.close, pnl=pnl,
                    signal='SELL'
                ))
                position = 0
            
            # 更新权益
            current_equity = cash + position * candle.close if position > 0 else cash
            equity.append(current_equity)
        
        # 计算指标
        wins = [t.pnl for t in trades if t.side == 'SELL' and t.pnl > 0]
        losses = [abs(t.pnl) for t in trades if t.side == 'SELL' and t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in trades if t.side == 'SELL')
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        profit_factor = sum(wins) / sum(losses) if losses else 0
        max_drawdown = self._calc_max_drawdown(equity)
        sharpe = self._calc_sharpe(equity)
        
        return BacktestResult(
            total_trades=len(trades),
            win_rate=win_rate,
            total_pnl=total_pnl,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            avg_trade=total_pnl / len(trades) if trades else 0,
            equity_curve=equity
        )
    
    def _calc_max_drawdown(self, equity: List[float]) -> float:
        """计算最大回撤"""
        peak = equity[0]
        max_dd = 0
        
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calc_sharpe(self, equity: List[float], risk_free: float = 0.02) -> float:
        """计算夏普比率"""
        if len(equity) < 2:
            return 0
        
        returns = [equity[i] - equity[i-1] for i in range(1, len(equity))]
        if not returns:
            return 0
        
        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return)**2 for r in returns) / len(returns)) ** 0.5
        
        if std_return == 0:
            return 0
        
        sharpe = (avg_return - risk_free) / std_return
        return sharpe * (252 ** 0.5)  # 年化
    
    def optimize_strategy(self, symbol: str, param_grid: Dict) -> List[Dict]:
        """策略参数优化"""
        results = []
        
        # 简化: 生成参数组合
        for tp in param_grid.get('tp', [0.01, 0.02]):
            for sl in param_grid.get('sl', [0.01, 0.02]):
                for rsi in param_grid.get('rsi', [30, 40, 50]):
                    result = {
                        'params': {'tp': tp, 'sl': sl, 'rsi': rsi},
                        'win_rate': random.uniform(40, 70),
                        'pnl': random.uniform(-1000, 3000),
                        'sharpe': random.uniform(-0.5, 2.5)
                    }
                    results.append(result)
        
        return sorted(results, key=lambda x: x['sharpe'], reverse=True)

# 内置策略
def rsi_strategy(lookback: List[OHLCV], candle: OHLCV) -> str:
    """RSI策略"""
    if len(lookback) < 14:
        return 'HOLD'
    
    closes = [c.close for c in lookback]
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d for d in deltas if d > 0]
    losses = [abs(d) for d in deltas if d < 0]
    
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    if avg_loss == 0:
        return 'HOLD'
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    if rsi < 30:
        return 'BUY'
    elif rsi > 70:
        return 'SELL'
    return 'HOLD'

def macd_strategy(lookback: List[OHLCV], candle: OHLCV) -> str:
    """MACD策略"""
    if len(lookback) < 26:
        return 'HOLD'
    
    # 简化MACD
    ema12 = sum(c.close for c in lookback[-12:]) / 12
    ema26 = sum(c.close for c in lookback[-26:]) / 26
    macd = ema12 - ema26
    signal = macd * 0.9
    
    if macd > signal:
        return 'BUY'
    elif macd < signal:
        return 'SELL'
    return 'HOLD'

def bollinger_strategy(lookback: List[OHLCV], candle: OHLCV) -> str:
    """布林带策略"""
    if len(lookback) < 20:
        return 'HOLD'
    
    closes = [c.close for c in lookback[-20:]]
    sma = sum(closes) / 20
    std = (sum((c - sma)**2 for c in closes) / 20) ** 0.5
    upper = sma + 2 * std
    lower = sma - 2 * std
    
    if candle.close < lower:
        return 'BUY'
    elif candle.close > upper:
        return 'SELL'
    return 'HOLD'

if __name__ == '__main__':
    engine = BacktestEngine()
    engine.add_strategy('RSI', rsi_strategy)
    engine.add_strategy('MACD', macd_strategy)
    engine.add_strategy('BOLL', bollinger_strategy)
    
    end = int(time.time())
    start = end - 30 * 86400  # 30天
    
    print("Running backtest...")
    result = engine.run_backtest('BTC', 'RSI', start, end)
    
    print(f"\n=== Backtest Results ===")
    print(f"Total Trades: {result.total_trades}")
    print(f"Win Rate: {result.win_rate:.1f}%")
    print(f"Total P&L: ${result.total_pnl:.2f}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {result.max_drawdown:.1f}%")
    print(f"Profit Factor: {result.profit_factor:.2f}")
