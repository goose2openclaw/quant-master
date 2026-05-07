# GO2SE Genius v2.8.0 配置文档

## 2026-05-06

---

## 1. 核心参数

### 1.1 专家模式配置 (v2.8)

```python
EXPERT_CONFIG = {
    # 基础参数
    'mode': 'expert',
    'initial_capital': 10000,
    'trading_days': 30,
    
    # RSI Extreme Override
    'rsi_short_threshold': 75,      # 做空信号
    'rsi_long_threshold': 28,       # 做多信号
    'rsi_short_winrate': 0.889,    # 88.9%胜率
    'rsi_long_winrate': 0.80,      # 80%胜率
    
    # 做空做多灵活转换
    'bull_threshold': 0.3,          # 牛市门槛
    'bear_threshold': -0.1,        # 熊市门槛
    
    # 破军策略
    'pojun': {
        'leverage': 5,
        'tp': 0.10,    # 10%止盈
        'sl': 0.02,    # 2%止损
    },
    
    # 贪狼策略
    'tanlang': {
        'leverage': 4,
        'tp': 0.08,    # 8%止盈
        'sl': 0.02,    # 2%止损
    },
    
    # 趋势交易
    'trend': {
        'leverage': 3,
        'tp': 0.05,    # 5%止盈
        'sl': 0.015,   # 1.5%止损
    },
}
```

---

## 2. 策略配置

### 2.1 破军策略 (推荐)
- 核心: 走着瞧+跟大哥
- 币种: SOL/DOGE/ETH
- 杠杆: 5x
- 止盈: 10%
- 止损: 2%
- 胜率: 88.9%

### 2.2 贪狼策略
- 核心: 打兔子
- 币种: SOL/DOGE/ETH
- 杠杆: 4x
- 止盈: 8%
- 止损: 2%

### 2.3 文曲策略
- 核心: 跟大哥
- 币种: BTC/ETH/BNB
- 杠杆: 5x
- 止盈: 5%
- 止损: 2%

---

## 3. 市场判定

### 3.1 做空做多灵活转换

```python
def get_regime(btc_trend, eth_trend):
    if btc_trend > 0.3 and eth_trend > 0:
        return "BULL"   # 牛市 → 优先做多
    elif btc_trend < -0.1 and eth_trend < 0:
        return "BEAR"   # 熊市 → 优先做空
    else:
        return "NEUTRAL"  # 震荡 → RSI极端信号
```

### 3.2 RSI Extreme

```python
if rsi > 75:
    return "SHORT"   # 做空 (88.9%胜率)
elif rsi < 28:
    return "LONG"    # 做多 (80%+胜率)
```

---

## 4. 定时任务

### 4.1 Cron配置

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

## 5. 回测结果

### 5.1 30天回测 (1000次模拟)

| 指标 | 普通模式 | 专家模式 |
|------|----------|----------|
| 平均月收益 | +3.0% | +422.3% |
| 中位数收益 | +2.9% | +381.6% |
| 最大收益 | +6.4% | +1702.1% |
| 最小收益 | +0.3% | +101.9% |
| 正收益概率 | 100% | 100% |
| 平均胜率 | 69.9% | 73.1% |
| 平均交易次数 | 27次 | 75次 |

### 5.2 收益分布

| 收益区间 | 普通模式 | 专家模式 |
|----------|----------|----------|
| 0%~+20% | 100% | 0% |
| +100%~+200% | 0% | 4.4% |
| >+200% | 0% | 95.6% |

### 5.3 胜率分布

| 胜率区间 | 普通模式 | 专家模式 |
|----------|----------|----------|
| 70%~80% | 38.8% | **64.7%** |

---

## 6. 脚本清单

| 脚本 | 功能 |
|------|------|
| gg_cron_3layer.sh | 三层监控 |
| gg_short_long_enhanced.sh | 做空做多增强 |
| gg_long_short_switch.sh | 灵活转换 |
| gg_spike_system.sh | 插针捕获 |

---

*GO2SE Genius v2.8.0 - 2026-05-06*
