# GO2SE v1.0 快速入门指南

## 系统概览

GO2SE (读作 "Goose") 🪿 是一款 AI 驱动的加密货币量化交易与投资平台。

---

## 快速开始

```bash
cd /root/.openclaw/workspace/skills/go2se/scripts
python3 dashboard.py
```

---

## 核心功能

### 🎯 交易策略 (7)
| 模块 | 命令 | 功能 |
|------|------|------|
| 主流币 | mainstream_strategy.py | 稳健长线 |
| 打地鼠 | mole_strategy.py | 短线套利 |
| 分层交易 | tiered_trading.py | 渐进建仓 |
| 声纳 Pro | sonar_pro_v3.py | 多因子信号 |
| 统一策略 | unified_strategy.py | 全市场 |
| 空投猎手 | airdrop_hunter.py | 新币监控 |
| Polymarket | polymarket_arb.py | 预测套利 |

### 📡 信号与扫描 (4)
| 模块 | 命令 |
|------|------|
| 实时预警 | realtime_alert.py |
| 趋势数据库 | trend_db.py |
| 高级信号 | advanced_signals.py |
| 竞品分析 | competitor_analyzer.py |

### 🛠️ 工具 (12)
| 模块 | 命令 |
|------|------|
| 仪表板 | dashboard.py |
| 风险管理 | risk_manager.py |
| 组合管理 | portfolio_manager.py |
| 交易日志 | trading_journal.py |
| 性能优化 | performance_optimizer.py |
| 回测引擎 | backtest_engine.py |
| 策略导入 | strategy_importer.py |
| 策略优化 | strategy_optimizer.py |
| 趋势更新 | trend_updater.py |
| 通知系统 | notification_system.py |
| Miro协作 | miro_integration.py |
| 反馈收集 | feedback_collector.py |

### 🏦 平台 (4)
| 模块 | 命令 |
|------|------|
| 微私募V2 | micro_pe_v2.py |
| 代币发行 | token_launch.py |
| 众包平台 | crowdsource_platform.py |
| 做市商联盟 | market_maker_alliance.py |

### 🌐 生态 (4)
| 模块 | 命令 |
|------|------|
| 多市场模拟 | market_simulator.py |
| 收益聚合 | yield_aggregator.py |
| 社区治理 | community_system.py |
| 合约生成 | contract_generator.py |

---

## 快捷命令

```bash
# 仪表板
python3 dashboard.py

# 空投扫描
python3 airdrop_hunter.py 5.0

# 高级信号
python3 advanced_signals.py

# 做市商联盟
python3 market_maker_alliance.py on   # 开启
python3 market_maker_alliance.py off  # 关闭

# 代币
python3 token_launch.py

# 微私募
python3 micro_pe_v2.py
```

---

## Cron 任务

| 任务 | 间隔 |
|------|------|
| mainstream | 30分钟 |
| mole | 15分钟 |
| unified | 15分钟 |
| airdrop | 30分钟 |
| pm-arbitrage | 30分钟 |
| trend-update | 1小时 |
| strategy-optimize | 12小时 |
| competitor-analysis | 24小时 |

---

## 风险控制

- 最大持仓: 5个
- 单日交易: 10笔
- 最大回撤: 10%
- 空投: 零Approval

---

## 文件结构

```
skills/go2se/
├── scripts/        (47个脚本)
├── defi/scripts/ (8个)
├── data/
└── *.md         (8个文档)
```

---

**版本**: 1.0 | **更新时间**: 2026-03-12
