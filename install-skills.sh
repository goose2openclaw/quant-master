#!/bin/bash

echo "开始安装OpenClaw技能..."

# 技能列表
SKILLS=(
    # 开发相关
    "mcp-builder"
    "using-superpowers" 
    "subagent-driven-development"
    "agent-tools"
    "vercel-react-best-practices"
    "agent-browser"
    
    # 办公文档
    "pptx"
    "pdf"
    "docx"
    "xlsx"
    
    # 网站相关
    "seo-audit"
    "audit-website"
    "copywriting"
    "webapp-testing"
    "baoyu-infographic"
    "frontend-design"
    "web-design-guidelines"
    
    # 思维工具
    "reflection"
    "executing-plan"
    "brainstorming"
    
    # 浏览器和搜索
    "agent-browser"
    "brave-search"
    
    # 系统工具
    "shell"
    "cron"
    "wake"
    
    # 通讯工具
    "whatsapp"
    "telegram"
    "gmail"
    
    # 开发协作
    "github"
    "notion"
    "obsidian"
    
    # 节点和硬件
    "nodes"
    
    # 社交媒体
    "twitter"
    "x"
    
    # 其他工具
    "calendar"
    "spotify"
)

# 安装函数
install_skill() {
    local skill=$1
    echo "正在安装: $skill"
    
    # 先搜索
    echo "搜索 $skill..."
    SEARCH_RESULT=$(clawhub search "$skill" 2>&1 | head -20)
    echo "搜索结果:"
    echo "$SEARCH_RESULT" | grep -E "(Install|Found|->)" || echo "未找到明确结果"
    
    # 尝试安装
    echo "尝试安装 $skill..."
    if clawhub install "$skill" --global --yes 2>&1 | grep -q "Installed"; then
        echo "✓ $skill 安装成功"
        return 0
    else
        echo "✗ $skill 安装失败"
        return 1
    fi
}

# 主安装循环
SUCCESS_COUNT=0
FAIL_COUNT=0

for skill in "${SKILLS[@]}"; do
    echo ""
    echo "========================================"
    install_skill "$skill"
    if [ $? -eq 0 ]; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
    sleep 1  # 避免请求过快
done

echo ""
echo "========================================"
echo "安装完成!"
echo "成功: $SUCCESS_COUNT"
echo "失败: $FAIL_COUNT"
echo "========================================"

# 显示已安装技能
echo ""
echo "已安装技能列表:"
openclaw skills list | grep "✓ ready" | head -30