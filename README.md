# QuantMaster - QMT + vnpy 融合系统

## 概述
完全自主可控的加密货币量化投资平台，融合QMT快捷交易与vnpy量化框架。

## 完整模块矩阵

| 模块 | 功能 | 状态 |
|------|------|------|
| core/ | 核心引擎 (事件/交易/网关/风控) | ✅ |
| data/ | 数据源 (实时行情+历史K线) | ✅ |
| portfolio/ | 持仓同步+资金管理 | ✅ |
| order/ | 订单管理 (生命周期+撤单+重试) | ✅ |
| monitor/ | 监控面板 (实时Dashboard) | ✅ |
| notification/ | 报警通知 (TG/邮件/Webhook) | ✅ |
| log_system/ | 日志系统 (交易记录+审计) | ✅ |
| permission/ | 权限管理 (多用户+角色) | ✅ |
| strategy_ide/ | 策略IDE (在线编辑) | ✅ |
| performance/ | 绩效分析 (归因+风险) | ✅ |
| alpha/ | Alpha策略 (vnpy) | ✅ |
| trader/ | 交易核心 (vnpy) | ✅ |
| chart/ | 图表 (vnpy) | ✅ |
| event/ | 事件驱动 (vnpy) | ✅ |
| rpc/ | 远程调用 (vnpy) | ✅ |

## 架构图

```
┌─────────────────────────────────────────────────────┐
│                  QuantMaster                        │
├─────────────────────────────────────────────────────┤
│  Web UI (Flask)  │  Dashboard  │  Strategy IDE     │
├─────────────────────────────────────────────────────┤
│  通知系统  │  日志系统  │  权限系统  │  绩效分析  │
├─────────────────────────────────────────────────────┤
│  订单管理  │  持仓管理  │  资金管理  │  风控      │
├─────────────────────────────────────────────────────┤
│  数据源 (实时+历史)  │  网关 (Binance等)           │
├─────────────────────────────────────────────────────┤
│  core: EventEngine │ TradingEngine │ RiskEngine     │
└─────────────────────────────────────────────────────┘
```

## 功能对照

| 功能 | QMT | vnpy | QuantMaster |
|------|-----|------|-------------|
| 快捷交易 | ✅ | - | ✅ |
| 篮子交易 | ✅ | - | ✅ |
| 风控规则 | ✅ | - | ✅ |
| 事件驱动 | - | ✅ | ✅ |
| Alpha研究 | - | ✅ | ✅ |
| CTA回测 | - | ✅ | ✅ |
| 图表 | - | ✅ | ✅ |
| 实时行情 | - | - | ✅ |
| 持仓同步 | - | - | ✅ |
| 订单管理 | - | - | ✅ |
| 多账号 | - | - | ✅ |
| Dashboard | - | - | ✅ |
| 报警通知 | ✅ | - | ✅ |
| 策略IDE | ✅ | - | ✅ |
| 绩效分析 | 部分 | - | ✅ |
| 权限管理 | ✅ | - | ✅ |

## 快速开始

```python
from core import TradingEngine, EventEngine
from data import DataSource
from portfolio import PortfolioManager

# 初始化
ds = DataSource(proxy)
ds.start()

pm = PortfolioManager()
pm.add_account('main', api_key, api_secret)
pm.set_data_source(ds)
pm.start_sync()

engine = TradingEngine(event_engine)
engine.set_gateway(binance_gateway)
```

## 自主升级
```bash
git remote add upstream https://github.com/vnpy/vnpy.git
git fetch upstream && git merge upstream/master
```

## 许可证
MIT
