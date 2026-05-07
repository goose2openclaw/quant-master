#!/bin/bash

echo "🚀 启动OPC Telegram Bot服务"
echo "============================"

# 配置路径
CONFIG_FILE="$HOME/.openclaw/workspace/skills/telegram/config/opc_bot.json"
LOG_FILE="$HOME/.openclaw/workspace/logs/telegram_bot.log"

# 检查配置
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    echo "请先运行配置脚本:"
    echo "  bash complete_telegram_setup.sh"
    exit 1
fi

# 加载配置
TOKEN=$(grep -o '"token":"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
CHAT_ID=$(grep -o '"chat_id":"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 配置文件中未找到Token"
    exit 1
fi

echo "✅ 配置加载成功"
echo "   Bot Token: ${TOKEN:0:10}...${TOKEN: -4}"
echo "   Chat ID: ${CHAT_ID:-未设置}"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 启动消息
START_MESSAGE="🔄 OPC Telegram Bot服务启动
时间: $(date '+%Y-%m-%d %H:%M:%S')
配置: $CONFIG_FILE
日志: $LOG_FILE"

echo "$START_MESSAGE" | tee -a "$LOG_FILE"

# 测试连接
echo -e "\n🔗 测试Bot连接..."
RESPONSE=$(curl -s "https://api.telegram.org/bot$TOKEN/getMe" 2>/dev/null || echo "{}")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    BOT_USERNAME=$(echo "$RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Bot连接成功: @$BOT_USERNAME"
    
    # 发送启动通知
    if [ -n "$CHAT_ID" ]; then
        echo -e "\n📤 发送启动通知..."
        NOTIFICATION="🚀 *OPC Telegram Bot已启动*
        
✅ *启动信息*
• 时间: $(date '+%Y-%m-%d %H:%M:%S')
• Bot: @$BOT_USERNAME
• 状态: 运行正常

📊 *服务状态*
• 连接: ✅ 正常
• 配置: ✅ 已加载
• 日志: ✅ 已启用

🔧 *可用命令*
• /status - 系统状态
• /crypto - 加密货币
• /jobs - 求职助手
• /help - 帮助信息

_服务启动完成，随时可用。_"
        
        curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
            -d "chat_id=$CHAT_ID" \
            -d "text=$NOTIFICATION" \
            -d "parse_mode=Markdown" >> "$LOG_FILE" 2>&1
        
        echo "✅ 启动通知已发送"
    fi
    
    # 启动监控服务（可选）
    echo -e "\n📊 启动监控服务..."
    nohup python3 "$HOME/.openclaw/workspace/scripts/monitor_skills.py" >> "$LOG_FILE" 2>&1 &
    
    echo -e "\n🎉 Telegram Bot服务启动完成!"
    echo "日志文件: $LOG_FILE"
    echo "监控服务: 已启动"
    echo "交互测试: python3 ~/.openclaw/workspace/scripts/test_telegram_interactive.py"
    
else
    echo "❌ Bot连接失败"
    echo "响应: $RESPONSE" | tee -a "$LOG_FILE"
    exit 1
fi
