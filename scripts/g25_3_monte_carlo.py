#!/usr/bin/env python3
"""
G25.3 蒙特卡洛仿真 - 1000个智能体模拟7天收益
"""
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

# 基于回测数据的参数
MAJOR_PARAMS = {
    'win_rate': 0.512,
    'avg_win': 0.162 / 0.512,  # 做多收益/胜率
    'avg_loss': -0.13 / 0.488,  # 亏损/失败率
    'leverage': 5,
    'position_size': 0.10,
    'trades_per_day': 0.5,  # 每天平均0.5笔交易
}

MEME_PARAMS = {
    'win_rate': 0.524,
    'avg_win': 0.291 / 0.524,  # 做多收益/胜率
    'avg_loss': -0.22 / 0.476,
    'leverage': 10,
    'position_size': 0.05,
    'trades_per_day': 1.0,  # Meme币交易更频繁
}

def simulate_agent(params, days=7, initial_capital=1000):
    """模拟单个智能体7天收益"""
    capital = initial_capital
    daily_returns = []
    
    for day in range(days):
        # 每天交易次数
        num_trades = np.random.poisson(params['trades_per_day'])
        
        daily_pnl = 0
        for _ in range(num_trades):
            # 判断是否盈利
            if random.random() < params['win_rate']:
                # 盈利交易
                pnl_pct = random.uniform(0.02, params['avg_win']) * params['leverage']
                position = capital * params['position_size']
                daily_pnl += position * pnl_pct
            else:
                # 亏损交易
                pnl_pct = random.uniform(params['avg_loss'], -0.02) * params['leverage']
                position = capital * params['position_size']
                daily_pnl += position * pnl_pct
        
        capital += daily_pnl
        daily_returns.append((capital / initial_capital - 1) * 100)
    
    final_return = (capital / initial_capital - 1) * 100
    return {
        'final_return': final_return,
        'final_capital': capital,
        'daily_returns': daily_returns,
        'max_drawdown': min(daily_returns) if daily_returns else 0
    }

