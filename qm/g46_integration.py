"""
G46 Integration - G46完整功能集成
包含: Oracle决策 + 黑名单 + 自动调配 + 42币扫描 + Meme策略 + Cross Margin + Polymarket
"""
import sys
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.binance_optimizer import BinanceAPI
    HAS_API = True
except:
    HAS_API = False

class MarketRegime(Enum):
    """市场状态"""
    BULL = "BULL"
    TRENDING_UP = "TRENDING_UP"
    RANGING = "RANGING"
    TRENDING_DOWN = "TRENDING_DOWN"
    BEAR = "BEAR"

class TradeAction(Enum):
    """交易操作"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    ADD = "ADD"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

@dataclass
class OracleDecision:
    """Oracle决策"""
    action: TradeAction
    rsi: float
    momentum: float
    confidence: float
    score: float
    reasons: List[str]

@dataclass
class CoinScore:
    """币种评分"""
    symbol: str
    price: float
    change_24h: float
    rsi: float
    momentum: float
    oracle_score: float
    action: TradeAction
    is_meme: bool
    in_blacklist: bool

class BlacklistManager:
    """黑名单管理"""
    
    BLACKLIST = [
        'NEIRO', 'TURBO', 'PEPE', 'FLOKI', 'BOME', 'SHIB', 'DOGE',
        'XEC', 'PAXG', 'BTT', 'NFT', 'FUN', 'MDT', 'LLT'
    ]
    
    @classmethod
    def is_blacklisted(cls, symbol: str) -> bool:
        return symbol.upper() in [s.upper() for s in cls.BLACKLIST]
    
    @classmethod
    def filter_blacklist(cls, symbols: List[str]) -> List[str]:
        return [s for s in symbols if not cls.is_blacklisted(s)]

class OracleDecisionEngine:
    """
    Oracle决策系统
    
    RSI + 动量综合评分
    """
    
    def __init__(self):
        self.config = {
            TradeAction.STRONG_BUY: {'rsi_max': 25, 'score_min': 90, 'conf_min': 0.40},
            TradeAction.BUY: {'rsi_max': 30, 'score_min': 75, 'conf_min': 0.30},
            TradeAction.ADD: {'rsi_max': 35, 'score_min': 60, 'conf_min': 0.20},
            TradeAction.HOLD: {'rsi_range': (30, 50), 'score_min': 50, 'conf_min': 0.10},
            TradeAction.REDUCE: {'rsi_min': 70, 'score_min': 60, 'conf_min': 0.10},
            TradeAction.SELL: {'rsi_min': 80, 'score_min': 50, 'conf_min': 0.00},
            TradeAction.STRONG_SELL: {'rsi_min': 85, 'score_min': 40, 'conf_min': 0.00},
        }
    
    def calculate_score(self, rsi: float, momentum: float, is_meme: bool = False) -> float:
        """计算综合评分"""
        # RSI评分 (低RSI=买入信号)
        if is_meme:
            if rsi < 25: rsi_score = 100
            elif rsi < 30: rsi_score = 80
            elif rsi < 35: rsi_score = 60
            elif rsi > 70: rsi_score = 20
            elif rsi > 80: rsi_score = 0
            else: rsi_score = 50
        else:
            if rsi < 30: rsi_score = 100
            elif rsi < 35: rsi_score = 70
            elif rsi > 70: rsi_score = 30
            elif rsi > 80: rsi_score = 0
            else: rsi_score = 50
        
        # 动量评分 (负动量=下跌=买入信号)
        if momentum < -5: momentum_score = 100
        elif momentum < -2: momentum_score = 70
        elif momentum < 0: momentum_score = 50
        elif momentum < 5: momentum_score = 30
        else: momentum_score = 10
        
        # 综合评分
        return rsi_score * 0.6 + momentum_score * 0.4
    
    def decide(self, symbol: str, rsi: float, momentum: float, is_meme: bool = False) -> OracleDecision:
        """Oracle决策"""
        score = self.calculate_score(rsi, momentum, is_meme)
        
        # 确定操作
        if is_meme:
            if rsi < 25 and score > 90: action = TradeAction.STRONG_BUY
            elif rsi < 30 and score > 75: action = TradeAction.BUY
            elif rsi < 35 and score > 60: action = TradeAction.ADD
            elif 30 <= rsi <= 50 and score > 50: action = TradeAction.HOLD
            elif rsi > 70 and score > 60: action = TradeAction.REDUCE
            elif rsi > 80: action = TradeAction.SELL
            else: action = TradeAction.HOLD
        else:
            if rsi < 30 and score > 90: action = TradeAction.STRONG_BUY
            elif rsi < 35 and score > 75: action = TradeAction.BUY
            elif rsi < 40 and score > 60: action = TradeAction.ADD
            elif 30 <= rsi <= 50 and score > 50: action = TradeAction.HOLD
            elif rsi > 65: action = TradeAction.REDUCE
            elif rsi > 75: action = TradeAction.SELL
            else: action = TradeAction.HOLD
        
        # 置信度
        conf_map = {
            TradeAction.STRONG_BUY: 0.85,
            TradeAction.BUY: 0.75,
            TradeAction.ADD: 0.65,
            TradeAction.HOLD: 0.50,
            TradeAction.REDUCE: 0.60,
            TradeAction.SELL: 0.70,
            TradeAction.STRONG_SELL: 0.80
        }
        confidence = conf_map.get(action, 0.5)
        
        reasons = [
            f"RSI: {rsi:.1f}",
            f"动量: {momentum:+.2f}%",
            f"评分: {score:.1f}",
            f"操作: {action.value}"
        ]
        
        return OracleDecision(
            action=action,
            rsi=rsi,
            momentum=momentum,
            confidence=confidence,
            score=score,
            reasons=reasons
        )

class PolymarketSignal:
    """
    Polymarket信号融合
    """
    
    @staticmethod
    def get_signal(market: str = "crypto") -> Dict:
        """获取Polymarket信号"""
        # 模拟Polymarket信号
        return {
            'bull_probability': random.uniform(0.3, 0.7),
            'volume': random.uniform(1e5, 1e6),
            'trend': random.choice(['bull', 'bear', 'neutral'])
        }
    
    @staticmethod
    def fuse_signals(oracle_score: float, polymarket_bull_prob: float) -> float:
        """融合信号"""
        # 综合信号 = Oracle x 60% + Polymarket x 40%
        polymarket_score = polymarket_bull_prob * 100
        return oracle_score * 0.6 + polymarket_score * 0.4

class FullCoverageScanner:
    """
    全域42币扫描
    """
    
    MAIN_COINS = [
        'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT', 'LINK', 'UNI',
        'AVAX', 'MATIC', 'ATOM', 'LTC', 'ETC', 'AAVE', 'APT', 'NEAR', 'FIL', 'ICP',
        'INJ', 'TIA', 'SEI', 'SUI', 'OP', 'ARB', 'LDO', 'CRV', 'RDNT', 'ENS'
    ]
    
    MEME_COINS = [
        'PEPE', 'SHIB', 'FLOKI', 'WIF', 'BABYDOGE', 'COOKIE', 'AI', 'NEIRO',
        'BOME', 'TURBO', 'PUMP', 'BONK'
    ]
    
    def __init__(self, api=None):
        self.api = api
        self.oracle = OracleDecisionEngine()
        self.blacklist = BlacklistManager()
        self.polymarket = PolymarketSignal()
    
    def scan_coin(self, symbol: str, is_meme: bool = False) -> CoinScore:
        """扫描单个币种"""
        # 检查黑名单
        if self.blacklist.is_blacklisted(symbol):
            return CoinScore(
                symbol=symbol, price=0, change_24h=0,
                rsi=50, momentum=0, oracle_score=0,
                action=TradeAction.HOLD, is_meme=is_meme, in_blacklist=True
            )
        
        # 获取价格 (模拟)
        price = random.uniform(1, 50000) if not self.api else 100
        change_24h = random.uniform(-10, 10)
        
        # 计算RSI和动量 (模拟)
        rsi = random.uniform(20, 80)
        momentum = random.uniform(-10, 10)
        
        # Oracle决策
        oracle = self.oracle.decide(symbol, rsi, momentum, is_meme)
        
        # Polymarket融合
        pm_signal = self.polymarket.get_signal()
        fused_score = self.polymarket.fuse_signals(oracle.score, pm_signal['bull_probability'])
        
        return CoinScore(
            symbol=symbol,
            price=price,
            change_24h=change_24h,
            rsi=rsi,
            momentum=momentum,
            oracle_score=fused_score,
            action=oracle.action,
            is_meme=is_meme,
            in_blacklist=False
        )
    
    def scan_all(self) -> Dict:
        """扫描所有42币"""
        results = []
        
        # 扫描主流币
        for coin in self.MAIN_COINS:
            score = self.scan_coin(coin, is_meme=False)
            if not score.in_blacklist:
                results.append(score)
        
        # 扫描Meme币
        for coin in self.MEME_COINS:
            if not self.blacklist.is_blacklisted(coin):
                score = self.scan_coin(coin, is_meme=True)
                if not score.in_blacklist:
                    results.append(score)
        
        # 按评分排序
        results.sort(key=lambda x: x.oracle_score, reverse=True)
        
        return {
            'total': len(results),
            'main_coins': [r for r in results if not r.is_meme],
            'meme_coins': [r for r in results if r.is_meme],
            'all_coins': results,
            'buy_signals': [r for r in results if r.action in [TradeAction.STRONG_BUY, TradeAction.BUY, TradeAction.ADD]],
            'sell_signals': [r for r in results if r.action in [TradeAction.SELL, TradeAction.STRONG_SELL, TradeAction.REDUCE]]
        }

class AutoFundAllocator:
    """
    自动资金调配
    """
    
    def __init__(self, total_capital: float = 10000):
        self.total_capital = total_capital
        self.min_order_value = 5  # 最小订单$5
        self.max_position_pct = 0.30  # 最大30%仓位
    
    def allocate(self, signals: List[CoinScore], available_usdt: float) -> List[Dict]:
        """自动分配资金"""
        allocations = []
        
        # 筛选买入信号
        buy_signals = [s for s in signals if s.action in [TradeAction.STRONG_BUY, TradeAction.BUY, TradeAction.ADD]]
        
        if not buy_signals:
            return [{'action': 'NO_SIGNALS', 'reason': 'No buy signals'}]
        
        # 计算可用资金
        usable_capital = min(available_usdt, self.total_capital * 0.8)  # 最多80%使用
        
        # 分配资金
        per_position = usable_capital / min(len(buy_signals), 5)  # 最多5个仓位
        
        if per_position < self.min_order_value:
            return [{'action': 'TOO_LITTLE_CAPITAL', 'reason': f'${per_position:.2f} < ${self.min_order_value}'}]
        
        for signal in buy_signals[:5]:
            allocations.append({
                'symbol': signal.symbol,
                'action': signal.action.value,
                'price': signal.price,
                'allocation': per_position,
                'quantity': per_position / signal.price if signal.price > 0 else 0,
                'oracle_score': signal.oracle_score,
                'reasons': signal.action.value
            })
        
        return allocations
    
    def rebalance(self, positions: List[Dict], signals: List[CoinScore]) -> Dict:
        """调仓决策"""
        decisions = {'sell': [], 'buy': [], 'hold': []}
        
        # 当前持仓
        current_symbols = {p['symbol'] for p in positions}
        
        # 信号中的币种
        signal_symbols = {s.symbol for s in signals if s.action in [TradeAction.BUY, TradeAction.STRONG_BUY]}
        
        # 需卖出的 (持仓但不在信号中)
        for pos in positions:
            if pos['symbol'] not in signal_symbols:
                decisions['sell'].append({
                    'symbol': pos['symbol'],
                    'quantity': pos['quantity'],
                    'reason': '不在信号中'
                })
        
        # 需买入的 (信号中有但不在持仓中)
        for signal in signals:
            if signal.action in [TradeAction.BUY, TradeAction.STRONG_BUY]:
                if signal.symbol not in current_symbols:
                    decisions['buy'].append({
                        'symbol': signal.symbol,
                        'allocation': 100,  # 默认$100
                        'reason': signal.action.value
                    })
        
        return decisions

class CrossMarginManager:
    """
    Cross Margin管理
    """
    
    def __init__(self, api=None):
        self.api = api
    
    def get_margin_mode(self) -> str:
        """获取当前Margin模式"""
        # 模拟
        return random.choice(['CROSS', 'ISOLATED'])
    
    def switch_to_cross_margin(self) -> bool:
        """切换到全仓"""
        # 模拟
        return True
    
    def switch_to_isolated_margin(self, symbol: str) -> bool:
        """切换到逐仓"""
        # 模拟
        return True
    
    def get_borrow_info(self) -> Dict:
        """获取借款信息"""
        return {
            'total_borrowed': random.uniform(0, 1000),
            'interest_rate': 0.0004,
            'max_borrow': 10000
        }

class G46Integration:
    """
    G46完整集成
    """
    
    def __init__(self, capital: float = 10000):
        self.capital = capital
        self.api = BinanceAPI() if HAS_API else None
        self.oracle = OracleDecisionEngine()
        self.blacklist = BlacklistManager()
        self.scanner = FullCoverageScanner(self.api)
        self.allocator = AutoFundAllocator(capital)
        self.margin = CrossMarginManager(self.api)
    
    def run_full_scan(self) -> Dict:
        """运行完整扫描"""
        scan_result = self.scanner.scan_all()
        
        # 自动分配
        allocations = self.allocator.allocate(scan_result['all_coins'], self.capital)
        
        return {
            'scan': scan_result,
            'allocations': allocations,
            'margin_mode': self.margin.get_margin_mode()
        }
    
    def generate_report(self) -> str:
        """生成报告"""
        result = self.run_full_scan()
        scan = result['scan']
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              G46 Integration - 全功能集成                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 全域扫描: {scan['total']}币
   主流币: {len(scan['main_coins'])} | Meme币: {len(scan['meme_coins'])}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🏆 买入信号 TOP 10                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for i, coin in enumerate(scan['buy_signals'][:10], 1):
            emoji = "🟢" if coin.action == TradeAction.STRONG_BUY else "🟡"
            meme_tag = " [MEME]" if coin.is_meme else ""
            report += f"{i:2}. {emoji} {coin.symbol:10}{meme_tag:8} RSI:{coin.rsi:5.1f} 动量:{coin.momentum:+6.2f}% 评分:{coin.oracle_score:5.1f} {coin.action.value}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔴 卖出信号                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for coin in scan['sell_signals'][:5]:
            report += f"   🔴 {coin.symbol:10} RSI:{coin.rsi:5.1f} 动量:{coin.momentum:+6.2f}% {coin.action.value}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    💰 自动资金分配                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for alloc in result['allocations'][:5]:
            if 'symbol' in alloc:
                report += f"   🟢 {alloc['symbol']:10} ${alloc['allocation']:>8,.0f} {alloc['action']}\n"
            else:
                report += f"   ⚠️ {alloc.get('action', 'UNKNOWN')}: {alloc.get('reason', '')}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 系统状态                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

   Margin模式: {result['margin_mode']}
   黑名单过滤: {len(self.blacklist.BLACKLIST)}币种
   买入信号: {len(scan['buy_signals'])}个
   卖出信号: {len(scan['sell_signals'])}个

"""
        
        return report

def main():
    g46 = G46Integration(10000)
    print(g46.generate_report())

if __name__ == '__main__':
    main()
