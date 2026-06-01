"""
25-Dimensional Full-Domain Simulation
25个维度全向仿真引擎
"""
import sys
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class DimensionResult:
    dimension: str
    value: float
    weight: float
    contribution: float
    status: str  # POSITIVE/NEGATIVE/NEUTRAL

@dataclass
class Simulation25DResult:
    total_score: float
    dimensions: List[DimensionResult]
    recommendation: str
    risk_level: str
    confidence: float

DIMENSIONS = {
    # 技术指标维度 (8)
    'tech_rsi': {'name': 'RSI', 'weight': 0.05, 'range': (0, 100)},
    'tech_macd': {'name': 'MACD', 'weight': 0.05, 'range': (-10, 10)},
    'tech_bollinger': {'name': 'Bollinger', 'weight': 0.04, 'range': (0, 100)},
    'tech_adx': {'name': 'ADX', 'weight': 0.04, 'range': (0, 100)},
    'tech_volume': {'name': 'Volume', 'weight': 0.04, 'range': (0, 200)},
    
    # 资金流向维度 (5)
    'flow_funding': {'name': 'Funding Rate', 'weight': 0.05, 'range': (-0.1, 0.1)},
    'flow_oi': {'name': 'Open Interest', 'weight': 0.04, 'range': (0, 200)},
    'flow_whale': {'name': 'Whale Flow', 'weight': 0.05, 'range': (-100, 100)},
    'flow_stable': {'name': 'Stablecoin Flow', 'weight': 0.03, 'range': (-50, 50)},
    'flow_exchange': {'name': 'Exchange Flow', 'weight': 0.03, 'range': (-50, 50)},
    
    # 市场情绪维度 (4)
    'sentiment_fear_greed': {'name': 'Fear & Greed', 'weight': 0.05, 'range': (0, 100)},
    'sentiment_social': {'name': 'Social Volume', 'weight': 0.03, 'range': (0, 100)},
    'sentiment_kol': {'name': 'KOL Sentiment', 'weight': 0.04, 'range': (-100, 100)},
    'sentiment_options': {'name': 'Options Skew', 'weight': 0.03, 'range': (-50, 50)},
    
    # 链上数据维度 (4)
    'onchain_tvl': {'name': 'TVL', 'weight': 0.04, 'range': (0, 200)},
    'onchain_active': {'name': 'Active Addr', 'weight': 0.03, 'range': (0, 100)},
    'onchain_gas': {'name': 'Gas Price', 'weight': 0.02, 'range': (0, 200)},
    'onchain_holders': {'name': 'Holders', 'weight': 0.02, 'range': (0, 100)},
    
    # 相关性维度 (2)
    'corr_btc': {'name': 'BTC Correlation', 'weight': 0.05, 'range': (-1, 1)},
    'corr_eth': {'name': 'ETH Correlation', 'weight': 0.03, 'range': (-1, 1)},
    
    # 波动率维度 (2)
    'vol_current': {'name': 'Current Vol', 'weight': 0.04, 'range': (0, 150)},
    'vol_implied': {'name': 'IV', 'weight': 0.04, 'range': (0, 150)},
    
    # 宏观维度 (2)
    'macro_rate': {'name': 'Interest Rate', 'weight': 0.03, 'range': (0, 10)},
    'macro_dxy': {'name': 'DXY', 'weight': 0.02, 'range': (80, 120)},
    
    # 时间维度 (1)
    'time_hour': {'name': 'Hour Effect', 'weight': 0.02, 'range': (-5, 5)},
    
    # 流动性维度 (1)
    'liq_spread': {'name': 'Bid-Ask Spread', 'weight': 0.03, 'range': (0, 10)},
}

