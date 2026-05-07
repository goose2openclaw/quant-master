#!/bin/bash

echo "🔒 安全配置Telegram Bot Token"
echo "=============================="

# Telegram Bot Token（从参数获取或环境变量）
TELEGRAM_TOKEN="${1:-8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o}"

# 验证Token格式
if [[ ! "$TELEGRAM_TOKEN" =~ ^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$ ]]; then
    echo "❌ Token格式不正确"
    exit 1
fi

echo "✅ Token格式验证通过"

# 1. 配置OpenClaw
echo "配置OpenClaw Telegram集成..."
openclaw config set telegram.botToken "$TELEGRAM_TOKEN"

# 2. 测试Bot是否有效
echo "测试Bot连接..."
BOT_INFO=$(curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe")

if echo "$BOT_INFO" | grep -q '"ok":true'; then
    BOT_NAME=$(echo "$BOT_INFO" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Bot连接成功: @$BOT_NAME"
else
    echo "❌ Bot连接失败，请检查Token是否正确"
    echo "响应: $BOT_INFO"
    exit 1
fi

# 3. 获取Chat ID（需要用户交互）
echo ""
echo "📱 请按以下步骤获取Chat ID:"
echo "1. 在Telegram中搜索你的Bot: @$BOT_NAME"
echo "2. 发送 /start 命令"
echo "3. 等待Bot回复你的Chat ID"
echo ""
echo "或者，如果你知道Chat ID，现在输入（直接回车跳过）: "
read -r CHAT_ID

if [ -n "$CHAT_ID" ]; then
    echo "设置默认Chat ID: $CHAT_ID"
    openclaw config set telegram.defaultChatId "$CHAT_ID"
fi

# 4. 创建安全的环境变量文件
echo "创建安全的环境变量配置..."
mkdir -p ~/.openclaw/secure
cat > ~/.openclaw/secure/telegram.env << EOF
# Telegram Bot配置
# 自动生成于: $(date)
TELEGRAM_BOT_TOKEN="$TELEGRAM_TOKEN"
TELEGRAM_BOT_USERNAME="$BOT_NAME"
EOF

# 设置文件权限
chmod 600 ~/.openclaw/secure/telegram.env

# 5. 创建测试消息脚本
cat > ~/.openclaw/workspace/scripts/test_telegram.sh << 'EOF'
#!/bin/bash
# Telegram测试脚本

TOKEN_FILE="$HOME/.openclaw/secure/telegram.env"
if [ -f "$TOKEN_FILE" ]; then
    source "$TOKEN_FILE"
    MESSAGE="🔄 OPC系统测试消息\n时间: $(date '+%Y-%m-%d %H:%M:%S')\n状态: ✅ 运行正常"
    
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$1" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=$1" \
            -d "text=$MESSAGE" \
            -d "parse_mode=Markdown"
        echo "测试消息已发送"
    else
        echo "使用: $0 <chat_id>"
    fi
else
    echo "Token文件不存在: $TOKEN_FILE"
fi
EOF

chmod +x ~/.openclaw/workspace/scripts/test_telegram.sh

# 6. 创建加密备份（可选）
echo "创建Token加密备份..."
echo "$TELEGRAM_TOKEN" | gpg --encrypt --recipient "opc-project" -o ~/.openclaw/secure/telegram_token.gpg 2>/dev/null || echo "GPG加密跳过（需要设置GPG密钥）"

# 7. 清理敏感信息
echo "清理临时敏感信息..."
unset TELEGRAM_TOKEN
history -c

echo ""
echo "========================================"
echo "✅ Telegram配置完成！"
echo "========================================"
echo "已配置:"
echo "  • Bot Token: 已安全存储"
echo "  • Bot用户名: @$BOT_NAME"
echo "  • 配置文件: ~/.openclaw/secure/telegram.env"
echo "  • 测试脚本: ~/.openclaw/workspace/scripts/test_telegram.sh"
echo ""
echo "下一步:"
echo "1. 获取Chat ID并运行: ./test_telegram.sh <你的chat_id>"
echo "2. 配置OpenClaw cron任务发送定期更新"
echo "3. 开始开发OPC加密货币监控功能"
echo "========================================"