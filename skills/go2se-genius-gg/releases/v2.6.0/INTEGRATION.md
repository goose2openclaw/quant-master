# GO2SE Genius v2.6 集成文档

## 2026-05-06

---

## 1. 定时任务集成

### 1.1 任务清单

| 任务 | 频率 | 功能 | 脚本 |
|------|------|------|------|
| 风险监控 | 1分钟 | 保证金率检查 | gg_cron_3layer.sh layer1 |
| 信号扫描 | 5分钟 | 做空做多信号 | gg_short_long_enhanced.sh |
| 插针检测 | 5分钟 | 插针捕获 | gg_spike_system.sh |
| 自主交易 | 5分钟 | 自动买卖 | gg_cron_3layer.sh layer2 |
| 日终报告 | 21:00 | 每日汇总 | gg_cron_3layer.sh layer3 |

### 1.2 Cron配置

```bash
# 风险监控 (每分钟)
*/1 * * * * $HOME/.openclaw/workspace/scripts/gg_cron_3layer.sh layer1

# 信号扫描 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_short_long_enhanced.sh

# 插针检测 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_spike_system.sh

# 日终报告 (每天21:00)
0 21 * * * $HOME/.openclaw/workspace/scripts/gg_cron_3layer.sh layer3
```

---

## 2. 做空做多增强系统

### 2.1 做空信号 (4种)

| 信号 | 触发条件 | 操作 |
|------|----------|------|
| SPIKE_UP | 向上插针突破布林上轨+1% | 做空 |
| RSI_OVERBOUGHT | RSI>70 + MACD死叉 | 做空 |
| WEAK_REBOUND | 反弹无力(<30%回落) | 做空 |
| VOL_PRICE_DIVERGE | 缩量上涨背离 | 做空 |

### 2.2 做多信号 (4种)

| 信号 | 触发条件 | 操作 |
|------|----------|------|
| SPIKE_DOWN | 向下插针跌破布林下轨-1% | 做多 |
| RSI_OVERSOLD | RSI<40 + MACD金叉 | 做多 |
| SUPPORT_REBOUND | 回调支撑确认 | 做多 |
| VOL_SUPPORT | 缩量获得支撑 | 做多 |

### 2.3 参数配置

```python
# 止损止盈
STOP_LOSS = 0.01  # 1%
TAKE_PROFIT = 0.02  # 2%
SPIKE_STOP_LOSS = 0.015  # 1.5%

# 资金配置
MIN_MARGIN_LEVEL = 3.0
DANGER_MARGIN_LEVEL = 2.5
MAX_POSITION = 0.2  # 20%
```

---

## 3. 即时算力匹配

### 3.1 算力池

| 等级 | CPU | 内存 | 风险 | 场景 |
|------|-----|------|------|------|
| 高 | 4核 | 8GB | 高 | 高确定性信号 |
| 中 | 2核 | 4GB | 中 | 中等信号 |
| 低 | 1核 | 2GB | 低 | 观望信号 |

### 3.2 匹配规则

```python
if signal in ['SPIKE_UP', 'RSI_OVERBOUGHT'] and confidence > 0.7:
    compute = 'high'
elif signal in ['RSI_OVERSOLD', 'SUPPORT_REBOUND'] and confidence > 0.6:
    compute = 'medium'
else:
    compute = 'low'
```

---

## 4. 即时资金调配

### 4.1 调配规则

| 保证金率 | 操作 | 仓位 | 杠杆 |
|----------|------|------|------|
| < 2.5 | 🚨强制减仓 | 0% | 禁止 |
| 2.5-3.0 | ⚠️预警 | 10% | 1x |
| 3.0-4.0 | ✅正常 | 15% | 2x |
| > 4.0 | 💰充裕 | 25% | 3x |

### 4.2 波动率调整

```python
if volatility > 0.03:
    position_pct *= 0.8  # 高波动减仓
    leverage = min(leverage, 2)
```

---

## 5. 安全机制

### 5.1 风险等级

| 等级 | 条件 | 操作 |
|------|------|------|
| 危险 | margin < 2.5 | 禁止开仓，强制减仓 |
| 预警 | margin < 3.0 | 谨慎操作，减半仓 |
| 正常 | margin >= 3.0 | 正常操作 |
| 充裕 | margin > 4.0 | 可加大仓位 |

### 5.2 止损规则

- 机械执行，不扛单
- 亏损达1%立即止损
- 插针模式亏损1.5%止损

---

## 6. 模式切换

### 6.1 普通模式

```python
MODE_NORMAL = {
    'trades_per_day': 3,
    'tp': 0.02,  # 2%
    'sl': 0.01,  # 1%
    'win_rate': 0.68,
    'leverage': 1
}
```

### 6.2 专家模式

```python
MODE_EXPERT = {
    'trades_per_day': 5,
    'tp': 0.03,  # 3%
    'sl': 0.01,  # 1%
    'win_rate': 0.72,
    'leverage': 'dynamic',  # 动态1-5x
    'spike_enhanced': True
}
```

---

*GO2SE Genius v2.6.0 - 2026-05-06*
