"""交易日志系统"""
import json, os, time
from datetime import datetime

class TradeLogger:
    """交易日志"""
    def __init__(self, log_dir):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.trade_file = f"{log_dir}/trades.json"
        self.equity_file = f"{log_dir}/equity.csv"
        self._init_files()
    
    def _init_files(self):
        if not os.path.exists(self.trade_file):
            with open(self.trade_file, 'w') as f:
                json.dump([], f)
        if not os.path.exists(self.equity_file):
            with open(self.equity_file, 'w') as f:
                f.write("time,equity,position_value,cash\n")
    
    def log_trade(self, trade):
        """记录交易"""
        trade['timestamp'] = datetime.now().isoformat()
        trades = json.load(open(self.trade_file))
        trades.append(trade)
        with open(self.trade_file, 'w') as f:
            json.dump(trades, f, indent=2)
    
    def log_equity(self, equity, position_value, cash):
        """记录权益曲线"""
        with open(self.equity_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()},{equity},{position_value},{cash}\n")
    
    def get_trades(self, limit=100):
        trades = json.load(open(self.trade_file))
        return trades[-limit:]
