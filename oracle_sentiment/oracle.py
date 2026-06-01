"""
Oracle & Market Sentiment Aggregator
MiroFish / CoinGecko / Twitter/KOL / RSI信号
"""
import sys
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class SentimentSignal:
    source: str
    symbol: str
    sentiment: str  # BULLISH/BEARISH/NEUTRAL
    confidence: float
    rsi: float
    volume_ratio: float
    timestamp: float

@dataclass
class TrendData:
    symbol: str
    trend_count: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    dominant_sentiment: str
    avg_confidence: float

class OracleSentimentAggregator:
    """
    Oracle 市场情绪聚合器
    - 多数据源聚合
    - 情绪信号生成
    - 趋势监控
    """
    
    def __init__(self):
        self.name = "Oracle Sentiment"
        self.sources = ['MiroFish', 'CoinGecko', 'Twitter', 'KOL', 'Glassnode']
        self.trends: Dict[str, TrendData] = {}
        self.signals: List[SentimentSignal] = []
    
    def fetch_all_signals(self, symbol: str = 'BTC') -> List[SentimentSignal]:
        """获取所有源信号"""
        signals = []
        
        for source in self.sources:
            signal = self._fetch_source_signal(source, symbol)
            signals.append(signal)
        
        self.signals = signals
        return signals
    
    def _fetch_source_signal(self, source: str, symbol: str) -> SentimentSignal:
        """从单个源获取信号"""
        # 模拟数据
        rsi = random.uniform(30, 70)
        sentiment = 'BULLISH' if rsi > 55 else 'BEARISH' if rsi < 45 else 'NEUTRAL'
        
        return SentimentSignal(
            source=source,
            symbol=symbol,
            sentiment=sentiment,
            confidence=random.uniform(0.6, 0.95),
            rsi=rsi,
            volume_ratio=random.uniform(0.8, 1.5),
            timestamp=time.time()
        )
    
    def get_aggregated_sentiment(self, symbol: str = 'BTC') -> Dict:
        """聚合情绪"""
        signals = self.fetch_all_signals(symbol)
        
        bullish = sum(1 for s in signals if s.sentiment == 'BULLISH')
        bearish = sum(1 for s in signals if s.sentiment == 'BEARISH')
        neutral = sum(1 for s in signals if s.sentiment == 'NEUTRAL')
        
        avg_rsi = sum(s.rsi for s in signals) / len(signals)
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        
        # 主导情绪
        if bullish > bearish and bullish > neutral:
            dominant = 'BULLISH'
        elif bearish > bullish and bearish > neutral:
            dominant = 'BEARISH'
        else:
            dominant = 'NEUTRAL'
        
        return {
            'symbol': symbol,
            'dominant_sentiment': dominant,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'neutral_count': neutral,
            'avg_rsi': avg_rsi,
            'avg_confidence': avg_confidence,
            'signals': signals,
            'timestamp': time.time()
        }
    
    def get_trends(self, limit: int = 123) -> List[TrendData]:
        """获取趋势列表"""
        symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT']
        trends = []
        
        for sym in symbols[:min(limit, len(symbols))]:
            sentiment = self.get_aggregated_sentiment(sym)
            
            trends.append(TrendData(
                symbol=sym,
                trend_count=random.randint(50, 200),
                bullish_count=sentiment['bullish_count'],
                bearish_count=sentiment['bearish_count'],
                neutral_count=sentiment['neutral_count'],
                dominant_sentiment=sentiment['dominant_sentiment'],
                avg_confidence=sentiment['avg_confidence']
            ))
        
        self.trends = {t.symbol: t for t in trends}
        return trends

if __name__ == '__main__':
    oracle = OracleSentimentAggregator()
    
    print("=== Oracle & Sentiment ===\n")
    
    # BTC情绪
    btc_sent = oracle.get_aggregated_sentiment('BTC')
    print(f"BTC Sentiment: {btc_sent['dominant_sentiment']}")
    print(f"  Sources: 🟢{btc_sent['bullish_count']} 🔴{btc_sent['bearish_count']} ⚪{btc_sent['neutral_count']}")
    print(f"  Avg RSI: {btc_sent['avg_rsi']:.1f}")
    print(f"  Confidence: {btc_sent['avg_confidence']:.1%}")
    
    # 趋势
    trends = oracle.get_trends(10)
    print(f"\nTop Trends ({len(trends)}):")
    for t in trends[:5]:
        print(f"  {t.symbol}: {t.dominant_sentiment} ({t.trend_count} trends)")
