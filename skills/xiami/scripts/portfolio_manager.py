#!/usr/bin/env python3
"""
XIAMI Portfolio Manager - Portfolio Management
Asset allocation, rebalancing, performance tracking
"""

import json
import random
from datetime import datetime
from typing import Dict, List

class PortfolioManager:
    """Portfolio Manager"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.assets = {
            "BTC": {"allocation": 40, "current": 68000, "pnl": 5.2},
            "ETH": {"allocation": 30, "current": 3300, "pnl": 3.8},
            "SOL": {"allocation": 15, "current": 145, "pnl": -1.2},
            "USDT": {"allocation": 10, "current": 1, "pnl": 0},
            "OTHER": {"allocation": 5, "current": 0, "pnl": 2.5},
        }
        self.history = []
        
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        total_value = sum(
            self.initial_capital * (alloc["allocation"]/100) * (1 + alloc["pnl"]/100)
            for alloc in self.assets.values()
        )
        
        total_pnl = total_value - self.initial_capital
        total_pnl_pct = (total_pnl / self.initial_capital) * 100
        
        return {
            "timestamp": datetime.now().isoformat(),
            "initial_capital": self.initial_capital,
            "current_value": total_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "assets": self.assets
        }
    
    def rebalance(self, target_alloc: Dict[str, int]) -> Dict:
        """Rebalance portfolio"""
        print("\n" + "="*50)
        print("Portfolio Rebalancing")
        print("="*50)
        
        print("\nCurrent Allocation:")
        for asset, alloc in self.assets.items():
            print(f"  {asset:8} {alloc['allocation']:3}%")
        
        print("\nTarget Allocation:")
        for asset, alloc in target_alloc.items():
            print(f"  {asset:8} {alloc:3}%")
        
        # Generate rebalance orders
        orders = []
        for asset, target in target_alloc.items():
            current = self.assets.get(asset, {"allocation": 0})["allocation"]
            diff = target - current
            
            if abs(diff) > 2:  # Only rebalance if difference > 2%
                action = "BUY" if diff > 0 else "SELL"
                orders.append({
                    "asset": asset,
                    "action": action,
                    "amount_pct": abs(diff)
                })
                self.assets[asset]["allocation"] = target
        
        print("\nRebalance Orders:")
        for order in orders:
            print(f"  {order['action']:4} {order['asset']:8} {order['amount_pct']:3}%")
        
        return {"status": "rebalanced", "orders": orders}
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        summary = self.get_portfolio_summary()
        
        # Simulate metrics
        return {
            "total_return": summary["total_pnl_pct"],
            "sharpe_ratio": round(random.uniform(1.5, 3.5), 2),
            "max_drawdown": round(random.uniform(3, 8), 1),
            "win_rate": round(random.uniform(55, 75), 1),
            "profit_factor": round(random.uniform(1.5, 3.0), 2),
            "calmar_ratio": round(random.uniform(1, 3), 2),
        }
    
    def run(self):
        """Run portfolio manager"""
        print("\n" + "="*60)
        print("XIAMI Portfolio Manager")
        print("="*60)
        
        summary = self.get_portfolio_summary()
        
        print(f"\nPortfolio Summary:")
        print(f"  Initial: ${summary['initial_capital']:,.2f}")
        print(f"  Current: ${summary['current_value']:,.2f}")
        print(f"  PnL: ${summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:.2f}%)")
        
        print(f"\nAsset Allocation:")
        for asset, data in summary["assets"].items():
            bar = "█" * int(data["allocation"]/5) + "░" * (20 - int(data["allocation"]/5))
            pnl_emoji = "+" if data["pnl"] > 0 else ""
            print(f"  {asset:8} [{bar:20}] {data['allocation']:3}%  {pnl_emoji}{data['pnl']:.1f}%")
        
        metrics = self.get_performance_metrics()
        print(f"\nPerformance Metrics:")
        for metric, value in metrics.items():
            print(f"  {metric:20} {value}")
        
        print("\n" + "="*60)


def main():
    import sys
    
    pm = PortfolioManager(10000)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "rebalance":
            target = {"BTC": 35, "ETH": 25, "SOL": 20, "USDT": 15, "OTHER": 5}
            result = pm.rebalance(target)
            print(json.dumps(result, indent=2))
        else:
            pm.run()
    else:
        pm.run()


if __name__ == '__main__':
    main()
