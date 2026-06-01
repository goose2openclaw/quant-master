"""
QuantMaster Autonomous Scanner v8.3
全域扫描 → 主动侦测 → 自主决策 → 自动执行
"""
import sys, time, json, asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

# Import all analysis modules
from funding_rate_tracking.funding_tracker import FundingRateTracker
from open_interest.oi_tracker import OpenInterestTracker
from liquidations.liquidation_tracker import LiquidationTracker
from whale_tracker.whale_monitor import WhaleTracker
from crypto_fear_greed.fear_greed_index import FearGreedIndex
from volatility_surface.vol_surface import VolatilitySurface
from options_skew.skew_analyzer import OptionsSkewAnalyzer
from crypto_correlations.correlation_matrix import CorrelationMatrix
from perp_funding_forecast.funding_forecast import PerpFundingForecaster
from perp_oi_gradient.oi_gradient import PerpOIGradient
from liquidation_cluster_analysis.cluster_analyzer import LiquidationClusterAnalyzer
from options_flow.flow_analyzer import OptionsFlowAnalyzer
from dex_cex_arb.dex_cex_arb import DEXCEXArbitrage
from stablecoin_flow.stablecoin_analyzer import StablecoinFlowAnalyzer

@dataclass
class CoinAnalysis:
    symbol: str
    price: float
    change_24h: float
    
    # Signal scores (0-100)
    funding_score: float
    oi_score: float
    liquidation_score: float
    whale_score: float
    vol_score: float
    skew_score: float
    momentum_score: float
    
    # Combined scores
    total_score: float
    signal: str
    confidence: float
    
    # Decision
    action: str
    reason: str
    
    # Metadata
    timestamp: float
    scan_duration_ms: float

