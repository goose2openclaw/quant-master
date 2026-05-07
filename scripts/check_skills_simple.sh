#!/bin/bash

echo "=== OPC项目技能状态检查 ==="
echo "检查时间: $(date)"
echo ""

SKILLS_DIR="/home/goose/.openclaw/workspace/skills"

check_skill() {
    local skill=$1
    local skill_dir="$SKILLS_DIR/$skill"
    
    echo -n "$skill: "
    
    if [[ -d "$skill_dir" ]]; then
        if [[ -f "$skill_dir/config.json" ]]; then
            if grep -q '"enabled": true' "$skill_dir/config.json" || \
               grep -q '"enabled": "true"' "$skill_dir/config.json"; then
                echo "✅ 已启用"
            else
                echo "⚠️  已安装但未启用"
            fi
        else
            echo "⚠️  已安装但无配置"
        fi
    else
        echo "❌ 未安装"
    fi
}

echo "--- 核心技能 ---"
core_skills=("telegram" "whatsapp" "opc-crypto-monitor" "opc-job-assistant" "opc-smart-contract" "opc-trading-helper")
for skill in "${core_skills[@]}"; do
    check_skill "$skill"
done

echo ""
echo "--- 辅助技能 ---"
aux_skills=("github" "cron" "shell" "web-search" "calendar" "gmail" "obsidian" "weather")
for skill in "${aux_skills[@]}"; do
    check_skill "$skill"
done

echo ""
echo "=== 完成 ==="
echo "运行以下命令启用所有技能："
echo "  bash ~/.openclaw/workspace/scripts/enable_all_skills_simple.sh"
