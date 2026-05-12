# go-reverse - 逆向仿真参数优化技能

## 概述
go-reverse 是一个逆向仿真参数优化引擎，针对每个具体币种/合约/证券，利用历史回测数据进行逆向拟合，生成和优化专属参数集，提升预测准确度。

## 核心概念

### 逆向仿真
通过历史数据反向推算最优参数：
```
历史数据 → 参数拟合 → 最优参数集 → 预测应用
     ↓
验证 → 迭代优化 → 参数更新
```

### 专属参数集
每个币种拥有自己的优化参数：
```python
BTC_PARAMS = {
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'momentum_threshold': 0.05,
    'volatility_multiplier': 2.0,
    'position_size': 0.10,
    ...
}
```

## 核心功能

### 1. 回测数据采集

| 数据类型 | 描述 |
|----------|------|
| OHLCV | 1m/5m/15m/1h/4h/1d |
| 订单流 | 买卖单簿 |
| 资金费率 | 合约资金费率 |
| 链上数据 | 流入/流出 |
| 情绪数据 | 多空比 |

### 2. 逆向拟合方法

#### 2.1 参数扫描
| 方法 | 描述 |
|------|------|
| `grid_search` | 网格搜索 |
| `random_search` | 随机搜索 |
| `bayesian` | 贝叶斯优化 |
| `genetic` | 遗传算法 |
| `gradient` | 梯度下降 |

#### 2.2 拟合目标
```python
# 优化目标
TARGETS = {
    'max_sharpe': '最大夏普比率',
    'max_return': '最大收益',
    'min_dd': '最小回撤',
    'max_winrate': '最高胜率',
    'balance': '平衡模式'
}
```

#### 2.3 参数约束
```python
# 每个参数的合理范围
PARAM_RANGES = {
    'rsi_oversold': (20, 40),
    'rsi_overbought': (60, 80),
    'momentum_threshold': (0.01, 0.10),
    'stop_loss': (0.02, 0.10),
    'take_profit': (0.05, 0.30),
    'position_size': (0.05, 0.25),
    'ma_short': (5, 30),
    'ma_long': (20, 200),
}
```

### 3. 逆向仿真模型

| 模型 | 适用场景 |
|------|----------|
| `reverse_rsi` | RSI参数优化 |
| `reverse_macd` | MACD参数优化 |
| `reverse_bollinger` | 布林带参数优化 |
| `reverse_grid` | 网格参数优化 |
| `reverse_dca` | 定投参数优化 |
| `reverse_momentum` | 动量参数优化 |
| `reverse_volatility` | 波动率参数优化 |

### 4. 优化流程

```
1. 数据准备
   └── 历史K线 → 特征提取

2. 参数初始化
   └── 默认参数 → 范围设置

3. 逆向拟合
   └── 网格/贝叶斯/遗传算法

4. 验证
   └── 训练集/测试集分离

5. 参数输出
   └── 最优参数集 → JSON

6. 持续迭代
   └── 新数据 → 参数更新
```

### 5. 输出格式

```json
{
  "coin": "BTC",
  "timeframe": "1h",
  "optimized_at": "2026-05-13",
  "target": "max_sharpe",
  "parameters": {
    "rsi_oversold": 28,
    "rsi_overbought": 72,
    "momentum_threshold": 0.035,
    "stop_loss": 0.035,
    "take_profit": 0.12,
    "position_size": 0.12
  },
  "backtest_results": {
    "total_return": 45.2,
    "sharpe_ratio": 2.34,
    "max_drawdown": 8.5,
    "win_rate": 68.5,
    "trade_count": 156
  },
  "validation": {
    "train_score": 0.72,
    "test_score": 0.68,
    "overfit_ratio": 0.06
  },
  "confidence": 0.85
}
```

### 6. 专属参数示例

```python
# BTC 专属参数 (波动性低)
BTC_PARAMS = {
    'rsi_oversold': 35,
    'rsi_overbought': 68,
    'stop_loss': 0.025,
    'take_profit': 0.08,
    'position_size': 0.15,
}

# PEPE 专属参数 (波动性高)
PEPE_PARAMS = {
    'rsi_oversold': 25,
    'rsi_overbought': 75,
    'stop_loss': 0.08,
    'take_profit': 0.25,
    'position_size': 0.05,
}

# ETH 专属参数 (平衡型)
ETH_PARAMS = {
    'rsi_oversold': 32,
    'rsi_overbought': 70,
    'stop_loss': 0.04,
    'take_profit': 0.12,
    'position_size': 0.10,
}
```

## API 使用

### Python API
```python
from skills.go_reverse import ReverseEngine

# 初始化
optimizer = ReverseEngine()

# 逆向拟合
result = optimizer.optimize(
    coin='BTC',
    timeframe='1h',
    period='90d',
    target='max_sharpe'
)

# 获取最优参数
params = result.get_params()
print(f"BTC最优参数: {params}")

# 应用到预测
prediction = go.predict('BTC', custom_params=params)

# 批量优化
results = optimizer.batch_optimize(
    coins=['BTC', 'ETH', 'PEPE'],
    timeframe='1h'
)

# 获取参数集
param_sets = optimizer.get_param_sets()
```

### 命令行
```bash
# 优化单个币种
go-reverse optimize BTC --timeframe 1h --period 90d

# 批量优化
go-reverse batch --coins BTC,ETH,PEPE --timeframe 1h

# 查看参数
go-reverse params BTC

# 验证参数
go-reverse validate BTC --params params.json
```

## 文件结构
```
skills/go-reverse/
├── SKILL.md              # 本文档
├── reverse_engine.py      # 核心引擎
├── optimizers.py        # 优化算法
├── validators.py         # 参数验证
└── cache/              # 参数缓存
```

---

**版本**: 1.0.0
**创建**: 2026-05-13
**作者**: OpenClaw AI Assistant
