#!/bin/bash

echo "开始安装OpenClaw技能（简化版）..."

# 先安装一些基础技能
BASIC_SKILLS=(
    "shell"
    "cron"
    "github"
    "telegram"
    "whatsapp"
    "gmail"
    "calendar"
    "notion"
    "obsidian"
    "twitter"
)

# 开发技能
DEV_SKILLS=(
    "vercel-react-best-practices"
    "frontend-design"
    "web-design-guidelines"
    "webapp-testing"
)

# 文档技能
DOC_SKILLS=(
    "pptx"
    "docx"
    "xlsx"
)

install_with_force() {
    local skill=$1
    echo "安装: $skill"
    clawhub install "$skill" --force 2>&1 | grep -E "(Installed|Resolving|Warning|Error)" || echo "安装完成"
    echo ""
}

# 安装基础技能
echo "=== 安装基础技能 ==="
for skill in "${BASIC_SKILLS[@]}"; do
    install_with_force "$skill"
    sleep 1
done

# 安装开发技能  
echo "=== 安装开发技能 ==="
for skill in "${DEV_SKILLS[@]}"; do
    install_with_force "$skill"
    sleep 1
done

# 安装文档技能
echo "=== 安装文档技能 ==="
for skill in "${DOC_SKILLS[@]}"; do
    install_with_force "$skill"
    sleep 1
done

echo "安装完成!"
echo ""
echo "已安装技能:"
ls -la ~/.openclaw/workspace/skills/ 2>/dev/null || echo "技能目录为空"