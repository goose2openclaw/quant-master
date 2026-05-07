#!/bin/bash

echo "🦸 OpenClaw Skills终极获取方案"
echo "================================"

# 方法1: 直接从GitHub下载技能文件
direct_github_download() {
    echo "方法1: 直接从GitHub下载"
    
    SKILLS=("github" "cron" "shell")
    GITHUB_BASE="https://raw.githubusercontent.com/openclaw/skills/main"
    
    for skill in "${SKILLS[@]}"; do
        echo "下载: $skill"
        
        # 创建技能目录
        mkdir -p ~/.openclaw/workspace/skills/$skill
        
        # 下载SKILL.md
        curl -s "$GITHUB_BASE/$skill/SKILL.md" -o ~/.openclaw/workspace/skills/$skill/SKILL.md 2>/dev/null
        
        if [ -s ~/.openclaw/workspace/skills/$skill/SKILL.md ]; then
            echo "  ✅ $skill/SKILL.md 下载成功"
        else
            echo "  ❌ $skill 下载失败，使用备用方案"
            create_minimal_skill "$skill"
        fi
    done
}

# 方法2: 创建最小化技能
create_minimal_skill() {
    local skill=$1
    
    cat > ~/.openclaw/workspace/skills/$skill/SKILL.md << EOF
---
name: $skill
description: 最小化 $skill 技能（手动创建）
---

# $skill (最小化版本)

这是一个手动创建的最小化技能，用于临时替代。

## 基本功能
提供 $skill 的基本功能。

## 注意
这是一个临时解决方案，建议网络恢复后安装完整版本。
EOF
    
    echo "  ⚠ 已创建最小化 $skill 技能"
}

# 方法3: 使用OpenClaw工具替代
use_openclaw_tools() {
    echo -e "\n方法3: 使用OpenClaw内置工具替代"
    
    echo "以下技能可以用OpenClaw工具直接替代:"
    echo "1. 'brave-search' → 使用 'web_search' 工具"
    echo "2. 'agent-browser' → 使用 'browser' 工具"
    echo "3. 'whatsapp' → 使用 'telegram' 或 'message' 工具"
    echo "4. 'pdf/docx/xlsx/pptx' → 使用 'read'/'write' 工具处理文本"
    
    echo -e "\n示例:"
    echo "  # 搜索替代brave-search"
    echo "  web_search --query '加密货币行情'"
    echo ""
    echo "  # 浏览器控制替代agent-browser"
    echo "  browser --action open --url 'https://coingecko.com'"
}

# 方法4: 检查已安装技能
check_installed_skills() {
    echo -e "\n📊 当前已安装技能状态:"
    echo "="*50
    
    # 检查workspace技能
    echo "Workspace技能:"
    ls ~/.openclaw/workspace/skills/ 2>/dev/null | while read skill; do
        if [ -f ~/.openclaw/workspace/skills/$skill/SKILL.md ]; then
            echo "  ✓ $skill"
        fi
    done
    
    echo -e "\nBundled技能 (已启用):"
    openclaw skills list | grep "✓ ready" | head -10 | awk '{print "  ✓ "$2}'
    
    echo -e "\nBundled技能 (未启用):"
    openclaw skills list | grep "✗ missing" | head -10 | awk '{print "  ✗ "$2}'
}

# 方法5: 创建技能启用脚本
create_skill_enabler() {
    echo -e "\n方法5: 创建技能启用脚本"
    
    cat > ~/.openclaw/workspace/enable_all_skills.sh << 'EOF'
#!/bin/bash
echo "启用所有可用的技能..."

# 1. 启用workspace中的技能
for skill_dir in ~/.openclaw/workspace/skills/*/; do
    if [ -d "$skill_dir" ]; then
        skill=$(basename "$skill_dir")
        echo "检查: $skill"
        
        # 如果SKILL.md存在，尝试启用
        if [ -f "$skill_dir/SKILL.md" ]; then
            echo "  ✓ $skill 已就绪"
        fi
    fi
done

# 2. 检查bundled技能
echo -e "\n可启用的bundled技能:"
openclaw skills list | grep "openclaw-bundled" | grep "✗ missing" | awk '{print "  " $2 ": " $3}' | head -10

echo -e "\n启用命令示例:"
echo "  openclaw skills enable <skill-name>"
EOF
    
    chmod +x ~/.openclaw/workspace/enable_all_skills.sh
    echo "✅ 技能启用脚本已创建: ~/.openclaw/workspace/enable_all_skills.sh"
}

# 主函数
main() {
    echo "开始执行Skills终极获取方案..."
    echo "="*50
    
    # 检查网络
    if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
        echo "✅ 网络可用，尝试直接下载"
        direct_github_download
    else
        echo "⚠ 网络不可用，使用离线方案"
        for skill in github cron shell; do
            create_minimal_skill "$skill"
        done
    fi
    
    use_openclaw_tools
    check_installed_skills
    create_skill_enabler
    
    echo -e "\n" "="*50
    echo "🎯 下一步行动建议:"
    echo "1. 运行技能检查: bash ~/.openclaw/workspace/enable_all_skills.sh"
    echo "2. 测试自定义OPC技能"
    echo "3. 使用OpenClaw工具替代缺失技能"
    echo "4. 网络恢复后运行: bash /tmp/safe_batch_install.sh"
    echo "="*50
}

# 执行
main