"""
AI Decision Module - 从Kronos精细克隆
基于LLM的自主决策系统，支持多Agent协作

来源: Kronos Trading System + AI Agent
"""
import time
import json
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class DecisionType(Enum):
    """决策类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    WAIT = "wait"
    REDUCE = "reduce"
    INCREASE = "increase"


class ConfidenceLevel(Enum):
    """置信度级别"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


@dataclass
class AIDecision:
    """AI决策数据类"""
    decision: DecisionType
    confidence: float  # 0-100
    confidence_level: ConfidenceLevel
    reasoning: str
    factors: List[str]
    risk_level: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)


@dataclass 
class AgentOpinion:
    """Agent意见"""
    agent_name: str
    agent_role: str
    opinion: DecisionType
    confidence: float
    reasoning: str
    vote_weight: float = 1.0


class FactorAnalyzer:
    """因子分析器 - 来自Kronos"""
    
    def __init__(self):
        self.factor_weights = {
            'technical': 0.3,
            'fundamental': 0.2,
            'sentiment': 0.2,
            'onchain': 0.15,
            'market': 0.15
        }
    
    def analyze(self, data: Dict) -> Dict[str, float]:
        """分析各因子得分"""
        scores = {}
        
        # Technical factors
        tech_score = self._analyze_technical(data.get('technical', {}))
        scores['technical'] = tech_score
        
        # Fundamental factors
        fund_score = self._analyze_fundamental(data.get('fundamental', {}))
        scores['fundamental'] = fund_score
        
        # Sentiment factors
        sent_score = self._analyze_sentiment(data.get('sentiment', {}))
        scores['sentiment'] = sent_score
        
        # On-chain factors
        onchain_score = self._analyze_onchain(data.get('onchain', {}))
        scores['onchain'] = onchain_score
        
        # Market factors
        market_score = self._analyze_market(data.get('market', {}))
        scores['market'] = market_score
        
        # Weighted total
        total = sum(scores[k] * self.factor_weights[k] for k in scores)
        scores['total'] = total
        
        return scores
    
    def _analyze_technical(self, data: Dict) -> float:
        """技术因子分析"""
        score = 50
        
        # RSI
        rsi = data.get('rsi', 50)
        if rsi < 30:
            score += 25
        elif rsi > 70:
            score -= 25
        else:
            score += (50 - abs(rsi - 50)) / 2
        
        # MACD
        macd = data.get('macd_histogram', 0)
        if macd > 0:
            score += 15
        else:
            score -= 15
        
        # Bollinger
        bb_position = data.get('bb_position', 50)
        if bb_position < 20:
            score += 10
        elif bb_position > 80:
            score -= 10
        
        return max(0, min(100, score))
    
    def _analyze_fundamental(self, data: Dict) -> float:
        """基本面因子分析"""
        score = 50
        
        # Market cap growth
        mcap_growth = data.get('mcap_growth', 0)
        if mcap_growth > 0.1:
            score += 20
        elif mcap_growth < -0.1:
            score -= 20
        
        # Volume trend
        volume_trend = data.get('volume_trend', 0)
        if volume_trend > 0.2:
            score += 15
        elif volume_trend < -0.2:
            score -= 15
        
        # Network activity
        activity = data.get('network_activity', 0)
        score += min(15, activity * 10)
        
        return max(0, min(100, score))
    
    def _analyze_sentiment(self, data: Dict) -> float:
        """情绪因子分析"""
        score = 50
        
        # Social sentiment
        social = data.get('social_sentiment', 0)
        score += social * 30
        
        # Fear & Greed
        fngg = data.get('fear_greed', 50)
        if fngg < 25:
            score += 20  # Extreme fear - potential buy
        elif fngg > 75:
            score -= 20  # Extreme greed - potential sell
        
        # News sentiment
        news = data.get('news_sentiment', 0)
        score += news * 10
        
        return max(0, min(100, score))
    
    def _analyze_onchain(self, data: Dict) -> float:
        """链上因子分析"""
        score = 50
        
        # Active addresses
        active_addr = data.get('active_addresses', 0)
        if active_addr > 10000:
            score += 20
        
        # Transaction volume
        tx_vol = data.get('tx_volume', 0)
        if tx_vol > 1000000:
            score += 15
        
        # Exchange flow
        inflow = data.get('exchange_inflow', 0)
        outflow = data.get('exchange_outflow', 0)
        if outflow > inflow:
            score += 15  # More outflow = bullish
        
        return max(0, min(100, score))
    
    def _analyze_market(self, data: Dict) -> float:
        """市场因子分析"""
        score = 50
        
        # BTC dominance
        btc_dom = data.get('btc_dominance', 50)
        if btc_dom < 45:
            score += 15  # Alt season
        
        # Market correlation
        correlation = data.get('btc_correlation', 0.5)
        score += (1 - correlation) * 20
        
        # Trend
        trend = data.get('market_trend', 'neutral')
        if trend == 'bullish':
            score += 15
        elif trend == 'bearish':
            score -= 15
        
        return max(0, min(100, score))


