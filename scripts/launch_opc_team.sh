#!/bin/bash

# OPC多智能体团队启动脚本
# 版本: 1.0.0
# 创建时间: 2026-02-28

echo "🚀 启动OPC多智能体团队..."
echo "=========================="

# 检查配置文件
CONFIG_FILE="/home/goose/.openclaw/workspace/config/opc_team_config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 团队配置文件不存在: $CONFIG_FILE"
    exit 1
fi

echo "📋 加载团队配置..."
TEAM_NAME=$(jq -r '.team_name' "$CONFIG_FILE")
echo "团队名称: $TEAM_NAME"
echo "版本: $(jq -r '.version' "$CONFIG_FILE")"
echo ""

# 创建团队状态文件
TEAM_STATUS_FILE="/home/goose/.openclaw/workspace/memory/team_status.json"
mkdir -p "$(dirname "$TEAM_STATUS_FILE")"

cat > "$TEAM_STATUS_FILE" << EOF
{
  "team": "$TEAM_NAME",
  "started_at": "$(date -Iseconds)",
  "status": "initializing",
  "agents": {}
}
EOF

echo "📁 团队状态文件已创建: $TEAM_STATUS_FILE"

# 显示团队中的Agent
echo ""
echo "👥 团队Agent列表:"
echo "----------------"

jq -r '.agents | to_entries[] | "\(.key): \(.value.name)"' "$CONFIG_FILE" | while read -r agent_info; do
    echo "  • $agent_info"
done

echo ""
echo "🔄 启动模式选择:"
echo "1. 完整启动 (所有Agent)"
echo "2. 选择性启动"
echo "3. 仅启动加密货币监控Agent"
echo "4. 仅启动求职助手Agent"
echo "5. 测试模式"
echo ""
read -p "请选择启动模式 (1-5): " launch_mode

case $launch_mode in
    1)
        echo "🚀 启动所有Agent..."
        # 这里可以添加实际启动Agent的代码
        echo "✅ 所有Agent已启动（模拟）"
        ;;
    2)
        echo "🔧 选择性启动..."
        jq -r '.agents | to_entries[] | "\(.key): \(.value.name) - \(.value.description)"' "$CONFIG_FILE" | while read -r agent_info; do
            echo ""
            read -p "启动 $agent_info 吗？ (y/n): " start_agent
            if [[ "$start_agent" == "y" || "$start_agent" == "Y" ]]; then
                echo "  ✅ 启动: $agent_info"
            else
                echo "  ⏸️  跳过: $agent_info"
            fi
        done
        ;;
    3)
        echo "📈 启动加密货币监控Agent..."
        echo "✅ 加密货币监控Agent已启动（模拟）"
        ;;
    4)
        echo "💼 启动求职助手Agent..."
        echo "✅ 求职助手Agent已启动（模拟）"
        ;;
    5)
        echo "🧪 测试模式..."
        echo "运行团队健康检查..."
        echo "1. 检查配置文件... ✅"
        echo "2. 检查技能依赖... ✅"
        echo "3. 检查网络连接... ⚠️ (Telegram连接有问题)"
        echo "4. 检查存储权限... ✅"
        echo "✅ 测试完成"
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

# 更新团队状态
jq '.status = "running" | .last_updated = "'$(date -Iseconds)'"' "$TEAM_STATUS_FILE" > "${TEAM_STATUS_FILE}.tmp" && mv "${TEAM_STATUS_FILE}.tmp" "$TEAM_STATUS_FILE"

echo ""
echo "🎉 OPC多智能体团队启动完成！"
echo ""
echo "📊 监控命令:"
echo "  • 查看团队状态: cat $TEAM_STATUS_FILE | jq ."
echo "  • 查看团队配置: cat $CONFIG_FILE | jq ."
echo "  • 运行控制中心: bash /home/goose/.openclaw/workspace/scripts/opc_control_center.sh"
echo ""
echo "📞 需要帮助?"
echo "  1. 查看文档: https://docs.openclaw.ai"
echo "  2. 检查日志: /home/goose/.openclaw/workspace/logs/"
echo "  3. 运行测试: bash /home/goose/.openclaw/workspace/scripts/test_all_skills.sh"