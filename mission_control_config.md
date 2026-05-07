# OpenClaw Mission Control 配置指南

## 系统概述
Mission Control 是一个基于Kanban看板的多智能体任务管理系统，专为OpenClaw设计。

### 核心特性
- **Kanban看板**: 可视化任务管理界面
- **多智能体协作**: 团队领导 + 多个工作智能体
- **HTTP API**: RESTful API接口
- **本地存储**: JSON文件存储，无需外部数据库
- **心跳轮询**: 智能体通过心跳检查任务

## 安装步骤

### 1. 克隆Mission Control应用
```bash
cd /home/goose/.openclaw
git clone https://github.com/0xindiebruh/openclaw-mission-control.git mission-control-app
cd mission-control-app
```

### 2. 安装依赖
```bash
npm install
```

### 3. 启动服务器
```bash
npm run dev
```

### 4. 访问看板
打开浏览器访问: `http://localhost:8080`

## OPC项目智能体配置

### 智能体团队配置
```typescript
// lib/config.ts 或自定义配置文件
export const AGENT_CONFIG = {
  brand: {
    name: "OPC Mission Control",
    subtitle: "加密货币智能体指挥中心",
  },
  agents: [
    // 团队领导
    {
      id: "lead",
      name: "指挥中心",
      emoji: "🎯",
      role: "团队领导",
      focus: "任务分配、策略规划、进度监控",
    },
    // 加密货币监控智能体
    {
      id: "crypto-monitor",
      name: "加密货币监控",
      emoji: "📈",
      role: "市场监控",
      focus: "价格监控、趋势分析、交易信号",
    },
    // 智能合约开发智能体
    {
      id: "smart-contract",
      name: "智能合约",
      emoji: "📝",
      role: "合约开发",
      focus: "Solidity开发、安全审查、测试部署",
    },
    // 求职助手智能体
    {
      id: "job-assistant",
      name: "求职助手",
      emoji: "💼",
      role: "职业发展",
      focus: "职位搜索、简历优化、面试准备",
    },
    // 交易辅助智能体
    {
      id: "trading-helper",
      name: "交易辅助",
      emoji: "💰",
      role: "交易支持",
      focus: "策略回测、风险管理、组合优化",
    },
    // 前端开发智能体
    {
      id: "frontend-dev",
      name: "前端开发",
      emoji: "🎨",
      role: "界面设计",
      focus: "仪表板设计、用户体验、响应式布局",
    },
    // 数据分析智能体
    {
      id: "data-analyst",
      name: "数据分析",
      emoji: "📊",
      role: "数据分析",
      focus: "数据清洗、统计分析、可视化",
    },
    // 文档管理智能体
    {
      id: "document-manager",
      name: "文档管理",
      emoji: "📚",
      role: "文档维护",
      focus: "文档编写、知识管理、报告生成",
    },
  ],
};
```

### 任务类别配置
```typescript
export const TASK_CATEGORIES = [
  { id: "crypto", name: "加密货币", color: "bg-green-100 text-green-800" },
  { id: "contract", name: "智能合约", color: "bg-blue-100 text-blue-800" },
  { id: "job", name: "求职助手", color: "bg-purple-100 text-purple-800" },
  { id: "trading", name: "交易辅助", color: "bg-yellow-100 text-yellow-800" },
  { id: "frontend", name: "前端开发", color: "bg-pink-100 text-pink-800" },
  { id: "data", name: "数据分析", color: "bg-indigo-100 text-indigo-800" },
  { id: "document", name: "文档管理", color: "bg-gray-100 text-gray-800" },
  { id: "general", name: "通用任务", color: "bg-gray-100 text-gray-800" },
];
```

## OpenClaw配置

### 多会话配置 (~/.openclaw/config.json)
```json
{
  "sessions": {
    "list": [
      {
        "id": "main",
        "default": true,
        "name": "指挥中心",
        "workspace": "~/.openclaw/workspace"
      },
      {
        "id": "crypto-monitor",
        "name": "加密货币监控",
        "workspace": "~/.openclaw/workspace-crypto",
        "agentDir": "~/.openclaw/agents/crypto/agent",
        "heartbeat": {
          "every": "15m",
          "prompt": "Check Mission Control for crypto monitoring tasks at http://localhost:8080/api/tasks/agent/crypto-monitor"
        }
      },
      {
        "id": "smart-contract",
        "name": "智能合约",
        "workspace": "~/.openclaw/workspace-contract",
        "agentDir": "~/.openclaw/agents/contract/agent",
        "heartbeat": {
          "every": "30m",
          "prompt": "Check Mission Control for smart contract tasks at http://localhost:8080/api/tasks/agent/smart-contract"
        }
      },
      {
        "id": "job-assistant",
        "name": "求职助手",
        "workspace": "~/.openclaw/workspace-job",
        "agentDir": "~/.openclaw/agents/job/agent",
        "heartbeat": {
          "every": "1h",
          "prompt": "Check Mission Control for job search tasks at http://localhost:8080/api/tasks/agent/job-assistant"
        }
      },
      {
        "id": "trading-helper",
        "name": "交易辅助",
        "workspace": "~/.openclaw/workspace-trading",
        "agentDir": "~/.openclaw/agents/trading/agent",
        "heartbeat": {
          "every": "10m",
          "prompt": "Check Mission Control for trading tasks at http://localhost:8080/api/tasks/agent/trading-helper"
        }
      }
    ]
  }
}
```

