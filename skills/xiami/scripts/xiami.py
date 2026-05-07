#!/usr/bin/env python3
"""
XIAMI Trading System
eXtensible AI-Driven Multi-source Intelligent trading
"""

import os
import sys
import json
import time
import ccxt
import numpy as np
import pandas as pd
from datetime import datetime

# 配置
CONFIG = {
    "mode": {
        "trend": {"enabled": True, "allocation": 0.5},
        "grid": {"enabled": True, "allocation": 0.3},
        "arbitrage": {"enabled": True, "allocation": 0.2}
    },
    "risk": {
        "max_position": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.15
    },
    "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
    "api_key": os.getenv("BINANCE_API_KEY", ""),
    "api_secret": os.getenv("BINANCE_SECRET", "")
}

class XiamiTrader:
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.exchange = ccxt.binance({
            'apiKey': self.config['api_key'],
            'secret': self.config['api_secret'],
            'enableRateLimit': True,
        })
        self.exchange.set_sandbox_mode(True)  # 模拟盘
    
    def get_ohlcv(self, symbol, timeframe='4h', limit=50):
        """获取K线数据"""
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
    
    def calculate_indicators(self, ohlcv):
        """计算技术指标"""
        if not ohlcv:
            return {}
        
        closes = [c[4] for c in ohlcv]
        
        # SMA
        sma20 = np.mean(closes[-20:]) if len(closes) >= 20 else 0
        sma50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma20
        
        # RSI
        gains = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        avg_gain = np.mean([g for g in gains[-14:] if g > 0]) if gains else 0
        avg_loss = np.mean([abs(g) for g in gains[-14:] if g < 0]) if gains else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = np.mean(closes[-12:])
        ema26 = np.mean(closes[-26:])
        macd = ema12 - ema26
        
        # 波动率
        volatility = np.std(closes[-20:]) / np.mean(closes[-20:]) * 100
        
        return {
            'close': closes[-1],
            'sma20': sma20,
            'sma50': sma50,
            'rsi': rsi,
            'macd': macd,
            'volatility': volatility
        }
    
    def calculate_signal_score(self, indicators):
        """计算信号分数 (-10 to +10)"""
        score = 0
        
        # RSI (权重 3)
        if indicators.get('rsi', 50) < 30:
            score += 3
        elif indicators.get('rsi', 50) > 70:
            score -= 3
        elif indicators.get('rsi', 50) < 40:
            score += 1
        elif indicators.get('rsi', 50) > 60:
            score -= 1
        
        # 趋势 (权重 4)
        if indicators.get('close', 0) > indicators.get('sma20', 0):
            score += 4
        else:
            score -= 4
        
        # MACD (权重 3)
        if indicators.get('macd', 0) > 0:
            score += 3
        else:
            score -= 3
        
        return max(-10, min(10, score))
    
    def get_signal(self, symbol):
        """获取交易信号"""
        ohlcv = self.get_ohlcv(symbol)
        indicators = self.calculate_indicators(ohlcv)
        score = self.calculate_signal_score(indicators)
        
        # 确定信号
        if score >= 5:
            signal = "🟢 强力买入"
        elif score >= 2:
            signal = "🟢 温和看涨"
        elif score >= -1:
            signal = "⚪ 中性"
        elif score >= -4:
            signal = "🔴 温和看跌"
        else:
            signal = "🔴 强力卖出"
        
        return {
            'symbol': symbol,
            'price': indicators.get('close', 0),
            'rsi': indicators.get('rsi', 0),
            'macd': indicators.get('macd', 0),
            'sma20': indicators.get('sma20', 0),
            'volatility': indicators.get('volatility', 0),
            'score': score,
            'signal': signal
        }
    
    def should_enter_trend(self, indicators):
        """趋势模式入场条件 (满足2/3)"""
        conditions = [
            indicators.get('rsi', 50) < 40,  # RSI超卖
            indicators.get('macd', 0) > 0,    # MACD金叉
            indicators.get('close', 0) > indicators.get('sma20', 0)  # 站上SMA20
        ]
        return sum(conditions) >= 2
    
    def should_enter_grid(self, indicators):
        """网格模式入场条件"""
        return (
            indicators.get('volatility', 0) < 3 and
            indicators.get('sma20', 0) > indicators.get('sma50', 0) > 0
        )
    
    def run_all_modes(self):
        """运行所有模式"""
        results = []
        
        for symbol in self.config['symbols']:
            signal_data = self.get_signal(symbol)
            indicators = {
                'rsi': signal_data['rsi'],
                'macd': signal_data['macd'],
                'sma20': signal_data['sma20'],
                'sma50': signal_data.get('sma20', 0),
                'close': signal_data['price'],
                'volatility': signal_data['volatility']
            }
            
            # 趋势模式
            if self.config['mode']['trend']['enabled']:
                if self.should_enter_trend(indicators):
                    results.append({
                        'mode': 'TREND',
                        'symbol': symbol,
                        'action': 'BUY',
                        'reason': 'RSI超卖 + MACD金叉 + 站上SMA20'
                    })
            
            # 网格模式
            if self.config['mode']['grid']['enabled']:
                if self.should_enter_grid(indicators):
                    results.append({
                        'mode': 'GRID',
                        'symbol': symbol,
                        'action': 'SETUP',
                        'reason': '波动率低 + 价格在区间'
                    })
        
        return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description='XIAMI Trading System')
    parser.add_argument('--signal', action='store_true', help='获取信号')
    parser.add_argument('--mode', choices=['trend', 'grid', 'arbitrage', 'all'], default='all', help='运行模式')
    parser.add_argument('--symbol', default='BTC/USDT', help='交易对')
    parser.add_argument('--backtest', action='store_true', help='回测模式')
    parser.add_argument('--days', type=int, default=30, help='回测天数')
    
    args = parser.parse_args()
    
    xiami = XiamiTrader()
    
    if args.signal:
        # 获取信号
        result = xiami.get_signal(args.symbol)
        print(f"\n{'='*60}")
        print(f"🦐 XIAMI 信号 - {result['symbol']}")
        print(f"{'='*60}")
        print(f"价格: ${result['price']:.2f}")
        print(f"RSI: {result['rsi']:.1f}")
        print(f"MACD: {result['macd']:.2f}")
        print(f"SMA20: ${result['sma20']:.2f}")
        print(f"波动率: {result['volatility']:.2f}%")
        print(f"{'='*60}")
        print(f"📊 信号分数: {result['score']:+d}/10")
        print(f"🚦 信号: {result['signal']}")
        print(f"{'='*60}\n")
    
    elif args.backtest:
        print(f"\n{'='*60}")
        print(f"🦐 XIAMI 回测模式 - 最近 {args.days} 天")
        print(f"{'='*60}\n")
        
        for symbol in CONFIG['symbols']:
            result = xiami.get_signal(symbol)
            print(f"{symbol}: {result['signal']}")
    
    else:
        # 运行所有模式
        results = xiami.run_all_modes()
        print(f"\n{'='*60}")
        print(f"🦐 XIAMI 交易信号")
        print(f"{'='*60}")
        
        if results:
            for r in results:
                print(f"\n{r['mode']} - {r['symbol']}")
                print(f"  动作: {r['action']}")
                print(f"  原因: {r['reason']}")
        else:
            print("\n⚪ 无交易信号 - 市场状态不适合")
        
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()
