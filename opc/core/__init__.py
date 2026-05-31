"""
OPC Core - One Powerful Core
整合所有模块的统一核心
"""
from .market import get_prices, get_all_balances, get_market_signal
from .strategy import scan_markets
from .executor import execute_buy, execute_sell
from .memory import save_trade, get_trade_history, analyze_performance, log_learning
from .config import *

print("OPC Core loaded - Market/Strategy/Executor/Memory integrated")
