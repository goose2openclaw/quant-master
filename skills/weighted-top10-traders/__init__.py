"""
Weighted Top 10 Traders v2.0
===========================
蒸馏全球顶级交易员的交易模式和风格，形成加权组合系统

包含10位金融界公认顶级交易员:
1. 乔治·索罗斯 (George Soros)
2. 斯坦利·德鲁肯米勒 (Stanley Druckenmiller)
3. 布鲁斯·柯夫纳 (Bruce Kovner)
4. 迈克尔·马库斯 (Michael Marcus)
5. 保罗·都铎·琼斯 (Paul Tudor Jones)
6. 理查德·丹尼斯 (Richard Dennis)
7. 马丁·舒华兹 (Martin Schwartz)
8. 比尔·利普舒茨 (Bill Lipschutz)
9. 杰西·利弗莫尔 (Jesse Livermore)
10. 吉姆·罗杰斯 (Jim Rogers)
"""

from .weighted_top10_traders import (
    WeightedTop10Traders,
    TraderProfile,
    MarketSignal,
    TradingDecision
)

__all__ = [
    'WeightedTop10Traders',
    'TraderProfile', 
    'MarketSignal',
    'TradingDecision'
]
__version__ = '2.0.0'
