---
name: go2se-deerflow
description: GO2SE团队CEO管理系统集成DeerFlow - 执行五条平行工作线。触发条件：团队管理、任务调度、系统监控、交易策略、市场分析。
---

# GO2SE CEO + DeerFlow 五条平行工作线

## 概述

GO2SE是专业Crypto量化AI投资平台，CEO通过DeerFlow编排多Agent执行五条平行工作线。

## 团队架构

| 组/技能 | 职责 | 任务 |
|---------|------|------|
| 技术组 | 代码开发 | 平台迭代开发、功能实现、算力优化 |
| 策略组 | 交易策略 | 信号扫描、风控、持仓管理 |
| 运营组 | 社交学习 | 外部资源、合作伙伴 |
| MiroFish | 团队技能 | 打破局限、发现真相、自主迭代 |

## 五条平行工作线

| 工作线 | 资源 | 任务 |
|--------|------|------|
| ① 系统健康 | 10% | 负总责、灵活调度、确保不当机 |
| ② 监控回复 | 5% | 主会话实时响应 |
| ③ 调度准备 | 10% | 每30分钟迭代 |
| ④ 执行工作 | 70% | 平台开发、功能实现 |
| ⑤ 社交学习 | 5% | 外部学习、合作伙伴 |

## DeerFlow集成

### 启动DeerFlow
```bash
cd /root/.openclaw/workspace/skills/deer-flow
docker compose up -d
# 或本地开发
cd backend && pip install -e . && cd ..
npm install && npm run dev
```

### 使用DeerFlow执行工作线
1. 打开 http://localhost:3000
2. 选择GO2SE CEO技能
3. 描述任务需求
4. DeerFlow编排多Agent协作执行

## 系统组件

| 组件 | 地址 | 功能 |
|------|------|------|
| GO2SE服务 | localhost:5000 | 策略管理、信号生成 |
| OpenClaw | localhost:18789 | AI Agent核心 |
| DeerFlow | localhost:3000 | 多Agent编排 |

## API端点

```bash
# 健康检查
curl http://localhost:5000/api/health

# 市场数据
curl http://localhost:5000/api/markets

# 信号聚合
curl http://localhost:5000/api/signals/aggregated

# 钱包优化
curl http://localhost:5000/api/wallet/optimize

# 风控
curl -X POST http://localhost:5000/api/risk/trailing \
  -H "Content-Type: application/json" \
  -d '{"coin":"BTC","entry_price":95000,"current_price":98500}'
```

## MiroFish预测市场

- 预测: /api/oracle/mirofish/predict
- 批量: /api/oracle/mirofish/batch
- 市场: /api/oracle/mirofish/markets

## 调度Cron

| 任务 | 频率 |
|------|------|
| GO2SE-CEO-管理 | 每30分钟 |
| GO2SE平台迭代 | 每30分钟 |
| 市场情报收集 | 每60分钟 |
| Capability-Evolver | 每2小时 |