class MultiAgentCouncil:
    """多Agent协商委员会 - 来自Kronos"""
    
    def __init__(self):
        self.agents = {}
        self.vote_history = []
    
    def register_agent(self, name: str, role: str, expertise: List[str], weight: float = 1.0):
        """注册Agent"""
        self.agents[name] = {
            'role': role,
            'expertise': expertise,
            'weight': weight
        }
    
    def get_opinions(self, market_data: Dict) -> List[AgentOpinion]:
        """获取各Agent意见"""
        opinions = []
        
        for name, info in self.agents.items():
            opinion = self._agent_opinion(name, info['role'], market_data)
            opinion.vote_weight = info['weight']
            opinions.append(opinion)
        
        return opinions
    
    def _agent_opinion(self, name: str, role: str, data: Dict) -> AgentOpinion:
        """单个Agent的意见"""
        
        if role == 'technical':
            return self._technical_agent(name, data)
        elif role == 'fundamental':
            return self._fundamental_agent(name, data)
        elif role == 'sentiment':
            return self._sentiment_agent(name, data)
        elif role == 'risk':
            return self._risk_agent(name, data)
        elif role == 'bull':
            return self._bull_agent(name, data)
        elif role == 'bear':
            return self._bear_agent(name, data)
        else:
            return AgentOpinion(name, role, DecisionType.HOLD, 50, "No specific opinion")
    
    def _technical_agent(self, name: str, data: Dict) -> AgentOpinion:
        """技术分析Agent"""
        tech = data.get('technical', {})
        rsi = tech.get('rsi', 50)
        
        if rsi < 30:
            return AgentOpinion(name, 'technical', DecisionType.BUY, 80, 
                              f"RSI超卖({rsi:.1f}), 潜在反弹机会", 1.2)
        elif rsi > 70:
            return AgentOpinion(name, 'technical', DecisionType.SELL, 80,
                              f"RSI超买({rsi:.1f}), 回调风险", 1.2)
        
        macd = tech.get('macd_histogram', 0)
        if macd > 0:
            return AgentOpinion(name, 'technical', DecisionType.BUY, 65,
                              "MACD柱状图正值, 趋势向上", 1.0)
        else:
            return AgentOpinion(name, 'technical', DecisionType.SELL, 65,
                              "MACD柱状图负值, 趋势向下", 1.0)
    
    def _fundamental_agent(self, name: str, data: Dict) -> AgentOpinion:
        """基本面Agent"""
        fund = data.get('fundamental', {})
        mcap_growth = fund.get('mcap_growth', 0)
        
        if mcap_growth > 0.1:
            return AgentOpinion(name, 'fundamental', DecisionType.BUY, 75,
                              f"市值增长{mcap_growth*100:.1f}%, 基本面强劲", 1.0)
        elif mcap_growth < -0.1:
            return AgentOpinion(name, 'fundamental', DecisionType.SELL, 75,
                              f"市值下降{abs(mcap_growth)*100:.1f}%, 基本面疲软", 1.0)
        
        return AgentOpinion(name, 'fundamental', DecisionType.HOLD, 50,
                          "基本面中性", 0.8)
    
    def _sentiment_agent(self, name: str, data: Dict) -> AgentOpinion:
        """情绪Agent"""
        sent = data.get('sentiment', {})
        fngg = sent.get('fear_greed', 50)
        
        if fngg < 25:
            return AgentOpinion(name, 'sentiment', DecisionType.BUY, 85,
                              f"极度恐惧({fngg}), 买入机会", 1.3)
        elif fngg > 75:
            return AgentOpinion(name, 'sentiment', DecisionType.SELL, 85,
                              f"极度贪婪({fngg}), 卖出时机", 1.3)
        
        return AgentOpinion(name, 'sentiment', DecisionType.HOLD, 50,
                          f"情绪中性({fngg})", 0.8)
    
    def _risk_agent(self, name: str, data: Dict) -> AgentOpinion:
        """风险Agent"""
        risk = data.get('risk', {})
        vol = risk.get('volatility', 50)
        
        if vol > 80:
            return AgentOpinion(name, 'risk', DecisionType.WAIT, 90,
                              f"波动率极高({vol}), 等待机会", 1.5)
        elif vol > 60:
            return AgentOpinion(name, 'risk', DecisionType.REDUCE, 75,
                              f"波动率高({vol}), 降低仓位", 1.2)
        
        return AgentOpinion(name, 'risk', DecisionType.HOLD, 60,
                          f"风险可控({vol})", 1.0)
    
    def _bull_agent(self, name: str, data: Dict) -> AgentOpinion:
        """牛市Agent"""
        return AgentOpinion(name, 'bull', DecisionType.BUY, 70,
                          "趋势向上, 逢低买入", 0.8)
    
    def _bear_agent(self, name: str, data: Dict) -> AgentOpinion:
        """熊市Agent"""
        return AgentOpinion(name, 'bear', DecisionType.SELL, 70,
                          "趋势向下, 逢高卖出", 0.8)
    
    def vote(self, opinions: List[AgentOpinion]) -> AIDecision:
        """投票汇总"""
        
        # Weighted voting
        votes = defaultdict(lambda: {'score': 0, 'count': 0, 'reasons': []})
        
        for op in opinions:
            decision = op.opinion
            weighted_score = op.confidence * op.vote_weight
            votes[decision]['score'] += weighted_score
            votes[decision]['count'] += 1
            votes[decision]['reasons'].append(op.reasoning)
        
        # Find winner
        best_decision = max(votes.keys(), key=lambda x: votes[x]['score'])
        total_score = sum(v['score'] for v in votes.values())
        confidence = (votes[best_decision]['score'] / total_score * 100) if total_score > 0 else 50
        
        # Confidence level
        if confidence >= 80:
            conf_level = ConfidenceLevel.VERY_HIGH
        elif confidence >= 60:
            conf_level = ConfidenceLevel.HIGH
        elif confidence >= 40:
            conf_level = ConfidenceLevel.MEDIUM
        elif confidence >= 20:
            conf_level = ConfidenceLevel.LOW
        else:
            conf_level = ConfidenceLevel.VERY_LOW
        
        return AIDecision(
            decision=best_decision,
            confidence=confidence,
            confidence_level=conf_level,
            reasoning="; ".join(votes[best_decision]['reasons'][:3]),
            factors=[op.agent_name for op in opinions],
            risk_level=self._assess_risk(opinions)
        )
    
    def _assess_risk(self, opinions: List[AgentOpinion]) -> str:
        """评估风险"""
        risk_votes = sum(1 for op in opinions if op.opinion in [DecisionType.WAIT, DecisionType.REDUCE])
        if risk_votes >= len(opinions) / 2:
            return "HIGH"
        elif risk_votes >= len(opinions) / 3:
            return "MEDIUM"
        return "LOW"


