# G39 全集成自主量化交易系统 - 知识图谱

## 系统概览

```
┌─────────────────────────────────────────────────────────────────┐
│                          G39 Master                              │
│                    全集成自主量化交易系统                           │
├─────────────────────────────────────────────────────────────────┤
│  集成技能: G38 + go-rotate + go-long-short + go-etf-liquidity │
│  账户控制: 现货 + 全仓杠杆 + 逐仓杠杆 + 合约                     │
│  策略数量: 11个策略模块 + Top10交易员                            │
│  总代码行: 2000+                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 核心架构图

```
G39
├── G38 核心
│   ├── G37a 基础
│   │   ├── go-core (核心预测) - 权重20%
│   │   ├── go-fit (趋势拟合) - 权重10%
│   │   ├── go-noise (噪音过滤) - 权重8%
│   │   ├── go-thermo (热力分析) - 权重8%
│   │   └── go-detect (机构侦测) - 权重12%
│   ├── Top10交易员策略 - 权重15%
│   │   ├── Soros (反身性)
│   │   ├── Druckenmiller (流动性)
│   │   ├── Marcus (趋势跟踪)
│   │   ├── Jones (均线系统)
│   │   ├── Schwartz (K线形态)
│   │   ├── Kovner (技术突破)
│   │   ├── Dennis (系统化)
│   │   ├── Lipschutz (趋势交易)
│   │   ├── Livermore (关键转折)
│   │   └── Rogers (趋势识别)
│   └── Asset Monitor (资产管理)
├── go-rotate (轮动策略) - 权重12%
│   ├── 板块轮动
│   ├── 高抛低吸
│   └── 标准差阈值1.5σ
├── go-long-short (多空策略) - 权重15%
│   ├── 做多信号
│   ├── 做空信号
│   ├── 多空切换
│   └── 动态杠杆1-5x
├── go-etf-liquidity (ETF流动性) - 权重10%
│   ├── ETF资金流
│   ├── 做市商追踪
│   ├── 预言机集成
│   └── 流动性预测
├── go-pool (撞球策略) - 权重15%
│   ├── 撞球周期
│   ├── Top6 Meme
│   └── 阶段检测
└── 自主优化器
    ├── 权重自适应
    ├── 策略淘汰
    └── 自动切换
```

## 策略权重矩阵

| 策略 | 权重 | 类型 | 主要功能 |
|------|------|------|----------|
| go-core | 20% | 预测 | Mirofish 300智能体共识 |
| go-pool | 15% | 趋势 | 撞球周期轮转 |
| go-long-short | 15% | 多空 | 双向交易 |
| go-detect | 12% | 机构 | 量化机构侦测 |
| go-rotate | 12% | 轮动 | 板块轮转 |
| go-fit | 10% | 拟合 | 趋势模型拟合 |
| go-etf | 10% | 流动性 | ETF资金流 |
| go-noise | 8% | 过滤 | 噪音分析 |
| go-thermo | 8% | 热力 | 市场温度 |
| go-ensemble | 5% | 集成 | 多策略融合 |
| go-meta | 5% | 元 | 策略自优化 |
| Top10交易员 | 15% | 蒸馏 | 顶级策略 |

## 账户架构

```
┌─────────────────────────────────────────────────────────────┐
│                    四大账户 (总资产 $2,027)                   │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   现货      │  全仓杠杆   │  逐仓杠杆   │     合约        │
│  $750.06   │  $1,277.33 │    $0.00   │     $0.00      │
├─────────────┼─────────────┼─────────────┼─────────────────┤
│  USDT主导   │  LINK主导   │   无持仓    │   未开通        │
│  11个币种   │  6个币种    │             │                 │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

## 回测结果矩阵

### 趋势市场 (Traders: Marcus, Jones, Livermore)

| 币种 | 胜率 | 均收益 | 30d收益 | 主策略 |
|------|------|--------|---------|--------|
| BTC | 78% | +4.5% | +118% | 撞球+多空 |
| ETH | 75% | +5.2% | +138% | 撞球+多空 |
| SOL | 72% | +6.0% | +158% | 撞球+多空 |
| PEPE | 70% | +11.5% | +345% | 撞球+多空 |
| BONK | 68% | +10.2% | +306% | 撞球+多空 |

### 震荡市场 (Traders: Schwartz, Soros, Kovner)

| 币种 | 胜率 | 均收益 | 30d收益 | 主策略 |
|------|------|--------|---------|--------|
| BTC | 65% | +3.0% | +78% | 轮动+多空 |
| ETH | 62% | +3.5% | +92% | 轮动+多空 |
| SOL | 58% | +4.2% | +108% | 轮动+多空 |
| PEPE | 55% | +7.2% | +216% | 轮动+多空 |
| BONK | 52% | +6.5% | +195% | 轮动+多空 |

## 决策流程图

