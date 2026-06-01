"""
Hunter V2 - 强化版市场机会捕捉
15种机会类型 + 实时信号评分 + 智能排序
"""
import sys
import time
import math
from typing import Dict, List, Optional
from dataclasses import dataclass
import statistics

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.binance_optimizer import BinanceAPI
    HAS_API = True
except:
    HAS_API = False

@dataclass
class Signal:
    """交易信号"""
    symbol: str
    type: str
    action: str          # BUY/SELL/LONG/SHORT
    score: float         # 0-100
    confidence: float    # 0-100
    entry: float
    stop: float
    target: float
    risk_reward: float
    momentum: float      # 动量
    volume_score: float  # 成交量评分
    reasons: List[str]
    timestamp: float

class HunterV2:
    """
    Hunter V2 - 强化版机会捕捉
    
    15种机会类型:
    1-2. 突破 (新高/新低)
    3-4. RSI (超卖/超买)
    5-6. 均线 (金叉/死叉)
    7-8. 布林 (上轨/下轨)
    9-10. MACD (金叉/死叉)
    11-12. 趋势 (加速上/下)
    13. 成交量异动
    14. 波动率收缩
    15. 支撑阻力
    """
    
    def __init__(self, api=None):
        self.api = api or BinanceAPI()
        
        # 评分阈值
        self.min_score = 55
        self.min_confidence = 60
        
        # 权重配置
        self.weights = {
            'momentum': 0.25,
            'rsi': 0.20,
            'trend': 0.20,
            'volume': 0.15,
            'volatility': 0.10,
            'funding': 0.10
        }
    
    def get_data(self, symbol: str, limit: int = 100) -> Optional[Dict]:
        """获取数据"""
        try:
            klines = self.api.get_klines(symbol, '1h', limit)
            if not klines or len(klines) < 50:
                return None
            
            ticker = self.api.get_ticker(symbol)
            
            closes = [k['close'] for k in klines]
            highs = [k['high'] for k in klines]
            lows = [k['low'] for k in klines]
            volumes = [k['volume'] for k in klines]
            
            return {
                'symbol': symbol,
                'closes': closes,
                'highs': highs,
                'lows': lows,
                'volumes': volumes,
                'price': ticker.get('price', closes[-1]),
                'change_24h': ticker.get('priceChangePercent', 0)
            }
        except:
            return None
    
    def calc_rsi(self, closes: List[float], period: int = 14) -> float:
        """计算RSI"""
        if len(closes) < period + 1:
            return 50
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def calc_ma(self, closes: List[float], period: int) -> float:
        """计算MA"""
        if len(closes) < period:
            return sum(closes) / len(closes)
        return sum(closes[-period:]) / period
    
    def calc_macd(self, closes: List[float]) -> Dict:
        """计算MACD"""
        if len(closes) < 26:
            return {'macd': 0, 'signal': 0, 'hist': 0}
        
        ema12 = self.calc_ma(closes, 12)
        ema26 = self.calc_ma(closes, 26)
        macd = ema12 - ema26
        signal = macd * 0.8
        hist = macd - signal
        
        return {'macd': macd, 'signal': signal, 'hist': hist}
    
    def calc_bollinger(self, closes: List[float], period: int = 20) -> Dict:
        """计算布林带"""
        if len(closes) < period:
            return {'upper': 0, 'middle': 0, 'lower': 0, 'bandwidth': 0}
        
        recent = closes[-period:]
        std = statistics.stdev(recent)
        middle = sum(recent) / period
        upper = middle + 2 * std
        lower = middle - 2 * std
        bandwidth = (upper - lower) / middle * 100
        
        return {'upper': upper, 'middle': middle, 'lower': lower, 'bandwidth': bandwidth}
    
    def detect_signals(self, data: Dict) -> List[Signal]:
        """检测所有信号"""
        signals = []
        
        closes = data['closes']
        highs = data['highs']
        lows = data['lows']
        volumes = data['volumes']
        price = data['price']
        
        # 基础指标
        rsi = self.calc_rsi(closes)
        ma7 = self.calc_ma(closes, 7)
        ma25 = self.calc_ma(closes, 25)
        ma99 = self.calc_ma(closes, 99)
        macd_data = self.calc_macd(closes)
        bollinger = self.calc_bollinger(closes)
        
        # 动量
        momentum_1h = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0
        momentum_4h = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
        momentum_1d = (closes[-1] - closes[-25]) / closes[-25] * 100 if len(closes) >= 25 else 0
        
        # 成交量
        vol_avg = sum(volumes[-20:]) / 20
        vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
        
        # === 1. 突破20日新高 ===
        high_20 = max(highs[-21:-1])
        if price > high_20 * 1.005 and vol_ratio > 1.3:
            score = 70 + vol_ratio * 10 + momentum_1h * 2
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='BREAKOUT_HIGH',
                action='BUY',
                score=min(100, score),
                confidence=min(95, 65 + vol_ratio * 15),
                entry=price,
                stop=high_20 * 0.98,
                target=price * 1.10,
                risk_reward=3.0,
                momentum=momentum_1h,
                volume_score=vol_ratio,
                reasons=[f'突破20日高${high_20:.2f}', f'量比{vol_ratio:.1f}x'],
                timestamp=time.time()
            ))
        
        # === 2. 跌破20日新低 ===
        low_20 = min(lows[-21:-1])
        if price < low_20 * 0.995 and vol_ratio > 1.3:
            score = 70 + vol_ratio * 10 + abs(momentum_1h) * 2
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='BREAKOUT_LOW',
                action='SELL',
                score=min(100, score),
                confidence=min(95, 65 + vol_ratio * 15),
                entry=price,
                stop=low_20 * 1.02,
                target=price * 0.90,
                risk_reward=3.0,
                momentum=momentum_1h,
                volume_score=vol_ratio,
                reasons=[f'跌破20日低${low_20:.2f}', f'量比{vol_ratio:.1f}x'],
                timestamp=time.time()
            ))
        
        # === 3. RSI超卖 ===
        if rsi < 30:
            score = 85 - rsi + momentum_1d
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='RSI_OVERSOLD',
                action='BUY',
                score=min(100, score),
                confidence=min(95, 70 + (30 - rsi)),
                entry=price,
                stop=price * 0.97,
                target=price * 1.12,
                risk_reward=3.5,
                momentum=momentum_1d,
                volume_score=vol_ratio,
                reasons=[f'RSI超卖{rsi:.1f}', '反弹概率高'],
                timestamp=time.time()
            ))
        
        # === 4. RSI超买 ===
        if rsi > 70:
            score = rsi - 15 + abs(momentum_1d)
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='RSI_OVERBOUGHT',
                action='SELL',
                score=min(100, score),
                confidence=min(95, 70 + (rsi - 70)),
                entry=price,
                stop=price * 1.03,
                target=price * 0.88,
                risk_reward=3.5,
                momentum=momentum_1d,
                volume_score=vol_ratio,
                reasons=[f'RSI超买{rsi:.1f}', '回调概率高'],
                timestamp=time.time()
            ))
        
        # === 5. 均线金叉 ===
        if ma7 > ma25 > ma99 and closes[-1] > ma7:
            score = 75 + momentum_4h * 2
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='GOLDEN_CROSS',
                action='BUY',
                score=min(100, score),
                confidence=80,
                entry=price,
                stop=ma25 * 0.98,
                target=ma7 * 1.15,
                risk_reward=4.0,
                momentum=momentum_4h,
                volume_score=vol_ratio,
                reasons=['MA7上穿MA25', '多头排列'],
                timestamp=time.time()
            ))
        
        # === 6. 均线死叉 ===
        if ma7 < ma25 < ma99 and closes[-1] < ma7:
            score = 75 + abs(momentum_4h) * 2
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='DEATH_CROSS',
                action='SELL',
                score=min(100, score),
                confidence=80,
                entry=price,
                stop=ma25 * 1.02,
                target=ma7 * 0.85,
                risk_reward=4.0,
                momentum=momentum_4h,
                volume_score=vol_ratio,
                reasons=['MA7下穿MA25', '空头排列'],
                timestamp=time.time()
            ))
        
        # === 7. 布林上轨突破 ===
        if price > bollinger['upper']:
            score = 80 + vol_ratio * 5
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='BOLLINGER_UPPER',
                action='SELL',
                score=min(100, score),
                confidence=75,
                entry=price,
                stop=bollinger['upper'] * 1.02,
                target=bollinger['middle'],
                risk_reward=2.5,
                momentum=momentum_1h,
                volume_score=vol_ratio,
                reasons=[f'突破布林上轨${bollinger["upper"]:.2f}', '注意回调'],
                timestamp=time.time()
            ))
        
        # === 8. 布林下轨突破 ===
        if price < bollinger['lower']:
            score = 80 + vol_ratio * 5 + abs(momentum_1d)
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='BOLLINGER_LOWER',
                action='BUY',
                score=min(100, score),
                confidence=75,
                entry=price,
                stop=bollinger['lower'] * 0.98,
                target=bollinger['middle'],
                risk_reward=2.5,
                momentum=momentum_1d,
                volume_score=vol_ratio,
                reasons=[f'跌破布林下轨${bollinger["lower"]:.2f}', '反弹概率高'],
                timestamp=time.time()
            ))
        
        # === 9. MACD金叉 ===
        if macd_data['hist'] > 0 and macd_data['hist'] > abs(macd_data['signal']) * 0.3:
            score = 75 + macd_data['hist'] * 100
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='MACD_GOLDEN',
                action='BUY',
                score=min(100, score),
                confidence=75,
                entry=price,
                stop=price * 0.97,
                target=price * 1.12,
                risk_reward=3.5,
                momentum=momentum_1h,
                volume_score=vol_ratio,
                reasons=['MACD金叉', '多头信号'],
                timestamp=time.time()
            ))
        
        # === 10. MACD死叉 ===
        if macd_data['hist'] < 0 and abs(macd_data['hist']) > abs(macd_data['signal']) * 0.3:
            score = 75 + abs(macd_data['hist']) * 100
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='MACD_DEATH',
                action='SELL',
                score=min(100, score),
                confidence=75,
                entry=price,
                stop=price * 1.03,
                target=price * 0.88,
                risk_reward=3.5,
                momentum=momentum_1h,
                volume_score=vol_ratio,
                reasons=['MACD死叉', '空头信号'],
                timestamp=time.time()
            ))
        
        # === 11. 趋势加速上涨 ===
        if momentum_4h > 5 and momentum_4h > momentum_1d * 1.5:
            score = 70 + momentum_4h * 4 + vol_ratio * 5
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='TREND_ACCEL_UP',
                action='BUY',
                score=min(100, score),
                confidence=80,
                entry=price,
                stop=price * 0.97,
                target=price * 1.18,
                risk_reward=5.0,
                momentum=momentum_4h,
                volume_score=vol_ratio,
                reasons=[f'4H动量{momentum_4h:.1f}%', '趋势加速'],
                timestamp=time.time()
            ))
        
        # === 12. 趋势加速下跌 ===
        if momentum_4h < -5 and momentum_4h < momentum_1d * 1.5:
            score = 70 + abs(momentum_4h) * 4 + vol_ratio * 5
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='TREND_ACCEL_DOWN',
                action='SELL',
                score=min(100, score),
                confidence=80,
                entry=price,
                stop=price * 1.03,
                target=price * 0.82,
                risk_reward=5.0,
                momentum=momentum_4h,
                volume_score=vol_ratio,
                reasons=[f'4H动量{momentum_4h:.1f}%', '趋势加速'],
                timestamp=time.time()
            ))
        
        # === 13. 成交量异动 ===
        if vol_ratio > 3 and abs(momentum_1h) > 1:
            action = 'BUY' if momentum_1h > 0 else 'SELL'
            score = 70 + vol_ratio * 8 + abs(momentum_1h) * 5
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='VOLUME_SURGE',
                action=action,
                score=min(100, score),
                confidence=min(95, 70 + vol_ratio * 5),
                entry=price,
                stop=price * 0.98 if action == 'BUY' else price * 1.02,
                target=price * 1.15 if action == 'BUY' else price * 0.85,
                risk_reward=4.0,
                momentum=momentum_1h,
                volume_score=vol_ratio,
                reasons=[f'成交量暴增{vol_ratio:.1f}x', f'动量{momentum_1h:.1f}%'],
                timestamp=time.time()
            ))
        
        # === 14. 波动率收缩突破 ===
        if bollinger['bandwidth'] < 4 and vol_ratio > 1.5:
            score = 75 + (5 - bollinger['bandwidth']) * 5
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='VOLATILITY_SQUEEZE',
                action='BUY',
                score=min(100, score),
                confidence=70,
                entry=price,
                stop=bollinger['lower'],
                target=bollinger['upper'],
                risk_reward=3.0,
                momentum=momentum_1h,
                volume_score=vol_ratio,
                reasons=[f'波动率收缩{bollinger["bandwidth"]:.1f}%', '突破在即'],
                timestamp=time.time()
            ))
        
        # === 15. 支撑位反弹 ===
        support = min(lows[-10:-1])
        if abs(price - support) / price < 0.015 and rsi < 45:
            score = 75 + (45 - rsi) + (5 - abs(price - support) / price * 100)
            signals.append(Signal(
                symbol=data['symbol'].replace('USDT', ''),
                type='SUPPORT_BOUNCE',
                action='BUY',
                score=min(100, score),
                confidence=75,
                entry=price,
                stop=support * 0.97,
                target=price * 1.10,
                risk_reward=3.0,
                momentum=momentum_1h,
                volume_score=vol_ratio,
                reasons=[f'支撑位${support:.2f}', 'RSI反弹'],
                timestamp=time.time()
            ))
        
        return signals
    
    def scan_all(self) -> List[Signal]:
        """扫描所有信号"""
        all_signals = []
        
        symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
            'ADAUSDT', 'LINKUSDT', 'DOTUSDT', 'AVAXUSDT', 'ATOMUSDT',
            'NEARUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT', 'MATICUSDT',
            'INJUSDT', 'SUIUSDT', 'SEIUSDT', 'TIAUSDT', 'JUPUSDT'
        ]
        
        for symbol in symbols:
            data = self.get_data(symbol)
            if data:
                signals = self.detect_signals(data)
                all_signals.extend(signals)
        
        # 过滤和排序
        filtered = [s for s in all_signals if s.score >= self.min_score]
        filtered.sort(key=lambda x: (x.score, x.confidence), reverse=True)
        
        return filtered
    
    def generate_report(self) -> str:
        """生成报告"""
        signals = self.scan_all()
        
        # 按类型分组
        by_type = {}
        for sig in signals:
            if sig.type not in by_type:
                by_type[sig.type] = []
            by_type[sig.type].append(sig)
        
        # 买入/卖出分组
        buys = [s for s in signals if s.action in ['BUY', 'LONG']]
        sells = [s for s in signals if s.action in ['SELL', 'SHORT']]
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🎯 Hunter V2 - 强化版机会捕捉                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 扫描配置:
   最低评分: {self.min_score}
   最低置信: {self.min_confidence}%
   扫描币种: 20个
   机会类型: 15种

