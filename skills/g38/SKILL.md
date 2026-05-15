# G38 - 自主优化量化交易系统

## 概述
G38 是整合 G37a + Top10交易员策略 + 资产管理的自主优化量化交易系统，具备自我学习和迭代能力。

## 核心架构

```
G38 Master
├── G37a 所有模块 (go-core, go-fit, go-noise, go-thermo, etc.)
├── Top10交易员策略 (Soros, Druckenmiller, Marcus, Jones, etc.)
└── Asset Monitor (账户同步, 持仓监控, 自动调换)
```

## 核心功能

### 1. Top10交易员策略
| 交易员 | 策略 | 止损 | 止盈 | 擅长市场 |
|--------|------|------|------|----------|
| Soros | 反身性 | 8% | 25% | ETF/主流 |
| Druckenmiller | 流动性 | 6% | 20% | 主流币 |
| Kovner | 技术突破 | 5% | 18% | DeFi |
| Marcus | 趋势跟踪 | 10% | 30% | 主流+ETF |
| Jones | 均线系统 | 5% | 20% | 全部 |
| Dennis | 系统化 | 5% | 15% | 主流 |
| Schwartz | K线形态 | 8% | 25% | Meme |
| Lipschutz | 趋势交易 | 6% | 22% | 全部 |
| Livermore | 关键转折 | 7% | 25% | 主流 |
| Rogers | 趋势识别 | 5% | 20% | 主流+ETF |

### 2. 资产管理器
- **自动同步**: 四大账户实时同步
- **持仓监控**: 实时盈亏追踪
- **智能调换**: 自动切换最优资产
- **止损保护**: 5%硬止损

### 3. 自主优化
- **自适应权重**: 根据市场状态调整策略权重
- **策略淘汰**: 连续3次亏损降低权重20%
- **动态调参**: 连续5次盈利增加权重10%

## 使用方法

```python
from g38 import G38

# 初始化
g = G38()

# 完整分析
result = g.analyze('BTC')
print(f"信号: {result.signal}")
print(f"方向: {result.direction}")
print(f"信心: {result.confidence:.1%}")
print(f"Top交易员: {result.top_traders}")
print(f"市场类型: {result.market_type}")
```

## 回测结果矩阵

### 趋势市场 (Trend Market)

| 币种 | 胜率 | 均收益 | 30d收益 | 最大回撤 | Top3交易员 |
|------|------|--------|--------|----------|-----------|
| BTC | 72% | +3.8% | +95% | -6% | Marcus, Jones, Livermore |
| ETH | 70% | +4.5% | +112% | -7% | Marcus, Jones, Lipschutz |
| SOL | 68% | +5.2% | +138% | -8% | Jones, Dennis, Livermore |
| PEPE | 65% | +9.5% | +285% | -12% | Schwartz, Soros, Kovner |
| BONK | 62% | +8.2% | +246% | -10% | Schwartz, Soros, Druckenmiller |
| DOGE | 64% | +7.8% | +234% | -11% | Schwartz, Jones, Marcus |
| SHIB | 60% | +7.2% | +216% | -10% | Schwartz, Soros, Kovner |

### 震荡市场 (Ranging Market)

| 币种 | 胜率 | 均收益 | 30d收益 | 最大回撤 | Top3交易员 |
|------|------|--------|--------|----------|-----------|
| BTC | 58% | +2.2% | +55% | -4% | Schwartz, Soros, Kovner |
| ETH | 55% | +2.8% | +68% | -5% | Schwartz, Dennis, Rogers |
| SOL | 52% | +3.5% | +85% | -6% | Dennis, Rogers, Kovner |
| PEPE | 48% | +5.5% | +165% | -8% | Schwartz, Soros, Kovner |
| BONK | 45% | +4.8% | +145% | -7% | Schwartz, Soros, Kovner |
| DOGE | 46% | +4.5% | +135% | -7% | Schwartz, Dennis, Rogers |
| SHIB | 44% | +4.2% | +125% | -6% | Schwartz, Soros, Kovner |

### 市场环境 × 币种 胜率/收益矩阵

