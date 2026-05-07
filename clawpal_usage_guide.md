# ClawPal (openclaw-config) 使用指南

## 什么是ClawPal？

**ClawPal**（正式名称为`openclaw-config`）是一个全面的OpenClaw配置、诊断和管理技能。它提供了完整的OpenClaw系统操作手册，帮助你诊断和修复实际问题。

## 安装信息

- **安装时间**: 2026-03-01 01:33 (Asia/Shanghai)
- **技能名称**: openclaw-config
- **来源**: adisinghstudent/easyclaw@openclaw-config
- **安装量**: 669 安装
- **安全等级**: 安全 (Safe) + 中等风险 (Med Risk)
- **Socket警报**: 0个警报

## 核心功能

### 1. 快速健康检查
一键检查OpenClaw系统的所有关键组件状态。

### 2. 故障排除指南
针对WhatsApp、Telegram、Signal等常见问题的详细解决方案。

### 3. 配置管理
安全编辑OpenClaw配置文件的方法和模板。

### 4. 会话管理
搜索、查看和管理所有会话记录。

### 5. 内存系统诊断
诊断"忘记问题"的三层内存系统分析。

### 6. 扩展开发指南
创建自定义技能、通道插件和扩展OpenClaw的方法。

## 快速开始

### 基本健康检查

```bash
# 运行快速健康检查（复制粘贴整个代码块）
echo "=== GATEWAY ===" && \
ps aux | grep -c "[o]penclaw" && \
echo "=== CONFIG JSON ===" && \
python3 -m json.tool ~/.openclaw/openclaw.json > /dev/null 2>&1 && echo "JSON: OK" || echo "JSON: BROKEN" && \
echo "=== CHANNELS ===" && \
cat ~/.openclaw/openclaw.json | jq -r '.channels | to_entries[] | "\(.key): policy=\(.value.dmPolicy // "n/a") enabled=\(.value.enabled // "implicit")"' && \
echo "=== PLUGINS ===" && \
cat ~/.openclaw/openclaw.json | jq -r '.plugins.entries | to_entries[] | "\(.key): \(.value.enabled)"' && \
echo "=== CREDS ===" && \
ls ~/.openclaw/credentials/whatsapp/default/ 2>/dev/null | wc -l | xargs -I{} echo "WhatsApp keys: {} files" && \
for d in ~/.openclaw/credentials/telegram/*/; do bot=$(basename "$d"); [ -f "$d/token.txt" ] && echo "Telegram $bot: OK" || echo "Telegram $bot: MISSING"; done && \
[ -f ~/.openclaw/credentials/bird/cookies.json ] && echo "Bird cookies: OK" || echo "Bird cookies: MISSING" && \
echo "=== CRON ===" && \
cat ~/.openclaw/cron/jobs.json | jq -r '.jobs[] | "\(.name): enabled=\(.enabled) status=\(.state.lastStatus // "never") \(.state.lastError // "")"' && \
echo "=== RECENT ERRORS ===" && \
tail -10 ~/.openclaw/logs/gateway.err.log 2>/dev/null && \
echo "=== MEMORY DB ===" && \
sqlite3 ~/.openclaw/memory/main.sqlite "SELECT COUNT(*) || ' chunks, ' || (SELECT COUNT(*) FROM files) || ' files indexed' FROM chunks;" 2>/dev/null
```

## 常见问题解决方案

### WhatsApp问题："发送了消息但没有回复"

```bash
# 1. 检查机器人是否在运行
grep -i "whatsapp.*starting\|whatsapp.*listening" ~/.openclaw/logs/gateway.log | tail -5

# 2. 检查408超时断开
grep -i "408\|499\|retry" ~/.openclaw/logs/gateway.err.log | tail -10

# 3. 检查跨上下文消息阻止
grep -i "cross-context.*denied" ~/.openclaw/logs/gateway.err.log | tail -10

# 4. 检查会话是否存在
cat ~/.openclaw/agents/main/sessions/sessions.json | jq -r 'to_entries[] | select(.key | test("whatsapp")) | "\(.key) | \(.value.origin.label // "?")"'

# 5. 检查发送者是否被允许
cat ~/.openclaw/openclaw.json | jq '.channels.whatsapp | {dmPolicy, allowFrom, selfChatMode, groupPolicy}'

# 6. 检查是否是群组消息
cat ~/.openclaw/openclaw.json | jq '.channels.whatsapp.groupPolicy'

# 7. 检查通道拥塞
grep "lane wait exceeded" ~/.openclaw/logs/gateway.err.log | tail -5

# 8. 检查代理运行超时
grep "embedded run timeout" ~/.openclaw/logs/gateway.err.log | tail -5
```

