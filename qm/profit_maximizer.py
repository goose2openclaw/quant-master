"""
QM Profit Maximizer - 利益最大化引擎
智能资本分配 + 风险对冲 + 复利策略
"""
import sys
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class AllocationPlan:
    """分配方案"""
    symbol: str
    category: str
    action: str
    capital: float
    expected_return: float
    risk_level: str
    allocation_pct: float

def parse_potential(p) -> float:
    """解析potential字符串"""
    if isinstance(p, (int, float)):
        return float(p)
    s = str(p).replace('%','').replace('/年','').replace('/月','')
    try:
        val = float(s.split('~')[0].split('-')[0].split()[0])
        return val / 100 if val > 1 else val
    except:
        return 0.0

class ProfitMaximizer:
    """
    利益最大化引擎
    
    策略:
    1. 核心-卫星策略 (Core-Satellite)
    2. 风险平价 (Risk Parity)
    3. 混合策略 (Hybrid)
    4. 凯利公式 (Kelly Criterion)
    5. 复利增长 (Compound Growth)
    """
    
    def __init__(self, total_capital: float = 10000):
        self.total_capital = total_capital
        self.risk_free_rate = 0.05  # 5%无风险利率
    
    def optimize_allocation(self, opportunities: List[Dict], strategy: str = 'hybrid') -> Dict:
        """优化分配方案"""
        
        if strategy == 'risk_parity':
            plans = self._risk_parity_allocation(opportunities)
        elif strategy == 'core_satellite':
            plans = self._core_satellite_allocation(opportunities)
        else:
            plans = self._hybrid_allocation(opportunities)
        
        # 计算汇总
        total_expected = sum(p.expected_return * p.capital for p in plans) / self.total_capital
        total_invested = sum(p.capital for p in plans)
        
        # 按类别汇总
        by_category = {}
        for p in plans:
            if p.category not in by_category:
                by_category[p.category] = {'capital': 0, 'expected': 0}
            by_category[p.category]['capital'] += p.capital
            by_category[p.category]['expected'] += p.expected_return * p.capital
        
        return {
            'strategy': strategy,
            'total_capital': self.total_capital,
            'total_invested': total_invested,
            'expected_return': total_expected,
            'expected_return_pct': total_expected * 100,
            'plans': [{
                'symbol': p.symbol,
                'category': p.category,
                'action': p.action,
                'capital': p.capital,
                'expected': p.expected_return * 100,
                'risk': p.risk_level
            } for p in plans],
            'by_category': by_category
        }
    
    def _risk_parity_allocation(self, opportunities: List[Dict]) -> List[AllocationPlan]:
        """风险平价分配"""
        plans = []
        
        # 按风险分类
        low_risk = [o for o in opportunities if o.get('risk') in ['低', '低-中']]
        medium_risk = [o for o in opportunities if o.get('risk') in ['中', '中-高']]
        high_risk = [o for o in opportunities if o.get('risk') in ['高', '极高']]
        
        total = self.total_capital
        allocations = [
            (low_risk, 0.40, '低风险'),
            (medium_risk, 0.35, '中风险'),
            (high_risk, 0.25, '高风险'),
        ]
        
        for opps, pct, risk_label in allocations:
            if not opps:
                continue
            cap = total * pct
            per_opp = cap / min(len(opps), 5)
            
            for opp in opps[:5]:
                plans.append(AllocationPlan(
                    symbol=opp['symbol'],
                    category=opp['category'],
                    action=opp['action'],
                    capital=per_opp,
                    expected_return=parse_potential(opp.get('potential', 0)),
                    risk_level=risk_label,
                    allocation_pct=pct / min(len(opps), 5)
                ))
        
        return plans
    
    def _core_satellite_allocation(self, opportunities: List[Dict]) -> List[AllocationPlan]:
        """核心-卫星策略"""
        plans = []
        
        # 核心: 70% 低风险稳定收益
        core_cap = self.total_capital * 0.70
        core_opps = [
            {'symbol': 'BTC', 'category': 'HODLER', 'action': 'HODL', 'expected': 0.05},
            {'symbol': 'BNB', 'category': 'EARN_LOCKED', 'action': 'STAKE', 'expected': 0.125},
            {'symbol': 'TIA', 'category': 'STAKING', 'action': 'STAKE', 'expected': 0.185},
            {'symbol': 'ETH', 'category': 'STAKING_ETH', 'action': 'STAKE', 'expected': 0.06},
        ]
        
        for opp in core_opps:
            cap = core_cap / len(core_opps)
            plans.append(AllocationPlan(
                symbol=opp['symbol'], category=opp['category'], action=opp['action'],
                capital=cap, expected_return=opp['expected'],
                risk_level='核心', allocation_pct=0.70/len(core_opps)
            ))
        
        # 卫星: 30% 高收益机会
        satellite_cap = self.total_capital * 0.30
        high_yield = sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)[:5]
        
        for opp in high_yield:
            cap = satellite_cap / len(high_yield)
            plans.append(AllocationPlan(
                symbol=opp['symbol'], category=opp['category'], action=opp['action'],
                capital=cap, expected_return=parse_potential(opp.get('potential', 0)),
                risk_level='卫星', allocation_pct=0.30/len(high_yield)
            ))
        
        return plans
    
    def _hybrid_allocation(self, opportunities: List[Dict]) -> List[AllocationPlan]:
        """混合策略"""
        plans = []
        
        # 40% 核心稳定
        core_cap = self.total_capital * 0.40
        core = [
            {'symbol': 'BTC', 'category': 'HODLER', 'action': 'HODL', 'expected': 0.05},
            {'symbol': 'ETH', 'category': 'STAKING_ETH', 'action': 'STAKE', 'expected': 0.06},
            {'symbol': 'BNB', 'category': 'BNB_VAULT', 'action': 'STAKE', 'expected': 0.10},
        ]
        for c in core:
            plans.append(AllocationPlan(
                symbol=c['symbol'], category=c['category'], action=c['action'],
                capital=core_cap/len(core), expected_return=c['expected'],
                risk_level='核心', allocation_pct=0.40/len(core)
            ))
        
        # 35% 收益增强
        enhanced_cap = self.total_capital * 0.35
        enhanced = sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)[:4]
        for e in enhanced:
            plans.append(AllocationPlan(
                symbol=e['symbol'], category=e['category'], action=e['action'],
                capital=enhanced_cap/len(enhanced), expected_return=parse_potential(e.get('potential', 0)),
                risk_level='增强', allocation_pct=0.35/len(enhanced)
            ))
        
        # 25% 高收益机会
        high_cap = self.total_capital * 0.25
        high_yield = [o for o in opportunities if o.get('action') in ['FARM', 'PARTICIPATE', 'LONG', 'SETUP_GRID']][:3]
        if not high_yield:
            high_yield = sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)[:3]
        for h in high_yield:
            plans.append(AllocationPlan(
                symbol=h['symbol'], category=h['category'], action=h['action'],
                capital=high_cap/len(high_yield), expected_return=parse_potential(h.get('potential', 0)),
                risk_level='高收益', allocation_pct=0.25/len(high_yield)
            ))
        
        return plans
    
    def calculate_compound_return(self, initial: float, monthly_rate: float, months: int) -> Dict:
        """计算复利收益"""
        final = initial
        
        for _ in range(months):
            actual_return = monthly_rate * random.uniform(0.7, 1.3)
            final = final * (1 + actual_return)
        
        return {
            'initial': initial,
            'final': final,
            'total_return': (final - initial) / initial * 100,
            'monthly_avg': monthly_rate * 100,
        }
    
    def generate_report(self, opportunities: List[Dict]) -> str:
        """生成收益最大化报告"""
        
        strategies = ['core_satellite', 'risk_parity', 'hybrid']
        results = {}
        
        for s in strategies:
            results[s] = self.optimize_allocation(opportunities, s)
        
        best = max(results.values(), key=lambda x: x['expected_return'])
        
        # 复利
        compound_30d = self.calculate_compound_return(self.total_capital, best['expected_return']/12, 1)
        compound_90d = self.calculate_compound_return(self.total_capital, best['expected_return']/12, 3)
        compound_180d = self.calculate_compound_return(self.total_capital, best['expected_return']/12, 6)
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           💰 QM Profit Maximizer - 利益最大化引擎                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 资本: ${self.total_capital:,.2f}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📈 三种策略对比                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

   策略              预期年化收益    风险水平
   ─────────────────────────────────────────────
   核心-卫星          {results['core_satellite']['expected_return_pct']:+.1f}%          中低风险
   风险平价          {results['risk_parity']['expected_return_pct']:+.1f}%          均衡风险
   混合策略 ⭐       {results['hybrid']['expected_return_pct']:+.1f}%          平衡配置

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🏆 最佳策略: {best['strategy']:<15}                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

   预期年化收益: {best['expected_return_pct']:+.1f}%
   资本总额: ${best['total_capital']:,.2f}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📋 分配方案                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for plan in best['plans']:
            emoji = "🟢" if plan['expected'] > 10 else "🟡" if plan['expected'] > 0 else "🔴"
            report += f"   {emoji} {plan['symbol']:10} {plan['category']:15} ${plan['capital']:8,.0f}  预期: {plan['expected']:+.1f}%\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    💎 复利增长预测                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

   30天:   ${compound_30d['final']:,.2f}  ({compound_30d['total_return']:+.1f}%)
   90天:   ${compound_90d['final']:,.2f}  ({compound_90d['total_return']:+.1f}%)
   180天:  ${compound_180d['final']:,.2f}  ({compound_180d['total_return']:+.1f}%)

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 按类别分布                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for cat, data in best['by_category'].items():
            pct = data['capital'] / best['total_invested'] * 100
            expected = data['expected'] / data['capital'] * 100 if data['capital'] > 0 else 0
            report += f"   {cat:15} ${data['capital']:8,.0f} ({pct:5.1f}%)  预期: {expected:+.1f}%\n"
        
        report += "\n" + "=" * 76 + "\n"
        
        return report

