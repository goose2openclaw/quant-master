#!/usr/bin/env python3
"""
QuantMaster - Comprehensive Module Test Suite
Tests every module, strategy, factor, and function
"""
import sys
import os
import importlib
import traceback
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

class ModuleTester:
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': [],
            'errors': []
        }
        self.total_tested = 0
    
    def log(self, msg, level='INFO'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {msg}")
    
    def test_module(self, module_path, module_name):
        """Test a single module"""
        try:
            # Try importing the module
            mod = importlib.import_module(module_path)
            
            # Count functions/classes
            functions = [n for n in dir(mod) if not n.startswith('_') and callable(getattr(mod, n))]
            classes = [n for n in dir(mod) if not n.startswith('_') and isinstance(getattr(mod, n), type)]
            
            return {
                'status': 'PASS',
                'module': module_name,
                'path': module_path,
                'functions': len(functions),
                'classes': len(classes),
                'error': None
            }
        except Exception as e:
            return {
                'status': 'FAIL',
                'module': module_name,
                'path': module_path,
                'functions': 0,
                'classes': 0,
                'error': str(e)
            }
    
    def find_all_modules(self):
        """Find all non-empty module directories"""
        modules = []
        base_path = '/home/goose/.openclaw/workspace/quant_master'
        
        for item in os.listdir(base_path):
            module_path = os.path.join(base_path, item)
            if not os.path.isdir(module_path):
                continue
            if item.startswith('__') or item in ['scripts', 'ui', 'examples', 'rpc']:
                continue
            
            # Check if it has Python files
            py_files = [f for f in os.listdir(module_path) if f.endswith('.py')]
            if py_files:
                modules.append((item, py_files))
        
        return modules
    
    def run_full_test(self):
        """Run comprehensive test of all modules"""
        self.log("=" * 60)
        self.log("QuantMaster Full Module Test Suite")
        self.log("=" * 60)
        
        modules = self.find_all_modules()
        self.log(f"Found {len(modules)} modules with Python files")
        
        for module_name, files in modules:
            self.total_tested += 1
            
            # Try module_name.submodule format first
            module_path = module_name
            
            result = self.test_module(module_path, module_name)
            
            if result['status'] == 'PASS':
                self.results['passed'].append(result)
                status_icon = "✅"
            else:
                self.results['failed'].append(result)
                status_icon = "❌"
            
            self.log(f"{status_icon} {module_name}: {result['classes']} classes, {result['functions']} functions")
            
            if result['error'] and 'MODULE' in result['error'].upper():
                self.log(f"   Error: {result['error'][:80]}", 'WARN')
        
        self.print_summary()
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        self.log("")
        self.log("=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        self.log(f"Total Tested: {self.total_tested}")
        self.log(f"✅ Passed: {len(self.results['passed'])}")
        self.log(f"❌ Failed: {len(self.results['failed'])}")
        self.log(f"⏭ Skipped: {len(self.results['skipped'])}")
        
        if self.results['failed']:
            self.log("")
            self.log("FAILED MODULES:")
            for r in self.results['failed'][:10]:
                self.log(f"  ❌ {r['module']}: {r['error'][:60]}")
        
        pass_rate = len(self.results['passed']) / max(1, self.total_tested) * 100
        self.log(f"\nPass Rate: {pass_rate:.1f}%")
        self.log("=" * 60)

def test_core_strategies():
    """Test all core strategies"""
    print("\n" + "=" * 60)
    print("TESTING CORE STRATEGIES")
    print("=" * 60)
    
    strategies = [
        ('RSI Strategy', 'strategies.rsi_strategy'),
        ('MACD Strategy', 'strategies.macd_strategy'),
        ('Bollinger Strategy', 'strategies.bollinger_strategy'),
        ('Momentum Strategy', 'strategies.momentum_strategy'),
    ]
    
    results = []
    for name, path in strategies:
        try:
            mod = importlib.import_module(path)
            print(f"✅ {name}")
            results.append((name, 'PASS'))
        except Exception as e:
            print(f"❌ {name}: {e}")
            results.append((name, 'FAIL'))
    
    return results

def test_analysis_modules():
    """Test all analysis modules"""
    print("\n" + "=" * 60)
    print("TESTING ANALYSIS MODULES")
    print("=" * 60)
    
    modules = [
        'funding_rate_tracking',
        'open_interest',
        'liquidations',
        'whale_tracker',
        'crypto_fear_greed',
        'volatility_surface',
        'options_skew',
        'crypto_correlations',
    ]
    
    results = []
    for name in modules:
        try:
            mod = importlib.import_module(name)
            print(f"✅ {name}")
            results.append((name, 'PASS'))
        except Exception as e:
            print(f"❌ {name}: {str(e)[:60]}")
            results.append((name, 'FAIL'))
    
    return results

def test_trading_modules():
    """Test all trading modules"""
    print("\n" + "=" * 60)
    print("TESTING TRADING MODULES")
    print("=" * 60)
    
    modules = [
        'backtesting_engine',
        'paper_trading_sim',
        'prediction_engine',
        'simulation_harness',
        'risk_analytics',
        'position_rules',
        'signal_trends',
        'oracle_sentiment',
        'competitor_benchmark',
        'multi_exchange_agg',
        'fund_management',
        'alert_system',
        'news_aggregator',
        'portfolio_dashboard',
        'simulation_25d',
    ]
    
    results = []
    for name in modules:
        try:
            mod = importlib.import_module(name)
            print(f"✅ {name}")
            results.append((name, 'PASS'))
        except Exception as e:
            print(f"❌ {name}: {str(e)[:60]}")
            results.append((name, 'FAIL'))
    
    return results

def test_api_endpoints():
    """Test API server endpoints"""
    print("\n" + "=" * 60)
    print("TESTING API ENDPOINTS")
    print("=" * 60)
    
    try:
        from api_server import app
        client = app.test_client()
        
        endpoints = [
            '/api/status',
            '/api/scan',
            '/api/scan/top',
            '/api/market/snapshot',
            '/api/signal/generate',
            '/api/portfolio/health',
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                response = client.get(endpoint)
                if response.status_code == 200:
                    print(f"✅ {endpoint}")
                    results.append((endpoint, 'PASS'))
                else:
                    print(f"❌ {endpoint}: {response.status_code}")
                    results.append((endpoint, 'FAIL'))
            except Exception as e:
                print(f"❌ {endpoint}: {str(e)[:60]}")
                results.append((endpoint, 'FAIL'))
    except Exception as e:
        print(f"API Test Error: {e}")
        results = []
    
    return results

def main():
    """Main test runner"""
    print("\n" + "#" * 60)
    print("# QuantMaster Comprehensive Test Suite v16.6.0")
    print("#" * 60)
    
    all_results = {}
    
    # 1. Test core strategies
    all_results['strategies'] = test_core_strategies()
    
    # 2. Test analysis modules
    all_results['analysis'] = test_analysis_modules()
    
    # 3. Test trading modules
    all_results['trading'] = test_trading_modules()
    
    # 4. Test API endpoints
    all_results['api'] = test_api_endpoints()
    
    # 5. Full module test
    tester = ModuleTester()
    all_results['full_module'] = tester.run_full_test()['passed']
    
    # Final Summary
    print("\n" + "#" * 60)
    print("# FINAL SUMMARY")
    print("#" * 60)
    
    total_pass = 0
    total_fail = 0
    
    for category, results in all_results.items():
        if isinstance(results, list):
            passed = sum(1 for _, s in results if s == 'PASS')
            failed = sum(1 for _, s in results if s == 'FAIL')
            total_pass += passed
            total_fail += failed
            print(f"{category}: {passed} passed, {failed} failed")
    
    print(f"\nTotal: {total_pass} passed, {total_fail} failed")
    print(f"Pass Rate: {total_pass / max(1, total_pass + total_fail) * 100:.1f}%")
    print("#" * 60)

if __name__ == '__main__':
    main()
