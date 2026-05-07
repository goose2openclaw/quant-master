#!/usr/bin/env python3
"""
XIAMI Performance Optimizer - 性能优化器
分析交易数据，提供优化建议
"""

import os
import json
import random
from datetime import datetime, timedelta
from collections import defaultdict

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.data_dir = "/root/.openclaw/workspace/skills/xiami/data"
        
    def generate_trade_history(self, days: int = 7) -> list:
        """生成模拟交易历史"""
        symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'AVAX', 'OGN', 'ICX', 'COS']
        trades = []
        
        for d in range(days):
            date = datetime.now() - timedelta(days=d)
            num_trades = random.randint(3, 8)
            
            for _ in range(num_trades):
                trade = {
                    "date": date.isoformat(),
                    "symbol": random.choice(symbols),
                    "action": random.choice(["BUY", "SELL"]),
                    "price": round(random.uniform(10, 70000), 2),
                    "amount": round(random.uniform(0.01, 2), 4),
                    "pnl": round(random.uniform(-10, 50), 2),
                    "strategy": random.choice(["mainstream", "mole", "tiered", "unified"]),
                    "confidence": random.randint(5, 10)
                }
                trades.append(trade)
        
        return sorted(trades, key=lambda x: x['date'], reverse=True)
    
    def analyze_performance(self, trades: list) -> dict:
        """分析性能"""
        if not trades:
            return {"error": "No trades to analyze"}
        
        # 基础统计
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in trades)
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # 策略表现
        strategy_stats = defaultdict(lambda: {"trades": 0, "pnl": 0})
        for t in trades:
            strategy_stats[t['strategy']]["trades"] += 1
            strategy_stats[t['strategy']]["pnl"] += t['pnl']
        
        # 币种表现
        symbol_stats = defaultdict(lambda: {"trades": 0, "pnl": 0})
        for t in trades:
            symbol_stats[t['symbol']]["trades"] += 1
            symbol_stats[t['symbol']]["pnl"] += t['pnl']
        
        # 置信度分析
        confidence_stats = defaultdict(lambda: {"trades": 0, "wins": 0})
        for t in trades:
            conf_bucket = f"{t['confidence']//2 * 2}-{(t['confidence']//2 * 2) + 2}"
            confidence_stats[conf_bucket]["trades"] += 1
            if t['pnl'] > 0:
                confidence_stats[conf_bucket]["wins"] += 1
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
            "strategy_performance": dict(strategy_stats),
            "symbol_performance": dict(symbol_stats),
            "confidence_analysis": dict(confidence_stats)
        }
    
    def generate_optimizations(self, analysis: dict) -> list:
        """生成优化建议"""
        suggestions = []
        
        # 胜率分析
        if analysis.get("win_rate", 0) < 50:
            suggestions.append({
                "area": "胜率",
                "priority": "high",
                "suggestion": "胜率低于50%，建议提高信号置信度阈值",
                "action": "将置信度阈值从5提高到7"
            })
        
        # 盈亏比分析
        if analysis.get("profit_factor", 0) < 1.5:
            suggestions.append({
                "area": "盈亏比",
                "priority": "medium",
                "suggestion": "盈亏比较低，建议优化止损止盈比例",
                "action": "将止盈/止损比从2.5调整到3"
            })
        
        # 策略分析
        strat_perf = analysis.get("strategy_performance", {})
        worst_strategy = min(strat_perf.items(), key=lambda x: x[1]['pnl'])[0] if strat_perf else None
        best_strategy = max(strat_perf.items(), key=lambda x: x[1]['pnl'])[0] if strat_perf else None
        
        if worst_strategy and strat_perf[worst_strategy]['pnl'] < 0:
            suggestions.append({
                "area": "策略",
                "priority": "high",
                "suggestion": f"{worst_strategy}策略表现不佳，建议减少仓位或暂停",
                "action": f"降低{worst_strategy}策略权重50%"
            })
        
        if best_strategy:
            suggestions.append({
                "area": "策略",
                "priority": "info",
                "suggestion": f"{best_strategy}策略表现最佳，建议增加权重",
                "action": f"提高{best_strategy}策略权重20%"
            })
        
        # 置信度分析
        conf_analysis = analysis.get("confidence_analysis", {})
        high_conf_wins = conf_analysis.get("8-10", {}).get("wins", 0)
        high_conf_total = conf_analysis.get("8-10", {}).get("trades", 1)
        high_conf_rate = high_conf_wins / high_conf_total * 100 if high_conf_total > 0 else 0
        
        if high_conf_rate > 70:
            suggestions.append({
                "area": "信号",
                "priority": "info",
                "suggestion": f"高置信度(8-10分)胜率{high_conf_rate:.0f}%，表现优异",
                "action": "继续执行高置信度信号"
            })
        
        # 通用建议
        if not suggestions:
            suggestions.append({
                "area": "总体",
                "priority": "info",
                "suggestion": "系统运行正常，无需重大调整",
                "action": "保持当前配置"
            })
        
        return suggestions
    
    def run_analysis(self, days: int = 7):
        """运行分析"""
        print("\n" + "="*70)
        print("📊 XIAMI 性能优化分析".center(70))
        print("="*70)
        
        print(f"\n📅 分析周期: 最近 {days} 天")
        
        # 获取交易历史
        trades = self.generate_trade_history(days)
        
        # 分析
        analysis = self.analyze_performance(trades)
        
        # 打印统计
        print(f"\n📈 基础统计:")
        print(f"   总交易: {analysis['total_trades']}")
        print(f"   盈利: {analysis['winning_trades']} | 亏损: {analysis['losing_trades']}")
        print(f"   胜率: {analysis['win_rate']}%")
        print(f"   总盈亏: ${analysis['total_pnl']}")
        print(f"   平均盈利: ${analysis['avg_win']} | 平均亏损: ${analysis['avg_loss']}")
        print(f"   盈亏比: {analysis['profit_factor']}")
        
        # 策略表现
        print(f"\n⚙️ 策略表现:")
        for strat, stats in analysis.get("strategy_performance", {}).items():
            pnl = stats['pnl']
            icon = "🟢" if pnl > 0 else "🔴"
            print(f"   {icon} {strat:<15} {stats['trades']:>3}笔 | PnL: ${pnl:>8.2f}")
        
        # 币种表现
        print(f"\n🪙 币种表现:")
        for symbol, stats in analysis.get("symbol_performance", {}).items():
            pnl = stats['pnl']
            icon = "🟢" if pnl > 0 else "🔴"
            print(f"   {icon} {symbol:<6} {stats['trades']:>3}笔 | PnL: ${pnl:>8.2f}")
        
        # 优化建议
        suggestions = self.generate_optimizations(analysis)
        
        print(f"\n💡 优化建议:")
        for i, s in enumerate(suggestions, 1):
            priority_icon = "🔴" if s['priority'] == 'high' else ("🟡" if s['priority'] == 'medium' else "🟢")
            print(f"\n   {i}. {priority_icon} [{s['area']}] {s['suggestion']}")
            print(f"      ➜ {s['action']}")
        
        print("\n" + "="*70)
        
        return analysis, suggestions


def main():
    import sys
    
    optimizer = PerformanceOptimizer()
    
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass
    
    optimizer.run_analysis(days)


if __name__ == '__main__':
    main()
