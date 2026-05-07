#!/usr/bin/env python3
"""
XIAMI Sonar Pro v2 - 多模式交易系统
支持资金利用率和回报率灵活调节
"""

import ccxt
import json
from datetime import datetime

class XiamiSonarPro:
    def __init__(self, mode=None):
        with open('skills/xiami/data/sonar_pro.json', 'r') as f:
            self.config = json.load(f)
        
        with open('skills/xiami/data/modes.json', 'r') as f:
            self.modes = json.load(f)
        
        # 使用指定模式或当前模式
        if mode:
            self.set_mode(mode)
        
        self.current = self.modes['current_mode']
    
    def set_mode(self, trading_mode=None, utilization=None, return_target=None):
        """设置交易模式"""
        if trading_mode:
            self.current['trading_mode'] = trading_mode
        if utilization:
            self.current['capital_utilization'] = utilization
        if return_target:
            self.current['return_target'] = return_target
        
        self.save_mode()
    
    def save_mode(self):
        """保存模式"""
        with open('skills/xiami/data/modes.json', 'r') as f:
            modes = json.load(f)
        modes['current_mode'] = self.current
        with open('skills/xiami/data/modes.json', 'w') as f:
            json.dump(modes, f, indent=2)
    
    def get_position_config(self):
        """获取仓位配置"""
        tm = self.modes['trading_modes'][self.current['trading_mode']]
        cu = self.modes['capital_utilization'][self.current['capital_utilization']]
        rt = self.modes['return_targets'][self.current['return_target']]
        
        return {
            'position_size': tm['position_size'] * cu['utilization'],
            'max_positions': tm['max_positions'],
            'stop_loss': tm['stop_loss'],
            'take_profit': tm['take_profit'],
            'leverage': tm['leverage'],
            'min_confidence': max(tm['min_confidence'], cu['filters']['min_confidence']),
            'risk_level': tm['risk_level'],
            'daily_target': rt['daily_target'],
            'filters': cu['filters']
        }
    
    def get_indicators(self, symbol):
        try:
            e = ccxt.binance()
            ohlcv = e.fetch_ohlcv(symbol, '5m', limit=50)
            
            closes = [c[4] for c in ohlcv]
            volumes = [c[5] for c in ohlcv]
            
            # RSI
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            rsi = 100 - (100 / (1 + avg_gain / (avg_loss + 0.0001)))
            
            # MACD
            ema12 = sum(closes[-12:]) / 12
            ema26 = sum(closes[-26:]) / 26
            macd = ema12 - ema26
            
            # SMA
            sma20 = sum(closes[-20:]) / 20
            
            # Volume
            vol_ma = sum(volumes[-20:]) / 20
            vol_ratio = volumes[-1] / vol_ma
            
            # Change
            change = (closes[-1] - closes[-10]) / closes[-10] * 100
            
            return {
                'symbol': symbol,
                'price': closes[-1],
                'rsi': rsi,
                'macd': macd,
                'sma20': sma20,
                'vol_ratio': vol_ratio,
                'change': change
            }
        except:
            return None
    
    def calculate_confidence(self, ind):
        score = 0
        
        if ind['rsi'] < 30: score += 3
        elif ind['rsi'] < 40: score += 2
        elif ind['rsi'] > 70: score -= 3
        elif ind['rsi'] > 60: score -= 2
        
        if ind['macd'] > 0: score += 2
        else: score -= 2
        
        if ind['price'] > ind['sma20']: score += 2
        else: score -= 2
        
        if ind['vol_ratio'] > 2: score += 2
        elif ind['vol_ratio'] > 1.5: score += 1
        
        return max(0, min(10, score))
    
    def detect_patterns(self, ind):
        patterns = []
        
        if ind['rsi'] > 50 and ind['price'] > ind['sma20'] and ind['macd'] > 0:
            patterns.append('上涨动量')
        if ind['rsi'] < 50 and ind['price'] < ind['sma20'] and ind['macd'] < 0:
            patterns.append('下跌动量')
        if ind['vol_ratio'] > 2 and ind['change'] > 3:
            patterns.append('放量突破')
        if ind['rsi'] < 30:
            patterns.append('超卖反弹')
        if ind['rsi'] > 70:
            patterns.append('超买回调')
        
        return patterns
    
    def should_trade(self, confidence, patterns, vol_ratio):
        cfg = self.get_position_config()
        filters = cfg['filters']
        
        if confidence < cfg['min_confidence']:
            return False, f"置信度{confidence}<{cfg['min_confidence']}"
        
        if vol_ratio < filters['min_volume_ratio']:
            return False, f"成交量不足"
        
        if len(patterns) < filters['min_patterns']:
            return False, f"形态不足"
        
        return True, f"置信度{confidence}"
    
    def run(self):
        print("="*60)
        print("XIAMI Sonar Pro v2 - 多模式交易")
        print(datetime.now().strftime('%H:%M:%S'))
        print("="*60)
        
        # 显示当前模式
        cfg = self.get_position_config()
        tm = self.modes['trading_modes'][self.current['trading_mode']]
        
        print(f"\n当前模式:")
        print(f"  交易模式: {tm['name']} ({tm['description']})")
        print(f"  资金利用率: {self.current['capital_utilization']}")
        print(f"  回报目标: {self.current['return_target']}")
        print(f"  仓位: {cfg['position_size']*100:.0f}%")
        print(f"  止损: {cfg['stop_loss']*100:.0f}% | 止盈: {cfg['take_profit']*100:.0f}%")
        print(f"  最小置信度: {cfg['min_confidence']}")
        
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
        
        results = []
        
        for symbol in symbols:
            ind = self.get_indicators(symbol)
            if not ind:
                continue
            
            confidence = self.calculate_confidence(ind)
            patterns = self.detect_patterns(ind)
            can_trade, reason = self.should_trade(confidence, patterns, ind['vol_ratio'])
            
            results.append({
                'symbol': symbol,
                'price': ind['price'],
                'change': ind['change'],
                'rsi': ind['rsi'],
                'vol_ratio': ind['vol_ratio'],
                'confidence': confidence,
                'patterns': patterns,
                'can_trade': can_trade,
                'reason': reason
            })
        
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"\n观测 {len(results)} 个标的")
        
        trades = [r for r in results if r['can_trade']]
        
        if trades:
            print(f"\n可执行信号 ({len(trades)}个):")
            for t in trades:
                print(f"\n{t['symbol']}")
                print(f"  ${t['price']:.2f} | {t['change']:+.1f}%")
                print(f"  RSI: {t['rsi']:.0f} | 成交量: {t['vol_ratio']:.1f}x")
                print(f"  置信度: {t['confidence']}/10")
                print(f"  形态: {', '.join(t['patterns'])}")
                print(f"  建议仓位: ${100 * cfg['position_size']:.2f}")
        else:
            print("\n⚪ 无交易信号")
        
        return results

if __name__ == "__main__":
    XiamiSonarPro().run()
