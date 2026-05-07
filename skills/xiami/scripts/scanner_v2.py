#!/usr/bin/env python3
"""
🦐 XIAMI Scanner v2 - 优化版全市场监测系统
- 自适应扫描频率
- 优先级排序
- 延迟优化
"""

import ccxt
import time
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class XiamiScannerV2:
    """优化版扫描器"""
    
    def __init__(self):
        self.exchanges = {}
        self.alerts = []
        self.stats = {
            'total_scans': 0,
            'total_alerts': 0,
            'total_trades': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # 优化配置
        self.config = {
            'exchanges': ['binance', 'bybit', 'okx', 'gate', 'mexc'],
            'min_volume': 50000,  # 最小成交量
            'change_threshold': 2.5,  # 波动阈值
            'top_n': 20,  # 每交易所扫描数量
            'mode': 'adaptive',  # adaptive, fast, deep
            'scan_interval': 30,  # 基础间隔(秒)
        }
        
        # 优先级权重
        self.weights = {
            'volume': 0.4,
            'change': 0.4,
            'liquidity': 0.2
        }
        
    def connect_exchanges(self):
        """快速连接交易所"""
        for ex_name in self.config['exchanges']:
            try:
                exchange = getattr(ccxt, ex_name)()
                exchange.load_markets()
                self.exchanges[ex_name] = exchange
                print(f"✅ {ex_name}")
            except Exception as e:
                print(f"❌ {ex_name}: {e}")
    
    def fetch_tickers_fast(self, exchange, symbols):
        """快速获取ticker"""
        try:
            return exchange.fetch_tickers(symbols)
        except:
            # 降级到单个获取
            result = {}
            for sym in symbols[:10]:  # 限制数量
                try:
                    result[sym] = exchange.fetch_ticker(sym)
                except:
                    pass
            return result
    
    def scan_exchange(self, ex_name):
        """扫描单个交易所"""
        if ex_name not in self.exchanges:
            return []
        
        exchange = self.exchanges[ex_name]
        alerts = []
        
        try:
            # 获取交易对列表
            markets = [m for m in exchange.markets.keys() if 'USDT' in m]
            
            # 优先获取高交易量
            symbols = markets[:self.config['top_n']]
            tickers = self.fetch_tickers_fast(exchange, symbols)
            
            for symbol, ticker in tickers.items():
                try:
                    change = ticker.get('percentage') or 0
                    volume = ticker.get('quoteVolume', 0)
                    
                    if abs(change) >= self.config['change_threshold'] and volume >= self.config['min_volume']:
                        score = (
                            self.weights['change'] * abs(change) +
                            self.weights['volume'] * (volume / 1e6) +
                            self.weights['liquidity'] * (1 if volume > 1e7 else 0)
                        )
                        
                        alerts.append({
                            'symbol': symbol,
                            'exchange': ex_name,
                            'price': ticker.get('last', 0),
                            'change': change,
                            'volume': volume,
                            'score': score,
                            'time': datetime.now().strftime('%H:%M:%S')
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"❌ {ex_name}: {e}")
        
        return alerts
    
    def scan_all(self):
        """全市场扫描"""
        start = time.time()
        
        all_alerts = []
        
        # 并行扫描
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.scan_exchange, ex): ex for ex in self.config['exchanges']}
            
            for future in as_completed(futures):
                try:
                    alerts = future.result()
                    all_alerts.extend(alerts)
                except:
                    pass
        
        # 按分数排序
        all_alerts.sort(key=lambda x: x['score'], reverse=True)
        
        elapsed = time.time() - start
        
        # 更新统计
        self.stats['total_scans'] += 1
        self.stats['total_alerts'] += len(all_alerts)
        
        return all_alerts, elapsed
    
    def generate_signal(self, alert):
        """生成信号"""
        change = alert['change']
        
        if change > 6:
            return "🟢🟢 强力买入", 10
        elif change > 3:
            return "🟢 买入", 6
        elif change > 1:
            return "🟡 观望", 2
        elif change < -6:
            return "🔴🔴 强力卖出", -10
        elif change < -3:
            return "🔴 卖出", -6
        else:
            return "⚪ 中性", 0
    
    def auto_trade_decision(self, alert):
        """自动交易决策"""
        signal, score = self.generate_signal(alert)
        
        # 高置信度信号
        if abs(score) >= 6 and alert['volume'] > 500000:
            return {
                'action': 'BUY' if score > 0 else 'SELL',
                'symbol': alert['symbol'],
                'exchange': alert['exchange'],
                'price': alert['price'],
                'reason': signal,
                'confidence': abs(score) / 10
            }
        return None
    
    def run_continuous(self, interval=1800):
        """持续运行"""
        print("=" * 60)
        print("🦐 XIAMI Scanner v2 - 持续监测模式")
        print(f"📡 扫描间隔: {interval}秒")
        print("=" * 60)
        
        self.connect_exchanges()
        
        iteration = 0
        while True:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"🔄 第 {iteration} 次扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            # 扫描
            alerts, elapsed = self.scan_all()
            
            print(f"\n⏱️ 扫描耗时: {elapsed:.2f}秒")
            print(f"📊 发现异常: {len(alerts)}")
            
            # 显示 top 10
            print("\n🏆 Top 10 信号:")
            for i, alert in enumerate(alerts[:10], 1):
                emoji = "📈" if alert['change'] > 0 else "📉"
                print(f"{i}. {emoji} {alert['symbol']} @ {alert['exchange']}")
                print(f"   价格: ${alert['price']:.4f} | 涨跌: {alert['change']:+.2f}%")
            
            # 自动交易决策
            print("\n🎯 自动交易信号:")
            trades = []
            for alert in alerts[:5]:
                trade = self.auto_trade_decision(alert)
                if trade:
                    trades.append(trade)
                    print(f"   ✅ {trade['action']} {trade['symbol']} @ ${trade['price']:.4f}")
                    print(f"      原因: {trade['reason']} | 置信度: {trade['confidence']*100:.0f}%")
            
            if trades:
                self.stats['total_trades'] += len(trades)
            
            # 打印统计
            print(f"\n📈 统计:")
            print(f"   总扫描: {self.stats['total_scans']}")
            print(f"   总异常: {self.stats['total_alerts']}")
            print(f"   自动交易: {self.stats['total_trades']}")
            
            # 自适应调整
            if elapsed > 10:
                self.config['top_n'] = max(10, self.config['top_n'] - 5)
                print(f"⚡ 优化: 降低扫描数量到 {self.config['top_n']}")
            
            time.sleep(interval)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=1800, help='扫描间隔(秒)')
    parser.add_argument('--once', action='store_true', help='单次扫描')
    args = parser.parse_args()
    
    scanner = XiamiScannerV2()
    
    if args.once:
        scanner.connect_exchanges()
        alerts, elapsed = scanner.scan_all()
        print(f"\n⏱️ 耗时: {elapsed:.2f}秒")
    else:
        scanner.run_continuous(args.interval)

if __name__ == "__main__":
    main()
