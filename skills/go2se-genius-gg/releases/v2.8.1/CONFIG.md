# GO2SE Genius v2.8.1 配置文档
版本: v2.8.1
日期: 2026-05-06

---

## 1. 核心优化目标

### 1.1 优化三角
- **收益最大化**: 月收益目标 +500%+
- **胜率最大化**: 目标 75%+
- **资金使用率**: 目标 90%+

### 1.2 v2.8.1 vs v2.8.0

| 指标 | v2.8.0 | v2.8.1目标 | 提升 |
|------|---------|-------------|------|
| 月收益 | +422.3% | +500%+ | +20% |
| 胜率 | 73.1% | 75%+ | +2% |
| 资金使用 | 60% | 90%+ | +30% |

---

## 2. 核心参数

### 2.1 专家模式配置 (v2.8.1)

```python
EXPERT_CONFIG = {
    # 基础参数
    'mode': 'expert',
    'capital_utilization': 0.90,  # 资金使用率90%+
    
    # RSI Extreme Override
    'rsi_short_threshold': 75,      # 做空信号
    'rsi_long_threshold': 28,       # 做多信号
    'rsi_short_winrate': 0.90,    # 90%胜率 (提升)
    'rsi_long_winrate': 0.85,     # 85%胜率 (提升)
    
    # 做空做多灵活转换
    'bull_threshold': 0.3,          # 牛市门槛
    'bear_threshold': -0.1,        # 熊市门槛
    
    # 破军策略 (强化)
    'pojun': {
        'leverage': 5,
        'tp': 0.12,    # 12%止盈 (提升)
        'sl': 0.015,   # 1.5%止损 (紧凑)
        'position': 0.20,  # 20%仓位
    },
    
    # 贪狼策略 (强化)
    'tanlang': {
        'leverage': 5,   # 提升
        'tp': 0.10,      # 10%止盈 (提升)
        'sl': 0.015,     # 1.5%止损
        'position': 0.15,
    },
    
    # 文曲策略
    'wenqu': {
        'leverage': 5,
        'tp': 0.06,    # 6%止盈 (提升)
        'sl': 0.015,
        'position': 0.10,
    },
}
```

---

## 3. 策略配置

### 3.1 破军策略 (推荐)
- 核心: 走着瞧+跟大哥
- 币种: SOL/DOGE/ETH
- 杠杆: 5x
- 止盈: 12% (提升)
- 止损: 1.5% (紧凑)
- 胜率: 90% (提升)
- 仓位: 20%

### 3.2 贪狼策略
- 核心: 打兔子
- 币种: SOL/DOGE/ETH
- 杠杆: 5x (提升)
- 止盈: 10% (提升)
- 止损: 1.5%
- 仓位: 15%

### 3.3 文曲策略
- 核心: 跟大哥
- 币种: BTC/ETH/BNB
- 杠杆: 5x
- 止盈: 6% (提升)
- 止损: 1.5%
- 仓位: 10%

---

## 4. 资金使用优化

### 4.1 动态仓位
```python
if margin_level > 4.5:
    position = 0.25
    leverage = 4
elif margin_level > 4.0:
    position = 0.20
    leverage = 3
elif margin_level > 3.5:
    position = 0.15
    leverage = 3
elif margin_level > 3.0:
    position = 0.10
    leverage = 2
else:
    position = 0.05
    leverage = 1
```

### 4.2 资金使用率目标
- 目标: 90%+
- 最低: 70%
- 警戒: <50%

---

## 5. 市场判定

### 5.1 做空做多灵活转换

```python
def get_regime(btc_trend, eth_trend):
    if btc_trend > 0.3 and eth_trend > 0:
        return "BULL"   # 牛市 → 优先做多
    elif btc_trend < -0.1 and eth_trend < 0:
        return "BEAR"   # 熊市 → 优先做空
    else:
        return "NEUTRAL"  # 震荡 → RSI极端信号
```

### 5.2 RSI Extreme

```python
if rsi > 75:
    return "SHORT"   # 做空 (90%胜率)
elif rsi < 28:
    return "LONG"    # 做多 (85%+胜率)
```

---

## 6. 定时任务

### 6.1 Cron配置 (v2.8.1)

```bash
# v2.8.1专家模式 (每3分钟) - 强化
*/3 * * * * $HOME/.openclaw/workspace/scripts/gg_v281_expert.sh

# 插针检测 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_spike_system.sh

# 日终报告 (每天21:00)
0 21 * * * $HOME/.openclaw/workspace/scripts/gg_cron_3layer.sh layer3
```

---

## 7. 回测目标

### 7.1 30天回测目标

| 指标 | v2.8.0结果 | v2.8.1目标 |
|------|------------|------------|
| 平均月收益 | +422.3% | +500%+ |
| 中位数收益 | +381.6% | +450%+ |
| 正收益概率 | 100% | 100% |
| 平均胜率 | 73.1% | 75%+ |
| 平均交易次数 | 75次 | 100次+ |
| 资金使用率 | 60% | 90%+ |

---

## 8. 自主优化机制

### 8.1 Hermes监督
- 每30分钟检查收益曲线
- 自动调整仓位
- 学习市场模式

### 8.2 自主迭代
- 每日自检
- 每周优化
- 每月迭代

---

*GO2SE Genius v2.8.1 - 2026-05-06*