## API使用指南

### 1. 初始化数据库
```bash
curl -X POST http://localhost:8080/api/seed
```

### 2. 创建任务
```bash
curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "监控比特币价格异常",
    "description": "监控比特币24小时价格波动，检测异常波动并生成报告",
    "category": "crypto",
    "priority": "high",
    "assignee": "crypto-monitor"
  }'
```

### 3. 智能体获取任务
```bash
# 加密货币监控智能体获取任务
curl http://localhost:8080/api/tasks/agent/crypto-monitor

# 智能合约智能体获取任务
curl http://localhost:8080/api/tasks/agent/smart-contract
```

### 4. 更新任务状态
```bash
curl -X PATCH http://localhost:8080/api/tasks/{taskId} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in-progress",
    "progress": "开始监控价格数据..."
  }'
```

### 5. 完成任务
```bash
curl -X PATCH http://localhost:8080/api/tasks/{taskId} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "done",
    "progress": "完成价格监控，发现3次异常波动",
    "result": "监控报告已生成：价格在14:30出现5%异常上涨"
  }'
```

## 心跳配置

### 智能体心跳配置
每个工作智能体需要配置心跳来轮询任务：

```json
{
  "heartbeat": {
    "every": "15m",
    "prompt": "Check Mission Control for tasks at http://localhost:8080/api/tasks/agent/{agent-id}"
  }
}
```

### 心跳工作流程
1. 智能体定期检查心跳
2. 调用Mission Control API获取任务
3. 如果有任务，开始执行
4. 更新任务状态和进度
5. 完成任务后标记为完成

## 任务示例

### 加密货币监控任务
```json
{
  "title": "每日加密货币市场报告",
  "description": "生成今日加密货币市场总结报告，包括：\n1. 前10大加密货币价格变化\n2. 交易量分析\n3. 市场情绪指标\n4. 异常波动检测",
  "category": "crypto",
  "priority": "medium",
  "assignee": "crypto-monitor",
  "estimatedHours": 2
}
```

### 智能合约开发任务
```json
{
  "title": "ERC-20代币合约安全审查",
  "description": "审查现有的ERC-20代币合约，检查：\n1. 重入攻击漏洞\n2. 整数溢出风险\n3. 权限控制问题\n4. Gas优化建议",
  "category": "contract",
  "priority": "high",
  "assignee": "smart-contract",
  "estimatedHours": 4
}
```

### 求职助手任务
```json
{
  "title": "区块链开发职位搜索",
  "description": "搜索最新的区块链开发职位，要求：\n1. 远程工作机会\n2. Solidity开发经验\n3. 年薪范围$80k-$150k\n4. 整理成Excel表格",
  "category": "job",
  "priority": "medium",
  "assignee": "job-assistant",
  "estimatedHours": 3
}
```

## 监控和管理

### 看板功能
1. **任务可视化**: 按状态、类别、优先级显示任务
2. **拖拽管理**: 拖拽任务改变状态
3. **过滤搜索**: 按智能体、类别、优先级过滤
4. **进度跟踪**: 实时显示任务进度

### 数据存储
- **位置**: `mission-control-app/data/`
- **文件**: `agents.json`, `tasks.json`, `logs.json`
- **备份**: 定期备份JSON文件

## 故障排除

### 常见问题
1. **服务器无法启动**: 检查端口8080是否被占用
2. **API无响应**: 检查服务器是否运行
3. **智能体无法获取任务**: 检查agent-id是否正确
4. **数据丢失**: 检查JSON文件权限和完整性

### 日志查看
```bash
# 查看服务器日志
cd /home/goose/.openclaw/mission-control-app
npm run dev 2>&1 | tee mission-control.log

# 查看API访问日志
tail -f data/logs.json
```

## 扩展和定制

### 添加新智能体
1. 在`AGENT_CONFIG`中添加新智能体
2. 在OpenClaw配置中添加新会话
3. 运行`curl -X POST http://localhost:8080/api/seed`更新数据库

### 自定义任务类别
1. 在`TASK_CATEGORIES`中添加新类别
2. 在前端界面中添加对应的颜色和图标

### 集成其他系统
1. **Webhook支持**: 添加webhook接收外部任务
2. **通知系统**: 集成Telegram/Email通知
3. **数据分析**: 导出任务数据进行分析

## 安全考虑

### 本地部署安全
1. **仅本地访问**: 默认绑定到localhost
2. **无认证**: 仅限本地网络访问
3. **数据加密**: 敏感数据可加密存储

### 生产环境建议
1. **添加认证**: 如果需要外部访问
2. **HTTPS**: 使用SSL证书
3. **防火墙**: 限制访问IP
4. **定期备份**: 备份JSON数据文件

## 性能优化

### 服务器优化
```javascript
// 在next.config.js中添加性能配置
module.exports = {
  reactStrictMode: true,
  swcMinify: true,
  compress: true,
};
```

### 数据库优化
1. **定期清理**: 删除已完成的老任务
2. **索引优化**: 为常用查询字段添加索引
3. **分页查询**: 大量任务时使用分页

## 总结

Mission Control为OpenClaw提供了完整的多智能体任务管理系统，特别适合OPC项目的复杂工作流管理。系统完全免费，基于本地存储，无需外部依赖。