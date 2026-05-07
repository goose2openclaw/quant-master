#!/usr/bin/env python3
"""
🦐 XIAMI 智能交易系统
- 常规扫描 (15/30分钟)
- 趋势检测后自动启动高频量化
- 高频运行直到趋势消失
"""

import ccxt
import time
import json
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class XiamiSmart:
    """智能交易系统"""
    
    def __init__(self):
        # 常规配置
        self.config = {
            'quant': {
                'enabled': True,
                'trigger_change': 3.0,  # 触发高频量化的异动阈值
                'interval_ms': 500,       # 高频周期
                'min_change': 2.0,      # 最小异动
                'max_positions': 3,
                'position_size': 30,
            },
            'mainstream': {
                'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
            },
            'mole': {
                'scan_limit': 100,
            }
        }
        
        # 状态
        self.in_quant_mode = False
        self.quant_start_time = None
        self.trend_coins = []  # 当前趋势币种
        self.positions = []
        
        # API延迟
        self.api_latency = {}
        
    def test_api_speed(self):
        """测试API速度"""
        exchanges = ['binance', 'bybit', 'okx']
        
        for ex in exchanges:
            try:
                e = getattr(ccxt, ex)()
                start = time.time()
                e.fetch_time()
                self.api_latency[ex] = (time.time() - start) * 1000
            except:
                self.api_latency[ex] = 99999
        
        fastest = min(self.api_latency.items(), key=lambda x: x[1])
        print(f"🌐 最快API: {fastest[0]} ({fastest[1]:.0f}ms)")
        
        return fastest[0]
    
    def detect_trend(self):
        """检测趋势币种"""
        trends = []
        
        try:
            e = ccxt.binance()
            e.load_markets()
            
            # 扫描主流币+热门币
            symbols = self.config['mainstream']['symbols']
            markets = [m for m in e.markets.keys() if 'USDT' in m][:self.config['mole']['scan_limit']]
            tickers = e.fetch_tickers(markets)
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage', 0) or 0
                volume = ticker.get('quoteVolume', 0)
                
                # 趋势条件: 异动 > 阈值 且 成交量足够
                if abs(change) >= self.config['quant']['trigger_change'] and volume > 500000:
                    trends.append({
                        'symbol': symbol,
                        'change': change,
                        'volume': volume,
                        'price': ticker.get('last', 0),
                        'exchange': 'binance'
                    })
        
        except Exception as e:
            print(f"检测错误: {e}")
        
        return trends
    
    def quant_cycle(self, symbols):
        """高频量化周期"""
        config = self.config['quant']
        
        if not symbols:
            return []
        
        alerts = []
        
        try:
            e = getattr(ccxt, self.test_api_speed())()
            e.load_markets()
            
            tickers = e.fetch_tickers(symbols[:20])
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage', 0) or 0
                volume = ticker.get('quoteVolume', 0)
                
                if abs(change) >= config['min_change'] and volume > 100000:
                    alerts.append({
                        'symbol': symbol,
                        'price': ticker.get('last', 0),
                        'change': change,
                        'volume': volume,
                        'direction': 'LONG' if change > 0 else 'SHORT'
                    })
        
        except:
            pass
        
        return sorted(alerts, key=lambda x: abs(x['change']), reverse=True)
    
    def check_trend_end(self):
        """检查趋势是否结束"""
        if not self.trend_coins:
            return True
        
        # 检查趋势币是否仍然活跃
        still_active = []
        
        try:
            e = ccxt.binance()
            for coin in self.trend_coins[:5]:
                try:
                    ticker = e.fetch_ticker(coin['symbol'])
                    change = ticker.get('percentage', 0) or 0
                    
                    # 如果仍然在趋势中 (变化超过阈值)
                    if abs(change) >= self.config['quant']['trigger_change'] * 0.5:
                        coin['change'] = change
                        still_active.append(coin)
                except:
                    pass
        
        except:
            pass
        
        # 更新趋势币
        self.trend_coins = still_active
        
        # 如果没有活跃趋势币，结束高频模式
        if not self.trend_coins:
            return True
        
        return False
    
    def notify_trend_start(self, trends):
        """通知趋势开始"""
        msg = f"""
🦐 XIAMI 趋势检测

⚡ 检测到 {len(trends)} 个趋势币种!
即将启动高频量化...

{chr(10).join([f"• {t['symbol']}: {t['change']:+.1f}%" for t in trends[:5]])}

⏱️ 高频模式: 每{self.config['quant']['interval_ms']}ms判断
🛑 趋势消失后自动恢复常规扫描
"""
        print(msg)
    
    def notify_trend_end(self):
        """通知趋势结束"""
        msg = f"""
🦐 XIAMI 趋势结束

⚠️ 趋势已消失
✅ 恢复常规扫描 (15/30分钟)
"""
        print(msg)
    
    def run_quant_mode(self, duration=60):
        """运行高频量化模式"""
        print(f"\n⚡ 进入高频量化模式 (持续 {duration}秒)...")
        
        start = time.time()
        cycles = 0
        trades = 0
        
        while time.time() - start < duration:
            # 检查趋势是否结束
            if self.check_trend_end():
                print("📉 趋势消失，退出高频模式")
                break
            
            # 高频扫描
            alerts = self.quant_cycle(self.trend_coins)
            
            if alerts and len(self.positions) < self.config['quant']['max_positions']:
                # 执行交易
                alert = alerts[0]
                
                # 检查是否已交易
                if not any(p['symbol'] == alert['symbol'] for p in self.positions):
                    trade = {
                        'symbol': alert['symbol'],
                        'direction': alert['direction'],
                        'price': alert['price'],
                        'change': alert['change'],
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
                    self.positions.append(trade)
                    trades += 1
                    
                    emoji = "📈" if alert['direction'] == "LONG" else "📉"
                    print(f"{emoji} 执行: {alert['symbol']} {alert['direction']} @ ${alert['price']:.4f}")
            
            cycles += 1
            time.sleep(self.config['quant']['interval_ms'] / 1000)
        
        print(f"\n⚡ 高频模式结束: {cycles}周期, {trades}笔交易")
        
        # 清空仓位记录
        self.positions = []
        
        return trades
    
    def run_normal_scan(self):
        """常规扫描模式"""
        print("\n📊 常规扫描...")
        
        # 检测趋势
        trends = self.detect_trend()
        
        if trends:
            print(f"⚡ 发现 {len(trends)} 个趋势币!")
            
            # 记录趋势币
            self.trend_coins = trends
            
            # 通知
            self.notify_trend_start(trends)
            
            # 启动高频量化
            self.run_quant_mode(duration=120)  # 高频运行2分钟
            
            # 检查趋势
            if not self.check_trend_end():
                # 趋势继续，再运行一轮
                print("📈 趋势持续，继续高频...")
                self.run_quant_mode(duration=120)
            
            # 趋势结束
            self.notify_trend_end()
            
        else:
            print("⚪ 无明显趋势")
    
    def run_cycle(self):
        """完整周期"""
        print("="*60)
        print("🦐 XIAMI 智能交易系统")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 测试API
        self.test_api_speed()
        
        # 常规扫描
        self.run_normal_scan()
        
        print("\n✅ 周期完成")

def main():
    xiami = XiamiSmart()
    xiami.run_cycle()

if __name__ == "__main__":
    main()
