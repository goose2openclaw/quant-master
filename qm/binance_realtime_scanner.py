"""
Binance Real-Time Deep Scanner
币安全面深度扫描 + 实时机会捕捉
"""
import sys
import time
import math
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import defaultdict
import statistics

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.binance_optimizer import BinanceAPI
    HAS_API = True
except:
    HAS_API = False

@dataclass
class RealTimeSignal:
    """实时信号"""
    symbol: str
    category: str        # MAIN/ALT/MEME/LAYER1/DEFI
    type: str            # 信号类型
    action: str          # BUY/SELL
    score: float
    confidence: float
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    
    # 深度数据
    rsi_14: float
    rsi_30: float
    rsi_60: float
    
    volume_ratio: float
    momentum_1h: float
    momentum_4h: float
    momentum_1d: float
    
    funding_rate: float
    open_interest: float
    
    support: float
    resistance: float
    
    reasons: List[str]
    timestamp: float

class BinanceDeepScanner:
    """
    币安深度实时扫描器
    
    功能:
    1. 全市场扫描 (现货+合约+期权)
    2. 多维度评分
    3. 实时信号检测
    4. 机会排序和筛选
    5. 自动建议
    """
    
    def __init__(self, api=None):
        self.api = api or BinanceAPI()
        
        # 评分配置
        self.min_score = 60
        self.min_confidence = 65
        
        # 币种分类
        self.categories = {
            'MAIN': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT', 'DOTUSDT'],
            'ALT': ['AVAXUSDT', 'LINKUSDT', 'MATICUSDT', 'ATOMUSDT', 'LTCUSDT', 'UNIUSDT', 'XLMUSDT', 'ETCUSDT'],
            'LAYER1': ['SOLUSDT', 'ADAUSDT', 'AVAXUSDT', 'ATOMUSDT', 'NEARUSDT', 'APTUSDT', 'SUIUSDT', 'SEIUSDT', 'TIAUSDT', 'INJUSDT'],
            'DEFI': ['UNIUSDT', 'AAVEUSDT', 'CRVUSDT', 'MKRUSDT', 'SNXUSDT', 'COMPUSDT', 'SUSHIUSDT'],
            'MEME': ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT', 'WIFUSDT', 'BONKUSDT', 'FLOKIUSDT'],
            'GAMING': ['GALAUSDT', 'IMXUSDT', 'MANAUSDT', 'SANDUSDT', 'AXSUSDT'],
            'AI': ['FETUSDT', 'RNDRUSDT', 'OCEANUSDT', 'AGIXUSDT', 'NMRUSDT'],
        }
        
        # 钱包套利机会币种
        self.funding_targets = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
        
        # 扫描历史
        self.scan_history = []
    
    def get_comprehensive_data(self, symbol: str) -> Optional[Dict]:
        """获取综合数据"""
        try:
            # K线数据
            klines_1h = self.api.get_klines(symbol, '1h', 100)
            klines_4h = self.api.get_klines(symbol, '4h', 100)
            klines_1d = self.api.get_klines(symbol, '1d', 100)
            
            if not klines_1h:
                return None
            
            # ticker数据
            ticker = self.api.get_ticker(symbol)
            
            # 解析数据
            closes_1h = [k['close'] for k in klines_1h]
            highs_1h = [k['high'] for k in klines_1h]
            lows_1h = [k['low'] for k in klines_1h]
            volumes_1h = [k['volume'] for k in klines_1h]
            
            closes_4h = [k['close'] for k in klines_4h] if klines_4h else closes_1h
            closes_1d = [k['close'] for k in klines_1d] if klines_1d else closes_1h
            
            current_price = ticker.get('price', closes_1h[-1])
            
            return {
                'symbol': symbol,
                'price': current_price,
                'change_24h': ticker.get('priceChangePercent', 0),
                'change_1h': (closes_1h[-1] - closes_1h[-2]) / closes_1h[-2] * 100 if len(closes_1h) >= 2 else 0,
                
                # K线数据
                'closes_1h': closes_1h,
                'closes_4h': closes_4h,
                'closes_1d': closes_1d,
                'highs_1h': highs_1h,
                'lows_1h': lows_1h,
                'volumes_1h': volumes_1h,
                
                # 成交量
                'volume_24h': ticker.get('volume', 0),
                'quote_volume_24h': ticker.get('quoteVolume', 0),
            }
        except Exception as e:
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
    
    def calc_support_resistance(self, highs: List[float], lows: List[float], closes: List[float], price: float) -> Dict:
        """计算支撑阻力"""
        # 近期高低点
        high_20 = max(highs[-20:])
        low_20 = min(lows[-20:])
        
        # 均线支撑阻力
        ma7 = self.calc_ma(closes, 7)
        ma25 = self.calc_ma(closes, 25)
        ma99 = self.calc_ma(closes, 99)
        
        return {
            'resistance': high_20,
            'support': low_20,
            'ma7': ma7,
            'ma25': ma25,
            'ma99': ma99
        }
    
    def analyze_momentum(self, closes_1h: List[float], closes_4h: List[float], closes_1d: List[float]) -> Dict:
        """分析动量"""
        mom_1h = (closes_1h[-1] - closes_1h[-2]) / closes_1h[-2] * 100 if len(closes_1h) >= 2 else 0
        mom_4h = (closes_1h[-1] - closes_1h[-5]) / closes_1h[-5] * 100 if len(closes_1h) >= 5 else 0
        mom_1d = (closes_1h[-1] - closes_1h[-25]) / closes_1h[-25] * 100 if len(closes_1h) >= 25 else 0
        
        return {
            'momentum_1h': mom_1h,
            'momentum_4h': mom_4h,
            'momentum_1d': mom_1d
        }
    
    def detect_all_signals(self, data: Dict) -> List[RealTimeSignal]:
        """检测所有信号"""
        signals = []
        
        symbol = data['symbol']
        price = data['price']
        closes_1h = data['closes_1h']
        highs_1h = data['highs_1h']
        lows_1h = data['lows_1h']
        volumes_1h = data['volumes_1h']
        
        # RSI多周期
        rsi_14 = self.calc_rsi(closes_1h, 14)
        rsi_30 = self.calc_rsi(closes_1h, 30)
        rsi_60 = self.calc_rsi(closes_1h, 60)
        
        # 动量
        momentum = self.analyze_momentum(closes_1h, data['closes_4h'], data['closes_1d'])
        
        # 成交量
        vol_avg = sum(volumes_1h[-20:]) / 20
        vol_ratio = volumes_1h[-1] / vol_avg if vol_avg > 0 else 1
        
        # 支撑阻力
        sr = self.calc_support_resistance(highs_1h, lows_1h, closes_1h, price)
        
        # 判断币种分类
        category = 'MAIN'
        for cat, symbols in self.categories.items():
            if symbol in symbols:
                category = cat
                break
        
        # === 信号1: RSI超卖反弹 ===
        if rsi_14 < 30 and momentum['momentum_1d'] > -10:
            score = 80 + (30 - rsi_14) * 2
            signals.append(RealTimeSignal(
                symbol=symbol.replace('USDT', ''),
                category=category,
                type='RSI_OVERSOLD',
                action='BUY',
                score=min(100, score),
                confidence=70 + (30 - rsi_14),
                entry=price,
                stop_loss=price * 0.97,
                take_profit=price * 1.12,
                risk_reward=3.5,
                rsi_14=rsi_14, rsi_30=rsi_30, rsi_60=rsi_60,
                volume_ratio=vol_ratio,
                momentum_1h=momentum['momentum_1h'],
                momentum_4h=momentum['momentum_4h'],
                momentum_1d=momentum['momentum_1d'],
                funding_rate=0, open_interest=0,
                support=sr['support'],
                resistance=sr['resistance'],
                reasons=[f'RSI14超卖{rsi_14:.1f}', '反弹概率高'],
                timestamp=time.time()
            ))
        
        # === 信号2: RSI超买回调 ===
        if rsi_14 > 70 and momentum['momentum_1d'] < 10:
            score = 80 + (rsi_14 - 70) * 2
            signals.append(RealTimeSignal(
                symbol=symbol.replace('USDT', ''),
                category=category,
                type='RSI_OVERBOUGHT',
                action='SELL',
                score=min(100, score),
                confidence=70 + (rsi_14 - 70),
                entry=price,
                stop_loss=price * 1.03,
                take_profit=price * 0.88,
                risk_reward=3.5,
                rsi_14=rsi_14, rsi_30=rsi_30, rsi_60=rsi_60,
                volume_ratio=vol_ratio,
                momentum_1h=momentum['momentum_1h'],
                momentum_4h=momentum['momentum_4h'],
                momentum_1d=momentum['momentum_1d'],
                funding_rate=0, open_interest=0,
                support=sr['support'],
                resistance=sr['resistance'],
                reasons=[f'RSI14超买{rsi_14:.1f}', '回调概率高'],
                timestamp=time.time()
            ))
        
        # === 信号3: 均线金叉 ===
        ma7 = sr['ma7']
        ma25 = sr['ma25']
        ma99 = sr['ma99']
        
        if ma7 > ma25 > ma99 and price > ma7:
            score = 75 + momentum['momentum_4h'] * 3
            signals.append(RealTimeSignal(
                symbol=symbol.replace('USDT', ''),
                category=category,
                type='GOLDEN_CROSS',
                action='BUY',
                score=min(100, score),
                confidence=80,
                entry=price,
                stop_loss=ma25 * 0.98,
                take_profit=ma7 * 1.15,
                risk_reward=4.0,
                rsi_14=rsi_14, rsi_30=rsi_30, rsi_60=rsi_60,
                volume_ratio=vol_ratio,
                momentum_1h=momentum['momentum_1h'],
                momentum_4h=momentum['momentum_4h'],
                momentum_1d=momentum['momentum_1d'],
                funding_rate=0, open_interest=0,
                support=sr['support'],
                resistance=sr['resistance'],
                reasons=['均线多头排列', 'MA7>MA25>MA99'],
                timestamp=time.time()
            ))
        
        # === 信号4: 均线死叉 ===
        if ma7 < ma25 < ma99 and price < ma7:
            score = 75 + abs(momentum['momentum_4h']) * 3
            signals.append(RealTimeSignal(
                symbol=symbol.replace('USDT', ''),
                category=category,
                type='DEATH_CROSS',
                action='SELL',
                score=min(100, score),
                confidence=80,
                entry=price,
                stop_loss=ma25 * 1.02,
                take_profit=ma7 * 0.85,
                risk_reward=4.0,
                rsi_14=rsi_14, rsi_30=rsi_30, rsi_60=rsi_60,
                volume_ratio=vol_ratio,
                momentum_1h=momentum['momentum_1h'],
                momentum_4h=momentum['momentum_4h'],
                momentum_1d=momentum['momentum_1d'],
                funding_rate=0, open_interest=0,
                support=sr['support'],
                resistance=sr['resistance'],
                reasons=['均线空头排列', 'MA7<MA25<MA99'],
                timestamp=time.time()
            ))
        
        # === 信号5: 突破20日新高 ===
        high_20 = sr['resistance']
        if price > high_20 * 1.01 and vol_ratio > 1.5:
            score = 75 + vol_ratio * 10
            signals.append(RealTimeSignal(
                symbol=symbol.replace('USDT', ''),
                category=category,
                type='BREAKOUT_HIGH',
                action='BUY',
                score=min(100, score),
                confidence=min(95, 65 + vol_ratio * 15),
                entry=price,
                stop_loss=high_20 * 0.98,
                take_profit=price * 1.15,
                risk_reward=4.0,
                rsi_14=rsi_14, rsi_30=rsi_30, rsi_60=rsi_60,
                volume_ratio=vol_ratio,
                momentum_1h=momentum['momentum_1h'],
                momentum_4h=momentum['momentum_4h'],
                momentum_1d=momentum['momentum_1d'],
                funding_rate=0, open_interest=0,
                support=sr['support'],
                resistance=sr['resistance'],
                reasons=[f'突破20日高${high_20:.2f}', f'量比{vol_ratio:.1f}x'],
                timestamp=time.time()
            ))
        
        # === 信号6: 成交量暴增 ===
        if vol_ratio > 3 and abs(momentum['momentum_1h']) > 0.5:
            action = 'BUY' if momentum['momentum_1h'] > 0 else 'SELL'
            score = 70 + vol_ratio * 8 + abs(momentum['momentum_1h']) * 10
            signals.append(RealTimeSignal(
                symbol=symbol.replace('USDT', ''),
                category=category,
                type='VOLUME_SURGE',
                action=action,
                score=min(100, score),
                confidence=min(95, 70 + vol_ratio * 5),
                entry=price,
                stop_loss=price * 0.98 if action == 'BUY' else price * 1.02,
                take_profit=price * 1.15 if action == 'BUY' else price * 0.85,
                risk_reward=4.0,
                rsi_14=rsi_14, rsi_30=rsi_30, rsi_60=rsi_60,
                volume_ratio=vol_ratio,
                momentum_1h=momentum['momentum_1h'],
                momentum_4h=momentum['momentum_4h'],
                momentum_1d=momentum['momentum_1d'],
                funding_rate=0, open_interest=0,
                support=sr['support'],
                resistance=sr['resistance'],
                reasons=[f'成交量暴增{vol_ratio:.1f}x', f'动量{momentum["momentum_1h"]:.2f}%'],
                timestamp=time.time()
            ))
        
        # === 信号7: 趋势加速 ===
        if momentum['momentum_4h'] > 5 and momentum['momentum_4h'] > momentum['momentum_1d']:
            score = 70 + momentum['momentum_4h'] * 5
            signals.append(RealTimeSignal(
                symbol=symbol.replace('USDT', ''),
                category=category,
                type='TREND_ACCEL_UP',
                action='BUY',
                score=min(100, score),
                confidence=80,
                entry=price,
                stop_loss=price * 0.97,
                take_profit=price * 1.20,
                risk_reward=5.0,
                rsi_14=rsi_14, rsi_30=rsi_30, rsi_60=rsi_60,
                volume_ratio=vol_ratio,
                momentum_1h=momentum['momentum_1h'],
                momentum_4h=momentum['momentum_4h'],
                momentum_1d=momentum['momentum_1d'],
                funding_rate=0, open_interest=0,
                support=sr['support'],
                resistance=sr['resistance'],
                reasons=[f'4H动量{momentum["momentum_4h"]:.1f}%', '趋势加速上涨'],
                timestamp=time.time()
            ))
        
        if momentum['momentum_4h'] < -5 and momentum['momentum_4h'] < momentum['momentum_1d']:
            score = 70 + abs(momentum['momentum_4h']) * 5
            signals.append(RealTimeSignal(
                symbol=symbol.replace('USDT', ''),
                category=category,
                type='TREND_ACCEL_DOWN',
                action='SELL',
                score=min(100, score),
                confidence=80,
                entry=price,
                stop_loss=price * 1.03,
                take_profit=price * 0.80,
                risk_reward=5.0,
                rsi_14=rsi_14, rsi_30=rsi_30, rsi_60=rsi_60,
                volume_ratio=vol_ratio,
                momentum_1h=momentum['momentum_1h'],
                momentum_4h=momentum['momentum_4h'],
                momentum_1d=momentum['momentum_1d'],
                funding_rate=0, open_interest=0,
                support=sr['support'],
                resistance=sr['resistance'],
                reasons=[f'4H动量{momentum["momentum_4h"]:.1f}%', '趋势加速下跌'],
                timestamp=time.time()
            ))
        
        # === 信号8: 支撑位反弹 ===
        if abs(price - sr['support']) / price < 0.02 and rsi_14 < 45:
            score = 75 + (45 - rsi_14) * 2
            signals.append(RealTimeSignal(
                symbol=symbol.replace('USDT', ''),
                category=category,
                type='SUPPORT_BOUNCE',
                action='BUY',
                score=min(100, score),
                confidence=75,
                entry=price,
                stop_loss=sr['support'] * 0.97,
                take_profit=price * 1.12,
                risk_reward=3.0,
                rsi_14=rsi_14, rsi_30=rsi_30, rsi_60=rsi_60,
                volume_ratio=vol_ratio,
                momentum_1h=momentum['momentum_1h'],
                momentum_4h=momentum['momentum_4h'],
                momentum_1d=momentum['momentum_1d'],
                funding_rate=0, open_interest=0,
                support=sr['support'],
                resistance=sr['resistance'],
                reasons=[f'支撑位${sr["support"]:.4f}', 'RSI反弹信号'],
                timestamp=time.time()
            ))
        
        return signals
    
    def scan_all(self) -> List[RealTimeSignal]:
        """扫描所有币种"""
        all_signals = []
        
        # 所有币种
        all_symbols = (
            ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT', 'DOTUSDT'] +  # MAIN
            ['AVAXUSDT', 'LINKUSDT', 'MATICUSDT', 'ATOMUSDT', 'LTCUSDT', 'UNIUSDT', 'XLMUSDT', 'ETCUSDT'] +  # ALT
            ['NEARUSDT', 'APTUSDT', 'SUIUSDT', 'SEIUSDT', 'TIAUSDT', 'INJUSDT', 'JUPUSDT', 'WLDUSDT'] +  # LAYER1
            ['AAVEUSDT', 'CRVUSDT', 'MKRUSDT', 'SNXUSDT', 'COMPUSDT', 'SUSHIUSDT', 'LDOUSDT', 'RPLUSDT'] +  # DEFI
            ['SHIBUSDT', 'PEPEUSDT', 'WIFUSDT', 'BONKUSDT', 'FLOKIUSDT', 'APEFEUSDT'] +  # MEME
            ['GALAUSDT', 'IMXUSDT', 'MANAUSDT', 'SANDUSDT', 'AXSUSDT'] +  # GAMING
            ['FETUSDT', 'RNDRUSDT', 'OCEANUSDT', 'AGIXUSDT', 'NMRUSDT']  # AI
        )
        
        print(f"\n🔍 开始深度扫描 {len(all_symbols)} 个币种...")
        
        for i, symbol in enumerate(all_symbols, 1):
            if i % 10 == 0:
                print(f"   进度: {i}/{len(all_symbols)}")
            
            data = self.get_comprehensive_data(symbol)
            if data:
                signals = self.detect_all_signals(data)
                all_signals.extend(signals)
        
        # 过滤和排序
        filtered = [s for s in all_signals if s.score >= self.min_score]
        filtered.sort(key=lambda x: x.score, reverse=True)
        
        print(f"\n✅ 扫描完成: {len(all_signals)}个信号, {len(filtered)}个满足条件")
        
        return filtered
    
    def scan_by_category(self, category: str) -> List[RealTimeSignal]:
        """按分类扫描"""
        symbols = self.categories.get(category, [])
        all_signals = []
        
        for symbol in symbols:
            data = self.get_comprehensive_data(symbol)
            if data:
                signals = self.detect_all_signals(data)
                all_signals.extend(signals)
        
        filtered = [s for s in all_signals if s.score >= self.min_score]
        filtered.sort(key=lambda x: x.score, reverse=True)
        
        return filtered
    
    def generate_report(self) -> str:
        """生成完整报告"""
        signals = self.scan_all()
        
        # 分组
        by_category = defaultdict(list)
        by_type = defaultdict(list)
        buys = []
        sells = []
        
        for sig in signals:
            by_category[sig.category].append(sig)
            by_type[sig.type].append(sig)
            if sig.action == 'BUY':
                buys.append(sig)
            else:
                sells.append(sig)
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       🔍 Binance Real-Time Deep Scanner - 深度实时扫描                ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏰ 扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 扫描概览                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   总信号: {len(signals)}个
   🟢 买入: {len(buys)}个
   🔴 卖出: {len(sells)}个
   分类: {len(by_category)}种
   类型: {len(by_type)}种

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🟢 TOP 买入信号                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for i, sig in enumerate(buys[:10], 1):
            report += f"""
   {i}. 🟢 {sig.symbol:8} [{sig.category:6}] {sig.type:20}
      评分: {sig.score:.1f} | 置信: {sig.confidence:.0f}%
      入场: ${sig.entry:.4f} | 目标: ${sig.take_profit:.4f}
      RSI: {sig.rsi_14:.1f} | 动量1H: {sig.momentum_1h:+.2f}%
      支撑: ${sig.support:.4f} | 阻力: ${sig.resistance:.4f}
"""
            for reason in sig.reasons:
                report += f"      → {reason}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔴 TOP 卖出信号                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for i, sig in enumerate(sells[:10], 1):
            report += f"""
   {i}. 🔴 {sig.symbol:8} [{sig.category:6}] {sig.type:20}
      评分: {sig.score:.1f} | 置信: {sig.confidence:.0f}%
      入场: ${sig.entry:.4f} | 目标: ${sig.take_profit:.4f}
      RSI: {sig.rsi_14:.1f} | 动量1H: {sig.momentum_1h:+.2f}%
      支撑: ${sig.support:.4f} | 阻力: ${sig.resistance:.4f}
"""
            for reason in sig.reasons:
                report += f"      → {reason}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 分类分布                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for cat, sigs in sorted(by_category.items(), key=lambda x: -len(x[1])):
            buy_count = len([s for s in sigs if s.action == 'BUY'])
            sell_count = len([s for s in sigs if s.action == 'SELL'])
            report += f"   {cat:8} {len(sigs):2}个 (🟢{buy_count} 🔴{sell_count})\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 类型分布                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for sig_type, sigs in sorted(by_type.items(), key=lambda x: -len(x[1])):
            buy_count = len([s for s in sigs if s.action == 'BUY'])
            sell_count = len([s for s in sigs if s.action == 'SELL'])
            report += f"   {sig_type:20} {len(sigs):2}个 (🟢{buy_count} 🔴{sell_count})\n"
        
        report += "\n" + "=" * 66 + "\n"
        
        return report
    
    def run(self):
        """运行扫描"""
        print(self.generate_report())

def main():
    scanner = BinanceDeepScanner()
    scanner.run()

if __name__ == '__main__':
    main()
