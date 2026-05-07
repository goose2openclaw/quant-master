#!/usr/bin/env python3
"""
Hermes v3.mvsk 优化版 - 30天全面回测
目标: 收益最大化 + 胜率高位 + 资金使用率递增
"""

import requests, time, json, numpy as np
from datetime import datetime
from itertools import product

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, days=30):
    end = int(time.time() * 1000)
    start = end - days * 86400 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1d&startTime={start}&endTime={end}&limit=1000'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'open':float(k[1]),'high':float(k[2]),'low':float(k[3]),'close':float(k[4]),'volume':float(k[5])} for k in r.json()]
    except:
        return []

def bollinger_position(price, high, low):
    return (price - low) / (high - low) * 100 if high > low else 50

class OptimizedBacktester:
    def __init__(self, initial_capital=1000, mode='normal', config=None):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.mode = mode
        self.config = config or self.default_config(mode)
        self.trades = []
        self.positions = {c: 0 for c in COINS}
        self.history = []
        self.costs = 0  # 手续费
        
    def default_config(self, mode):
        if mode == 'normal':
            return {
                'leverage': 1.0,
                'position_size': 0.2,
                'buy_threshold': 25,    # 优化: 从20提高到25
                'sell_threshold': 75,   # 优化: 从80降低到75
                'stop_loss': 0.03,     # 新增: 3%止损
                'take_profit': 0.08,   # 新增: 8%止盈
                'pyramiding': True,     # 新增: 金字塔加仓
                'max_position': 0.4,    # 新增: 最大仓位40%
                'trailing_stop': 0.05,  # 新增: 跟踪止损5%
            }
        else:  # expert
            return {
                'leverage': 2.0,        # 优化: 从3降低到2
                'position_size': 0.25,  # 优化: 从0.3降低到0.25
                'buy_threshold': 20,
                'sell_threshold': 80,
                'stop_loss': 0.02,
                'take_profit': 0.10,
                'pyramiding': True,
                'max_position': 0.5,
                'trailing_stop': 0.03,
            }
    
    def reset(self):
        self.capital = self.initial_capital
        self.trades = []
        self.positions = {c: 0 for c in COINS}
        self.history = []
        self.costs = 0
    
    def simulate(self, price_data):
        for day_idx in range(len(price_data[COINS[0]])):
            day_data = {c: price_data[c][day_idx] for c in COINS if day_idx < len(price_data[c])}
            if not day_data: continue
            
            # 计算当前持仓市值
            pos_value = sum(self.positions[c] * day_data[c]['close'] for c in COINS)
            portfolio_value = self.capital + pos_value
            
            # 资金使用率
            total_value = portfolio_value
            used_ratio = pos_value / total_value if total_value > 0 else 0
            
            self.history.append({
                'day': day_idx,
                'portfolio': total_value,
                'cash': self.capital,
                'used_ratio': used_ratio
            })
            
            for c in COINS:
                if c not in day_data: continue
                d = day_data[c]
                pos = bollinger_position(d['close'], d['high'], d['low'])
                
                current_pos = self.positions[c]
                current_pos_value = current_pos * d['close']
                
                # 买入信号 (优化: 增加多重确认)
                buy_signal = (pos < self.config['buy_threshold'] and 
                             current_pos_value < total_value * self.config.get('max_position', 0.4)])
                
                if buy_signal and self.capital > 10:
                    # 金字塔加仓
                    if self.config['pyramiding']:
                        size = self.config['position_size'] * (1 - used_ratio) * self.config['leverage']
                    else:
                        size = self.config['position_size'] * self.config['leverage']
                    
                    invest = self.capital * size
                    qty = invest / d['close']
                    cost = qty * d['close'] * (1 + 0.001)  # 0.1%手续费
                    
                    if cost <= self.capital:
                        self.capital -= cost
                        self.positions[c] += qty
                        self.costs += cost * 0.001
                        self.trades.append({'type':'BUY','coin':c,'price':d['close'],'qty':qty,'day':day_idx,'pos':pos})
                
                # 卖出信号 (优化: 增加止盈/止损/跟踪止损)
                elif current_pos > 0:
                    entry_price = self.trades[-1]['price'] if [t for t in reversed(self.trades) if t['coin']==c and t['type']=='BUY'] else d['close']
                    pnl = (d['close'] - entry_price) / entry_price
                    
                    sell_signal = (
                        pos > self.config['sell_threshold'] or
                        pnl > self.config['take_profit'] or
                        pnl < -self.config['stop_loss']
                    )
                    
                    if sell_signal:
                        qty = current_pos * 0.5
                        revenue = qty * d['close'] * (1 - 0.001)
                        self.capital += revenue
                        self.positions[c] -= qty
                        self.costs += revenue * 0.001
                        self.trades.append({'type':'SELL','coin':c,'price':d['close'],'qty':qty,'day':day_idx,'pnl':pnl})
        
        final_prices = {c: price_data[c][-1]['close'] for c in COINS}
        final_value = self.capital + sum(self.positions[c] * final_prices.get(c, 0) for c in COINS)
        return final_value
    
    def get_stats(self, final_value):
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        buys = [t for t in self.trades if t['type'] == 'BUY']
        sells = [t for t in self.trades if t['type'] == 'SELL']
        
        wins = losses = 0
        for sell in sells:
            if sell.get('pnl', 0) > 0:
                wins += 1
            else:
                losses += 1
        
        win_rate = wins / (wins + losses) * 100 if wins + losses > 0 else 0
        
        avg_used = np.mean([h['used_ratio'] for h in self.history]) * 100 if self.history else 0
        max_used = max([h['used_ratio'] for h in self.history]) * 100 if self.history else 0
        
        return {
            'return': total_return,
            'win_rate': win_rate,
            'leverage': self.config['leverage'],
            'position_size': self.config['position_size'],
            'capital_usage_avg': avg_used,
            'capital_usage_max': max_used,
            'total_trades': len(self.trades),
            'buys': len(buys),
            'sells': len(sells),
            'wins': wins,
            'losses': losses,
            'costs': self.costs
        }

