"""
Factor Matrix - 因子矩阵系统
所有因子统一矩阵化管理
"""
import sys
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

class FactorCategory(Enum):
    TECHNICAL = "technical"
    ONCHAIN = "onchain"
    SENTIMENT = "sentiment"
    MACRO = "macro"
    LIQUIDITY = "liquidity"
    FUNDING = "funding"

class FactorType(Enum):
    MOMENTUM = "momentum"
    VALUE = "value"
    VOLATILITY = "volatility"
    QUALITY = "quality"
    SIZE = "size"

@dataclass
class FactorConfig:
    factor_id: str
    name: str
    category: FactorCategory
    factor_type: FactorType
    params: Dict[str, float]
    weight: float
    enabled: bool
    normalized_value: float  # -1 to 1
    created_at: float
    updated_at: float
    tags: List[str] = field(default_factory=list)

@dataclass
class FactorValue:
    factor_id: str
    factor_name: str
    raw_value: float
    normalized_value: float
    percentile: float
    timestamp: float

class FactorMatrix:
    """
    因子矩阵
    - 网格化管理所有因子
    - 实时归一化
    - 相关性分析
    - 动态权重
    """
    
    def __init__(self):
        self.name = "Factor Matrix"
        self.factors: Dict[str, FactorConfig] = {}
        self.factor_values: Dict[str, List[FactorValue]] = {}
        
        # 矩阵配置
        self.matrix_config = {
            'normalization_window': 100,
            'min_correlation': 0.3,
            'max_correlation': 0.9,
            'weight_update_interval': 3600
        }
        
        # 初始化内置因子
        self._init_builtin_factors()
    
    def _init_builtin_factors(self):
        """初始化内置因子"""
        builtins = [
            # 技术因子
            ('RSI', FactorCategory.TECHNICAL, FactorType.MOMENTUM, {'period': 14}),
            ('MACD', FactorCategory.TECHNICAL, FactorType.MOMENTUM, {'fast': 12, 'slow': 26}),
            ('BB_WIDTH', FactorCategory.TECHNICAL, FactorType.VOLATILITY, {'period': 20}),
            ('ADX', FactorCategory.TECHNICAL, FactorType.MOMENTUM, {'period': 14}),
            ('ATR', FactorCategory.TECHNICAL, FactorType.VOLATILITY, {'period': 14}),
            ('STOCH', FactorCategory.TECHNICAL, FactorType.MOMENTUM, {'k_period': 14, 'd_period': 3}),
            
            # 链上因子
            ('MVRV', FactorCategory.ONCHAIN, FactorType.VALUE, {'period': 365}),
            ('NVT', FactorCategory.ONCHAIN, FactorType.VALUE, {'period': 14}),
            ('TVL', FactorCategory.ONCHAIN, FactorType.QUALITY, {'period': 7}),
            ('ACTIVE_ADDR', FactorCategory.ONCHAIN, FactorType.SIZE, {'period': 1}),
            ('GAS_PRICE', FactorCategory.ONCHAIN, FactorType.VOLATILITY, {'period': 1}),
            
            # 情绪因子
            ('FEAR_GREED', FactorCategory.SENTIMENT, FactorType.MOMENTUM, {}),
            ('SOCIAL_VOL', FactorCategory.SENTIMENT, FactorType.SIZE, {'period': 7}),
            ('KOL_SENTIMENT', FactorCategory.SENTIMENT, FactorType.MOMENTUM, {}),
            
            # 流动性因子
            ('FUNDING_RATE', FactorCategory.FUNDING, FactorType.MOMENTUM, {}),
            ('OPEN_INTEREST', FactorCategory.LIQUIDITY, FactorType.SIZE, {'period': 1}),
            ('BID_ASK_SPREAD', FactorCategory.LIQUIDITY, FactorType.VOLATILITY, {}),
            
            # 宏观因子
            ('DXY', FactorCategory.MACRO, FactorType.MOMENTUM, {}),
            ('BTC_DOMINANCE', FactorCategory.MACRO, FactorType.SIZE, {}),
            ('ALTSEASON', FactorCategory.MACRO, FactorType.MOMENTUM, {}),
        ]
        
        for name, cat, ftype, params in builtins:
            fid = f"FACTOR_{name.upper()}"
            self.factors[fid] = FactorConfig(
                factor_id=fid,
                name=name,
                category=cat,
                factor_type=ftype,
                params=params,
                weight=1.0 / len(builtins),  # 平均权重
                enabled=True,
                normalized_value=0,
                created_at=time.time(),
                updated_at=time.time(),
                tags=['builtin']
            )
    
    def add_factor(self, factor: FactorConfig) -> bool:
        """添加因子"""
        if factor.factor_id in self.factors:
            return False
        self.factors[factor.factor_id] = factor
        self._recalculate_weights()
        return True
    
    def remove_factor(self, factor_id: str) -> bool:
        """移除因子"""
        if factor_id in self.factors:
            del self.factors[factor_id]
            self._recalculate_weights()
            return True
        return False
    
    def enable_factor(self, factor_id: str) -> bool:
        """启用因子"""
        if factor_id in self.factors:
            self.factors[factor_id].enabled = True
            self.factors[factor_id].updated_at = time.time()
            self._recalculate_weights()
            return True
        return False
    
    def disable_factor(self, factor_id: str) -> bool:
        """禁用因子"""
        if factor_id in self.factors:
            self.factors[factor_id].enabled = False
            self.factors[factor_id].updated_at = time.time()
            self._recalculate_weights()
            return True
        return False
    
    def _recalculate_weights(self):
        """重新计算权重"""
        enabled = [f for f in self.factors.values() if f.enabled]
        if not enabled:
            return
        
        # 平均权重
        w = 1.0 / len(enabled)
        for f in enabled:
            f.weight = w
    
    def update_factor_value(self, factor_id: str, value: float):
        """更新因子值"""
        if factor_id not in self.factors:
            return
        
        factor = self.factors[factor_id]
        
        # 归一化 (简化版: 假设value在0-100)
        normalized = (value - 50) / 50  # -1 to 1
        normalized = max(-1, min(1, normalized))
        
        factor.normalized_value = normalized
        factor.updated_at = time.time()
        
        # 记录历史
        if factor_id not in self.factor_values:
            self.factor_values[factor_id] = []
        
        fv = FactorValue(
            factor_id=factor_id,
            factor_name=factor.name,
            raw_value=value,
            normalized_value=normalized,
            percentile=value,  # 简化
            timestamp=time.time()
        )
        self.factor_values[factor_id].append(fv)
    
    def calculate_all_factors(self, market_data: Dict) -> Dict[str, FactorValue]:
        """计算所有因子"""
        results = {}
        
        for fid, factor in self.factors.items():
            if not factor.enabled:
                continue
            
            # 模拟因子计算
            raw_value = self._calculate_factor_value(factor, market_data)
            self.update_factor_value(fid, raw_value)
            
            results[fid] = FactorValue(
                factor_id=fid,
                factor_name=factor.name,
                raw_value=raw_value,
                normalized_value=factor.normalized_value,
                percentile=raw_value,
                timestamp=time.time()
            )
        
        return results
    
    def _calculate_factor_value(self, factor: FactorConfig, data: Dict) -> float:
        """计算单个因子值"""
        import random
        
        # 基础值50
        base = 50
        
        # 根据类型和类别调整
        if factor.category == FactorCategory.TECHNICAL:
            base += random.uniform(-15, 15)
        elif factor.category == FactorCategory.ONCHAIN:
            base += random.uniform(-10, 20)
        elif factor.category == FactorCategory.SENTIMENT:
            base += random.uniform(-20, 20)
        elif factor.category == FactorCategory.MACRO:
            base += random.uniform(-5, 5)
        
        # 动量类因子
        if factor.factor_type == FactorType.MOMENTUM:
            base += random.uniform(0, 10)
        elif factor.factor_type == FactorType.VOLATILITY:
            base += random.uniform(-10, 10)
        
        return max(0, min(100, base))
    
    def get_composite_score(self) -> float:
        """获取复合因子得分"""
        total = 0
        for fid, factor in self.factors.items():
            if not factor.enabled:
                continue
            total += factor.normalized_value * factor.weight
        
        # 转换到0-100
        score = (total + 1) / 2 * 100
        return max(0, min(100, score))
    
    def get_factor_by_category(self, category: FactorCategory) -> List[FactorConfig]:
        """按类别获取因子"""
        return [f for f in self.factors.values() if f.category == category and f.enabled]
    
    def get_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """获取相关性矩阵"""
        enabled = [f for f in self.factors.values() if f.enabled]
        n = len(enabled)
        
        corr = {}
        for i, f1 in enumerate(enabled):
            corr[f1.factor_id] = {}
            for j, f2 in enumerate(enabled):
                if i == j:
                    corr[f1.factor_id][f2.factor_id] = 1.0
                else:
                    # 简化相关性
                    import random
                    corr[f1.factor_id][f2.factor_id] = random.uniform(-0.5, 0.5)
        
        return corr
    
    def get_matrix_view(self) -> Dict:
        """获取矩阵视图"""
        enabled = [f for f in self.factors.values() if f.enabled]
        
        by_category = {}
        for cat in FactorCategory:
            cats = [f for f in enabled if f.category == cat]
            by_category[cat.value] = {
                'count': len(cats),
                'total_weight': sum(f.weight for f in cats)
            }
        
        return {
            'total_factors': len(self.factors),
            'enabled_count': len(enabled),
            'composite_score': self.get_composite_score(),
            'by_category': by_category,
            'factors': [{
                'id': f.factor_id,
                'name': f.name,
                'category': f.category.value,
                'weight': f.weight,
                'normalized_value': f.normalized_value,
                'enabled': f.enabled
            } for f in self.factors.values()]
        }

if __name__ == '__main__':
    matrix = FactorMatrix()
    
    print("=== Factor Matrix ===\n")
    
    view = matrix.get_matrix_view()
    print(f"Total Factors: {view['total_factors']}")
    print(f"Enabled: {view['enabled_count']}")
    print(f"Composite Score: {view['composite_score']:.1f}")
    
    # 计算因子
    values = matrix.calculate_all_factors({'price': 67000})
    print(f"\nCalculated: {len(values)} factors")
    
    # 分类显示
    for cat in ['technical', 'onchain', 'sentiment']:
        cats = matrix.get_factor_by_category(FactorCategory[cat.upper()])
        print(f"\n{cat.upper()}: {len(cats)} factors")
        for f in cats[:3]:
            print(f"  {f.name}: {f.normalized_value:+.2f}")
