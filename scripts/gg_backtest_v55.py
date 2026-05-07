#!/usr/bin/env python3
"""
Hermes v5.5 (蒸馏前版本) - 30天回测
普通模式 vs 专家模式
"""

import requests, time, json, numpy as np

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, days=30):
    end = int(time.time() * 1000)
    start = end - days * 86400 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1d&startTime={start}&endTime={end}&limit=1000'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'open':float(k[1]),'high':float(k[2]),'low':float(k[3]),'close':float(k[4])} for k in r.json()]
    except:
        return []

def bollinger_position(price, high, low):
    return (price - low) / (high - low) * 100 if high > low else 50

class Backtester:
    def __init__(self, initial_capital=1000, mode='normal', cfg=None):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.mode = mode
        self.cfg = cfg or self.default_cfg(mode)
        self.trades = []
        self.positions = {c: 0 for c in COINS}
        self.history = []
        
    def default_cfg(self, mode):
        # 普通模式
        if mode == 'normal':
            return {
                'leverage': 1.0,
                'position_size': 0.1,
                'buy_th': 20,
                'sell_th': 80,
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'position_ratio': 0.3  # 每次交易仓位比例
            }
        # 专家模式
        return {
            'leverage': 2.0,
            'position_size': 0.2,
            'buy_th': 15,
            'sell_th': 85,
            'stop_loss': 0.03,
            'take_profit': 0.15,
            'position_ratio': 0.5
        }
    
    def reset(self):
        self.capital = self.initial_capital
        self.trades = []
        self.positions = {c: 0 for c in COINS}
        self.history = []
    
    def simulate(self, price_data):
        for day_idx in range(len(price_data[COINS[0]])):
            day_data = {c: price_data[c][day_idx] for c in COINS if day_idx < len(price_data[c])}
            if not day_data: continue
            
            pos_value = sum(self.positions[c] * day_data[c]['close'] for c in COINS)
            total_value = self.capital + pos_value
            used_ratio = pos_value / total_value if total_value > 0 else 0
            
            self.history.append({'day':day_idx,'portfolio':total_value,'used_ratio':used_ratio})
            
            for c in COINS:
                if c not in day_data: continue
                d = day_data[c]
                pos = bollinger_position(d['close'], d['high'], d['low'])
                current_pos = self.positions[c]
                current_pos_value = current_pos * d['close']
                
                # 买入 - 低吸
                if pos < self.cfg['buy_th'] and current_pos_value < total_value * self.cfg['position_size'] and self.capital > 10:
                    invest = self.capital * self.cfg['position_ratio']
                    qty = invest / d['close']
                    cost = qty * d['close'] * 1.001
                    if cost <= self.capital:
                        self.capital -= cost
                        self.positions[c] += qty
                        self.trades.append({'type':'BUY','coin':c,'price':d['close'],'day':day_idx})
                
                # 卖出 - 高抛
                elif current_pos > 0 and pos > self.cfg['sell_th']:
                    qty = current_pos * 0.5
                    revenue = qty * d['close'] * 0.999
                    self.capital += revenue
                    self.positions[c] -= qty
                    self.trades.append({'type':'SELL','coin':c,'price':d['close'],'day':day_idx})
        
        final_prices = {c: price_data[c][-1]['close'] for c in COINS}
        return self.capital + sum(self.positions[c] * final_prices.get(c, 0) for c in COINS)
    
    def get_stats(self, final_value):
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        sells = [t for t in self.trades if t['type'] == 'SELL']
        buys = [t for t in self.trades if t['type'] == 'BUY']
        
        # 计算胜负
        wins = losses = 0
        for i, sell in enumerate(sells):
            prev_buys = [b for b in reversed(buys) if b['coin'] == sell['coin'] and b['day'] < sell['day']]
            if prev_buys and sell['price'] > prev_buys[0]['price']:
                wins += 1
            else:
                losses += 1
        
        win_rate = wins / len(sells) * 100 if sells else 0
        avg_used = np.mean([h['used_ratio'] for h in self.history]) * 100 if self.history else 0
        max_used = max([h['used_ratio'] for h in self.history]) * 100 if self.history else 0
        
        return {
            'return': total_return,
            'win_rate': win_rate,
            'leverage': self.cfg['leverage'],
            'position_size': self.cfg['position_size'],
            'capital_usage_avg': avg_used,
            'capital_usage_max': max_used,
            'total_trades': len(self.trades),
            'buys': len(buys),
            'sells': len(sells),
            'wins': wins,
            'losses': losses
        }

