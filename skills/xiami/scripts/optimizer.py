#!/usr/bin/env python3
"""
XIAMI Strategy Optimizer
自动优化策略参数并回测
"""

import ccxt
import json
import itertools
from datetime import datetime, timedelta

class XiamiOptimizer:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.exchange.set_sandbox_mode(True)
        
    def fetch_data(self, symbol, days=30):
        """获取历史数据"""
        ohlcv = self.exchange.fetch_ohlcv(symbol, '1d', limit=days)
        return [c[4] for c in ohlcv]  # close prices
    
    def backtest(self, closes, params):
        """回测策略"""
        rsi_period = params['rsi_period']
        rsi_oversold = params['rsi_oversold']
        rsi_overbought = params['rsi_overbought']
        sma_period = params['sma_period']
        
        trades = []
        position = 0
        entry_price = 0
        
        for i in range(rsi_period + sma_period, len(closes)):
            # 计算 RSI
            period = closes[i-rsi_period:i]
            gains = [period[j] - period[j-1] for j in range(1, len(period))]
            avg_gain = sum([g for g in gains if g > 0]) / rsi_period
            avg_loss = sum([abs(g) for g in gains if g < 0]) / rsi_period
            rsi = 100 - (100 / (1 + avg_gain/avg_loss)) if avg_loss > 0 else 50
            
            # 计算 SMA
            sma = sum(closes[i-sma_period:i]) / sma_period
            
            # 入场信号
            if position == 0 and rsi < rsi_oversold and closes[i] > sma:
                position = 1
                entry_price = closes[i]
                
            # 出场信号
            elif position == 1 and (rsi > rsi_overbought or closes[i] < sma):
                profit = (closes[i] - entry_price) / entry_price * 100
                trades.append(profit)
                position = 0
        
        if trades:
            return {
                'total_trades': len(trades),
                'win_rate': sum([1 for t in trades if t > 0]) / len(trades) * 100,
                'avg_profit': sum(trades) / len(trades),
                'total_profit': sum(trades)
            }
        return {'total_trades': 0, 'win_rate': 0, 'avg_profit': 0, 'total_profit': 0}
    
    def optimize(self, symbol='BTC/USDT'):
        """参数优化"""
        print(f"\n{'='*60}")
        print(f"🔧 XIAMI 策略优化 - {symbol}")
        print(f"{'='*60}")
        
        closes = self.fetch_data(symbol, 60)
        
        # 参数网格
        best_params = None
        best_profit = -999
        
        results = []
        
        for rsi_p in [14, 21, 28]:
            for rsi_oversold in [25, 30, 35, 40]:
                for rsi_overbought in [60, 65, 70, 75, 80]:
                    for sma_p in [10, 20, 30, 50]:
                        params = {
                            'rsi_period': rsi_p,
                            'rsi_oversold': rsi_oversold,
                            'rsi_overbought': rsi_overbought,
                            'sma_period': sma_p
                        }
                        
                        result = self.backtest(closes, params)
                        
                        if result['total_trades'] > 0:
                            score = result['total_profit'] * 0.7 + result['win_rate'] * 0.3
                            
                            results.append({
                                'params': params,
                                'result': result,
                                'score': score
                            })
        
        # 排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n📊 Top 5 参数组合:")
        print("-" * 60)
        
        for i, r in enumerate(results[:5], 1):
            p = r['params']
            res = r['result']
            print(f"{i}. RSI({p['rsi_period']}) oversold={p['rsi_oversold']} overbought={p['rsi_overbought']} SMA={p['sma_period']}")
            print(f"   交易: {res['total_trades']} | 胜率: {res['win_rate']:.1f}% | 收益: {res['total_profit']:+.1f}%")
        
        if results:
            best = results[0]
            print(f"\n🏆 最佳参数:")
            print(f"   RSI周期: {best['params']['rsi_period']}")
            print(f"   超卖: {best['params']['rsi_oversold']}")
            print(f"   超买: {best['params']['rsi_overbought']}")
            print(f"   SMA周期: {best['params']['sma_period']}")
            print(f"   预期收益: {best['result']['total_profit']:+.1f}%")
        
        return results[0] if results else None

if __name__ == "__main__":
    optimizer = XiamiOptimizer()
    
    # 优化多个币种
    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        try:
            optimizer.optimize(symbol)
        except Exception as e:
            print(f"Error: {e}")
