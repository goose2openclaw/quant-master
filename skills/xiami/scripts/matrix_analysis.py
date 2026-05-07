#!/usr/bin/env python3
"""XIAMI 矩阵分析系统"""

import json

def load_data():
    with open('skills/xiami/data/matrix_analysis.json', 'r') as f:
        return json.load(f)

def main():
    data = load_data()
    
    print("="*80)
    print("🦐 XIAMI 2025年BTC市场分析矩阵")
    print("="*80)
    
    for strat in ['extreme', 'conservative', 'balanced']:
        s = data['trading_strategies'][strat]
        m = data['matrix'][strat]
        markets = data['market_states_2025']
        
        print(f"\n{'='*80}")
        print(f"📊 {s['name']} | 仓位:{s['position']*100:.0f}% 杠杆:{s['leverage']}x 止损:{s['stop_loss']*100:.0f}%")
        print("="*80)
        print(f"{'市场':<12} {'收益':<10} {'回撤':<10} {'胜率':<8} {'PF':<6} {'夏普':<6} {'建议':<12}")
        print("-"*80)
        
        for state in markets:
            r = m[state]
            print(f"{markets[state]['name']:<12} {r['return']:>+8.1f}% {r['drawdown']:>9.0f}% {r['win_rate']:>7.0%} {r['pf']:>5.1f} {r['sharpe']:>5.1f} {r['rec']:<12}")
    
    # 汇总
    print("\n" + "="*80)
    print("📈 策略对比汇总")
    print("="*80)
    
    for strat in ['extreme', 'conservative', 'balanced']:
        m = data['matrix'][strat]
        avg_r = sum(r['return'] for r in m.values()) / 4
        avg_d = sum(r['drawdown'] for r in m.values()) / 4
        avg_w = sum(r['win_rate'] for r in m.values()) / 4
        avg_s = sum(r['sharpe'] for r in m.values()) / 4
        name = data['trading_strategies'][strat]['name']
        print(f"{name:<12} 平均收益:{avg_r:>+7.1f}% 平均回撤:{avg_d:>6.0f}% 胜率:{avg_w:>6.0%} 夏普:{avg_s:>5.1f}")

if __name__ == "__main__":
    main()
