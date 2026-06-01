"""
Enhanced QM - QuantMaster with Full Binance Coverage
"""
import sys
import time
import random
from typing import List, Dict, Optional

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.enhancements.bnb_scanner import BinanceFullScanner
    HAS_FULL_SCANNER = True
except:
    HAS_FULL_SCANNER = False

class EnhancedQM:
    """
    Enhanced QM - 币安全覆盖
    
    Features:
    - 14个币安产品类别全覆盖
    - 利益最大化策略
    - 智能分配
    """
    
    def __init__(self, capital: float = 10000):
        self.capital = capital
        self.initial_capital = capital
        
        # 初始化全扫描器
        if HAS_FULL_SCANNER:
            self.scanner = BinanceFullScanner()
        
        # 分配策略
        self.allocation = {
            'SPOT': 0.30,        # 30% 现货
            'FUTURES': 0.20,     # 20% 合约
            'EARN': 0.25,         # 25% 理财
            'LAUNCH': 0.10,       # 10% Launchpad
            'STAKING': 0.15,      # 15% 流动性质押
        }
        
    def scan_all_opportunities(self) -> Dict:
        """扫描所有机会"""
        if not HAS_FULL_SCANNER:
            return {'total': 0, 'opportunities': []}
        
        all_opps = self.scanner.scan_all()
        
        # 按类别分组
        by_category = {}
        for opp in all_opps:
            if opp.category not in by_category:
                by_category[opp.category] = []
            by_category[opp.category].append({
                'symbol': opp.symbol,
                'name': opp.name,
                'score': opp.score,
                'action': opp.action,
                'potential': opp.potential,
                'risk': opp.risk,
                'reason': opp.reason
            })
        
        return {
            'total': len(all_opps),
            'categories': len(by_category),
            'by_category': by_category,
            'top_20': [{
                'symbol': o.symbol,
                'category': o.category,
                'score': o.score,
                'action': o.action,
                'potential': o.potential
            } for o in all_opps[:20]]
        }
    
    def maximize_returns(self) -> Dict:
        """利益最大化分配"""
        if not HAS_FULL_SCANNER:
            return {}
        
        scan = self.scan_all_opportunities()
        
        # 按类别分配
        allocation_plan = {}
        
        for cat, pct in self.allocation.items():
            cat_opps = scan['by_category'].get(cat, [])
            if cat_opps:
                # 选择该类别最高分
                best = max(cat_opps, key=lambda x: x['score'])
                capital_alloc = self.capital * pct
                
                allocation_plan[cat] = {
                    'symbol': best['symbol'],
                    'score': best['score'],
                    'action': best['action'],
                    'potential': best['potential'],
                    'capital': capital_alloc,
                    'expected_return': self._calc_expected(cat, best['score'])
                }
        
        # 计算总预期收益
        total_expected = sum(v['expected_return'] for v in allocation_plan.values())
        
        return {
            'allocation_plan': allocation_plan,
            'total_expected': total_expected,
            'expected_30d_return': f"+{total_expected:.1f}%"
        }
    
    def _calc_expected(self, category: str, score: float) -> float:
        """计算预期收益"""
        # 基础收益
        base_returns = {
            'SPOT': 15,
            'FUTURES': 30,
            'EARN': 8,
            'LAUNCH': 50,
            'STAKING': 12,
            'BNB_VAULT': 10,
            'MEGADROP': 45,
            'HODLER': 5,
        }
        
        base = base_returns.get(category, 10)
        
        # 按评分调整
        score_factor = (score - 50) / 50 + 1  # 50分=1x, 100分=2x
        
        return base * score_factor
    
    def get_top_10(self) -> List[Dict]:
        """获取Top 10机会"""
        if not HAS_FULL_SCANNER:
            return []
        
        all_opps = self.scanner.scan_all()
        return [{
            'rank': i+1,
            'symbol': o.symbol,
            'category': o.category,
            'score': o.score,
            'action': o.action,
            'potential': o.potential,
            'risk': o.risk,
            'reason': o.reason
        } for i, o in enumerate(all_opps[:10])]
    
    def generate_report(self) -> str:
        """生成报告"""
        if not HAS_FULL_SCANNER:
            return "Full scanner not available"
        
        scan = self.scan_all_opportunities()
        max_plan = self.maximize_returns()
        top10 = self.get_top_10()
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║           Enhanced QM - 币安全覆盖 + 利益最大化                 ║
╚══════════════════════════════════════════════════════════════════════╝

📊 扫描结果:
   总机会: {scan['total']}
   类别数: {scan['categories']}

"""
        
        report += "📂 类别分布:\n"
        for cat, opps in scan['by_category'].items():
            top = max(opps, key=lambda x: x['score'])
            report += f"   {cat:15} {len(opps):2}个 最高: {top['score']:.1f} ({top['symbol']})\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    🏆 TOP 10 机会                                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        
        for item in top10:
            emoji = "🟢" if item['action'] in ['BUY', 'LONG', 'STAKE', 'FARM', 'LONG_FUNDING'] else "🔴"
            report += f"{item['rank']:2}. {emoji} {item['category']:12} {item['symbol']:12} {item['score']:5.1f} | {item['action']:12} | {item['potential']}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    💰 利益最大化分配                                ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        
        for cat, info in max_plan.get('allocation_plan', {}).items():
            report += f"   {cat:15} {info['symbol']:10} ${info['capital']:8,.0f} 预期: {info['expected_return']:.1f}%\n"
        
        report += f"""
   ═════════════════════════════════════════════
   总预期30天收益: {max_plan.get('expected_30d_return', 'N/A')}
   ═════════════════════════════════════════════
"""
        
        return report

def main():
    qm = EnhancedQM(10000)
    print(qm.generate_report())

if __name__ == '__main__':
    main()
