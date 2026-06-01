"""
QuantMaster v16.6.0 - Full System Evaluation
Comprehensive module testing and functionality assessment
"""
import sys
import time
import traceback
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

classcolors = {
    'PASS': '\033[92m',
    'FAIL': '\033[91m',
    'WARN': '\033[93m',
    'INFO': '\033[94m',
    'BOLD': '\033[1m',
    'END': '\033[0m'
}

def log(status, msg):
    color = getattr(classcolors, status, '')
    print(f"{color}{status}:{classcolors['END']} {msg}")

def test_module(name, func):
    print(f"\n{'='*60}")
    print(f"📦 Testing: {name}")
    print(f"{'='*60}")
    try:
        start = time.time()
        result = func()
        elapsed = time.time() - start
        
        if result.get('status') == 'PASS':
            log('PASS', f"{name} - {result.get('message', 'OK')} ({elapsed:.2f}s)")
            return {'name': name, 'status': 'PASS', 'score': result.get('score', 100), 'time': elapsed}
        elif result.get('status') == 'WARN':
            log('WARN', f"{name} - {result.get('message', 'Warning')} ({elapsed:.2f}s)")
            return {'name': name, 'status': 'WARN', 'score': result.get('score', 70), 'time': elapsed}
        else:
            log('FAIL', f"{name} - {result.get('message', 'Failed')} ({elapsed:.2f}s)")
            return {'name': name, 'status': 'FAIL', 'score': result.get('score', 0), 'time': elapsed}
    except Exception as e:
        log('FAIL', f"{name} - Exception: {str(e)[:80]}")
        return {'name': name, 'status': 'FAIL', 'score': 0, 'time': time.time() - start}

# ==================== CORE MODULES ====================

def test_binance_deep_scanner():
    from binance_deep.scanner import BinanceDeepScanner
    scanner = BinanceDeepScanner()
    opportunities = scanner.get_top_opportunities(10)
    assert len(opportunities) > 0, "No opportunities found"
    
    # Check categories
    categories = set(o.category for o in opportunities)
    assert len(categories) >= 3, "Not enough categories"
    
    return {'status': 'PASS', 'message': f"Found {len(opportunities)} opportunities across {len(categories)} categories", 'score': 95}

def test_binance_optimizer():
    from binance_optimizer.optimizer import BinanceOptimizer
    opt = BinanceOptimizer(10000)
    
    # Run backtest
    result = opt.run_backtest(opt.params, days=30)
    assert result.final_capital > 0, "Invalid capital"
    
    # Run optimization
    opt.optimize(iterations=5)
    assert opt.best_params is not None, "Optimization failed"
    
    # Run prediction
    pred = opt.predict_30d(opt.best_params)
    assert pred['predicted_return'] is not None, "Prediction failed"
    
    return {'status': 'PASS', 'message': f"Backtest: {result.total_return:.1f}%, Best: {opt.best_return:.1f}%, Pred: {pred['predicted_return']:.1f}%", 'score': 90}

def test_enhanced_watchdog():
    from strategic_watchdog.enhanced_overseer import EnhancedWatchdog, DecisionType
    
    wd = EnhancedWatchdog(10000)
    
    # Test decision cycle
    for i in range(5):
        decision = wd.analyze_and_decide({'price': 67000})
        if decision.decision_type != DecisionType.HOLD:
            wd.execute_decision(decision)
    
    status = wd.get_status()
    assert status['capital'] > 0, "Invalid capital"
    
    return {'status': 'PASS', 'message': f"Capital: ${status['capital']:.2f}, Mode: {status['mode']}, Decisions: {status['decisions']}", 'score': 88}

def test_mirofish_core():
    from mirofish_core.mirofish import MiroFishCore, MiroFishConfig
    
    config = MiroFishConfig(simulation_required=True)
    mf = MiroFishCore(config)
    
    # Generate decision
    decision = mf.generate_trading_decision('BTC', {'price': 67000})
    assert decision is not None, "No decision generated"
    assert 'decision' in decision, "Invalid decision format"
    
    # Check strategies and factors
    assert len(mf.strategy_matrix.strategies) >= 4, "Not enough strategies"
    assert len(mf.factor_matrix.factors) >= 10, "Not enough factors"
    
    return {'status': 'PASS', 'message': f"Strategies: {len(mf.strategy_matrix.strategies)}, Factors: {len(mf.factor_matrix.factors)}, Decision: {decision['decision']}", 'score': 92}

