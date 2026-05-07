# OpenClaw技能安装计划

## 已安装的技能（✓ ready）:
1. 📦 clawhub - 技能管理工具
2. 📦 healthcheck - 安全检查
3. 📦 skill-creator - 技能创建
4. 🧵 tmux - 远程控制tmux
5. 🌤️ weather - 天气查询
6. 📦 calendar - 日历管理 (workspace)
7. 📦 find-skills - 技能发现 (workspace)
8. 📦 gmail - Gmail集成 (workspace)
9. 📦 telegram - Telegram机器人 (workspace)
10. 📦 obsidian - Obsidian笔记 (workspace)

## 需要安装的技能分类:

### A. 开发相关（高优先级）
1. vercel-react-best-practices - React最佳实践
2. frontend-design - 前端设计
3. web-design-guidelines - 网页设计指南
4. webapp-testing - Web应用测试

### B. 办公文档（高优先级）
1. pptx - PowerPoint文档处理
2. pdf - PDF文档处理  
3. docx - Word文档处理
4. xlsx - Excel文档处理

### C. 通讯工具（中优先级）
1. whatsapp - WhatsApp集成（已有telegram）
2. github - GitHub操作

### D. 思维工具（中优先级）
1. reflection - 反思工具
2. executing-plan - 执行计划
3. brainstorming - 头脑风暴

### E. 其他工具（低优先级）
1. agent-browser - 浏览器控制
2. brave-search - Brave搜索
3. shell - Shell操作
4. cron - 定时任务
5. notion - Notion集成（已有）
6. nodes - 节点管理
7. twitter/x - Twitter/X集成
8. spotify - Spotify控制

## 安装策略:
1. 先安装开发相关技能（对OPC项目最重要）
2. 安装办公文档技能
3. 安装通讯工具
4. 其他技能根据需求逐步安装

## 安装命令参考:
```bash
# 搜索技能
clawhub search [技能名称]

# 安装技能（需要--force因为有些被标记为可疑）
clawhub install [技能slug] --force

# 查看已安装技能
openclaw skills list | grep "✓ ready"
```