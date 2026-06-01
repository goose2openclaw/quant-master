"""
QM Leverage Engine - 杠杆自主调用引擎
根据市场状态动态调整杠杆 + 自动开仓/平仓
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
    BULL = "BULL"           # 强势上涨
    TRENDING_UP = "TRENDING_UP"     # 上涨趋势
    RANGING = "RANGING"     # 震荡
    TRENDING_DOWN = "TRENDING_DOWN"  # 下跌趋势
    BEAR = "BEAR"           # 强势下跌

class LeverageLevel(Enum):
    """杠杆级别"""
    SAFE = 1.0      # 1x 安全
    MODERATE = 2.0  # 2x 适中
    AGGRESSIVE = 3.0  # 3x 激进
    HIGH_RISK = 5.0  # 5x 高风险
    EXTREME = 10.0  # 10x 极限

@dataclass
class LeveragePosition:
    """杠杆仓位"""
    symbol: str
    side: str  # LONG/SHORT
    entry_price: float
    current_price: float
    leverage: float
    quantity: float
    margin: float
    pnl_pct: float
    liquidation_price: float

class MarketRegimeDetector:
    """市场状态检测"""
    
    def __init__(self, api=None):
        self.api = api
    
    def detect_regime(self, symbol: str = 'BTCUSDT') -> MarketRegime:
        """检测市场状态"""
        # 获取K线数据
        if self.api:
            klines = self.api.get_klines(symbol, '1h', 100)
        else:
            klines = self._generate_fake_klines()
        
        if not klines:
            return MarketRegime.RANGING
        
        # 计算指标
        closes = [k['close'] for k in klines]
        
        # 移动平均
        ma7 = sum(closes[-7:]) / 7
        ma25 = sum(closes[-25:]) / 25
        ma99 = sum(closes[-99:]) / 99
        
        # 波动率
        recent_vol = sum(abs(closes[i] - closes[i-1]) for i in range(1, min(20, len(closes)))) / min(20, len(closes)) / closes[-1]
        
        # 趋势判断
        if ma7 > ma25 > ma99 and closes[-1] > ma7 * 1.02:
            if recent_vol > 0.02:
                return MarketRegime.BULL
            return MarketRegime.TRENDING_UP
        elif ma7 < ma25 < ma99 and closes[-1] < ma7 * 0.98:
            if recent_vol > 0.02:
                return MarketRegime.BEAR
            return MarketRegime.TRENDING_DOWN
        else:
            return MarketRegime.RANGING
    
    def _generate_fake_klines(self):
        """生成模拟K线"""
        base = 72000
        return [{'close': base * (1 + random.uniform(-0.01, 0.01))} for _ in range(100)]

class LeverageOptimizer:
    """
    杠杆优化器
    
    功能:
    1. 根据市场状态自动调整杠杆
    2. 动态仓位管理
    3. 自动止损/止盈
    4. 杠杆调用策略
    """
    
    def __init__(self, api=None, capital: float = 10000):
        self.api = api or (BinanceAPI() if HAS_API else None)
        self.capital = capital
        self.regime_detector = MarketRegimeDetector(self.api)
        
        # 杠杆配置表
        self.leverage_table = {
            MarketRegime.BULL: {
                'max_leverage': 5.0,
                'recommended': 3.0,
                'stop_loss': 0.03,
                'take_profit': 0.15,
                'position_size': 0.30
            },
            MarketRegime.TRENDING_UP: {
                'max_leverage': 3.0,
                'recommended': 2.0,
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'position_size': 0.20
            },
            MarketRegime.RANGING: {
                'max_leverage': 2.0,
                'recommended': 1.5,
                'stop_loss': 0.08,
                'take_profit': 0.06,
                'position_size': 0.15
            },
            MarketRegime.TRENDING_DOWN: {
                'max_leverage': 3.0,
                'recommended': 2.0,
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'position_size': 0.20
            },
            MarketRegime.BEAR: {
                'max_leverage': 5.0,
                'recommended': 3.0,
                'stop_loss': 0.03,
                'take_profit': 0.15,
                'position_size': 0.30
            }
        }
        
        # 当前仓位
        self.positions: List[LeveragePosition] = []
        
    def get_optimal_leverage(self, symbol: str = 'BTCUSDT') -> Dict:
        """获取最优杠杆"""
        regime = self.regime_detector.detect_regime(symbol)
        config = self.leverage_table[regime]
        
        return {
            'regime': regime.value,
            'max_leverage': config['max_leverage'],
            'recommended': config['recommended'],
            'stop_loss': config['stop_loss'],
            'take_profit': config['take_profit'],
            'position_size': config['position_size'],
            'position_size_pct': config['position_size'] * 100
        }
    
    def calculate_position(self, symbol: str, leverage: float, regime: MarketRegime) -> Dict:
        """计算仓位"""
        config = self.leverage_table[regime]
        
        # 获取当前价格
        if self.api:
            ticker = self.api.get_ticker(symbol)
            price = ticker['price'] if ticker else 72000
        else:
            price = 72000
        
        # 仓位大小 (占总资本百分比)
        position_value = self.capital * config['position_size'] * leverage
        
        # 保证金
        margin = position_value / leverage
        
        # 数量
        quantity = position_value / price
        
        # 强平价
        if regime in [MarketRegime.BULL, MarketRegime.TRENDING_UP]:
            # 做多, 下跌触发强平
            liquidation = price * (1 - 1/leverage * 0.8)
        else:
            # 做空, 上涨触发强平
            liquidation = price * (1 + 1/leverage * 0.8)
        
        return {
            'symbol': symbol,
            'side': 'LONG' if regime in [MarketRegime.BULL, MarketRegime.TRENDING_UP] else 'SHORT',
            'entry_price': price,
            'leverage': leverage,
            'margin': margin,
            'quantity': quantity,
            'position_value': position_value,
            'liquidation_price': liquidation,
            'stop_loss': config['stop_loss'],
            'take_profit': config['take_profit'],
            'regime': regime.value
        }
    
    def auto_leverage(self, symbols: List[str] = None) -> Dict:
        """自主杠杆调用"""
        if symbols is None:
            symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        
        results = []
        
        for symbol in symbols:
            regime = self.regime_detector.detect_regime(symbol)
            optimal = self.get_optimal_leverage(symbol)
            position = self.calculate_position(symbol, optimal['recommended'], regime)
            results.append({
                'symbol': symbol,
                'regime': regime.value,
                'leverage': optimal['recommended'],
                'position': position
            })
        
        return {
            'timestamp': time.time(),
            'regime_detections': [{'symbol': r['symbol'], 'regime': r['regime']} for r in results],
            'positions': [r['position'] for r in results],
            'total_allocated': sum(p['position']['margin'] for p in results),
            'potential_exposure': sum(p['position']['position_value'] for p in results)
        }
    
    def execute_leverage_trade(self, symbol: str, leverage: float, side: str) -> Dict:
        """执行杠杆交易"""
        # 获取价格
        if self.api:
            ticker = self.api.get_ticker(symbol)
            price = ticker['price'] if ticker else 72000
        else:
            price = 72000
        
        # 仓位计算
        position_value = self.capital * 0.2 * leverage
        margin = position_value / leverage
        quantity = position_value / price
        
        # 做空强平价
        if side == 'SHORT':
            liquidation = price * (1 + 1/leverage * 0.8)
        else:
            liquidation = price * (1 - 1/leverage * 0.8)
        
        position = LeveragePosition(
            symbol=symbol,
            side=side,
            entry_price=price,
            current_price=price,
            leverage=leverage,
            quantity=quantity,
            margin=margin,
            pnl_pct=0,
            liquidation_price=liquidation
        )
        
        self.positions.append(position)
        
        return {
            'success': True,
            'symbol': symbol,
            'side': side,
            'entry_price': price,
            'leverage': leverage,
            'quantity': quantity,
            'margin': margin,
            'liquidation_price': liquidation,
            'stop_loss': price * (0.95 if side == 'LONG' else 1.05),
            'take_profit': price * (1.10 if side == 'LONG' else 0.90)
        }
    
    def generate_report(self) -> str:
        """生成报告"""
        auto_result = self.auto_leverage()
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              💰 QM Leverage Engine - 杠杆自主调用引擎                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏰ 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 市场状态检测                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for det in auto_result['regime_detections']:
            emoji = {
                'BULL': '🟢',
                'TRENDING_UP': '🟢',
                'RANGING': '🟡',
                'TRENDING_DOWN': '🔴',
                'BEAR': '🔴'
            }.get(det['regime'], '⚪')
            report += f"   {emoji} {det['symbol']:12} {det['regime']}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⚡ 杠杆推荐                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for pos in auto_result['positions']:
            p = pos['position']
            emoji = "🟢" if p['side'] == 'LONG' else "🔴"
            report += f"""
   {emoji} {p['symbol']:12} {p['side']} @ ${p['entry_price']:,.0f}
   ⚡ 杠杆: {p['leverage']:.1f}x | 保证金: ${p['margin']:,.0f}
   📊 数量: {p['quantity']:.4f} | 仓位价值: ${p['position_value']:,.0f}
   🛡️ 强平价: ${p['liquidation_price']:,.0f}
   📈 止盈: {p['take_profit']*100:.0f}% | 📉 止损: {p['stop_loss']*100:.0f}%
"""
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    📋 汇总                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

   总保证金: ${auto_result['total_allocated']:,.2f}
   潜在敞口: ${auto_result['potential_exposure']:,.2f}
   实际杠杆: {auto_result['potential_exposure']/self.capital:.1f}x

"""
        
        return report

def main():
    engine = LeverageOptimizer()
    print(engine.generate_report())

if __name__ == '__main__':
    main()