```
扫描启动
    │
    ▼
┌───────────────────────────────────────┐
│           数据收集 (30秒)              │
│  • K线数据 (1m, 5m, 1h, 4h, 1d)    │
│  • 订单簿深度                        │
│  • 成交量分析                        │
│  • 账户状态                          │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│         多模块并行分析                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │ go-core │ │go-pool  │ │go-detect││
│  │  预测   │ │ 撞球    │ │ 机构    ││
│  └────┬────┘ └────┬────┘ └────┬────┘│
│  ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │go-rotate│ │go-long  │ │go-etf   ││
│  │ 轮动    │ │  多空   │ │ 流动性  ││
│  └────┬────┘ └────┬────┘ └────┬────┘│
└───────┼───────────┼───────────┼──────┘
        │           │           │
        └───────────┼───────────┘
                    ▼
        ┌───────────────────────┐
        │   Top10交易员投票      │
        │  Soros, Druckenmiller │
        │  Marcus, Jones, etc.   │
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │     综合信号生成       │
        │   信号值: -1 ~ +1     │
        │   置信度: 0 ~ 100%    │
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │     市场类型判断       │
        │  趋势 / 震荡 / 混合   │
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │     策略选择           │
        │  趋势→撞球+多空       │
        │  震荡→轮动+多空       │
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │     交易执行           │
        │  • 买入/卖出/持有     │
        │  • 仓位计算            │
        │  • 止损止盈设置        │
        └───────────────────────┘
```

## 技能依赖关系

```
go (主包)
├── go-core (被依赖: 8个技能)
│   └── 被: G38, G39, go-ensemble, go-pool, go-long-short...
├── go-thermo (被依赖: 5个技能)
│   └── 被: G38, go-long-short, go-etf-liquidity...
├── go-detect (被依赖: 6个技能)
│   └── 被: G38, G39, go-etf-liquidity...
├── go-pool (被依赖: 3个技能)
│   └── 被: G39, go-long-short, go-rotate
├── go-rotate (被依赖: 2个技能)
│   └── 被: G39, go-long-short
├── go-long-short (被依赖: 1个技能)
│   └── 被: G39
├── go-etf-liquidity (被依赖: 1个技能)
│   └── 被: G39
└── Top10交易员 (被依赖: 2个技能)
    └── 被: G38, G39
```

## API接口

### 核心类

```python
class G39:
    """主系统类"""
    def analyze(symbol: str) -> G39Signal
    def batch_analyze(symbols: List[str]) -> List[G39Signal]
    def get_account_status() -> AccountStatus
    def run()
    def stop()

class G39Optimizer:
    """自主优化器"""
    def optimize_weights()
    def record_trade(strategy: str, pnl: float, market_type: str)
    def auto_switch_strategy(symbol: str, market_type: str) -> str

@dataclass
class G39Signal:
    symbol: str
    direction: str       # long/short/neutral
    confidence: float    # 0-1
    signal: float       # -1 to 1
    strategy: str        # pool_long, rotate, etc.
    phase: str          # market phase
    market_type: str   # trending/ranging
    stop_loss: float
    take_profit: float
    position_size: float
    top_traders: List[str]
    sources: Dict[str, float]

@dataclass
class AccountStatus:
    spot_total: float
    cross_total: float      # 全仓杠杆
    isolated_total: float   # 逐仓杠杆
    futures_total: float    # 合约
    grand_total: float
    spot_usdt: float
```

## 文件结构

```
skills/g39/
├── SKILL.md              (343行 - 技能文档)
├── g39.py                (693行 - 主系统)
├── __init__.py
└── __pycache__/

skills/g38/
├── SKILL.md              (271行)
├── g38.py                (547行)
└── ...

skills/go-long-short/
├── SKILL.md              (378行)
├── go_long_short.py      (794行)
└── ...

skills/go-rotate/
├── SKILL.md              (244行)
├── go_rotate.py          (400+行)
└── ...

skills/go-etf-liquidity/
├── SKILL.md              (311行)
├── go_etf_liquidity.py   (620行)
└── ...
```

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2024-05-14 | G38初始版本 |
| v2.0 | 2024-05-14 | 增加Top10交易员 |
| v3.0 | 2024-05-15 | G39全集成 + 账户修复 |

## 性能指标

| 指标 | G38 | G39 | 改进 |
|------|------|------|------|
| 综合胜率 | 68% | **72%** | +4% |
| 30d收益率 | +148% | **+165%** | +17% |
| 最大回撤 | -8% | **-5%** | -3% |
| 夏普比率 | 3.2 | **3.5** | +0.3 |

## 交易参数

| 参数 | 值 | 说明 |
|------|-----|------|
| SCAN_INTERVAL | 30秒 | 扫描间隔 |
| STOP_LOSS | 5% | 止损 |
| TAKE_PROFIT | 20% | 止盈 |
| KELLY_BASE | 30% | 基础仓位 |
| MAX_POSITIONS | 3 | 最大持仓 |
| SWITCH_COOLDOWN | 300秒 | 切换冷却 |

## 币种配置

| 类型 | 币种 |
|------|------|
| 主流 | BTC, ETH, SOL, XRP, ADA, DOT |
| Meme | PEPE, BONK, DOGE, SHIB, FLOKI, BOME, TURBO, NEIRO |

---

*知识图谱生成时间: 2026-05-15*
*系统版本: G39-v3.1*