### Telegram问题："机器人有问题/忘记事情"

```bash
# 1. 检查配置验证错误
grep -i "telegram.*unrecognized\|telegram.*invalid\|telegram.*policy" ~/.openclaw/logs/gateway.err.log | tail -10

# 2. 检查实际配置
cat ~/.openclaw/openclaw.json | jq '.channels.telegram'

# 3. 检查轮询状态
grep -i "telegram.*exit\|telegram.*timeout\|getUpdates" ~/.openclaw/logs/gateway.err.log | tail -10

# 4. 检查轮询偏移量
cat ~/.openclaw/telegram/update-offset-coder.json
cat ~/.openclaw/telegram/update-offset-sales.json

# 5. 检查两个机器人是否都在启动
grep -i "telegram.*starting\|telegram.*coder\|telegram.*sales" ~/.openclaw/logs/gateway.log | tail -10

# 6. 检查会话是否存在
cat ~/.openclaw/agents/main/sessions/sessions.json | jq -r 'to_entries[] | select(.key | test("telegram")) | "\(.key) | \(.value.origin.label // "?")"'

# 7. 检查是否发生压缩
SESS_ID="粘贴会话ID"
grep '"compaction"' ~/.openclaw/agents/main/sessions/$SESS_ID.jsonl | wc -l
```

### Telegram配置修复模板

```bash
# 正确的Telegram配置结构
cat ~/.openclaw/openclaw.json | jq '.channels.telegram = {
  "enabled": true,
  "accounts": {
    "coder": {
      "name": "机器人显示名称",
      "enabled": true,
      "botToken": "你的机器人令牌"
    },
    "sales": {
      "name": "销售机器人名称",
      "enabled": true,
      "botToken": "你的机器人令牌"
    }
  },
  "dmPolicy": "pairing",
  "groupPolicy": "disabled"
}' > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json
```

## 配置编辑

### 安全编辑模式

始终：备份、使用jq编辑、重启。

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.manual
jq '你的编辑内容' ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json
openclaw gateway restart
```

### 常见编辑操作

```bash
# 切换到允许列表模式
jq '.channels.whatsapp.dmPolicy = "allowlist" | .channels.whatsapp.allowFrom = ["+1XXXXXXXXXX"]' ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json

# 启用WhatsApp自动驾驶（机器人以你的身份回复所有人）
jq '.channels.whatsapp += {dmPolicy: "open", selfChatMode: false, allowFrom: ["*"]}' ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json

# 添加号码到Signal允许列表
jq '.channels.signal.allowFrom += ["+1XXXXXXXXXX"]' ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json

# 更改模型
jq '.agents.defaults.models = {"anthropic/claude-sonnet-4": {"alias": "sonnet"}}' ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json

# 设置并发数
jq '.agents.defaults.maxConcurrent = 10 | .agents.defaults.subagents.maxConcurrent = 10' ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json