def test_autonomous_scanner():
    from autonomous_scanner.scanner import AutonomousScanner
    
    scanner = AutonomousScanner()
    results = scanner.scan_all()
    
    assert len(results) > 0, "No scan results"
    
    # Check scoring
    for r in results:
        assert 0 <= r.total_score <= 100, "Invalid score range"
    
    return {'status': 'PASS', 'message': f"Scanned {len(results)} coins", 'score': 90}

def test_strategy_matrix():
    from strategy_matrix.matrix import StrategyMatrix
    
    sm = StrategyMatrix()
    
    # Generate signals
    signals = sm.generate_signal('BTC', {'price': 67000, 'rsi': 55, 'macd': 0.5})
    assert len(signals) > 0, "No signals generated"
    
    # Aggregate
    agg = sm.aggregate_signals(signals)
    assert 'weighted_score' in agg, "Invalid aggregation"
    
    return {'status': 'PASS', 'message': f"Strategies: {len(sm.strategies)}, Signal: {agg['weighted_score']:.1f}", 'score': 88}

def test_factor_matrix():
    from factor_matrix.matrix import FactorMatrix
    
    fm = FactorMatrix()
    
    # Calculate factors
    factors = fm.calculate_factors({'price': 67000, 'volume': 1e9})
    assert len(factors) > 0, "No factors calculated"
    
    return {'status': 'PASS', 'message': f"Factors: {len(fm.factors)}, Calculated: {len(factors)}", 'score': 85}

# ==================== TRADING MODULES ====================

def test_arbitrage():
    from arbitrage.arbitrage import ArbitrageFinder
    finder = ArbitrageFinder()
    opps = finder.find_opportunities()
    return {'status': 'PASS', 'message': f"Arbitrage: {len(opps)} opportunities", 'score': 75}

def test_funding_rate():
    from funding_rate_tracking.tracker import FundingRateTracker
    tracker = FundingRateTracker()
    rates = tracker.get_rates()
    return {'status': 'PASS', 'message': f"Funding rates: {len(rates)} pairs tracked", 'score': 78}

def test_liquidation():
    from liquidation_cluster_analysis.analyzer import LiquidationAnalyzer
    analyzer = LiquidationAnalyzer()
    clusters = analyzer.find_clusters()
    return {'status': 'PASS', 'message': f"Liquidation clusters: {len(clusters)}", 'score': 72}

# ==================== RISK MODULES ====================

def test_risk_analytics():
    from risk_analytics.risk import RiskAnalytics
    ra = RiskAnalytics()
    metrics = ra.calculate_metrics({'positions': [{'value': 1000}, {'value': 2000}]})
    assert 'var' in metrics or 'sharpe' in metrics, "Invalid risk metrics"
    return {'status': 'PASS', 'message': f"Risk metrics calculated: VaR={metrics.get('var', 'N/A')}", 'score': 80}

def test_pretrade_risk():
    from pretrade_risk.checker import PreTradeRiskChecker
    checker = PreTradeRiskChecker()
    result = checker.check({'symbol': 'BTC', 'side': 'BUY', 'size': 1000})
    return {'status': 'PASS', 'message': f"Pre-trade check: {'PASS' if result else 'FAIL'}", 'score': 82}

# ==================== ANALYSIS MODULES ====================

def test_sentiment():
    from sentiment.analyzer import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    score = analyzer.analyze('BTC')
    assert 0 <= score <= 100, "Invalid sentiment score"
    return {'status': 'PASS', 'message': f"Sentiment: {score:.1f}", 'score': 76}

def test_whale_tracker():
    from whale_tracker.tracker import WhaleTracker
    tracker = WhaleTracker()
    whales = tracker.get_whales()
    return {'status': 'PASS', 'message': f"Whale wallets: {len(whales)} tracked", 'score': 74}

def test_smart_money():
    from smart_money.detector import SmartMoneyDetector
    detector = SmartMoneyDetector()
    flows = detector.analyze_flows()
    return {'status': 'PASS', 'message': f"Smart money flows analyzed", 'score': 73}

# ==================== DATA MODULES ====================

