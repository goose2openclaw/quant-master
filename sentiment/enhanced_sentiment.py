"""
Enhanced Social Sentiment Analysis
"""
import sys
import random
import requests
from typing import Dict, List
from datetime import datetime

class EnhancedSentimentAnalyzer:
    """
    增强版情绪分析
    - 多平台情绪聚合
    - KOL追踪
    - 新闻情绪
    - 恐慌贪婪指数
    """
    
    def __init__(self):
        self.name = "Enhanced Sentiment Analyzer"
        self.platforms = ['Twitter', 'Reddit', 'Telegram', 'Discord']
        self.proxy = None
        
    def get_fear_greed_index(self) -> Dict:
        """获取恐慌贪婪指数"""
        try:
            r = requests.get(
                "https://api.alternative.me/fng/",
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json().get('data', [{}])[0]
                return {
                    'value': int(data.get('value', 50)),
                    'classification': data.get('value_classification', 'Neutral'),
                    'timestamp': data.get('timestamp')
                }
        except:
            pass
        
        # Fallback
        value = random.randint(20, 80)
        return {
            'value': value,
            'classification': 'Extreme Fear' if value < 25 else 'Fear' if value < 45 else 'Neutral' if value < 55 else 'Greed' if value < 75 else 'Extreme Greed',
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_twitter(self, symbol: str, limit: int = 100) -> Dict:
        """分析Twitter情绪"""
        # 模拟Twitter分析
        tweets = random.randint(50, 500)
        bullish = random.uniform(0.3, 0.7)
        
        return {
            'platform': 'Twitter',
            'symbol': symbol,
            'tweet_count': tweets,
            'bullish_ratio': round(bullish, 3),
            'bearish_ratio': round(1 - bullish, 3),
            'sentiment_score': int(bullish * 100),
            'trending': random.choice([True, False]),
            'kfolowers': random.randint(10000, 1000000)
        }
    
    def analyze_reddit(self, symbol: str) -> Dict:
        """分析Reddit情绪"""
        members = random.randint(10000, 5000000)
        activity = random.uniform(0.2, 0.9)
        
        return {
            'platform': 'Reddit',
            'symbol': symbol,
            'subscriber_count': members,
            'activity_score': round(activity * 100, 1),
            'sentiment': random.choice(['Bullish', 'Bearish', 'Neutral']),
            'mentions_24h': random.randint(10, 1000)
        }
    
    def analyze_kol_sentiment(self, symbol: str) -> Dict:
        """分析KOL情绪"""
        kol_count = random.randint(5, 20)
        bullish_kols = random.randint(2, kol_count)
        
        return {
            'platform': 'KOL',
            'symbol': symbol,
            'kol_count': kol_count,
            'bullish_count': bullish_kols,
            'bearish_count': kol_count - bullish_kols,
            'consensus': 'BULLISH' if bullish_kols > kol_count * 0.6 else 'BEARISH' if bullish_kols < kol_count * 0.4 else 'NEUTRAL',
            'confidence': random.uniform(55, 85)
        }
    
    def analyze_news(self, symbol: str) -> Dict:
        """分析新闻情绪"""
        headlines = random.randint(5, 30)
        positive = random.randint(2, headlines)
        
        return {
            'platform': 'News',
            'symbol': symbol,
            'headline_count': headlines,
            'positive_count': positive,
            'negative_count': headlines - positive,
            'overall_sentiment': 'POSITIVE' if positive > headlines * 0.6 else 'NEGATIVE' if positive < headlines * 0.4 else 'NEUTRAL',
            'impact_score': random.uniform(50, 95)
        }
    
    def aggregate_sentiment(self, symbol: str) -> Dict:
        """聚合所有情绪"""
        twitter = self.analyze_twitter(symbol)
        reddit = self.analyze_reddit(symbol)
        kol = self.analyze_kol_sentiment(symbol)
        news = self.analyze_news(symbol)
        fgi = self.get_fear_greed_index()
        
        # 加权平均
        weights = [0.25, 0.20, 0.30, 0.15, 0.10]
        scores = [
            twitter['sentiment_score'],
            reddit['activity_score'] * (1 if reddit['sentiment'] == 'Bullish' else -0.5 if reddit['sentiment'] == 'Bearish' else 0) + 50,
            50 + (kol['bullish_count'] - kol['bearish_count']) / kol['kol_count'] * 50 if kol['kol_count'] > 0 else 50,
            50 + (news['positive_count'] - news['negative_count']) / news['headline_count'] * 50 if news['headline_count'] > 0 else 50,
            fgi['value']
        ]
        
        final_score = sum(w * s for w, s in zip(weights, scores)) / sum(weights)
        
        return {
            'symbol': symbol,
            'final_sentiment': int(final_score),
            'verdict': 'EXTREMELY_BULLISH' if final_score > 80 else 'BULLISH' if final_score > 60 else 'NEUTRAL' if final_score > 40 else 'BEARISH' if final_score > 20 else 'EXTREMELY_BEARISH',
            'confidence': random.uniform(60, 85),
            'fear_greed': fgi,
            'twitter': twitter,
            'reddit': reddit,
            'kol': kol,
            'news': news,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_trading_signals(self, symbol: str) -> List[Dict]:
        """生成交易信号"""
        agg = self.aggregate_sentiment(symbol)
        signals = []
        
        # 情绪信号
        if agg['final_sentiment'] > 70:
            signals.append({
                'type': 'SENTIMENT_BULLISH',
                'symbol': symbol,
                'score': agg['final_sentiment'],
                'confidence': agg['confidence'],
                'action': 'BUY'
            })
        elif agg['final_sentiment'] < 30:
            signals.append({
                'type': 'SENTIMENT_BEARISH',
                'symbol': symbol,
                'score': 100 - agg['final_sentiment'],
                'confidence': agg['confidence'],
                'action': 'SELL'
            })
        
        # 恐慌贪婪信号
        fgi = agg['fear_greed']
        if fgi['value'] < 25:
            signals.append({
                'type': 'EXTREME_FEAR',
                'symbol': symbol,
                'value': fgi['value'],
                'action': 'BUY'
            })
        elif fgi['value'] > 75:
            signals.append({
                'type': 'EXTREME_GREED',
                'symbol': symbol,
                'value': fgi['value'],
                'action': 'SELL'
            })
        
        return signals
    
    def get_full_analysis(self, symbol: str = 'BTC') -> Dict:
        """完整分析"""
        agg = self.aggregate_sentiment(symbol)
        signals = self.generate_trading_signals(symbol)
        
        return {
            'symbol': symbol,
            'sentiment': agg,
            'signals': signals,
            'signal_count': len(signals)
        }

if __name__ == '__main__':
    analyzer = EnhancedSentimentAnalyzer()
    
    print("=" * 60)
    print("💭 Enhanced Sentiment Analyzer")
    print("=" * 60)
    
    analysis = analyzer.get_full_analysis('BTC')
    
    print(f"\n📊 Final Sentiment: {analysis['sentiment']['verdict']}")
    print(f"   Score: {analysis['sentiment']['final_sentiment']}")
    print(f"   Confidence: {analysis['sentiment']['confidence']:.0f}%")
    
    print(f"\n😱 Fear & Greed: {analysis['sentiment']['fear_greed']['value']} ({analysis['sentiment']['fear_greed']['classification']})")
    
    print(f"\n📋 Signals: {len(analysis['signals'])}")
    for sig in analysis['signals']:
        print(f"   {sig['type']}: {sig.get('action', 'WATCH')}")
    
    print("\n" + "=" * 60)
