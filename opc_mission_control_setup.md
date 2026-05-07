# OPC Mission Control 快速设置指南

## 🎯 系统概述
一个完全免费的多智能体任务管理系统，专为OPC项目设计。

### 核心优势
- ✅ **完全免费** - 无任何费用
- ✅ **本地运行** - 无需外部服务
- ✅ **开源代码** - 可自由修改
- ✅ **无需Codex付费** - 使用本地智能体

## 🚀 快速启动

### 1. 启动Mission Control服务器
```bash
# 运行启动脚本
bash /home/goose/.openclaw/workspace/scripts/start_mission_control.sh
```

### 2. 访问看板
打开浏览器: `http://localhost:8080`

### 3. 初始化数据库
```bash
# 在新的终端中运行
curl -X POST http://localhost:8080/api/seed
```

## 🤖 OPC智能体团队

### 已配置的智能体
| 智能体ID | 名称 | 角色 | 专注领域 |
|---------|------|------|----------|
| `lead` | 指挥中心 | 团队领导 | 任务分配、策略规划 |
| `crypto-monitor` | 加密货币监控 | 市场监控 | 价格分析、趋势检测 |
| `smart-contract` | 智能合约 | 合约开发 | Solidity、安全审查 |
| `job-assistant` | 求职助手 | 职业发展 | 职位搜索、简历优化 |
| `trading-helper` | 交易辅助 | 交易支持 | 策略回测、风险管理 |
| `frontend-dev` | 前端开发 | 界面设计 | 仪表板、用户体验 |
| `data-analyst` | 数据分析 | 数据分析 | 数据清洗、可视化 |
| `document-manager` | 文档管理 | 文档维护 | 文档编写、知识管理 |

## 📋 任务管理

### 创建加密货币监控任务
```bash
curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "监控比特币价格异常",
    "description": "监控比特币24小时价格波动，检测异常波动",
    "category": "crypto",
    "priority": "high",
    "assignee": "crypto-monitor"
  }'
```

### 创建智能合约开发任务
```bash
curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "ERC-20代币合约安全审查",
    "description": "审查ERC-20合约的安全漏洞",
    "category": "contract",
    "priority": "high",
    "assignee": "smart-contract"
  }'
```

## 🔧 智能体集成

### 智能体心跳配置
每个智能体可以配置心跳来检查任务：

```json
{
  "heartbeat": {
    "every": "15m",
    "prompt": "Check Mission Control for tasks: http://localhost:8080/api/tasks/agent/{agent-id}"
  }
}
```

### 手动触发智能体检查
```bash
# 加密货币监控智能体检查任务
curl http://localhost:8080/api/tasks/agent/crypto-monitor

# 智能合约智能体检查任务
curl http://localhost:8080/api/tasks/agent/smart-contract
```

## 🎨 看板功能

### 可视化界面
1. **任务卡片** - 显示任务详情、状态、优先级
2. **拖拽操作** - 拖拽任务改变状态
3. **过滤搜索** - 按智能体、类别、状态过滤
4. **进度跟踪** - 实时显示任务进度

### 任务状态流程
```
待办 → 待处理 → 进行中 → 审核中 → 已完成
```

## 💾 数据存储

### 本地JSON文件
- `mission-control-app/data/agents.json` - 智能体数据
- `mission-control-app/data/tasks.json` - 任务数据
- `mission-control-app/data/logs.json` - 操作日志

### 数据备份
```bash
# 备份任务数据
cp /home/goose/.openclaw/mission-control-app/data/tasks.json /home/goose/.openclaw/backup/tasks-$(date +%Y%m%d).json
```

## 🔍 监控和调试

### 查看服务器日志
```bash
# 实时查看日志
tail -f /home/goose/.openclaw/mission-control-app/logs/mission-control-*.log
```

### 检查API状态
```bash
# 检查服务器健康状态
curl http://localhost:8080/api/health

# 查看所有任务
curl http://localhost:8080/api/tasks
```

## 🛠️ 故障排除

### 常见问题
1. **端口冲突** - 修改`package.json`中的端口号
2. **依赖问题** - 删除`node_modules`重新安装
3. **数据损坏** - 从备份恢复JSON文件

### 重启服务
```bash
# 停止服务
pkill -f "next"

# 重新启动
cd /home/goose/.openclaw/mission-control-app
npm run dev
```

## 📈 扩展功能

### 自定义智能体
1. 修改`mission-control-app/lib/config.ts`
2. 添加新的智能体配置
3. 重新运行`curl -X POST http://localhost:8080/api/seed`

### 任务模板
创建常用任务模板：
```bash
# 加密货币日报模板
curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "加密货币日报 - $(date +%Y-%m-%d)",
    "description": "生成今日加密货币市场报告",
    "category": "crypto",
    "priority": "medium",
    "assignee": "crypto-monitor",
    "template": true
  }'
```

## 🎯 最佳实践

### 任务分配建议
1. **紧急任务** - 分配给专用智能体，设置高优先级
2. **日常任务** - 设置定期心跳检查
3. **复杂任务** - 分解为多个子任务
4. **协作任务** - 多个智能体协同完成

### 性能优化
1. **定期清理** - 删除已完成的老任务
2. **任务分页** - 大量任务时使用分页查询
3. **缓存优化** - 频繁查询的数据可以缓存

## 📚 相关资源

### 文档
- `mission_control_config.md` - 完整配置指南
- `SKILL.md` - Mission Control技能文档
- GitHub仓库: https://github.com/0xindiebruh/openclaw-mission-control

### 技能
- `openclaw-mission-control` - 已安装的技能
- 位置: `~/.openclaw/workspace/.agents/skills/openclaw-mission-control`

## 🏁 开始使用

### 第一步：启动服务
```bash
bash /home/goose/.openclaw/workspace/scripts/start_mission_control.sh
```

### 第二步：初始化
```bash
curl -X POST http://localhost:8080/api/seed
```

### 第三步：创建任务
使用上面的curl命令创建OPC项目任务

### 第四步：智能体执行
配置智能体心跳或手动触发任务执行

---

**🎉 恭喜！你现在拥有一个完全免费、功能完整的OpenClaw Mission Control系统！**