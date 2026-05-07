#!/usr/bin/env python3
"""
🦐 XIAMI 分层交易系统
- 主流币: 低风险，稳定收益
- 山寨币: 高风险，高收益
"""

import ccxt
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class XiamiTieredTrading:
    """分层交易系统"""
    
    def __init__(self):
        # 主流币 (Tier 1) - 低波动，稳定
        self.tier1 = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 
            'SOL/USDT', 'XRP/USDT', 'ADA/USDT',
            'DOGE/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT'
        ]
        
        # 山寨币 (Tier 2) - 高波动，高风险
        self.tier2 = []
        
        # 配置
        self.config = {
            'tier1': {
                'max_position': 0.15,  # 15%仓位
                'stop_loss': 0.03,     # 3%止损
                'take_profit': 0.08,   # 8%止盈
                'min_change': 2,       # 最小波动
            },
            'tier2': {
                'max_position': 0.08,  # 8%仓位
                'stop_loss': 0.05,     # 5%止损
                'take_profit': 0.15,   # 15%止盈
                'min_change': 4,       # 最小波动
            }
        }
        
    def get_tier2_coins(self, exchange):
        """获取高潜力山寨币"""
        try:
            markets = [m for m in exchange.markets.keys() if 'USDT' in m]
            tickers = exchange.fetch_tickers(markets[:100])
            
            candidates = []
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage') or 0
                volume = ticker.get('quoteVolume', 0)
                
                # 过滤条件
                if volume > 100000 and abs(change) > 3:
                    # 排除主流币
                    if symbol not in self.tier1:
                        candidates.append({
                            'symbol': symbol,
                            'change': change,
                            'volume': volume
                        })
            
            # 按波动排序
            candidates.sort(key=lambda x: abs(x['change']), reverse=True)
            return [c['symbol'] for c in candidates[:10]]
            
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def scan_tier(self, exchange_name, symbols, tier):
        """扫描层级"""
        config = self.config[tier]
        alerts = []
        
        try:
            exchange = getattr(ccxt, exchange_name)()
            exchange.load_markets()
            
            tickers = exchange.fetch_tickers(symbols)
            
            for symbol, ticker in tickers.items():
                change = ticker.get('percentage') or 0
                volume = ticker.get('quoteVolume', 0)
                
                if abs(change) >= config['min_change'] and volume > 50000:
                    score = abs(change) * (volume / 1e6)
                    
                    alerts.append({
                        'symbol': symbol,
                        'exchange': exchange_name,
                        'price': ticker.get('last', 0),
                        'change': change,
                        'volume': volume,
                        'score': score,
                        'tier': tier
                    })
                    
        except Exception as e:
            print(f"❌ {exchange_name}: {e}")
        
        return alerts
    
    def scan_all(self):
        """全市场扫描"""
        print("\n" + "="*60)
        print("🦐 XIAMI 分层交易系统")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        all_alerts = []
        
        # Tier 1 扫描 (主流币)
        print("\n📊 Tier 1 主流币扫描...")
        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = [ex.submit(self.scan_tier, 'binance', self.tier1, 'tier1')]
            for f in futures:
                all_alerts.extend(f.result())
        
        # Tier 2 扫描 (自动发现山寨币)
        print("📊 Tier 2 山寨币扫描...")
        try:
            binance = ccxt.binance()
            binance.load_markets()
            self.tier2 = self.get_tier2_coins(binance)[:20]
            
            with ThreadPoolExecutor(max_workers=3) as ex:
                futures = [ex.submit(self.scan_tier, 'binance', self.tier2[:10], 'tier2')]
                for f in futures:
                    all_alerts.extend(f.result())
                    
        except Exception as e:
            print(f"❌ Tier2: {e}")
        
        # 排序
        all_alerts.sort(key=lambda x: x['score'], reverse=True)
        
        return all_alerts
    
    def generate_signal(self, alert):
        """生成信号"""
        tier = alert['tier']
        config = self.config[tier]
        change = alert['change']
        
        if tier == 'tier1':
            # 主流币: 稳健
            if change > config['min_change']:
                return "🟢 买入", 8, "Tier1-稳健"
            elif change < -config['min_change']:
                return "🔴 卖出", -8, "Tier1-稳健"
        else:
            # 山寨币: 激进
            if change > 8:
                return "🟢🟢 强力买入", 10, "Tier2-高风险"
            elif change > config['min_change']:
                return "🟢 买入", 6, "Tier2-高风险"
            elif change < -8:
                return "🔴🔴 强力卖出", -10, "Tier2-高风险"
            elif change < -config['min_change']:
                return "🔴 卖出", -6, "Tier2-高风险"
        
        return "⚪ 观望", 0, ""
    
    def run(self):
        """运行系统"""
        alerts = self.scan_all()
        
        print(f"\n📊 发现 {len(alerts)} 个信号")
        
        # 分类显示
        tier1_alerts = [a for a in alerts if a['tier'] == 'tier1']
        tier2_alerts = [a for a in alerts if a['tier'] == 'tier2']
        
        print("\n" + "="*60)
        print("🏆 TIER 1 - 主流币 (低风险)")
        print("="*60)
        for a in tier1_alerts[:5]:
            signal, score, note = self.generate_signal(a)
            emoji = "📈" if a['change'] > 0 else "📉"
            print(f"{emoji} {a['symbol']}: {a['change']:+.1f}% | {signal}")
        
        print("\n" + "="*60)
        print("🔥 TIER 2 - 山寨币 (高风险)")
        print("="*60)
        for a in tier2_alerts[:5]:
            signal, score, note = self.generate_signal(a)
            emoji = "📈" if a['change'] > 0 else "📉"
            print(f"{emoji} {a['symbol']}: {a['change']:+.1f}% | {signal}")
        
        # 交易决策
        print("\n" + "="*60)
        print("🎯 交易信号")
        print("="*60)
        
        trades = []
        
        # Tier1: 最多2个
        for a in tier1_alerts[:2]:
            signal, score, note = self.generate_signal(a)
            if score != 0:
                trades.append({
                    'tier': 'TIER1',
                    'symbol': a['symbol'],
                    'action': signal,
                    'position': '15%',
                    'stop_loss': '3%',
                    'take_profit': '8%'
                })
        
        # Tier2: 最多3个
        for a in tier2_alerts[:3]:
            signal, score, note = self.generate_signal(a)
            if abs(score) >= 6:
                trades.append({
                    'tier': 'TIER2',
                    'symbol': a['symbol'],
                    'action': signal,
                    'position': '8%',
                    'stop_loss': '5%',
                    'take_profit': '15%'
                })
        
        for t in trades:
            print(f"\n{t['tier']} | {t['action']} {t['symbol']}")
            print(f"   仓位: {t['position']} | 止损: {t['stop_loss']} | 止盈: {t['take_profit']}")
        
        if not trades:
            print("⚪ 无交易信号")
        
        return trades

if __name__ == "__main__":
    system = XiamiTieredTrading()
    system.run()
