# 已安装技能表格
生成时间: 2026-02-28 11:40

## 技能统计
- **总技能数**: 70
- **已安装**: 28 (40%)
- **缺失**: 42 (60%)

## 已安装技能列表

| 序号 | 技能名称 | 状态 | 描述 | 来源 |
|------|----------|------|------|------|
| 1 | clawhub | ✓ ready | Use the ClawHub CLI to search, install, update, and publish agent skills from clawhub.com | openclaw-workspace |
| 2 | discord | ✓ ready | 最小化 discord 技能（自动创建） | openclaw-workspace |
| 3 | healthcheck | ✓ ready | Host security hardening and risk-tolerance configuration for OpenClaw deployments | openclaw-workspace |
| 4 | notion | ✓ ready | 最小化 notion 技能（自动创建） | openclaw-workspace |
| 5 | obsidian | ✓ ready | Work with Obsidian vaults (plain Markdown notes) and automate via obsidian-cli | openclaw-workspace |
| 6 | skill-creator | ✓ ready | Create or update AgentSkills. Use when designing, structuring, or packaging skills | openclaw-workspace |
| 7 | tmux | ✓ ready | Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping pane output | openclaw-workspace |
| 8 | video-frames | ✓ ready | Extract frames or short clips from videos using ffmpeg | openclaw-workspace |
| 9 | weather | ✓ ready | Get current weather and forecasts via wttr.in or Open-Meteo | openclaw-workspace |
| 10 | speech-to-text | ✓ ready | Transcribe audio to text with Whisper models via inference.sh CLI | agents-skills-personal |
| 11 | whisper | ✓ ready | OpenAI's general-purpose speech recognition model. Supports 99 languages | agents-skills-personal |
| 12 | agent-browser | ✓ ready | 最小化 agent-browser 技能（自动创建） | openclaw-workspace |
| 13 | brave-search | ✓ ready | 最小化 brave-search 技能（自动创建） | openclaw-workspace |
| 14 | calendar | ✓ ready | Calendar management and scheduling. Create events, manage meetings, and sync across calendar providers | openclaw-workspace |
| 15 | docx | ✓ ready | 最小化 docx 技能（自动创建） | openclaw-workspace |
| 16 | find-skills | ✓ ready | Helps users discover and install agent skills when they ask questions like "how do I do X" | openclaw-workspace |
| 17 | frontend-design | ✓ ready | Create distinctive, production-grade frontend interfaces with high design quality | openclaw-workspace |
| 18 | gmail | ✓ ready | Gmail API integration with managed OAuth. Read, send, and manage emails, threads, labels, and drafts | openclaw-workspace |
| 19 | opc-crypto-monitor | ✓ ready | OPC项目自定义技能 - opc-crypto-monitor | openclaw-workspace |
| 20 | opc-job-assistant | ✓ ready | OPC项目自定义技能 - opc-job-assistant | openclaw-workspace |
| 21 | opc-smart-contract | ✓ ready | OPC项目自定义技能 - opc-smart-contract | openclaw-workspace |
| 22 | opc-trading-helper | ✓ ready | OPC项目自定义技能 - opc-trading-helper | openclaw-workspace |
| 23 | pdf | ✓ ready | 最小化 pdf 技能（自动创建） | openclaw-workspace |
| 24 | pptx | ✓ ready | 最小化 pptx 技能（自动创建） | openclaw-workspace |
| 25 | telegram | ✓ ready | OpenClaw skill for designing Telegram Bot API workflows and command-driven conversations | openclaw-workspace |
| 26 | web-fetch | ✓ ready | 最小化 web-fetch 技能（自动创建） | openclaw-workspace |
| 27 | whatsapp | ✓ ready | OPC项目专用WhatsApp集成 - 支持消息、模板、媒体、自动化通知 | openclaw-workspace |
| 28 | xlsx | ✓ ready | 最小化 xlsx 技能（自动创建） | openclaw-workspace |

## 技能分类

### 核心工具类
1. **clawhub** - 技能管理
2. **skill-creator** - 技能创建
3. **find-skills** - 技能发现

### 通信类
1. **discord** - Discord集成
2. **telegram** - Telegram集成
3. **whatsapp** - WhatsApp集成
4. **gmail** - 邮件管理

### 文档处理类
1. **docx** - Word文档
2. **pdf** - PDF文档
3. **pptx** - PowerPoint
4. **xlsx** - Excel表格

### 开发工具类
1. **frontend-design** - 前端设计
2. **tmux** - 终端管理
3. **agent-browser** - 浏览器控制

### 音频/视频处理类
1. **speech-to-text** - 语音转文字
2. **whisper** - 语音识别
3. **video-frames** - 视频处理

### 数据获取类
1. **weather** - 天气信息
2. **brave-search** - 网页搜索
3. **web-fetch** - 网页抓取
4. **calendar** - 日历管理

### OPC项目专用
1. **opc-crypto-monitor** - 加密货币监控
2. **opc-job-assistant** - 求职助手
3. **opc-smart-contract** - 智能合约
4. **opc-trading-helper** - 交易辅助

### 个人知识管理
1. **obsidian** - 笔记管理
2. **notion** - Notion集成

### 系统管理
1. **healthcheck** - 安全检查

## 建议安装的缺失技能

基于"搜索更多特定功能的技能"请求，建议搜索：

### 加密货币相关
- `crypto-ta-analyzer` - 技术分析
- `smart-contract-security` - 合约安全
- `defi-monitor` - DeFi监控

### 开发相关
- `github` - GitHub集成
- `docker` - 容器管理
- `kubernetes` - K8s管理

### 数据分析
- `data-analysis` - 数据分析
- `machine-learning` - 机器学习
- `visualization` - 数据可视化

### 自动化
- `workflow-automation` - 工作流自动化
- `cron-scheduler` - 定时任务
- `api-gateway` - API网关

## 下一步建议

1. **使用find-skills技能搜索**:
   ```bash
   # 搜索加密货币相关技能
   npx skills find crypto
   
   # 搜索开发相关技能
   npx skills find github docker
   
   # 搜索数据分析技能
   npx skills find data analysis
   ```

2. **安装感兴趣的新技能**:
   ```bash
   # 安装技能
   npx skills install <skill-name>
   ```

3. **配置已安装技能**:
   - 检查Telegram技能配置（当前有401错误）
   - 配置WhatsApp集成
   - 设置日历同步

4. **测试音频处理系统**:
   - 新的音频文件将自动处理
   - 转录结果保存在`transcriptions/`目录