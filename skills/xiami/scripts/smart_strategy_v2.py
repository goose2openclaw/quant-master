#!/usr/bin/env python3
"""
🦐 XIAMI 智能交易系统 v2
- 常规扫描 (15/30分钟)
- 趋势检测后自动启动高频量化
- 高频: 每200-1000ms判断一次
- 趋势消失后恢复常规扫描
"""

import ccxt
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class XiamiSmartV2:
    """智能交易系统"""
    
    def __init__(self):
        # 配置
        self.config = {
            # 常规扫描
            'normal': {
                'interval': 900,  # 15分钟
            },
            # 高频量化
            'quant': {
                'trigger_change': 3.0,  # 触发阈值
                'check_interval': 500,   # 500ms检查一次
                'min_change': 2.0,      # 最小交易异动
                'max_positions': 3,
                'position_size': 30,
            }
        }
        
        # 状态
        self.in_quant_mode = False
        self.quant_start = None
        self.trend_coins = []  # 当前趋势币
        self.positions = []    # 当前持仓
        
        # API
        self.api_latency = {}
        self.fastest_ex = 'binance'
        
    def test_api(self):
        """API测速"""
        for ex in ['binance', 'bybit', 'okx']:
            try:
                e = getattr(ccxt, ex)()
                start = time.time()
                e.fetch_time()
                self.api_latency[ex] = (time.time() - start) * 1000
            except:
                self.api_latency[ex] = 99999
        
        self.fastest_ex = min(self.api_latency.items(), key=lambda x: x[1])[0]
        return self.fastest_ex
    
    def detect_trend(self):
        """检测趋势币"""
        trends = []
        
        try:
            e = getattr(ccxt, self.fastest_ex)()
            e.load_markets()
            
            markets = [m for m in e.markets.keys() if 'USDT' in m][:100]
            tickers = e.fetch_tickers(markets)
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage') or 0
                volume = ticker.get('quoteVolume', 0)
                
                # 趋势条件
                if abs(change) >= self.config['quant']['trigger_change'] and volume > 500000:
                    trends.append({
                        'symbol': symbol,
                        'change': change,
                        'volume': volume,
                        'price': ticker.get('last', 0),
                    })
        
        except Exception as e:
            print(f"检测错误: {e}")
        
        return sorted(trends, key=lambda x: abs(x['change']), reverse=True)
    
    def check_trend_live(self, symbols):
        """高频检测: 实时检查趋势是否存活"""
        if not symbols:
            return False, []
        
        active = []
        
        try:
            e = getattr(ccxt, self.fastest_ex)()
            active_tickers = e.fetch_tickers(symbols[:10])
            
            for symbol in symbols[:10]:
                if symbol not in active_tickers:
                    continue
                    
                t = active_tickers[symbol]
                change = t.get('percentage') or 0
                
                # 趋势仍在 (变化大于阈值的50%)
                if abs(change) >= self.config['quant']['trigger_change'] * 0.5:
                    active.append({
                        'symbol': symbol,
                        'change': change,
                        'price': t.get('last', 0),
                    })
        
        except:
            pass
        
        return len(active) > 0, active
    
    def quant_once(self):
        """高频: 执行一次判断和操作"""
        config = self.config['quant']
        
        if not self.trend_coins:
            return None
        
        # 获取趋势币的实时数据
        symbols = [c['symbol'] for c in self.trend_coins]
        
        alerts = []
        
        try:
            e = getattr(ccxt, self.fastest_ex)()
            tickers = e.fetch_tickers(symbols[:10])
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage') or 0
                volume = ticker.get('quoteVolume', 0)
                
                if abs(change) >= config['min_change'] and volume > 100000:
                    alerts.append({
                        'symbol': symbol,
                        'change': change,
                        'price': ticker.get('last', 0),
                        'direction': 'BUY' if change > 0 else 'SELL'
                    })
        
        except:
            pass
        
        if not alerts:
            return None
        
        # 按变化排序，取最强信号
        alerts.sort(key=lambda x: abs(x['change']), reverse=True)
        signal = alerts[0]
        
        # 检查是否已持仓
        if any(p['symbol'] == signal['symbol'] for p in self.positions):
            return None
        
        # 执行交易
        if len(self.positions) < config['max_positions']:
            self.positions.append(signal)
            
            return {
                'action': 'TRADE',
                'symbol': signal['symbol'],
                'direction': signal['direction'],
                'price': signal['price'],
                'change': signal['change'],
                'time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
            }
        
        return None
    
    def run_quant_mode(self, max_duration=180):
        """运行高频模式"""
        print(f"\n⚡ 高频量化模式 (每{self.config['quant']['check_interval']}ms判断)")
        print(f"   趋势币: {[c['symbol'] for c in self.trend_coins[:3]]}")
        
        start = time.time()
        cycles = 0
        trades = 0
        
        while time.time() - start < max_duration:
            # 检查趋势是否存活
            is_active, active_coins = self.check_trend_live([c['symbol'] for c in self.trend_coins])
            
            if not is_active:
                print(f"\n📉 趋势消失，退出高频模式")
                break
            
            # 更新趋势币
            self.trend_coins = active_coins
            
            # 高频判断一次
            result = self.quant_once()
            
            if result:
                trades += 1
                emoji = "🟢" if result['direction'] == 'BUY' else "🔴"
                print(f"{emoji} [{result['time']}] {result['direction']} {result['symbol']} @ ${result['price']:.4f} ({result['change']:+.1f}%)")
            
            cycles += 1
            
            # 等待下一个周期
            time.sleep(self.config['quant']['check_interval'] / 1000)
        
        # 清理持仓
        self.positions = []
        
        print(f"\n⚡ 高频结束: {cycles}次判断, {trades}笔交易")
        
        return trades
    
    def run_normal_mode(self):
        """常规模式"""
        print(f"\n📊 常规扫描 (每{self.config['normal']['interval']}秒)")
        
        # 检测趋势
        trends = self.detect_trend()
        
        if trends:
            print(f"⚡ 发现 {len(trends)} 个趋势币!")
            
            # 记录趋势币
            self.trend_coins = trends
            
            # 启动高频
            trades = self.run_quant_mode(max_duration=120)
            
            # 检查是否继续趋势
            is_active, _ = self.check_trend_live([c['symbol'] for c in self.trend_coins])
            
            if is_active:
                print("📈 趋势持续，继续高频...")
                self.run_quant_mode(max_duration=120)
            
            print("\n✅ 恢复常规扫描")
        else:
            print("⚪ 无明显趋势")
    
    def run(self):
        """主循环"""
        print("="*60)
        print("🦐 XIAMI 智能交易系统 v2")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # API测速
        self.test_api()
        
        # 常规扫描
        self.run_normal_mode()
        
        print("\n✅ 周期完成")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=500, help='高频检查间隔(ms)')
    parser.add_argument('--duration', type=int, default=120, help='高频持续时间(秒)')
    args = parser.parse_args()
    
    xiami = XiamiSmartV2()
    xiami.config['quant']['check_interval'] = args.interval
    xiami.run()

if __name__ == "__main__":
    main()
