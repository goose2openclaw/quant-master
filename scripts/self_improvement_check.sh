#!/bin/bash
# 自我改进检查脚本
# 定期检查系统状态和学习进展

echo "🧠 自我改进检查 - $(date)"
echo "=================================="

# 1. 检查系统状态
echo "📊 1. 系统状态检查"
echo "----------------------------------"
openclaw status --brief

# 2. 检查技能状态
echo ""
echo "🛠️  2. 技能状态检查"
echo "----------------------------------"
total_skills=$(openclaw skills list | grep "✓ ready" | wc -l)
echo "已安装技能: $total_skills 个"

# 3. 检查音频处理系统
echo ""
echo "🎤 3. 音频处理系统检查"
echo "----------------------------------"
if command -v python3 &> /dev/null; then
    python3 -c "from faster_whisper import WhisperModel; print('✅ faster-whisper 可用')"
else
    echo "❌ Python3 未安装"
fi

if [ -d "/home/goose/.openclaw/media/inbound" ]; then
    audio_files=$(ls /home/goose/.openclaw/media/inbound/*.ogg 2>/dev/null | wc -l)
    echo "待处理音频文件: $audio_files 个"
fi

# 4. 检查记忆文件
echo ""
echo "📝 4. 记忆系统检查"
echo "----------------------------------"
if [ -f "/home/goose/.openclaw/workspace/memory/$(date +%Y-%m-%d).md" ]; then
    echo "✅ 今日记忆文件存在"
    lines=$(wc -l < "/home/goose/.openclaw/workspace/memory/$(date +%Y-%m-%d).md")
    echo "   行数: $lines"
else
    echo "⚠️  今日记忆文件不存在"
fi

if [ -f "/home/goose/.openclaw/workspace/MEMORY.md" ]; then
    echo "✅ 长期记忆文件存在"
fi

# 5. 检查Brave搜索
echo ""
echo "🔍 5. 搜索功能检查"
echo "----------------------------------"
if [ -f "/home/goose/.openclaw/workspace/.agents/skills/brave-search/search.js" ]; then
    echo "✅ Brave搜索技能可用"
    # 测试简单搜索
    cd /home/goose/.openclaw/workspace/.agents/skills/brave-search
    echo "   测试搜索中..."
    ./search.js "test" -n 1 2>&1 | grep -q "Result" && echo "✅ 搜索功能正常" || echo "⚠️  搜索可能有问题"
else
    echo "❌ Brave搜索技能不可用"
fi

# 6. 检查自我改进系统
echo ""
echo "🚀 6. 自我改进系统检查"
echo "----------------------------------"
if [ -f "/home/goose/.openclaw/workspace/.agents/skills/self-improving-agent/SKILL.md" ]; then
    echo "✅ 自我改进技能已安装"
    
    # 检查语义记忆
    if [ -f "/home/goose/.openclaw/workspace/.agents/skills/self-improving-agent/memory/semantic-patterns.json" ]; then
        pattern_count=$(jq '.patterns | length' "/home/goose/.openclaw/workspace/.agents/skills/self-improving-agent/memory/semantic-patterns.json" 2>/dev/null || echo "0")
        echo "   语义模式数量: $pattern_count"
    fi
else
    echo "❌ 自我改进技能未安装"
fi

# 7. 用户偏好检查
echo ""
echo "👤 7. 用户偏好检查"
echo "----------------------------------"
if [ -f "/home/goose/.openclaw/workspace/USER.md" ]; then
    echo "✅ 用户档案存在"
    user_info=$(grep -c "Name\|Timezone\|Project" "/home/goose/.openclaw/workspace/USER.md")
    echo "   信息条目: $user_info 个"
else
    echo "⚠️  用户档案不存在或为空"
fi

# 8. 生成改进建议
echo ""
echo "💡 8. 改进建议"
echo "----------------------------------"
echo "基于当前检查，建议："

# 检查是否需要更新记忆
if [ ! -f "/home/goose/.openclaw/workspace/memory/$(date +%Y-%m-%d).md" ]; then
    echo "1. 📝 创建今日记忆文件"
fi

# 检查技能数量
if [ "$total_skills" -lt 20 ]; then
    echo "2. 🛠️  安装更多技能（当前: $total_skills）"
fi

# 检查音频处理
if ! command -v python3 &> /dev/null; then
    echo "3. 🐍 安装Python3"
fi

# 检查搜索功能
if [ ! -f "/home/goose/.openclaw/workspace/.agents/skills/brave-search/search.js" ]; then
    echo "4. 🔍 安装或修复Brave搜索"
fi

# 检查自我改进
if [ ! -f "/home/goose/.openclaw/workspace/.agents/skills/self-improving-agent/SKILL.md" ]; then
    echo "5. 🧠 安装自我改进技能"
fi

echo ""
echo "=================================="
echo "✅ 检查完成于: $(date)"
echo ""
echo "📋 总结:"
echo "   - 系统状态: $(openclaw status --brief | grep -o 'running\|stopped' | head -1)"
echo "   - 技能数量: $total_skills"
echo "   - 音频处理: $(command -v python3 &> /dev/null && echo '就绪' || echo '需配置')"
echo "   - 搜索功能: $([ -f "/home/goose/.openclaw/workspace/.agents/skills/brave-search/search.js" ] && echo '就绪' || echo '需配置')"
echo "   - 自我改进: $([ -f "/home/goose/.openclaw/workspace/.agents/skills/self-improving-agent/SKILL.md" ] && echo '已安装' || echo '未安装')"

# 保存检查结果
check_file="/home/goose/.openclaw/workspace/logs/self_improvement_check_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "/home/goose/.openclaw/workspace/logs"
{
    echo "自我改进检查报告 - $(date)"
    echo "=================================="
    openclaw status --brief
    echo ""
    echo "技能数量: $total_skills"
    echo "音频文件: $audio_files"
    echo "语义模式: $pattern_count"
} > "$check_file"

echo ""
echo "📄 详细报告保存到: $check_file"