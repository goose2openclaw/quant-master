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
