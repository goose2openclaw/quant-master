"""
G38 - 自主优化量化交易系统
整合 G37a + Top10交易员策略 + 资产管理
"""

from .g38 import G38, G38Signal, AssetMonitor, Top10TraderAnalyzer

__all__ = ['G38', 'G38Signal', 'AssetMonitor', 'Top10TraderAnalyzer']
__version__ = '2.0.0'