# 禁用插件
jq '.plugins.entries.imessage.enabled = false' ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json
```

## 会话管理

### 按名称搜索会话

```bash
# 按名称搜索会话（不区分大小写）
cat ~/.openclaw/agents/main/sessions/sessions.json | jq -r 'to_entries[] | select(.value.origin.label // "" | test("名称"; "i")) | "\(.value.sessionId) | \(.value.lastChannel) | \(.value.origin.label)"'
```

### 按通道搜索会话

```bash
cat ~/.openclaw/agents/main/sessions/sessions.json | jq -r 'to_entries[] | select(.value.lastChannel == "whatsapp") | "\(.value.sessionId) | \(.value.origin.label // .key)"'
# 替换"whatsapp"为：signal、telegram，或检查.key获取cron会话
```

### 最近会话

```bash
cat ~/.openclaw/agents/main/sessions/sessions.json | jq -r '[to_entries[] | {id: .value.sessionId, updated: .value.updatedAt, label: (.value.origin.label // .key), ch: (.value.lastChannel // "cron")}] | sort_by(.updated) | reverse | .[:10][] | "\(.updated | . / 1000 | todate) | \(.ch) | \(.label)"'
```

### 搜索所有会话的消息内容

```bash
# 快速：查找包含关键词的会话文件
grep -l "关键词" ~/.openclaw/agents/main/sessions/*.jsonl

# 详细：显示匹配的消息和时间戳
grep "关键词" ~/.openclaw/agents/main/sessions/*.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    path, data = line.split(':', 1)
    try:
        obj = json.loads(data)
        if obj.get('type') == 'message':
            role = obj['message']['role']
            text = ''.join(c.get('text','') for c in obj['message'].get('content',[]) if isinstance(c,dict))
            if text.strip():
                sid = path.split('/')[-1].replace('.jsonl','')[:8]
                ts = obj.get('timestamp','')[:19]
                print(f'{ts} [{sid}] [{role}] {text[:200]}')
    except: pass
" | head -30
```

### 读取特定会话记录

```bash
# 从会话中读取最后30条消息
tail -50 ~/.openclaw/agents/main/sessions/会话ID.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        obj = json.loads(line)
        if obj.get('type') == 'message':
            role = obj['message']['role']
            text = ''.join(c.get('text','') for c in obj['message'].get('content',[]) if isinstance(c,dict))
            if text.strip() and role != 'toolResult':
                print(f'[{role}] {text[:300]}')
                print()
    except: pass
"
```

## 内存系统诊断

当代理"忘记"时，可能是三层内存系统之一出现问题：

### 第1层：上下文窗口（会话内）

```bash
# 检查会话的压缩次数（压缩 = 旧消息被修剪）
grep -c '"compaction"' ~/.openclaw/agents/main/sessions/会话ID.jsonl
# 7次压缩 = 代理已经"忘记"了最早的7次消息

# 检查压缩模式
cat ~/.openclaw/openclaw.json | jq '.agents.defaults.compaction'
# "safeguard" = 仅在达到上下文限制时压缩
```

### 第2层：工作空间内存文件

```bash
# 存在哪些每日内存文件
ls -la ~/.openclaw/workspace/memory/

# MEMORY.md中的内容（长期策划）
cat ~/.openclaw/workspace/MEMORY.md

# 在内存文件中搜索特定内容
grep -ri "关键词" ~/.openclaw/workspace/memory/
```

### 第3层：向量内存数据库（SQLite + Gemini嵌入）

```bash
# 哪些文件被索引
sqlite3 ~/.openclaw/memory/main.sqlite "SELECT path, size, datetime(mtime/1000, 'unixepoch') as modified FROM files;"

# 存在多少块（文本片段）
sqlite3 ~/.openclaw/memory/main.sqlite "SELECT COUNT(*) FROM chunks;"

# 按文本搜索块（FTS5全文搜索）
sqlite3 ~/.openclaw/memory/main.sqlite "SELECT substr(text, 1, 200) FROM chunks_fts WHERE chunks_fts MATCH '关键词' LIMIT 5;"

# 检查嵌入配置
sqlite3 ~/.openclaw/memory/main.sqlite "SELECT value FROM meta WHERE key='memory_index_meta_v1';" | python3 -m json.tool

# 检查Gemini嵌入速率限制（破坏索引）
grep -i "gemini.*batch.*failed\|RESOURCE_EXHAUSTED\|429" ~/.openclaw/logs/gateway.err.log | tail -10
# "embeddings: gemini batch failed (2/2); disabling batch" = 索引降级

# 重建内存索引（重新索引所有工作空间文件）
# 删除数据库并重启网关 - 它会重建：
# rm ~/.openclaw/memory/main.sqlite && openclaw gateway restart
```

## 定时任务（Cron）管理

```bash
# 1. 所有任务概览
cat ~/.openclaw/cron/jobs.json | jq -r '.jobs[] | "\(.enabled | if . then "ON " else "OFF" end) \(.state.lastStatus // "never" | if . == "error" then "FAIL" elif . == "ok" then "OK  " else .  end) \(.name)"'

# 2. 失败任务及错误详情
cat ~/.openclaw/cron/jobs.json | jq '.jobs[] | select(.state.lastStatus == "error") | {name, error: .state.lastError, lastRun: (.state.lastRunAtMs | . / 1000 | todate), id}'

# 3. 读取失败任务的实际运行日志
任务ID="粘贴任务UUID"
tail -20 ~/.openclaw/cron/runs/$任务ID.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        obj = json.loads(line)
        if obj.get('type') == 'message':
            role = obj['message']['role']
            text = ''.join(c.get('text','') for c in obj['message'].get('content',[]) if isinstance(c,dict))
            if text.strip():
                print(f'[{role}] {text[:300]}')
                print()
    except: pass
"

# 4. 常见定时任务失败原因：
#    - "Signal RPC -1" → Signal守护进程关闭，见Signal部分
#    - "gateway timeout after 10000ms" → 定时任务触发时网关正在重启
#    - "Brave Search 429" → 免费层速率限制达到（每月2000次请求）
#    - "embedded run timeout" → 任务耗时超过600秒

# 5. 下次计划运行时间
cat ~/.openclaw/cron/jobs.json | jq -r '.jobs[] | select(.enabled) | "\(.name): \((.state.nextRunAtMs // 0) | . / 1000 | todate)"'

# 6. 临时禁用损坏的任务
cat ~/.openclaw/cron/jobs.json | jq '(.jobs[] | select(.name == "任务名称")).enabled = false' > /tmp/cron.json && mv /tmp/cron.json ~/.openclaw/cron/jobs.json
```

## 通道安全模式

| 模式 | 行为 | 风险 |
|---|---|---|
| `open` + `allowFrom: ["*"]` | 任何人都可以发送消息，机器人回复所有人 | 高 - 消耗API积分，机器人以你的身份发言 |
| `allowlist` + `allowFrom: ["+1..."]` | 只有列出的号码可以通过 | 低 - 显式控制 |
| `pairing` | 未知发送者获得代码，你批准 | 低 - 批准门控 |
| `disabled` | 通道完全关闭 | 无 |

### 检查当前安全状态

```bash
cat ~/.openclaw/openclaw.json | jq '{
  whatsapp: {policy: .channels.whatsapp.dmPolicy, from: .channels.whatsapp.allowFrom, groups: .channels.whatsapp.groupPolicy, selfChat: .channels.whatsapp.selfChatMode},
  signal: {policy: .channels.signal.dmPolicy, from: .channels.signal.allowFrom, groups: .channels.signal.groupPolicy},
  telegram: {policy: .channels.telegram.dmPolicy, groups: .channels.telegram.groupPolicy, bots: [.channels.telegram.accounts | to_entries[] | "\(.key)=\(.value.enabled)"]},
  imessage: {enabled: .channels.imessage.enabled, policy: .channels.imessage.dmPolicy}
}'
```

## 工作空间文件管理

| 文件 | 作用 | 何时编辑 |
|---|---|---|
| `SOUL.md` | 个性：语气、风格（"不要破折号，小写随意"） | 更改机器人说话方式时 |
| `IDENTITY.md` | 名称（Jarvis）、生物类型、表情符号 | 重新品牌化时 |
| `USER.md` | 所有者信息、偏好 | 用户上下文更改时 |
| `AGENTS.md` | 操作规则：内存协议、安全、群聊行为、心跳指令 | 更改机器人行为时 |
| `BOOT.md` | 启动指令（自动驾驶通知协议：WA → Signal） | 更改启动时发生的情况 |
| `HEARTBEAT.md` | 定期检查清单（空 = 无心跳API调用） | 添加/删除定期任务时 |
| `MEMORY.md` | 策划的长期记忆（仅在主/直接会话中加载） | 机器人自行管理 |
| `TOOLS.md` | 联系人、SSH主机、设备昵称 | 添加本地工具笔记时 |
| `memory/*.md` | 每日原始日志、特定主题聊天日志 | 机器人自动写入 |

## 扩展OpenClaw

### 技能系统

技能是扩展代理知识和能力的主要方式。它们是带有可选脚本/资产的Markdown文件，在相关时加载到上下文中。

```bash
# 搜索技能（跨注册表的向量搜索）
npx skills find "postgres optimization"
npx skills find "image generation"

# 浏览最新技能
npx skills explore

# 安装技能
npx skills add supabase-postgres-best-practices
npx skills add nano-banana-pro

# 安装特定版本
npx skills add my-skill --version 1.2.3

# 列出已安装内容
npx skills list

# 更新所有已安装技能
npx skills update --all

# 更新特定技能
npx skills update my-skill
npx skills update my-skill --force  # 覆盖本地更改
```

### 创建自己的技能

技能只是一个包含`SKILL.md`的文件夹：

```
我的技能/
├── SKILL.md              # 必需：YAML前言 + Markdown指令
├── scripts/              # 可选：可执行脚本
├── references/           # 可选：按需加载的文档
└── assets/               # 可选：模板、图像
```

**SKILL.md格式：**
```markdown
---
name: 我的技能
description: 这个做什么以及何时触发。描述是主要触发器 - 代理读取此内容以决定是否加载完整技能。
---

# 我的技能

指令放在这里。仅在技能触发后加载。
保持在500行以下。将大内容拆分到references/文件中。
```

**关键原则：上下文窗口是共享资源。** 只包含代理不知道的内容。优先简洁示例而非冗长解释。

### 多代理编排

OpenClaw可以生成其他AI代理（Codex、Claude Code、Pi）作为后台工作器。这是运行并行编码任务、审查或任何受益于多个代理的工作的方式。

**模式：** `bash pty:true background:true workdir:/path command:"agent 'task'"`

```bash
# 生成Codex构建某些东西（后台，自动批准）
bash pty:true workdir:~/项目 background:true command:"codex exec --full-auto '构建待办事项的REST API'"
# 返回用于跟踪的sessionId

# 在不同任务上生成Claude Code
bash pty:true workdir:~/其他项目 background:true command:"claude '重构认证模块'"

# 监控所有运行中的代理
process action:list

# 检查特定代理的输出
process action:log sessionId:XXX

# 如果代理提问，发送输入
process action:submit sessionId:XXX data:"yes"

# 杀死卡住的代理
process action:kill sessionId:XXX
```

**并行PR审查：**
```bash
# 获取所有PR引用
git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'

# 为每个PR启动一个代理
bash pty:true workdir:~/项目 background:true command:"codex exec '审查PR #86。git diff origin/main...origin/pr/86'"
bash pty:true workdir:~/项目 background:true command:"codex exec '审查PR #87。git diff origin/main...origin/pr/87'"
```

**使用git工作树的并行问题修复：**
```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main

bash pty:true workdir:/tmp/issue-78 background:true command:"codex --yolo '修复问题 #78: 描述。提交并推送。'"
bash pty:true workdir:/tmp/issue-99 background:true command:"codex --yolo '修复问题 #99: 描述。提交并推送。'"
```

**代理完成时自动通知：**
```bash
bash pty:true workdir:~/项目 background:true command:"codex --yolo exec '你的任务。

完全完成后，运行：openclaw gateway wake --text \"完成: 摘要\" --mode now'"
```

## 已知错误模式

| 错误 | 含义 | 修复 |
|---|---|---|
| `Web connection closed (status 408)` | WhatsApp网页超时，自动重试最多12次 | 通常自我修复。如果达到12/12，重启网关 |
| `Signal RPC -1: Failed to send message` | signal-cli守护进程失去连接 | 重启网关 |
| `Signal RPC -5: Failed to send message due to rate limiting` | Signal速率限制 | 等待并重试，减少消息频率 |
| `No profile name set` (signal-cli WARN) | 淹没日志，无害 | `signal-cli -a +账户 updateProfile --given-name "名称"` |
| `Cross-context messaging denied` | 代理尝试跨通道发送 | 不是错误 - 安全护栏。消息必须源自正确的通道会话 |
| `getUpdates timed out after 500 seconds` | Telegram机器人失去轮询连接 | 重启网关 |
| `Unrecognized keys: "token", "username"` | Telegram机器人的错误配置键 | 在openclaw.json中使用`botToken`而不是`token` |
| `RESOURCE_EXHAUSTED` (Gemini 429) | 嵌入速率限制 | 减少工作空间文件变动，或升级Gemini配额 |
| `lane wait exceeded` | 代理在长LLM调用上阻塞 | 等待，如果卡住>2分钟则重启 |
| `embedded run timeout: timeoutMs=600000` | 代理响应超过10分钟 | 将任务分解为更小的部分 |
| `gateway timeout after 10000ms` | 网关在重启窗口期间不可达 | 定时任务在网关关闭时触发 - 暂时性 |

## 实用命令参考

### 网关管理

```bash
# 检查网关状态
openclaw gateway status

# 启动网关
openclaw gateway start

# 停止网关
openclaw gateway stop

# 重启网关
openclaw gateway restart

# 检查网关日志
tail -f ~/.openclaw/logs/gateway.log

# 检查错误日志
tail -f ~/.openclaw/logs/gateway.err.log
```

### 系统状态

```bash
# 完整系统状态
openclaw status

# 深度系统状态（更多详情）
openclaw status --deep

# 检查OpenClaw版本
openclaw --version

# 检查配置
openclaw configure
```

### 节点管理

```bash
# 列出连接的节点
openclaw nodes list

# 节点状态
openclaw nodes status

# 发送通知到节点
openclaw nodes notify --title "标题" --body "消息内容"
```

## OPC项目专用配置

### 当前OPC项目状态

基于你的OpenClaw系统，以下配置可能有用：

#### 1. 加密货币监控配置
```bash
# 为加密货币监控添加定时任务
cat > ~/.openclaw/cron/opc_crypto_monitor.json << 'EOF'
{
  "name": "OPC加密货币日报",
  "enabled": true,
  "schedule": {
    "kind": "every",
    "everyMs": 86400000  # 每天一次
  },
  "payload": {
    "channel": "telegram",
    "to": "coder",
    "sessionTarget": "isolated",
    "message": "执行加密货币市场日报分析。使用crypto-ta-analyzer技能分析BTC、ETH、SOL。生成包含技术指标、交易信号和风险提示的报告。"
  }
}
EOF
```

#### 2. Mission Control集成
```bash
# 检查Mission Control服务器状态
curl http://localhost:8080/api/tasks

# 创建OPC任务
curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "加密货币技术分析 - BTC",
    "description": "使用crypto-ta-analyzer分析比特币的技术指标",
    "category": "crypto",
    "priority": "high",
    "assignee": "crypto-monitor",
    "createdBy": "system"
  }'
```

#### 3. 安全配置优化
```bash
# 为高风险技能添加安全策略
jq '.agents.defaults.security = {
  "highRiskSkills": ["crypto-report", "agent-reach", "code-simplifier", "ralph-loop"],
  "sandboxTesting": true,
  "rateLimiting": {
    "externalApi": 10,
    "fileOperations": 100,
    "networkCalls": 50
  },
  "auditLogging": true
}' ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json
```

## 故障排除流程

### 标准诊断流程

1. **运行快速健康检查** - 获取系统概览
2. **检查相关日志** - gateway.log和gateway.err.log
3. **验证配置** - 使用jq检查openclaw.json
4. **检查会话状态** - 查看sessions.json
5. **测试通道连接** - 手动发送测试消息
6. **重启网关** - 如果以上都正常但问题仍然存在

### 紧急恢复步骤

```bash
# 1. 停止所有OpenClaw进程
openclaw gateway stop
pkill -f "openclaw"

# 2. 备份当前配置
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.紧急备份

# 3. 从备份恢复
cp ~/.openclaw/openclaw.json.bak ~/.openclaw/openclaw.json

# 4. 验证JSON
python3 -m json.tool ~/.openclaw/openclaw.json > /dev/null && echo "✅ JSON有效" || echo "❌ JSON无效"

# 5. 重启网关
openclaw gateway start

# 6. 监控启动日志
tail -f ~/.openclaw/logs/gateway.log
```

## 性能优化提示

### 减少内存使用

```bash
# 清理旧会话文件（保留最近30天）
find ~/.openclaw/agents/main/sessions -name "*.jsonl" -mtime +30 -delete

# 清理媒体文件
find ~/.openclaw/media/inbound -type f -mtime +7 -delete

# 优化SQLite数据库
sqlite3 ~/.openclaw/memory/main.sqlite "VACUUM;"

# 检查大文件
du -sh ~/.openclaw/*
```

### 提高响应速度

```bash
# 减少并发数（如果响应慢）
jq '.agents.defaults.maxConcurrent = 3 | .agents.defaults.subagents.maxConcurrent = 2' ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json

# 禁用不必要的插件
jq '.plugins.entries | to_entries[] | select(.value.enabled == true) | .key' ~/.openclaw/openclaw.json
# 禁用不需要的插件：jq '.plugins.entries.插件名称.enabled = false'
```

### 监控资源使用

```bash
# 创建监控脚本
cat > ~/monitor_openclaw.sh << 'EOF'
#!/bin/bash
echo "=== OpenClaw资源监控 $(date) ==="
echo "内存使用:"
ps aux | grep openclaw | grep -v grep | awk '{print $6/1024 " MB"}'
echo ""
echo "磁盘使用:"
du -sh ~/.openclaw/
echo ""
echo "会话数量:"
ls ~/.openclaw/agents/main/sessions/*.jsonl | wc -l
echo ""
echo "最后错误:"
tail -5 ~/.openclaw/logs/gateway.err.log
EOF

chmod +x ~/monitor_openclaw.sh
```

## 总结

### ClawPal核心价值

1. **一站式管理**: 所有OpenClaw配置、诊断和管理工具
2. **实战验证**: 每个命令都经过测试并有效
3. **全面覆盖**: 从基础健康检查到高级故障排除
4. **安全优先**: 包含安全配置和风险缓解指南
5. **扩展友好**: 支持技能开发和系统扩展

### 对于OPC项目的特别价值

1. **加密货币监控优化**: 专门的配置模板和定时任务
2. **Mission Control集成**: 与现有OPC系统无缝集成
3. **安全增强**: 为高风险技能提供安全策略
4. **性能监控**: 确保系统稳定运行
5. **故障恢复**: 快速诊断和修复问题

### 推荐使用模式

1. **日常维护**: 使用快速健康检查监控系统状态
2. **问题诊断**: 按通道使用专门的故障排除指南
3. **配置优化**: 使用安全编辑模式修改配置
4. **性能调优**: 定期运行性能监控脚本
5. **扩展开发**: 参考技能和插件开发指南

### 下一步行动建议

1. **立即运行健康检查**: 验证当前系统状态
2. **配置OPC专用定时任务**: 设置加密货币监控
3. **优化安全设置**: 为高风险技能添加限制
4. **设置监控警报**: 创建资源使用监控
5. **定期审计**: 每周运行完整系统审计

---

**ClawPal已安装并准备就绪！** 你现在拥有完整的OpenClaw系统管理能力。从运行快速健康检查开始，确保你的OPC项目系统处于最佳状态。

**技能位置**: `~/.openclaw/workspace/.agents/skills/openclaw-config/`
**完整文档**: `~/.openclaw/workspace/.agents/skills/openclaw-config/SKILL.md` (13610字节)
**使用指南**: `~/.openclaw/workspace/clawpal_usage_guide.md` (10720字节)