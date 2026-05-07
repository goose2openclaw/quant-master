#!/usr/bin/env python3
"""
🦐 XIAMI 主流币策略 - 稳健收益
结合市场情绪和真实数据
"""

import ccxt
import time
import json
from datetime import datetime

class XiamiMainstream:
    """主流币交易策略"""
    
    def __init__(self):
        self.symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 
            'SOL/USDT', 'XRP/USDT', 'ADA/USDT',
            'DOGE/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT'
        ]
        
        # 资金分配
        self.capital_per_coin = 100  # 每个币100 USDT
        
        # 止盈止损
        self.stop_loss = 0.03  # 3%
        self.take_profit = 0.08  # 8%
        
    def get_market_sentiment(self):
        """获取市场情绪"""
        try:
            binance = ccxt.binance()
            ticker = binance.fetch_ticker('BTC/USDT')
            
            change_24h = ticker.get('percentage', 0)
            volume = ticker.get('quoteVolume', 0)
            
            # 情绪判断
            if change_24h > 5:
                sentiment = "FOMO"
                bias = "bullish"
            elif change_24h > 2:
                sentiment = "乐观"
                bias = "bullish"
            elif change_24h < -5:
                sentiment = "恐慌"
                bias = "bearish"
            elif change_24h < -2:
                sentiment = "悲观"
                bias = "bearish"
            else:
                sentiment = "中性"
                bias = "neutral"
            
            return {
                'sentiment': sentiment,
                'bias': bias,
                'btc_change': change_24h,
                'volume': volume
            }
        except Exception as e:
            return {'sentiment': '未知', 'bias': 'neutral', 'btc_change': 0}
    
    def analyze_symbol(self, symbol):
        """分析单个币"""
        try:
            binance = ccxt.binance()
            ticker = binance.fetch_ticker(symbol)
            
            change = ticker.get('percentage', 0)
            price = ticker.get('last', 0)
            volume = ticker.get('quoteVolume', 0)
            
            # 交易信号
            signal = None
            
            # 回调买入 (下跌2-5%)
            if -5 < change < -2:
                signal = "买入-回调"
                reason = f"价格回调 {change:.1f}%"
                action = "BUY"
            
            # 突破买入 (上涨2-5%)
            elif 2 < change < 5:
                signal = "买入-突破"
                reason = f"价格上涨 {change:.1f}%"
                action = "BUY"
            
            # 强力买入 (>5%)
            elif change > 5:
                signal = "观望-过热"
                reason = f"涨幅过大 {change:.1f}%"
                action = "WAIT"
            
            # 止损卖出 (<-3%)
            elif change < -3:
                signal = "卖出-止损"
                reason = f"下跌 {change:.1f}%"
                action = "SELL"
            
            return {
                'symbol': symbol,
                'price': price,
                'change': change,
                'volume': volume,
                'signal': signal,
                'reason': reason,
                'action': action
            }
            
        except Exception as e:
            return None
    
    def run(self):
        """运行策略"""
        print("="*60)
        print("🦐 XIAMI 主流币策略 - 稳健收益")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 市场情绪
        sentiment = self.get_market_sentiment()
        print(f"\n📊 市场情绪: {sentiment['sentiment']} (BTC: {sentiment['btc_change']:+.1f}%)")
        
        # 分析所有币
        signals = []
        
        for symbol in self.symbols:
            result = self.analyze_symbol(symbol)
            if result and result['action'] != 'WAIT':
                signals.append(result)
        
        # 交易决策
        print("\n" + "="*60)
        print("🎯 交易信号")
        print("="*60)
        
        # 只做多 (买入信号)
        buy_signals = [s for s in signals if s['action'] == 'BUY']
        
        if buy_signals and sentiment['bias'] != 'bearish':
            # 情绪好才买
            for s in buy_signals[:2]:  # 最多2个
                print(f"\n🟢 买入 {s['symbol']}")
                print(f"   价格: ${s['price']:.4f}")
                print(f"   原因: {s['reason']}")
                print(f"   止损: {self.stop_loss*100}%")
                print(f"   止盈: {self.take_profit*100}%")
        else:
            print("\n⚪ 无买入信号")
        
        # 卖出信号
        sell_signals = [s for s in signals if s['action'] == 'SELL']
        for s in sell_signals[:1]:
            print(f"\n🔴 卖出 {s['symbol']}")
            print(f"   原因: {s['reason']}")
        
        return signals

if __name__ == "__main__":
    XiamiMainstream().run()
