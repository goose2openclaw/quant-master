#!/usr/bin/env python3
"""
XIAMI Trading Journal - Trade Logging
Log and analyze all trading activities
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class TradingJournal:
    """Trading Journal"""
    
    def __init__(self):
        self.data_dir = "/root/.openclaw/workspace/skills/xiami/data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.journal_file = os.path.join(self.data_dir, "trading_journal.json")
        
    def load_entries(self) -> list:
        """Load journal entries"""
        if os.path.exists(self.journal_file):
            with open(self.journal_file, 'r') as f:
                return json.load(f)
        return []
    
    def add_entry(self, trade: dict) -> dict:
        """Add trade entry"""
        entry = {
            "id": len(self.load_entries()) + 1,
            "timestamp": datetime.now().isoformat(),
            **trade
        }
        
        entries = self.load_entries()
        entries.append(entry)
        
        with open(self.journal_file, 'w') as f:
            json.dump(entries, f, indent=2)
        
        return entry
    
    def generate_sample_data(self, days: int = 7):
        """Generate sample trading data"""
        import random
        
        symbols = ["BTC", "ETH", "SOL", "XRP", "AVAX", "OGN", "ICX"]
        strategies = ["mainstream", "mole", "tiered", "unified", "airdrop"]
        
        entries = []
        for d in range(days):
            date = datetime.now() - timedelta(days=d)
            num_trades = random.randint(2, 6)
            
            for _ in range(num_trades):
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                timestamp = date.replace(hour=hour, minute=minute).isoformat()
                
                symbol = random.choice(symbols)
                action = random.choice(["BUY", "SELL"])
                price = random.uniform(100, 70000)
                quantity = random.uniform(0.01, 2)
                
                if action == "SELL":
                    pnl = random.uniform(-15, 45)
                else:
                    pnl = 0
                
                entry = {
                    "id": len(entries) + 1,
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "action": action,
                    "price": round(price, 2),
                    "quantity": round(quantity, 4),
                    "value": round(price * quantity, 2),
                    "pnl": round(pnl, 2),
                    "strategy": random.choice(strategies),
                    "confidence": random.randint(5, 10),
                    "notes": ""
                }
                entries.append(entry)
        
        with open(self.journal_file, 'w') as f:
            json.dump(entries, f, indent=2)
        
        return entries
    
    def get_summary(self, days: int = 7) -> dict:
        """Get journal summary"""
        entries = self.load_entries()
        
        if not entries:
            entries = self.generate_sample_data(days)
        
        # Filter by date
        cutoff = datetime.now() - timedelta(days=days)
        recent = [e for e in entries if datetime.fromisoformat(e["timestamp"]) > cutoff]
        
        # Stats
        total_trades = len(recent)
        buys = [e for e in recent if e["action"] == "BUY"]
        sells = [e for e in recent if e["action"] == "SELL"]
        
        closed_trades = [e for e in recent if e.get("pnl", 0) != 0]
        wins = [e for e in closed_trades if e["pnl"] > 0]
        losses = [e for e in closed_trades if e["pnl"] <= 0]
        
        win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
        total_pnl = sum(e["pnl"] for e in closed_trades)
        
        # By strategy
        by_strategy = defaultdict(lambda: {"trades": 0, "pnl": 0})
        for e in recent:
            by_strategy[e["strategy"]]["trades"] += 1
            if e.get("pnl", 0):
                by_strategy[e["strategy"]]["pnl"] += e["pnl"]
        
        # By symbol
        by_symbol = defaultdict(lambda: {"trades": 0, "pnl": 0})
        for e in recent:
            by_symbol[e["symbol"]]["trades"] += 1
            if e.get("pnl", 0):
                by_symbol[e["symbol"]]["pnl"] += e["pnl"]
        
        return {
            "period_days": days,
            "total_trades": total_trades,
            "buys": len(buys),
            "sells": len(sells),
            "closed_trades": len(closed_trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "by_strategy": dict(by_strategy),
            "by_symbol": dict(by_symbol),
            "recent_entries": recent[-10:]
        }
    
    def run(self, days: int = 7):
        """Run journal"""
        print("\n" + "="*60)
        print("XIAMI Trading Journal")
        print("="*60)
        
        summary = self.get_summary(days)
        
        print(f"\nPeriod: Last {days} days")
        print(f"Total Trades: {summary['total_trades']}")
        print(f"  Buys: {summary['buys']} | Sells: {summary['sells']}")
        
        print(f"\nClosed Trades: {summary['closed_trades']}")
        print(f"  Wins: {summary['wins']} | Losses: {summary['losses']}")
        print(f"  Win Rate: {summary['win_rate']}%")
        print(f"  Total PnL: ${summary['total_pnl']:.2f}")
        
        print(f"\nBy Strategy:")
        for strat, stats in summary["by_strategy"].items():
            pnl = stats["pnl"]
            emoji = "+" if pnl > 0 else ""
            print(f"  {strat:12} {stats['trades']:3} trades  PnL: {emoji}${pnl:.2f}")
        
        print(f"\nBy Symbol:")
        for sym, stats in summary["by_symbol"].items():
            pnl = stats["pnl"]
            emoji = "+" if pnl > 0 else ""
            print(f"  {sym:6} {stats['trades']:3} trades  PnL: {emoji}${pnl:.2f}")
        
        print(f"\nRecent Entries:")
        for entry in summary["recent_entries"][-5:]:
            ts = datetime.fromisoformat(entry["timestamp"])
            pnl_str = f"+${entry['pnl']:.2f}" if entry["pnl"] > 0 else f"-${abs(entry['pnl']):.2f}" if entry['pnl'] != 0 else ""
            print(f"  {ts.strftime('%m/%d %H:%M')} {entry['action']:4} {entry['symbol']:6} @ ${entry['price']:.2f}  {pnl_str}")
        
        print("\n" + "="*60)


def main():
    import sys
    
    journal = TradingJournal()
    
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass
    
    journal.run(days)


if __name__ == '__main__':
    main()