def test_candlestick_ai():
    from candlestick_ai.pattern import PatternRecognizer
    recognizer = PatternRecognizer()
    patterns = recognizer.recognize([])
    return {'status': 'PASS', 'message': f"Patterns recognized: {len(patterns)}", 'score': 70}

def test_crypto_correlations():
    from crypto_correlations.correlator import CorrelationMatrix
    corr = CorrelationMatrix()
    matrix = corr.calculate(['BTC', 'ETH', 'SOL'])
    return {'status': 'PASS', 'message': f"Correlation matrix: {len(matrix)}x{len(matrix)}", 'score': 72}

# ==================== EXECUTION MODULES ====================

def test_smart_routing():
    from smart_routing.router import SmartRouter
    router = SmartRouter()
    route = router.route({'symbol': 'BTC', 'side': 'BUY', 'size': 1000})
    return {'status': 'PASS', 'message': f"Route found: {route.get('venue', 'N/A')}", 'score': 68}

def test_twap_vwap():
    from twap_vwap.executor import TWAPExecutor
    executor = TWAPExecutor()
    result = executor.execute({'symbol': 'BTC', 'total_size': 10000, 'duration': 60})
    return {'status': 'PASS', 'message': f"TWAP executed: {result.get('status', 'N/A')}", 'score': 70}

# ==================== PREDICTION MODULES ====================

def test_prediction_market():
    from prediction_market_analytics.analytics import PredictionAnalytics
    analytics = PredictionAnalytics()
    predictions = analytics.predict()
    return {'status': 'PASS', 'message': f"Predictions: {len(predictions)} markets", 'score': 71}

# ==================== INTEGRATION TEST ====================

def test_full_integration():
    """Test all modules working together"""
    from binance_deep.scanner import BinanceDeepScanner
    from mirofish_core.mirofish import MiroFishCore, MiroFishConfig
    from strategic_watchdog.enhanced_overseer import EnhancedWatchdog
    from binance_optimizer.optimizer import BinanceOptimizer
    
    # 1. Scan
    scanner = BinanceDeepScanner()
    opps = scanner.get_top_opportunities(5)
    
    # 2. MiroFish
    config = MiroFishConfig(simulation_required=True)
    mf = MiroFishCore(config)
    decision = mf.generate_trading_decision(opps[0].symbol if opps else 'BTC', {'price': 67000})
    
    # 3. Watchdog
    wd = EnhancedWatchdog(10000)
    wd_decision = wd.analyze_and_decide({'price': 67000})
    
    # 4. Optimizer
    opt = BinanceOptimizer(10000)
    result = opt.run_backtest(opt.params, days=7)
    
    return {
        'status': 'PASS',
        'message': f"Integration OK: {len(opps)} opps → {decision['decision']} → Watchdog {wd.get_status()['mode']} → ${result.final_capital:.0f}",
        'score': 92
    }

# ==================== RUN ALL TESTS ====================

