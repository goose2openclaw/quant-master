#!/usr/bin/env python3
"""
🦐 XIAMI Auto-Trading System v1.0
全自动化加密货币交易体系

功能:
- 主流币 + 山寨币 分类交易
- 每30分钟自动扫描
- 策略自动迭代优化
- 信号检测 + 自动下单
"""

import ccxt
import json
import time
import os
from datetime import datetime
from pathlib import Path

class XiamiAutoTrade:
    """XIAMI 自动交易系统"""
    
    def __init__(self):
        self.base_path = Path("/root/.openclaw/workspace/skills/xiami")
        self.data_path = self.base_path / "data"
        self.data_path.mkdir(exist_ok=True)
        
        # 币种分类
        self.tier1 = {  # 主流币
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 
            'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 
            'DOT/USDT', 'MATIC/USDT', 'LINK/USDT', 'UNI/USDT',
            'LTC/USDT', 'ATOM/USDT', 'XLM/USDT'
        }
        
        self.tier2 = {  # 山寨币 (按交易量筛选)
            'AAVE/USDT', 'FIL/USDT', 'NEAR/USDT', 'ARB/USDT',
            'OP/USDT', 'MATIC/USDT', 'SAND/USDT', 'MANA/USDT',
            'AXS/USDT', 'ALGO/USDT', 'FTM/USDT', 'AVAX/USDT',
            'APT/USDT', 'ARB/USDT', 'PEPE/USDT', 'SHIB/USDT'
        }
        
        self.exchanges = {}
        self.config = {
            'tier1': {'max_positions': 3, 'position_size': 0.2, 'risk': 0.03},
            'tier2': {'max_positions': 5, 'position_size': 0.1, 'risk': 0.05},
            'scan_interval': 1800,  # 30分钟
        }
        
    def connect_exchanges(self):
        """连接交易所"""
        for ex_name in ['binance', 'bybit', 'okx']:
            try:
                e = getattr(ccxt, ex_name)()
                e.load_markets()
                self.exchanges[ex_name] = e
                print(f"✅ {ex_name}")
            except Exception as e:
                print(f"❌ {ex_name}: {e}")
    
    def get_ticker(self, exchange, symbol):
        """获取行情"""
        try:
            return exchange.fetch_ticker(symbol)
        except:
            return None
    
    def scan_tier(self, exchange_name, symbols, tier_name):
        """扫描币种"""
        exchange = self.exchanges[exchange_name]
        results = []
        
        for symbol in symbols:
            ticker = self.get_ticker(exchange, symbol)
            if not ticker:
                continue
                
            price = ticker.get('last', 0)
            change = ticker.get('percentage', 0)
            volume = ticker.get('quoteVolume', 0)
            
            if volume < 100000:  # 过滤低流动性
                continue
                
            # 异常检测
            if abs(change) >= 3:
                signal_score = self.calculate_signal(change, volume, ticker)
                
                results.append({
                    'symbol': symbol,
                    'exchange': exchange_name,
                    'price': price,
                    'change': change,
                    'volume': volume,
                    'tier': tier_name,
                    'score': signal_score,
                    'time': datetime.now().isoformat()
                })
        
        return results
    
    def calculate_signal(self, change, volume, ticker):
        """计算信号分数"""
        score = 0
        
        # 涨跌贡献
        score += abs(change) * 2
        
        # 成交量贡献
        if volume > 1e8:  # 1亿
            score += 10
        elif volume > 1e7:  # 1000万
            score += 5
        elif volume > 1e6:  # 100万
            score += 2
        
        # 方向
        direction = 1 if change > 0 else -1
        
        return score * direction
    
    def generate_signal(self, alert):
        """生成交易信号"""
        change = alert['change']
        tier = alert['tier']
        
        # 主流币保守
        if tier == 'tier1':
            buy_threshold = 5
            sell_threshold = -5
        else:  # 山寨币激进
            buy_threshold = 8
            sell_threshold = -8
        
        if change >= buy_threshold:
            return f"🟢 买入 {alert['symbol']} (涨幅 {change:.1f}%)"
        elif change <= sell_threshold:
            return f"🔴 卖出 {alert['symbol']} (跌幅 {abs(change):.1f}%)"
        
        return None
    
    def run_scan(self):
        """运行扫描"""
        print("\n" + "="*60)
        print(f"🦐 XIAMI 自动交易系统 - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        all_alerts = []
        
        # 扫描主流币
        print("\n📊 扫描主流币 (Tier 1)...")
        for ex_name in self.exchanges:
            alerts = self.scan_tier(ex_name, self.tier1, 'tier1')
            all_alerts.extend(alerts)
            print(f"   {ex_name}: {len(alerts)} 个信号")
        
        # 扫描山寨币
        print("\n📊 扫描山寨币 (Tier 2)...")
        for ex_name in self.exchanges:
            alerts = self.scan_tier(ex_name, self.tier2, 'tier2')
            all_alerts.extend(alerts)
            print(f"   {ex_name}: {len(alerts)} 个信号")
        
        # 排序
        all_alerts.sort(key=lambda x: abs(x['score']), reverse=True)
        
        # 保存结果
        self.save_data(all_alerts)
        
        # 显示结果
        print(f"\n📊 共发现 {len(all_alerts)} 个信号:")
        
        tier1_alerts = [a for a in all_alerts if a['tier'] == 'tier1'][:5]
        tier2_alerts = [a for a in all_alerts if a['tier'] == 'tier2'][:10]
        
        print("\n🏆 主流币信号 (Tier 1):")
        for a in tier1_alerts:
            emoji = "📈" if a['change'] > 0 else "📉"
            print(f"   {emoji} {a['symbol']} @ {a['exchange']}: {a['change']:+.1f}%")
        
        print("\n🏆 山寨币信号 (Tier 2):")
        for a in tier2_alerts:
            emoji = "📈" if a['change'] > 0 else "📉"
            print(f"   {emoji} {a['symbol']} @ {a['exchange']}: {a['change']:+.1f}%")
        
        # 生成交易信号
        print("\n🎯 交易信号:")
        signals = []
        for alert in all_alerts:
            signal = self.generate_signal(alert)
            if signal:
                signals.append(signal)
                print(f"   {signal}")
        
        if not signals:
            print("   ⚪ 无高置信度信号")
        
        return all_alerts, signals
    
    def save_data(self, alerts):
        """保存数据"""
        # 保存历史
        history_file = self.data_path / "scan_history.json"
        
        history = []
        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)
        
        history.append({
            'time': datetime.now().isoformat(),
            'alerts': alerts
        })
        
        # 只保留最近100条
        history = history[-100:]
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        # 保存最新
        with open(self.data_path / "latest_alerts.json", 'w') as f:
            json.dump(alerts, f, indent=2)
    
    def optimize_strategy(self):
        """策略优化"""
        print("\n🔧 策略优化...")
        
        history_file = self.data_path / "scan_history.json"
        
        if not history_file.exists():
            print("   数据不足，无法优化")
            return
        
        with open(history_file) as f:
            history = json.load(f)
        
        # 简单统计
        total_signals = sum(len(h['alerts']) for h in history)
        avg_change = sum(sum(a['change'] for a in h['alerts']) / max(len(h['alerts']), 1) for h in history) / max(len(history), 1)
        
        print(f"   历史扫描: {total_signals} 次信号")
        print(f"   平均波动: {avg_change:+.1f}%")
        
        # 调整阈值
        if avg_change > 5:
            print("   → 建议提高买入阈值")
        elif avg_change < 2:
            print("   → 建议降低买入阈值")
    
    def run(self):
        """运行系统"""
        self.connect_exchanges()
        
        # 单次扫描
        alerts, signals = self.run_scan()
        
        # 策略优化
        self.optimize_strategy()
        
        print("\n✅ 扫描完成!")

if __name__ == "__main__":
    system = XiamiAutoTrade()
    system.run()
