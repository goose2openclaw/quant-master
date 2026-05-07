#!/usr/bin/env python3
"""
Hermes v3.mvsk 30天全面回测
普通模式 vs 专家模式
"""

import requests, time, json, numpy as np
from datetime import datetime, timedelta
from itertools import product

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

# 币种
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, interval='1d', days=30):
    """获取K线数据"""
    end = int(time.time() * 1000)
    start = end - days * 86400 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit=1000'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        data = []
        for k in r.json():
            data.append({
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'time': int(k[0])
            })
        return data
    except Exception as e:
        print(f"  K线获取失败 {sym}: {e}")
        return []

def bollinger_position(price, high, low, period=20):
    """布林带位置"""
    if high == low: return 50
    return (price - low) / (high - low) * 100

class Backtester:
    def __init__(self, initial_capital=1000, mode='normal'):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.mode = mode
        self.trades = []
        self.positions = {c: 0 for c in COINS}
        self.history = []
        
        # 模式参数
        if mode == 'normal':
            self.leverage = 1.0
            self.position_size = 0.1  # 10%仓位
            self.threshold_buy = 20   # 位置<20%买入
            self.threshold_sell = 80  # 位置>80%卖出
        else:  # expert
            self.leverage = 3.0
            self.position_size = 0.3  # 30%仓位
            self.threshold_buy = 15
            self.threshold_sell = 85
        
    def reset(self):
        self.capital = self.initial_capital
        self.trades = []
        self.positions = {c: 0 for c in COINS}
        self.history = []
    
    def simulate(self, price_data):
        """模拟交易"""
        for day_idx in range(len(price_data)):
            day_data = {c: price_data[c][day_idx] for c in COINS if day_idx < len(price_data[c])}
            if not day_data: continue
            
            # 记录每日状态
            portfolio_value = self.capital + sum(self.positions[c] * day_data[c]['close'] for c in COINS)
            self.history.append({
                'day': day_idx,
                'portfolio': portfolio_value,
                'cash': self.capital
            })
            
            # 决策
            for c in COINS:
                if c not in day_data: continue
                d = day_data[c]
                pos = bollinger_position(d['close'], d['high'], d['low'])
                
                # 买入信号
                if pos < self.threshold_buy and self.capital > 10:
                    invest = self.capital * self.position_size * self.leverage
                    qty = invest / d['close']
                    cost = qty * d['close']
                    self.capital -= cost
                    self.positions[c] += qty
                    self.trades.append({'type':'BUY','coin':c,'price':d['close'],'qty':qty,'day':day_idx})
                
                # 卖出信号
                elif pos > self.threshold_sell and self.positions[c] > 0:
                    qty = self.positions[c] * 0.5  # 卖出一半
                    revenue = qty * d['close']
                    self.capital += revenue
                    self.positions[c] -= qty
                    self.trades.append({'type':'SELL','coin':c,'price':d['close'],'qty':qty,'day':day_idx})
        
        # 最终结算
        final_prices = {c: price_data[c][-1]['close'] for c in COINS if c in price_data}
        final_value = self.capital + sum(self.positions[c] * final_prices.get(c, 0) for c in COINS)
        return final_value
    
    def get_stats(self, final_value):
        """计算统计指标"""
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # 统计交易
        buys = [t for t in self.trades if t['type'] == 'BUY']
        sells = [t for t in self.trades if t['type'] == 'SELL']
        
        # 计算胜率
        wins = losses = 0
        for i, sell in enumerate([t for t in self.trades if t['type'] == 'SELL']):
            buy_prices = [t['price'] for t in reversed(buys) if t['coin'] == sell['coin']]
            if buy_prices and sell['price'] > buy_prices[0]:
                wins += 1
            else:
                losses += 1
        
        win_rate = wins / (wins + losses) * 100 if wins + losses > 0 else 0
        
        # 资金使用率
        max_used = max([h['cash'] for h in self.history]) if self.history else self.initial_capital
        capital_usage = (self.initial_capital - min([h['cash'] for h in self.history])) / self.initial_capital * 100 if self.history else 0
        
        return {
            'return': total_return,
            'win_rate': win_rate,
            'leverage': self.leverage,
            'capital_usage': capital_usage,
            'total_trades': len(self.trades),
            'buys': len(buys),
            'sells': len(sells),
            'wins': wins,
            'losses': losses
        }