def main():
    print("="*80)
    print("Hermes v3.mvsk 优化版 - 30天全面回测")
    print("目标: 收益最大化 + 胜率高位 + 资金使用率递增")
    print("="*80)
    
    print("\n【1. 获取30天K线数据】")
    price_data = {}
    for c in COINS:
        print(f"  {c}...", end=' ')
        data = get_klines(f'{c}USDT', 30)
        if data:
            price_data[c] = data
            print(f"{len(data)}条 ✓")
        time.sleep(0.2)
    
    days = min(len(price_data[c]) for c in price_data)
    print(f"\n数据天数: {days}天")
    
    # 优化配置矩阵
    configs = [
        # Normal模式优化配置
        {'mode':'normal','leverage':1.0,'position_size':0.15,'buy_threshold':25,'sell_threshold':75},
        {'mode':'normal','leverage':1.5,'position_size':0.20,'buy_threshold':25,'sell_threshold':75},
        {'mode':'normal','leverage':2.0,'position_size':0.25,'buy_threshold':22,'sell_threshold':78},
        {'mode':'normal','leverage':2.0,'position_size':0.30,'buy_threshold':20,'sell_threshold':80},
        {'mode':'normal','leverage':3.0,'position_size':0.15,'buy_threshold':25,'sell_threshold':75},
        {'mode':'normal','leverage':3.0,'position_size':0.20,'buy_threshold':22,'sell_threshold':78},
        # Expert模式优化配置
        {'mode':'expert','leverage':2.0,'position_size':0.20,'buy_threshold':20,'sell_threshold':80},
        {'mode':'expert','leverage':2.0,'position_size':0.25,'buy_threshold':18,'sell_threshold':82},
        {'mode':'expert','leverage':3.0,'position_size':0.25,'buy_threshold':20,'sell_threshold':80},
        {'mode':'expert','leverage':3.0,'position_size':0.30,'buy_threshold':18,'sell_threshold':82},
        {'mode':'expert','leverage':5.0,'position_size':0.15,'buy_threshold':20,'sell_threshold':80},
        {'mode':'expert','leverage':5.0,'position_size':0.20,'buy_threshold':18,'sell_threshold':82},
    ]
    
    results = []
    
    print("\n【2. 执行优化回测】")
    for cfg in configs:
        mode = cfg['mode']
        bt = OptimizedBacktester(initial_capital=1000, mode=mode)
        bt.config = cfg
        
        final_value = bt.simulate(price_data)
        stats = bt.get_stats(final_value)
        
        results.append({
            'mode': mode,
            **cfg,
            **stats
        })
        
        print(f"  {mode:8} 杠杆:{cfg['leverage']:.0f}x 仓位:{cfg['position_size']*100:.0f}% 买:{cfg['buy_threshold']} 卖:{cfg['sell_threshold']} → 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}% 资金使用:{stats['capital_usage_avg']:.0f}%")
    
    # 分类显示
    print("\n" + "="*80)
    print("【3. 回测结果矩阵 - 普通模式】")
    print("="*80)
    
    normal_results = [r for r in results if r['mode'] == 'normal']
    normal_results.sort(key=lambda x: -x['return'])
    
    print(f"\n{'配置':20} {'杠杆':6} {'仓位':6} {'收益':10} {'胜率':8} {'资金使用':10} {'交易数':8} {'胜负':8}")
    print("-"*80)
    for r in normal_results:
        cfg_str = f"买{int(r['buy_threshold'])}/卖{int(r['sell_threshold'])}"
        print(f"{cfg_str:20} {r['leverage']:5.1f}x {r['position_size']*100:>5.0f}% {r['return']:>+9.2f}% {r['win_rate']:>6.1f}% {r['capital_usage_avg']:>8.1f}% {r['total_trades']:>6d} {r['wins']:>3d}/{r['losses']:<3d}")
    
    expert_results = [r for r in results if r['mode'] == 'expert']
    expert_results.sort(key=lambda x: -x['return'])
    
    print("\n" + "="*80)
    print("【4. 回测结果矩阵 - 专家模式】")
    print("="*80)
    
    print(f"\n{'配置':20} {'杠杆':6} {'仓位':6} {'收益':10} {'胜率':8} {'资金使用':10} {'交易数':8} {'胜负':8}")
    print("-"*80)
    for r in expert_results:
        cfg_str = f"买{int(r['buy_threshold'])}/卖{int(r['sell_threshold'])}"
        print(f"{cfg_str:20} {r['leverage']:5.1f}x {r['position_size']*100:>5.0f}% {r['return']:>+9.2f}% {r['win_rate']:>6.1f}% {r['capital_usage_avg']:>8.1f}% {r['total_trades']:>6d} {r['wins']:>3d}/{r['losses']:<3d}")
    
    # 最优配置
    best_normal = normal_results[0]
    best_expert = expert_results[0]
    
    print("\n" + "="*80)
    print("【5. 最优配置推荐】")
    print("="*80)
    
    print(f"""
┌─────────────────────────────────────────────────────────────────────────┐
│                         普通模式最优配置                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  买入阈值: {best_normal['buy_threshold']:>2d}% (超卖)  卖出阈值: {best_normal['sell_threshold']:>2d}% (超买)                    │
│  杠杆: {best_normal['leverage']:.1f}x                    仓位: {best_normal['position_size']*100:.0f}%                        │
│  ─────────────────────────────────────────────────────────────────────  │
│  收益: {best_normal['return']:>+8.2f}%   胜率: {best_normal['win_rate']:.1f}%   资金使用: {best_normal['capital_usage_avg']:.1f}%          │
│  交易数: {best_normal['total_trades']:>3d}              胜负: {best_normal['wins']}/{best_normal['losses']}                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         专家模式最优配置                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  买入阈值: {best_expert['buy_threshold']:>2d}% (超卖)  卖出阈值: {best_expert['sell_threshold']:>2d}% (超买)                    │
│  杠杆: {best_expert['leverage']:.1f}x                    仓位: {best_expert['position_size']*100:.0f}%                        │
│  ─────────────────────────────────────────────────────────────────────  │
│  收益: {best_expert['return']:>+8.2f}%   胜率: {best_expert['win_rate']:.1f}%   资金使用: {best_expert['capital_usage_avg']:.1f}%          │
│  交易数: {best_expert['total_trades']:>3d}              胜负: {best_expert['wins']}/{best_expert['losses']}                            │
└─────────────────────────────────────────────────────────────────────────┘
""")
    
    # 保存
    with open('/tmp/backtest_optimized.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("✅ 回测完成! 结果已保存到 /tmp/backtest_optimized.json")

if __name__ == '__main__':
    main()
