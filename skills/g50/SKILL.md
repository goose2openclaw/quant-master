# G50 机器学习预测量化系统

## 版本
**v5.0** - ML预测 + 强化学习

## 核心升级

### 1. MLPricePredictor - 机器学习预测
- 随机森林思想预测
- 实时特征学习
- 方向预测 (上涨/下跌/震荡)
- 信心度评估

### 2. RLTrader - 强化学习交易员
- Q-Learning 算法
- 状态空间: RSI + MACD + 趋势
- 动作空间: 买入/持有/卖出
- Epsilon-greedy 探索

### 3. G40全部继承
- 7大策略融合
- AssetManagerPro
- AutoRebalancerPro

## 核心参数

```python
ML_CONFIDENCE_THRESHOLD = 0.60
PREDICTION_HORIZON = 24
RL_LEARNING_RATE = 0.01
RL_DISCOUNT_FACTOR = 0.95
SCAN_INTERVAL = 15  # 秒
STOP_LOSS = 3%
TAKE_PROFIT = 12%
KELLY = 15%
```

## 信号融合

```
综合信号 = 
  ML方向 × ML信心 × 0.4 +
  RL动作 × |Q值| × 0.3 +
  基础信号 × 0.3
```

## 与G40对比

| 特性 | G40 | G50 |
|------|-----|-----|
| 预测能力 | 策略信号 | **ML预测** |
| 策略优化 | 规则权重 | **Q-Learning** |
| 市场分析 | 单周期 | **多周期** |
| 扫描间隔 | 20s | **15s** |
| 信号置信 | 0.55 | **0.60** |

## 启动

```bash
python3 skills/g50/g50.py
```

## GitHub
- Branch: g12branch
- Commit: G50 v5.0
