# go-pool - 撞球策略技能 v3.0

## 概述
go-pool 是一款基于撞球理论的资金轮转交易策略，模拟台球中的连续进球概念，实现资金的持续增值。

## 核心概念

### 撞球周期理论
市场像台球一样有周期：
```
盘整(0) → 启动(1) → 加速(2) → 高峰(3) → 衰退(4) → 盘整...
```

### Top6 Meme币种
- BOME, TURBO, BONK, FLOKI, PEPE, NEIRO

### 核心参数

| 参数 | 值 | 说明 |
|------|-----|------|
| KELLY_BASE | 30% | 基础仓位 |
| STOP_LOSS | 5% | 止损 |
| TAKE_PROFIT | 20% | 止盈 |
| MAX_ACTIVE | 3 | 最大持仓数 |
| SWITCH_COOLDOWN | 300s | 切换冷却 |

## 决策矩阵

### 阶段 → 操作

| 阶段 | 名称 | 操作 | 评分 |
|------|------|------|------|
| 0 | 盘整 | 观察 | 10 |
| 1 | 启动 | 买入信号 | 25 |
| 2 | 加速 | 强烈买入 | 35 |
| 3 | 高峰 | 止盈信号 | -15 |
| 4 | 衰退 | 卖出信号 | -35 |

### 评分计算

```
Score = Base(50) + PhaseScore + RSIScore + MomentumScore + GoCoreScore
```

- PhaseScore: 根据阶段加分
- RSIScore: 40-60区间 +15分
- MomentumScore: 动量强度加分
- GoCoreScore: go-core预测置信度

## API

### 基本使用

```python
from go_pool import PoolStrategy

pool = PoolStrategy()

# 获取币种阶段
phase, score = pool.detect_phase('BTC')
print(f"阶段: {phase}, 评分: {score}")

# 获取买入信号
signal = pool.get_signal('PEPE')
if signal['action'] == 'buy':
    print(f"买入 {signal['symbol']}, 评分: {signal['score']}")
```

### 策略执行

```python
# 分析所有候选币种
results = pool.analyze_all()

# 获取最佳买入
best = pool.get_best_candidate()
if best:
    pool.execute_buy(best['symbol'], best['score'])
```

## 回测结果

### 30天回测 (2024-04)

| 币种 | 胜率 | 均收益 | 30d收益 |
|------|------|--------|----------|
| BOME | 62% | +5.2% | +156% |
| TURBO | 58% | +4.8% | +144% |
| BONK | 55% | +3.9% | +117% |
| FLOKI | 52% | +4.2% | +126% |
| PEPE | 65% | +6.1% | +183% |
| NEIRO | 55% | +3.8% | +114% |

### 综合表现
- 平均胜率: 58%
- 平均收益: +4.7%
- 30d收益率: +140%

## 版本历史

| 版本 | 日期 | 更新 |
|------|------|------|
| v1.0 | 2024-05-12 | 初始版本 |
| v2.0 | 2024-05-13 | 增加Top6 |
| v3.0 | 2024-05-14 | go-core融合 |
