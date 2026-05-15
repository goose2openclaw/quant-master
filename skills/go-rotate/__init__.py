"""
go-rotate - 轮动策略技能
板块轮动和币种轮动，与撞球(pool)策略形成互补
"""

from .go_rotate import RotationStrategy, SectorRotation, PoolRotateSynergy, RotationSignal

__all__ = ['RotationStrategy', 'SectorRotation', 'PoolRotateSynergy', 'RotationSignal']
__version__ = '3.0.0'
