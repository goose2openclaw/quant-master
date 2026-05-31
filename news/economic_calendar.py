"""
财经日历 + 事件提醒
"""
import requests, time, json
from datetime import datetime, timedelta
from threading import Thread

class EconomicEvent:
    def __init__(self, date, time_str, country, event, impact, previous, forecast, actual):
        self.date = date
        self.time_str = time_str
        self.country = country
        self.event = event
        self.impact = impact  # high/medium/low
        self.previous = previous
        self.forecast = forecast
        self.actual = actual
        self.alert_sent = False

class EconomicCalendar:
    """
    财经日历
    重要经济事件: 非农、CPI、利率决议等
    """
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.events = []
        self.alerts = []
    
    def fetch_events(self, start_date=None, end_date=None):
        """获取财经日历"""
        # 使用 investing.com 经济日历数据 (简化)
        try:
            # 硬编码常见事件
            common_events = [
                {'date': '2024-01-10', 'time': '21:30', 'country': 'US', 'event': 'Non-Farm Payrolls', 'impact': 'high'},
                {'date': '2024-01-15', 'time': '21:30', 'country': 'US', 'event': 'CPI YoY', 'impact': 'high'},
                {'date': '2024-02-01', 'time': '03:00', 'country': 'US', 'event': 'FOMC Rate Decision', 'impact': 'high'},
                {'date': '2024-03-20', 'time': '03:00', 'country': 'US', 'event': 'FOMC Rate Decision', 'impact': 'high'},
            ]
            
            self.events = [
                EconomicEvent(
                    e['date'], e['time'], e['country'], e['event'],
                    e['impact'], None, None, None
                ) for e in common_events
            ]
            return self.events
        except Exception as e:
            print(f"[Calendar] Fetch error: {e}")
        return []
    
    def get_upcoming(self, hours=24):
        """获取未来事件"""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        upcoming = []
        
        for event in self.events:
            event_dt = datetime.strptime(f"{event.date} {event.time_str}", "%Y-%m-%d %H:%M")
            if now <= event_dt <= cutoff:
                upcoming.append({
                    'date': event.date,
                    'time': event.time_str,
                    'country': event.country,
                    'event': event.event,
                    'impact': event.impact,
                    'minutes_until': int((event_dt - now).total_seconds() / 60)
                })
        
        return upcoming
    
    def get_high_impact_events(self):
        """获取高影响力事件"""
        return [e for e in self.events if e.impact == 'high']

class NewsMonitor:
    """新闻监控"""
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.news = []
        self.keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'binance', 'crypto', 'sec', 'etf']
    
    def fetch_crypto_news(self, limit=20):
        """获取加密货币新闻"""
        try:
            r = requests.get(
                "https://cryptopanic.com/api/v1/posts/",
                params={'auth_token': 'public', 'kind': 'news', 'limit': limit},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json().get('results', [])
                for item in data:
                    news_item = {
                        'time': item.get('published_at'),
                        'title': item.get('title'),
                        'source': item.get('source', {}).get('title'),
                        'url': item.get('url'),
                        'votes': item.get('votes', {}).get('positive', 0)
                    }
                    self.news.append(news_item)
                return self.news[-limit:]
        except Exception as e:
            print(f"[News] Fetch error: {e}")
        return []
    
    def search_news(self, keyword):
        """搜索新闻"""
        all_news = self.fetch_crypto_news(100)
        return [n for n in all_news if keyword.lower() in n['title'].lower()]
    
    def get_sentiment(self):
        """获取新闻情绪"""
        if not self.news:
            self.fetch_crypto_news(50)
        
        if not self.news:
            return {'score': 0, 'positive': 0, 'negative': 0, 'neutral': 0}
        
        positive = sum(1 for n in self.news if n['votes'] > 5)
        negative = sum(1 for n in self.news if n['votes'] < 0)
        neutral = len(self.news) - positive - negative
        
        score = (positive - negative) / len(self.news) * 100 if self.news else 0
        
        return {
            'score': score,
            'positive': positive,
            'negative': negative,
            'neutral': neutral
        }
