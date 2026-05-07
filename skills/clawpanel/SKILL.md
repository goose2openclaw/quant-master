# ClawPanel - OpenClaw 可视化管理面板

ClawPanel 是 OpenClaw 的专业级可视化管理面板，比 openclaw-control-ui 更强大。

## 官方信息

- **GitHub**: https://github.com/zhaoxinyi02/ClawPanel
- **版本**: Pro / Lite 双发行
- **技术栈**: Go + React 18 + TailwindCSS + SQLite + WebSocket
- **端口**: 19527

## 版本对比

| 维度 | ClawPanel Lite | ClawPanel Pro |
|------|---------------|---------------|
| 目标用户 | 新手/开箱即用 | 进阶用户 |
| OpenClaw | 内置 2026.4.8 | 外部接管/一键安装 |
| 运行时控制 | 面板全托管 | 用户自行决定 |
| 通道插件 | 预置常用插件 | 按需安装 |
| Linux | ✅ 已可用 | ✅ 已可用 |
| macOS | 预览阶段 | ✅ 已可用 |
| Windows | ❌ 暂不提供 | ✅ 已可用 |

## 核心功能

### 1. 进程管理
- 启动/停止/重启 OpenClaw
- 实时状态监控（内存/CPU/运行时间）
- 一键重启 OpenClaw / 网关

### 2. 通道管理 (20+)
- QQ (NapCat) · 微信 · Telegram · Discord · WhatsApp
- 飞书 · 钉钉 · 企业微信 · QQ官方Bot · IRC
- 一键启用/禁用

### 3. 插件管理
- 插件市场浏览
- 一键安装/卸载/更新/启用/禁用
- 可视化配置表单
- 冲突检测

### 4. 路由拓扑图
- React Flow DAG 可视化
- 通道 → Agent → 绑定关系
- 实时统计指标

### 5. 工作流系统
- 可视化拖拽画布
- 节点: input / wait_user / approval / ai_plan / ai_task / analyze / summary / publish / end
- AI 生成模板
- 自动任务接管

### 6. 配置管理
- JSON 模式 + 差异预览
- 自动快照备份
- 智能错误检测

### 7. 日志监控
- WebSocket 实时日志
- 消息流追踪
- SQLite 持久化

### 8. 自动更新
- SHA256 校验
- 自动备份回滚
- 离线更新支持

## 安装命令

### ClawPanel Lite (Linux)
```bash
export CLAWPANEL_PUBLIC_BASE="http://43.248.142.249:19527"
curl -fsSL "$CLAWPANEL_PUBLIC_BASE/scripts/install-lite.sh" -o install-lite.sh
sudo CLAWPANEL_PUBLIC_BASE="$CLAWPANEL_PUBLIC_BASE" bash install-lite.sh
```

### ClawPanel Pro (Linux)
```bash
export CLAWPANEL_PUBLIC_BASE="http://43.248.142.249:19527"
curl -fsSL "$CLAWPANEL_PUBLIC_BASE/scripts/install.sh" -o install.sh
sudo CLAWPANEL_PUBLIC_BASE="$CLAWPANEL_PUBLIC_BASE" bash install.sh
```

### Windows (PowerShell 管理员)
```powershell
$env:CLAWPANEL_PUBLIC_BASE="http://43.248.142.249:19527"
irm "$env:CLAWPANEL_PUBLIC_BASE/scripts/install.ps1" | iex
```

## 默认信息

- **端口**: 19527
- **默认密码**: `clawpanel`
- **首次登录后**: 建议修改密码

## Skill 集成

当前 GO2SE 使用的是 openclaw-control-ui。如果要切换到 ClawPanel:
1. 安装 ClawPanel Pro (外部接管模式)
2. 配置接入现有 OpenClaw
3. 迁移完成

## 状态检查

当前环境没有安装 ClawPanel。如果需要安装:
- Pro 版本适合已有 OpenClaw 环境
- Lite 版本适合想要开箱即用的新环境
