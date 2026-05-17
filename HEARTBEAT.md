# HEARTBEAT.md

## ⚠️ 核心指令
**G45 v1.3 全技能自主调度系统是主交易系统**

### 🌟 G45 全技能自主调度系统 v1.3

| 脚本 | 功能 | 优先级 |
|------|------|--------|
| skills/g45/g45.py | 全技能自主调度量化 (v1.3) | P0 |
| skills/g40/g40.py | 备用实盘交易 | P1 |

### G45 v1.3 核心功能
1. **MultiTimeframeAnalyzer** - 多时间框架分析 (5m/15m/1h/4h)
2. **SignalFusion** - 高级信号融合引擎
3. **StrategyOptimizer** - 策略组合优化 (9大策略)
4. **DynamicStopLoss** - 动态止盈止损

### 技能权重 (动态调整)
- go-core: 20%
- go-pool: 15%
- go-long-short: 15%
- go-detect: 12%
- go-rotate: 10%

### 风控参数
- 止损: 3%
- 止盈: 12%
- 移动止盈: 启用 (1.5%回调)
- Kelly: 15%
- 扫描间隔: 12s
- MTF权重: 30%

### 当前状态
- **G45 v1.3**: 就绪 (含MTF分析)
- **G40**: 实盘运行中
- **GitHub**: 待推送

### 持久化
- 日志文件: /home/goose/.openclaw/workspace/logs/g45.log

---
**最后更新**: 2026-05-17 23:00
**版本**: G45-v1.3 - 深度优化版