class AIDecisionEngine:
    """AI决策引擎 - 整合所有组件"""
    
    def __init__(self):
        self.factor_analyzer = FactorAnalyzer()
        self.council = MultiAgentCouncil()
        self.decision_history = []
        
        # Register default agents
        self._register_default_agents()
    
    def _register_default_agents(self):
        """注册默认Agent"""
        self.council.register_agent('tech_expert', 'technical', ['RSI', 'MACD', 'Bollinger'], 1.0)
        self.council.register_agent('fund_expert', 'fundamental', ['market_cap', 'volume'], 0.9)
        self.council.register_agent('sentiment_guru', 'sentiment', ['social', 'news'], 1.0)
        self.council.register_agent('risk_manager', 'risk', ['volatility', 'drawdown'], 1.2)
        self.council.register_agent('bull_trader', 'bull', ['trend'], 0.6)
        self.council.register_agent('bear_trader', 'bear', ['trend'], 0.6)
    
    def decide(self, market_data: Dict) -> AIDecision:
        """做出决策"""
        
        # 1. Factor analysis
        factor_scores = self.factor_analyzer.analyze(market_data)
        
        # 2. Multi-agent opinions
        opinions = self.council.get_opinions(market_data)
        
        # 3. Vote and decide
        decision = self.council.vote(opinions)
        
        # 4. Add factor context
        decision.metadata['factor_scores'] = factor_scores
        decision.metadata['agent_count'] = len(opinions)
        
        # 5. Store history
        self.decision_history.append({
            'decision': decision.decision.value,
            'confidence': decision.confidence,
            'timestamp': decision.timestamp
        })
        
        return decision
    
    def get_recommendation(self, symbol: str, data: Dict) -> str:
        """获取简洁建议"""
        decision = self.decide(data)
        
        emoji = {
            DecisionType.BUY: "🟢",
            DecisionType.SELL: "🔴",
            DecisionType.HOLD: "🟡",
            DecisionType.WAIT: "⏳",
            DecisionType.REDUCE: "📉",
            DecisionType.INCREASE: "📈"
        }.get(decision.decision, "⚪")
        
        conf_emoji = {
            ConfidenceLevel.VERY_HIGH: "⭐⭐⭐⭐⭐",
            ConfidenceLevel.HIGH: "⭐⭐⭐⭐",
            ConfidenceLevel.MEDIUM: "⭐⭐⭐",
            ConfidenceLevel.LOW: "⭐⭐",
            ConfidenceLevel.VERY_LOW: "⭐"
        }.get(decision.confidence_level, "⚪")
        
        return f"{emoji} {decision.decision.value.upper()} ({conf_emoji}) - {decision.reasoning[:50]}..."
    
    def get_stats(self) -> Dict:
        """获取决策统计"""
        if not self.decision_history:
            return {}
        
        recent = self.decision_history[-100:]
        decisions = [d['decision'] for d in recent]
        
        return {
            'total_decisions': len(self.decision_history),
            'recent_decisions': len(recent),
            'buy_ratio': decisions.count('buy') / len(decisions) * 100,
            'sell_ratio': decisions.count('sell') / len(decisions) * 100,
            'hold_ratio': decisions.count('hold') / len(decisions) * 100,
            'avg_confidence': sum(d['confidence'] for d in recent) / len(recent)
        }


