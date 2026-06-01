"""
GM V2 - 整合Hunter V2的强化版
"""
import sys
import time
import random
from typing import Dict, List

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.hunter_v2 import HunterV2
    from qm.g46_integration import G46Integration
    from qm.deep_system import DeepSystem
    from qm.profit_maximizer import ProfitMaximizer
    HAS_V2 = True
except Exception as e:
    HAS_V2 = False
    print(f"Import error: {e}")

class GMV2:
    """
    GM V2 - 强化版统一系统
    整合Hunter V2 + G46 + DeepSystem
    """
    
    def __init__(self, capital: float = 10000):
        self.capital = capital
        self.initial_capital = capital
        
        # 初始化Hunter V2
        print("=" * 60)
        print("🚀 GM V2 - 初始化")
        print("=" * 60)
        
        self.hunter = HunterV2()
        print("✅ Hunter V2 OK")
        
        try:
            self.g46 = G46Integration(self.capital)
            print("✅ G46Integration OK")
        except:
            self.g46 = None
            print("⚠️ G46 limited")
        
        try:
            self.deep = DeepSystem(self.capital)
            print("✅ DeepSystem OK")
        except:
            self.deep = None
            print("⚠️ DeepSystem limited")
        
        print("=" * 60)
    
    def run_scan(self) -> Dict:
        """运行扫描"""
        print("\n" + "=" * 60)
        print("🔍 GM V2 Full Scan")
        print("=" * 60)
        
        results = {
            'timestamp': time.time(),
            'hunter': {},
            'g46': {},
            'deep': {},
            'summary': {}
        }
        
        # Hunter V2扫描
        print("\n🎯 Hunter V2扫描...")
        report = self.hunter.generate_report()
        
        # 解析Hunter结果
        signals = self.hunter.scan_all()
        buys = [s for s in signals if s.action in ['BUY', 'LONG']]
        sells = [s for s in signals if s.action in ['SELL', 'SHORT']]
        
        results['hunter'] = {
            'total': len(signals),
            'buys': len(buys),
            'sells': len(sells),
            'top_buys': buys[:5],
            'top_sells': sells[:5]
        }
        
        print(f"   发现: {len(signals)}个信号 (🟢{len(buys)} 🔴{len(sells)})")
        
        # G46扫描
        if self.g46:
            print("\n🔧 G46扫描...")
            try:
                g46_result = self.g46.run_full_scan()
                scan = g46_result.get('scan', {})
                results['g46'] = {
                    'total': scan.get('total', 0),
                    'buy_signals': len(scan.get('buy_signals', [])),
                    'sell_signals': len(scan.get('sell_signals', []))
                }
                print(f"   扫描: {scan.get('total', 0)}币")
                print(f"   买入: {len(scan.get('buy_signals', []))}信号")
            except Exception as e:
                print(f"   ⚠️ G46 error: {e}")
        
        # Deep系统
        if self.deep:
            print("\n🔍 DeepSystem扫描...")
            try:
                deep_result = self.deep.run()
                results['deep'] = deep_result
                print(f"   机会: {deep_result.get('scan', {}).get('total', 0)}个")
            except Exception as e:
                print(f"   ⚠️ Deep error: {e}")
        
        # 综合评分
        print("\n📊 综合分析...")
        
        # 计算综合评分
        hunter_score = len(buys) * 10 - len(sells) * 8
        g46_score = results['g46'].get('buy_signals', 0) * 10 - results['g46'].get('sell_signals', 0) * 8
        
        overall = (hunter_score + g46_score) / 2
        
        results['summary'] = {
            'hunter_score': hunter_score,
            'g46_score': g46_score,
            'overall': overall,
            'recommendation': 'BUY' if overall > 20 else ('SELL' if overall < -20 else 'HOLD')
        }
        
        print(f"   Hunter评分: {hunter_score}")
        print(f"   G46评分: {g46_score}")
        print(f"   综合评分: {overall:.1f}")
        print(f"   建议: {results['summary']['recommendation']}")
        
        return results
    
    def generate_report(self) -> str:
        """生成报告"""
        results = self.run_scan()
        
        hunter = results.get('hunter', {})
        summary = results.get('summary', {})
        
        # 推荐信号
        top_buys = hunter.get('top_buys', [])
        top_sells = hunter.get('top_sells', [])
        
        rec = summary.get('recommendation', 'HOLD')
        rec_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(rec, '⚪')
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🚀 GM V2 Report - {time.strftime('%Y-%m-%d %H:%M')}                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏰ 生成时间: {time.strftime('%H:%M:%S')}

╔══════════════════════════════════════════════════════════════════════════════╗
║           📊 系统状态                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   资金: ${self.capital:,.2f}
   版本: GM V2 (Hunter V2 + G46 + DeepSystem)
   状态: ✅ 正常运行

╔══════════════════════════════════════════════════════════════════════════════╗
║           📈 信号概览                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   Hunter V2: {hunter.get('total', 0)}个信号
   🟢 买入: {hunter.get('buys', 0)}个
   🔴 卖出: {hunter.get('sells', 0)}个

╔══════════════════════════════════════════════════════════════════════════════╗
║           🎯 综合评分                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   Hunter评分: {summary.get('hunter_score', 0):+.0f}
   G46评分: {summary.get('g46_score', 0):+.0f}
   综合评分: {summary.get('overall', 0):+.1f}

╔══════════════════════════════════════════════════════════════════════════════╗
║           💡 交易建议: {rec_emoji} {rec}                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        if rec == 'BUY' and top_buys:
            report += f"""
🟢 买入信号 (TOP 5):

"""
            for i, sig in enumerate(top_buys[:5], 1):
                report += f"""   {i}. {sig.symbol:8} {sig.type:20}
      评分: {sig.score:.1f} | 置信: {sig.confidence:.0f}%
      入场: ${sig.entry:.4f} | 目标: ${sig.target:.4f}
      风险回报: {sig.risk_reward:.1f}:1

"""
        
        elif rec == 'SELL' and top_sells:
            report += f"""
🔴 卖出信号 (TOP 5):

"""
            for i, sig in enumerate(top_sells[:5], 1):
                report += f"""   {i}. {sig.symbol:8} {sig.type:20}
      评分: {sig.score:.1f} | 置信: {sig.confidence:.0f}%
      入场: ${sig.entry:.4f} | 目标: ${sig.target:.4f}
      风险回报: {sig.risk_reward:.1f}:1

"""
        
        else:
            report += """
⚠️ 当前市场信号不明显,建议观望

   市场震荡期间,等待更明确的信号出现
   建议关注支撑位反弹信号

"""
        
        return report
    
    def run(self):
        """运行"""
        print(self.generate_report())

def main():
    gm = GMV2(10000)
    gm.run()

if __name__ == '__main__':
    main()
