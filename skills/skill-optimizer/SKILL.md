# SkillOptimizer - 策略优化器

## 版本
**v1.0** - G40 核心策略优化器

## 功能

### 1. 多策略融合
整合 10+ 交易策略，统一信号生成和权重分配。

### 2. 市场状态检测
- trending (趋势市场)
- ranging (震荡市场)
- volatile (高波动市场)

### 3. 自适应权重
根据市场状态和历史表现动态调整策略权重。

### 4. 自我进化
记录每笔交易表现，自动淘汰低效策略。

## 策略列表

| 策略 | 功能 | 权重范围 |
|------|------|----------|
| go-core | 趋势跟踪核心 | 10-30% |
| go-pool | 资金流向撞球 | 10-25% |
| go-rotate | 板块轮动检测 | 10-25% |
| go-long-short | 多空信号 | 5-30% |
| go-detect | 异常波动检测 | 10-15% |
| go-etf | ETF流动性信号 | 5-10% |
| go-fit | 适配策略 | 5% |
| go-noise | 噪音交易 | 0-5% |
| go-thermo | 热力策略 | 0-5% |
| top10 | 顶级交易员信号 | 5-10% |

## 使用

```python
from strategy_optimizer import StrategyOptimizer

optimizer = StrategyOptimizer(g40_instance)
result = optimizer.calculate_signal('BTC')
print(f"信号: {result['signal']:.2f}, 信心: {result['confidence']:.2%}")
```

## GitHub
- Branch: g12branch
