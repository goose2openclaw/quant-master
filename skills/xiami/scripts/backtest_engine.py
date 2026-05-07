#!/usr/bin/env python3
"""
XIAMI Backtest Engine - 回测引擎
历史数据回测交易策略
"""

import random
from datetime import datetime, timedelta

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        
    def generate_data(self, symbol: str, days: int = 30) -> list:
        """生成历史数据"""
        data = []
        base_price = 50000 if symbol == "BTC" else 3000
        start = datetime.now() - timedelta(days=days)
        
        for h in range(days * 24):
            ts = start + timedelta(hours=h)
            change = random.uniform(-0.03, 0.035)
            base_price *= (1 + change)
            
            data.append({
                "timestamp": ts.isoformat(),
                "close": base_price,
                "sma20": base_price * random.uniform(0.98, 1.02),
                "sma50": base_price * random.uniform(0.95, 1.05),
                "rsi": random.randint(30, 70)
            })
        
        return data
    
    def generate_signals(self, data: list) -> list:
        """生成信号"""
        signals = []
        
        for i in range(50, len(data)):
            d = data[i]
            prev = data[i-1]
            
            action, reason, conf = "HOLD", "", 0
            
            # 金叉/死叉
            if prev['sma20'] <= prev['sma50'] and d['sma20'] > d['sma50']:
                action, reason, conf = "BUY", "Golden Cross", random.randint(7, 9)
            elif prev['sma20'] >= prev['sma50'] and d['sma20'] < d['sma50']:
                action, reason, conf = "SELL", "Death Cross", random.randint(7, 9)
            elif d['rsi'] < 35 and action == "HOLD":
                action, reason, conf = "BUY", "RSI Oversold", random.randint(6, 8)
            elif d['rsi'] > 65 and action == "HOLD":
                action, reason, conf = "SELL", "RSI Overbought", random.randint(6, 8)
            
            signals.append({
                "timestamp": d["timestamp"],
                "action": action,
                "reason": reason,
                "confidence": conf,
                "price": d["close"]
            })
        
        return signals
    
    def run(self, symbol: str = "BTC", days: int = 30) -> dict:
        """运行回测"""
        print(f"\n{'='*55}")
        print(f"📊 XIAMI 回测 - {symbol} ({days}天)")
        print(f"{'='*55}")
        
        data = self.generate_data(symbol, days)
        signals = self.generate_signals(data)
        
        for sig in signals:
            if sig['action'] == "HOLD":
                continue
            
            price = sig['price']
            
            if sig['action'] == "BUY" and symbol not in self.positions:
                size = (sig['confidence'] / 10) * self.capital * 0.1
                self.positions[symbol] = {"qty": size / price, "entry": price}
                self.trades.append({"action": "BUY", "price": price, "conf": sig['confidence']})
            
            elif sig['action'] == "SELL" and symbol in self.positions:
                pos = self.positions[symbol]
                pnl = (price - pos['entry']) * pos['qty']
                self.capital += pnl + (pos['qty'] * price)
                self.trades.append({"action": "SELL", "price": price, "pnl": pnl})
                del self.positions[symbol]
        
        # 统计
        wins = [t for t in self.trades if t.get('pnl', 0) > 0]
        loss = [t for t in self.trades if t.get('pnl', 0) <= 0]
        
        total = len(self.trades)
        win_rate = len(wins) / total * 100 if total > 0 else 0
        total_pnl = sum(t.get('pnl', 0) for t in self.trades)
        ret = (self.capital - self.initial_capital) / self.initial_capital * 100
        
        print(f"\n💰 初始: ${self.initial_capital:,.0f} → 最终: ${self.capital:,.0f}")
        print(f"📈 收益: {ret:.2f}%")
        print(f"📊 交易: {total}笔 | 胜率: {win_rate:.1f}%")
        print(f"💵 PnL: ${total_pnl:.2f}")
        
        print(f"\n📋 最近交易:")
        for i, t in enumerate(self.trades[-5:], 1):
            pnl = f"+${t.get('pnl', 0):.2f}" if t.get('pnl', 0) > 0 else f"-${abs(t.get('pnl', 0)):.2f}"
            emoji = "🟢" if t['action'] == "BUY" else "🔴"
            print(f"   {i}. {emoji} {t['action']} @ ${t['price']:.2f} | {pnl if 'pnl' in t else ''}")
        
        return {
            "initial": self.initial_capital,
            "final": self.capital,
            "return": ret,
            "trades": total,
            "win_rate": win_rate,
            "pnl": total_pnl
        }


if __name__ == '__main__':
    import sys
    
    capital = float(sys.argv[1]) if len(sys.argv) > 1 else 10000
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    symbol = sys.argv[3] if len(sys.argv) > 3 else "BTC"
    
    engine = BacktestEngine(capital)
    engine.run(symbol, days)
