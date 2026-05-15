"""
go-long-short - 多空双向交易技能
支持做多、做空和多空切换
"""

from .go_long_short import LongShortStrategy, DirectionSignal, SwitchSignal, Position, GoComponents

__all__ = ['LongShortStrategy', 'DirectionSignal', 'SwitchSignal', 'Position', 'GoComponents']
__version__ = '3.0.0'
