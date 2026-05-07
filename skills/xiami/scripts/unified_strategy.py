#!/usr/bin/env python3
"""
🦐 XIAMI 整合策略系统
- 多层扫描 (高频量化 + 打地鼠 + 主流币)
- API速度优化
- 自动通知
- 持续迭代
"""

import ccxt
import time
import json
import requests
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class XiamiUnified:
    """XIAMI 整合策略"""
    
    def __init__(self):
        # 配置
        self.config = {
            # 高频量化
            'quant': {
                'enabled': True,
                'interval_ms': 200,
                'min_change': 3.0,
                'max_positions': 3,
                'position_size': 30,
                'stop_loss': 0.02,
                'take_profit': 0.05,
            },
            # 打地鼠
            'mole': {
                'enabled': True,
                'interval': 900,  # 15分钟
                'min_change': 5.0,
                'max_coins': 3,
                'position_size': 50,
            },
            # 主流币
            'mainstream': {
                'enabled': True,
                'interval': 1800,  # 30分钟
                'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT'],
                'position_size': 100,
            },
            # 通知
            'notify': {
                'enabled': True,
                'webhook': '',  # Discord/Slack webhook
                'telegram': '',  # Telegram bot token
                'telegram_chat_id': '',
            }
        }
        
        # API延迟缓存
        self.api_latency = {}
        
        # 信号历史
        self.signal_history = []
        
        # 持仓
        self.positions = []
        
    def test_api_speed(self):
        """测试API速度"""
        exchanges = ['binance', 'bybit', 'okx', 'gate', 'mexc']
        
        for ex in exchanges:
            try:
                e = getattr(ccxt, ex)()
                start = time.time()
                e.fetch_time()
                latency = (time.time() - start) * 1000
                self.api_latency[ex] = latency
            except:
                self.api_latency[ex] = 99999
        
        # 排序
        sorted_api = sorted(self.api_latency.items(), key=lambda x: x[1])
        
        print(f"\n🌐 API速度: {sorted_api[0][0]} ({sorted_api[0][1]:.0f}ms) 最快")
        
        return sorted_api[0][0]
    
    def notify(self, message):
        """发送通知"""
        if not self.config['notify']['enabled']:
            return
        
        print(f"\n📱 发送通知...")
        
        # Telegram
        if self.config['notify']['telegram']:
            try:
                url = f"https://api.telegram.org/bot{self.config['notify']['telegram']}/sendMessage"
                data = {
                    'chat_id': self.config['notify']['telegram_chat_id'],
                    'text': message
                }
                requests.post(url, json=data, timeout=5)
                print("✅ Telegram 发送成功")
            except Exception as e:
                print(f"❌ Telegram 失败: {e}")
        
        # Discord Webhook
        if self.config['notify']['webhook']:
            try:
                data = {'content': message}
                requests.post(self.config['notify']['webhook'], json=data, timeout=5)
                print("✅ Discord 发送成功")
            except Exception as e:
                print(f"❌ Discord 失败: {e}")
    
    def quant_scan(self):
        """高频量化扫描 (200ms)"""
        config = self.config['quant']
        if not config['enabled']:
            return []
        
        # 使用最快交易所
        sorted_api = sorted(self.api_latency.items(), key=lambda x: x[1])
        fast_ex = sorted_api[0][0]
        
        alerts = []
        
        try:
            e = getattr(ccxt, fast_ex)()
            e.load_markets()
            
            markets = [m for m in e.markets.keys() if 'USDT' in m][:50]
            tickers = e.fetch_tickers(markets)
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage') or 0
                volume = ticker.get('quoteVolume', 0)
                
                if abs(change) >= config['min_change'] and volume > 100000:
                    alerts.append({
                        'type': 'QUANT',
                        'symbol': symbol,
                        'exchange': fast_ex,
                        'price': ticker.get('last', 0),
                        'change': change,
                        'volume': volume,
                        'priority': abs(change) * (volume/1e6)
                    })
                    
        except:
            pass
        
        return sorted(alerts, key=lambda x: x['priority'], reverse=True)
    
    def mole_scan(self):
        """打地鼠扫描"""
        config = self.config['mole']
        
        alerts = []
        
        try:
            e = ccxt.binance()
            e.load_markets()
            
            markets = [m for m in e.markets.keys() if 'USDT' in m][:100]
            tickers = e.fetch_tickers(markets)
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage') or 0
                volume = ticker.get('quoteVolume', 0)
                
                if abs(change) >= config['min_change'] and volume > 50000:
                    alerts.append({
                        'type': 'MOLE',
                        'symbol': symbol,
                        'exchange': 'binance',
                        'price': ticker.get('last', 0),
                        'change': change,
                        'volume': volume,
                    })
                    
        except:
            pass
        
        return sorted(alerts, key=lambda x: abs(x['change']), reverse=True)
    
    def mainstream_scan(self):
        """主流币扫描"""
        config = self.config['mainstream']
        
        alerts = []
        
        try:
            e = ccxt.binance()
            
            for symbol in config['symbols']:
                try:
                    ticker = e.fetch_ticker(symbol)
                    change = ticker.get('percentage') or 0
                    
                    # 回调买入信号
                    if -5 < change < -2:
                        alerts.append({
                            'type': 'MAINSTREAM',
                            'signal': 'BUY_CALLBACK',
                            'symbol': symbol,
                            'price': ticker.get('last', 0),
                            'change': change,
                            'reason': f'回调 {change:.1f}%'
                        })
                    elif change > 2:
                        alerts.append({
                            'type': 'MAINSTREAM', 
                            'signal': 'BUY_BREAKOUT',
                            'symbol': symbol,
                            'price': ticker.get('last', 0),
                            'change': change,
                            'reason': f'突破 {change:.1f}%'
                        })
                        
                except:
                    continue
                    
        except:
            pass
        
        return alerts
    
    def generate_notification(self, alert):
        """生成通知消息"""
        emoji = "📈" if alert.get('change', 0) > 0 else "📉"
        
        msg = f"""
🦐 XIAMI 交易信号

类型: {alert['type']}
{emoji} 币种: {alert['symbol']}
💰 价格: ${alert.get('price', 0):.6f}
📊 涨跌: {alert.get('change', 0):+.1f}%

原因: {alert.get('reason', alert.get('signal', '异动'))}
⏰ 时间: {datetime.now().strftime('%H:%M:%S')}
"""
        
        return msg
    
    def run_cycle(self):
        """运行完整周期"""
        print("="*60)
        print("🦐 XIAMI 整合策略系统")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 1. API测速
        fastest = self.test_api_speed()
        
        # 2. 高频量化
        if self.config['quant']['enabled']:
            print("\n⚡ 高频量化扫描...")
            quant_alerts = self.quant_scan()
            
            if quant_alerts:
                top = quant_alerts[0]
                print(f"   ⚡ 信号: {top['symbol']} {top['change']:+.1f}%")
                
                # 通知
                msg = self.generate_notification(top)
                self.notify(msg)
        
        # 3. 打地鼠
        if self.config['mole']['enabled']:
            print("\n🎯 打地鼠扫描...")
            mole_alerts = self.mole_scan()
            
            if mole_alerts:
                for a in mole_alerts[:3]:
                    print(f"   🎯 {a['symbol']} {a['change']:+.1f}%")
                    msg = self.generate_notification(a)
                    self.notify(msg)
        
        # 4. 主流币
        if self.config['mainstream']['enabled']:
            print("\n📈 主流币扫描...")
            mainstream_alerts = self.mainstream_scan()
            
            if mainstream_alerts:
                for a in mainstream_alerts[:2]:
                    print(f"   📈 {a['symbol']}: {a['reason']}")
                    msg = self.generate_notification(a)
                    self.notify(msg)
        
        print("\n✅ 扫描完成")
    
    def run_continuously(self, duration=3600):
        """持续运行"""
        print(f"🚀 开始持续运行 ({duration}秒)...")
        
        start = time.time()
        
        while time.time() - start < duration:
            self.run_cycle()
            
            # 等待
            time.sleep(60)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--notify', action='store_true', help='启用通知')
    parser.add_argument('--telegram_token', default='', help='Telegram Token')
    parser.add_argument('--telegram_chat_id', default='', help='Telegram Chat ID')
    parser.add_argument('--discord_webhook', default='', help='Discord Webhook')
    args = parser.parse_args()
    
    xiami = XiamiUnified()
    
    # 配置通知
    if args.notify:
        xiami.config['notify']['enabled'] = True
        xiami.config['notify']['telegram'] = args.telegram_token
        xiami.config['notify']['telegram_chat_id'] = args.telegram_chat_id
        xiami.config['notify']['webhook'] = args.discord_webhook
    
    xiami.run_cycle()

if __name__ == "__main__":
    main()
