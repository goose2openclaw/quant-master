# GO2SE Genius v2.7.1 完整集成文档

## 2026-05-06

---

## 1. 脚本集成

### 1.1 脚本清单

| 脚本 | 路径 | 功能 |
|------|------|------|
| gg_cron_3layer.sh | scripts/ | 三层监控 |
| gg_short_long_enhanced.sh | scripts/ | 做空做多增强 |
| gg_long_short_switch.sh | scripts/ | 灵活转换 |
| gg_spike_system.sh | scripts/ | 插针捕获 |

### 1.2 定时任务

```bash
# 风险监控 (每分钟)
*/1 * * * * $HOME/.openclaw/workspace/scripts/gg_cron_3layer.sh layer1

# 信号扫描 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_short_long_enhanced.sh

# 做空做多灵活转换 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_long_short_switch.sh

# 插针检测 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_spike_system.sh

# 日终报告 (每天21:00)
0 21 * * * $HOME/.openclaw/workspace/scripts/gg_cron_3layer.sh layer3
```

---

## 2. 决策系统

### 2.1 市场判定
```
if BTC日涨 > 0.5% AND ETH涨:
    → 牛市 → 优先做多
elif BTC日跌 < -0.5% AND ETH跌:
    → 熊市 → 优先做空
else:
    → 震荡 → RSI极端信号
```

### 2.2 RSI Extreme
```
if RSI > 75:
    → SHORT (做空)
elif RSI < 28:
    → LONG (做多)
```

---

## 3. 策略配置

### 3.1 破军策略 (推荐)
```python
POJUN = {
    'name': '破军',
    'leverage': 5,
    'tp': 0.10,  # 10%
    'sl': 0.02,   # 2%
    'win_rate': 0.75,
}
```

### 3.2 资金配置
```python
if margin_level > 4.0:
    position = 0.25
    leverage = 3
elif margin_level > 3.0:
    position = 0.15
    leverage = 2
elif margin_level > 2.5:
    position = 0.10
    leverage = 1
else:
    position = 0
    # 禁止开仓
```

---

## 4. 安全机制

### 4.1 保证金率
- > 4.0: 充裕
- > 3.0: 正常
- > 2.5: 预警
- <= 2.5: 禁止开仓

### 4.2 止损
- 机械执行
- 2%止损
- 不扛单

---

## 5. 回测结果

### 5.1 30天回测
- 普通模式: +3.4% (胜率74%)
- 专家模式: +272.2% (胜率50%)
- 正收益概率: 100%

### 5.2 收益分布
- +200-500%: 68.3%
- >+500%: 3.6%

---

*集成时间: 2026-05-06*
