"""
QM Core - Unified QuantMaster System
Combines: Coin Selector + MiroFish + Watchdog + Binance Scanner + Optimizer
"""
import sys
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

class TradeMode(Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"

class SignalStrength(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

@dataclass
class QMTrade:
    """交易记录"""
    timestamp: float
    symbol: str
    side: str  # BUY/SELL
    mode: str  # SIMULATION/LIVE
    price: float
    quantity: float
    value: float
    pnl: float = 0
    signal: str = ""
    confidence: float = 0

@dataclass
class QMPortfolio:
    """组合"""
    initial_capital: float
    simulation_capital: float
    live_capital: float
    simulation_positions: Dict[str, float] = field(default_factory=dict)
    live_positions: Dict[str, float] = field(default_factory=dict)
    trades: List[QMTrade] = field(default_factory=list)
    equity_curve_sim: List[float] = field(default_factory=list)
    equity_curve_live: List[float] = field(default_factory=list)

class QM:
    """
    QM - QuantMaster Unified System
    
    Features:
    1. Coin Selection - Multi-factor coin ranking
    2. Signal Generation - MiroFish + Technical analysis
    3. Decision Making - Watchdog risk management
    4. Trade Execution - Simulation + Live
    5. Performance Tracking
    """
    
    def __init__(self, initial_capital: float = 10000, mode: TradeMode = TradeMode.SIMULATION):
        self.name = "QM - QuantMaster"
        self.mode = mode
        self.portfolio = QMPortfolio(
            initial_capital=initial_capital,
            simulation_capital=initial_capital,
            live_capital=initial_capital * 0.1  # 10% for live
        )
        
        # Initialize components
        self._init_components()
        
        # Stats
        self.total_trades = 0
        self.simulation_trades = 0
        self.live_trades = 0
        self.win_count = 0
        self.loss_count = 0
        
    def _init_components(self):
        """初始化组件"""
        try:
            from coin_selector.selector import EnhancedCoinSelector
            self.coin_selector = EnhancedCoinSelector()
        except:
            self.coin_selector = None
            
        try:
            from mirofish_core.mirofish import MiroFishCore, MiroFishConfig
            self.mirofish = MiroFishCore(MiroFishConfig(simulation_required=True))
        except:
            self.mirofish = None
            
        try:
            from strategic_watchdog.enhanced_overseer import EnhancedWatchdog
            self.watchdog = EnhancedWatchdog(self.portfolio.simulation_capital)
        except:
            self.watchdog = None
            
        try:
            from binance_deep.scanner import BinanceDeepScanner
            self.scanner = BinanceDeepScanner()
        except:
            self.scanner = None
    
    def scan_market(self) -> Dict:
        """扫描市场"""
        result = {
            'timestamp': time.time(),
            'mode': self.mode.value,
            'scanner_opportunities': [],
            'coin_rankings': [],
            'top_picks': [],
            'market_sentiment': 'NEUTRAL',
            'actionable_signals': []
        }
        
        # Binance scanner
        if self.scanner:
            try:
                opps = self.scanner.get_top_opportunities(10)
                result['scanner_opportunities'] = [
                    {'symbol': o.symbol, 'score': o.score, 'action': o.action, 'category': o.category}
                    for o in opps
                ]
            except:
                pass
        
        # Coin selector
        if self.coin_selector:
            try:
                report = self.coin_selector.get_full_report()
                result['coin_rankings'] = report['all_rankings'][:10]
                result['market_sentiment'] = report['market_sentiment']
                result['top_picks'] = report['buy_list'][:5]
            except:
                pass
        
        return result
    
    def analyze_coin(self, symbol: str) -> Dict:
        """分析币种"""
        analysis = {
            'symbol': symbol,
            'timestamp': time.time(),
            'mirofish_decision': None,
            'watchdog_verdict': None,
            'signal_strength': SignalStrength.HOLD.value,
            'confidence': 50,
            'recommendation': 'HOLD',
            'reasons': []
        }
        
        # MiroFish
        if self.mirofish:
            try:
                decision = self.mirofish.generate_trading_decision(symbol, {'price': 67000})
                analysis['mirofish_decision'] = decision
                analysis['confidence'] = decision.get('confidence', 50) * 100
            except:
                pass
        
        # Generate signal
        if analysis['confidence'] >= 75:
            if analysis['mirofish_decision'] and analysis['mirofish_decision'].get('decision') == 'BUY':
                analysis['signal_strength'] = SignalStrength.STRONG_BUY.value
                analysis['recommendation'] = 'BUY'
                analysis['reasons'].append('MiroFish强烈看涨')
        elif analysis['confidence'] >= 60:
            analysis['signal_strength'] = SignalStrength.BUY.value
            analysis['recommendation'] = 'BUY'
            analysis['reasons'].append('MiroFish看涨信号')
        elif analysis['confidence'] <= 35:
            analysis['signal_strength'] = SignalStrength.SELL.value
            analysis['recommendation'] = 'SELL'
            analysis['reasons'].append('MiroFish看跌信号')
        
        return analysis
    
    def execute_trade(self, symbol: str, side: str, quantity: float, price: float, 
                     trade_mode: str = None) -> Dict:
        """执行交易"""
        if trade_mode is None:
            trade_mode = self.mode.value
        
        value = quantity * price
        
        # Check capital
        if trade_mode == TradeMode.SIMULATION.value:
            if side == "BUY" and value > self.portfolio.simulation_capital:
                return {'success': False, 'reason': 'Insufficient capital'}
            self.portfolio.simulation_capital -= value if side == "BUY" else -value
        else:
            if side == "BUY" and value > self.portfolio.live_capital:
                return {'success': False, 'reason': 'Insufficient capital'}
            self.portfolio.live_capital -= value if side == "BUY" else -value
        
        # P&L simulation
        pnl = random.uniform(-value * 0.1, value * 0.2) if trade_mode == TradeMode.SIMULATION.value else 0
        
        # Record trade
        trade = QMTrade(
            timestamp=time.time(),
            symbol=symbol,
            side=side,
            mode=trade_mode,
            price=price,
            quantity=quantity,
            value=value,
            pnl=pnl,
            confidence=self.analyze_coin(symbol).get('confidence', 50)
        )
        self.portfolio.trades.append(trade)
        
        # Update stats
        self.total_trades += 1
        if trade_mode == TradeMode.SIMULATION.value:
            self.simulation_trades += 1
        else:
            self.live_trades += 1
        if pnl > 0:
            self.win_count += 1
        elif pnl < 0:
            self.loss_count += 1
        
        return {
            'success': True,
            'trade': {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'value': value,
                'pnl': pnl,
                'mode': trade_mode
            }
        }
    
    def run_simulation(self, cycles: int = 10) -> Dict:
        """运行模拟交易"""
        print(f"\n{'='*60}")
        print(f"🎮 QM Simulation - {cycles} Cycles")
        print(f"{'='*60}")
        
        for cycle in range(1, cycles + 1):
            print(f"\n📍 Cycle {cycle}/{cycles}")
            
            # Scan market
            market = self.scan_market()
            print(f"   Market: {market['market_sentiment']}")
            print(f"   Scanner: {len(market['scanner_opportunities'])} opps")
            print(f"   Rankings: {len(market['coin_rankings'])} coins")
            
            # Top pick
            if market['top_picks']:
                top = market['top_picks'][0]
                print(f"   🏆 Top: {top['symbol']} ({top['score']:.1f}分)")
                
                # Analyze
                analysis = self.analyze_coin(top['symbol'])
                print(f"   📊 Signal: {analysis['signal_strength']} ({analysis['confidence']:.0f}%)")
                print(f"   💡 Recommendation: {analysis['recommendation']}")
                
                # Execute if strong signal
                if analysis['recommendation'] == 'BUY' and analysis['confidence'] >= 60:
                    qty = self.portfolio.simulation_capital * 0.1 / 67000  # 10% capital
                    result = self.execute_trade(top['symbol'], 'BUY', qty, 67000, 'SIMULATION')
                    if result['success']:
                        print(f"   ✅ BUY {top['symbol']}: ${result['trade']['value']:.2f}, P&L: ${result['trade']['pnl']:.2f}")
        
        # Final report
        sim_pnl = self.portfolio.simulation_capital - self.portfolio.initial_capital
        win_rate = self.win_count / max(1, self.total_trades) * 100
        
        print(f"\n{'='*60}")
        print(f"📊 Simulation Results")
        print(f"{'='*60}")
        print(f"   Initial: ${self.portfolio.initial_capital:,.2f}")
        print(f"   Final: ${self.portfolio.simulation_capital:,.2f}")
        print(f"   P&L: ${sim_pnl:+,.2f} ({sim_pnl/self.portfolio.initial_capital*100:+.1f}%)")
        print(f"   Trades: {self.simulation_trades}")
        print(f"   Win Rate: {win_rate:.0f}%")
        print(f"{'='*60}")
        
        return {
            'initial_capital': self.portfolio.initial_capital,
            'final_capital': self.portfolio.simulation_capital,
            'pnl': sim_pnl,
            'pnl_pct': sim_pnl / self.portfolio.initial_capital * 100,
            'total_trades': self.simulation_trades,
            'win_rate': win_rate
        }
    
    def get_live_opportunities(self) -> List[Dict]:
        """获取实盘机会建议"""
        market = self.scan_market()
        opportunities = []
        
        # Process scanner opportunities
        for opp in market.get('scanner_opportunities', []):
            if opp['action'] in ['BUY', 'LONG', 'ARB', 'FARM', 'STAKE']:
                opportunities.append({
                    'type': 'SCANNER',
                    'symbol': opp['symbol'],
                    'score': opp['score'],
                    'action': opp['action'],
                    'category': opp.get('category', 'SPOT'),
                    'priority': 'HIGH' if opp['score'] > 75 else 'MEDIUM' if opp['score'] > 60 else 'LOW',
                    'recommendation': f"Consider {opp['action']} {opp['symbol']}",
                    'confidence': min(95, opp['score'] + 10),
                    'mode': 'LIVE'
                })
        
        # Process coin rankings
        for coin in market.get('coin_rankings', [])[:5]:
            analysis = self.analyze_coin(coin['symbol'])
            if analysis['recommendation'] in ['BUY', 'SELL']:
                opportunities.append({
                    'type': 'ANALYSIS',
                    'symbol': coin['symbol'],
                    'score': coin['score'],
                    'action': analysis['recommendation'],
                    'category': 'TECHNICAL',
                    'priority': 'HIGH' if analysis['confidence'] > 70 else 'MEDIUM',
                    'recommendation': f"{analysis['recommendation']} {coin['symbol']}: {', '.join(analysis['reasons'][:2])}",
                    'confidence': analysis['confidence'],
                    'mode': 'LIVE'
                })
        
        # Sort by priority and confidence
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        opportunities.sort(key=lambda x: (priority_order.get(x['priority'], 3), -x['confidence']))
        
        return opportunities[:10]
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'mode': self.mode.value,
            'initial_capital': self.portfolio.initial_capital,
            'simulation_capital': self.portfolio.simulation_capital,
            'live_capital': self.portfolio.live_capital,
            'simulation_pnl': self.portfolio.simulation_capital - self.portfolio.initial_capital,
            'live_pnl': self.portfolio.live_capital - self.portfolio.initial_capital * 0.1,
            'total_trades': self.total_trades,
            'simulation_trades': self.simulation_trades,
            'live_trades': self.live_trades,
            'win_count': self.win_count,
            'loss_count': self.loss_count,
            'win_rate': self.win_count / max(1, self.win_count + self.loss_count) * 100
        }

def main():
    """Main entry"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    QM - QuantMaster Unified System               ║
║              Simulation + Live Trading Opportunity System          ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize QM
    qm = QM(initial_capital=10000, mode=TradeMode.SIMULATION)
    
    # Run simulation
    sim_result = qm.run_simulation(cycles=5)
    
    # Get live opportunities
    print(f"\n{'='*60}")
    print(f"📈 Live Trading Opportunities")
    print(f"{'='*60}")
    
    opps = qm.get_live_opportunities()
    print(f"\nFound {len(opps)} actionable opportunities:\n")
    
    for i, opp in enumerate(opps, 1):
        emoji = "🟢" if opp['action'] == 'BUY' else "🔴"
        print(f"{i}. {emoji} {opp['symbol']:10} {opp['action']:6} | {opp['recommendation']}")
        print(f"   Score: {opp['score']:.1f} | Confidence: {opp['confidence']:.0f}% | Priority: {opp['priority']}")
        print()
    
    # Status
    status = qm.get_status()
    print(f"\n{'='*60}")
    print(f"📊 QM Status")
    print(f"{'='*60}")
    print(f"   Mode: {status['mode']}")
    print(f"   Simulation Capital: ${status['simulation_capital']:,.2f}")
    print(f"   Simulation P&L: ${status['simulation_pnl']:+,.2f}")
    print(f"   Live Capital: ${status['live_capital']:,.2f} (for opportunities)")
    print(f"   Total Trades: {status['total_trades']}")
    print(f"   Win Rate: {status['win_rate']:.0f}%")
    print(f"{'='*60}")
    
    return qm

if __name__ == '__main__':
    main()
