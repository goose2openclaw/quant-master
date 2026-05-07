---
name: opc-go2se-relay
description: |
  GO2SE v6i 系统状态监控与 Telegram 中继技能。
  通过 OpenClaw 内置 Telegram 连接发送双引擎状态。
---

# GO2SE Telegram 中继技能

## API 端点
- v6a: http://localhost:8000/health
- v6i: http://localhost:8001/health  
- v6i performance: http://localhost:8001/api/performance

## 命令
/status go2se — 显示双引擎状态
/analyze go2se — 发送完整报告到 Telegram
