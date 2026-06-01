"""
社交情绪分析 - Twitter/Reddit/社区
"""
import requests, time, json
from threading import Thread

class SocialSentiment:
    """
    社交媒体情绪分析
    """
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.twitter_token = None
        self.sentiment_cache = {}
        self.FearGreedIndex = 50
    
    def get_fear_greed_index(self):
        """获取贪婪恐惧指数"""
        try:
            r = requests.get(
                "https://api.alternative.me/fng/",
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json().get('data', [{}])[0]
                self.FearGreedIndex = int(data.get('value', 50))
                return {
                    'value': self.FearGreedIndex,
                    'classification': data.get('value_classification', 'Neutral'),
                    'timestamp': data.get('timestamp')
                }
        except Exception as e:
            print(f"[Sentiment] Fear/Greed API error: {e}")
        return {'value': 50, 'classification': 'Neutral'}
    
    def analyze_twitter(self, symbol, limit=100):
        """分析Twitter情绪"""
        # 简化: 使用关键词搜索
        try:
            # 如果有Twitter API token
            if self.twitter_token:
                headers = {'Authorization': f'Bearer {self.twitter_token}'}
                r = requests.get(
                    f"https://api.twitter.com/2/tweets/search/recent",
                    params={'query': f'${symbol} OR {symbol} crypto', 'max_results': limit},
                    headers=headers, proxies=self.proxy, timeout=10
                )
                if r.status_code == 200:
                    tweets = r.json().get('data', [])
                    return self._analyze_tweets(tweets)
        except:
            pass
        
        # 无token时返回模拟数据
        return {'score': 50, 'positive': 50, 'negative': 30, 'neutral': 20}
    
    def _analyze_tweets(self, tweets):
        """分析推文情绪 (简化版)"""
        positive_keywords = ['bull', 'moon', 'pump', 'gain', 'up', 'buy', 'long', 'hodl']
        negative_keywords = ['bear', 'dump', 'crash', 'loss', 'down', 'sell', 'short', 'scam']
        
        scores = []
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            score = 0
            for kw in positive_keywords:
                if kw in text:
                    score += 1
            for kw in negative_keywords:
                if kw in text:
                    score -= 1
            scores.append(score)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        normalized = max(0, min(100, 50 + avg_score * 10))
        
        return {
            'score': normalized,
            'positive': sum(1 for s in scores if s > 0),
            'negative': sum(1 for s in scores if s < 0),
            'neutral': sum(1 for s in scores if s == 0),
            'tweet_count': len(tweets)
        }
    
    def get_community_sentiment(self, symbol):
        """获取社区情绪"""
        # 综合多个来源
        fg = self.get_fear_greed_index()
        twitter = self.analyze_twitter(symbol)
        
        # 加权平均
        combined = (fg['value'] * 0.4 + twitter['score'] * 0.6)
        
        return {
            'combined_score': combined,
            'fear_greed': fg,
            'twitter': twitter,
            'interpretation': self._interpret_sentiment(combined)
        }
    
    def _interpret_sentiment(self, score):
        if score >= 75:
            return "极度贪婪"
        elif score >= 60:
            return "贪婪"
        elif score >= 40:
            return "中性"
        elif score >= 25:
            return "恐惧"
        else:
            return "极度恐惧"