def main():
    print("="*80)
    print("Hermes v5.5 (蒸馏前版本) - 30天回测")
    print("普通模式 vs 专家模式")
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
    
    # 配置矩阵
    configs = [
        # 普通模式
        {'mode':'normal','leverage':1.0,'position_size':0.1,'buy_th':20,'sell_th':80,'position_ratio':0.3},
        {'mode':'normal','leverage':1.0,'position_size':0.15,'buy_th':20,'sell_th':80,'position_ratio':0.4},
        {'mode':'normal','leverage':1.5,'position_size':0.1,'buy_th':20,'sell_th':80,'position_ratio':0.3},
        {'mode':'normal','leverage':2.0,'position_size':0.1,'buy_th':15,'sell_th':85,'position_ratio':0.3},
        {'mode':'normal','leverage':2.0,'position_size':0.15,'buy_th':18,'sell_th':82,'position_ratio':0.4},
        {'mode':'normal','leverage':3.0,'position_size':0.1,'buy_th':20,'sell_th':80,'position_ratio':0.2},
        # 专家模式
        {'mode':'expert','leverage':2.0,'position_size':0.2,'buy_th':15,'sell_th':85,'position_ratio':0.5},
        {'mode':'expert','leverage':2.0,'position_size':0.25,'buy_th':15,'sell_th':85,'position_ratio':0.5},
        {'mode':'expert','leverage':3.0,'position_size':0.2,'buy_th':15,'sell_th':85,'position_ratio':0.4},
        {'mode':'expert','leverage':3.0,'position_size':0.25,'buy_th':12,'sell_th':88,'position_ratio':0.5},
        {'mode':'expert','leverage':5.0,'position_size':0.15,'buy_th':15,'sell_th':85,'position_ratio':0.3},
        {'mode':'expert','leverage':5.0,'position_size':0.2,'buy_th':12,'sell_th':88,'position_ratio':0.4},
    ]
    
    results = []
    
    print("\n【2. 执行回测】")
    for cfg in configs:
        bt = Backtester(initial_capital=1000, mode=cfg['mode'])
        bt.cfg = cfg
        final_value = bt.simulate(price_data)
        stats = bt.get_stats(final_value)
        results.append({**cfg, **stats})
        print(f"  {cfg['mode']:8} 杠杆:{cfg['leverage']:.0f}x 仓位:{cfg['position_ratio']*100:.0f}% 买:{cfg['buy_th']} 卖:{cfg['sell_th']} → 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}% 资金:{stats['capital_usage_avg']:.0f}%")
    
    # 结果矩阵
    normal = sorted([r for r in results if r['mode']=='normal'], key=lambda x: -x['return'])
    expert = sorted([r for r in results if r['mode']=='expert'], key=lambda x: -x['return'])
    
    print("\n" + "="*80)
    print("【3. 回测结果矩阵 - 普通模式】")
    print("="*80)
    
    print(f"\n{'配置':16} {'杠杆':5} {'仓位':5} {'收益':9} {'胜率':7} {'资金(均/最大)':16} {'交易':6} {'胜负':8}")
    print("-"*80)
    for r in normal:
        cfg_str = f"买{r['buy_th']}/卖{r['sell_th']}"
        print(f"{cfg_str:16} {r['leverage']:>4.1f}x {r['position_ratio']*100:>4.0f}% {r['return']:>+8.2f}% {r['win_rate']:>5.1f}% {r['capital_usage_avg']:>5.1f}%/{r['capital_usage_max']:>5.1f}% {r['total_trades']:>5d} {r['wins']:>3d}/{r['losses']:<3d}")
    
    print("\n" + "="*80)
    print("【4. 回测结果矩阵 - 专家模式】")
    print("="*80)
    
    print(f"\n{'配置':16} {'杠杆':5} {'仓位':5} {'收益':9} {'胜率':7} {'资金(均/最大)':16} {'交易':6} {'胜负':8}")
    print("-"*80)
    for r in expert:
        cfg_str = f"买{r['buy_th']}/卖{r['sell_th']}"
        print(f"{cfg_str:16} {r['leverage']:>4.1f}x {r['position_ratio']*100:>4.0f}% {r['return']:>+8.2f}% {r['win_rate']:>5.1f}% {r['capital_usage_avg']:>5.1f}%/{r['capital_usage_max']:>5.1f}% {r['total_trades']:>5d} {r['wins']:>3d}/{r['losses']:<3d}")
    
    # 最优
    bn, be = normal[0], expert[0]
    
    print("\n" + "="*80)
    print("【5. 最优配置推荐 - v5.5 蒸馏前版本】")
    print("="*80)
    
    print(f"""
┌─────────────────────────────────────────────────────────────────────────┐
│                     普通模式最优                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  买入:{bn['buy_th']}% 卖出:{bn['sell_th']}%  杠杆:{bn['leverage']:.1f}x  仓位:{bn['position_ratio']*100:.0f}%                        │
│  收益:{bn['return']:>+8.2f}%  胜率:{bn['win_rate']:.1f}%  资金使用:{bn['capital_usage_avg']:.1f}/{bn['capital_usage_max']:.1f}%  交易:{bn['total_trades']}次          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     专家模式最优                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  买入:{be['buy_th']}% 卖出:{be['sell_th']}%  杠杆:{be['leverage']:.1f}x  仓位:{be['position_ratio']*100:.0f}%                        │
│  收益:{be['return']:>+8.2f}%  胜率:{be['win_rate']:.1f}%  资金使用:{be['capital_usage_avg']:.1f}/{be['capital_usage_max']:.1f}%  交易:{be['total_trades']}次          │
└─────────────────────────────────────────────────────────────────────────┘
""")
    
    with open('/tmp/backtest_v55.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("✅ 回测完成!")

if __name__ == '__main__':
    main()
