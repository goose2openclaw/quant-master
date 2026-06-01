"""
QM Unified - 模块数据打通 + 专业策略逻辑
"""
import sys
import time
import random
import math
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.binance_optimizer import BinanceAPI
    HAS_API = True
except:
    HAS_API = False

@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    price: float
    rsi: float
    momentum: float
    trend: float
    volume_ratio: float
    volatility: float
    funding_rate: float
    change_24h: float

@dataclass
class TradingSignal:
    """交易信号"""
    symbol: str
    action: str  # BUY/SELL/HOLD
    score: float
    confidence: float
    reasons: List[str]
    entry_price: float
    stop_loss: float
    take_profit: float

class DataBridge:
    """数据桥 - 打通所有模块"""
    
    def __init__(self, api=None):
        self.api = api or BinanceAPI()
        self.cache = {}
        self.cache_time = {}
        
    def get_market_data(self, symbol: str) -> MarketData:
        """获取完整市场数据"""
        try:
            ticker = self.api.get_ticker(symbol)
            klines = self.api.get_klines(symbol, '1h', 100)
            
            if not ticker or not klines:
                return self._default_data(symbol)
            
            closes = [k['close'] for k in klines]
            
            # RSI
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas[-14:]]
            losses = [-d if d < 0 else 0 for d in deltas[-14:]]
            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs))
            
            # 动量
            momentum = (closes[-1] - closes[-24]) / closes[-24] * 100 if len(closes) >= 24 else 0
            
            # 趋势
            ma7 = sum(closes[-7:]) / 7
            ma25 = sum(closes[-25:]) / 25
            trend = (ma7 - ma25) / ma25 * 100
            
            # 成交量
            volumes = [k['volume'] for k in klines]
            avg_vol = sum(volumes[-24:]) / 24
            vol_ratio = volumes[-1] / avg_vol if avg_vol > 0 else 1
            
            # 波动率
            volatility = (max(closes[-24:]) - min(closes[-24:])) / closes[-1]
            
            # 资金费率
            funding = self.api.get_funding_rate(symbol.replace('USDT', 'USD'))
            funding_rate = funding['funding_rate'] if funding else 0
            
            return MarketData(
                symbol=symbol,
                price=ticker['price'],
                rsi=rsi,
                momentum=momentum,
                trend=trend,
                volume_ratio=vol_ratio,
                volatility=volatility,
                funding_rate=funding_rate,
                change_24h=ticker['change_pct']
            )
        except Exception as e:
            return self._default_data(symbol)
    
    def _default_data(self, symbol: str) -> MarketData:
        return MarketData(
            symbol=symbol,
            price=100,
            rsi=50,
            momentum=0,
            trend=0,
            volume_ratio=1,
            volatility=0.02,
            funding_rate=0,
            change_24h=0
        )

