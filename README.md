# QuantMaster - QMT + vnpy 融合量化平台 v4.1

## 概述
完全自主可控的加密货币量化交易平台，融合QMT快捷交易与vnpy量化框架。

## 完整模块矩阵 (35个)

| # | 模块 | 功能 | 状态 |
|---|------|------|------|
| 1 | core/ | 核心引擎 | ✅ |
| 2 | data/ | HTTP+WebSocket数据 | ✅ |
| 3 | portfolio/ | 持仓同步+资金管理 | ✅ |
| 4 | order/ | 订单管理 | ✅ |
| 5 | monitor/ | 基础监控 | ✅ |
| 6 | notification/ | 报警通知 | ✅ |
| 7 | log_system/ | 日志系统 | ✅ |
| 8 | permission/ | 权限管理 | ✅ |
| 9 | strategy_ide/ | 策略IDE | ✅ |
| 10 | performance/ | 绩效分析 | ✅ |
| 11 | **strategies/** | **18种策略** | ✅ v4.1 |
| 12 | backtest/ | 回测引擎 | ✅ |
| 13 | api_server/ | REST+WebSocket | ✅ |
| 14 | factors/ | 技术因子 | ✅ |
| 15 | db/ | SQLite持久化 | ✅ |
| 16 | exchanges/ | 多交易所 | ✅ |
| 17 | optimizer/ | 网格+遗传优化 | ✅ |
| 18 | ml_factors/ | ML因子+预测 | ✅ |
| 19 | futures/ | 合约交易 | ✅ v4.0 |
| 20 | scheduler/ | Cron调度器 | ✅ v4.0 |
| 21 | paper_trading/ | Paper模拟交易 | ✅ v4.0 |
| 22 | risk/ | VAR+止损风控 | ✅ v4.0 |
| 23 | onchain/ | 链上数据 | ✅ v4.0 |
| 24 | news/ | 财经日历+新闻 | ✅ v4.0 |
| 25 | sentiment/ | 社交情绪 | ✅ v4.0 |
| 26 | arbitrage/ | 跨交易所套利 | ✅ v4.0 |
| 27 | factor_research/ | 因子研究框架 | ✅ v4.0 |
| 28 | pro_dashboard/ | 专业Dashboard | ✅ v4.0 |
| 29 | slippage/ | 成交质量分析 | ✅ v4.0 |
| 30 | live_signals/ | 实时信号推送 | ✅ v4.0 |
| 31 | automation/ | 信号自动执行 | ✅ v4.0 |
| 32 | **chart/** | **实时TradingView图表** | ✅ v4.1 |

## v4.1 新增

### 18种交易策略
1. RSI均值回归
2. MACD趋势
3. Bollinger Bands布林带
4. Momentum动量
5. **Grid网格交易**
6. **Martingale马丁**
7. **DCA定投**
8. **Scalping剥头皮**
9. **Swing波段**
10. **Breakout突破**
11. **MeanReversion均值回归**
12. **TrendFollowing趋势跟随**
13. **PairTrading配对交易**
14. **Ichimoku云图**
15. **VWAP成交量加权**
16. **VolatilityBreakout波动率突破**
17. **Fibonacci斐波那契**
18. **Turtle海龟**

### TradingView图表
```python
from chart import TradingViewChart, ChartServer

chart = TradingViewChart('BTCUSDT')
chart.add_candle(CandleData(time, open, high, low, close, volume))

server = ChartServer(chart, port=8095)
server.run()  # 访问 http://localhost:8095
```

## 功能对照表

| 类别 | 功能 | 完整度 | 状态 |
|------|------|--------|------|
| 现货交易 | 快捷/篮子/市价/限价 | ✅ 100% | 完成 |
| 合约交易 | 永续/杠杆/止损止盈 | ✅ 100% | 完成 |
| 数据 | HTTP+WS实时+历史 | ✅ 90% | 完成 |
| 链上数据 | 巨鲸/资金费率/强平 | ✅ 80% | 完成 |
| 新闻事件 | 财经日历/新闻/情绪 | ✅ 80% | 完成 |
| 策略 | 18种策略 | ✅ 100% | 完成 |
| 回测 | 事件驱动回测 | ✅ 100% | 完成 |
| 参数优化 | 网格+遗传算法 | ✅ 100% | 完成 |
| 风控 | VAR/止损/风险敞口 | ✅ 100% | 完成 |
| 图表 | **实时TradingView** | ✅ 100% | **新增** |
| 通知 | TG/邮件/Webhook/信号 | ✅ 100% | 完成 |
| 多账号 | 跨交易所管理 | ✅ 100% | 完成 |
| 跨交易所对冲 | 套利监控 | ✅ 100% | 完成 |
| 调度 | Cron定时任务 | ✅ 100% | 完成 |
| Paper交易 | 模拟盘 | ✅ 100% | 完成 |

## 快速开始

```python
from quant_master import QuantMaster

qm = QuantMaster()
qm.initialize(API_KEY, API_SECRET, PROXY)
qm.start()

# 交易
qm.send_order('BTCUSDT', 'BUY', 0.01)

# 合约
qm.futures.open_long('ETHUSDT', 1, leverage=5)

# 策略
from strategies import RSIStrategy, GridStrategy
strategy = GridStrategy('BTCUSDT', grid_num=10)

# 图表
qm.chart_server.run()

# 调度
qm.scheduler.add_interval('check', check_func, 60)
```

## 架构

```
┌──────────────────────────────────────────────────────────────┐
│                      QuantMaster v4.1                         │
├──────────────────────────────────────────────────────────────┤
│  18 Strategies: RSI|MACD|BB|Momentum|Grid|Martingale|DCA   │
│  Scalping|Swing|Breakout|MeanRev|Trend|Pair|Ichimoku|VWAP │
│  VolBreakout|Fibonacci|Turtle                               │
├──────────────────────────────────────────────────────────────┤
│  TradingView实时图表 | Pro Dashboard | Web UI | REST API     │
├──────────────────────────────────────────────────────────────┤
│  Signal → Automation → Order → Execution → Risk             │
├──────────────────────────────────────────────────────────────┤
│  Spot | Futures | Paper | Arbitrage | Multi-Exchange         │
├──────────────────────────────────────────────────────────────┤
│  Data + OnChain + News + Sentiment + Factors + ML            │
├──────────────────────────────────────────────────────────────┤
│  Core: Event Engine | SQLite DB | Scheduler | Optimizer      │
└──────────────────────────────────────────────────────────────┘
```

## 许可证
MIT
