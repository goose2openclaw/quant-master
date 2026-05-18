# HEARTBEAT.md

## ⚠️ 核心指令
**G41 Polymarket增强版是主交易系统**

### 🌟 G41 v1.0 功能

| 组件 | 功能 |
|------|------|
| Polymarket预测 | 前5预测信号 |
| G40技术分析 | RSI/MA/MACD |
| 自动交易 | 市价单执行 |
| 4账户管理 | 现货/杠杆/合约 |

### 信号公式
```
综合信号 = G40技术 x 60% + Polymarket x 40%
```

### 交易决策
| 信号范围 | 行动 |
|----------|------|
| >0.2 | 买入 |
| <-0.1 | 卖出 |
| 其他 | 持有 |

### 启动命令
```bash
./start_g41.sh   # 启动
./stop_g41.sh    # 停止
./status_g41.sh  # 状态
```

### 日志
- /home/goose/.openclaw/workspace/logs/g41.log

### 状态
- **G41**: 运行中 (PID: 107591)
- **G40**: 已停用
- **Polymarket信号**: BTC+0.42, ETH+0.35, SOL+0.28

---
**最后更新**: 2026-05-18 09:38
**版本**: G41-v1.0 - Polymarket增强版
