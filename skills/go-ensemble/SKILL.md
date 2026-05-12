# go-ensemble - 加权组合矫正技能

## 概述
go-ensemble 是一款加权组合优化引擎，整合所有可用的因子、策略和功能，构建可调加权系数矩阵，通过反向预测（回测）和仿真与实际数据的持续迭代比较，不断修正权重，使整体预测越来越准确。

## 核心概念

### 1. 因子与策略

#### 1.1 可用因子
```python
FACTORS = {
    # 技术因子
    'technical': ['rsi', 'macd', 'bollinger', 'ma_cross', 'stoch', 'atr', 'adx', 'cci'],
    
    # 量子因子
    'quantum': ['wave_function', 'tunneling', 'phase_transition', 'energy_level'],
    
    # 热力学因子
    'thermo': ['temperature', 'entropy', 'kinetic_energy', 'heat_cycle', 'phase'],
    
    # 人性因子
    'human': ['fomo', 'fear', 'herd', 'chasing', 'disposition'],
    
    # 机构因子
    'institutional': ['mm_ratio', 'trend_ratio', 'hft_ratio', 'arb_ratio'],
    
    # 反人性因子
    'contrarian': ['human_ratio', 'contrarian_ratio', 'turning_point'],
    
    # 逆向仿真因子
    'reverse': ['optimized_rsi', 'optimized_macd', 'optimized_params'],
    
    # 元学习因子
    'meta': ['strategy_discovery', 'factor_discovery', 'skill_comparison'],
}
```

#### 1.2 可用策略
```python
STRATEGIES = {
    'mirofish': Mirofish1000Strategy,      # 模拟鱼群策略
    'oracle': OracleStrategy,              # 神谕策略
    'momentum': MomentumStrategy,         # 动量策略
    'reversion': ReversionStrategy,        # 回归策略
    'breakout': BreakoutStrategy,         # 突破策略
    'quantum': QuantumStrategy,            # 量子策略
    'thermo': ThermoStrategy,             # 热力学策略
    'contrarian': ContrarianStrategy,      # 反人性策略
    'detection': DetectionStrategy,       # 机构侦测策略
}
```

### 2. 加权系数矩阵

#### 2.1 矩阵结构
```
W = [w₁, w₂, w₃, ..., wₙ]  (权重向量)

w₁: 技术因子权重
w₂: 量子因子权重
w₃: 热力学因子权重
...
wₙ: 机构因子权重

Σwᵢ = 1.0  (归一化)
```

#### 2.2 矩阵维度
```python
MATRIX_DIMENSIONS = {
    'factor_weights': n_factors,      # 因子权重
    'strategy_weights': n_strategies,  # 策略权重
    'timeframe_weights': n_timeframes,  # 时间框架权重
    'coin_weights': n_coins,          # 币种权重
}
```

### 3. 反向预测 (Backtesting)

#### 3.1 回测流程
```
1. 获取历史数据
2. 应用当前权重矩阵 W
3. 生成预测信号
4. 计算预测误差
5. 调整权重
6. 重复迭代
```

#### 3.2 回测指标
```python
BACKTEST_METRICS = {
    'return': '收益率',
    'sharpe': '夏普比率',
    'drawdown': '最大回撤',
    'win_rate': '胜率',
    'profit_factor': '盈亏比',
    'calmar_ratio': '卡尔马比率',
}
```

### 4. 仿真与迭代

#### 4.1 仿真流程
```
Simulation Loop:
    1. Forward simulation with current W
    2. Compare with real data
    3. Calculate error: E = Σ(predicted - actual)²
    4. Update W using gradient descent or genetic algorithm
    5. Repeat until convergence or max iterations
```

#### 4.2 迭代方法
| 方法 | 描述 | 适用场景 |
|------|------|----------|
| `gradient_descent` | 梯度下降 | 连续优化 |
| `genetic` | 遗传算法 | 全局搜索 |
| `bayesian` | 贝叶斯优化 | 高维稀疏 |
| `ensemble` | 集成方法 | 稳定优化 |

