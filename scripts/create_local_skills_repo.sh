#!/bin/bash

echo "🏗️ 创建本地OpenClaw技能仓库"
echo "============================="

# 工作目录
WORKSPACE="$HOME/.openclaw/workspace"
SKILLS_DIR="$WORKSPACE/skills"
LOCAL_REPO="$WORKSPACE/local_skills_repo"
BACKUP_DIR="$WORKSPACE/backup"

# 创建目录
mkdir -p "$LOCAL_REPO"
mkdir -p "$BACKUP_DIR"

# 1. 收集所有现有技能
collect_existing_skills() {
    echo "收集现有技能..."
    
    if [ ! -d "$SKILLS_DIR" ]; then
        echo "❌ 技能目录不存在: $SKILLS_DIR"
        return 1
    fi
    
    # 查找所有SKILL.md文件
    SKILL_FILES=$(find "$SKILLS_DIR" -name "SKILL.md" 2>/dev/null)
    
    if [ -z "$SKILL_FILES" ]; then
        echo "⚠ 没有找到任何技能文件"
        return 0
    fi
    
    local count=0
    
    for skill_file in $SKILL_FILES; do
        skill_dir=$(dirname "$skill_file")
        skill_name=$(basename "$skill_dir")
        
        echo "处理: $skill_name"
        
        # 复制到本地仓库
        mkdir -p "$LOCAL_REPO/$skill_name"
        cp -r "$skill_dir"/* "$LOCAL_REPO/$skill_name/" 2>/dev/null
        
        ((count++))
    done
    
    echo "✅ 收集了 $count 个技能到本地仓库"
    return $count
}

# 2. 从备份中恢复技能
restore_from_backup() {
    echo "从备份中恢复技能..."
    
    # 查找最近的备份
    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "skills_backup_*.tar.gz" -type f 2>/dev/null | sort -r | head -1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        echo "找到备份: $LATEST_BACKUP"
        
        # 提取到临时目录
        TEMP_DIR="/tmp/skills_restore_$(date +%s)"
        mkdir -p "$TEMP_DIR"
        
        tar -xzf "$LATEST_BACKUP" -C "$TEMP_DIR" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            # 复制技能到本地仓库
            if [ -d "$TEMP_DIR/skills" ]; then
                for skill_dir in "$TEMP_DIR"/skills/*/; do
                    if [ -d "$skill_dir" ]; then
                        skill_name=$(basename "$skill_dir")
                        echo "恢复: $skill_name"
                        
                        mkdir -p "$LOCAL_REPO/$skill_name"
                        cp -r "$skill_dir"/* "$LOCAL_REPO/$skill_name/" 2>/dev/null
                    fi
                done
            fi
            
            rm -rf "$TEMP_DIR"
            echo "✅ 从备份恢复了技能"
        else
            echo "❌ 备份解压失败"
        fi
    else
        echo "⚠ 没有找到备份文件"
    fi
}

# 3. 创建核心技能模板
create_core_skill_templates() {
    echo "创建核心技能模板..."
    
    # 核心技能列表
    CORE_SKILLS=(
        "github"
        "cron"
        "shell"
        "telegram"
        "whatsapp"
        "brave-search"
        "agent-browser"
        "pdf"
        "docx"
        "xlsx"
        "pptx"
    )
    
    local created=0
    
    for skill in "${CORE_SKILLS[@]}"; do
        # 如果已经存在，跳过
        if [ -f "$LOCAL_REPO/$skill/SKILL.md" ]; then
            continue
        fi
        
        echo "创建: $skill"
        
        # 创建技能目录
        skill_dir="$LOCAL_REPO/$skill"
        mkdir -p "$skill_dir"
        mkdir -p "$skill_dir/scripts"
        mkdir -p "$skill_dir/references"
        
        # 创建SKILL.md
        case $skill in
            "github")
                create_github_skill "$skill_dir"
                ;;
            "cron")
                create_cron_skill "$skill_dir"
                ;;
            "shell")
                create_shell_skill "$skill_dir"
                ;;
            "telegram")
                create_telegram_skill "$skill_dir"
                ;;
            "whatsapp")
                create_whatsapp_skill "$skill_dir"
                ;;
            "brave-search")
                create_brave_search_skill "$skill_dir"
                ;;
            "agent-browser")
                create_agent_browser_skill "$skill_dir"
                ;;
            "pdf"|"docx"|"xlsx"|"pptx")
                create_document_skill "$skill_dir" "$skill"
                ;;
            *)
                create_generic_skill "$skill_dir" "$skill"
                ;;
        esac
        
        ((created++))
    done
    
    echo "✅ 创建了 $created 个核心技能模板"
}

# GitHub技能模板
create_github_skill() {
    local skill_dir=$1
    
    cat > "$skill_dir/SKILL.md" << 'EOF'
---
name: github
description: GitHub代码仓库管理
version: 1.0.0
category: development
---

# GitHub技能

管理GitHub代码仓库，包括克隆、提交、推送等操作。

## 功能
- 克隆仓库
- 提交更改
- 推送代码
- 拉取更新
- 查看状态

## 使用方法
```bash
# 克隆仓库
openclaw skills run github clone <repo_url>

# 查看状态
openclaw skills run github status

# 提交更改
openclaw skills run github commit "提交信息"

# 推送代码
openclaw skills run github push
```

## 配置
编辑config.json文件配置GitHub凭证。
EOF
    
    # 创建脚本
    cat > "$skill_dir/scripts/github.sh" << 'EOF'
#!/bin/bash
# GitHub工具脚本

case $1 in
    "clone")
        git clone "$2"
        ;;
    "status")
        git status
        ;;
    "commit")
        git add . && git commit -m "$2"
        ;;
    "push")
        git push
        ;;
    "pull")
        git pull
        ;;
    *)
        echo "用法: $0 <clone|status|commit|push|pull> [参数]"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/github.sh"
    
    # 创建配置
    cat > "$skill_dir/config.json" << 'EOF'
{
  "github": {
    "enabled": true,
    "auto_sync": true,
    "default_branch": "main"
  }
}
EOF
}

# Cron技能模板
create_cron_skill() {
    local skill_dir=$1
    
    cat > "$skill_dir/SKILL.md" << 'EOF'
---
name: cron
description: 定时任务管理
version: 1.0.0
category: automation
---

# Cron技能

管理系统定时任务，支持添加、删除、列出任务。

## 功能
- 添加定时任务
- 列出所有任务
- 删除任务
- 测试任务

## 使用方法
```bash
# 添加任务
openclaw skills run cron add "* * * * * /path/to/script.sh"

# 列出任务
openclaw skills run cron list

# 删除任务
openclaw skills run cron remove "任务描述"
```

## 配置
编辑config.json文件配置默认任务。
EOF
    
    # 创建脚本
    cat > "$skill_dir/scripts/cron.sh" << 'EOF'
#!/bin/bash
# Cron管理脚本

case $1 in
    "add")
        (crontab -l 2>/dev/null; echo "$2") | crontab -
        echo "任务已添加: $2"
        ;;
    "list")
        crontab -l
        ;;
    "remove")
        crontab -l | grep -v "$2" | crontab -
        echo "任务已移除"
        ;;
    *)
        echo "用法: $0 <add|list|remove> [参数]"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/cron.sh"
    
    # 创建配置
    cat > "$skill_dir/config.json" << 'EOF'
{
  "cron": {
    "enabled": true,
    "tasks": []
  }
}
EOF
}

# Shell技能模板
create_shell_skill() {
    local skill_dir=$1
    
    cat > "$skill_dir/SKILL.md" << 'EOF'
---
name: shell
description: 系统Shell命令执行
version: 1.0.0
category: system
---

# Shell技能

执行系统Shell命令，监控系统状态。

## 功能
- 执行Shell命令
- 监控系统资源
- 管理进程
- 查看网络状态

## 使用方法
```bash
# 查看磁盘使用
openclaw skills run shell disk

# 查看内存使用
openclaw skills run shell memory

# 查看进程
openclaw skills run shell process

# 执行自定义命令
openclaw skills run shell exec "ls -la"
```

## 配置
编辑config.json文件配置命令别名。
EOF
    
    # 创建脚本
    cat > "$skill_dir/scripts/shell.sh" << 'EOF'
#!/bin/bash
# Shell工具脚本

case $1 in
    "disk")
        df -h
        ;;
    "memory")
        free -h
        ;;
    "process")
        ps aux --sort=-%cpu | head -11
        ;;
    "network")
        netstat -tulpn
        ;;
    "exec")
        shift
        eval "$@"
        ;;
    *)
        echo "用法: $0 <disk|memory|process|network|exec> [命令]"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/shell.sh"
    
    # 创建配置
    cat > "$skill_dir/config.json" << 'EOF'
{
  "shell": {
    "enabled": true,
    "safe_mode": true,
    "allowed_commands": ["ls", "ps", "df", "free", "netstat"]
  }
}
EOF
}

# Telegram技能模板
create_telegram_skill() {
    local skill_dir=$1
    
    cat > "$skill_dir/SKILL.md" << 'EOF'
---
name: telegram
description: Telegram Bot通信
version: 1.0.0
category: communication
---

# Telegram技能

通过Telegram Bot发送和接收消息。

## 功能
- 发送消息
- 接收消息
- 管理聊天
- 设置命令

## 使用方法
```bash
# 发送消息
openclaw skills run telegram send <chat_id> "消息内容"

# 测试连接
openclaw skills run telegram test

# 获取更新
openclaw skills run telegram updates
```

## 配置
编辑config.json文件配置Bot Token。
EOF
    
    # 创建脚本
    cat > "$skill_dir/scripts/telegram.sh" << 'EOF'
#!/bin/bash
# Telegram工具脚本

TOKEN="8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o"
BASE_URL="https://api.telegram.org/bot$TOKEN"

case $1 in
    "send")
        curl -s -X POST "$BASE_URL/sendMessage" \
            -d "chat_id=$2" \
            -d "text=$3" \
            -d "parse_mode=Markdown"
        ;;
    "test")
        curl -s "$BASE_URL/getMe"
        ;;
    "updates")
        curl -s "$BASE_URL/getUpdates"
        ;;
    *)
        echo "用法: $0 <send|test|updates> [参数]"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/telegram.sh"
    
    # 创建配置
    cat > "$skill_dir/config.json" << 'EOF'
{
  "telegram": {
    "bot_token": "8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o",
    "enabled": true,
    "notifications": {
      "enabled": true,
      "crypto_alerts": true,
      "system_status": true
    }
  }
}
EOF
}

# WhatsApp技能模板
create_whatsapp_skill() {
    local skill_dir=$1
    
    cat > "$skill_dir/SKILL.md" << 'EOF'
---
name: whatsapp
description: WhatsApp消息通信
version: 1.0.0
category: communication
---

# WhatsApp技能

通过WhatsApp发送和接收消息。

## 功能
- 发送WhatsApp消息
- 接收消息
- 管理联系人
- 群组消息

## 注意
需要配置WhatsApp API凭证。

## 配置
编辑config.json文件配置API凭证。
EOF
    
    # 创建配置
    cat > "$skill_dir/config.json" << 'EOF'
{
  "whatsapp": {
    "enabled": false,
    "api_key": "",
    "api_secret": ""
  }
}
EOF
}

# Brave Search技能模板
create_brave_search_skill() {
    local skill_dir=$1
    
    cat > "$skill_dir/SKILL.md" << 'EOF'
---
name: brave-search
description: Brave搜索引擎
version: 1.0.0
category: web
---

# Brave Search技能

使用Brave搜索引擎进行网络搜索。

## 功能
- 网络搜索
- 图片搜索
- 新闻搜索
- 视频搜索

## 使用方法
```bash
# 搜索网络
openclaw skills run brave-search search "搜索关键词"

# 搜索图片
openclaw skills run brave-search images "图片关键词"
```

## 配置
编辑config.json文件配置API密钥。
EOF
    
    # 创建配置
    cat > "$skill_dir/config.json" << 'EOF'
{
  "brave_search": {
    "enabled": false,
    "api_key": "",
    "safe_search": true
  }
}
EOF
}

# Agent Browser技能模板
create_agent_browser_skill() {
    local skill_dir=$1
    
    cat > "$skill_dir/SKILL.md" << 'EOF'
---
name: agent-browser
description: 自动化浏览器控制
version: 1.0.0
category: web
---

# Agent Browser技能

控制浏览器进行自动化操作。

## 功能
- 打开网页
- 点击元素
- 填写表单
- 截图
- 执行JavaScript

## 配置
编辑config.json文件配置浏览器设置。
EOF
    
    # 创建配置
    cat > "$skill_dir/config.json" << 'EOF'
{
  "agent_browser": {
    "enabled": true,
    "browser": "chromium",
    "headless": true,
    "timeout": 30000
  }
}
EOF
}

# 文档处理技能模板
create_document_skill() {
    local skill_dir=$1
    local skill=$2
    
    cat > "$skill_dir/SKILL.md" << EOF
---
name: $skill
description: ${skill^^}文档处理
version: 1.0.0
category: document
---

# ${skill^^}技能

处理${skill^^}格式的文档。

## 功能
- 读取${skill^^}文档
- 创建${skill^^}文档
- 编辑${skill^^}文档
- 转换格式

## 配置
编辑config.json文件配置文档处理选项。
EOF
    
    # 创建配置
    cat > "$skill_dir/config.json" << EOF
{
  "${skill}": {
    "enabled": true,
    "auto_convert": false,
    "default_template": ""
  }
}
EOF
}

# 通用技能模板
create_generic_skill() {
    local skill_dir=$1
    local skill=$2
    
    cat > "$skill_dir/SKILL.md" << EOF
---
name: $skill
description: $skill 功能
version: 1.0.0
category: utility
---

# $skill 技能

$skill 功能实现。

## 功能
- 功能1
- 功能2
- 功能3

## 配置
编辑config.json文件进行配置。
EOF
    
    # 创建配置
    cat > "$skill_dir/config.json" << EOF
{
  "${skill}": {
    "enabled": true,
    "auto_start": false
  }
}
EOF
}

# 4. 创建本地仓库索引
create_repo_index() {
    echo "创建本地仓库索引..."
    
    # 统计技能
    SKILL_COUNT=$(find "$LOCAL_REPO" -name "SKILL.md" 2>/dev/null | wc -l)
    
    # 创建索引文件
    cat > "$LOCAL_REPO/INDEX.md" << EOF
# 本地OpenClaw技能仓库

## 仓库信息
- 创建时间: $(date)
- 技能数量: $SKILL_COUNT
- 位置: $LOCAL_REPO

## 可用技能

$(find "$LOCAL_REPO" -name "SKILL.md" 2>/dev/null | xargs -I {} dirname {} | xargs -I {} basename {} | sort | while read skill; do
    description=$(grep -i "description:" "$LOCAL_REPO/$skill/SKILL.md" 2>/dev/null | head -1 | cut -d':' -f2- | sed 's/^ *//;s/ *$//')
    echo "- **$skill**: ${description:-无描述}"
done)

## 使用方法

### 1. 复制技能到工作空间
\`\`\`bash
# 复制所有技能
cp -r $LOCAL_REPO/* ~/.open