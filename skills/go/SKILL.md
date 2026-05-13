# go - 加密量化交易系列技能包

## 概述
go系列是完整的加密货币量化交易技能生态系统，包含13+专业技能模块。

## 核心技能

### go-core (核心引擎)
**路径**: `../go-core/`
**功能**: Mirofish 300智能体共识预测，自适应权重，多周期共振
**版本**: v2.0

### go-quantum (量子分析)
**路径**: `../go-quantum/`  
**功能**: 量子态分析，隧穿效应，能量计算

### go-thermo (热力学)
**路径**: `../go-thermo/`
**功能**: 市场温度，相变分析，熵计算

### go-contrarian (反人性)
**路径**: `../go-contrarian/`
**功能**: FOMO/FEAR检测，人性因子，逆向交易

### go-detect (机构侦测)
**路径**: `../go-detect/`
**功能**: 机构订单捕捉，趋势跟随，mean reversion

### go-ensemble (集成)
**路径**: `../go-ensemble/`
**功能**: 多策略加权组合，策略融合

### go-meta (自迭代)
**路径**: `../go-meta/`
**功能**: 自我迭代优化，学习反馈

### go-reverse (反向)
**路径**: `../go-reverse/`
**功能**: 反向模拟预测

### go-fit (趋势拟合)
**路径**: `../go-fit/`
**功能**: 趋势线拟合，入场点识别

### go-noise (噪音分析)
**路径**: `../go-noise/`
**功能**: 市场噪音过滤，信号增强

### go-hotspot (热点)
**路径**: `../go-hotspot/`
**功能**: 热点追踪，板块轮动

### go-fastlane (快车道)
**路径**: `../go-fastlane/`
**功能**: 快速反应执行

## Phase 3 扩展技能

### go-orderbook (订单簿)
**路径**: `../go-orderbook/`
**功能**: 实时订单簿分析，机构订单捕捉

### go-liquidation (清算)
**路径**: `../go-liquidation/`
**功能**: 清算价格预测，爆仓预警

### go-cross-exchange (跨交易所)
**路径**: `../go-cross-exchange/`
**功能**: 多交易所价格对比，套利机会

## 使用方法

```python
from skills.go_core import GoCore

# 初始化
go = GoCore(num_agents=300)

# 预测
result = go.predict('BTC')
print(f"信号: {result['signal']}")
print(f"置信度: {result['confidence']:.0%}")

# 扫描
signals = go.scan(tier='meme', min_score=35)
```

## 版本历史

- v2.0 (2026-05-13): 三阶段优化完成
  - Phase 1: 并行计算, 缓存系统
  - Phase 2: 自适应权重, 多周期共振
  - Phase 3: 订单簿, 清算, 跨交易所

## 交易参数

| 参数 | 值 | 描述 |
|------|-----|------|
| MIN_TRADE_USDT | 1 | 最低交易金额 |
| MAX_POSITION_PCT | 15% | 最大仓位 |
| STOP_LOSS | 5% | 止损 |
| TAKE_PROFIT | 25% | 止盈 |
| SCAN_INTERVAL | 20s | 扫描间隔 |
| MIN_CONFIDENCE | 35% | 最低置信度 |