class MultiFactorScorer:
    """多因子评分系统"""
    
    def __init__(self):
        # 动态权重
        self.weights = {
            'rsi': 0.25,
            'momentum': 0.20,
            'trend': 0.20,
            'volume': 0.15,
            'volatility': 0.10,
            'funding': 0.10
        }
        
        # 动态阈值
        self.thresholds = {
            'buy': 70,
            'sell': 30,
            'strong_buy': 85,
            'strong_sell': 15
        }
    
    def update_thresholds(self, market_regime: str):
        """根据市场环境更新阈值"""
        if market_regime == 'BULL':
            self.thresholds['buy'] = 75
            self.thresholds['sell'] = 25
            self.weights['momentum'] = 0.30
            self.weights['rsi'] = 0.15
        elif market_regime == 'BEAR':
            self.thresholds['buy'] = 65
            self.thresholds['sell'] = 35
            self.weights['rsi'] = 0.30
            self.weights['momentum'] = 0.15
        else:  # RANGE
            self.thresholds['buy'] = 70
            self.thresholds['sell'] = 30
            self.weights = {
                'rsi': 0.25,
                'momentum': 0.20,
                'trend': 0.20,
                'volume': 0.15,
                'volatility': 0.10,
                'funding': 0.10
            }
    
    def calculate_rsi_score(self, rsi: float) -> float:
        """RSI评分"""
        if rsi < 20:
            return 100
        elif rsi < 30:
            return 90
        elif rsi < 40:
            return 75
        elif rsi > 80:
            return 0
        elif rsi > 70:
            return 20
        elif rsi > 60:
            return 40
        else:
            return 50
    
    def calculate_momentum_score(self, momentum: float) -> float:
        """动量评分"""
        if momentum < -10:
            return 100
        elif momentum < -5:
            return 85
        elif momentum < -2:
            return 70
        elif momentum > 10:
            return 0
        elif momentum > 5:
            return 15
        elif momentum > 2:
            return 30
        else:
            return 50
    
    def calculate_trend_score(self, trend: float) -> float:
        """趋势评分"""
        if trend > 5:
            return 80
        elif trend > 2:
            return 65
        elif trend > 0:
            return 55
        elif trend > -2:
            return 45
        elif trend > -5:
            return 30
        else:
            return 15
    
    def calculate_volume_score(self, vol_ratio: float) -> float:
        """成交量评分"""
        if vol_ratio > 2:
            return 90
        elif vol_ratio > 1.5:
            return 75
        elif vol_ratio > 1:
            return 60
        elif vol_ratio > 0.5:
            return 40
        else:
            return 25
    
    def calculate_volatility_score(self, volatility: float) -> float:
        """波动率评分 (低波动=高评分)"""
        if volatility < 0.01:
            return 90
        elif volatility < 0.02:
            return 75
        elif volatility < 0.03:
            return 60
        elif volatility < 0.05:
            return 40
        else:
            return 25
    
    def calculate_funding_score(self, funding_rate: float) -> float:
        """资金费率评分"""
        if funding_rate > 0.001:
            return 85  # 正费率,做多有利
        elif funding_rate < -0.001:
            return 70  # 负费率,套利机会
        else:
            return 50
    
    def calculate_score(self, data: MarketData, regime: str = 'RANGE') -> float:
        """综合评分"""
        self.update_thresholds(regime)
        
        rsi_s = self.calculate_rsi_score(data.rsi)
        mom_s = self.calculate_momentum_score(data.momentum)
        trend_s = self.calculate_trend_score(data.trend)
        vol_s = self.calculate_volume_score(data.volume_ratio)
        vola_s = self.calculate_volatility_score(data.volatility)
        fund_s = self.calculate_funding_score(data.funding_rate)
        
        total = (
            rsi_s * self.weights['rsi'] +
            mom_s * self.weights['momentum'] +
            trend_s * self.weights['trend'] +
            vol_s * self.weights['volume'] +
            vola_s * self.weights['volatility'] +
            fund_s * self.weights['funding']
        )
        
        return total

class MarketEnvironmentFilter:
    """市场环境过滤器"""
    
    @staticmethod
    def detect_regime(data_list: List[MarketData]) -> str:
        """检测市场环境"""
        if not data_list:
            return 'RANGE'
        
        avg_trend = sum(d.trend for d in data_list) / len(data_list)
        avg_momentum = sum(d.momentum for d in data_list) / len(data_list)
        
        if avg_trend > 2 and avg_momentum > 2:
            return 'BULL'
        elif avg_trend < -2 and avg_momentum < -2:
            return 'BEAR'
        else:
            return 'RANGE'
    
    @staticmethod
    def filter_signals(signals: List[TradingSignal], regime: str) -> List[TradingSignal]:
        """根据环境过滤信号"""
        if regime == 'BULL':
            # 只做多
            return [s for s in signals if s.action in ['BUY', 'HOLD']]
        elif regime == 'BEAR':
            # 只做空或观望
            return [s for s in signals if s.action in ['SELL', 'HOLD']]
        else:
            return signals

class DynamicThresholds:
    """动态阈值调整"""
    
    def __init__(self):
        self.base_thresholds = {
            'buy': 70,
            'sell': 30,
            'strong_buy': 85,
            'strong_sell': 15
        }
        self.current = self.base_thresholds.copy()
    
    def adjust(self, win_rate: float, avg_return: float):
        """根据绩效调整阈值"""
        if win_rate > 0.7 and avg_return > 0.05:
            # 策略有效,收紧阈值
            self.current['buy'] = 75
            self.current['sell'] = 25
        elif win_rate < 0.4 or avg_return < -0.02:
            # 策略失效,放宽阈值
            self.current['buy'] = 65
            self.current['sell'] = 35
        else:
            # 保持不变
            self.current = self.base_thresholds.copy()
    
    def get(self) -> Dict:
        return self.current.copy()

