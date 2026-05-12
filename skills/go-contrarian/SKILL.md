# go-contrarian - 反人性分析技能

## 概述
go-contrarian 是一个反人性分析引擎，通过回测历史数据，识别交易中的人性特征和反人性因素，尤其关注市场转折点和关键时刻，形成人性/反人性比例趋势，预测下一个转折点的人性表现。

## 核心概念

### 人性因素
人类在交易中常见的非理性行为：
- **贪婪 (Greed)**: FOMO追高, 持有亏损仓位期望回本
- **恐惧 (Fear)**: 恐慌抛售, 止损过早
- **从众 (Herd)**: 跟随大众, 羊群效应
- **锚定 (Anchoring)**: 锚定成本价, 不愿止损
- **确认偏误 (Confirmation)**: 只看支持自己观点的信息
- **后见之明 (Hindsight)**: 过度自信

### 反人性因素
识别并利用人类非理性：
- **逆向交易**: 在大众恐惧时买入, 在大众贪婪时卖出
- **止损纪律**: 严格止损, 不让亏损扩大
- **仓位管理**: 分散风险, 不重仓单一币种
- **情绪隔离**: 不受短期波动影响
- **概率思维**: 关注期望值而非单次结果

## 核心功能

### 1. 人性特征识别

#### 1.1 价格行为人性特征
| 特征 | 描述 | 信号 |
|------|------|------|
| `fomo_spike` | FOMO上涨 | 放量突破后回调 |
| `panic_dump` | 恐慌抛售 | 放量下跌后反弹 |
| `chasing` | 追涨杀跌 | RSI极端值附近的追单 |
| `diamond_hands` | 钻石手 | 长期持有不动 |
| `paper_hands` | 纸手 | 小盈即跑 |

#### 1.2 成交量人性特征
| 特征 | 描述 | 信号 |
|------|------|------|
| `volume_spike` | 成交量突增 | 人性驱动 |
| `volume_dry` | 成交量枯竭 | 冷静期 |
| `buy_the_dip` | 抄底 | 逆人性 |
| `sell_the_rip` | 卖反弹 | 顺势 |

#### 1.3 持仓人性特征
| 特征 | 描述 | 信号 |
|------|------|------|
| `avg_entry_anchor` | 成本锚定 | 不愿止损 |
| `overweight_top` | 重仓追高 | 风险聚集 |
| `diversification_illusion` | 分散幻觉 | 持仓过多 |

### 2. 转折点识别

#### 2.1 转折点类型
| 类型 | 描述 | 人性特征 |
|------|------|----------|
| `top_local` | 局部顶部 | 贪婪顶峰, FOMO高潮 |
| `bottom_local` | 局部底部 | 恐慌抛售, 绝望 |
| `trend_reversal` | 趋势反转 | 过度乐观/悲观 |
| `consolidation_break` | 盘整突破 | 犹豫到确认 |

#### 2.2 转折点信号
```python
# 转折点检测
TURNOINT_SIGNALS = {
    'rsi_extreme': (RSI > 80 or RSI < 20),  # RSI极端
    'volume_diverge': (price_up & volume_down),  # 量价背离
    'momentum_weaken': (momentum_peak & price_peak),  # 动量减弱
    'sentiment_extreme': (fear_greed > 90 or < 10),  # 情绪极端
}
```

### 3. 人性/反人性比例

#### 3.1 比例计算
```
Human_Ratio = Human_Factor_Score / Total_Score
Contrarian_Ratio = 1 - Human_Ratio

Human_Factor_Score = f(FOMO, Fear, Herd, Anchoring)
Contrarian_Factor_Score = f(逆向交易, 止损纪律, 仓位管理)
```

#### 3.2 比例趋势
```json
{
  "coin": "BTC",
  "timeframe": "1h",
  "current": {
    "human_ratio": 0.75,
    "contrarian_ratio": 0.25,
    "phase": "GREED_PEAK"
  },
  "history": [
    {"time": "10:00", "human_ratio": 0.60},
    {"time": "10:30", "human_ratio": 0.70},
    {"time": "11:00", "human_ratio": 0.80},
  ],
  "prediction": {
    "next_turning_point": "2026-05-13 14:00",
    "expected_human_ratio": 0.85,
    "expected_phase": "EXTREME_GREED",
    "action": "CONTRARIAN_SELL"
  }
}
```

### 4. 人性K线图

```
Human K线图:
┌─────────────────────────────────────────────────────────┐
│ 1.0 ┤  ╱╲    ╱╲    ╱╲                         │
│      │ ╱  ╲╱    ╲╱    ╲                       │
│ 0.5 ┤                  ╱╲                       │
│      │                 ╱  ╲                      │
│ 0.0 ┤                ╱    ╲                     │
│      │               ╱      ╲                    │
│      │              ╱        ╲                   │
└─────────────────────────────────────────────────────────┘
        ↑局部顶  ↑转折点  ↑局部底  ↑转折点
        
反人性信号: CONTRARIAN_BUY (当人性比<0.3)
人性信号: HUMAN_SELL (当人性比>0.8)
```

### 5. 预测模型

```python
# 转折点预测
class TurningPointPredictor:
    def predict(self, coin, timeframe):
        # 分析历史转折点
        turning_points = self.find_turning_points(coin, timeframe)
        
        # 计算人性比例
        human_ratios = self.calculate_human_ratios(turning_points)
        
        # 预测下次转折点
        next_turning = self.predict_next(turning_points)
        
        # 输出预测
        return {
            'next_time': next_turning.time,
            'expected_ratio': next_turning.human_ratio,
            'expected_phase': next_turning.phase,
            'confidence': next_turning.confidence
        }
```

## API 使用

### Python API
```python
from skills.go_contrarian import ContrarianEngine

# 初始化
contrarian = ContrarianEngine()

# 分析人性特征
analysis = contrarian.analyze(
    coin='BTC',
    timeframe='1h',
    period='30d'
)

# 获取人性比例
ratio = analysis.get_human_ratio()
print(f"当前人性比: {ratio.human:.2%}")
print(f"反人性比: {ratio.contrarian:.2%}")

# 获取人性K线
kline = analysis.get_human_kline()
print(f"人性K线数据: {kline}")

# 预测下次转折点
prediction = analysis.predict_turning_point()
print(f"下次转折: {prediction.time}")
print(f"预期人性比: {prediction.human_ratio:.2%}")
print(f"操作建议: {prediction.action}")

# 获取人性阶段
phase = analysis.get_phase()
print(f"当前阶段: {phase}")
```

### 命令行
```bash
# 人性分析
go-contrarian analyze BTC --timeframe 1h --period 30d

# 人性K线
go-contrarian kline BTC --timeframe 1h

# 预测转折点
go-contrarian predict BTC --horizon 24h

# 人性阶段
go-contrarian phase BTC
```

## 文件结构
```
skills/go-contrarian/
├── SKILL.md              # 本文档
├── contrarian_engine.py    # 核心引擎
├── human_features.py      # 人性特征
├── turning_point.py       # 转折点检测
└── prediction.py         # 预测模型
```

---

**版本**: 1.0.0
**创建**: 2026-05-13
**作者**: OpenClaw AI Assistant
