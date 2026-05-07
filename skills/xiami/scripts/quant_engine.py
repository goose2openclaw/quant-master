#!/usr/bin/env python3
"""
🦐 XIAMI High-Frequency Quant System
- 高频量化交易 (200ms 周期)
- API速度优化
- 极速异动检测
"""

import ccxt
import time
import asyncio
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import heapq

class XiamiQuant:
    """高频量化交易系统"""
    
    def __init__(self):
        # 交易所API延迟测试
        self.exchanges_config = {
            'binance': {'latency': 999, 'score': 0},
            'bybit': {'latency': 999, 'score': 0},
            'okx': {'latency': 999, 'score': 0},
            'gate': {'latency': 999, 'score': 0},
            'mexc': {'latency': 999, 'score': 0},
        }
        
        # 量化参数
        self.quant_config = {
            'interval_ms': 200,       # 200ms 执行一次
            'min_change': 3.0,       # 最小异动 3%
            'max_positions': 3,       # 最多3个仓位
            'position_size': 30,      # 每个仓位30USDT
            'stop_loss': 0.02,        # 2% 止损
            'take_profit': 0.05,      # 5% 止盈
            'fee_reserve': 0.001,     # 手续费预留
        }
        
        # 当前持仓
        self.positions = []
        
        # 信号缓存
        self.signal_cache = []
        
        # 最快交易所
        self.fastest_exchange = None
        
        # 运行状态
        self.running = False
        
    def test_api_latency(self):
        """测试API延迟"""
        print("\n" + "="*60)
        print("🌐 API 延迟测试")
        print("="*60)
        
        for ex_name in self.exchanges_config:
            try:
                exchange = getattr(ccxt, ex_name)()
                
                # 测试时间端点
                start = time.time()
                try:
                    exchange.public_get_time()
                except:
                    exchange.fetch_time()
                latency = (time.time() - start) * 1000
                
                self.exchanges_config[ex_name]['latency'] = latency
                self.exchanges_config[ex_name]['score'] = max(0, 1000 - latency)
                
                print(f"✅ {ex_name}: {latency:.0f}ms")
                
            except Exception as e:
                self.exchanges_config[ex_name]['latency'] = 9999
                print(f"❌ {ex_name}: 失败")
        
        # 排序找最快
        sorted_ex = sorted(self.exchanges_config.items(), 
                          key=lambda x: x[1]['latency'])
        
        self.fastest_exchange = sorted_ex[0][0]
        
        print(f"\n🏆 最快交易所: {self.fastest_exchange} ({sorted_ex[0][1]['latency']:.0f}ms)")
        
        return self.fastest_exchange
    
    def scan_fast_exchange(self, exchange_name, limit=50):
        """快速扫描单个交易所"""
        alerts = []
        
        try:
            exchange = getattr(ccxt, exchange_name)()
            exchange.load_markets()
            
            markets = [m for m in exchange.markets.keys() if 'USDT' in m][:limit]
            
            # 获取ticker
            tickers = exchange.fetch_tickers(markets)
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage') or 0
                volume = ticker.get('quoteVolume', 0)
                price = ticker.get('last', 0)
                
                # 异动检测
                if abs(change) >= self.quant_config['min_change'] and volume > 100000:
                    # 计算优先级分数
                    score = (abs(change) * 10) + (volume / 1e6) + (1000 - self.exchanges_config[exchange_name]['latency']) / 100
                    
                    alerts.append({
                        'symbol': symbol,
                        'exchange': exchange_name,
                        'price': price,
                        'change': change,
                        'volume': volume,
                        'score': score,
                        'timestamp': time.time()
                    })
                    
        except Exception as e:
            pass
        
        return alerts
    
    def quant_cycle(self):
        """量化交易周期 (200ms)"""
        all_alerts = []
        
        # 并行扫描最快的前3个交易所
        sorted_ex = sorted(self.exchanges_config.items(), 
                          key=lambda x: x[1]['latency'])[:3]
        ex_names = [ex[0] for ex in sorted_ex]
        
        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = [ex.submit(self.scan_fast_exchange, name) for name in ex_names]
            
            for future in futures:
                all_alerts.extend(future.result())
        
        if not all_alerts:
            return None
        
        # 按分数排序
        all_alerts.sort(key=lambda x: x['score'], reverse=True)
        
        # 更新缓存
        self.signal_cache = all_alerts
        
        return all_alerts[0] if all_alerts else None
    
    def execute_signal(self, signal):
        """执行交易信号"""
        config = self.quant_config
        
        # 方向
        direction = "LONG" if signal['change'] > 0 else "SHORT"
        
        # 计算交易参数
        price = signal['price']
        size = config['position_size']
        
        if direction == "LONG":
            stop_loss_price = price * (1 - config['stop_loss'])
            take_profit_price = price * (1 + config['take_profit'])
        else:
            stop_loss_price = price * (1 + config['stop_loss'])
            take_profit_price = price * (1 - config['take_profit'])
        
        # 预估手续费
        fee = price * size * config['fee_reserve']
        
        # 净收益
        gross = abs(signal['change']) * 100
        net = gross - (config['fee_reserve'] * 200)
        
        return {
            'symbol': signal['symbol'],
            'exchange': signal['exchange'],
            'direction': direction,
            'entry_price': price,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
            'position_size': size,
            'fee': fee,
            'gross_profit': f"{gross:.1f}%",
            'net_profit': f"{net:.1f}%",
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    
    def run_quant(self, duration=60):
        """运行高频量化"""
        print("="*60)
        print("⚡ XIAMI 高频量化系统")
        print(f"⏱️ 周期: {self.quant_config['interval_ms']}ms")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 测试API延迟
        self.test_api_latency()
        
        self.running = True
        
        start_time = time.time()
        cycles = 0
        total_signals = 0
        executed_trades = []
        
        print(f"\n🚀 开始量化交易 (持续 {duration}秒)...")
        
        while time.time() - start_time < duration:
            # 量化周期
            signal = self.quant_cycle()
            
            if signal:
                # 有信号
                total_signals += 1
                
                # 检查是否需要交易
                should_trade = False
                
                # 检查是否已有仓位
                if len(self.positions) < self.quant_config['max_positions']:
                    # 检查是否已交易过
                    recent = [p for p in executed_trades 
                             if p['symbol'] == signal['symbol'] 
                             and time.time() - p.get('time_ts', 0) < 60]
                    
                    if not recent:
                        should_trade = True
                
                if should_trade:
                    trade = self.execute_signal(signal)
                    trade['time_ts'] = time.time()
                    executed_trades.append(trade)
                    
                    print(f"\n⚡ 执行交易!")
                    print(f"   {trade['direction']} {trade['symbol']}")
                    print(f"   价格: ${trade['entry_price']:.6f}")
                    print(f"   涨跌: {signal['change']:+.1f}%")
                    print(f"   止损: ${trade['stop_loss']:.6f}")
                    print(f"   止盈: ${trade['take_profit']:.6f}")
                    print(f"   预计净收益: {trade['net_profit']}")
            
            cycles += 1
            
            # 等待下一个周期
            time.sleep(self.quant_config['interval_ms'] / 1000)
        
        self.running = False
        
        # 总结
        print("\n" + "="*60)
        print("📊 量化总结")
        print("="*60)
        print(f"总周期: {cycles}")
        print(f"发现信号: {total_signals}")
        print(f"执行交易: {len(executed_trades)}")
        
        if executed_trades:
            print("\n📋 交易记录:")
            for t in executed_trades:
                print(f"  - {t['direction']} {t['symbol']} @ ${t['entry_price']:.6f}")
        
        return executed_trades

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=60, help='运行时长(秒)')
    parser.add_argument('--interval', type=int, default=200, help='周期(ms)')
    args = parser.parse_args()
    
    quant = XiamiQuant()
    quant.quant_config['interval_ms'] = args.interval
    quant.run_quant(args.duration)

if __name__ == "__main__":
    main()
