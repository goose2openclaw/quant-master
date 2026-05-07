#!/usr/bin/env python3
"""
XIAMI 实时预警系统 - 毫秒级价格变动检测
持续监控，发现极速信号立即预警
"""

import ccxt
import time
import json
import sqlite3
from datetime import datetime
from collections import deque

class RealtimeAlert:
    def __init__(self):
        self.exchange = ccxt.binance()
        
        # 监控标的
        self.symbols = [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 
            'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT',
            'DOT/USDT', 'MATIC/USDT', 'LINK/USDT', 'UNI/USDT'
        ]
        
        # 价格历史 (用于检测变动)
        self.price_history = {s: deque(maxlen=60) for s in self.symbols}
        
        # 预警阈值
        self.alert_config = {
            'price_change_1m': 1.0,    # 1分钟价格变动超过1%
            'price_change_3m': 2.5,   # 3分钟价格变动超过2.5%
            'volume_spike': 2.0,      # 成交量超过2倍
            'rsi_extreme': 25,        # RSI超卖
            'rsi_overbought': 75      # RSI超买
        }
        
        # 信号记录
        self.signals = []
        
    def get_realtime_data(self, symbol):
        """获取实时数据"""
        try:
            # 获取1分钟K线
            ohlcv_1m = self.exchange.fetch_ohlcv(symbol, '1m', limit=60)
            ohlcv_5m = self.exchange.fetch_ohlcv(symbol, '5m', limit=20)
            
            current_price = ohlcv_1m[-1][4]
            volume_1m = ohlcv_1m[-1][5]
            
            # 计算变化率
            closes_1m = [c[4] for c in ohlcv_1m]
            closes_5m = [c[4] for c in ohlcv_5m]
            
            change_1m = (closes_1m[-1] - closes_1m[-2]) / closes_1m[-2] * 100
            change_3m = (closes_1m[-1] - closes_1m[-3]) / closes_1m[-3] * 100
            
            # RSI
            deltas = [closes_1m[i] - closes_1m[i-1] for i in range(1, len(closes_1m))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            rsi = 100 - (100 / (1 + avg_gain / (avg_loss + 0.0001)))
            
            # 成交量
            avg_vol = sum([c[5] for c in ohlcv_1m[-10:]]) / 10
            vol_ratio = volume_1m / avg_vol if avg_vol > 0 else 1
            
            return {
                'price': current_price,
                'change_1m': change_1m,
                'change_3m': change_3m,
                'rsi': rsi,
                'vol_ratio': vol_ratio,
                'volume': volume_1m
            }
        except Exception as e:
            return None
    
    def check_alerts(self, symbol, data):
        """检查是否触发预警"""
        alerts = []
        cfg = self.alert_config
        
        # 价格变动预警
        if abs(data['change_1m']) >= cfg['price_change_1m']:
            direction = "🚀 暴涨" if data['change_1m'] > 0 else "💨 暴跌"
            alerts.append(f"{direction} {abs(data['change_1m']):.2f}% (1m)")
        
        if abs(data['change_3m']) >= cfg['price_change_3m']:
            direction = "📈 上涨" if data['change_3m'] > 0 else "📉 下跌"
            alerts.append(f"{direction} {abs(data['change_3m']):.2f}% (3m)")
        
        # RSI 预警
        if data['rsi'] <= cfg['rsi_extreme']:
            alerts.append(f"🔥 RSI超卖: {data['rsi']:.1f}")
        elif data['rsi'] >= cfg['rsi_overbought']:
            alerts.append(f"⚠️ RSI超买: {data['rsi']:.1f}")
        
        # 成交量预警
        if data['vol_ratio'] >= cfg['volume_spike']:
            alerts.append(f"💥 成交量爆发: {data['vol_ratio']:.1f}x")
        
        return alerts
    
    def run_once(self):
        """运行一次扫描"""
        print("="*60)
        print("🔔 XIAMI 实时预警系统")
        print(datetime.now().strftime('%H:%M:%S'))
        print("="*60)
        
        all_alerts = []
        
        for symbol in self.symbols:
            data = self.get_realtime_data(symbol)
            if not data:
                continue
            
            alerts = self.check_alerts(symbol, data)
            
            if alerts:
                print(f"\n🚨 {symbol}")
                print(f"   价格: ${data['price']:.4f}")
                for alert in alerts:
                    print(f"   {alert}")
                all_alerts.extend([(symbol, alert) for alert in alerts])
        
        if not all_alerts:
            print("\n✅ 无预警信号")
        
        return all_alerts
    
    def run_continuous(self, interval=30, duration=300):
        """持续运行"""
        print(f"开始持续监控 (每{interval}秒扫描, 共{duration}秒)")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            self.run_once()
            time.sleep(interval)

if __name__ == '__main__':
    alert = RealtimeAlert()
    alert.run_once()
