#!/bin/bash
echo "启用混合安装的技能..."

for skill_dir in ~/.openclaw/workspace/skills/*/; do
    if [ -d "$skill_dir" ]; then
        skill=$(basename "$skill_dir")
        if [ -f "$skill_dir/SKILL.md" ]; then
            echo "检查: $skill"
            # 这里可以添加启用命令
            # openclaw skills enable "$skill"
        fi
    fi
done

echo "启用完成"
