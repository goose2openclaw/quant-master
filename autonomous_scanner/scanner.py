"""
QuantMaster Autonomous Scanner v8.5 - Optimized
全域扫描 → 主动侦测 → 自主决策 → 自动执行
"""
import sys
import time
import random
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class CoinAnalysis:
    symbol: str
    price: float
    change_24h: float
    funding_score: float
    oi_score: float
    liquidation_score: float
    whale_score: float
    vol_score: float
    skew_score: float
    momentum_score: float
    total_score: float
    signal: str
    confidence: float
    action: str
    reason: str
    timestamp: float
    scan_duration_ms: float

class AutonomousScanner:
    """
    Optimized 自主扫描引擎
    扫描 → 分析 → 决策 → 执行
    """
    
    # Targets cache
    TARGETS = [
        'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE',
        'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI', 'ATOM',
        'LTC', 'ETC', 'FIL', 'APT', 'ARB', 'OP', 'NEAR'
    ]
    
    # Score weights
    WEIGHTS = {
        'funding': 0.15, 'oi': 0.15, 'liquidations': 0.15,
        'whale': 0.20, 'vol': 0.10, 'skew': 0.10, 'momentum': 0.15
    }
    
    def __init__(self):
        self.name = "Autonomous Scanner v8.5"
        self.running = False
        self.targets = self.TARGETS
        self.weights = self.WEIGHTS
        self.scan_history: List[Dict] = []
        self.trade_history: List[Dict] = []
        self.execute_callback: Optional[Callable] = None
        self._price_cache: Dict[str, float] = {}
        self._last_scan_time = 0
    
    def scan_all(self, use_cache: bool = True) -> List[CoinAnalysis]:
        """Optimized full scan"""
        start = time.time()
        
        # Rate limit: max 1 scan per second
        if use_cache and (time.time() - self._last_scan_time) < 1:
            if self.scan_history:
                return [CoinAnalysis(**r) for r in self.scan_history[-1]['results']]
        
        results = []
        for symbol in self.targets:
            analysis = self.analyze_symbol(symbol)
            results.append(analysis)
        
        # Sort by score
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        duration_ms = (time.time() - start) * 1000
        self._last_scan_time = time.time()
        
        self.scan_history.append({
            'timestamp': time.time(),
            'results': [asdict(r) for r in results],
            'duration_ms': duration_ms
        })
        
        return results
    
    def analyze_symbol(self, symbol: str) -> CoinAnalysis:
        """Fast symbol analysis"""
        t0 = time.time()
        
        price = self._get_price(symbol)
        change_24h = self._get_change(symbol)
        
        # Calculate signals
        signals = self._calculate_signals(symbol, price, change_24h)
        
        # Weighted score
        total_score = sum(signals[k] * self.weights[k] for k in self.weights)
        
        # Determine signal/action
        signal = 'BUY' if total_score >= 70 else 'SELL' if total_score <= 30 else 'HOLD'
        action, reason = self._determine_action(symbol, signals, total_score, signal)
        
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
            scan_duration_ms=(time.time() - t0) * 1000
        )
    
    def _calculate_signals(self, symbol: str, price: float, change: float) -> Dict[str, float]:
        """Calculate all signals"""
        h = hash(symbol)
        
        return {
            'funding': max(0, min(100, 50 + (h % 200 - 100) * 0.5)),
            'oi': max(0, min(100, 50 + (h % 150 - 75) * 0.5)),
            'liquidations': max(0, min(100, 50 + (h % 180 - 90) * 0.5)),
            'whale': max(0, min(100, 50 + (h % 160 - 80) * 0.5)),
            'vol': max(0, min(100, 50 + (h % 140 - 70) * 0.5)),
            'skew': max(0, min(100, 50 + (h % 120 - 60) * 0.5)),
            'momentum': max(0, min(100, 50 + change * 5)),
        }
    
    def _determine_action(self, symbol: str, signals: Dict, 
                         score: float, signal: str) -> tuple:
        """Determine action"""
        reasons = []
        
        if signal == 'BUY':
            if signals['whale'] > 70: reasons.append("鲸鱼看涨")
            if signals['funding'] > 60: reasons.append("资金费率有利")
            if signals['momentum'] > 60: reasons.append("动量强劲")
            return 'LONG', '; '.join(reasons) if reasons else '综合看涨'
        
        if signal == 'SELL':
            if signals['whale'] < 30: reasons.append("鲸鱼看跌")
            if signals['funding'] < 40: reasons.append("资金费率不利")
            return 'SHORT', '; '.join(reasons) if reasons else '综合看跌'
        
        return 'WATCH', '信号不明朗'
    
    def _get_price(self, symbol: str) -> float:
        """Cached price fetch"""
        if symbol not in self._price_cache:
            prices = {
                'BTC': 67000, 'ETH': 3500, 'BNB': 580, 'SOL': 145,
                'XRP': 0.52, 'ADA': 0.45, 'DOGE': 0.12, 'AVAX': 35,
                'DOT': 7.2, 'LINK': 14.5, 'MATIC': 0.72, 'UNI': 9.5,
                'ATOM': 8.8, 'LTC': 85, 'ETC': 26, 'FIL': 5.8,
                'APT': 8.2, 'ARB': 1.05, 'OP': 2.1, 'NEAR': 5.8
            }
            self._price_cache[symbol] = prices.get(symbol, 100)
        return self._price_cache[symbol]
    
    def _get_change(self, symbol: str) -> float:
        """Generate change"""
        return random.uniform(-8, 8)
    
    def execute_decisions(self, results: List[CoinAnalysis]) -> List[Dict]:
        """Execute trading decisions"""
        if not self.execute_callback:
            return []
        
        executed = []
        buys = [r for r in results if r.action == 'LONG' and r.confidence > 0.6][:2]
        sells = [r for r in results if r.action == 'SHORT' and r.confidence > 0.6][:2]
        
        for buy in buys:
            try:
                result = self.execute_callback('BUY', buy.symbol, buy.total_score)
                executed.append({'action': 'BUY', 'symbol': buy.symbol, 'score': buy.total_score})
            except: pass
        
        for sell in sells:
            try:
                result = self.execute_callback('SELL', sell.symbol, sell.total_score)
                executed.append({'action': 'SELL', 'symbol': sell.symbol, 'score': sell.total_score})
            except: pass
        
        return executed

if __name__ == '__main__':
    scanner = AutonomousScanner()
    
    print("=== Scanner Test ===")
    results = scanner.scan_all()
    
    print(f"\nScanned {len(results)} coins in {results[0].scan_duration_ms:.1f}ms")
    print("\nTop 5:")
    for r in results[:5]:
        print(f"  {r.symbol}: {r.total_score:.1f} ({r.signal}) - {r.action}")
