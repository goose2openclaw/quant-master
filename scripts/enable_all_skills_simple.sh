#!/bin/bash

# 简单技能启用脚本

echo "启用所有OPC相关技能..."
echo ""

SKILLS_DIR="/home/goose/.openclaw/workspace/skills"

# 技能列表
SKILLS=(
    "telegram"
    "whatsapp"
    "opc-crypto-monitor"
    "opc-job-assistant"
    "opc-smart-contract"
    "opc-trading-helper"
    "github"
    "cron"
    "shell"
    "web-search"
    "calendar"
    "gmail"
    "obsidian"
    "weather"
)

for skill in "${SKILLS[@]}"; do
    config_file="$SKILLS_DIR/$skill/config.json"
    
    if [[ -f "$config_file" ]]; then
        # 启用技能（简单文本替换）
        sed -i 's/"enabled": false/"enabled": true/g' "$config_file" 2>/dev/null || true
        sed -i 's/"enabled": "false"/"enabled": "true"/g' "$config_file" 2>/dev/null || true
        
        # 如果文件中没有enabled字段，添加一个
        if ! grep -q '"enabled"' "$config_file"; then
            # 简单地在文件开头添加
            sed -i '1s/{/{\n  "'"$skill"'": {\n    "enabled": true,/g' "$config_file" 2>/dev/null || true
        fi
        
        echo "✅ 启用: $skill"
    else
        echo "⚠️  跳过: $skill (无配置文件)"
    fi
done

echo ""
echo "🎉 所有技能启用完成！"
echo ""
echo "下一步：重启OpenClaw使配置生效"