class AutonomousScanner:
    """
    自主扫描引擎
    扫描 → 分析 → 决策 → 执行
    """
    
    def __init__(self):
        self.name = "QuantMaster Autonomous Scanner v8.3"
        self.running = False
        
        # Initialize all analyzer modules
        self.analyzers = {
            'funding': FundingRateTracker(),
            'oi': OpenInterestTracker(),
            'liquidations': LiquidationTracker(),
            'whale': WhaleTracker(),
            'fear_greed': FearGreedIndex(),
            'vol': VolatilitySurface(),
            'skew': OptionsSkewAnalyzer(),
            'corr': CorrelationMatrix(),
            'perp_fund': PerpFundingForecaster(),
            'perp_oi': PerpOIGradient(),
            'liq_cluster': LiquidationClusterAnalyzer(),
            'options_flow': OptionsFlowAnalyzer(),
            'arb': DEXCEXArbitrage(),
            'stablecoin': StablecoinFlowAnalyzer(),
        }
        
        # Scan targets (major coins)
        self.targets = [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 
            'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI', 'ATOM', 
            'LTC', 'ETC', 'FIL', 'APT', 'ARB', 'OP', 'NEAR'
        ]
        
        # Decision thresholds
        self.buy_threshold = 70
        self.sell_threshold = 30
        
        # History
        self.scan_history = []
        self.trade_history = []
        
        # Execution callback
        self.execute_callback = None
        
        print(f"✅ {self.name} initialized")
        print(f"   Targets: {len(self.targets)} coins")
        print(f"   Analyzers: {len(self.analyzers)} modules")
    
    # =========================================================================
    # CORE SCANNING
    # =========================================================================
    
    def scan_all(self) -> List[CoinAnalysis]:
        """扫描所有目标币种"""
        start = time.time()
        results = []
        
        print(f"\n{'='*60}")
        print(f"🔍 SCANNING {len(self.targets)} COINS AT {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        for symbol in self.targets:
            analysis = self.analyze_symbol(symbol)
            results.append(analysis)
            
            # Print progress
            signal_emoji = '🟢' if analysis.signal == 'BUY' else '🔴' if analysis.signal == 'SELL' else '⚪'
            print(f"  {signal_emoji} {symbol:6} | Score: {analysis.total_score:5.1f} | Signal: {analysis.signal:4} | {analysis.action}")
        
        duration = (time.time() - start) * 1000
        
        # Sort by score
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        print(f"\n⏱ Scan completed in {duration:.0f}ms")
        print(f"{'='*60}")
        
        self.scan_history.append({
            'timestamp': time.time(),
            'results': results,
            'duration_ms': duration
        })
        
        return results
    
    def analyze_symbol(self, symbol: str) -> CoinAnalysis:
        """深度分析单个币种"""
        t0 = time.time()
        
        # Simulated price data (would normally fetch from API)
        price = self._get_price(symbol)
        change_24h = self._get_change(symbol)
        
        # Gather signals from all modules
        signals = {}
        
        try:
            # 1. Funding Rate
            rates = self.analyzers['funding'].fetch_funding_rates()
            funding_rate = rates.get(f'{symbol}USDT', 0)
            signals['funding'] = self._score_funding(funding_rate)
        except: signals['funding'] = 50
        
        try:
            # 2. Open Interest
            oi_data = self.analyzers['oi'].fetch_oi(symbol)
            signals['oi'] = self._score_oi(oi_data)
        except: signals['oi'] = 50
        
        try:
            # 3. Liquidations
            liq_data = self.analyzers['liquidations'].detect_squeeze(symbol)
            signals['liquidations'] = self._score_liquidation(liq_data)
        except: signals['liquidations'] = 50
        
        try:
            # 4. Whale Activity
            whale_data = self.analyzers['whale'].get_whale_sentiment(symbol)
            signals['whale'] = self._score_whale(whale_data)
        except: signals['whale'] = 50
        
        try:
            # 5. Volatility
            vol_data = self.analyzers['vol'].build_smile(symbol, '1M')
            signals['vol'] = self._score_volatility(vol_data)
        except: signals['vol'] = 50
        
        try:
            # 6. Options Skew
            skew_data = self.analyzers['skew'].calculate_skew_metrics(symbol, '1M')
            signals['skew'] = self._score_skew(skew_data)
        except: signals['skew'] = 50
        
        # 7. Momentum (price based)
        signals['momentum'] = self._score_momentum(change_24h)
        
        # Calculate total score (weighted average)
        weights = {
            'funding': 0.15,
            'oi': 0.15,
            'liquidations': 0.15,
            'whale': 0.20,
            'vol': 0.10,
            'skew': 0.10,
            'momentum': 0.15
        }
        
        total_score = sum(signals[k] * weights[k] for k in weights)
        
        # Determine signal
        if total_score >= self.buy_threshold:
            signal = 'BUY'
        elif total_score <= self.sell_threshold:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        # Determine action
        action, reason = self._determine_action(symbol, signals, total_score, signal)
        
        scan_duration = (time.time() - t0) * 1000
        
        return CoinAnalysis(
            symbol=symbol,
            price=price,
            change_24h=change_24h,
            funding_score=signals['funding'],
            oi_score=signals['oi'],
            liquidation_score=signals['liquidations'],
            whale_score=signals['whale'],
            vol_score=signals['vol'],
            skew_score=signals['skew'],
            momentum_score=signals['momentum'],
            total_score=total_score,
            signal=signal,
            confidence=abs(total_score - 50) / 50,
            action=action,
            reason=reason,
            timestamp=time.time(),
            scan_duration_ms=scan_duration
        )
    
    # =========================================================================
    # SIGNAL SCORING (0-100, 50=neutral)
    # =========================================================================
    
    def _score_funding(self, rate: float) -> float:
        """资金费率评分"""
        # Negative funding = good for longs (higher score)
        # Positive funding = good for shorts (lower score)
        score = 50 - rate * 10000  # Rate in %, e.g., 0.01% = 100
        return max(0, min(100, 50 + score))
    
    def _score_oi(self, oi_data: Dict) -> float:
        """OI评分"""
        change = oi_data.get('change_24h_pct', 0)
        # Increasing OI = more interest = positive
        score = 50 + change * 5
        return max(0, min(100, score))
    
    def _score_liquidation(self, liq_data: Dict) -> float:
        """强平评分"""
        squeeze_score = liq_data.get('squeeze_score', 0)
        # High squeeze = potential move = higher score
        score = 50 + squeeze_score * 30
        return max(0, min(100, score))
    
    def _score_whale(self, whale_data: Dict) -> float:
        """鲸鱼评分"""
        sentiment = whale_data.get('sentiment', 'NEUTRAL')
        if sentiment == 'BULLISH': return 80
        if sentiment == 'BEARISH': return 20
        return 50
    
    def _score_volatility(self, vol_data: Dict) -> float:
        """波动率评分"""
        atm_vol = vol_data.get('atm_vol', 0.5)
        # Low vol = potential breakout setup
        if atm_vol < 0.4: return 70
        if atm_vol > 0.8: return 30
        return 50
    
    def _score_skew(self, skew_data: Dict) -> float:
        """Skew评分"""
        rr = skew_data.get('rr_25d', 0)
        # Negative RR (more put skew) = bullish signal
        score = 50 - rr * 500
        return max(0, min(100, score))
    
    def _score_momentum(self, change_24h: float) -> float:
        """动量评分"""
        score = 50 + change_24h * 5
        return max(0, min(100, score))
    
    # =========================================================================
    # DECISION ENGINE
    # =========================================================================
    
    def _determine_action(self, symbol: str, signals: Dict, 
                         total_score: float, signal: str) -> tuple:
        """决定行动"""
        reasons = []
        
        if signal == 'BUY':
            if signals['whale'] > 70:
                reasons.append("鲸鱼看涨")
            if signals['funding'] > 60:
                reasons.append("资金费率有利")
            if signals['momentum'] > 60:
                reasons.append("动量强劲")
            if signals['liquidations'] > 65:
                reasons.append("强平挤压信号")
            return 'LONG', '; '.join(reasons) if reasons else '综合看涨'
        
        elif signal == 'SELL':
            if signals['whale'] < 30:
                reasons.append("鲸鱼看跌")
            if signals['funding'] < 40:
                reasons.append("资金费率不利")
            if signals['momentum'] < 40:
                reasons.append("动量疲弱")
            return 'SHORT', '; '.join(reasons) if reasons else '综合看跌'
        
        else:
            return 'WATCH', '信号不明朗,等待确认'
    
    # =========================================================================
    # AUTONOMOUS EXECUTION
    # =========================================================================
    
    def execute_decisions(self, results: List[CoinAnalysis]) -> List[Dict]:
        """自动执行决策"""
        if not self.execute_callback:
            print("⚠ No execution callback set")
            return []
        
        executed = []
        
        # Get top BUY and SELL signals
        buys = [r for r in results if r.action in ['LONG'] and r.confidence > 0.6]
        sells = [r for r in results if r.action in ['SHORT'] and r.confidence > 0.6]
        
        # Execute top opportunities
        for buy in buys[:2]:  # Max 2 longs
            try:
                result = self.execute_callback('BUY', buy.symbol, buy.total_score)
                executed.append({
                    'action': 'BUY',
                    'symbol': buy.symbol,
                    'score': buy.total_score,
                    'confidence': buy.confidence,
                    'reason': buy.reason,
                    'result': result
                })
                print(f"  ✅ EXECUTED BUY {buy.symbol} @ score {buy.total_score:.1f}")
            except Exception as e:
                print(f"  ❌ BUY {buy.symbol} failed: {e}")
        
        for sell in sells[:2]:  # Max 2 shorts
            try:
                result = self.execute_callback('SELL', sell.symbol, sell.total_score)
                executed.append({
                    'action': 'SELL',
                    'symbol': sell.symbol,
                    'score': sell.total_score,
                    'confidence': sell.confidence,
                    'reason': sell.reason,
                    'result': result
                })
                print(f"  ✅ EXECUTED SELL {sell.symbol} @ score {sell.total_score:.1f}")
            except Exception as e:
                print(f"  ❌ SELL {sell.symbol} failed: {e}")
        
        self.trade_history.extend(executed)
        return executed
    
    # =========================================================================
    # DATA PROVIDERS (simulated, replace with real API)
    # =========================================================================
    
    def _get_price(self, symbol: str) -> float:
        """获取价格"""
        prices = {
            'BTC': 67000, 'ETH': 3500, 'BNB': 580, 'SOL': 145,
            'XRP': 0.52, 'ADA': 0.45, 'DOGE': 0.12, 'AVAX': 35,
            'DOT': 7.2, 'LINK': 14.5, 'MATIC': 0.72, 'UNI': 9.5,
            'ATOM': 8.8, 'LTC': 85, 'ETC': 26, 'FIL': 5.8,
            'APT': 8.2, 'ARB': 1.05, 'OP': 2.1, 'NEAR': 5.8
        }
        return prices.get(symbol, 100)
    
    def _get_change(self, symbol: str) -> float:
        """获取24h变化"""
        import random
        return random.uniform(-8, 8)
    
    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    
    def run_autonomous(self, interval_seconds: int = 60):
        """自主运行主循环"""
        self.running = True
        print(f"\n🚀 {self.name} STARTING AUTONOMOUS MODE")
        print(f"   Scan interval: {interval_seconds}s")
        print(f"   Targets: {', '.join(self.targets[:5])}...")
        
        cycle = 0
        while self.running:
            cycle += 1
            print(f"\n{'#'*60}")
            print(f"# AUTONOMOUS CYCLE {cycle} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'#'*60}")
            
            try:
                # 1. Scan all
                results = self.scan_all()
                
                # 2. Show top opportunities
                print(f"\n📊 TOP OPPORTUNITIES:")
                for r in results[:5]:
                    print(f"   {r.symbol:6} | Score: {r.total_score:5.1f} | {r.signal:4} | {r.action}")
                
                # 3. Execute decisions
                print(f"\n⚡ EXECUTING DECISIONS:")
                self.execute_decisions(results)
                
            except Exception as e:
                print(f"❌ Cycle error: {e}")
            
            # Wait for next cycle
            print(f"\n⏳ Next scan in {interval_seconds}s (Ctrl+C to stop)...")
            time.sleep(interval_seconds)

# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == '__main__':
    scanner = AutonomousScanner()
    
    # Single scan test
    print("\n" + "="*60)
    print("SINGLE SCAN TEST")
    print("="*60)
    
    results = scanner.scan_all()
    
    # Show summary
    print("\n📊 SCAN RESULTS SUMMARY:")
    print(f"{'Symbol':<8} {'Price':<12} {'Change':<10} {'Score':<8} {'Signal':<8} {'Action'}")
    print("-" * 60)
    
    for r in results:
        change_str = f"{r.change_24h:+.2f}%"
        print(f"{r.symbol:<8} ${r.price:<11,.0f} {change_str:<10} {r.total_score:<8.1f} {r.signal:<8} {r.action}")
    
    # Top opportunity
    top = results[0]
    print(f"\n🏆 TOP OPPORTUNITY: {top.symbol}")
    print(f"   Score: {top.total_score:.1f}")
    print(f"   Signal: {top.signal}")
    print(f"   Action: {top.action}")
    print(f"   Reason: {top.reason}")