if __name__ == "__main__":
    engine = AIDecisionEngine()
    
    # Test data
    test_data = {
        'technical': {
            'rsi': 28,
            'macd_histogram': 150,
            'bb_position': 15
        },
        'fundamental': {
            'mcap_growth': 0.15,
            'volume_trend': 0.3,
            'network_activity': 8
        },
        'sentiment': {
            'social_sentiment': 0.6,
            'fear_greed': 22,
            'news_sentiment': 0.4
        },
        'onchain': {
            'active_addresses': 15000,
            'tx_volume': 2000000,
            'exchange_outflow': 100000,
            'exchange_inflow': 50000
        },
        'market': {
            'btc_dominance': 42,
            'btc_correlation': 0.6,
            'market_trend': 'bullish'
        },
        'risk': {
            'volatility': 55
        }
    }
    
    print("=== AI Decision Engine Test ===")
    
    decision = engine.decide(test_data)
    
    print(f"\nDecision: {decision.decision.value}")
    print(f"Confidence: {decision.confidence:.1f}% ({decision.confidence_level.name})")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Risk Level: {decision.risk_level}")
    print(f"Factors: {decision.factors}")
    
    print(f"\nFactor Scores:")
    for k, v in decision.metadata['factor_scores'].items():
        if k != 'total':
            print(f"  {k}: {v:.1f}")
    
    print(f"\nRecommendation: {engine.get_recommendation('BTCUSDT', test_data)}")
    
    stats = engine.get_stats()
    print(f"\nStats: {stats}")
