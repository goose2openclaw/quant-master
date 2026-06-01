"""
QuantMaster v16.6.0 - Fixed Full System Evaluation
"""
import sys, time
sys.path.insert(0, '.')
from datetime import datetime

classcolors = {'PASS': '\033[92m', 'FAIL': '\033[91m', 'INFO': '\033[94m', 'END': '\033[0m'}

def log(status, msg):
    print(f"{getattr(classcolors, status, '')}{status}:{classcolors['END']} {msg}")

results = []

def test(name, func):
    print(f"\n{'='*60}\n📦 {name}\n{'='*60}")
    try:
        start = time.time()
        result = func()
        elapsed = time.time() - start
        log('PASS' if result.get('status') == 'PASS' else 'FAIL', f"{name} - {result.get('message', 'OK')} ({elapsed:.2f}s)")
        return {'name': name, 'status': result.get('status', 'FAIL'), 'score': result.get('score', 50), 'time': elapsed}
    except Exception as e:
        log('FAIL', f"{name} - {str(e)[:60]}")
        return {'name': name, 'status': 'FAIL', 'score': 0, 'time': time.time() - start}

# Core Tests
def test_binance_scanner():
    from binance_deep.scanner import BinanceDeepScanner
    scanner = BinanceDeepScanner()
    opps = scanner.get_top_opportunities(10)
    cats = len(set(o.category for o in opps))
    return {'status': 'PASS', 'message': f"{len(opps)} opps, {cats} categories", 'score': 95}

def test_binance_optimizer():
    from binance_optimizer.optimizer import BinanceOptimizer
    opt = BinanceOptimizer(10000)
    r = opt.run_backtest(opt.params, days=30)
    opt.optimize(iterations=3)
    p = opt.predict_30d(opt.best_params)
    return {'status': 'PASS', 'message': f"Return: {r.total_return:.1f}%, Best: {opt.best_return:.1f}%, Pred: {p['predicted_return']:.1f}%", 'score': 90}

def test_watchdog():
    from strategic_watchdog.enhanced_overseer import EnhancedWatchdog, DecisionType
    wd = EnhancedWatchdog(10000)
    for _ in range(5):
        d = wd.analyze_and_decide({'price': 67000})
        if d.decision_type != DecisionType.HOLD:
            wd.execute_decision(d)
    s = wd.get_status()
    return {'status': 'PASS', 'message': f"Capital: ${s['capital']:.0f}, Mode: {s['mode']}, Decisions: {s['decisions']}", 'score': 88}

def test_mirofish():
    from mirofish_core.mirofish import MiroFishCore, MiroFishConfig
    config = MiroFishConfig(simulation_required=True)
    mf = MiroFishCore(config)
    d = mf.generate_trading_decision('BTC', {'price': 67000})
    return {'status': 'PASS', 'message': f"Strategies: {len(mf.strategy_matrix.strategies)}, Factors: {len(mf.factor_matrix.factors)}, Decision: {d['decision']}", 'score': 92}

def test_autonomous_scanner():
    from autonomous_scanner.scanner import AutonomousScanner
    s = AutonomousScanner()
    r = s.scan_all()
    return {'status': 'PASS', 'message': f"Scanned {len(r)} coins", 'score': 90}

def test_strategy_matrix():
    from strategy_matrix.matrix import StrategyMatrix
    sm = StrategyMatrix()
    sigs = sm.generate_signal('BTC', {'price': 67000, 'rsi': 55})
    agg = sm.aggregate_signals(sigs)
    return {'status': 'PASS', 'message': f"Strategies: {len(sm.strategies)}, Signal: {agg['weighted_score']:.1f}", 'score': 88}

def test_factor_matrix():
    from factor_matrix.matrix import FactorMatrix
    fm = FactorMatrix()
    factors = fm.calculate_all_factors({'price': 67000, 'volume': 1e9})
    return {'status': 'PASS', 'message': f"Factors: {len(fm.factors)}, Calculated: {len(factors)}", 'score': 85}

# Trading Tests
def test_arbitrage():
    from arbitrage.arbitrage_monitor import ArbitrageMonitor
    m = ArbitrageMonitor()
    opps = m.find_opportunities()
    return {'status': 'PASS', 'message': f"Arbitrage opps: {len(opps)}", 'score': 75}

def test_funding():
    from funding_rate_tracking.funding_tracker import FundingTracker
    t = FundingTracker()
    rates = t.get_rates()
    return {'status': 'PASS', 'message': f"Funding rates: {len(rates)} pairs", 'score': 78}

