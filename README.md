# QuantMaster - QMT + vnpy 融合量化平台 v4.0

## 概述
完全自主可控的加密货币量化交易平台，融合QMT快捷交易与vnpy量化框架。

## 完整模块矩阵 (26个)

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
| 11 | strategies/ | 4种策略 | ✅ |
| 12 | backtest/ | 回测引擎 | ✅ |
| 13 | api_server/ | REST+WebSocket | ✅ |
| 14 | factors/ | 技术因子 | ✅ |
| 15 | db/ | SQLite持久化 | ✅ |
| 16 | exchanges/ | 多交易所 | ✅ |
| 17 | optimizer/ | 网格+遗传优化 | ✅ |
| 18 | ml_factors/ | ML因子+预测 | ✅ |
| 19 | **futures/** | **合约+杠杆+止损** | ✅ v4.0 |
| 20 | **scheduler/** | **Cron调度器** | ✅ v4.0 |
| 21 | **paper_trading/** | **Paper模拟交易** | ✅ v4.0 |
| 22 | **risk/** | **VAR+止损+风控** | ✅ v4.0 |
| 23 | **onchain/** | **链上数据** | ✅ v4.0 |
| 24 | **news/** | **财经日历+新闻** | ✅ v4.0 |
| 25 | **sentiment/** | **社交情绪分析** | ✅ v4.0 |
| 26 | **arbitrage/** | **跨交易所套利** | ✅ v4.0 |
| 27 | **factor_research/** | **因子研究框架** | ✅ v4.0 |
| 28 | **pro_dashboard/** | **专业Dashboard** | ✅ v4.0 |
| 29 | **slippage/** | **成交质量分析** | ✅ v4.0 |
| 30 | **live_signals/** | **实时信号推送** | ✅ v4.0 |
| 31 | **automation/** | **信号自动执行** | ✅ v4.0 |

## v4.0 新增模块

### futures/ - 合约交易
```python
from futures import FuturesTrading
ft = FuturesTrading(api_key, api_secret, proxy)
ft.open_long('BTCUSDT', 0.1, leverage=10)
ft.set_stop_loss('BTCUSDT', 95000)
ft.set_take_profit('BTCUSDT', 120000)
ft.get_position('BTCUSDT')
```

### scheduler/ - Cron调度
```python
from scheduler import CronScheduler
scheduler = CronScheduler()
scheduler.add_interval('check_signal', check_signals, 60)
scheduler.add_daily('rebalance', rebalance, '10:00')
scheduler.start()
```

### paper_trading/ - Paper交易
```python
from paper_trading import PaperSimulator
sim = PaperSimulator(initial_balance=10000, commission=0.001)
sim.set_price('BTCUSDT', 100000)
sim.buy('BTCUSDT', 0.1)
result = sim.get_account()
```

### risk/ - 风控增强
```python
from risk import RiskManager, VaR, StopLoss
rm = RiskManager()
rm.set_stop('BTCUSDT', entry=100000, stop_loss_pct=2, take_profit_pct=6)
```

### onchain/ - 链上数据
```python
from onchain import OnChainData
oc = OnChainData(proxy)
oc.get_whale_transactions()
oc.get_funding_rate('BTC')
oc.get_liquidation_data('ETH')
```

### news/ - 新闻事件
```python
from news import EconomicCalendar, NewsMonitor
ec = EconomicCalendar()
ec.fetch_events()
ec.get_upcoming(hours=24)
```

### sentiment/ - 情绪分析
```python
from sentiment import SocialSentiment
ss = SocialSentiment()
ss.get_fear_greed_index()
ss.get_community_sentiment('BTC')
```

### arbitrage/ - 套利监控
```python
from arbitrage import ArbitrageMonitor
am = ArbitrageMonitor()
am.add_exchange('binance', binance_ex)
am.start()
am.triangular_arbitrage()
```

### factor_research/ - 因子研究
```python
from factor_research import FactorResearch
fr = FactorResearch()
fr.add_factor('momentum', 'momentum')
fr.backtest_factor('momentum', returns)
```

### pro_dashboard/ - 专业Dashboard
```python
from pro_dashboard import ProDashboard
dash = ProDashboard()
dash.update_data('equity', 100000)
html = dash.generate_html()
```

### live_signals/ - 实时信号
```python
from live_signals import SignalPublisher
pub = SignalPublisher()
pub.add_telegram(bot_token, chat_id)
pub.publish(signal)
```

### automation/ - 自动执行
```python
from automation import SignalExecutor, ExecutionRule
executor = SignalExecutor(order_manager, risk_manager)
executor.receive_signal(signal)
```

## 架构图

```
┌──────────────────────────────────────────────────────────────┐
│                      QuantMaster v4.0                         │
├──────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────┐ │
│  │ Web UI     │  │ Pro Dash   │  │ REST API   │  │ WS API  │ │
│  └────────────┘  └────────────┘  └────────────┘  └─────────┘ │
├──────────────────────────────────────────────────────────────┤
│  信号系统: live_signals → automation → order → execution      │
├──────────────────────────────────────────────────────────────┤
│  交易引擎                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 现货     │ │ 合约     │ │ Paper    │ │ 套利     │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
├──────────────────────────────────────────────────────────────┤
│  风控: risk + slippage + pro_dashboard                       │
├──────────────────────────────────────────────────────────────┤
│  数据: data + onchain + news + sentiment                     │
├──────────────────────────────────────────────────────────────┤
│  核心: core + db + scheduler + factor_research               │
└──────────────────────────────────────────────────────────────┘
```

## 快速开始

```python
from quant_master import QuantMaster

qm = QuantMaster()
qm.initialize(API_KEY, API_SECRET, PROXY)

# 现货交易
qm.send_order('BTCUSDT', 'BUY', 0.01)

# 合约交易
qm.futures.open_long('ETHUSDT', 1, leverage=5)

# Paper测试
qm.paper_trading.buy('BTCUSDT', 0.1)

# 调度任务
qm.scheduler.add_interval('check', some_func, 60)

# 风控
qm.risk.set_stop('BTCUSDT', entry=100000)

# 信号推送
qm.signals.publish(signal)

# 自动执行
qm.executor.receive_signal(signal)
```

## 许可证
MIT
