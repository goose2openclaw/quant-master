#!/usr/bin/env python3
"""
go - 加密量化交易系列技能包
=========================
整合所有go系列模块的统一接口
"""

from .go_core import GoCore
from .go_thermo import GoThermo
from .go_noise import GoNoise
from .go_fit import GoFit
from .go_ensemble import GoEnsemble
from .go_meta import GoMeta
from .go_detect import GoDetect
from .go_contrarian import GoContrarian
from .go_reverse import GoReverse
from .go_fastlane import GoFastLane
from .go_pool import GoPool
from .go_orderbook import GoOrderBook
from .go_liquidation import GoLiquidation
from .go_cross_exchange import GoCrossExchange

class GoQuantSystem:
    """整合所有模块的量化系统"""
    
    def __init__(self):
        self.core = GoCore()
        self.thermo = GoThermo()
        self.noise = GoNoise()
        self.fit = GoFit()
        self.ensemble = GoEnsemble()
        self.meta = GoMeta()
        self.detect = GoDetect()
        self.contrarian = GoContrarian()
        self.reverse = GoReverse()
        self.fastlane = GoFastLane()
        self.pool = GoPool()
        self.orderbook = GoOrderBook()
        self.liquidation = GoLiquidation()
        self.cross_exchange = GoCrossExchange()
    
    def run_all(self, symbol: str) -> dict:
        """运行所有模块分析"""
        results = {
            'symbol': symbol,
            'modules': {},
            'composite': {}
        }
        
        # 各模块分析
        results['modules']['go-core'] = self.core.predict(symbol)
        results['modules']['go-thermo'] = self.thermo.analyze(symbol)
        results['modules']['go-noise'] = self.noise.analyze(symbol)
        results['modules']['go-fit'] = self.fit.fit(symbol)
        results['modules']['go-detect'] = self.detect.detect(symbol)
        results['modules']['go-contrarian'] = self.contrarian.analyze(symbol)
        results['modules']['go-reverse'] = self.reverse.analyze(symbol)
        results['modules']['go-fastlane'] = self.fastlane.scan(symbol)
        results['modules']['go-pool'] = self.pool.analyze(symbol)
        results['modules']['go-orderbook'] = self.orderbook.analyze(symbol)
        results['modules']['go-liquidation'] = self.liquidation.analyze(symbol)
        
        # 综合评分
        signals = []
        weights = {
            'go-core': 0.25,
            'go-thermo': 0.10,
            'go-noise': 0.10,
            'go-fit': 0.15,
            'go-pool': 0.15,
            'go-detect': 0.15,
            'go-fastlane': 0.10
        }
        
        for name, data in results['modules'].items():
            if 'signal' in data:
                signals.append((name, data['signal'], weights.get(name, 0.1)))
        
        total_weight = sum(w for _, _, w in signals)
        composite_signal = sum(s * w for _, s, w in signals) / total_weight
        confidence = sum(abs(s) * w for _, s, w in signals) / total_weight
        
        results['composite'] = {
            'signal': composite_signal,
            'confidence': confidence,
            'direction': 'long' if composite_signal > 0 else 'short' if composite_signal < 0 else 'neutral'
        }
        
        return results
    
    def get_trade_signal(self, symbol: str) -> dict:
        """获取交易信号"""
        analysis = self.run_all(symbol)
        composite = analysis['composite']
        
        return {
            'symbol': symbol,
            'action': composite['direction'],
            'confidence': composite['confidence'],
            'signal': composite['signal'],
            'modules_used': list(analysis['modules'].keys())
        }

__all__ = [
    'GoCore', 'GoThermo', 'GoNoise', 'GoFit',
    'GoEnsemble', 'GoMeta', 'GoDetect', 'GoContrarian',
    'GoReverse', 'GoFastLane', 'GoPool', 'GoOrderBook',
    'GoLiquidation', 'GoCrossExchange', 'GoQuantSystem'
]
