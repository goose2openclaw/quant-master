#!/usr/bin/env python3
"""
XIAMI Sonar Pro v3 - 极速趋势识别系统
优化: 更短时间框架 + 实时价格变动 + 多交易所聚合
"""

import ccxt
import json
import time
from datetime import datetime

class XiamiSonarProV3:
    def __init__(self):
        # 加载配置
        with open('skills/xiami/data/sonar_pro.json', 'r') as f:
            self.config = json.load(f)
        
        with open('skills/xiami/data/modes.json', 'r') as f:
            self.modes = json.load(f)
        
        self.current = self.modes['current_mode']
        
        # 极速模式: 多交易所实例
        self.exchanges = {
            'binance': ccxt.binance(),
            'bybit': ccxt.bybit(),
            'okx': ccxt.okx()
        }
        
        # 极速时间框架 (新增 1m, 3m)
        self.timeframes = {
            '1m': {'observe': True, 'execute': True, 'min_confidence': 2},
            '3m': {'observe': True, 'execute': True, 'min_confidence': 3},
            '5m': {'observe': True, 'execute': True, 'min_confidence': 4},
            '15m': {'observe': True, 'execute': True, 'min_confidence': 5}
        }
        
        # 极速信号指标
        self.fast_indicators = ['RSI', 'MACD', 'BB', 'EMA_CROSS', 'VOL_SPIKE']
        
    def fetch_fast_ohlcv(self, symbol, timeframe='1m', limit=30):
        """极速获取K线数据"""
        results = {}
        for name, exchange in self.exchanges.items():
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                results[name] = ohlcv
            except:
                continue
        return results
    
    def calculate_fast_indicators(self, ohlcv_data):
        """极速计算指标"""
        if not ohlcv_data:
            return None
        
        # 使用第一个可用的交易所数据
        exchange = list(ohlcv_data.values())[0]
        closes = [c[4] for c in exchange]
        volumes = [c[5] for c in exchange]
        
        # RSI (快速)
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[-6:]) / 6
        avg_loss = sum(losses[-6:]) / 6
        rsi = 100 - (100 / (1 + avg_gain / (avg_loss + 0.0001)))
        
        # EMA 快速交叉
        ema5 = sum(closes[-5:]) / 5
        ema10 = sum(closes[-10:]) / 10
        ema_cross = 1 if ema5 > ema10 else -1
        
        # 布林带
        sma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
        std = (sum((c - sma20) ** 2 for c in closes[-20:]) / 20) ** 0.5 if len(closes) >= 20 else 0
        bb_upper = sma20 + 2 * std
        bb_lower = sma20 - 2 * std
        
        # 成交量爆发
        avg_vol = sum(volumes[-10:]) / 10
        vol_ratio = volumes[-1] / avg_vol if avg_vol > 0 else 1
        
        # 价格变动率 (实时)
        change_1m = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0
        change_3m = (closes[-1] - closes[-3]) / closes[-3] * 100 if len(closes) >= 3 else 0
        change_5m = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
        
        return {
            'rsi': rsi,
            'ema_cross': ema_cross,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'bb_mid': sma20,
            'vol_ratio': vol_ratio,
            'change_1m': change_1m,
            'change_3m': change_3m,
            'change_5m': change_5m,
            'price': closes[-1],
            'volume': volumes[-1]
        }
    
    def detect_fast_patterns(self, ind):
        """极速形态识别"""
        patterns = []
        
        # 1. RSI 超卖超买
        if ind['rsi'] < 25:
            patterns.append(('超卖', 3))
        elif ind['rsi'] < 35:
            patterns.append(('接近超卖', 2))
        
        if ind['rsi'] > 75:
            patterns.append(('超买', 3))
        elif ind['rsi'] > 65:
            patterns.append(('接近超买', 2))
        
        # 2. 布林带突破
        if ind['price'] < ind['bb_lower']:
            patterns.append(('布林下轨反弹', 3))
        elif ind['price'] > ind['bb_upper']:
            patterns.append(('布林上轨回落', 3))
        
        # 3. EMA 交叉
        if ind['ema_cross'] > 0:
            patterns.append(('EMA金叉', 2))
        else:
            patterns.append(('EMA死叉', 2))
        
        # 4. 成交量爆发
        if ind['vol_ratio'] > 2:
            patterns.append(('成交量爆发', 3))
        elif ind['vol_ratio'] > 1.5:
            patterns.append(('成交量放大', 2))
        
        # 5. 快速变动 (核心: 实时检测)
        if abs(ind['change_1m']) > 2:
            patterns.append((f'1分钟{"涨" if ind["change_1m"] > 0 else "跌"}幅{abs(ind["change_1m"]):.1f}%', 4))
        if abs(ind['change_3m']) > 5:
            patterns.append((f'3分钟{"涨" if ind["change_3m"] > 0 else "跌"}幅{abs(ind["change_3m"]):.1f}%', 3))
        
        return patterns
    
    def calculate_fast_confidence(self, ind, patterns):
        """极速置信度计算"""
        score = 0
        
        # RSI (30-70 区间加分)
        if 30 < ind['rsi'] < 70:
            score += 2
        
        # 成交量
        if ind['vol_ratio'] > 1.5:
            score += 2
        if ind['vol_ratio'] > 2:
            score += 2
        
        # 价格变动加分
        if abs(ind['change_1m']) > 1:
            score += 2
        if abs(ind['change_3m']) > 3:
            score += 2
        
        # 形态加分
        for pattern, weight in patterns:
            score += weight
        
        return max(0, min(10, score))
    
    def should_fast_trade(self, confidence, patterns, ind):
        """极速交易决策"""
        cfg = self.get_position_config()
        
        # 极速模式: 降低置信度门槛
        min_conf = max(cfg['min_confidence'] - 2, 2)  # 最低2分
        
        if confidence < min_conf:
            return False, f"置信度{confidence}<{min_conf}"
        
        if ind['vol_ratio'] < 1.2:
            return False, f"成交量不足"
        
        return True, f"置信度{confidence}"
    
    def get_position_config(self):
        tm = self.modes['trading_modes'][self.current['trading_mode']]
        cu = self.modes['capital_utilization'][self.current['capital_utilization']]
        
        return {
            'position_size': tm['position_size'] * cu['utilization'],
            'stop_loss': tm['stop_loss'],
            'take_profit': tm['take_profit'],
            'min_confidence': max(tm['min_confidence'], cu['filters']['min_confidence'])
        }
    
    def run(self):
        print("="*60)
        print("🔱 XIAMI Sonar Pro V3 - 极速趋势识别")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("="*60)
        
        # 监控标的
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'AVAX/USDT', 'DOGE/USDT']
        
        # 极速模式: 同时扫描所有标的
        results = []
        
        for symbol in symbols:
            ohlcv_data = self.fetch_fast_ohlcv(symbol, '1m', limit=30)
            if not ohlcv_data:
                continue
            
            ind = self.calculate_fast_indicators(ohlcv_data)
            if not ind:
                continue
            
            patterns = self.detect_fast_patterns(ind)
            confidence = self.calculate_fast_confidence(ind, patterns)
            can_trade, reason = self.should_fast_trade(confidence, patterns, ind)
            
            results.append({
                'symbol': symbol,
                'price': ind['price'],
                'rsi': ind['rsi'],
                'change_1m': ind['change_1m'],
                'vol_ratio': ind['vol_ratio'],
                'confidence': confidence,
                'patterns': patterns,
                'can_trade': can_trade,
                'reason': reason
            })
        
        # 按置信度排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"\n📊 极速扫描 {len(symbols)} 个标的")
        
        # 显示前3名
        for i, r in enumerate(results[:3]):
            status = "🟢" if r['can_trade'] else "⚪"
            print(f"\n{i+1}. {status} {r['symbol']} @ ${r['price']:.4f}")
            print(f"   RSI: {r['rsi']:.1f} | 1分钟涨跌: {r['change_1m']:+.2f}%")
            print(f"   成交量: {r['vol_ratio']:.1f}x | 置信度: {r['confidence']}/10")
            print(f"   形态: {', '.join([p[0] for p in r['patterns']][:3])}")
        
        # 检查极速信号
        fast_signals = [r for r in results if r['can_trade'] and r['confidence'] >= 5]
        
        if fast_signals:
            print(f"\n🎯 极速信号 ({len(fast_signals)}个)")
            for s in fast_signals:
                direction = "买入" if s['change_1m'] > 0 else "卖出"
                print(f"  {s['symbol']}: {direction} @ {s['price']:.4f}")
        else:
            print(f"\n⚪ 无极速信号")
        
        return results

if __name__ == '__main__':
    sonar = XiamiSonarProV3()
    sonar.run()
