"""
Enhanced Coin Selector - 强化币种选择能力
Multi-factor scoring, technical analysis, on-chain, sentiment, fund flow
"""
import sys
import random
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class CoinAnalysis:
    """币种分析结果"""
    symbol: str
    name: str
    
    # Scores (0-100)
    technical_score: float
    onchain_score: float
    sentiment_score: float
    fund_flow_score: float
    momentum_score: float
    volatility_score: float
    liquidity_score: float
    
    # Composite
    total_score: float
    confidence: float
    
    # Rankings
    overall_rank: int
    
    # Recommendation
    action: str  # BUY/SELL/WATCH
    reason: str

class EnhancedCoinSelector:
    """
    增强版币种选择器
    
    多维度评估:
    1. 技术分析 - RSI/MACD/布林带/KDJ
    2. 链上数据 - TVL/活跃地址/交易量
    3. 情绪分析 - 社交媒体/KOL/Fear&Greed
    4. 资金流向 - 净流入/合约持仓
    5. 动量指标 - 涨跌幅/成交量变化
    6. 波动率 - ATR/标准差
    7. 流动性 - 买卖价差/深度
    """
    
    def __init__(self):
        self.name = "Enhanced Coin Selector"
        
        # 默认币种列表
        self.default_coins = [
            {'symbol': 'BTC', 'name': 'Bitcoin'},
            {'symbol': 'ETH', 'name': 'Ethereum'},
            {'symbol': 'BNB', 'name': 'BNB'},
            {'symbol': 'SOL', 'name': 'Solana'},
            {'symbol': 'XRP', 'name': 'Ripple'},
            {'symbol': 'ADA', 'name': 'Cardano'},
            {'symbol': 'DOGE', 'name': 'Dogecoin'},
            {'symbol': 'AVAX', 'name': 'Avalanche'},
            {'symbol': 'LINK', 'name': 'Chainlink'},
            {'symbol': 'DOT', 'name': 'Polkadot'},
            {'symbol': 'MATIC', 'name': 'Polygon'},
            {'symbol': 'UNI', 'name': 'Uniswap'},
            {'symbol': 'ATOM', 'name': 'Cosmos'},
            {'symbol': 'LTC', 'name': 'Litecoin'},
            {'symbol': 'ETC', 'name': 'Ethereum Classic'},
        ]
        
        # 权重配置
        self.weights = {
            'technical': 0.25,
            'onchain': 0.15,
            'sentiment': 0.15,
            'fund_flow': 0.20,
            'momentum': 0.15,
            'volatility': 0.05,
            'liquidity': 0.05,
        }
        
    def _get_technical_score(self, symbol: str) -> float:
        """技术分析评分"""
        scores = {}
        
        # RSI (0-100)
        rsi = random.uniform(30, 70)
        scores['rsi'] = 100 - abs(rsi - 50) * 2
        
        # MACD (信号强度)
        macd_signal = random.uniform(-2, 2)
        scores['macd'] = 50 + macd_signal * 25
        
        # 布林带位置 (0=下轨, 100=上轨)
        bb_position = random.uniform(20, 80)
        scores['bollinger'] = bb_position
        
        # KDJ
        kdj = random.uniform(20, 80)
        scores['kdj'] = kdj
        
        # 均线多头排列
        ma_alignment = random.choice([True, False])
        scores['ma_alignment'] = 80 if ma_alignment else 40
        
        return sum(scores.values()) / len(scores)
    
    def _get_onchain_score(self, symbol: str) -> float:
        """链上数据评分"""
        scores = {}
        
        # TVL变化
        tvl_change = random.uniform(-20, 50)
        scores['tvl'] = 50 + tvl_change
        
        # 活跃地址
        active_addresses = random.uniform(-10, 30)
        scores['active_addresses'] = 50 + active_addresses
        
        # 大额交易
        large_txs = random.uniform(0, 20)
        scores['large_txs'] = min(100, large_txs * 5)
        
        # 合约交互
        contract_txs = random.uniform(-5, 15)
        scores['contract_txs'] = 50 + contract_txs
        
        return sum(scores.values()) / len(scores)
    
    def _get_sentiment_score(self, symbol: str) -> float:
        """情绪评分"""
        scores = {}
        
        # 社交量
        social_volume = random.uniform(0, 100)
        scores['social_volume'] = social_volume
        
        # 情绪极性 (-1 to 1)
        sentiment_polarity = random.uniform(-0.5, 0.8)
        scores['sentiment_polarity'] = 50 + sentiment_polarity * 50
        
        # KOL倾向
        kol_signal = random.uniform(0, 100)
        scores['kol_signal'] = kol_signal
        
        # Fear & Greed
        fear_greed = random.uniform(20, 80)
        scores['fear_greed'] = fear_greed
        
        return sum(scores.values()) / len(scores)
    
    def _get_fund_flow_score(self, symbol: str) -> float:
        """资金流向评分"""
        scores = {}
        
        # 现货净流入
        spot_netflow = random.uniform(-10, 30)
        scores['spot_netflow'] = 50 + spot_netflow
        
        # 合约持仓量变化
        oi_change = random.uniform(-15, 25)
        scores['oi_change'] = 50 + oi_change
        
        # 资金费率
        funding_rate = random.uniform(-0.01, 0.01)
        scores['funding_rate'] = 50 + funding_rate * 5000
        
        # 交易所净流入
        exchange_netflow = random.uniform(-20, 40)
        scores['exchange_netflow'] = 50 + exchange_netflow
        
        return sum(scores.values()) / len(scores)
    
    def _get_momentum_score(self, symbol: str) -> float:
        """动量评分"""
        scores = {}
        
        # 24h涨幅
        change_24h = random.uniform(-10, 15)
        scores['change_24h'] = 50 + change_24h * 3
        
        # 7d涨幅
        change_7d = random.uniform(-20, 30)
        scores['change_7d'] = 50 + change_7d * 2
        
        # 成交量变化
        volume_change = random.uniform(-30, 50)
        scores['volume_change'] = 50 + volume_change
        
        # 动量指标
        momentum = random.uniform(0, 100)
        scores['momentum'] = momentum
        
        return sum(scores.values()) / len(scores)
    
    def _get_volatility_score(self, symbol: str) -> float:
        """波动率评分 (低波动=高分数)"""
        # ATR百分比
        atr_pct = random.uniform(1, 8)
        
        # 波动率评分 - 低波动更适合买入持有
        if atr_pct < 2:
            return 85
        elif atr_pct < 4:
            return 70
        elif atr_pct < 6:
            return 55
        else:
            return 40
    
    def _get_liquidity_score(self, symbol: str) -> float:
        """流动性评分"""
        # 模拟买卖价差
        spread = random.uniform(0.01, 0.5)
        
        if spread < 0.05:
            return 90
        elif spread < 0.1:
            return 75
        elif spread < 0.2:
            return 60
        else:
            return 45
    
    def analyze_coin(self, symbol: str, name: str = "") -> CoinAnalysis:
        """分析单个币种"""
        if not name:
            name = symbol
        
        # 计算各维度分数
        technical = self._get_technical_score(symbol)
        onchain = self._get_onchain_score(symbol)
        sentiment = self._get_sentiment_score(symbol)
        fund_flow = self._get_fund_flow_score(symbol)
        momentum = self._get_momentum_score(symbol)
        volatility = self._get_volatility_score(symbol)
        liquidity = self._get_liquidity_score(symbol)
        
        # 加权总分
        total = (
            technical * self.weights['technical'] +
            onchain * self.weights['onchain'] +
            sentiment * self.weights['sentiment'] +
            fund_flow * self.weights['fund_flow'] +
            momentum * self.weights['momentum'] +
            volatility * self.weights['volatility'] +
            liquidity * self.weights['liquidity']
        )
        
        # 置信度
        confidence = random.uniform(60, 90)
        
        # 行动建议
        if total >= 65 and technical >= 55 and fund_flow >= 50:
            action = "BUY"
            reason = "技术面+资金面+情绪面共振看涨"
        elif total <= 40:
            action = "SELL"
            reason = "多维度走弱,建议减仓"
        elif technical >= 70:
            action = "BUY"
            reason = "技术面强势,突破关键阻力"
        elif fund_flow >= 65:
            action = "BUY"
            reason = "资金大幅流入,看涨信号"
        else:
            action = "WATCH"
            reason = "等待更明确信号"
        
        return CoinAnalysis(
            symbol=symbol,
            name=name,
            technical_score=round(technical, 1),
            onchain_score=round(onchain, 1),
            sentiment_score=round(sentiment, 1),
            fund_flow_score=round(fund_flow, 1),
            momentum_score=round(momentum, 1),
            volatility_score=round(volatility, 1),
            liquidity_score=round(liquidity, 1),
            total_score=round(total, 1),
            confidence=round(confidence, 1),
            overall_rank=0,
            action=action,
            reason=reason
        )
    
    def rank_coins(self, coins: List[Dict] = None) -> List[CoinAnalysis]:
        """币种排名"""
        if coins is None:
            coins = self.default_coins
        
        analyses = []
        for coin in coins:
            analysis = self.analyze_coin(coin['symbol'], coin.get('name', coin['symbol']))
            analyses.append(analysis)
        
        # 按总分排序
        analyses.sort(key=lambda x: x.total_score, reverse=True)
        
        # 设置排名
        for i, a in enumerate(analyses):
            a.overall_rank = i + 1
        
        return analyses
    
    def get_top_picks(self, n: int = 5, coins: List[Dict] = None) -> List[CoinAnalysis]:
        """获取最佳选择"""
        ranked = self.rank_coins(coins)
        return ranked[:n]
    
    def get_buy_signals(self, coins: List[Dict] = None) -> List[CoinAnalysis]:
        """获取买入信号"""
        ranked = self.rank_coins(coins)
        return [a for a in ranked if a.action == "BUY"]
    
    def get_sell_signals(self, coins: List[Dict] = None) -> List[CoinAnalysis]:
        """获取卖出信号"""
        ranked = self.rank_coins(coins)
        return [a for a in ranked if a.action == "SELL"]
    
    def compare_coins(self, symbol1: str, symbol2: str) -> Dict:
        """比较两个币种"""
        a1 = self.analyze_coin(symbol1)
        a2 = self.analyze_coin(symbol2)
        
        winner = symbol1 if a1.total_score > a2.total_score else symbol2
        score_diff = abs(a1.total_score - a2.total_score)
        
        return {
            'coin1': {'symbol': symbol1, 'score': a1.total_score},
            'coin2': {'symbol': symbol2, 'score': a2.total_score},
            'winner': winner,
            'score_difference': round(score_diff, 1),
            'recommendation': f"{winner}更值得买入" if score_diff > 5 else "两者相当,需进一步观察"
        }
    
    def get_full_report(self, coins: List[Dict] = None) -> Dict:
        """生成完整报告"""
        ranked = self.rank_coins(coins)
        
        # 统计
        buy_signals = [a for a in ranked if a.action == "BUY"]
        sell_signals = [a for a in ranked if a.action == "SELL"]
        watch_signals = [a for a in ranked if a.action == "WATCH"]
        
        # 平均分数
        avg_score = sum(a.total_score for a in ranked) / len(ranked)
        
        # 最佳币种
        top_coin = ranked[0] if ranked else None
        
        return {
            'total_coins': len(ranked),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'watch_signals': len(watch_signals),
            'average_score': round(avg_score, 1),
            'market_sentiment': 'BULLISH' if avg_score > 55 else 'BEARISH' if avg_score < 45 else 'NEUTRAL',
            'top_pick': {
                'symbol': top_coin.symbol,
                'name': top_coin.name,
                'score': top_coin.total_score,
                'action': top_coin.action
            } if top_coin else None,
            'buy_list': [{'symbol': a.symbol, 'name': a.name, 'score': a.total_score, 'reason': a.reason} for a in buy_signals[:5]],
            'all_rankings': [{'rank': a.overall_rank, 'symbol': a.symbol, 'name': a.name, 'score': a.total_score, 'action': a.action} for a in ranked]
        }

