"""
QuantMaster Modules - Q@C v6 集成模块

模块列表:
- indicators: 100+ 技术指标 (从Lean/TradingView克隆)
- multi_exchange: 多交易所支持 (Binance/Bybit/OKX/Hyperliquid)
- alerts: TradingView风格警报系统
- ai_decision: Kronos风格AI决策系统
- backtest: Lean专业回测引擎
"""
__version__ = "6.0.0"

from .indicators import TechnicalIndicators, MultiTimeFrameAnalyzer, PivotPoints
from .multi_exchange import ExchangeRouter, BinanceAPI, BybitAPI, OKXAPI, HyperliquidAPI
from .alerts import AlertManager, AlertType, AlertPriority, AlertCondition
from .ai_decision import AIDecisionEngine, DecisionType, ConfidenceLevel
from .backtest import BacktestEngine, StrategyLibrary

__all__ = [
    'TechnicalIndicators',
    'MultiTimeFrameAnalyzer', 
    'PivotPoints',
    'ExchangeRouter',
    'BinanceAPI',
    'BybitAPI',
    'OKXAPI',
    'HyperliquidAPI',
    'AlertManager',
    'AlertType',
    'AlertPriority',
    'AlertCondition',
    'AIDecisionEngine',
    'DecisionType',
    'ConfidenceLevel',
    'BacktestEngine',
    'StrategyLibrary'
]