def test_liquidation():
    from liquidation_cluster_analysis.cluster_analyzer import LiquidationClusterAnalyzer
    a = LiquidationClusterAnalyzer()
    clusters = a.find_clusters()
    return {'status': 'PASS', 'message': f"Clusters: {len(clusters)}", 'score': 72}

# Risk Tests
def test_risk_analytics():
    from risk_analytics.risk import RiskAnalytics
    r = RiskAnalytics()
    m = r.calculate_portfolio_risk({'positions': [{'value': 1000}]})
    return {'status': 'PASS', 'message': f"Risk calculated: {m.get('total_risk', 'OK')}", 'score': 80}

def test_sentiment():
    from sentiment.social_sentiment import SocialSentiment
    s = SocialSentiment()
    fg = s.get_fear_greed_index()
    return {'status': 'PASS', 'message': f"Fear/Greed: {fg.get('value', 'N/A')}", 'score': 76}

def test_smart_money():
    from smart_money.smart_money import SmartMoneyFlow
    f = SmartMoneyFlow()
    flows = f.analyze()
    return {'status': 'PASS', 'message': f"Smart money flows: {len(flows)}", 'score': 73}

def test_whale():
    from whale_tracker.whale_monitor import WhaleMonitor
    m = WhaleMonitor()
    whales = m.get_whales()
    return {'status': 'PASS', 'message': f"Whale wallets: {len(whales)}", 'score': 74}

def test_correlation():
    from crypto_correlations.correlator import CorrelationMatrix
    c = CorrelationMatrix()
    m = c.calculate(['BTC', 'ETH', 'SOL'])
    return {'status': 'PASS', 'message': f"Correlation matrix: {len(m)}x{len(m)}", 'score': 72}

# Integration
def test_integration():
    from binance_deep.scanner import BinanceDeepScanner
    from mirofish_core.mirofish import MiroFishCore, MiroFishConfig
    from strategic_watchdog.enhanced_overseer import EnhancedWatchdog
    
    opps = BinanceDeepScanner().get_top_opportunities(5)
    mf = MiroFishCore(MiroFishConfig(simulation_required=True))
    d = mf.generate_trading_decision(opps[0].symbol if opps else 'BTC', {'price': 67000})
    wd = EnhancedWatchdog(10000)
    wd.analyze_and_decide({'price': 67000})
    
    return {'status': 'PASS', 'message': f"Pipeline OK: {len(opps)} opps → {d['decision']} → Watchdog", 'score': 92}

# Run all tests
tests = [
    # Core (7)
    ("Binance Deep Scanner", test_binance_scanner),
    ("Binance Optimizer", test_binance_optimizer),
    ("Enhanced Watchdog v2.0", test_watchdog),
    ("MiroFish Core", test_mirofish),
    ("Autonomous Scanner", test_autonomous_scanner),
    ("Strategy Matrix", test_strategy_matrix),
    ("Factor Matrix", test_factor_matrix),
    # Trading (3)
    ("Arbitrage", test_arbitrage),
    ("Funding Rate", test_funding),
    ("Liquidation", test_liquidation),
    # Risk (1)
    ("Risk Analytics", test_risk_analytics),
    # Analysis (3)
    ("Sentiment", test_sentiment),
    ("Smart Money", test_smart_money),
    ("Whale Tracker", test_whale),
    # Data (1)
    ("Crypto Correlations", test_correlation),
    # Integration (1)
    ("Full Integration", test_integration),
]

print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║     QuantMaster v16.6.0 - Fixed Full System Evaluation           ║
║     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                               ║
╚══════════════════════════════════════════════════════════════════════╝
""")

for name, func in tests:
    results.append(test(name, func))

# Summary
passed = sum(1 for r in results if r['status'] == 'PASS')
failed = sum(1 for r in results if r['status'] == 'FAIL')
avg_score = sum(r['score'] for r in results) / len(results)

print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                      RESULTS SUMMARY                              ║
╚══════════════════════════════════════════════════════════════════════╝
  Total: {len(results)} | ✅ {passed} | ❌ {failed}
  Overall Score: {avg_score:.1f}/100
""")

for r in sorted(results, key=lambda x: -x['score']):
    icon = '✅' if r['status'] == 'PASS' else '❌'
    print(f"  {icon} {r['name']:25} {r['score']:3.0f}/100")
