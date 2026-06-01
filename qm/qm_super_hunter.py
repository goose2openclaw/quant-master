"""
QM Super Hunter - 超级机会猎手
增强版市场机会捕捉 - 10种机会类型
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
class Opportunity:
    """机会"""
    symbol: str
    type: str
    action: str
    score: float
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    reasons: List[str]

class SuperHunter:
    """
    超级机会猎手 - 10种机会类型
    """
    
    def __init__(self, api=None):
        self.api = api or BinanceAPI()
        self.min_score = 60
        self.min_confidence = 65
    
    def get_klines(self, symbol: str, limit: int = 100) -> List[Dict]:
        """获取K线"""
        try:
            return self.api.get_klines(symbol, '1h', limit) or []
        except:
            return []
    
    def get_ticker(self, symbol: str) -> Dict:
        """获取行情"""
        try:
            return self.api.get_ticker(symbol) or {}
        except:
            return {}
    
    def detect_all_opportunities(self, symbol: str) -> List[Opportunity]:
        """检测所有机会"""
        opportunities = []
        
        klines = self.get_klines(symbol)
        ticker = self.get_ticker(symbol)
        
        if not klines or len(klines) < 20:
            return opportunities
        
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        volumes = [k['volume'] for k in klines]
        
        current_price = ticker.get('price', closes[-1])
        
        # 1. 突破机会
        opp = self._breakout(closes, highs, lows, volumes, current_price, symbol)
        if opp: opportunities.append(opp)
        
        # 2. RSI超卖/超买
        opp = self._rsi_extreme(closes, current_price, symbol)
        if opp: opportunities.append(opp)
        
        # 3. 均线金叉/死叉
        opp = self._ma_cross(closes, current_price, symbol)
        if opp: opportunities.append(opp)
        
        # 4. 成交量异常
        opp = self._volume_surge(closes, volumes, current_price, symbol)
        if opp: opportunities.append(opp)
        
        # 5. 布林带突破
        opp = self._bollinger_break(closes, current_price, symbol)
        if opp: opportunities.append(opp)
        
        # 6. 支撑阻力反转
        opp = self._support_resistance(closes, highs, lows, current_price, symbol)
        if opp: opportunities.append(opp)
        
        # 7. 趋势加速
        opp = self._trend_acceleration(closes, current_price, symbol)
        if opp: opportunities.append(opp)
        
        # 8. MACD信号
        opp = self._macd_signal(closes, current_price, symbol)
        if opp: opportunities.append(opp)
        
        # 9. 波动率收缩
        opp = self._volatility_squeeze(closes, highs, lows, current_price, symbol)
        if opp: opportunities.append(opp)
        
        # 10. 资金费率套利
        opp = self._funding_arbitrage(symbol, ticker)
        if opp: opportunities.append(opp)
        
        return opportunities
    
    def _breakout(self, closes, highs, lows, volumes, price, symbol) -> Optional[Opportunity]:
        """突破检测"""
        # 20日高点
        high_20 = max(highs[-21:-1])
        low_20 = min(lows[-21:-1])
        
        vol_avg = sum(volumes[-20:]) / 20
        vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
        
        # 突破新高
        if price > high_20 * 1.005 and vol_ratio > 1.5:
            score = 70 + vol_ratio * 10
            confidence = min(95, 60 + vol_ratio * 15)
            
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='BREAKOUT_HIGH',
                action='BUY',
                score=score,
                confidence=confidence,
                entry_price=price,
                stop_loss=low_20,
                take_profit=price * 1.08,
                risk_reward=3.0,
                reasons=[f'突破{high_20:.2f}', f'成交量放大{vol_ratio:.1f}x']
            )
        
        # 跌破新低
        if price < low_20 * 0.995 and vol_ratio > 1.5:
            score = 70 + vol_ratio * 10
            confidence = min(95, 60 + vol_ratio * 15)
            
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='BREAKOUT_LOW',
                action='SELL',
                score=score,
                confidence=confidence,
                entry_price=price,
                stop_loss=high_20,
                take_profit=price * 0.92,
                risk_reward=3.0,
                reasons=[f'跌破{low_20:.2f}', f'成交量放大{vol_ratio:.1f}x']
            )
        
        return None
    
    def _rsi_extreme(self, closes, price, symbol) -> Optional[Opportunity]:
        """RSI超买超卖"""
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-14:]]
        losses = [-d if d < 0 else 0 for d in deltas[-14:]]
        
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        # RSI超卖 → 买入机会
        if rsi < 30:
            score = 80 - rsi
            confidence = min(95, 70 + (30 - rsi))
            
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='RSI_OVERSOLD',
                action='BUY',
                score=score,
                confidence=confidence,
                entry_price=price,
                stop_loss=price * 0.97,
                take_profit=price * 1.10,
                risk_reward=3.3,
                reasons=[f'RSI超卖{rsi:.1f}', '反弹概率高']
            )
        
        # RSI超买 → 卖出机会
        if rsi > 70:
            score = rsi - 20
            confidence = min(95, 70 + (rsi - 70))
            
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='RSI_OVERBOUGHT',
                action='SELL',
                score=score,
                confidence=confidence,
                entry_price=price,
                stop_loss=price * 1.03,
                take_profit=price * 0.90,
                risk_reward=3.3,
                reasons=[f'RSI超买{rsi:.1f}', '回调概率高']
            )
        
        return None
    
    def _ma_cross(self, closes, price, symbol) -> Optional[Opportunity]:
        """均线金叉死叉"""
        ma7 = sum(closes[-7:]) / 7
        ma25 = sum(closes[-25:]) / 25
        ma99 = sum(closes[-99:]) / 99 if len(closes) >= 99 else ma25
        
        # 金叉
        if ma7 > ma25 > ma99 and closes[-1] > ma7:
            score = 75
            confidence = 80
            
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='GOLDEN_CROSS',
                action='BUY',
                score=score,
                confidence=confidence,
                entry_price=price,
                stop_loss=ma25 * 0.98,
                take_profit=price * 1.12,
                risk_reward=4.0,
                reasons=['MA7上穿MA25', '多头排列']
            )
        
        # 死叉
        if ma7 < ma25 < ma99 and closes[-1] < ma7:
            score = 75
            confidence = 80
            
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='DEATH_CROSS',
                action='SELL',
                score=score,
                confidence=confidence,
                entry_price=price,
                stop_loss=ma25 * 1.02,
                take_profit=price * 0.88,
                risk_reward=4.0,
                reasons=['MA7下穿MA25', '空头排列']
            )
        
        return None
    
    def _volume_surge(self, closes, volumes, price, symbol) -> Optional[Opportunity]:
        """成交量异常"""
        vol_avg = sum(volumes[-20:]) / 20
        vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
        
        if vol_ratio > 3:
            price_change = abs(closes[-1] - closes[-2]) / closes[-2] * 100
            
            if price_change > 2:
                action = 'BUY' if closes[-1] > closes[-2] else 'SELL'
                
                return Opportunity(
                    symbol=symbol.replace('USDT', ''),
                    type='VOLUME_SURGE',
                    action=action,
                    score=70 + vol_ratio * 5,
                    confidence=min(95, 65 + vol_ratio * 5),
                    entry_price=price,
                    stop_loss=price * 0.97,
                    take_profit=price * 1.10,
                    risk_reward=3.3,
                    reasons=[f'成交量暴增{vol_ratio:.1f}x', f'价格变动{price_change:.1f}%']
                )
        
        return None
    
    def _bollinger_break(self, closes, price, symbol) -> Optional[Opportunity]:
        """布林带突破"""
        import statistics
        if len(closes) < 20:
            return None
        
        std = statistics.stdev(closes[-20:])
        ma20 = sum(closes[-20:]) / 20
        upper = ma20 + 2 * std
        lower = ma20 - 2 * std
        
        if price > upper:
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='BOLLINGER_UPPER',
                action='SELL',
                score=80,
                confidence=75,
                entry_price=price,
                stop_loss=upper * 1.02,
                take_profit=ma20,
                risk_reward=2.5,
                reasons=[f'突破布林上轨{upper:.2f}', '注意回调风险']
            )
        
        if price < lower:
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='BOLLINGER_LOWER',
                action='BUY',
                score=80,
                confidence=75,
                entry_price=price,
                stop_loss=lower * 0.98,
                take_profit=ma20,
                risk_reward=2.5,
                reasons=[f'跌破布林下轨{lower:.2f}', '反弹概率高']
            )
        
        return None
    
    def _support_resistance(self, closes, highs, lows, price, symbol) -> Optional[Opportunity]:
        """支撑阻力反转"""
        # 找近期支撑
        support_levels = []
        for i in range(5, len(closes) - 1):
            if closes[i] < closes[i-1] and closes[i] < closes[i+1]:
                support_levels.append(closes[i])
        
        # 找近期阻力
        resistance_levels = []
        for i in range(5, len(closes) - 1):
            if closes[i] > closes[i-1] and closes[i] > closes[i+1]:
                resistance_levels.append(closes[i])
        
        if not support_levels or not resistance_levels:
            return None
        
        nearest_support = min(support_levels, key=lambda x: abs(x - price))
        nearest_resistance = min(resistance_levels, key=lambda x: abs(x - price))
        
        # 接近支撑位
        if abs(price - nearest_support) / price < 0.02:
            score = 75
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='SUPPORT_BOUNCE',
                action='BUY',
                score=score,
                confidence=70,
                entry_price=price,
                stop_loss=nearest_support * 0.97,
                take_profit=nearest_resistance,
                risk_reward=2.0,
                reasons=[f'接近支撑{nearest_support:.2f}', '反弹概率高']
            )
        
        # 接近阻力位
        if abs(price - nearest_resistance) / price < 0.02:
            score = 75
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='RESISTANCE_REJECT',
                action='SELL',
                score=score,
                confidence=70,
                entry_price=price,
                stop_loss=nearest_resistance * 1.03,
                take_profit=nearest_support,
                risk_reward=2.0,
                reasons=[f'接近阻力{nearest_resistance:.2f}', '回落概率高']
            )
        
        return None
    
    def _trend_acceleration(self, closes, price, symbol) -> Optional[Opportunity]:
        """趋势加速"""
        if len(closes) < 10:
            return None
        
        # 计算短期和长期动量
        mom_short = (closes[-1] - closes[-5]) / closes[-5] * 100
        mom_long = (closes[-1] - closes[-10]) / closes[-10] * 100
        
        # 加速上涨
        if mom_short > 5 and mom_short > mom_long * 1.5:
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='TREND_ACCEL_UP',
                action='BUY',
                score=75 + mom_short * 3,
                confidence=80,
                entry_price=price,
                stop_loss=price * 0.97,
                take_profit=price * 1.15,
                risk_reward=4.0,
                reasons=[f'短期动量{mom_short:.1f}%', '趋势加速']
            )
        
        # 加速下跌
        if mom_short < -5 and mom_short < mom_long * 1.5:
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='TREND_ACCEL_DOWN',
                action='SELL',
                score=75 + abs(mom_short) * 3,
                confidence=80,
                entry_price=price,
                stop_loss=price * 1.03,
                take_profit=price * 0.85,
                risk_reward=4.0,
                reasons=[f'短期动量{mom_short:.1f}%', '趋势加速']
            )
        
        return None
    
    def _macd_signal(self, closes, price, symbol) -> Optional[Opportunity]:
        """MACD信号"""
        if len(closes) < 26:
            return None
        
        # 计算EMA
        ema12 = sum(closes[-12:]) / 12
        ema26 = sum(closes[-26:]) / 26
        macd = ema12 - ema26
        signal = macd * 0.8  # 简化signal线
        
        hist = macd - signal
        
        # MACD金叉
        if hist > 0 and abs(hist) > abs(signal) * 0.5:
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='MACD_GOLDEN',
                action='BUY',
                score=75,
                confidence=75,
                entry_price=price,
                stop_loss=price * 0.97,
                take_profit=price * 1.12,
                risk_reward=3.5,
                reasons=['MACD金叉', '多头信号']
            )
        
        # MACD死叉
        if hist < 0 and abs(hist) > abs(signal) * 0.5:
            return Opportunity(
                symbol=symbol.replace('USDT', ''),
                type='MACD_DEATH',
                action='SELL',
                score=75,
                confidence=75,
                entry_price=price,
                stop_loss=price * 1.03,
                take_profit=price * 0.88,
                risk_reward=3.5,
                reasons=['MACD死叉', '空头信号']
            )
        
        return None
    
    def _volatility_squeeze(self, closes, highs, lows, price, symbol) -> Optional[Opportunity]:
        """波动率收缩"""
        if len(highs) < 20 or len(lows) < 20:
            return None
        
        # 计算布林带宽度
        import statistics
        std = statistics.stdev(closes[-20:])
        ma20 = sum(closes[-20:]) / 20
        bandwidth = (max(highs[-20:]) - min(lows[-20:])) / ma20 * 100
        
        # 收缩后放大
        if bandwidth < 5:  # 低波动率
            current_range = (highs[-1] - lows[-1]) / price * 100
            
            if current_range > 2:
                return Opportunity(
                    symbol=symbol.replace('USDT', ''),
                    type='VOLATILITY_SQUEEZE',
                    action='BUY',
                    score=70,
                    confidence=70,
                    entry_price=price,
                    stop_loss=lows[-1],
                    take_profit=highs[-1] * 1.05,
                    risk_reward=2.5,
                    reasons=[f'波动率收缩{bandwidth:.1f}%', '突破在即']
                )
        
        return None
    
    def _funding_arbitrage(self, symbol, ticker) -> Optional[Opportunity]:
        """资金费率套利"""
        try:
            funding = self.api.get_funding_rate(symbol.replace('USDT', 'USD'))
            if not funding:
                return None
            
            rate = funding.get('funding_rate', 0) * 100
            
            if abs(rate) > 0.05:
                annual = rate * 3 * 365
                
                return Opportunity(
                    symbol=symbol.replace('USDT', ''),
                    type='FUNDING_ARB',
                    action='LONG' if rate > 0 else 'SHORT',
                    score=80 + abs(rate) * 500,
                    confidence=85,
                    entry_price=ticker.get('price', 100),
                    stop_loss=0,
                    take_profit=0,
                    risk_reward=annual / 10,
                    reasons=[f'资金费率{rate:+.4f}%', f'年化{annual:+.1f}%']
                )
        except:
            pass
        
        return None
    
    def scan_all(self) -> List[Opportunity]:
        """扫描所有机会"""
        all_opportunities = []
        
        symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
            'ADAUSDT', 'LINKUSDT', 'DOTUSDT', 'AVAXUSDT', 'ATOMUSDT',
            'NEARUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT', 'MATICUSDT'
        ]
        
        for symbol in symbols:
            opps = self.detect_all_opportunities(symbol)
            all_opportunities.extend(opps)
        
        # 过滤和排序
        filtered = [o for o in all_opportunities if o.score >= self.min_score]
        filtered.sort(key=lambda x: x.score, reverse=True)
        
        return filtered[:15]
    
    def generate_report(self) -> str:
        """生成报告"""
        opportunities = self.scan_all()
        
        # 按类型分组
        by_type = {}
        for opp in opportunities:
            if opp.type not in by_type:
                by_type[opp.type] = []
            by_type[opp.type].append(opp)
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🎯 QM Super Hunter - 超级机会猎手                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 扫描配置:
   最低评分: {self.min_score}
   最低置信: {self.min_confidence}%
   扫描币种: 15个

╔══════════════════════════════════════════════════════════════════════════════╗
║           🎯 发现机会 ({len(opportunities)}个)                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        if not opportunities:
            report += "\n   ⚠️ 当前无满足条件的交易机会\n"
        else:
            for i, opp in enumerate(opportunities[:10], 1):
                emoji = '🟢' if opp.action in ['BUY', 'LONG'] else '🔴'
                report += f"""
   {i}. {emoji} {opp.symbol:8} {opp.type:20}
      操作: {opp.action} | 评分: {opp.score:.1f} | 置信: {opp.confidence:.0f}%
      风险回报: {opp.risk_reward:.1f}:1
"""
                for reason in opp.reasons[:2]:
                    report += f"      • {reason}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           📊 机会类型分布                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for opp_type, opps in sorted(by_type.items(), key=lambda x: -len(x[1])):
            report += f"   {opp_type:25} {len(opps)}个\n"
        
        report += "\n" + "=" * 66 + "\n"
        
        return report

def main():
    hunter = SuperHunter()
    print(hunter.generate_report())

if __name__ == '__main__':
    main()
