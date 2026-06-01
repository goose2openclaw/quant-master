"""
News Aggregator - 行情快讯
币圈快讯/行情播报/新闻聚合
"""
import sys
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class NewsItem:
    news_id: str
    title: str
    summary: str
    source: str
    category: str  # MARKET/DEVELOPMENT/REGULATION/SOCIAL
    sentiment: str  # BULLISH/BEARISH/NEUTRAL
    symbols: List[str]
    impact_score: float  # 0-100
    url: str
    timestamp: float

class NewsAggregator:
    """
    行情快讯聚合器
    - 多源聚合
    - 情绪分析
    - 影响评分
    """
    
    def __init__(self):
        self.name = "News Aggregator"
        self.news_sources = ['CoinDesk', 'CoinTelegraph', 'Twitter', 'Reddit', 'Glassnode']
        self.news: List[NewsItem] = []
        self.news_count = 0
    
    def fetch_latest_news(self, limit: int = 20) -> List[NewsItem]:
        """获取最新快讯"""
        # 模拟新闻数据
        headlines = [
            ("BTC ETF净流入创新高", "比特币ETF昨日净流入达$1.2B", "MARKET", "BULLISH", ["BTC"]),
            ("以太坊升级临近", "Pectra升级预计下月激活", "DEVELOPMENT", "BULLISH", ["ETH"]),
            ("SEC新主席表态", "SEC对加密监管态度转暖", "REGULATION", "BULLISH", ["BTC", "ETH"]),
            ("各大交易所存款激增", "CEX总存款达到$50B", "MARKET", "NEUTRAL", ["BTC", "ETH"]),
            (" whale地址异动", "某巨鲸地址转入$100M BTC", "SOCIAL", "BULLISH", ["BTC"]),
            ("做空协议漏洞", "某DeFi协议遭受攻击", "DEVELOPMENT", "BEARISH", ["SOL"]),
            ("做市商退出市场", "多家做市商暂停做市", "MARKET", "BEARISH", ["BTC"]),
            ("机构持仓创新高", "机构加密持仓超$100B", "MARKET", "BULLISH", ["BTC", "ETH"]),
        ]
        
        new_items = []
        for i, (title, summary, category, sentiment, symbols) in enumerate(headlines[:limit]):
            self.news_count += 1
            item = NewsItem(
                news_id=f"NEWS_{self.news_count:05d}",
                title=title,
                summary=summary,
                source=random.choice(self.news_sources),
                category=category,
                sentiment=sentiment,
                symbols=symbols,
                impact_score=random.uniform(50, 95),
                url=f"https://example.com/news/{self.news_count}",
                timestamp=time.time() - i * 300  # 5分钟间隔
            )
            new_items.append(item)
            self.news.append(item)
        
        # 按时间排序
        new_items.sort(key=lambda x: x.timestamp, reverse=True)
        return new_items
    
    def get_market_brief(self) -> Dict:
        """获取市场简报"""
        news = self.fetch_latest_news(10)
        
        bullish = sum(1 for n in news if n.sentiment == 'BULLISH')
        bearish = sum(1 for n in news if n.sentiment == 'BEARISH')
        neutral = sum(1 for n in news if n.sentiment == 'NEUTRAL')
        
        avg_impact = sum(n.impact_score for n in news) / len(news) if news else 0
        
        # 影响最大的新闻
        top_news = max(news, key=lambda x: x.impact_score) if news else None
        
        return {
            'timestamp': time.time(),
            'total_news': len(news),
            'sentiment_breakdown': {
                'bullish': bullish,
                'bearish': bearish,
                'neutral': neutral
            },
            'avg_impact': avg_impact,
            'top_news': {
                'title': top_news.title if top_news else None,
                'source': top_news.source if top_news else None,
                'impact': top_news.impact_score if top_news else 0
            },
            'news': [{
                'id': n.news_id,
                'title': n.title,
                'source': n.source,
                'sentiment': n.sentiment,
                'symbols': n.symbols,
                'impact': n.impact_score,
                'time_ago': self._time_ago(n.timestamp)
            } for n in news[:5]]
        }
    
    def get_news_by_symbol(self, symbol: str) -> List[NewsItem]:
        """获取特定币种新闻"""
        return [n for n in self.news if symbol in n.symbols]
    
    def get_news_by_sentiment(self, sentiment: str) -> List[NewsItem]:
        """按情绪筛选"""
        return [n for n in self.news if n.sentiment == sentiment]
    
    def _time_ago(self, timestamp: float) -> str:
        """转换为相对时间"""
        diff = time.time() - timestamp
        
        if diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff/60)}m ago"
        elif diff < 86400:
            return f"{int(diff/3600)}h ago"
        else:
            return f"{int(diff/86400)}d ago"
    
    def get_quick_brief(self) -> str:
        """获取快速简报"""
        brief = self.get_market_brief()
        
        emoji = "🟢" if brief['sentiment_breakdown']['bullish'] > brief['sentiment_breakdown']['bearish'] else "🔴"
        
        return (
            f"{emoji} 快讯 ({brief['total_news']}条)\n"
            f"🟢 {brief['sentiment_breakdown']['bullish']} | "
            f"🔴 {brief['sentiment_breakdown']['bearish']} | "
            f"⚪ {brief['sentiment_breakdown']['neutral']}\n"
            f"📊 均影响: {brief['avg_impact']:.0f}%\n"
            f"🔥 {brief['top_news']['title'] or 'N/A'}"
        )

if __name__ == '__main__':
    news_agg = NewsAggregator()
    
    print("=== News Aggregator ===\n")
    
    # 市场简报
    brief = news_agg.get_market_brief()
    print("Market Brief:")
    print(news_agg.get_quick_brief())
    
    print("\nLatest News:")
    for item in brief['news'][:5]:
        print(f"  [{item['sentiment']}] {item['title']}")
        print(f"    {item['source']} | {item['time_ago']} | Impact: {item['impact']:.0f}%")
