"""
G39 - 全集成自主量化交易系统
整合 G38 + 轮动 + 多空 + ETF流动性 + 资产管理
具备自主优化能力
"""

from .g39 import G39, G39Signal, AccountStatus, G39Optimizer

__all__ = ['G39', 'G39Signal', 'AccountStatus', 'G39Optimizer']
__version__ = '3.0.0'