def run_simulation():
    print("=" * 80)
    print("G25.3 蒙特卡洛仿真 - 1000个智能体 x 7天")
    print("=" * 80)
    
    num_agents = 1000
    days = 7
    initial_capital = 1000
    
    print(f"\n仿真参数:")
    print(f"  智能体数量: {num_agents}")
    print(f"  仿真天数: {days}")
    print(f"  初始资金: ${initial_capital}")
    print(f"  主流币胜率: {MAJOR_PARAMS['win_rate']*100:.1f}%")
    print(f"  Meme币胜率: {MEME_PARAMS['win_rate']*100:.1f}%")
    
    # 主流币仿真
    print(f"\n{'='*80}")
    print("【主流币组合仿真】")
    print("-" * 80)
    
    major_results = []
    for i in range(num_agents):
        result = simulate_agent(MAJOR_PARAMS, days, initial_capital)
        major_results.append(result)
    
    major_returns = [r['final_return'] for r in major_results]
    major_returns.sort(reverse=True)
    
    # 统计
    avg_return = np.mean(major_returns)
    median_return = np.median(major_returns)
    std_return = np.std(major_returns)
    max_return = max(major_returns)
    min_return = min(major_returns)
    percentile_95 = np.percentile(major_returns, 95)
    percentile_5 = np.percentile(major_returns, 5)
    profitable_count = sum(1 for r in major_returns if r > 0)
    win_rate_sim = profitable_count / num_agents * 100
    
    print(f"\n📊 主流币仿真结果 (n={num_agents}):")
    print(f"  平均收益: {avg_return:+.2f}%")
    print(f"  中位数收益: {median_return:+.2f}%")
    print(f"  标准差: {std_return:.2f}%")
    print(f"  最大收益: {max_return:+.2f}%")
    print(f"  最大亏损: {min_return:+.2f}%")
    print(f"  95%分位: {percentile_95:+.2f}%")
    print(f"  5%分位: {percentile_5:+.2f}%")
    print(f"  盈利概率: {win_rate_sim:.1f}%")
    
    # Meme币仿真
    print(f"\n{'='*80}")
    print("【Meme币组合仿真】")
    print("-" * 80)
    
    meme_results = []
    for i in range(num_agents):
        result = simulate_agent(MEME_PARAMS, days, initial_capital)
        meme_results.append(result)
    
    meme_returns = [r['final_return'] for r in meme_results]
    meme_returns.sort(reverse=True)
    
    avg_return_m = np.mean(meme_returns)
    median_return_m = np.median(meme_returns)
    std_return_m = np.std(meme_returns)
    max_return_m = max(meme_returns)
    min_return_m = min(meme_returns)
    percentile_95_m = np.percentile(meme_returns, 95)
    percentile_5_m = np.percentile(meme_returns, 5)
    profitable_m = sum(1 for r in meme_returns if r > 0)
    win_rate_m = profitable_m / num_agents * 100
    
    print(f"\n📊 Meme币仿真结果 (n={num_agents}):")
    print(f"  平均收益: {avg_return_m:+.2f}%")
    print(f"  中位数收益: {median_return_m:+.2f}%")
    print(f"  标准差: {std_return_m:.2f}%")
    print(f"  最大收益: {max_return_m:+.2f}%")
    print(f"  最大亏损: {min_return_m:+.2f}%")
    print(f"  95%分位: {percentile_95_m:+.2f}%")
    print(f"  5%分位: {percentile_5_m:+.2f}%")
    print(f"  盈利概率: {win_rate_m:.1f}%")
    
    # 综合仿真 (50%主流 + 50% Meme)
    print(f"\n{'='*80}")
    print("【综合组合仿真 (50%主流 + 50%Meme)】")
    print("-" * 80)
    
    combined_returns = []
    for i in range(num_agents):
        major_r = major_results[i]['final_return']
        meme_r = meme_results[i]['final_return']
        combined_r = (major_r + meme_r) / 2
        combined_returns.append(combined_r)
    
    combined_returns.sort(reverse=True)
    
    avg_combined = np.mean(combined_returns)
    median_combined = np.median(combined_returns)
    std_combined = np.std(combined_returns)
    max_combined = max(combined_returns)
    min_combined = min(combined_returns)
    percentile_95_c = np.percentile(combined_returns, 95)
    percentile_5_c = np.percentile(combined_returns, 5)
    profitable_c = sum(1 for r in combined_returns if r > 0)
    win_rate_c = profitable_c / num_agents * 100
    
    print(f"\n📊 综合仿真结果 (n={num_agents}):")
    print(f"  平均收益: {avg_combined:+.2f}%")
    print(f"  中位数收益: {median_combined:+.2f}%")
    print(f"  标准差: {std_combined:.2f}%")
    print(f"  最大收益: {max_combined:+.2f}%")
    print(f"  最大亏损: {min_combined:+.2f}%")
    print(f"  95%分位 (乐观): {percentile_95_c:+.2f}%")
    print(f"  5%分位 (悲观): {percentile_5_c:+.2f}%")
    print(f"  盈利概率: {win_rate_c:.1f}%")
    
    # 按资金规模放大
    print(f"\n{'='*80}")
    print("【收益预测 (按实际资金规模)】")
    print("-" * 80)
    
    capital_major = 748.78  # 现货账户
    capital_meme = 748.78
    
    print(f"\n基于${capital_major:.2f}主流币账户:")
    print(f"  预期7天收益: ${capital_major * avg_return / 100:+.2f}")
    print(f"  乐观情况(95%): ${capital_major * percentile_95_c / 100:+.2f}")
    print(f"  悲观情况(5%): ${capital_major * percentile_5_c / 100:+.2f}")
    
    # 收益分布
    print(f"\n{'='*80}")
    print("【收益分布】")
    print("-" * 80)
    
    buckets = [
        ("<-20%", sum(1 for r in combined_returns if r < -20)),
        ("-20%~-10%", sum(1 for r in combined_returns if -20 <= r < -10)),
        ("-10%~0%", sum(1 for r in combined_returns if -10 <= r < 0)),
        ("0%~10%", sum(1 for r in combined_returns if 0 <= r < 10)),
        ("10%~20%", sum(1 for r in combined_returns if 10 <= r < 20)),
        ("20%~30%", sum(1 for r in combined_returns if 20 <= r < 30)),
        ("30%~50%", sum(1 for r in combined_returns if 30 <= r < 50)),
        (">50%", sum(1 for r in combined_returns if r >= 50)),
    ]
    
    print(f"\n{'区间':<12} {'数量':>8} {'占比':>10}")
    for label, count in buckets:
        pct = count / num_agents * 100
        bar = "█" * int(pct / 2)
        print(f"{label:<12} {count:>8} {pct:>6.1f}% {bar}")
    
    print(f"\n{'='*80}")
    
    return {
        'major': {'avg': avg_return, 'median': median_return, 'win_rate': win_rate_sim},
        'meme': {'avg': avg_return_m, 'median': median_return_m, 'win_rate': win_rate_m},
        'combined': {'avg': avg_combined, 'median': median_combined, 'win_rate': win_rate_c}
    }

if __name__ == '__main__':
    results = run_simulation()