class QMUnified:
    """
    QM Unified - 模块数据打通 + 专业策略
    """
    
    def __init__(self, capital: float = 10000):
        self.capital = capital
        self.api = BinanceAPI() if HAS_API else None
        self.bridge = DataBridge(self.api)
        self.scorer = MultiFactorScorer()
        self.filter = MarketEnvironmentFilter()
        self.thresholds = DynamicThresholds()
        
        # 持仓
        self.positions = {}
        
    def scan(self) -> List[TradingSignal]:
        """扫描机会"""
        symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
            'ADAUSDT', 'LINKUSDT', 'DOTUSDT', 'AVAXUSDT', 'ATOMUSDT'
        ]
        
        signals = []
        all_data = []
        
        for symbol in symbols:
            data = self.bridge.get_market_data(symbol)
            all_data.append(data)
            
            score = self.scorer.calculate_score(data)
            
            action = 'HOLD'
            if score >= self.thresholds.current['strong_buy']:
                action = 'STRONG_BUY'
            elif score >= self.thresholds.current['buy']:
                action = 'BUY'
            elif score <= self.thresholds.current['strong_sell']:
                action = 'STRONG_SELL'
            elif score <= self.thresholds.current['sell']:
                action = 'SELL'
            
            # 止损止盈
            if action in ['BUY', 'STRONG_BUY']:
                stop_loss = data.price * 0.98  # 2%止损
                take_profit = data.price * 1.06  # 6%止盈
            elif action in ['SELL', 'STRONG_SELL']:
                stop_loss = data.price * 1.02
                take_profit = data.price * 0.94
            else:
                stop_loss = 0
                take_profit = 0
            
            reasons = [
                f"RSI: {data.rsi:.1f}",
                f"动量: {data.momentum:+.2f}%",
                f"趋势: {data.trend:+.2f}%",
                f"评分: {score:.1f}"
            ]
            
            signals.append(TradingSignal(
                symbol=symbol.replace('USDT', ''),
                action=action,
                score=score,
                confidence=min(95, score + 10),
                reasons=reasons,
                entry_price=data.price,
                stop_loss=stop_loss,
                take_profit=take_profit
            ))
        
        # 环境过滤
        regime = self.filter.detect_regime(all_data)
        filtered = self.filter.filter_signals(signals, regime)
        
        return sorted(filtered, key=lambda x: x.score, reverse=True)
    
    def generate_report(self) -> str:
        """生成报告"""
        signals = self.scan()
        
        # 检测环境
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
        all_data = [self.bridge.get_market_data(s) for s in symbols]
        regime = self.filter.detect_regime(all_data)
        
        regime_emoji = {'BULL': '🟢', 'BEAR': '🔴', 'RANGE': '🟡'}
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              QM Unified - 模块打通 + 专业策略                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

🌐 市场环境: {regime_emoji.get(regime, '⚪')} {regime}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 多因子评分 TOP 10                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for sig in signals[:10]:
            emoji = {
                'STRONG_BUY': '🟢🟢',
                'BUY': '🟢',
                'HOLD': '🟡',
                'SELL': '🔴',
                'STRONG_SELL': '🔴🔴'
            }.get(sig.action, '⚪')
            
            report += f"{emoji} {sig.symbol:8} {sig.action:12} 评分:{sig.score:5.1f} 置信:{sig.confidence:.0f}%\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 动态阈值                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        th = self.thresholds.get()
        report += f"   买入阈值: >{th['buy']}  强买: >{th['strong_buy']}\n"
        report += f"   卖出阈值: <{th['sell']}  强卖: <{th['strong_sell']}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    📈 因子权重                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        w = self.scorer.weights
        report += f"   RSI:      {w['rsi']*100:.0f}%\n"
        report += f"   动量:     {w['momentum']*100:.0f}%\n"
        report += f"   趋势:     {w['trend']*100:.0f}%\n"
        report += f"   成交量:   {w['volume']*100:.0f}%\n"
        report += f"   波动率:   {w['volatility']*100:.0f}%\n"
        report += f"   资金费率: {w['funding']*100:.0f}%\n"
        
        report += "\n" + "=" * 70 + "\n"
        
        return report

def main():
    qm = QMUnified(10000)
    print(qm.generate_report())

if __name__ == '__main__':
    main()