### 5. 权重更新策略

#### 5.1 自适应学习
```python
class WeightUpdater:
    def update(self, W, error, learning_rate):
        # 梯度下降更新
        ΔW = -learning_rate * ∂E/∂W
        W_new = W + ΔW
        
        # 归一化
        W_new = W_new / ΣW_new
        
        return W_new
```

#### 5.2 动量更新
```python
# 加入动量加速收敛
ΔW_t = β * ΔW_{t-1} - η * ∂E/∂W
```

### 6. 持续迭代机制

#### 6.1 在线学习
```python
class OnlineLearner:
    def learn(self, new_data, predictions):
        # 计算新样本误差
        error = self.compute_error(predictions, new_data)
        
        # 更新权重
        self.W = self.update(self.W, error)
        
        # 检查漂移
        if self.detect_drift(error):
            self.trigger_retraining()
```

#### 6.2 漂移检测
```python
DRIFT_SIGNALS = {
    'error_spike': (error > μ + 3σ),  # 误差突增
    'distribution_shift': (KL_divergence > threshold),  # 分布漂移
    'concept_drift': (correlation change),  # 概念漂移
}
```

## 加权组合结构

```json
{
  "weight_matrix": {
    "factors": {
      "technical": 0.15,
      "quantum": 0.15,
      "thermo": 0.10,
      "human": 0.10,
      "institutional": 0.15,
      "contrarian": 0.20,
      "reverse": 0.10,
      "meta": 0.05
    },
    "strategies": {
      "mirofish": 0.25,
      "oracle": 0.30,
      "momentum": 0.15,
      "reversion": 0.10,
      "breakout": 0.10,
      "quantum": 0.05,
      "thermo": 0.05
    },
    "timeframes": {
      "1m": 0.10,
      "5m": 0.15,
      "1h": 0.30,
      "4h": 0.25,
      "1d": 0.20
    }
  },
  "optimization": {
    "method": "genetic",
    "learning_rate": 0.01,
    "momentum": 0.9,
    "iterations": 1000
  }
}
```

## API 使用

### Python API
```python
from skills.go_ensemble import EnsembleEngine

# 初始化
ensemble = EnsembleEngine()

# 添加组件
ensemble.add_factor('rsi', predictor_func, weight=0.1)
ensemble.add_strategy('mirofish', strategy_func, weight=0.2)
ensemble.add_skill('go-quantum', skill_instance, weight=0.15)

# 训练权重
ensemble.train(
    coin='BTC',
    period='90d',
    method='genetic',
    iterations=500
)

# 获取预测
prediction = ensemble.predict('BTC')

# 获取当前权重
weights = ensemble.get_weights()
print(f"技术因子: {weights['factors']['technical']:.2%}")
print(f"量子因子: {weights['factors']['quantum']:.2%}")

# 在线更新
ensemble.update(new_data, actual_result)

# 保存/加载
ensemble.save_weights('weights.json')
ensemble.load_weights('weights.json')
```

### 命令行
```bash
# 训练权重
go-ensemble train BTC --period 90d --method genetic --iterations 500

# 预测
go-ensemble predict BTC

# 查看权重
go-ensemble weights

# 在线更新
go-ensemble update --data_file data.csv

# 保存
go-ensemble save weights.json

# 加载
go-ensemble load weights.json
```

## 文件结构
```
skills/go-ensemble/
├── SKILL.md              # 本文档
├── ensemble_engine.py       # 核心引擎
├── weight_optimizer.py      # 权重优化
├── backtest.py            # 回测模块
├── simulation.py          # 仿真模块
└── drift_detector.py       # 漂移检测
```

---

**版本**: 1.0.0
**创建**: 2026-05-13
**作者**: OpenClaw AI Assistant
