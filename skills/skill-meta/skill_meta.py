#!/usr/bin/env python3
"""
SkillMeta - G40 技能调度元系统
===========================
智能组合和调度各个交易策略技能
"""

import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class SkillState:
    """技能状态"""
    ACTIVE = "active"
    DORMANT = "dormant"
    COOLDOWN = "cooldown"
    
    def __init__(self, name: str):
        self.name = name
        self.state = self.ACTIVE
        self.score = 50  # 性能评分 0-100
        self.usage_count = 0
        self.last_used = 0
        self.cooldown_until = 0
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0
    
    def use(self):
        """使用技能"""
        self.usage_count += 1
        self.last_used = time.time()
    
    def record_win(self, pnl: float):
        """记录盈利"""
        self.wins += 1
        self.total_pnl += pnl
        self.score = min(100, self.score + 1)
    
    def record_loss(self, pnl: float):
        """记录亏损"""
        self.losses += 1
        self.total_pnl += pnl
        self.score = max(0, self.score - 2)
    
    def win_rate(self) -> float:
        """胜率"""
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.5
    
    def avg_pnl(self) -> float:
        """平均盈亏"""
        total = self.wins + self.losses
        return self.total_pnl / total if total > 0 else 0
    
    def enter_cooldown(self, seconds: int):
        """进入冷却"""
        self.state = self.COOLDOWN
        self.cooldown_until = time.time() + seconds
    
    def update(self):
        """更新状态"""
        if self.state == self.COOLDOWN:
            if time.time() >= self.cooldown_until:
                self.state = self.ACTIVE


