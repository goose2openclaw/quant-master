"""
Asset Monitor and Trader
=====================
资产管理与自主币种调换系统
"""

from .asset_monitor_trader import AssetMonitorTrader, AccountStatus, TradeDecision, Position, CoinPrediction

__all__ = [
    'AssetMonitorTrader',
    'AccountStatus',
    'TradeDecision',
    'Position',
    'CoinPrediction'
]
__version__ = '1.1.0'
