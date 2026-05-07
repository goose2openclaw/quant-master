# XIAMI v4.0 快速入门指南

## 系统概览

XIAMI v4.0 是一个去中心化 AI 驱动的量化交易与 DeFi 生态系统。

### 核心模块

| # | 模块 | 命令 | 功能 |
|---|------|------|------|
| 1 | 主流币策略 | mainstream_strategy.py | BTC/ETH 稳健交易 |
| 2 | 打地鼠策略 | mole_strategy.py | 短线套利 |
| 3 | 分层交易 | tiered_trading.py | 渐进式建仓 |
| 4 | 声纳 Pro | sonar_pro_v3.py | 多因子信号 |
| 5 | 统一策略 | unified_strategy.py | 全市场覆盖 |
| 6 | 新币空投 | airdrop_hunter.py | 空投猎手 |
| 7 | Polymarket | polymarket_arb.py | 预测市场套利 |

### 快捷工具

| 命令 | 功能 |
|------|------|
| dashboard.py | 综合仪表板 |
| performance_optimizer.py | 性能分析 |
| backtest_engine.py | 回测引擎 |
| notification_system.py | 通知系统 |
| miro_integration.py | Miro 白板 |
| feedback_collector.py | 反馈收集 |

---

## 快速开始

```bash
cd /root/.openclaw/workspace/skills/xiami/scripts

# 查看仪表板
python3 dashboard.py

# 运行打地鼠
python3 mole_strategy.py

# 空投扫描
python3 airdrop_hunter.py 5.0

# 回测
python3 backtest_engine.py 10000 30 BTC

# 性能分析
python3 performance_optimizer.py 7
```

---

## Cron 任务 (8个)

| 任务 | 间隔 |
|------|------|
| mainstream | 30分钟 |
| mole | 15分钟 |
| unified | 15分钟 |
| tiered-trading | 30分钟 |
| airdrop-hunter | 30分钟 |
| pm-arbitrage | 30分钟 |

---

## 风险控制

- 最大持仓: 5个
- 单日交易: 10笔
- 最大回撤: 10%
- 新币: 零Approval

---

## 文件结构

```
scripts/
├── dashboard.py              # 仪表板
├── performance_optimizer.py  # 性能分析
├── backtest_engine.py       # 回测
├── notification_system.py   # 通知
├── airdrop_hunter.py       # 空投
├── mole_strategy.py        # 打地鼠
├── miro_integration.py     # Miro
└── ...
```

**版本**: 4.0 | **更新**: 2026-03-12
