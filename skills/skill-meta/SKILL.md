# SkillMeta - 技能调度元系统

## 概述
SkillMeta 是 G40 的技能调度核心，负责智能组合和调度各个交易策略技能。

## 核心功能

### 1. 技能状态管理
- 每个技能的: 状态(活跃/休眠/冷却)
- 性能评分 (0-100)
- 使用频率统计
- 最后使用时间

### 2. 技能组合策略
- 市场适配组合
- 风险对冲组合
- 趋势跟随组合
- 震荡交易组合

### 3. 智能调度
- 基于市场状态的技能选择
- 基于账户状况的技能组合
- 基于信号强度的技能排序

## 技能分类

### 趋势类 (Trend)
- go-core: 趋势跟踪核心
- go-pool: 资金流向
- top10: 顶级交易员

### 震荡类 (Range)
- go-rotate: 板块轮动
- go-long-short: 多空信号
- go-noise: 噪音交易

### 风险类 (Risk)
- go-detect: 异常检测
- go-etf: ETF流动性
- go-thermo: 热力监控

## 组合模板

### 趋势市场组合
```
go-core (30%) + go-pool (25%) + go-detect (15%) + top10 (10%)
```

### 震荡市场组合
```
go-rotate (25%) + go-long-short (25%) + go-noise (15%) + go-etf (10%)
```

### 高波动市场组合
```
go-long-short (30%) + go-detect (20%) + go-thermo (15%) + go-fit (10%)
```

## 使用方法

```python
from skill_meta import SkillMeta, get_optimal_combination

meta = SkillMeta(g40_instance)
combination = get_optimal_combination('trending', confidence=0.7)
meta.execute_combination(combination)
```

---

*版本: 1.0*
*日期: 2026-05-17*
