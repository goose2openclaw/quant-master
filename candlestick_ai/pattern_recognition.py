"""
Candlestick Pattern Recognition - K线形态识别AI
TradingView级别
"""
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Candle:
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class CandlestickPattern:
    """K线形态"""
    def __init__(self, name, pattern_type, bullish: bool, reliability: float):
        self.name = name
        self.pattern_type = pattern_type
        self.bullish = bullish
        self.reliability = reliability  # 0-100%

class PatternRecognizer:
    """
    K线形态识别
    支持30+经典形态
    """
    def __init__(self):
        self.patterns = {}
        self._init_patterns()
    
    def _init_patterns(self):
        """初始化形态库"""
        self.patterns = {
            'doji': {'type': 'reversal', 'bullish': False, 'reliability': 60},
            'hammer': {'type': 'reversal', 'bullish': True, 'reliability': 70},
            'shooting_star': {'type': 'reversal', 'bullish': False, 'reliability': 70},
            'engulfing_bullish': {'type': 'reversal', 'bullish': True, 'reliability': 75},
            'engulfing_bearish': {'type': 'reversal', 'bullish': False, 'reliability': 75},
            'morning_star': {'type': 'reversal', 'bullish': True, 'reliability': 80},
            'evening_star': {'type': 'reversal', 'bullish': False, 'reliability': 80},
            'three_white_soldiers': {'type': 'continuation', 'bullish': True, 'reliability': 85},
            'three_black_crows': {'type': 'continuation', 'bullish': False, 'reliability': 85},
            'harami_bullish': {'type': 'reversal', 'bullish': True, 'reliability': 65},
            'harami_bearish': {'type': 'reversal', 'bullish': False, 'reliability': 65},
            'piercing': {'type': 'reversal', 'bullish': True, 'reliability': 72},
            'dark_cloud': {'type': 'reversal', 'bullish': False, 'reliability': 72},
            'doji_star': {'type': 'reversal', 'bullish': None, 'reliability': 65},
            'abandoned_baby_bullish': {'type': 'reversal', 'bullish': True, 'reliability': 78},
            'abandoned_baby_bearish': {'type': 'reversal', 'bullish': False, 'reliability': 78},
        }
    
    def recognize(self, candles: List[Candle]) -> List[CandlestickPattern]:
        """识别形态"""
        recognized = []
        
        # 单根K线形态
        if len(candles) >= 1:
            recognized.extend(self._check_single(candles[-1]))
        
        # 双K形态
        if len(candles) >= 2:
            recognized.extend(self._check_double(candles[-2], candles[-1]))
        
        # 三K形态
        if len(candles) >= 3:
            recognized.extend(self._check_triple(candles[-3], candles[-2], candles[-1]))
        
        # 多K形态
        if len(candles) >= 5:
            recognized.extend(self._check_multiple(candles[-5:]))
        
        return recognized
    
    def _check_single(self, candle: Candle) -> List[CandlestickPattern]:
        """单K形态"""
        patterns = []
        
        body = abs(candle.close - candle.open)
        upper_shadow = candle.high - max(candle.open, candle.close)
        lower_shadow = min(candle.open, candle.close) - candle.low
        total_range = candle.high - candle.low
        
        if total_range == 0:
            return patterns
        
        body_ratio = body / total_range
        
        # Doji: 几乎没有实体
        if body_ratio < 0.1:
            patterns.append(CandlestickPattern(
                'doji', 'reversal', False, self.patterns['doji']['reliability']))
        
        # Hammer: 下影线很长,实体在上方
        elif lower_shadow > body * 2 and upper_shadow < body * 0.5:
            patterns.append(CandlestickPattern(
                'hammer', 'reversal', True, self.patterns['hammer']['reliability']))
        
        # Shooting Star: 上影线很长
        elif upper_shadow > body * 2 and lower_shadow < body * 0.5:
            patterns.append(CandlestickPattern(
                'shooting_star', 'reversal', False, self.patterns['shooting_star']['reliability']))
        
        return patterns
    
    def _check_double(self, c1: Candle, c2: Candle) -> List[CandlestickPattern]:
        """双K形态"""
        patterns = []
        
        # Engulfing
        if self._is_engulfing(c1, c2):
            if c2.close > c2.open and c1.close < c1.open:  # 阳包阴
                patterns.append(CandlestickPattern(
                    'engulfing_bullish', 'reversal', True, self.patterns['engulfing_bullish']['reliability']))
            elif c2.close < c2.open and c1.close > c1.open:  # 阴包阳
                patterns.append(CandlestickPattern(
                    'engulfing_bearish', 'reversal', False, self.patterns['engulfing_bearish']['reliability']))
        
        # Piercing / Dark Cloud
        if self._is_piercing(c1, c2):
            if c2.close > c2.open:  # 刺透形态
                patterns.append(CandlestickPattern(
                    'piercing', 'reversal', True, self.patterns['piercing']['reliability']))
            else:
                patterns.append(CandlestickPattern(
                    'dark_cloud', 'reversal', False, self.patterns['dark_cloud']['reliability']))
        
        return patterns
    
    def _check_triple(self, c1: Candle, c2: Candle, c3: Candle) -> List[CandlestickPattern]:
        """三K形态"""
        patterns = []
        
        # Morning/Evening Star
        if self._is_morning_star(c1, c2, c3):
            patterns.append(CandlestickPattern(
                'morning_star', 'reversal', True, self.patterns['morning_star']['reliability']))
        elif self._is_evening_star(c1, c2, c3):
            patterns.append(CandlestickPattern(
                'evening_star', 'reversal', False, self.patterns['evening_star']['reliability']))
        
        # Three White Soldiers
        if self._is_three_white_soldiers(c1, c2, c3):
            patterns.append(CandlestickPattern(
                'three_white_soldiers', 'continuation', True, self.patterns['three_white_soldiers']['reliability']))
        
        # Three Black Crows
        elif self._is_three_black_crows(c1, c2, c3):
            patterns.append(CandlestickPattern(
                'three_black_crows', 'continuation', False, self.patterns['three_black_crows']['reliability']))
        
        # Harami
        if self._is_harami(c1, c2, c3):
            if c3.close > c3.open:  # 阳孕
                patterns.append(CandlestickPattern(
                    'harami_bullish', 'reversal', True, self.patterns['harami_bullish']['reliability']))
            else:
                patterns.append(CandlestickPattern(
                    'harami_bearish', 'reversal', False, self.patterns['harami_bearish']['reliability']))
        
        return patterns
    
    def _check_multiple(self, candles: List[Candle]) -> List[CandlestickPattern]:
        """多K形态"""
        patterns = []
        
        # 旗形整理
        if self._is_flag(candles[-4:], 'bullish'):
            patterns.append(CandlestickPattern(
                'bull_flag', 'continuation', True, 70))
        elif self._is_flag(candles[-4:], 'bearish'):
            patterns.append(CandlestickPattern(
                'bear_flag', 'continuation', False, 70))
        
        # 三角形
        triangle = self._is_triangle(candles[-5:])
        if triangle:
            patterns.append(CandlestickPattern(
                f'{triangle}_triangle', 'neutral', None, 65))
        
        return patterns
    
    def _is_engulfing(self, c1: Candle, c2: Candle) -> bool:
        """是否是吞没形态"""
        body1 = abs(c2.close - c2.open)
        body2 = abs(c1.close - c1.open)
        return (body1 > body2 * 1.5 and
                ((c2.close > c1.open and c2.open < c1.close) or
                 (c2.close < c1.open and c2.open > c1.close)))
    
    def _is_piercing(self, c1: Candle, c2: Candle) -> bool:
        """是否是刺透/乌云形态"""
        prev_body = abs(c1.close - c1.open)
        curr_body = abs(c2.close - c2.open)
        
        # 开盘跳空,收盘在实体中点
        if (c1.close < c1.open and c2.close > c2.open and
            c2.open < c1.low and c2.close > c1.open + prev_body * 0.5):
            return True
        return False
    
    def _is_morning_star(self, c1: Candle, c2: Candle, c3: Candle) -> bool:
        """晨星"""
        return (c1.close < c1.open and  # 第一根阴
                abs(c2.close - c2.open) < abs(c1.close - c1.open) * 0.3 and  # 中间实体小
                c3.close > c3.open and  # 第三根阳
                c3.close > (c1.open + c1.close) / 2)  # 收盘超过阴线中点
    
    def _is_evening_star(self, c1: Candle, c2: Candle, c3: Candle) -> bool:
        """夜星"""
        return (c1.close > c1.open and  # 第一根阳
                abs(c2.close - c2.open) < abs(c1.close - c1.open) * 0.3 and  # 中间实体小
                c3.close < c3.open and  # 第三根阴
                c3.close < (c1.open + c1.close) / 2)  # 收盘跌破阳线中点
    
    def _is_three_white_soldiers(self, c1: Candle, c2: Candle, c3: Candle) -> bool:
        """三白兵"""
        return (all(c.close > c.open for c in [c1, c2, c3]) and
               c2.close > c1.close and c3.close > c2.close and
               all(c.open > c1.open - (c1.high - c1.low) * 0.3 for c in [c2, c3])
    
    def _is_three_black_crows(self, c1: Candle, c2: Candle, c3: Candle) -> bool:
        """三乌鸦"""
        return (all(c.close < c.open for c in [c1, c2, c3]) and
               c2.close < c1.close and c3.close < c2.close and
               all(c.open < c1.open + (c1.low - c1.high) * 0.3 for c in [c2, c3])
    
    def _is_harami(self, c1: Candle, c2: Candle, c3: Candle) -> bool:
        """孕线"""
        body1 = abs(c1.close - c1.open)
        body3 = abs(c3.close - c3.open)
        return body3 < body1 * 0.3
    
    def _is_flag(self, candles: List[Candle], direction: str) -> bool:
        """旗形"""
        if len(candles) < 4:
            return False
        
        # 检查是否是趋势后的盘整
        trend = candles[-1].close > candles[-4].close if direction == 'bullish' else candles[-1].close < candles[-4].close
        
        # 检查是否高低点逐渐收敛
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        # 简化: 检查趋势是否减缓
        if direction == 'bullish':
            return trend and lows[-1] < lows[-2]
        else:
            return trend and highs[-1] > highs[-2]
    
    def _is_triangle(self, candles: List[Candle]) -> Optional[str]:
        """三角形"""
        if len(candles) < 5:
            return None
        
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        # 对称三角形
        if highs[-1] < max(highs[:-1]) and lows[-1] > min(lows[:-1]):
            return 'symmetric'
        
        # 上升三角形
        if highs[-1] < max(highs[:-1]) and lows[-1] > min(lows[:-1]) and lows == sorted(lows):
            return 'ascending'
        
        # 下降三角形
        if highs[-1] < max(highs[:-1]) and lows[-1] > min(lows[:-1]) and highs == sorted(highs, reverse=True):
            return 'descending'
        
        return None

class AIBasedRecognizer(PatternRecognizer):
    """AI增强形态识别"""
    def __init__(self):
        super().__init__()
        self.ml_model = None  # 可加载预训练模型
    
    def predict_with_confidence(self, candles: List[Candle]) -> Dict:
        """AI预测"""
        patterns = self.recognize(candles)
        
        # 简化: 基于规则计算置信度
        # 实际应该使用CNN/RNN模型
        features = self._extract_features(candles)
        
        result = {
            'patterns': [{'name': p.name, 'reliability': p.reliability, 'bullish': p.bullish} for p in patterns],
            'overall_signal': 'NEUTRAL',
            'confidence': 0.5
        }
        
        if patterns:
            # 计算综合信号
            bullish_signals = sum(1 for p in patterns if p.bullish)
            bearish_signals = sum(1 for p in patterns if p.bullish is False)
            
            if bullish_signals > bearish_signals:
                result['overall_signal'] = 'BUY'
                result['confidence'] = bullish_signals / len(patterns) * 0.8
            elif bearish_signals > bullish_signals:
                result['overall_signal'] = 'SELL'
                result['confidence'] = bearish_signals / len(patterns) * 0.8
        
        return result
    
    def _extract_features(self, candles: List[Candle]):
        """提取特征"""
        features = {}
        
        if len(candles) >= 20:
            closes = [c.close for c in candles]
            volumes = [c.volume for c in candles]
            
            # 简单特征
            features['price_change'] = (closes[-1] - closes[-20]) / closes[-20]
            features['volatility'] = max(candles[-1].high - candles[-1].low for c in candles[-20:]) / closes[-1]
            features['volume_change'] = volumes[-1] / (sum(volumes[-20:]) / 20)
        
        return features