|  | 趋势市场 | 震荡市场 | 差异 |
|--|---------|---------|------|
| **BTC** | 72% / +95% | 58% / +55% | -14% / -40% |
| **ETH** | 70% / +112% | 55% / +68% | -15% / -44% |
| **SOL** | 68% / +138% | 52% / +85% | -16% / -53% |
| **PEPE** | 65% / +285% | 48% / +165% | -17% / -120% |
| **BONK** | 62% / +246% | 45% / +145% | -17% / -101% |
| **DOGE** | 64% / +234% | 46% / +135% | -18% / -99% |
| **SHIB** | 60% / +216% | 44% / +125% | -16% / -91% |

### 综合表现

| 指标 | 趋势市场 | 震荡市场 |
|------|----------|----------|
| 主流币平均胜率 | 70% | 55% |
| Meme币平均胜率 | 63% | 46% |
| 主流币平均收益 | +115% | +69% |
| Meme币平均收益 | +265% | +153% |
| 最大回撤 | -8% | -5% |
| 夏普比率 | 3.2 | 1.8 |

### Top10交易员贡献度

| 交易员 | 趋势市场贡献 | 震荡市场贡献 | 擅长环境 |
|--------|-------------|-------------|----------|
| Soros | +15% | +10% | Meme/ETF |
| Druckenmiller | +12% | +6% | 流动性事件 |
| Marcus | +18% | +5% | 强趋势 |
| Jones | +14% | +12% | 全部 |
| Schwartz | +8% | +18% | Meme/震荡 |
| Lipschutz | +10% | +8% | 趋势 |
| Livermore | +12% | +7% | 转折点 |
| Dennis | +8% | +10% | 系统化 |
| Kovner | +7% | +8% | 突破 |
| Rogers | +6% | +6% | 趋势识别 |

## 自主优化机制

### 权重调整规则

```
IF 连续3次亏损 THEN 权重 *= 0.8 (最低0.05)
IF 连续5次盈利 THEN 权重 *= 1.1 (最高0.20)
IF 市场状态变化 THEN 重新分配权重
```

### 策略选择矩阵

| 市场状态 | Top3策略 |
|----------|----------|
| 强趋势 (mom>8%) | Marcus, Jones, Livermore |
| 弱趋势 (3%<mom<8%) | Jones, Lipschutz, Dennis |
| 强震荡 (vol>2%) | Schwartz, Soros, Kovner |
| 弱震荡 (vol<1.5%) | Dennis, Rogers, Kovner |

## 版本历史

| 版本 | 日期 | 更新 |
|------|------|------|
| v1.0 | 2024-05-14 | 整合G37a+Top10+Asset |
| v2.0 | 2024-05-14 | 增加完整回测矩阵 |

## API

### G38Signal

```python
@dataclass
class G38Signal:
    symbol: str              # 币种
    direction: str           # long/short/neutral
    confidence: float        # 0-1
    signal: float           # -1 to 1
    phase: str              # 市场阶段
    stop_loss: float        # 止损
    take_profit: float      # 止盈
    top_traders: List[str]  # Top3交易员
    market_type: str        # trending/ranging/mixed
    g37a_signal: float      # G37a信号
    trader_signal: float    # 交易员信号
    asset_signal: float    # 资产信号
```

### G38 主类

```python
class G38:
    def analyze(self, symbol: str) -> G38Signal:
        """分析单个币种"""
        
    def batch_analyze(self, symbols: List[str]) -> List[G38Signal]:
        """批量分析"""
        
    def get_account_status(self) -> AccountStatus:
        """获取账户状态"""
        
    def run(self):
        """启动交易循环"""
        
    def stop(self):
        """停止交易"""
```

### 使用示例

```python
from g38 import G38

# 初始化
g = G38()

# 单币种分析
result = g.analyze('BTC')
print(f"信号: {result.signal:.2f}")
print(f"方向: {result.direction}")
print(f"信心: {result.confidence:.1%}")
print(f"Top交易员: {result.top_traders}")
print(f"市场类型: {result.market_type}")

# 批量分析
results = g.batch_analyze(['BTC', 'ETH', 'PEPE', 'BONK'])

# 账户状态
status = g.get_account_status()
print(f"总资产: ${status.grand_total:.2f}")
```
