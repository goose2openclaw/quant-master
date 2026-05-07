#!/bin/bash
# ClawPal健康检查脚本 (无需jq)

echo "=== ClawPal健康检查 (无jq版本) ==="
echo "开始时间: $(date)"
echo ""

# 检查OpenClaw进程
echo "=== GATEWAY ==="
OPENCLAW_PROCESSES=$(ps aux | grep -c "[o]penclaw")
echo "OpenClaw进程数: $OPENCLAW_PROCESSES"
if [ $OPENCLAW_PROCESSES -ge 1 ]; then
    echo "✅ OpenClaw运行中"
else
    echo "❌ OpenClaw未运行"
fi
echo ""

# 检查配置文件JSON格式
echo "=== CONFIG JSON ==="
if python3 -c "import json; json.load(open('/home/goose/.openclaw/openclaw.json'))" 2>/dev/null; then
    echo "✅ JSON格式正确"
else
    echo "❌ JSON格式错误"
fi
echo ""

# 使用Python解析channels
echo "=== CHANNELS ==="
python3 << 'PYTHON_END'
import json
import os

config_path = os.path.expanduser('~/.openclaw/openclaw.json')
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    channels = config.get('channels', {})
    for key, value in channels.items():
        policy = value.get('dmPolicy', 'n/a')
        enabled = value.get('enabled', 'implicit')
        print(f"{key}: policy={policy} enabled={enabled}")
        
except Exception as e:
    print(f"解析错误: {e}")
PYTHON_END
echo ""

# 使用Python解析plugins
echo "=== PLUGINS ==="
python3 << 'PYTHON_END'
import json
import os

config_path = os.path.expanduser('~/.openclaw/openclaw.json')
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    plugins = config.get('plugins', {}).get('entries', {})
    for key, value in plugins.items():
        enabled = value.get('enabled', False)
        print(f"{key}: {enabled}")
        
except Exception as e:
    print(f"解析错误: {e}")
PYTHON_END
echo ""

# 检查credentials
echo "=== CREDS ==="
# WhatsApp
whatsapp_dir="/home/goose/.openclaw/credentials/whatsapp/default/"
if [ -d "$whatsapp_dir" ]; then
    file_count=$(ls "$whatsapp_dir" 2>/dev/null | wc -l)
    echo "WhatsApp keys: $file_count files"
else
    echo "WhatsApp目录不存在"
fi

# Telegram
for d in /home/goose/.openclaw/credentials/telegram/*/; do
    if [ -d "$d" ]; then
        bot=$(basename "$d")
        if [ -f "$d/token.txt" ]; then
            echo "Telegram $bot: ✅ OK"
        else
            echo "Telegram $bot: ❌ MISSING"
        fi
    fi
done

# Bird cookies
if [ -f "/home/goose/.openclaw/credentials/bird/cookies.json" ]; then
    echo "Bird cookies: ✅ OK"
else
    echo "Bird cookies: ❌ MISSING"
fi
echo ""

# 检查cron
echo "=== CRON ==="
if [ -f "/home/goose/.openclaw/cron.json" ]; then
    cron_count=$(python3 -c "import json; data=json.load(open('/home/goose/.openclaw/cron.json')); print(len(data.get('jobs', [])))" 2>/dev/null || echo "0")
    echo "Cron任务数: $cron_count"
else
    echo "Cron文件不存在"
fi
echo ""

# 检查技能
echo "=== SKILLS ==="
skills_dir="/home/goose/.openclaw/workspace/.agents/skills"
if [ -d "$skills_dir" ]; then
    skill_count=$(find "$skills_dir" -maxdepth 1 -type d | wc -l)
    echo "技能总数: $((skill_count - 1))"
    
    # 检查高风险技能
    high_risk_skills=("crypto-report" "agent-reach" "code-simplifier" "ralph-loop" "evomap")
    echo "高风险技能检查:"
    for skill in "${high_risk_skills[@]}"; do
        if [ -d "$skills_dir/$skill" ]; then
            echo "  $skill: ✅ 已安装"
        else
            echo "  $skill: ❌ 未安装"
        fi
    done
else
    echo "技能目录不存在"
fi
echo ""

# 检查Mission Control
echo "=== MISSION CONTROL ==="
if curl -s http://localhost:8080 > /dev/null; then
    echo "Mission Control: ✅ 运行中 (http://localhost:8080)"
else
    echo "Mission Control: ❌ 未运行"
fi
echo ""

# 检查OpenClaw网关
echo "=== OPENCLAW GATEWAY ==="
if curl -s http://localhost:18789 > /dev/null; then
    echo "OpenClaw网关: ✅ 运行中 (http://localhost:18789)"
else
    echo "OpenClaw网关: ❌ 未运行"
fi
echo ""

# 系统资源
echo "=== SYSTEM RESOURCES ==="
echo "内存使用:"
ps aux --sort=-%mem | head -5 | grep -E "openclaw|mission"
echo ""
echo "磁盘空间:"
df -h /home/goose/.openclaw
echo ""

echo "=== 健康检查完成 ==="
echo "结束时间: $(date)"
echo ""
echo "📊 总结:"
echo "  1. 使用Python替代jq进行JSON解析"
echo "  2. 检查了所有关键系统组件"
echo "  3. 提供了完整的健康状态报告"
echo ""
echo "🎯 建议:"
echo "  1. 如需完整ClawPal功能，请安装jq: sudo apt-get install jq"
echo "  2. 定期运行此脚本监控系统健康"