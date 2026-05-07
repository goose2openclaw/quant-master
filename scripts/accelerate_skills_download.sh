#!/bin/bash

echo "🚀 OpenClaw Skills下载加速工具"
echo "================================"

# 颜色定义
RED='\033[0;31m'
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

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 检查网络连接
check_network() {
    print_section "检查网络连接"
    
    if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
        print_success "网络连接正常"
        return 0
    else
        print_error "网络连接失败"
        return 1
    fi
}

# 方法1: 优化clawhub配置
optimize_clawhub() {
    print_section "优化clawhub配置"
    
    # 创建优化配置
    cat > ~/.clawhubrc << 'EOF'
{
  "registry": "https://registry.openclaw.ai",
  "timeout": 60000,
  "retries": 5,
  "concurrency": 1,
  "cache": {
    "enabled": true,
    "ttl": 86400000,
    "path": "~/.clawhub-cache"
  },
  "proxy": null
}
EOF
    
    # 清理缓存
    rm -rf ~/.clawhub-cache 2>/dev/null
    mkdir -p ~/.clawhub-cache
    
    print_success "clawhub配置已优化"
}

# 方法2: 从OpenClaw自带技能启用
enable_bundled_skills() {
    print_section "启用OpenClaw自带技能"
    
    # 检查哪些bundled技能可用
    echo "可用的bundled技能:"
    openclaw skills list | grep "openclaw-bundled" | grep "✗ missing" | head -10
    
    # 创建启用脚本
    cat > /tmp/enable_bundled.sh << 'EOF'
#!/bin/bash
# 启用bundled技能的脚本

SKILLS_TO_ENABLE=(
    "github"
    "notion"
    "discord"
    "gifgrep"
    "himalaya"
    "blogwatcher"
    "camsnap"
    "canvas"
    "coding-agent"
    "gemini"
)

for skill in "${SKILLS_TO_ENABLE[@]}"; do
    echo "尝试启用: $skill"
    if openclaw skills list | grep -q "$skill.*✗ missing"; then
        echo "  $skill 未安装，需要先安装依赖"
    fi
done
EOF
    
    chmod +x /tmp/enable_bundled.sh
    print_success "bundled技能启用脚本已创建: /tmp/enable_bundled.sh"
}

