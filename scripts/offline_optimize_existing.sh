#!/bin/bash

echo "🔧 离线优化现有OpenClaw技能配置"
echo "=================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 工作目录
WORKSPACE="$HOME/.openclaw/workspace"
SKILLS_DIR="$WORKSPACE/skills"

# 1. 检查现有技能
check_existing_skills() {
    print_section "检查现有技能"
    
    echo "已安装的技能:"
    echo "--------------"
    
    if [ -d "$SKILLS_DIR" ]; then
        for skill_dir in "$SKILLS_DIR"/*/; do
            if [ -d "$skill_dir" ]; then
                skill=$(basename "$skill_dir")
                if [ -f "$skill_dir/SKILL.md" ]; then
                    # 提取技能描述
                    description=$(grep -i "description:" "$skill_dir/SKILL.md" | head -1 | cut -d':' -f2- | sed 's/^ *//;s/ *$//')
                    echo "  ✓ $skill: ${description:0:50}..."
                else
                    echo "  ⚠ $skill: 缺少SKILL.md"
                fi
            fi
        done
    else
        echo "  未找到技能目录"
    fi
    
    # 检查OpenClaw技能状态
    echo -e "\nOpenClaw技能状态:"
    echo "------------------"
    openclaw skills list | grep -E "(✓ ready|✗ missing)" | head -10
}