class SkillMeta:
    """
    技能调度元系统
    负责智能组合和调度各个交易策略技能
    """
    
    # 技能分类
    TREND_SKILLS = ['go-core', 'go-pool', 'top10', 'go-thermo']
    RANGE_SKILLS = ['go-rotate', 'go-long-short', 'go-noise', 'go-fit']
    RISK_SKILLS = ['go-detect', 'go-etf', 'go-noise']
    
    # 市场状态组合模板
    COMBINATIONS = {
        'trending': {
            'skills': ['go-core', 'go-pool', 'go-detect', 'top10'],
            'weights': [0.30, 0.25, 0.15, 0.10],
            'description': '趋势市场组合'
        },
        'ranging': {
            'skills': ['go-rotate', 'go-long-short', 'go-noise', 'go-etf'],
            'weights': [0.25, 0.25, 0.15, 0.10],
            'description': '震荡市场组合'
        },
        'volatile': {
            'skills': ['go-long-short', 'go-detect', 'go-thermo', 'go-fit'],
            'weights': [0.30, 0.20, 0.15, 0.10],
            'description': '高波动市场组合'
        },
        'conservative': {
            'skills': ['go-etf', 'go-core', 'go-rotate'],
            'weights': [0.30, 0.25, 0.20],
            'description': '保守组合'
        },
        'aggressive': {
            'skills': ['go-pool', 'go-core', 'top10', 'go-long-short'],
            'weights': [0.30, 0.25, 0.20, 0.15],
            'description': '激进组合'
        }
    }
    
    def __init__(self, g40=None):
        self.g40 = g40
        self.skills: Dict[str, SkillState] = {}
        self.active_combination = []
        self.performance_history = []
        
        # 初始化所有技能状态
        all_skills = (self.TREND_SKILLS + self.RANGE_SKILLS + self.RISK_SKILLS)
        for skill in set(all_skills):
            self.skills[skill] = SkillState(skill)
    
    def detect_market_regime(self) -> str:
        """检测市场状态"""
        if self.g40:
            try:
                return self.g40.optimizer.detect_market_regime()
            except: pass
        
        # 默认检测
        return 'trending'
    
    def get_optimal_combination(self, market_regime: str = None, confidence: float = 0.5) -> List[Tuple[str, float]]:
        """
        获取最佳技能组合
        
        Args:
            market_regime: 市场状态 (trending/ranging/volatile)
            confidence: 信号信心度 (0-1)
        
        Returns:
            List of (skill_name, weight) tuples
        """
        if market_regime is None:
            market_regime = self.detect_market_regime()
        
        # 根据市场状态选择组合
        combo = self.COMBINATIONS.get(market_regime, self.COMBINATIONS['trending'])
        
        # 根据信心度调整
        if confidence < 0.4:
            # 低信心使用保守组合
            combo = self.COMBINATIONS['conservative']
        elif confidence > 0.8:
            # 高信心使用激进组合
            combo = self.COMBINATIONS['aggressive']
        
        # 应用技能评分调整
        adjusted_weights = []
        for skill, weight in zip(combo['skills'], combo['weights']):
            skill_state = self.skills.get(skill)
            if skill_state:
                # 性能评分调整权重
                score_factor = skill_state.score / 100
                adjusted_weights.append(weight * score_factor)
            else:
                adjusted_weights.append(weight)
        
        # 归一化
        total = sum(adjusted_weights)
        if total > 0:
            adjusted_weights = [w / total for w in adjusted_weights]
        
        return list(zip(combo['skills'], adjusted_weights))
    
    def execute_combination(self, combination: List[Tuple[str, float]], symbol: str) -> Dict:
        """
        执行技能组合
        
        Args:
            combination: (skill, weight) tuples
            symbol: 交易币种
        
        Returns:
            执行结果
        """
        if not self.g40:
            return {'action': 'skip', 'reason': 'No G40 instance'}
        
        results = []
        total_signal = 0
        total_confidence = 0
        total_weight = 0
        
        for skill, weight in combination:
            skill_state = self.skills.get(skill)
            if not skill_state or skill_state.state == self.COOLDOWN:
                continue
            
            # 调用技能
            signal = self._call_skill(skill, symbol)
            if signal:
                total_signal += signal['signal'] * weight
                total_confidence += signal['confidence'] * weight
                total_weight += weight
                
                skill_state.use()
                results.append({
                    'skill': skill,
                    'weight': weight,
                    'signal': signal
                })
        
        if total_weight > 0 and total_confidence > 0:
            final_signal = total_signal / total_weight
            final_confidence = total_confidence / total_weight
            
            return {
                'action': 'trade',
                'symbol': symbol,
                'signal': final_signal,
                'confidence': final_confidence,
                'details': results
            }
        
        return {'action': 'skip', 'reason': 'No valid signals'}
    
    def _call_skill(self, skill: str, symbol: str) -> Optional[Dict]:
        """调用单个技能"""
        if not self.g40:
            return None
        
        try:
            # 调用G40的分析方法
            result = self.g40.optimizer.calculate_signal(symbol)
            return {
                'signal': result.get('signal', 0),
                'confidence': result.get('confidence', 0.5)
            }
        except:
            return None
    
    def record_trade_result(self, skill: str, pnl: float):
        """记录交易结果"""
        skill_state = self.skills.get(skill)
        if skill_state:
            if pnl > 0:
                skill_state.record_win(pnl)
            else:
                skill_state.record_loss(pnl)
    
    def get_skill_status(self) -> Dict:
        """获取所有技能状态"""
        status = {}
        for name, state in self.skills.items():
            status[name] = {
                'state': state.state,
                'score': state.score,
                'usage_count': state.usage_count,
                'win_rate': state.win_rate(),
                'avg_pnl': state.avg_pnl()
            }
        return status
    
    def recommend_skill(self, category: str) -> str:
        """推荐指定类别的最佳技能"""
        if category == 'trend':
            skills = self.TREND_SKILLS
        elif category == 'range':
            skills = self.RANGE_SKILLS
        elif category == 'risk':
            skills = self.RISK_SKILLS
        else:
            return None
        
        best_skill = None
        best_score = -1
        
        for skill in skills:
            state = self.skills.get(skill)
            if state and state.state == SkillState.ACTIVE:
                if state.score > best_score:
                    best_score = state.score
                    best_skill = skill
        
        return best_skill


# 全局函数
def get_optimal_combination(market_regime: str, confidence: float = 0.5) -> List[Tuple[str, float]]:
    """获取最佳技能组合 (快捷函数)"""
    meta = SkillMeta()
    return meta.get_optimal_combination(market_regime, confidence)


# ============ 主程序 ============

if __name__ == "__main__":
    print("SkillMeta - G40 技能调度元系统")
    print("=" * 50)
    
    meta = SkillMeta()
    
    # 显示所有组合
    for regime, combo in meta.COMBINATIONS.items():
        print(f"\n{combo['description']} ({regime}):")
        for skill, weight in zip(combo['skills'], combo['weights']):
            print(f"  {skill}: {weight:.0%}")
    
    # 测试获取组合
    print("\n" + "=" * 50)
    print("测试: trending市场, 信心度0.7")
    combo = meta.get_optimal_combination('trending', 0.7)
    for skill, weight in combo:
        print(f"  {skill}: {weight:.1%}")