class Simulation25D:
    """
    25维度全向仿真引擎
    多维度综合分析
    """
    
    def __init__(self):
        self.name = "25-D Simulation"
        self.dimensions = DIMENSIONS
        self.total_dimensions = len(DIMENSIONS)
    
    def simulate_dimension(self, dim_key: str) -> DimensionResult:
        """模拟单个维度"""
        dim = self.dimensions[dim_key]
        min_val, max_val = dim['range']
        
        # 生成随机值 (模拟真实数据)
        if dim_key in ['flow_funding', 'corr_btc', 'corr_eth']:
            value = random.uniform(min_val, max_val)
        elif dim_key in ['sentiment_fear_greed', 'tech_rsi']:
            value = random.uniform(30, 70)
        else:
            value = random.uniform(min_val * 0.5, max_val * 0.8)
        
        # 计算贡献
        if dim_key in ['flow_funding', 'corr_btc', 'corr_eth']:
            # 这类维度 value 就是偏离中心的程度
            contribution = value * dim['weight'] * 10
        else:
            # 标准化到 0-1
            normalized = (value - min_val) / (max_val - min_val)
            contribution = (normalized - 0.5) * dim['weight'] * 100
        
        # 状态判断
        if contribution > 2:
            status = 'POSITIVE'
        elif contribution < -2:
            status = 'NEGATIVE'
        else:
            status = 'NEUTRAL'
        
        return DimensionResult(
            dimension=dim['name'],
            value=value,
            weight=dim['weight'],
            contribution=contribution,
            status=status
        )
    
    def run_full_simulation(self, symbol: str = 'BTC') -> Simulation25DResult:
        """运行完整25维仿真"""
        dimensions = []
        total_contribution = 0
        
        for dim_key in self.dimensions:
            result = self.simulate_dimension(dim_key)
            dimensions.append(result)
            total_contribution += result.contribution
        
        # 归一化总分 (-100 to +100)
        total_score = max(-100, min(100, total_contribution))
        
        # 置信度
        positive_count = sum(1 for d in dimensions if d.status == 'POSITIVE')
        confidence = positive_count / self.total_dimensions
        
        # 建议
        if total_score > 30 and confidence > 0.6:
            recommendation = 'STRONG_BUY'
        elif total_score > 10 and confidence > 0.5:
            recommendation = 'BUY'
        elif total_score < -30 and confidence > 0.6:
            recommendation = 'STRONG_SELL'
        elif total_score < -10 and confidence > 0.5:
            recommendation = 'SELL'
        else:
            recommendation = 'HOLD'
        
        # 风险等级
        vol_dims = [d for d in dimensions if 'vol' in d.dimension.lower()]
        avg_vol = sum(d.value for d in vol_dims) / len(vol_dims) if vol_dims else 50
        
        if avg_vol > 80:
            risk_level = 'EXTREME'
        elif avg_vol > 60:
            risk_level = 'HIGH'
        elif avg_vol > 40:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return Simulation25DResult(
            total_score=total_score,
            dimensions=dimensions,
            recommendation=recommendation,
            risk_level=risk_level,
            confidence=confidence
        )
    
    def get_dimension_breakdown(self, result: Simulation25DResult) -> Dict:
        """获取维度分解"""
        breakdown = {
            'positive': [],
            'negative': [],
            'neutral': []
        }
        
        for dim in result.dimensions:
            breakdown[dim.status.lower()].append({
                'name': dim.dimension,
                'value': dim.value,
                'contribution': dim.contribution
            })
        
        return breakdown

if __name__ == '__main__':
    sim = Simulation25D()
    
    print("=== 25-Dimensional Simulation ===\n")
    
    result = sim.run_full_simulation('BTC')
    
    print(f"Total Dimensions: {sim.total_dimensions}")
    print(f"Total Score: {result.total_score:.1f}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Confidence: {result.confidence:.1%}")
    
    breakdown = sim.get_dimension_breakdown(result)
    
    print(f"\nPositive Factors ({len(breakdown['positive'])}):")
    for f in sorted(breakdown['positive'], key=lambda x: x['contribution'], reverse=True)[:5]:
        print(f"  + {f['name']}: {f['contribution']:.1f}")
    
    print(f"\nNegative Factors ({len(breakdown['negative'])}):")
    for f in sorted(breakdown['negative'], key=lambda x: x['contribution'])[:5]:
        print(f"  - {f['name']}: {f['contribution']:.1f}")
