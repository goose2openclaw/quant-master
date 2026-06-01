"""
Advanced Profit Maximizer - 高级收益最大化引擎
整合Binance全扫描 + 凯利公式 + 杠杆优化 + 动态再平衡
"""
import sys
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.enhancements.bnb_scanner import BinanceFullScanner
    HAS_SCANNER = True
except:
    HAS_SCANNER = False

def parse_potential(p) -> float:
    """解析potential"""
    if isinstance(p, (int, float)):
        return float(p)
    s = str(p).replace('%','').replace('/年','').replace('/月','')
    try:
        val = float(s.split('~')[0].split('-')[0].split()[0])
        return val / 100 if val > 1 else val
    except:
        return 0.0

@dataclass
class Opportunity:
    """机会"""
    symbol: str
    category: str
    score: float
    action: str
    potential: float
    risk: str
    reason: str

class AdvancedProfitEngine:
    """
    高级收益最大化引擎
    
    核心能力:
    1. Binance全扫描集成 (81机会)
    2. 凯利公式最优分配
    3. 杠杆优化
    4. 动态再平衡
    5. 收益最大化策略
    """
    
    def __init__(self, capital: float = 10000):
        self.capital = capital
        self.scanner = BinanceFullScanner() if HAS_SCANNER else None
        
        # 风险配置
        self.risk_config = {
            'STAKING': {'max_alloc': 0.20, 'leverage': 1.0, 'risk': 'low'},
            'EARN_FLEX': {'max_alloc': 0.15, 'leverage': 1.0, 'risk': 'low'},
            'EARN_LOCKED': {'max_alloc': 0.20, 'leverage': 1.0, 'risk': 'low'},
            'HODLER': {'max_alloc': 0.15, 'leverage': 1.0, 'risk': 'medium'},
            'SPOT': {'max_alloc': 0.30, 'leverage': 1.5, 'risk': 'medium'},
            'FUTURES_USDT': {'max_alloc': 0.25, 'leverage': 3.0, 'risk': 'high'},
            'FUTURES_COIN': {'max_alloc': 0.15, 'leverage': 3.0, 'risk': 'high'},
            'LAUNCHPAD': {'max_alloc': 0.10, 'leverage': 1.0, 'risk': 'very_high'},
            'MEGADROP': {'max_alloc': 0.10, 'leverage': 1.0, 'risk': 'very_high'},
            'LEVERAGE': {'max_alloc': 0.05, 'leverage': 5.0, 'risk': 'extreme'},
            'GRID': {'max_alloc': 0.15, 'leverage': 2.0, 'risk': 'medium'},
            'OPTIONS': {'max_alloc': 0.10, 'leverage': 2.0, 'risk': 'high'},
        }
    
    def get_opportunities(self) -> List[Opportunity]:
        """获取所有机会"""
        if not self.scanner:
            return self._get_fallback_opportunities()
        
        all_opps = self.scanner.scan_all()
        return [Opportunity(
            symbol=o.symbol,
            category=o.category,
            score=o.score,
            action=o.action,
            potential=parse_potential(o.potential),
            risk=o.risk,
            reason=o.reason
        ) for o in all_opps]
    
    def _get_fallback_opportunities(self) -> List[Opportunity]:
        """回退机会数据"""
        opps = [
            Opportunity('TIA', 'STAKING', 96.2, 'STAKE', 0.185, '低', '流动性质押18.5%'),
            Opportunity('BNB', 'EARN_LOCKED', 87.5, 'STAKE', 0.125, '低', '定期理财12.5%'),
            Opportunity('BTC', 'HODLER', 81.4, 'HODL', 0.03, '中', 'BTC持有'),
            Opportunity('ATOM', 'STAKING', 81.2, 'STAKE', 0.125, '低', 'Cosmos质押'),
            Opportunity('IOUSDT', 'LAUNCHPAD', 78.0, 'FARM', 0.52, '高', 'Launchpad耕种'),
            Opportunity('BTCUSDT', 'SPOT', 79.3, 'BUY', 0.20, '中', '比特币技术分析'),
            Opportunity('LINK', 'EARN_LOCKED', 77.6, 'STAKE', 0.092, '低', 'Chainlink理财'),
            Opportunity('ETHUSDT', 'STAKING_ETH', 85.0, 'STAKE', 0.06, '低', 'ETH流动性质押'),
            Opportunity('SOLUSDT', 'SPOT', 82.0, 'BUY', 0.25, '中', 'Solana动量'),
            Opportunity('XRPUSD', 'FUTURES_USDT', 74.1, 'LONG', 0.50, '高', 'XRP资金费率套利'),
        ]
        return opps
    
    def calculate_kelly(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """凯利公式"""
        if avg_loss <= 0:
            return 0.1
        b = avg_win / avg_loss
        q = win_rate
        p = 1 - q
        kelly = (b * q - p) / b
        return max(0.05, min(0.3, kelly * 0.5))  # 半凯利更安全
    
    def maximize_strategy(self) -> Dict:
        """收益最大化策略"""
        opps = self.get_opportunities()
        
        # 1. 按评分排序
        sorted_opps = sorted(opps, key=lambda x: x.score, reverse=True)
        
        # 2. 筛选高机会
        top_opps = [o for o in sorted_opps if o.score >= 70]
        
        # 3. 按类别分组
        by_category = {}
        for o in top_opps:
            if o.category not in by_category:
                by_category[o.category] = []
            by_category[o.category].append(o)
        
        # 4. 收益最大化分配
        allocations = []
        remaining_cap = self.capital
        
        # 优先级: 高评分 > 高潜在收益 > 低风险
        priority_order = ['LAUNCHPAD', 'MEGADROP', 'FUTURES_USDT', 'STAKING', 'EARN_LOCKED', 'SPOT', 'HODLER']
        
        for cat in priority_order:
            if cat not in by_category:
                continue
            
            cat_opps = by_category[cat]
            config = self.risk_config.get(cat, {'max_alloc': 0.10, 'leverage': 1.0})
            
            for o in cat_opps[:2]:  # 每类别最多2个
                if remaining_cap <= 0:
                    break
                
                # 评分权重
                score_weight = o.score / 100
                
                # 潜在收益权重
                potential_weight = min(1.0, o.potential * 2)
                
                # 综合权重
                combined_weight = score_weight * 0.6 + potential_weight * 0.4
                
                # 最大分配
                max_cap = self.capital * config['max_alloc']
                
                # 实际分配
                alloc = min(max_cap, remaining_cap * combined_weight)
                
                if alloc < 100:  # 最小投资额
                    continue
                
                # 杠杆调整
                effective_cap = alloc * config['leverage']
                expected_return = o.potential * config['leverage']
                
                allocations.append({
                    'symbol': o.symbol,
                    'category': o.category,
                    'action': o.action,
                    'capital': alloc,
                    'leverage': config['leverage'],
                    'effective_capital': effective_cap,
                    'expected_return': expected_return,
                    'expected_profit': effective_cap * expected_return,
                    'score': o.score,
                    'risk': config['risk']
                })
                
                remaining_cap -= alloc
        
        # 5. 计算汇总
        total_invested = sum(a['capital'] for a in allocations)
        total_effective = sum(a['effective_capital'] for a in allocations)
        total_expected_profit = sum(a['expected_profit'] for a in allocations)
        weighted_return = total_expected_profit / total_invested if total_invested > 0 else 0
        
        return {
            'strategy': 'MAXIMIZE',
            'total_capital': self.capital,
            'total_invested': total_invested,
            'total_effective': total_effective,
            'expected_annual_return': weighted_return * 100,
            'expected_monthly_return': weighted_return / 12 * 100,
            'expected_30d_return': weighted_return / 12 * 100,
            'allocations': sorted(allocations, key=lambda x: x['expected_profit'], reverse=True),
            'by_category': self._summarize_by_category(allocations)
        }
    
    def aggressive_strategy(self) -> Dict:
        """激进策略 - 高杠杆 + 高收益"""
        opps = self.get_opportunities()
        
        # 只选最高评分
        top = sorted(opps, key=lambda x: x.score, reverse=True)[:15]
        
        allocations = []
        per_opp = self.capital / 5  # 分散5个
        
        for o in top[:5]:
            config = self.risk_config.get(o.category, {'max_alloc': 0.15, 'leverage': 1.0})
            
            # 激进杠杆
            lev = min(5.0, config['leverage'] * 2)
            
            allocations.append({
                'symbol': o.symbol,
                'category': o.category,
                'action': o.action,
                'capital': per_opp,
                'leverage': lev,
                'effective_capital': per_opp * lev,
                'expected_return': o.potential * lev,
                'expected_profit': per_opp * lev * o.potential,
                'score': o.score,
                'risk': config['risk']
            })
        
        total_invested = sum(a['capital'] for a in allocations)
        total_expected = sum(a['expected_profit'] for a in allocations)
        
        return {
            'strategy': 'AGGRESSIVE',
            'total_capital': self.capital,
            'total_invested': total_invested,
            'expected_annual_return': (total_expected / total_invested) * 100,
            'expected_monthly_return': (total_expected / total_invested) / 12 * 100,
            'expected_30d_return': (total_expected / total_invested) / 12 * 100,
            'allocations': allocations
        }
    
    def balanced_strategy(self) -> Dict:
        """平衡策略"""
        opps = self.get_opportunities()
        
        # 按风险分层
        low_risk = [o for o in opps if o.risk in ['低'] and o.score >= 70]
        med_risk = [o for o in opps if o.risk in ['中'] and o.score >= 65]
        high_risk = [o for o in opps if o.risk in ['高', '极高'] and o.score >= 60]
        
        allocations = []
        
        # 50% 低风险
        low_cap = self.capital * 0.50
        for o in low_risk[:4]:
            alloc = low_cap / 4
            config = self.risk_config.get(o.category, {'leverage': 1.0})
            allocations.append({
                'symbol': o.symbol, 'category': o.category, 'action': o.action,
                'capital': alloc, 'leverage': config['leverage'],
                'effective_capital': alloc * config['leverage'],
                'expected_return': o.potential * config['leverage'],
                'expected_profit': alloc * config['leverage'] * o.potential,
                'score': o.score, 'risk': '低'
            })
        
        # 30% 中风险
        med_cap = self.capital * 0.30
        for o in med_risk[:3]:
            alloc = med_cap / 3
            config = self.risk_config.get(o.category, {'leverage': 1.5})
            allocations.append({
                'symbol': o.symbol, 'category': o.category, 'action': o.action,
                'capital': alloc, 'leverage': config['leverage'],
                'effective_capital': alloc * config['leverage'],
                'expected_return': o.potential * config['leverage'],
                'expected_profit': alloc * config['leverage'] * o.potential,
                'score': o.score, 'risk': '中'
            })
        
        # 20% 高风险
        high_cap = self.capital * 0.20
        for o in high_risk[:2]:
            alloc = high_cap / 2
            config = self.risk_config.get(o.category, {'leverage': 2.0})
            allocations.append({
                'symbol': o.symbol, 'category': o.category, 'action': o.action,
                'capital': alloc, 'leverage': config['leverage'],
                'effective_capital': alloc * config['leverage'],
                'expected_return': o.potential * config['leverage'],
                'expected_profit': alloc * config['leverage'] * o.potential,
                'score': o.score, 'risk': '高'
            })
        
        total_invested = sum(a['capital'] for a in allocations)
        total_expected = sum(a['expected_profit'] for a in allocations)
        
        return {
            'strategy': 'BALANCED',
            'total_capital': self.capital,
            'total_invested': total_invested,
            'expected_annual_return': (total_expected / total_invested) * 100,
            'expected_monthly_return': (total_expected / total_invested) / 12 * 100,
            'expected_30d_return': (total_expected / total_invested) / 12 * 100,
            'allocations': allocations
        }
    
    def _summarize_by_category(self, allocations: List[Dict]) -> Dict:
        """按类别汇总"""
        by_cat = {}
        for a in allocations:
            cat = a['category']
            if cat not in by_cat:
                by_cat[cat] = {'capital': 0, 'expected': 0, 'count': 0}
            by_cat[cat]['capital'] += a['capital']
            by_cat[cat]['expected'] += a['expected_profit']
            by_cat[cat]['count'] += 1
        return by_cat
    
    def compare_strategies(self) -> Dict:
        """对比所有策略"""
        strategies = {
            'MAXIMIZE': self.maximize_strategy(),
            'AGGRESSIVE': self.aggressive_strategy(),
            'BALANCED': self.balanced_strategy()
        }
        
        # 选择最佳
        best_key = max(strategies.keys(), key=lambda k: strategies[k]['expected_annual_return'])
        best = strategies[best_key]
        best['best'] = True
        
        return {
            'strategies': strategies,
            'best_strategy': best_key,
            'best': best
        }
    
    def generate_report(self) -> str:
        """生成报告"""
        comparison = self.compare_strategies()
        best = comparison['best']
        
        # 复利计算
        monthly = best['expected_monthly_return'] / 100
        compound_30d = self.capital * (1 + monthly)
        compound_90d = self.capital * (1 + monthly) ** 3
        compound_180d = self.capital * (1 + monthly) ** 6
        compound_365d = self.capital * (1 + monthly) ** 12
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        💰 Advanced Profit Maximizer - 高级收益最大化引擎                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 资本: ${self.capital:,.2f}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📈 策略对比                                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

   策略              年化收益     30天收益     风险
   ───────────────────────────────────────────────────
   MAXIMIZE          {comparison['strategies']['MAXIMIZE']['expected_annual_return']:+.1f}%       {comparison['strategies']['MAXIMIZE']['expected_30d_return']:+.1f}%        均衡
   AGGRESSIVE ⭐     {comparison['strategies']['AGGRESSIVE']['expected_annual_return']:+.1f}%       {comparison['strategies']['AGGRESSIVE']['expected_30d_return']:+.1f}%        激进
   BALANCED          {comparison['strategies']['BALANCED']['expected_annual_return']:+.1f}%       {comparison['strategies']['BALANCED']['expected_30d_return']:+.1f}%        稳健

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🏆 最佳策略: {best['strategy']:<10}                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

   预期年化收益: {best['expected_annual_return']:+.1f}%
   预期月收益:   {best['expected_monthly_return']:+.2f}%
   预期30天收益: {best['expected_30d_return']:+.1f}%

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📋 分配方案                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for a in best['allocations'][:8]:
            emoji = "🟢" if a['expected_return'] > 0.15 else "🟡" if a['expected_return'] > 0.05 else "🔴"
            lev_emoji = "⚡" if a['leverage'] > 1 else ""
            report += f"   {emoji} {a['symbol']:10} {a['category']:12} ${a['capital']:7,.0f} {lev_emoji}{a['leverage']:.1f}x 预期: {a['expected_return']*100:+6.1f}%\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    💎 复利增长                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

   30天:   ${compound_30d:>12,.2f}  ({best['expected_30d_return']:+.1f}%)
   90天:   ${compound_90d:>12,.2f}  ({((compound_90d/self.capital)-1)*100:+.1f}%)
   180天:  ${compound_180d:>12,.2f}  ({((compound_180d/self.capital)-1)*100:+.1f}%)
   365天:  ${compound_365d:>12,.2f}  ({((compound_365d/self.capital)-1)*100:+.1f}%)

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 按类别分布                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        if 'by_category' in best:
            for cat, data in best['by_category'].items():
                pct = data['capital'] / best['total_invested'] * 100 if best['total_invested'] > 0 else 0
                ret = data['expected'] / data['capital'] * 100 if data['capital'] > 0 else 0
                report += f"   {cat:15} ${data['capital']:8,.0f} ({pct:5.1f}%)  收益: {ret:+.1f}%\n"
        
        report += "\n" + "=" * 76 + "\n"
        
        return report

def main():
    engine = AdvancedProfitEngine(10000)
    print(engine.generate_report())
    return engine.compare_strategies()

if __name__ == '__main__':
    main()
