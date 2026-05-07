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
