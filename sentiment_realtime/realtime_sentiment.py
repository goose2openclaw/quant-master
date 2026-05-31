"""
实时情绪分析 - 社交媒体实时监控
"""
import requests, time, json
from threading import Thread
from datetime import datetime

class SocialPost:
    """社交帖子"""
    def __init__(self, platform, author, content, timestamp, likes=0, shares=0, sentiment=0):
        self.platform = platform
        self.author = author
        self.content = content
        self.timestamp = timestamp
        self.likes = likes
        self.shares = shares
        self.sentiment = sentiment  # -1 to 1
        self.impact_score = 0

class RealtimeSentimentMonitor:
    """
    实时情绪监控
    来源: Twitter, Reddit, Telegram, Discord
    """
    def __init__(self, api_keys=None):
        self.api_keys = api_keys or {}
        self.posts = []
        self.alerts = []
        self.running = False
        self.thread = None
        self.callbacks = []
        
        # 关键词追踪
        self.keywords = {
            'bitcoin': ['bitcoin', 'btc', '₿'],
            'ethereum': ['ethereum', 'eth'],
            'binance': ['binance', 'bnb'],
            'defi': ['defi', 'yield', 'liquidity'],
            'nft': ['nft', 'opensea', 'blur'],
            'bullish': ['bull', 'moon', 'pump', 'lambo', 'to the moon'],
            'bearish': ['bear', 'dump', 'crash', 'rekt', 'capitulation']
        }
        
        # 情绪阈值
        self.alert_threshold = 0.7  # 极端情绪触发警报
    
    def start(self):
        """启动监控"""
        self.running = True
        self.thread = Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        print("[Sentiment] 实时监控启动")
    
    def stop(self):
        """停止监控"""
        self.running = False
        print("[Sentiment] 实时监控停止")
    
    def add_callback(self, callback):
        """添加回调"""
        self.callbacks.append(callback)
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 收集帖子
                self._fetch_twitter()
                self._fetch_reddit()
                self._fetch_telegram()
                
                # 分析情绪
                self._analyze_sentiment()
                
                # 检查警报
                self._check_alerts()
                
                time.sleep(60)  # 每分钟更新
            except Exception as e:
                print(f"[Sentiment] Error: {e}")
                time.sleep(300)
    
    def _fetch_twitter(self):
        """抓取Twitter"""
        # 简化实现
        pass
    
    def _fetch_reddit(self):
        """抓取Reddit"""
        try:
            r = requests.get(
                "https://www.reddit.com/r/CryptoCurrency/hot.json",
                params={'limit': 25},
                timeout=10
            )
            if r.status_code == 200:
                for post in r.json()['data']['children']:
                    d = post['data']
                    self.posts.append(SocialPost(
                        platform='reddit',
                        author=d['author'],
                        content=d['title'],
                        timestamp=datetime.fromtimestamp(d['created_utc']),
                        likes=d['score'],
                        shares=d['num_comments'],
                        sentiment=self._analyze_text(d['title'])
                    ))
        except:
            pass
    
    def _fetch_telegram(self):
        """抓取Telegram"""
        # 需要TG API
        pass
    
    def _analyze_text(self, text):
        """分析文本情绪"""
        text_lower = text.lower()
        
        bullish_keywords = ['bull', 'moon', 'pump', 'lambo', 'buy', 'long', 'gain']
        bearish_keywords = ['bear', 'dump', 'crash', 'sell', 'short', 'loss', 'rekt']
        
        score = 0
        for kw in bullish_keywords:
            if kw in text_lower:
                score += 0.2
        for kw in bearish_keywords:
            if kw in text_lower:
                score -= 0.2
        
        return max(-1, min(1, score))
    
    def _analyze_sentiment(self):
        """分析整体情绪"""
        if not self.posts:
            return 0
        
        # 加权平均 (点赞越多权重越高)
        total_weight = 0
        weighted_sum = 0
        
        for post in self.posts[-100:]:  # 最近100条
            weight = 1 + post.likes * 0.01 + post.shares * 0.05
            weighted_sum += post.sentiment * weight
            total_weight += weight
        
        avg_sentiment = weighted_sum / total_weight if total_weight > 0 else 0
        
        # 更新帖子情绪
        for post in self.posts:
            post.impact_score = abs(post.sentiment) * (1 + post.likes * 0.01)
        
        return avg_sentiment
    
    def _check_alerts(self):
        """检查情绪警报"""
        sentiment = self._analyze_sentiment()
        
        if abs(sentiment) >= self.alert_threshold:
            alert = {
                'time': datetime.now().isoformat(),
                'sentiment': sentiment,
                'type': 'extreme_bullish' if sentiment > 0 else 'extreme_bearish',
                'post_count': len(self.posts)
            }
            self.alerts.append(alert)
            
            # 触发回调
            for cb in self.callbacks:
                try:
                    cb(alert)
                except:
                    pass
        
        # 只保留最近50条警报
        self.alerts = self.alerts[-50:]
    
    def get_sentiment_score(self):
        """获取情绪分数"""
        return self._analyze_sentiment()
    
    def get_trending_topics(self):
        """获取热门话题"""
        topics = {}
        for post in self.posts[-100:]:
            for keyword, aliases in self.keywords.items():
                for alias in aliases:
                    if alias in post.content.lower():
                        topics[keyword] = topics.get(keyword, 0) + 1
        return sorted(topics.items(), key=lambda x: x[1], reverse=True)
    
    def get_emotion_distribution(self):
        """获取情绪分布"""
        recent = self.posts[-100:]
        
        bullish = sum(1 for p in recent if p.sentiment > 0.2)
        bearish = sum(1 for p in recent if p.sentiment < -0.2)
        neutral = len(recent) - bullish - bearish
        
        return {
            'bullish': bullish,
            'bearish': bearish,
            'neutral': neutral,
            'total': len(recent)
        }