# 方法3: 创建自定义技能（绕过下载）
create_custom_skills() {
    print_section "创建自定义技能（绕过下载限制）"
    
    CUSTOM_SKILLS=(
        "opc-crypto-monitor"
        "opc-trading-helper"
        "opc-job-assistant"
        "opc-smart-contract"
    )
    
    for skill in "${CUSTOM_SKILLS[@]}"; do
        SKILL_DIR="$HOME/.openclaw/workspace/skills/$skill"
        
        if [ ! -d "$SKILL_DIR" ]; then
            mkdir -p "$SKILL_DIR"
            mkdir -p "$SKILL_DIR/scripts"
            mkdir -p "$SKILL_DIR/references"
            
            # 创建SKILL.md
            cat > "$SKILL_DIR/SKILL.md" << EOF
---
name: $skill
description: OPC项目自定义技能 - $skill
---

# $skill

## 功能
OPC项目专用技能，用于加密货币监控、交易辅助等。

## 使用方法
\`\`\`bash
# 运行脚本
./scripts/${skill}.sh
\`\`\`

## 配置
编辑config.json进行配置
EOF
            
            # 创建示例脚本
            cat > "$SKILL_DIR/scripts/${skill}.sh" << 'EOF'
#!/bin/bash
echo "这是 $skill 的脚本"
echo "运行时间: $(date)"
echo "可以在这里添加具体功能"
EOF
            
            chmod +x "$SKILL_DIR/scripts/${skill}.sh"
            
            print_success "创建自定义技能: $skill"
        else
            print_warning "技能已存在: $skill"
        fi
    done
}

# 方法4: 使用替代方案
setup_alternatives() {
    print_section "设置功能替代方案"
    
    # 创建替代功能脚本
    ALTERNATIVES_DIR="$HOME/.openclaw/workspace/alternatives"
    mkdir -p "$ALTERNATIVES_DIR"
    
    # 1. 替代github技能
    cat > "$ALTERNATIVES_DIR/git_helper.sh" << 'EOF'
#!/bin/bash
# Git操作助手（替代github技能）

ACTION=$1
REPO=$2

case $ACTION in
    "clone")
        git clone "$REPO"
        ;;
    "status")
        git status
        ;;
    "pull")
        git pull
        ;;
    "push")
        git push
        ;;
    *)
        echo "用法: $0 <clone|status|pull|push> [repo_url]"
        ;;
esac
EOF
    
    # 2. 替代cron技能
    cat > "$ALTERNATIVES_DIR/scheduler.py" << 'EOF'
#!/usr/bin/env python3
"""
简单任务调度器（替代cron技能）
"""

import schedule
import time
from datetime import datetime

def job():
    print(f"任务执行时间: {datetime.now()}")

# 设置定时任务
schedule.every(10).minutes.do(job)
schedule.every().hour.do(job)
schedule.every().day.at("10:30").do(job)

print("任务调度器已启动...")
while True:
    schedule.run_pending()
    time.sleep(1)
EOF
    
    # 3. 替代shell技能
    cat > "$ALTERNATIVES_DIR/system_tools.sh" << 'EOF'
#!/bin/bash
# 系统工具集合（替代shell技能）

cmd=$1

case $cmd in
    "disk")
        df -h
        ;;
    "memory")
        free -h
        ;;
    "process")
        ps aux | head -20
        ;;
    "network")
        netstat -tulpn
        ;;
    *)
        echo "可用命令: disk, memory, process, network"
        ;;
esac
EOF
    
    chmod +x "$ALTERNATIVES_DIR"/*.sh
    chmod +x "$ALTERNATIVES_DIR"/*.py
    
    print_success "替代方案已创建: $ALTERNATIVES_DIR"
}

# 方法5: 批量安装尝试
batch_install_try() {
    print_section "尝试批量安装（谨慎使用）"
    
    print_warning "注意: 批量安装可能触发速率限制"
    print_warning "建议每次只安装1-2个技能，间隔10秒"
    
    # 创建安全的批量安装脚本
    cat > /tmp/safe_batch_install.sh << 'EOF'
#!/bin/bash
# 安全的批量安装脚本

SKILLS=(
    "github"
    "cron"
    "shell"
)

for skill in "${SKILLS[@]}"; do
    echo "安装: $skill"
    
    # 先检查是否已安装
    if openclaw skills list | grep -q "$skill.*✓ ready"; then
        echo "  ✓ 已安装"
        continue
    fi
    
    # 尝试安装
    if clawhub install "$skill" --force 2>&1 | grep -q "Installed"; then
        echo "  ✅ 安装成功"
    else
        echo "  ❌ 安装失败"
    fi
    
    # 等待避免速率限制
    echo "等待10秒..."
    sleep 10
done
EOF
    
    chmod +x /tmp/safe_batch_install.sh
    print_success "安全批量安装脚本已创建: /tmp/safe_batch_install.sh"
    print_warning "请手动运行: bash /tmp/safe_batch_install.sh"
}

# 主函数
main() {
    echo "开始优化Skills下载速度..."
    echo "="*50
    
    # 检查网络
    if ! check_network; then
        print_error "网络不可用，只能使用离线方案"
        echo ""
        echo "离线方案:"
        echo "1. 启用bundled技能"
        echo "2. 创建自定义技能"
        echo "3. 使用替代方案"
        echo ""
        
        enable_bundled_skills
        create_custom_skills
        setup_alternatives
        
        echo ""
        print_success "离线方案配置完成！"
        return 0
    fi
    
    # 网络可用，使用完整方案
    optimize_clawhub
    enable_bundled_skills
    create_custom_skills
    setup_alternatives
    batch_install_try
    
    echo ""
    echo "="*50
    print_success "Skills下载加速配置完成！"
    echo ""
    echo "🎯 推荐执行顺序:"
    echo "1. 运行安全批量安装: bash /tmp/safe_batch_install.sh"
    echo "2. 启用bundled技能: bash /tmp/enable_bundled.sh"
    echo "3. 测试自定义技能"
    echo "4. 如有需要，使用替代方案"
    echo ""
    echo "📊 当前技能状态:"
    openclaw skills list | grep -E "(✓ ready|✗ missing)" | head -15
    echo "="*50
}

# 执行主函数
main