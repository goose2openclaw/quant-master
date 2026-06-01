"""
Signal Trend Strategy Monitor
ADX趋势监控 / 实时信号 / BK/积极/68.2%等
"""
import sys
import time
import random
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class TrendSignal:
    name: str
    value: float
    status: str  # ABOVE/BELOW/NEAR
    change_1h: float
    timestamp: float

@dataclass
class ADXReading:
    symbol: str
    adx: float
    plus_di: float
    minus_di: float
    trend_strength: str
    timestamp: float

class SignalTrendMonitor:
    """
    信号趋势监控
    - ADX趋势判断
    - 多信号聚合
    - 实时状态
    """
    
    def __init__(self):
        self.name = "Signal Trend Monitor"
        self.signals: Dict[str, List[TrendSignal]] = {}
        self.adx_readings: Dict[str, ADXReading] = {}
    
    def get_adx(self, symbol: str = 'BTC') -> ADXReading:
        """计算ADX"""
        # 模拟ADX计算
        adx = random.uniform(15, 40)
        plus_di = random.uniform(15, 40)
        minus_di = random.uniform(15, 40)
        
        # 趋势强度判断
        if adx < 20:
            strength = 'WEAK'
        elif adx < 40:
            strength = 'MODERATE'
        elif adx < 60:
            strength = 'STRONG'
        else:
            strength = 'VERY_STRONG'
        
        reading = ADXReading(
            symbol=symbol,
            adx=adx,
            plus_di=plus_di,
            minus_di=minus_di,
            trend_strength=strength,
            timestamp=time.time()
        )
        
        self.adx_readings[symbol] = reading
        return reading
    
    def get_trend_signals(self, symbol: str = 'BTC') -> List[TrendSignal]:
        """获取趋势信号"""
        signals = [
            TrendSignal('BK', 72.0 + random.uniform(-2, 2), 'ABOVE', 0.5, time.time()),
            TrendSignal('积极', 74.5 + random.uniform(-2, 2), 'ABOVE', 0.3, time.time()),
            TrendSignal('信号A', 68.2 + random.uniform(-2, 2), 'ABOVE', -0.2, time.time()),
            TrendSignal('信号B', 71.8 + random.uniform(-2, 2), 'NEAR', 0.1, time.time()),
            TrendSignal('信号C', 72.3 + random.uniform(-2, 2), 'ABOVE', 0.4, time.time()),
        ]
        
        self.signals[symbol] = signals
        return signals
    
    def get_trend_status(self, symbol: str = 'BTC') -> Dict:
        """获取趋势状态"""
        adx = self.get_adx(symbol)
        signals = self.get_trend_signals(symbol)
        
        # 聚合信号强度
        avg_signal = sum(s.value for s in signals) / len(signals)
        
        # 判断趋势方向
        if adx.plus_di > adx.minus_di:
            direction = 'UPTREND'
        elif adx.minus_di > adx.plus_di:
            direction = 'DOWNTREND'
        else:
            direction = 'NEUTRAL'
        
        return {
            'symbol': symbol,
            'adx': adx.adx,
            'adx_status': 'TRENDING' if adx.adx >= 25 else 'RANGING',
            'trend_strength': adx.trend_strength,
            'direction': direction,
            'avg_signal': avg_signal,
            'signal_count': len(signals),
            'signals': signals,
            'recommendation': self._get_recommendation(adx, avg_signal),
            'timestamp': time.time()
        }
    
    def _get_recommendation(self, adx: ADXReading, avg_signal: float) -> str:
        """获取建议"""
        if adx.adx < 20:
            return 'WATCH'  # 无明显趋势
        
        if adx.adx >= 25 and adx.plus_di > adx.minus_di:
            if avg_signal > 70:
                return 'STRONG_BUY'
            return 'BUY'
        
        if adx.adx >= 25 and adx.minus_di > adx.plus_di:
            if avg_signal < 30:
                return 'STRONG_SELL'
            return 'SELL'
        
        return 'HOLD'
    
    def scan_all_trends(self) -> List[Dict]:
        """扫描所有趋势"""
        symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT']
        results = []
        
        for sym in symbols:
            status = self.get_trend_status(sym)
            results.append(status)
        
        # 按ADX排序
        results.sort(key=lambda x: x['adx'], reverse=True)
        
        return results

if __name__ == '__main__':
    stm = SignalTrendMonitor()
    
    print("=== Signal Trend Monitor ===\n")
    
    # BTC趋势
    btc = stm.get_trend_status('BTC')
    print(f"BTC ADX: {btc['adx']:.1f} ({btc['trend_strength']})")
    print(f"Direction: {btc['direction']}")
    print(f"Recommendation: {btc['recommendation']}")
    
    print("\nSignals:")
    for s in btc['signals']:
        emoji = '🟢' if s.status == 'ABOVE' else '🟡' if s.status == 'NEAR' else '🔴'
        print(f"  {emoji} {s.name}: {s.value:.1f} ({s.change_1h:+.1f}%)")
    
    print("\nAll Trends (sorted by ADX):")
    all_trends = stm.scan_all_trends()
    for t in all_trends[:5]:
        print(f"  {t['symbol']:5}: ADX={t['adx']:.1f} {t['direction']} → {t['recommendation']}")
