"""
NLP交易信号 - 自然语言处理
Bloomberg GPT级别
"""
import re, json
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class TradingSignal:
    symbol: str
    sentiment: float  # -1 to 1
    confidence: float  # 0 to 1
    source: str
    headline: str
    action: str  # BUY, SELL, NEUTRAL
    reasoning: str

class NLPSentimentAnalyzer:
    """NLP情感分析"""
    def __init__(self):
        # 情感词典
        self.positive_words = {
            'bullish', 'buy', 'long', 'moon', 'pump', 'gain', 'profit', 'up', 'rise',
            'surge', 'rally', 'growth', 'positive', 'upgrade', 'outperform', 'buy',
            'breakout', 'omentum', 'accumulate', 'undervalued', 'cheap'
        }
        self.negative_words = {
            'bearish', 'sell', 'short', 'dump', 'crash', 'loss', 'down', 'fall',
            'decline', 'drop', 'sell', 'downgrade', 'underperform', 'bubble',
            'overvalued', 'expensive', 'risk', 'warning', 'rekt', 'capitulation'
        }
        
        # 强度修饰词
        self.strong_modifiers = {'very', 'extremely', 'strongly', 'massively', 'huge'}
        self.weak_modifiers = {'slightly', 'somewhat', 'maybe', 'perhaps'}
    
    def analyze(self, text):
        """分析情感"""
        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)
        
        positive_count = sum(1 for w in words if w in self.positive_words)
        negative_count = sum(1 for w in words if w in self.negative_words)
        
        # 计算修饰
        modifier = 1.0
        for w in words:
            if w in self.strong_modifiers:
                modifier = 1.5
            elif w in self.weak_modifiers:
                modifier = 0.5
        
        # 计算得分
        net = (positive_count - negative_count) * modifier
        sentiment = max(-1, min(1, net / (len(words) + 1) * 10))
        
        # 置信度
        total_signals = positive_count + negative_count
        confidence = min(1.0, total_signals / 5)
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_signals': positive_count,
            'negative_signals': negative_count
        }

class NewsSignalExtractor:
    """新闻信号提取"""
    def __init__(self):
        self.nlp = NLPSentimentAnalyzer()
        
        # 交易对模式
        self.symbol_patterns = [
            (r'\$?BTC(?:itcoin)?', 'BTC'),
            (r'\$?ETH(?:ereum)?', 'ETH'),
            (r'\$?BNB?', 'BNB'),
            (r'\$?SOL(?:ana)?', 'SOL'),
            (r'\$?XRP?', 'XRP'),
            (r'\$?ADA?', 'ADA'),
            (r'\$?DOGE?', 'DOGE'),
        ]
        
        # 价格相关模式
        self.price_patterns = [
            (r'target\s*\$?([\d,]+)', 'price_target'),
            (r'support\s*\$?([\d,]+)', 'support'),
            (r'resistance\s*\$?([\d,]+)', 'resistance'),
            (r'break(?:out)?\s*(?:above\s*)?\$?([\d,]+)', 'breakout'),
        ]
    
    def extract_signal(self, headline, body=None):
        """从新闻提取交易信号"""
        text = headline + (body or '')
        
        # 提取标的
        symbols = set()
        for pattern, symbol in self.symbol_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                symbols.add(symbol)
        
        # 情感分析
        sentiment = self.nlp.analyze(text)
        
        # 提取价格信息
        price_targets = []
        for pattern, ptype in self.price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                price_targets.append({'type': ptype, 'price': float(match.replace(',', ''))})
        
        # 生成信号
        action = 'NEUTRAL'
        if sentiment['sentiment'] > 0.3 and sentiment['confidence'] > 0.5:
            action = 'BUY'
        elif sentiment['sentiment'] < -0.3 and sentiment['confidence'] > 0.5:
            action = 'SELL'
        
        return TradingSignal(
            symbol=list(symbols)[0] if symbols else 'UNKNOWN',
            sentiment=sentiment['sentiment'],
            confidence=sentiment['confidence'],
            source='news',
            headline=headline,
            action=action,
            reasoning=f"Sentiment: {sentiment['sentiment']:.2f}, Confidence: {sentiment['confidence']:.2f}"
        )

