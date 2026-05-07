#!/bin/bash

# OPC项目技能简化优化脚本（无需jq）

set -e

echo ""
echo "========================================"
echo "    OPC项目技能简化优化"
echo "========================================"
echo ""

SKILLS_DIR="/home/goose/.openclaw/workspace/skills"
CONFIG_DIR="/home/goose/.openclaw/workspace/config"
SCRIPTS_DIR="/home/goose/.openclaw/workspace/scripts"
OPC_PROJECT_DIR="/home/goose/opc-project"

# 创建必要目录
echo "创建必要目录..."
mkdir -p "$OPC_PROJECT_DIR/logs/telegram"
mkdir -p "$OPC_PROJECT_DIR/logs/whatsapp"
mkdir -p "$OPC_PROJECT_DIR/logs/system"
mkdir -p "$OPC_PROJECT_DIR/data"
mkdir -p "$OPC_PROJECT_DIR/backup"

echo "✅ 目录创建完成"
echo ""

# 优化Telegram配置
echo "优化Telegram配置..."
if [[ -d "$SKILLS_DIR/telegram" ]]; then
    cat > "$SKILLS_DIR/telegram/config.json" << 'EOF'
{
  "telegram": {
    "enabled": true,
    "botToken": "8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o",
    "configFile": "/home/goose/.openclaw/workspace/config/openclaw_opc.json",
    "performance": {
      "cacheEnabled": true,
      "cacheTTL": 300,
      "retryAttempts": 3,
      "timeout": 30000
    },
    "notifications": {
      "cryptoAlerts": true,
      "jobAlerts": true,
      "systemStatus": true
    },
    "optimized": "2026-02-28",
    "version": "2.0.0",
    "status": "optimized"
  }
}
EOF
    echo "✅ Telegram配置优化完成"
else
    echo "⚠️ Telegram技能目录不存在"
fi
echo ""

# 优化WhatsApp配置
echo "优化WhatsApp配置..."
if [[ -d "$SKILLS_DIR/whatsapp" ]]; then
    cat > "$SKILLS_DIR/whatsapp/config.json" << 'EOF'
{
  "whatsapp": {
    "enabled": true,
    "configFile": "/home/goose/.openclaw/workspace/config/whatsapp_config.json",
    "performance": {
      "cacheEnabled": true,
      "cacheTTL": 300,
      "retryAttempts": 3,
      "timeout": 30000
    },
    "setup": {
      "status": "needs_configuration",
      "configGuide": "请更新 ~/.openclaw/workspace/config/whatsapp_config.json"
    },
    "optimized": "2026-02-28",
    "version": "2.0.0",
    "status": "ready_for_config"
  }
}
EOF
    echo "✅ WhatsApp配置优化完成"
else
    echo "⚠️ WhatsApp技能目录不存在"
fi
echo ""

# 优化OPC自定义技能
echo "优化OPC自定义技能..."
OPC_SKILLS=("opc-crypto-monitor" "opc-job-assistant" "opc-smart-contract" "opc-trading-helper")

for skill in "${OPC_SKILLS[@]}"; do
    if [[ -d "$SKILLS_DIR/$skill" ]]; then
        cat > "$SKILLS_DIR/$skill/config.json" << EOF
{
  "$skill": {
    "enabled": true,
    "optimized": "2026-02-28",
    "performance": {
      "cacheEnabled": true,
      "cacheTTL": 600,
      "timeout": 30000
    },
    "integration": {
      "withTelegram": true,
      "withWhatsApp": true
    },
    "version": "2.0.0",
    "status": "optimized"
  }
}
EOF
        echo "✅ $skill 配置优化完成"
        
        # 创建日志目录
        mkdir -p "$OPC_PROJECT_DIR/logs/$skill"
    else
        echo "⚠️ $skill 目录不存在"
    fi
done
echo ""

# 创建技能启用脚本
echo "创建技能启用脚本..."
cat > "$SCRIPTS_DIR/enable_all_skills_simple.sh" << 'EOF'
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
EOF

chmod +x "$SCRIPTS_DIR/enable_all_skills_simple.sh"
echo "✅ 技能启用脚本创建完成"
echo ""

# 创建状态检查脚本
echo "创建状态检查脚本..."
cat > "$SCRIPTS_DIR/check_skills_simple.sh" << 'EOF'
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
EOF

chmod +x "$SCRIPTS_DIR/check_skills_simple.sh"
echo "✅ 状态检查脚本创建完成"
echo ""

# 更新OpenClaw主配置标记
echo "更新OpenClaw配置标记..."
if [[ -f "$CONFIG_DIR/openclaw_opc.json" ]]; then
    # 简单地在文件中添加优化标记
    if ! grep -q "optimized" "$CONFIG_DIR/openclaw_opc.json"; then
        sed -i 's/"description": ".*"/"description": "OPC项目专用OpenClaw配置 - 优化于2026-02-28"/g' "$CONFIG_DIR/openclaw_opc.json" 2>/dev/null || true
    fi
    echo "✅ 配置标记更新完成"
else
    echo "⚠️ OpenClaw主配置文件不存在"
fi
echo ""

# 生成报告
echo "生成优化报告..."
REPORT_FILE="$OPC_PROJECT_DIR/logs/skills_optimization_simple_$(date +%Y%m%d_%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
# OPC项目技能简化优化报告

## 优化时间
$(date)

## 优化内容
1. Telegram配置优化
2. WhatsApp配置优化  
3. OPC自定义技能优化
4. 创建管理脚本
5. 创建日志目录

## 创建的脚本
1. 技能启用: ~/.openclaw/workspace/scripts/enable_all_skills_simple.sh
2. 状态检查: ~/.openclaw/workspace/scripts/check_skills_simple.sh
3. WhatsApp测试: ~/.openclaw/workspace/scripts/test_whatsapp.sh

## 下一步操作
1. 启用所有技能:
   bash ~/.openclaw/workspace/scripts/enable_all_skills_simple.sh

2. 检查技能状态:
   bash ~/.openclaw/workspace/scripts/check_skills_simple.sh

3. 配置WhatsApp认证信息:
   编辑 ~/.openclaw/workspace/config/whatsapp_config.json

4. 测试Telegram连接（网络恢复后）

## 目录结构
- 项目目录: ~/opc-project/
- 技能目录: ~/.openclaw/workspace/skills/
- 配置目录: ~/.openclaw/workspace/config/
- 脚本目录: ~/.openclaw/workspace/scripts/
- 日志目录: ~/opc-project/logs/

## 状态
✅ 优化完成
🕒 $(date)
EOF

echo "✅ 优化报告生成完成: $REPORT_FILE"
echo ""

echo "========================================"
echo "🎉 技能简化优化完成！"
echo ""
echo "立即执行:"
echo "  1. 启用技能: bash $SCRIPTS_DIR/enable_all_skills_simple.sh"
echo "  2. 检查状态: bash $SCRIPTS_DIR/check_skills_simple.sh"
echo ""
echo "报告位置: $REPORT_FILE"
echo ""
echo "优化完成时间: $(date)"
echo "========================================"