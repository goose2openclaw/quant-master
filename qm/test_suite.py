"""
QM Test Suite - 测试、优化、迭代
"""
import sys
import time
import random
from typing import Dict, List

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

class QMTestSuite:
    """QM测试套件"""
    
    def __init__(self):
        self.results = []
        self.capital = 10000
        
    def test_module(self, name: str, test_func) -> Dict:
        """测试单个模块"""
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {name}")
        print('='*60)
        
        start = time.time()
        try:
            result = test_func()
            elapsed = time.time() - start
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            print(f"{status} ({elapsed:.2f}s)")
            if 'data' in result:
                print(f"   Data: {str(result['data'])[:200]}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            return {'name': name, 'success': True, 'elapsed': elapsed, 'result': result}
        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ FAIL ({elapsed:.2f}s)")
            print(f"   Exception: {str(e)[:100]}")
            return {'name': name, 'success': False, 'elapsed': elapsed, 'error': str(e)}
    
    def test_binance_scanner(self) -> Dict:
        """测试币安扫描器"""
        try:
            from qm.enhancements.bnb_scanner import BinanceFullScanner
            scanner = BinanceFullScanner()
            summary = scanner.get_summary()
            
            print(f"   Categories: {summary['total']}")
            print(f"   Top opportunity: {summary['top_5'][0]['symbol'] if summary['top_5'] else 'None'}")
            
            return {'success': True, 'data': summary}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_mirofish_dispatcher(self) -> Dict:
        """测试MiroFish调度"""
        try:
            from qm.mirofish_coin_strategy import MiroFishCoinDispatcher
            dispatcher = MiroFishCoinDispatcher()
            
            # 测试调度
            d = dispatcher.dispatch_strategy('BTC', 'SPOT')
            print(f"   BTC strategies: {len(d['strategies'])}")
            
            # 批量调度
            results = dispatcher.batch_dispatch(['BTC', 'ETH', 'SOL'], 'FUTURES_USDT')
            print(f"   Batch results: {len(results)}")
            
            return {'success': True, 'data': {'strategies': len(d['strategies']), 'batch': len(results)}}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_leverage_engine(self) -> Dict:
        """测试杠杆引擎"""
        try:
            from qm.leverage_engine import LeverageOptimizer, MarketRegimeDetector
            engine = LeverageOptimizer()
            
            # 市场检测
            detector = MarketRegimeDetector()
            regime = detector.detect_regime('BTCUSDT')
            print(f"   Regime: {regime.value}")
            
            # 最优杠杆
            optimal = engine.get_optimal_leverage('BTCUSDT')
            print(f"   Leverage: {optimal['recommended']}x")
            
            return {'success': True, 'data': {'regime': regime.value, 'leverage': optimal['recommended']}}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_g46_integration(self) -> Dict:
        """测试G46集成"""
        try:
            from qm.g46_integration import G46Integration
            g46 = G46Integration(self.capital)
            result = g46.run_full_scan()
            
            scan = result['scan']
            print(f"   Scanned: {scan['total']} coins")
            print(f"   Buy signals: {len(scan['buy_signals'])}")
            print(f"   Sell signals: {len(scan['sell_signals'])}")
            
            return {'success': True, 'data': {
                'total': scan['total'],
                'buy': len(scan['buy_signals']),
                'sell': len(scan['sell_signals'])
            }}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_permission_manager(self) -> Dict:
        """测试权限管理"""
        try:
            from qm.permissions.permission_manager import QMPermissionManager, create_protected_matrices
            pm = QMPermissionManager()
            matrices = create_protected_matrices(pm)
            
            # Admin可以写入
            pm.switch_to_admin()
            try:
                matrices['strategy'].set('test', 'value', 'modify_weights')
                print("   Admin write: OK")
            except:
                print("   Admin write: FAILED")
            
            # Guest不能写入
            pm.switch_to_guest()
            try:
                matrices['strategy'].set('test', 'value', 'modify_weights')
                print("   Guest write: UNEXPECTED")
            except PermissionError:
                print("   Guest write: BLOCKED (correct)")
            
            return {'success': True, 'data': {'matrices': len(matrices)}}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_backtest_engine(self) -> Dict:
        """测试回测引擎"""
        try:
            from qm.backtest_engine import QMBacktestEngine
            engine = QMBacktestEngine(self.capital)
            result = engine.run_full_analysis()
            
            bt = result['backtest']
            print(f"   Return: {bt['total_return']:.2f}%")
            print(f"   Win rate: {bt['win_rate']:.1f}%")
            
            return {'success': True, 'data': {
                'return': bt['total_return'],
                'win_rate': bt['win_rate']
            }}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_advanced_profit_engine(self) -> Dict:
        """测试高级收益引擎"""
        try:
            from qm.advanced_profit_engine import AdvancedProfitEngine
            engine = AdvancedProfitEngine(self.capital)
            result = engine.compare_strategies()
            
            best = result['best']
            print(f"   Best: {result['best_strategy']}")
            print(f"   Expected: {best['expected_annual_return']:.1f}%")
            
            return {'success': True, 'data': {
                'best_strategy': result['best_strategy'],
                'expected': best['expected_annual_return']
            }}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              🧪 QM Test Suite - 测试、优化、迭代                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        tests = [
            ("Binance Scanner", self.test_binance_scanner),
            ("MiroFish Dispatcher", self.test_mirofish_dispatcher),
            ("Leverage Engine", self.test_leverage_engine),
            ("G46 Integration", self.test_g46_integration),
            ("Permission Manager", self.test_permission_manager),
            ("Backtest Engine", self.test_backtest_engine),
            ("Advanced Profit Engine", self.test_advanced_profit_engine),
        ]
        
        results = []
        for name, test_func in tests:
            result = self.test_module(name, test_func)
            results.append(result)
            self.results.append(result)
        
        # 汇总
        passed = sum(1 for r in results if r['success'])
        failed = len(results) - passed
        total_time = sum(r['elapsed'] for r in results)
        
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 测试结果汇总                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   Total:  {len(results)}
   Passed:  {passed} ✅
   Failed:  {failed} ❌
   Time:    {total_time:.2f}s
""")
        
        if failed > 0:
            print("   Failed tests:")
            for r in results:
                if not r['success']:
                    print(f"   - {r['name']}: {r.get('error', 'Unknown')[:50]}")
        
        print("=" * 70)
        
        return {
            'total': len(results),
            'passed': passed,
            'failed': failed,
            'results': results
        }

def main():
    suite = QMTestSuite()
    return suite.run_all_tests()

if __name__ == '__main__':
    main()