def main():
    pm = ProfitMaximizer(10000)
    
    opportunities = [
        {'symbol': 'TIA', 'category': 'STAKING', 'score': 96.2, 'action': 'STAKE', 'potential': '18.5%/年', 'risk': '低'},
        {'symbol': 'BNB', 'category': 'EARN_LOCKED', 'score': 87.5, 'action': 'STAKE', 'potential': '12.5%/年', 'risk': '低'},
        {'symbol': 'BTC', 'category': 'HODLER', 'score': 81.4, 'action': 'HODL', 'potential': '+3%', 'risk': '中'},
        {'symbol': 'ATOM', 'category': 'STAKING', 'score': 81.2, 'action': 'STAKE', 'potential': '12.5%/年', 'risk': '低'},
        {'symbol': 'IOUSDT', 'category': 'LAUNCHPAD', 'score': 78.0, 'action': 'FARM', 'potential': '52%', 'risk': '高'},
        {'symbol': 'BTCUSDT', 'category': 'SPOT', 'score': 79.3, 'action': 'BUY', 'potential': '10-30%/月', 'risk': '中'},
        {'symbol': 'LINK', 'category': 'EARN_LOCKED', 'score': 77.6, 'action': 'STAKE', 'potential': '9.2%/年', 'risk': '低'},
        {'symbol': 'ETHUSDT', 'category': 'STAKING_ETH', 'score': 85.0, 'action': 'STAKE', 'potential': '6%/年', 'risk': '低'},
    ]
    
    print(pm.generate_report(opportunities))

if __name__ == '__main__':
    main()