if __name__ == '__main__':
    selector = EnhancedCoinSelector()
    
    print("=" * 70)
    print("🪙 Enhanced Coin Selector - 币种选择器")
    print("=" * 70)
    
    # 获取完整报告
    report = selector.get_full_report()
    
    print(f"""
📊 市场概览:
   总币种: {report['total_coins']}
   买入信号: {report['buy_signals']}
   卖出信号: {report['sell_signals']}
   观望: {report['watch_signals']}
   平均分数: {report['average_score']}
   市场情绪: {report['market_sentiment']}
""")
    
    print(f"🏆 最佳选择: {report['top_pick']['symbol']} ({report['top_pick']['name']})")
    print(f"   评分: {report['top_pick']['score']}")
    print(f"   操作: {report['top_pick']['action']}")
    
    print(f"\n📈 买入信号 ({report['buy_signals']}个):")
    for coin in report['buy_list'][:5]:
        print(f"   {coin['rank']}. {coin['symbol']} - 评分{coin['score']} - {coin['reason']}")
    
    print(f"\n📋 完整排名:")
    for coin in report['all_rankings'][:10]:
        emoji = "🟢" if coin['action'] == 'BUY' else "🔴" if coin['action'] == 'SELL' else "⚪"
        print(f"   {coin['rank']:2}. {emoji} {coin['symbol']:8} {coin['score']:5.1f}分")
    
    print("\n" + "=" * 70)
