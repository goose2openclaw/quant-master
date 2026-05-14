"""
Top 10 Trader to Crypto
====================
将十大交易员策略适配到加密货币市场
"""

from .top10_trader_crypto import (
    Top10TraderCrypto,
    Backtester,
    CryptoTraderProfile,
    MarketSignal,
    TradeDecision,
    TRADERS,
    COIN_CATEGORIES
)

__all__ = [
    'Top10TraderCrypto',
    'Backtester',
    'CryptoTraderProfile',
    'MarketSignal',
    'TradeDecision',
    'TRADERS',
    'COIN_CATEGORIES'
]
__version__ = '1.1.0'
