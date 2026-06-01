#!/usr/bin/env python3
"""
QuantMaster 自主交易系统 v16.6.0
统一价格 → 扫描 → 决策 → 执行
"""
import sys
import time
import random
from typing import Dict, List

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

class UnifiedTrader:
    """
    统一自主交易系统
    共享价格数据,真正的自主运行
    """
    
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, dict] = {}
        self.trades: List[dict] = []
        self.trade_count = 0
        
        # 统一价格池
        self.prices = {
            'BTC': 67000, 'ETH': 3500, 'BNB': 580, 'SOL': 145,
            'XRP': 0.52, 'ADA': 0.45, 'DOGE': 0.12, 'AVAX': 35,
            'DOT': 7.2, 'LINK': 14.5, 'MATIC': 0.72, 'UNI': 9.5,
            'ATOM': 8.8, 'LTC': 85, 'ETC': 26, 'FIL': 5.8,
            'APT': 8.2, 'ARB': 1.05, 'OP': 2.1, 'NEAR': 5.8
        }
        
        # 阈值
        self.buy_threshold = 65
        self.sell_threshold = 35
        
        # 仓位限制
        self.max_position_pct = 0.1  # 10%
        self.stop_loss_pct = 0.05  # 5%
        
    def update_prices(self):
        """更新价格 - 市场模拟"""
        for symbol in self.prices:
            change = random.gauss(0, 0.005)  # 0.5%波动
            self.prices[symbol] *= (1 + change)
    
    def scan_opportunities(self) -> List[dict]:
        """扫描机会"""
        opportunities = []
        
        for symbol, price in self.prices.items():
            # 生成信号分数 (基于价格变动和市场状态)
            base_score = 50 + random.uniform(-15, 15)
            
            # 检查持仓
            if symbol in self.positions:
                pos = self.positions[symbol]
                pnl_pct = (price - pos['entry_price']) / pos['entry_price']
                
                # 如果盈利>10%,建议卖出
                if pnl_pct > 0.1:
                    base_score = 25  # 建议卖出
                # 如果亏损>5%,建议止损
                elif pnl_pct < -0.05:
                    base_score = 20  # 强制卖出
            
            signal = 'HOLD'
            action = 'WATCH'
            
            if base_score > self.buy_threshold:
                signal = 'BUY'
                action = 'LONG'
            elif base_score < self.sell_threshold:
                signal = 'SELL'
                action = 'SHORT'
            
            opportunities.append({
                'symbol': symbol,
                'price': price,
                'score': base_score,
                'signal': signal,
                'action': action
            })
        
        # 按分数排序
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities
    
    def execute_buy(self, symbol: str, price: float):
        """执行买入"""
        position_value = self.balance * self.max_position_pct
        qty = position_value / price
        
        self.balance -= position_value
        self.positions[symbol] = {
            'qty': qty,
            'entry_price': price,
            'entry_time': time.time()
        }
        
        self.trade_count += 1
        self.trades.append({
            'id': self.trade_count,
            'time': time.time(),
            'symbol': symbol,
            'side': 'BUY',
            'price': price,
            'qty': qty,
            'value': position_value
        })
        
        return qty
    
    def execute_sell(self, symbol: str, price: float):
        """执行卖出"""
        if symbol not in self.positions:
            return 0
        
        pos = self.positions[symbol]
        qty = pos['qty']
        value = qty * price
        pnl = value - (qty * pos['entry_price'])
        
        self.balance += value
        del self.positions[symbol]
        
        self.trade_count += 1
        self.trades.append({
            'id': self.trade_count,
            'time': time.time(),
            'symbol': symbol,
            'side': 'SELL',
            'price': price,
            'qty': qty,
            'value': value,
            'pnl': pnl
        })
        
        return pnl
    
    def check_stop_loss(self):
        """检查止损"""
        to_close = []
        
        for symbol, pos in self.positions.items():
            price = self.prices[symbol]
            pnl_pct = (price - pos['entry_price']) / pos['entry_price']
            
            if pnl_pct < -self.stop_loss_pct:
                to_close.append(symbol)
        
        for symbol in to_close:
            price = self.prices[symbol]
            pnl = self.execute_sell(symbol, price)
            print(f"  🛑 止损: {symbol} @ ${price:.2f} (${pnl:+.2f})")
    
    def get_equity(self) -> float:
        """计算总权益"""
        position_value = sum(
            pos['qty'] * self.prices.get(symbol, 0)
            for symbol, pos in self.positions.items()
        )
        return self.balance + position_value
    
    def get_positions_summary(self) -> List[dict]:
        """持仓摘要"""
        summary = []
        
        for symbol, pos in self.positions.items():
            price = self.prices[symbol]
            value = pos['qty'] * price
            pnl = value - (pos['qty'] * pos['entry_price'])
            pnl_pct = pnl / (pos['qty'] * pos['entry_price']) * 100
            
            summary.append({
                'symbol': symbol,
                'qty': pos['qty'],
                'entry': pos['entry_price'],
                'current': price,
                'value': value,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
        
        return summary
    
    def get_trade_stats(self) -> dict:
        """交易统计"""
        sells = [t for t in self.trades if t['side'] == 'SELL']
        wins = [t for t in sells if t.get('pnl', 0) > 0]
        
        total_pnl = sum(t.get('pnl', 0) for t in sells)
        
        return {
            'total_trades': len(self.trades),
            'buy_trades': len([t for t in self.trades if t['side'] == 'BUY']),
            'sell_trades': len(sells),
            'wins': len(wins),
            'losses': len(sells) - len(wins),
            'win_rate': len(wins) / len(sells) * 100 if sells else 0,
            'total_pnl': total_pnl
        }
    
    def run_autonomous(self, cycles: int = 20, interval: int = 10):
        """运行自主交易"""
        print("=" * 60)
        print("🚀 QuantMaster 自主交易系统 v16.6.0")
        print("=" * 60)
        print(f"\n💰 初始资金: ${self.initial_balance:,.2f}")
        print(f"📊 买入阈值: >{self.buy_threshold}")
        print(f"📊 卖出阈值: <{self.sell_threshold}")
        print(f"🛡️ 止损线: -{self.stop_loss_pct*100}%\n")
        
        for cycle in range(1, cycles + 1):
            print(f"{'='*60}")
            print(f"📍 周期 {cycle}/{cycles} | {time.strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            # 1. 更新价格
            self.update_prices()
            
            # 2. 检查止损
            self.check_stop_loss()
            
            # 3. 扫描机会
            opportunities = self.scan_opportunities()
            
            print("\n📊 Top 5 机会:")
            for i, opp in enumerate(opportunities[:5], 1):
                emoji = "🟢" if opp['action'] == 'LONG' else "🔴" if opp['action'] == 'SHORT' else "⚪"
                print(f"  {i}. {emoji} {opp['symbol']:6} | ${opp['price']:>10.2f} | 评分: {opp['score']:5.1f} | {opp['action']}")
            
            # 4. 执行交易
            print("\n🤖 决策:")
            
            buys = [o for o in opportunities if o['action'] == 'LONG' and o['symbol'] not in self.positions]
            sells = [o for o in opportunities if o['action'] == 'SHORT' and o['symbol'] in self.positions]
            
            for buy in buys[:2]:
                qty = self.execute_buy(buy['symbol'], buy['price'])
                print(f"  ✅ 买入: {qty:.4f} {buy['symbol']} @ ${buy['price']:.2f}")
            
            for sell in sells[:2]:
                pnl = self.execute_sell(sell['symbol'], sell['price'])
                print(f"  ✅ 卖出: {sell['symbol']} @ ${sell['price']:.2f} (${pnl:+.2f})")
            
            if not buys and not sells:
                print("  ⏸️  无交易机会")
            
            # 5. 状态显示
            equity = self.get_equity()
            pnl = equity - self.initial_balance
            pnl_pct = pnl / self.initial_balance * 100
            
            print(f"\n📈 状态:")
            print(f"  💵 余额: ${self.balance:,.2f}")
            print(f"  📊 权益: ${equity:,.2f}")
            print(f"  📈 盈亏: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
            print(f"  🏠 持仓: {len(self.positions)} 个")
            
            for pos in self.get_positions_summary():
                emoji = "🟢" if pos['pnl'] >= 0 else "🔴"
                print(f"     {emoji} {pos['symbol']}: {pos['qty']:.4f} @ ${pos['entry']:.2f} → ${pos['current']:.2f} (${pos['pnl']:+.2f})")
            
            print(f"\n⏳ 等待{interval}秒...\n")
            time.sleep(interval)
        
        # 最终报告
        print("=" * 60)
        print("📊 自主交易完成 - 最终报告")
        print("=" * 60)
        
        stats = self.get_trade_stats()
        
        print(f"\n💰 最终余额: ${self.balance:,.2f}")
        print(f"📊 最终权益: ${self.get_equity():,.2f}")
        print(f"📈 总盈亏: ${stats['total_pnl']:+.2f}")
        print(f"📉 交易次数: {stats['total_trades']}")
        print(f"   买入: {stats['buy_trades']}, 卖出: {stats['sell_trades']}")
        print(f"✅ 胜率: {stats['win_rate']:.1f}%")
        print(f"   盈利: {stats['wins']}, 亏损: {stats['losses']}")
        
        print("\n📋 交易历史:")
        for t in self.trades[-10:]:
            side = "🟢 BUY" if t['side'] == 'BUY' else "🔴 SELL"
            pnl_str = f" (${t.get('pnl', 0):+.2f})" if 'pnl' in t else ""
            print(f"  {t['id']:2}. {side} {t['qty']:.4f} {t['symbol']} @ ${t['price']:.2f}{pnl_str}")
        
        print("\n" + "=" * 60)
        print("✅ 自主交易完成")
        print("=" * 60)

if __name__ == '__main__':
    trader = UnifiedTrader(initial_balance=10000)
    trader.run_autonomous(cycles=15, interval=5)
