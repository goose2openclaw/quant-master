# QuantMaster - QMT + vnpy 融合量化平台 v3.1

## 概述
完全自主可控的加密货币量化交易平台，融合QMT快捷交易与vnpy量化框架。

## 完整模块矩阵

| # | 模块 | 功能 | 状态 |
|---|------|------|------|
| 1 | core/ | 核心引擎 (事件/交易/网关/风控) | ✅ |
| 2 | data/ | 数据源 (HTTP+**WebSocket实时行情**) | ✅ |
| 3 | portfolio/ | 持仓同步+资金管理 | ✅ |
| 4 | order/ | 订单管理 (生命周期+撤单+重试) | ✅ |
| 5 | monitor/ | 监控面板 (实时Dashboard) | ✅ |
| 6 | notification/ | 报警通知 (TG/邮件/Webhook) | ✅ |
| 7 | log_system/ | 日志系统 (交易记录+审计) | ✅ |
| 8 | permission/ | 权限管理 (多用户+角色) | ✅ |
| 9 | strategy_ide/ | 策略IDE (在线编辑) | ✅ |
| 10 | performance/ | 绩效分析 (归因+风险) | ✅ |
| 11 | **strategies/** | **策略实现 (RSI/MACD/Bollinger/Momentum)** | ✅ 新 |
| 12 | **backtest/** | **回测引擎 (事件驱动)** | ✅ 新 |
| 13 | **api_server/** | **REST+WebSocket API** | ✅ 新 |
| 14 | **factors/** | **技术因子库 (RSI/MACD/ATR/ADX等)** | ✅ 新 |
| 15 | alpha/ | Alpha策略 (vnpy) | ✅ |
| 16 | trader/ | 交易核心 (vnpy) | ✅ |
| 17 | chart/ | 图表 (vnpy) | ✅ |
| 18 | event/ | 事件驱动 (vnpy) | ✅ |
| 19 | rpc/ | 远程调用 (vnpy) | ✅ |

## v3.1 新增模块

### strategies/implementations/
- `rsi_strategy.py` - RSI均值回归策略
- `macd_strategy.py` - MACD趋势策略
- `bollinger_strategy.py` - 布林带策略
- `momentum_strategy.py` - 动量策略

### backtest/engine.py
- 事件驱动回测引擎
- 支持多策略
- 绩效统计 (胜率/回撤/夏普)

### api_server/
- `rest_api.py` - REST API (端口8091)
- `websocket_api.py` - WebSocket API (端口8092)

### factors/technical.py
- RSI, MACD, Bollinger Bands, EMA
- ATR, ADX, Stochastic, OBV, VWAP

### data/websocket_data.py
- Binance WebSocket实时行情
- Ticker/K线/深度订阅

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     QuantMaster v3.1                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Web UI   │  │ REST API │  │   WS API │  │StrategyIDE│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │              │             │              │          │
│  ┌────┴──────────────┴─────────────┴──────────────┴────┐   │
│  │              QuantMaster 统一系统                      │   │
│  │  trading_engine │ order_manager │ portfolio │ risk     │   │
│  └────────────────────────┬──────────────────────────────┘   │
│                           │                                  │
│  ┌────────────────────────┴──────────────────────────────┐ │
│  │  数据层                                                  │ │
│  │  data_source │ ws_client │ history_data │ factors       │ │
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

```python
from quant_master import QuantMaster, RSIStrategy, BacktestEngine

# 初始化
qm = QuantMaster()
qm.initialize(API_KEY, API_SECRET, PROXY)
qm.start()

# 交易
order = qm.send_order('BTCUSDT', 'BUY', 0.01)

# 回测
engine = BacktestEngine()
strategy = RSIStrategy('BTCUSDT')
qm.run_backtest(strategy, 'BTCUSDT', '2024-01-01', '2024-12-31')

# API服务
qm.run_api(8091)
```

## REST API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/status` | GET | 系统状态 |
| `/api/v1/positions` | GET | 持仓 |
| `/api/v1/orders` | GET/POST | 订单 |
| `/api/v1/orders/<id>` | DELETE | 取消订单 |
| `/api/v1/backtest` | POST | 回测 |
| `/api/v1/performance` | GET | 绩效 |
| `/api/v1/risk/status` | GET | 风控 |

## 策略列表

| 策略 | 原理 |
|------|------|
| RSI | RSI超卖买入, 超买卖出 |
| MACD | MACD金叉买入, 死叉卖出 |
| Bollinger | 价格触及下轨买入, 上轨卖出 |
| Momentum | 24h涨幅超阈值+RSI强势买入 |

## 自主升级
```bash
git remote add upstream https://github.com/vnpy/vnpy.git
git fetch upstream && git merge upstream/master
```

## 许可证
MIT