class EarningsAnalyzer:
    """财报分析"""
    def __init__(self):
        self.metrics_patterns = {
            'revenue': r'revenue[:\s]*\$?([\d,]+)',
            'eps': r'EPS[:\s]*\$?([\d,]+)',
            'growth': r'growth[:\s]*([\d,]+)%\s*(?:YoY|QoQ)',
        }
    
    def analyze_earnings(self, text):
        """分析财报"""
        metrics = {}
        
        for metric, pattern in self.metrics_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics[metric] = float(match.group(1).replace(',', ''))
        
        # 判断
        sentiment = 0
        if 'revenue' in metrics and metrics['revenue'] > 0:
            sentiment += 0.3
        if 'growth' in metrics and metrics['growth'] > 20:
            sentiment += 0.4
        if 'eps' in metrics and metrics['eps'] > 0:
            sentiment += 0.3
        
        return {
            'metrics': metrics,
            'sentiment': max(-1, min(1, sentiment)),
            'action': 'BUY' if sentiment > 0.5 else 'NEUTRAL'
        }

class RegulatoryAnalyzer:
    """监管政策分析"""
    def __init__(self):
        self.regulatory_keywords = {
            'SEC': {'negative': ['lawsuit', 'fraud', 'investigation', 'violation'], 
                    'positive': ['approval', 'clearance', 'compliant']},
            'FED': {'negative': ['rate hike', 'tightening', 'hawkish'],
                    'positive': ['rate cut', 'easing', 'dovish']},
            'ECB': {'negative': ['rate hike', 'tightening'],
                    'positive': [' QE', 'stimulus', 'easing']},
        }
    
    def analyze_regulation(self, text):
        """分析监管影响"""
        text_lower = text.lower()
        
        impacts = {}
        for regulator, keywords in self.regulatory_keywords.items():
            positive_count = sum(1 for kw in keywords['positive'] if kw in text_lower)
            negative_count = sum(1 for kw in keywords['negative'] if kw in text_lower)
            
            impacts[regulator] = {
                'positive': positive_count,
                'negative': negative_count,
                'net': positive_count - negative_count
            }
        
        # 综合影响
        total_impact = sum(i['net'] for i in impacts.values())
        
        return {
            'regulatory_impact': impacts,
            'sentiment': max(-1, min(1, total_impact * 0.3)),
            'affected_symbols': self._extract_crypto_mentions(text_lower)
        }
    
    def _extract_crypto_mentions(self, text):
        """提取提及的加密货币"""
        mentions = []
        patterns = [(r'bitcoin', 'BTC'), (r'ethereum', 'ETH'), (r'cryptocurrency', 'CRYPTO')]
        for pattern, symbol in patterns:
            if re.search(pattern, text):
                mentions.append(symbol)
        return mentions

class NLPSignalEngine:
    """
    NLP信号引擎
    综合新闻、财报、监管分析
    """
    def __init__(self):
        self.news_extractor = NewsSignalExtractor()
        self.earnings_analyzer = EarningsAnalyzer()
        self.regulatory_analyzer = RegulatoryAnalyzer()
        self.signal_history = []
    
    def process_news(self, headline, body=None):
        """处理新闻"""
        signal = self.news_extractor.extract_signal(headline, body)
        self.signal_history.append(signal)
        return signal
    
    def process_earnings(self, company, text):
        """处理财报"""
        result = self.earnings_analyzer.analyze_earnings(text)
        return result
    
    def process_regulation(self, text):
        """处理监管"""
        result = self.regulatory_analyzer.analyze_regulation(text)
        return result
    
    def get_aggregated_signal(self, texts):
        """聚合多个文本的信号"""
        signals = []
        
        for text in texts:
            if isinstance(text, dict):
                text = text.get('headline', '') + ' ' + text.get('body', '')
            signal = self.news_extractor.extract_signal(text)
            signals.append(signal)
        
        if not signals:
            return None
        
        # 加权平均
        weighted_sentiment = sum(s.sentiment * s.confidence for s in signals)
        total_confidence = sum(s.confidence for s in signals)
        
        avg_sentiment = weighted_sentiment / total_confidence if total_confidence > 0 else 0
        avg_confidence = total_confidence / len(signals)
        
        return {
            'sentiment': avg_sentiment,
            'confidence': avg_confidence,
            'action': 'BUY' if avg_sentiment > 0.3 else ('SELL' if avg_sentiment < -0.3 else 'NEUTRAL'),
            'signal_count': len(signals)
        }