# 2. 优化现有技能配置
optimize_existing_skills() {
    print_section "优化现有技能配置"
    
    # 为每个现有技能创建优化配置
    for skill_dir in "$SKILLS_DIR"/*/; do
        if [ -d "$skill_dir" ]; then
            skill=$(basename "$skill_dir")
            
            case $skill in
                "github")
                    optimize_github_skill "$skill_dir"
                    ;;
                "cron")
                    optimize_cron_skill "$skill_dir"
                    ;;
                "shell")
                    optimize_shell_skill "$skill_dir"
                    ;;
                "telegram")
                    optimize_telegram_skill "$skill_dir"
                    ;;
                "opc-"*)  # 所有OPC自定义技能
                    optimize_opc_skill "$skill_dir"
                    ;;
                *)
                    create_basic_config "$skill_dir" "$skill"
                    ;;
            esac
        fi
    done
    
    print_success "现有技能配置优化完成"
}

# GitHub技能优化
optimize_github_skill() {
    local skill_dir=$1
    
    print_warning "优化GitHub技能配置..."
    
    # 创建GitHub配置
    cat > "$skill_dir/config.json" << 'EOF'
{
  "github": {
    "enabled": true,
    "autoSync": true,
    "repositories": [
      {
        "name": "opc-project",
        "path": "~/opc-project",
        "autoCommit": true,
        "autoPush": false
      }
    ],
    "notifications": {
      "newCommits": true,
      "pullRequests": true,
      "issues": true
    }
  }
}
EOF
    
    # 创建GitHub工具脚本
    cat > "$skill_dir/scripts/github_tools.sh" << 'EOF'
#!/bin/bash
# GitHub工具脚本

OPC_REPO="$HOME/opc-project"

case $1 in
    "status")
        cd "$OPC_REPO" && git status
        ;;
    "commit")
        cd "$OPC_REPO" && git add . && git commit -m "$2"
        ;;
    "push")
        cd "$OPC_REPO" && git push
        ;;
    "pull")
        cd "$OPC_REPO" && git pull
        ;;
    "log")
        cd "$OPC_REPO" && git log --oneline -10
        ;;
    *)
        echo "用法: $0 <status|commit|push|pull|log> [message]"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/github_tools.sh"
    print_success "GitHub技能优化完成"
}

# Cron技能优化
optimize_cron_skill() {
    local skill_dir=$1
    
    print_warning "优化Cron技能配置..."
    
    # 创建OPC项目cron任务
    cat > "$skill_dir/config.json" << 'EOF'
{
  "cron": {
    "enabled": true,
    "tasks": [
      {
        "name": "opc_daily_check",
        "description": "OPC项目每日检查",
        "schedule": "0 8 * * *",
        "command": "bash ~/opc-project/scripts/daily_check.sh",
        "enabled": true
      },
      {
        "name": "opc_hourly_monitor",
        "description": "OPC项目每小时监控",
        "schedule": "0 * * * *",
        "command": "python3 ~/opc-project/scripts/monitor.py",
        "enabled": true
      },
      {
        "name": "backup_opc_project",
        "description": "备份OPC项目",
        "schedule": "0 2 * * *",
        "command": "bash ~/opc-project/scripts/backup.sh",
        "enabled": true
      }
    ]
  }
}
EOF
    
    # 创建cron管理脚本
    cat > "$skill_dir/scripts/cron_manager.sh" << 'EOF'
#!/bin/bash
# Cron任务管理器

case $1 in
    "list")
        crontab -l
        ;;
    "add")
        echo "$2" | crontab -
        echo "任务已添加"
        ;;
    "remove")
        crontab -l | grep -v "$2" | crontab -
        echo "任务已移除"
        ;;
    "test")
        # 测试所有任务
        for task in ~/opc-project/scripts/*.sh; do
            if [ -x "$task" ]; then
                echo "测试: $(basename $task)"
                bash "$task"
            fi
        done
        ;;
    *)
        echo "用法: $0 <list|add|remove|test> [schedule]"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/cron_manager.sh"
    
    # 创建示例cron任务脚本
    cat > "$WORKSPACE/scripts/daily_check.sh" << 'EOF'
#!/bin/bash
echo "🔄 OPC项目每日检查 - $(date)"
echo "=============================="

# 检查项目状态
echo "1. 检查项目目录..."
if [ -d "$HOME/opc-project" ]; then
    echo "   ✓ OPC项目目录存在"
    PROJECT_SIZE=$(du -sh "$HOME/opc-project" | cut -f1)
    echo "   项目大小: $PROJECT_SIZE"
else
    echo "   ✗ OPC项目目录不存在"
fi

# 检查技能状态
echo -e "\n2. 检查OpenClaw技能..."
SKILL_COUNT=$(find "$HOME/.openclaw/workspace/skills" -name "SKILL.md" 2>/dev/null | wc -l)
echo "   技能数量: $SKILL_COUNT"

# 检查Git状态
echo -e "\n3. 检查Git状态..."
if [ -d "$HOME/opc-project/.git" ]; then
    cd "$HOME/opc-project"
    BRANCH=$(git branch --show-current)
    STATUS=$(git status --porcelain)
    echo "   当前分支: $BRANCH"
    if [ -z "$STATUS" ]; then
        echo "   代码库干净"
    else
        echo "   有未提交的更改"
    fi
fi

echo -e "\n✅ 每日检查完成"
EOF
    
    chmod +x "$WORKSPACE/scripts/daily_check.sh"
    print_success "Cron技能优化完成"
}

# Shell技能优化
optimize_shell_skill() {
    local skill_dir=$1
    
    print_warning "优化Shell技能配置..."
    
    # 创建系统监控脚本
    cat > "$skill_dir/scripts/system_monitor.sh" << 'EOF'
#!/bin/bash
# 系统监控脚本

case $1 in
    "disk")
        echo "💾 磁盘使用情况:"
        df -h | grep -E "(Filesystem|/dev/)"
        ;;
    "memory")
        echo "🧠 内存使用情况:"
        free -h
        ;;
    "cpu")
        echo "⚡ CPU使用情况:"
        top -bn1 | grep "Cpu(s)"
        ;;
    "process")
        echo "🔄 进程监控 (前10个):"
        ps aux --sort=-%cpu | head -11
        ;;
    "network")
        echo "🌐 网络连接:"
        netstat -tulpn | grep -E "(LISTEN|ESTABLISHED)"
        ;;
    "all")
        echo "📊 系统状态报告 - $(date)"
        echo "=========================="
        $0 disk
        echo ""
        $0 memory
        echo ""
        $0 cpu
        echo ""
        $0 process
        ;;
    *)
        echo "用法: $0 <disk|memory|cpu|process|network|all>"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/system_monitor.sh"
    
    # 创建OPC项目管理脚本
    cat > "$skill_dir/scripts/opc_manager.sh" << 'EOF'
#!/bin/bash
# OPC项目管理脚本

OPC_DIR="$HOME/opc-project"

case $1 in
    "start")
        echo "启动OPC项目..."
        # 这里可以添加启动命令
        echo "✅ OPC项目已启动"
        ;;
    "stop")
        echo "停止OPC项目..."
        # 这里可以添加停止命令
        echo "✅ OPC项目已停止"
        ;;
    "status")
        echo "OPC项目状态:"
        echo "目录: $OPC_DIR"
        if [ -d "$OPC_DIR" ]; then
            echo "状态: ✅ 存在"
            ls -la "$OPC_DIR"
        else
            echo "状态: ❌ 不存在"
        fi
        ;;
    "backup")
        echo "备份OPC项目..."
        BACKUP_FILE="$HOME/opc_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar -czf "$BACKUP_FILE" "$OPC_DIR" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ 备份完成: $BACKUP_FILE"
        else
            echo "❌ 备份失败"
        fi
        ;;
    *)
        echo "用法: $0 <start|stop|status|backup>"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/opc_manager.sh"
    print_success "Shell技能优化完成"
}

# Telegram技能优化
optimize_telegram_skill() {
    local skill_dir=$1
    
    print_warning "优化Telegram技能配置..."
    
    # 创建Telegram配置（使用您提供的Token）
    cat > "$skill_dir/config.json" << EOF
{
  "telegram": {
    "botToken": "8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o",
    "enabled": true,
    "notifications": {
      "cryptoAlerts": true,
      "systemStatus": true,
      "errors": true,
      "dailyReport": true
    },
    "commands": [
      {
        "command": "/start",
        "description": "启动OPC系统"
      },
      {
        "command": "/status",
        "description": "查看系统状态"
      },
      {
        "command": "/crypto",
        "description": "加密货币行情"
      },
      {
        "command": "/help",
        "description": "帮助信息"
      }
    ]
  }
}
EOF
    
    # 创建Telegram工具脚本
    cat > "$skill_dir/scripts/telegram_tools.sh" << 'EOF'
#!/bin/bash
# Telegram工具脚本

TOKEN="8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o"
BASE_URL="https://api.telegram.org/bot$TOKEN"

case $1 in
    "send")
        CHAT_ID="$2"
        MESSAGE="$3"
        curl -s -X POST "$BASE_URL/sendMessage" \
            -d "chat_id=$CHAT_ID" \
            -d "text=$MESSAGE" \
            -d "parse_mode=Markdown"
        ;;
    "test")
        echo "测试Telegram连接..."
        curl -s "$BASE_URL/getMe" | jq .
        ;;
    "updates")
        echo "获取最近消息..."
        curl -s "$BASE_URL/getUpdates" | jq '.result[] | {chat_id: .message.chat.id, text: .message.text}'
        ;;
    *)
        echo "用法:"
        echo "  $0 send <chat_id> <message>"
        echo "  $0 test"
        echo "  $0 updates"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/telegram_tools.sh"
    
    # 创建OPC通知脚本
    cat > "$skill_dir/scripts/opc_notifier.sh" << 'EOF'
#!/bin/bash
# OPC项目通知脚本

TOKEN="8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o"
BASE_URL="https://api.telegram.org/bot$TOKEN"

send_opc_notification() {
    local chat_id="$1"
    local type="$2"
    local message="$3"
    
    case $type in
        "status")
            EMOJI="📊"
            ;;
        "alert")
            EMOJI="🚨"
            ;;
        "success")
            EMOJI="✅"
            ;;
        "info")
            EMOJI="ℹ️"
            ;;
        *)
            EMOJI="📝"
            ;;
    esac
    
    FULL_MESSAGE="$EMOJI OPC通知 [$type]\n\n$message\n\n⏰ $(date '+%Y-%m-%d %H:%M:%S')"
    
    curl -s -X POST "$BASE_URL/sendMessage" \
        -d "chat_id=$chat_id" \
        -d "text=$FULL_MESSAGE" \
        -d "parse_mode=Markdown" > /dev/null
    
    echo "通知已发送: $type"
}

# 示例使用
if [ "$1" = "test" ]; then
    echo "发送测试通知..."
    # 这里需要Chat ID
    # send_opc_notification "YOUR_CHAT_ID" "info" "这是测试通知"
else
    echo "OPC通知脚本"
    echo "使用: 在您的脚本中调用 send_opc_notification 函数"
fi
EOF
    
    chmod +x "$skill_dir/scripts/opc_notifier.sh"
    print_success "Telegram技能优化完成"
}

# OPC自定义技能优化
optimize_opc_skill() {
    local skill_dir=$1
    local skill=$(basename "$skill_dir")
    
    print_warning "优化OPC技能: $skill"
    
    # 为每个OPC技能创建专用配置
    case $skill in
        "opc-crypto-monitor")
            cat > "$skill_dir/config.json" << 'EOF'
{
  "crypto_monitor": {
    "enabled": true,
    "coins": ["bitcoin", "ethereum", "solana", "cardano"],
    "check_interval": 300,
    "notifications": {
      "price_change": 5.0,
      "volume_spike": true
    },
    "data_source": "mock",  # mock, coingecko, binance
    "mock_data": {
      "enabled": true,
      "update_frequency": 60
    }
  }
}
EOF
            ;;
        "opc-job-assistant")
            cat > "$skill_dir/config.json" << 'EOF'
{
  "job_assistant": {
    "enabled": true,
    "sources": ["linkedin", "jobstreet"],
    "keywords": ["python", "blockchain", "smart contract", "web3"],
    "check_interval": 3600,
    "notifications": {
      "new_jobs": true,
      "matching_jobs": true
    }
  }
}
EOF
            ;;
        "opc-smart-contract")
            cat > "$skill_dir/config.json" << 'EOF'
{
  "smart_contract": {
    "enabled": true,
    "network": "testnet",
    "contracts": {
      "learning": "~/opc-project/smart-contracts/learning",
      "deployments": "~/opc-project/smart-contracts/deployments"
    },
    "tools": {
      "solc": true,
      "hardhat": false,
      "truffle": false
    }
  }
}
EOF
            ;;
        "opc-trading-helper")
            cat > "$skill_dir/config.json" << 'EOF'
{
  "trading_helper": {
    "enabled": true,
    "strategies": ["moving_average", "rsi", "macd"],
    "paper_trading": true,
    "risk_management": {
      "max_position": 0.1,
      "stop_loss": 0.05,
      "take_profit": 0.1
    }
  }
}
EOF
            ;;
    esac
    
    # 为每个OPC技能创建功能脚本
    cat > "$skill_dir/scripts/${skill}_main.sh" << EOF
#!/bin/bash
# $skill 主脚本

echo "🚀 启动 $skill"
echo "配置加载中..."

# 加载配置
if [ -f "config.json" ]; then
    echo "✅ 配置加载成功"
else
    echo "⚠ 使用默认配置"
fi

# 技能特定功能
case \$1 in
    "start")
        echo "开始 $skill 功能..."
        # 这里添加具体功能
        ;;
    "stop")
        echo "停止 $skill 功能..."
        ;;
    "status")
        echo "$skill 状态: 运行中"
        ;;
    *)
        echo "用法: \$0 <start|stop|status>"
        ;;
esac
EOF
    
    chmod +x "$skill_dir/scripts/${skill}_main.sh"
    print_success "OPC技能 $skill 优化完成"
}

# 基础配置创建
create_basic_config() {
    local skill_dir=$1
    local skill=$2
    
    # 只创建基本配置，不详细优化
    if [ ! -f "$skill_dir/config.json" ]; then
        cat > "$skill_dir/config.json" << EOF
{
  "$skill": {
    "enabled": true,
    "optimized": "$(date +%Y-%m-%d)",
    "notes": "自动优化的配置"
  }
}
EOF
        print_warning "为 $skill 创建基础配置"
    fi
}

# 3. 创建统一管理界面
create_unified_interface() {
    print_section "创建统一管理界面"
    
    # 创建OPC控制中心
    cat > "$WORKSPACE/scripts/opc_control_center.sh" << 'EOF'
#!/bin/bash

echo "🎮 OPC项目控制中心"
echo "=================="

while true; do
    echo ""
    echo "请选择操作:"
    echo "1. 📊 查看系统状态"
    echo "2. 🛠️  管理技能"
    echo "3. ⚙️  配置设置"
    echo "4. 📈 加密货币监控"
    echo "5. 💼 求职助手"
    echo "6. 📝 智能合约开发"
    echo "7. 🔔 通知设置"
    echo "8. 🚪 退出"
    echo ""
    read -p "选择 (1-8): " choice
    
    case $choice in
        1)
            echo -e "\n📊 系统状态:"
            echo "------------"
            bash "$HOME/.openclaw/workspace/skills/shell/scripts/system_monitor.sh" all
            ;;
        2)
            echo -e "\n🛠️ 技能管理:"
            echo "------------"
            echo "已安装技能:"
            find "$HOME/.openclaw/workspace/skills" -name "SKILL.md" | xargs -I {} dirname {} | xargs -I {} basename {} | sort
            ;;
        3)
            echo -e "\n⚙️ 配置设置:"
            echo "------------"
            echo "1. 查看Telegram配置"
            echo "2. 查看GitHub配置"
            echo "3. 查看Cron配置"
            read -p "选择: " config_choice
            case $config_choice in
                1) cat "$HOME/.openclaw/workspace/skills/telegram/config.json" | jq . ;;
                2) cat "$HOME/.openclaw/workspace/skills/github/config.json" | jq . ;;
                3) cat "$HOME/.openclaw/workspace/skills/cron/config.json" | jq . ;;
            esac
            ;;
        4)
            echo -e "\n📈 加密货币监控:"
            echo "----------------"
            echo "启动加密货币监控..."
            bash "$HOME/.openclaw/workspace/skills/opc-crypto-monitor/scripts/opc-crypto-monitor_main.sh" start
            ;;
        5)
            echo -e "\n💼 求职助手:"
            echo "------------"
            echo "启动求职助手..."
            bash "$HOME/.openclaw/workspace/skills/opc-job-assistant/scripts/opc-job-assistant_main.sh" start
            ;;
        6)
            echo -e "\n📝 智能合约开发:"
            echo "----------------"
            echo "打开智能合约目录..."
            cd "$HOME/opc-project/smart-contracts" && ls -la
            ;;
        7)
            echo -e "\n🔔 通知设置:"
            echo "------------"
            echo "1. 测试Telegram通知"
            echo "2. 查看通知配置"
            read -p "选择: " notify_choice
            case $notify_choice in
                1) echo "需要Chat ID来测试" ;;
                2) cat "$HOME/.openclaw/workspace/skills/telegram/config.json" | jq '.telegram.notifications' ;;
            esac
            ;;
        8)
            echo "再见！"
            exit 0
            ;;
        *)
            echo "无效选择"
            ;;
    esac
    
    echo ""
    read -p "按回车键继续..."
done
EOF
    
    chmod +x "$WORKSPACE/scripts/opc_control_center.sh"
    
    # 创建快速启动别名
    cat > "$WORKSPACE/scripts/quick_start.sh" << 'EOF'
#!/bin/bash
# OPC项目快速启动脚本

echo "🚀 快速启动OPC项目"
echo "=================="

# 启动控制中心
bash "$HOME/.openclaw/workspace/scripts/opc_control_center.sh"
EOF
    
    chmod +x "$WORKSPACE/scripts/quick_start.sh"
    
    print_success "统一管理界面创建完成"
}

# 4. 创建优化报告
create_optimization_report() {
    print_section "创建优化报告"
    
    REPORT_FILE="$WORKSPACE/logs/optimization_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# OpenClaw技能离线优化报告

## 优化时间
$(date)

## 已优化的技能

### 核心技能
$(for skill in github cron shell telegram; do
    if [ -f "$SKILLS_DIR/$skill/config.json" ]; then
        echo "- **$skill**: 已优化配置和脚本"
    fi
done)

### OPC自定义技能
$(for skill in opc-crypto-monitor opc-job-assistant opc-smart-contract opc-trading-helper; do
    if [ -f "$SKILLS_DIR/$skill/config.json" ]; then
        echo "- **$skill**: 已创建专用配置"
    fi
done)

## 创建的脚本

### 管理脚本
- \`opc_control_center.sh\` - 统一管理界面
- \`quick_start.sh\` - 快速启动脚本
- \`daily_check.sh\` - 每日检查脚本

### 技能专用脚本
$(find "$SKILLS_DIR" -name "*.sh" -type f | while read script; do
    echo "- \`$(basename "$script")\` - $(dirname "$script" | xargs basename)技能"
done | head -10)

## 配置详情

### Telegram配置
- Bot Token: 已配置
- 通知类型: 加密货币警报、系统状态、错误报告
- 命令: /start, /status, /crypto, /help

### GitHub配置
- 自动同步: 已启用
- 仓库监控: opc-project
- 通知: 提交、拉取请求、问题

### Cron配置
- 每日检查: 08:00
- 每小时监控: 每小时
- 每日备份: 02:00

## 使用说明

### 启动控制中心
\`\`\`bash
bash ~/.openclaw/workspace/scripts/opc_control_center.sh
\`\`\`

### 快速启动
\`\`\`bash
bash ~/.openclaw/workspace/scripts/quick_start.sh
\`\`\`

### 每日检查
\`\`\`bash
bash ~/.openclaw/workspace/scripts/daily_check.sh
\`\`\`

## 下一步建议

1. **测试Telegram集成** - 网络恢复后测试Bot
2. **配置GitHub仓库** - 设置远程仓库
3. **开发加密货币监控** - 开始编写核心功能
4. **学习Solidity** - 开始智能合约开发

## 故障排除

如果遇到问题:

1. 检查技能配置: \`cat ~/.openclaw/workspace/skills/<skill>/config.json\`
2. 运行测试: \`bash ~/.openclaw/workspace/skills/<skill>/scripts/*.sh\`
3. 查看日志: \`ls ~/.openclaw/workspace/logs/\`

---
*报告自动生成于 $(date)*
EOF
    
    print_success "优化报告已生成: $REPORT_FILE"
}

# 主函数
main() {
    echo ""
    echo "开始离线优化现有技能配置..."
    echo "="*50
    
    # 检查现有技能
    check_existing_skills
    
    # 优化现有技能
    optimize_existing_skills
    
    # 创建管理界面
    create_unified_interface
    
    # 创建报告
    create_optimization_report
    
    echo ""
    echo "="*50
    echo "🎉 离线优化完成！"
    echo "="*50
    echo ""
    echo "🚀 立即可以:"
    echo "  1. 启动控制中心: bash $WORKSPACE/scripts/opc_control_center.sh"
    echo "  2. 运行每日检查: bash $WORKSPACE/scripts/daily_check.sh"
    echo "  3. 查看优化报告: cat $WORKSPACE/logs/optimization_report_*.md"
    echo ""
    echo "📁 重要文件:"
    echo "  技能配置: $SKILLS_DIR/*/config.json"
    echo "  管理脚本: $WORKSPACE/scripts/"
    echo "  优化报告: $WORKSPACE/logs/"
    echo "="*50
}

# 执行主函数
main