def main():
    print("="*70)
    print("Hermes v3.mvsk 30天全面回测")
    print("="*70)
    
    # 获取数据
    print("\n【1. 获取30天K线数据】")
    price_data = {}
    for c in COINS:
        print(f"  获取 {c}...", end=' ')
        data = get_klines(f'{c}USDT', '1d', 30)
        if data:
            price_data[c] = data
            print(f"{len(data)}条")
        else:
            print("失败")
        time.sleep(0.3)
    
    if not price_data:
        print("无法获取数据!")
        return
    
    days = min(len(price_data[c]) for c in price_data)
    print(f"\n数据天数: {days}天")
    
    # 回测参数矩阵
    modes = ['normal', 'expert']
    leverages = [1.0, 2.0, 3.0, 5.0]
    position_sizes = [0.1, 0.2, 0.3, 0.5]
    
    results = []
    
    print("\n【2. 执行回测】")
    for mode, lev, pos_size in product(modes, leverages, position_sizes):
        bt = Backtester(initial_capital=1000, mode=mode)
        bt.leverage = lev
        bt.position_size = pos_size
        
        final_value = bt.simulate(price_data)
        stats = bt.get_stats(final_value)
        
        results.append({
            'mode': mode,
            'leverage': lev,
            'position_size': pos_size,
            **stats
        })
        
        print(f"  {mode:8} 杠杆:{lev:.0f}x 仓位:{pos_size*100:.0f}% → 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}%")
    
    # 结果矩阵
    print("\n" + "="*70)
    print("【3. 回测结果矩阵】")
    print("="*70)
    
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│                    普通模式 (Normal Mode)                           │")
    print("├──────────┬────────┬──────────┬──────────┬──────────┬────────┬────────┤")
    print("│   杠杆   │ 仓位   │   收益   │   胜率   │ 资金使用│ 交易数 │ 胜负  │")
    print("├──────────┼────────┼──────────┼──────────┼──────────┼────────┼────────┤")
    
    for r in results:
        if r['mode'] != 'normal': continue
        print(f"│   {r['leverage']:.0f}x     │ {r['position_size']*100:>5.0f}%  │ {r['return']:>+8.2f}% │ {r['win_rate']:>7.1f}% │ {r['capital_usage']:>8.1f}% │   {r['total_trades']:>3d}   │ {r['wins']:>2d}/{r['losses']:>2d} │")
    
    print("└──────────┴────────┴──────────┴──────────┴──────────┴────────┴────────┘")
    
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│                    专家模式 (Expert Mode)                            │")
    print("├──────────┬────────┬──────────┬──────────┬──────────┬────────┬────────┤")
    print("│   杠杆   │ 仓位   │   收益   │   胜率   │ 资金使用│ 交易数 │ 胜负  │")
    print("├──────────┼────────┼──────────┼──────────┼──────────┼────────┼────────┤")
    
    for r in results:
        if r['mode'] != 'expert': continue
        print(f"│   {r['leverage']:.0f}x     │ {r['position_size']*100:>5.0f}%  │ {r['return']:>+8.2f}% │ {r['win_rate']:>7.1f}% │ {r['capital_usage']:>8.1f}% │   {r['total_trades']:>3d}   │ {r['wins']:>2d}/{r['losses']:>2d} │")
    
    print("└──────────┴────────┴──────────┴──────────┴──────────┴────────┴────────┘")
    
    # 最优配置
    best_normal = max([r for r in results if r['mode'] == 'normal'], key=lambda x: x['return'])
    best_expert = max([r for r in results if r['mode'] == 'expert'], key=lambda x: x['return'])
    
    print("\n【4. 最优配置推荐】")
    print(f"  普通模式最优: 杠杆{best_normal['leverage']:.0f}x + 仓位{best_normal['position_size']*100:.0f}% → 收益{best_normal['return']:+.2f}%")
    print(f"  专家模式最优: 杠杆{best_expert['leverage']:.0f}x + 仓位{best_expert['position_size']*100:.0f}% → 收益{best_expert['return']:+.2f}%")
    
    # 保存结果
    with open('/tmp/backtest_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ 回测完成! 结果已保存到 /tmp/backtest_results.json")

if __name__ == '__main__':
    main()