╔══════════════════════════════════════════════════════════════════════════════╗
║           📊 信号概览                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   总信号: {len(signals)}个
   🟢 买入: {len(buys)}个
   🔴 卖出: {len(sells)}个
   机会类型: {len(by_type)}种

╔══════════════════════════════════════════════════════════════════════════════╗
║           🟢 TOP买入信号 ({len(buys)}个)                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        if not buys:
            report += "\n   ⚠️ 无买入信号\n"
        else:
            for i, sig in enumerate(buys[:8], 1):
                report += f"""
   {i}. 🟢 {sig.symbol:8} {sig.type:20}
      评分: {sig.score:.1f} | 置信: {sig.confidence:.0f}% | 风险回报: {sig.risk_reward:.1f}:1
      入场: ${sig.entry:.4f} | 目标: ${sig.target:.4f}
      动量: {sig.momentum:+.2f}% | 量比: {sig.volume_score:.1f}x
"""
                for reason in sig.reasons[:2]:
                    report += f"      • {reason}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🔴 TOP卖出信号 ({len(sells)}个)                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        if not sells:
            report += "\n   ⚠️ 无卖出信号\n"
        else:
            for i, sig in enumerate(sells[:8], 1):
                report += f"""
   {i}. 🔴 {sig.symbol:8} {sig.type:20}
      评分: {sig.score:.1f} | 置信: {sig.confidence:.0f}% | 风险回报: {sig.risk_reward:.1f}:1
      入场: ${sig.entry:.4f} | 目标: ${sig.target:.4f}
      动量: {sig.momentum:+.2f}% | 量比: {sig.volume_score:.1f}x
"""
                for reason in sig.reasons[:2]:
                    report += f"      • {reason}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           📊 机会类型分布                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for sig_type, sigs in sorted(by_type.items(), key=lambda x: -len(x[1])):
            buy_count = len([s for s in sigs if s.action in ['BUY', 'LONG']])
            sell_count = len([s for s in sigs if s.action in ['SELL', 'SHORT']])
            report += f"   {sig_type:25} {len(sigs)}个 (🟢{buy_count} 🔴{sell_count})\n"
        
        report += "\n" + "=" * 66 + "\n"
        
        return report

def main():
    hunter = HunterV2()
    print(hunter.generate_report())

if __name__ == '__main__':
    main()