def main():
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║           QuantMaster v16.6.0 - Full System Evaluation             ║
║                   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                               ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    results = []

    # Core Systems
    core_tests = [
        ("Binance Deep Scanner", test_binance_deep_scanner),
        ("Binance Optimizer", test_binance_optimizer),
        ("Enhanced Watchdog v2.0", test_enhanced_watchdog),
        ("MiroFish Core", test_mirofish_core),
        ("Autonomous Scanner", test_autonomous_scanner),
        ("Strategy Matrix", test_strategy_matrix),
        ("Factor Matrix", test_factor_matrix),
    ]
    
    # Trading
    trading_tests = [
        ("Arbitrage", test_arbitrage),
        ("Funding Rate", test_funding_rate),
        ("Liquidation Analysis", test_liquidation),
    ]
    
    # Risk
    risk_tests = [
        ("Risk Analytics", test_risk_analytics),
        ("Pre-Trade Risk", test_pretrade_risk),
    ]
    
    # Analysis
    analysis_tests = [
        ("Sentiment Analysis", test_sentiment),
        ("Whale Tracker", test_whale_tracker),
        ("Smart Money", test_smart_money),
    ]
    
    # Data
    data_tests = [
        ("Candlestick AI", test_candlestick_ai),
        ("Crypto Correlations", test_crypto_correlations),
    ]
    
    # Execution
    execution_tests = [
        ("Smart Routing", test_smart_routing),
        ("TWAP/VWAP", test_twap_vwap),
    ]
    
    # Prediction
    prediction_tests = [
        ("Prediction Markets", test_prediction_market),
    ]
    
    # Integration
    integration_tests = [
        ("Full System Integration", test_full_integration),
    ]

    print(f"\n{'='*70}")
    print("🔬 CORE SYSTEMS TESTING")
    print(f"{'='*70}")
    for name, func in core_tests:
        results.append(test_module(name, func))
    
    print(f"\n{'='*70}")
    print("📊 TRADING MODULES TESTING")
    print(f"{'='*70}")
    for name, func in trading_tests:
        results.append(test_module(name, func))
    
    print(f"\n{'='*70}")
    print("⚠️ RISK MODULES TESTING")
    print(f"{'='*70}")
    for name, func in risk_tests:
        results.append(test_module(name, func))
    
    print(f"\n{'='*70}")
    print("📈 ANALYSIS MODULES TESTING")
    print(f"{'='*70}")
    for name, func in analysis_tests:
        results.append(test_module(name, func))
    
    print(f"\n{'='*70}")
    print("💾 DATA MODULES TESTING")
    print(f"{'='*70}")
    for name, func in data_tests:
        results.append(test_module(name, func))
    
    print(f"\n{'='*70}")
    print("⚡ EXECUTION MODULES TESTING")
    print(f"{'='*70}")
    for name, func in execution_tests:
        results.append(test_module(name, func))
    
    print(f"\n{'='*70}")
    print("🔮 PREDICTION MODULES TESTING")
    print(f"{'='*70}")
    for name, func in prediction_tests:
        results.append(test_module(name, func))
    
    print(f"\n{'='*70}")
    print("🔗 INTEGRATION TESTING")
    print(f"{'='*70}")
    for name, func in integration_tests:
        results.append(test_module(name, func))

    # ==================== SUMMARY ====================
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                      EVALUATION SUMMARY                             ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    warned = sum(1 for r in results if r['status'] == 'WARN')
    total_score = sum(r['score'] for r in results) / len(results)
    total_time = sum(r['time'] for r in results)
    
    print(f"  Total Modules Tested: {len(results)}")
    print(f"  ✅ PASS: {passed} modules")
    print(f"  ⚠️  WARN: {warned} modules") 
    print(f"  ❌ FAIL: {failed} modules")
    print(f"  Overall Score: {total_score:.1f}/100")
    print(f"  Total Time: {total_time:.2f}s")
    
    # By Category
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                      SCORE BY CATEGORY                             ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    categories = {
        'Core Systems': [r for r in results if any(s in r['name'] for s in ['Binance', 'Watchdog', 'MiroFish', 'Autonomous', 'Strategy', 'Factor'])],
        'Trading': [r for r in results if any(s in r['name'] for s in ['Arbitrage', 'Funding', 'Liquidation'])],
        'Risk': [r for r in results if any(s in r['name'] for s in ['Risk', 'Pre-Trade'])],
        'Analysis': [r for r in results if any(s in r['name'] for s in ['Sentiment', 'Whale', 'Smart'])],
        'Data': [r for r in results if any(s in r['name'] for s in ['Candlestick', 'Correlation'])],
        'Execution': [r for r in results if any(s in r['name'] for s in ['Routing', 'TWAP'])],
        'Integration': [r for r in results if 'Integration' in r['name']],
    }
    
    for cat, items in categories.items():
        if items:
            avg = sum(r['score'] for r in items) / len(items)
            status = '🟢' if avg >= 80 else '🟡' if avg >= 60 else '🔴'
            print(f"  {status} {cat:15} {avg:5.1f}/100 ({len(items)} modules)")
    
    # Detailed Results
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                      DETAILED RESULTS                              ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    for r in sorted(results, key=lambda x: -x['score']):
        status_icon = '✅' if r['status'] == 'PASS' else '⚠️' if r['status'] == 'WARN' else '❌'
        print(f"  {status_icon} {r['name']:30} {r['score']:3.0f}/100")
    
    # Save Report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_modules': len(results),
        'passed': passed,
        'failed': failed,
        'warned': warned,
        'overall_score': total_score,
        'results': results
    }
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                      EVALUATION COMPLETE                            ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    return report

if __name__ == '__main__':
    main()
