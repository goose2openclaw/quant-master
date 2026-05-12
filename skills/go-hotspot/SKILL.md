# go-hotspot - 投资热点技能

## 概述
go-hotspot 是一个投资热点分析与追踪引擎，通过对比特币归一化的相对价格K线图，分析资金流向、市场热点转换、跨币种轮动，形成投资热点流动图和加权热点趋势信号。

## 核心概念

### 投资热点定义
投资热点是指在特定时间段内，资金集中涌入的币种或资产，反映市场情绪和资金流向的变化。

### 归一化K线图
```
Relative_Price = Asset_Price / BTC_Price
Hotspot_Ratio = Relative_Price_Current / Relative_Price_Past
```

## 核心功能

### 1. 数据源
- **交易所**: Binance, Coinbase, Kraken
- **资产**: 主流币(30+)、Meme币(25+)、股票(10+)
- **时间框架**: 1m, 5m, 15m, 1h, 4h, 1d
- **回溯周期**: 7d, 30d, 90d, 180d

### 2. 热点分析模型

#### 2.1 资金流向模型
| 模型ID | 名称 | 描述 |
|--------|------|------|
| `flow_ inflows` | 净流入分析 | 交易所净流入/流出 |
| `flow_outflows` | 净流出分析 | 跨交易所转账 |
| `flow_whale` | 巨鲸追踪 | 大户转账监控 |
| `flow_retail` | 散户流向 | 散户资金方向 |
| `flow_institutional` | 机构流向 | ETF/灰度资金流 |

#### 2.2 热点轮动模型
| 模型ID | 名称 | 描述 |
|--------|------|------|
| `rotate_major_to_alt` | 主流切山寨 | BTC优势转向 |
| `rotate_alt_to_major` | 山寨切主流 | 山寨资金轮动 |
| `rotate_sector` | 板块轮动 | DeFi/L1/Metaverse轮动 |
| `rotate_meme` | Meme轮动 | 新Meme热点切换 |
| `rotate_cross` | 跨市场轮动 | 股债商品联动 |

#### 2.3 相对强弱模型
| 模型ID | 名称 | 描述 |
|--------|------|------|
| `rel_btc_dom` | BTC主导地位 | BTC市值占比变化 |
| `rel_alt_cap` | 山寨市值 | 排除BTC的市值 |
| `rel_strength` | 相对强弱 | vs BTC/ETH/S&P500 |
| `rel_momentum` | 相对动量 | 相对价格动量 |
| `rel_correlation` | 相关性变化 | 滚动相关性 |

#### 2.4 合约杠杆模型
| 模型ID | 名称 | 描述 |
|--------|------|------|
| `lever_long_short` | 多空比 | 合约多空比 |
| `lever_funding` | 资金费率 | 合约资金费率 |
| `lever_open_interest` | 未平仓量 | 持仓量变化 |
| `lever_liquidation` | 清算热力 | 清算密集区 |
| `lever_taker` | Taker买卖比 | 主动买卖盘 |

#### 2.5 跨资产模型
| 模型ID | 名称 | 描述 |
|--------|------|------|
| `cross_corr_btc_eth` | BTC-ETH相关 | 比特币以太坊相关性 |
| `cross_corr_btc_sp500` | BTC-标普相关 | 与美股相关性 |
| `cross_corr_alt_btc` | 山寨-BTC相关 | 山寨与BTC联动 |
| `cross_lead_lag` | 领先滞后 | 谁领先谁滞后 |
| `cross_spread` | 跨资产价差 | 相关资产价差 |

### 3. 投资热点指标

| 指标 | 描述 | 计算方法 |
|------|------|----------|
| `hotspot_score` | 热点评分 | 归一化价格变化 |
| `hotspot_velocity` | 热点速度 | 价格变化率 |
| `hotspot_acceleration` | 热点加速 | 速度变化率 |
| `hotspot_momentum` | 热点动量 | 滚动动量和 |
| `hotspot_temperature` | 热点温度 | 成交量加权变化 |
| `hotspot_flow` | 资金流量 | 净流入/总流通 |

### 4. 热点周期

| 周期 | 描述 | 适用场景 |
|------|------|----------|
| `ultrafast` | <1小时 | 短线交易 |
| `intraday` | 1-24小时 | 日内交易 |
| `swing` | 1-7天 | 波段交易 |
| `position` | 1-4周 | 持仓策略 |
| `trend` | 1-3月 | 趋势跟踪 |

### 5. 热点信号

```json
{
  "coin": "PEPE",
  "timeframe": "1h",
  "hotspot_score": 0.85,
  "hotspot_velocity": 2.3,
  "hotspot_momentum": "ACCELERATING",
  "temperature": 78.5,
  "flow_direction": "INFLOW",
  "vs_btc_performance": "+15.3%",
  "vs_eth_performance": "+8.7%",
  "rank_change": "+12",
  "signal": "STRONG_HOTSPOT",
  "confidence": 0.82,
  "action": "BUY"
}
```

### 6. 热点流动图

```
BTC Dominance: 52.3% (-2.1%)
┌─────────────────────────────────────────┐
│ PEPE  ████████████████████░░░  +45% 🔥
│ FLOKI █████████████████░░░░░░ +32% 🌡️
│ WIF   ████████████████░░░░░░░ +28% 📈
│ DOGE  ████████████░░░░░░░░░░ +18% ↗️
│ ETH   ██████████░░░░░░░░░░░░ +12% →
│ BTC   ░░░░░░░░░░░░░░░░░░░░░ 基准  │
└─────────────────────────────────────────┘

资金流向: PEPE > FLOKI > WIF > DOGE
热点温度: 78.5°C (高热)
```

### 7. 加权热点输出

```python
# 热点权重计算
weights = {
    'relative_performance': 0.30,  # 相对BTC表现
    'momentum': 0.25,             # 动量
    'flow_direction': 0.20,        # 资金流向
    'volume': 0.15,               # 成交量
    'leverage': 0.10              # 合约数据
}

# 综合热点评分
hotspot_score = Σ(weight_i × metric_i)
```

## API 使用

### Python API
```python
from skills.go_hotspot import HotspotEngine

# 初始化
hotspot = HotspotEngine()

# 分析热点
analysis = hotspot.analyze(
    coins=['BTC', 'ETH', 'PEPE', 'FLOKI'],
    timeframe='1h',
    period='7d'
)

# 获取热点排名
ranking = analysis.get_ranking()
print(f"热点排名: {ranking}")

# 获取热点信号
signal = analysis.get_signal('PEPE')
print(f"信号: {signal.action}")
print(f"置信度: {signal.confidence}")

# 获取热点流动图
flow = analysis.get_flow_map()
print(f"资金流向: {flow.direction}")

# 获取热点趋势
trend = analysis.get_trend('BTC')
print(f"BTC热点趋势: {trend}")
```

### 命令行
```bash
# 热点分析
go-hotspot analyze --coins PEPE,FLOKI,WIF --timeframe 1h

# 热点排名
go-hotspot ranking --tier meme --period 7d

# 热点轮动
go-hotspot rotate --from BTC --to altcoin

# 热点预测
go-hotspot predict PEPE --horizon 24h
```

## 文件结构
```
skills/go-hotspot/
├── SKILL.md            # 本文档
├── hotspot_engine.py    # 核心引擎
├── flow_models.py      # 资金流模型
├── rotate_models.py    # 轮动模型
└── cache/             # 缓存
```

---

**版本**: 1.0.0
**创建**: 2026-05-13
**作者**: OpenClaw AI Assistant
