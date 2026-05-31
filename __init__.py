"""
QuantMaster - QMT + vnpy 融合量化平台
"""
from .quant_master import QuantMaster
from .strategies import RSIStrategy, MACDStrategy, BollingerStrategy, MomentumStrategy
from .factors.technical import TechnicalFactors
from .backtest.engine import BacktestEngine

__version__ = "3.1"
__all__ = [
    'QuantMaster',
    'RSIStrategy', 'MACDStrategy', 'BollingerStrategy', 'MomentumStrategy',
    'TechnicalFactors',
    'BacktestEngine'
]
