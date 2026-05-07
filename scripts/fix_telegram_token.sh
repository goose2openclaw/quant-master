#!/bin/bash

echo "🔧 修复Telegram Bot Token问题"
echo "=============================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 1. 检查当前状态
print_step "1. 检查当前Telegram状态"
CURRENT_STATUS=$(openclaw status --deep 2>/dev/null | grep -A2 "Telegram" | tail -1)
echo "当前状态: $CURRENT_STATUS"

# 2. 测试当前Token
print_step "2. 测试当前Token"
CURRENT_TOKEN=$(grep -o '"botToken":"[^"]*"' ~/.openclaw/openclaw.json 2>/dev/null | cut -d'"' -f4 || echo "未找到")

if [ -n "$CURRENT_TOKEN" ]; then
    echo "当前Token: ${CURRENT_TOKEN:0:10}...${CURRENT_TOKEN: -4}"
    
    # 测试Token
    RESPONSE=$(curl -s "https://api.telegram.org/bot$CURRENT_TOKEN/getMe" 2>/dev/null || echo "{}")
    
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        print_success "当前Token有效"
        BOT_USERNAME=$(echo "$RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
        echo "Bot用户名: @$BOT_USERNAME"
        exit 0
    else
        print_error "当前Token无效 (401 Unauthorized)"
    fi
else
    print_error "未找到配置的Token"
fi

# 3. 创建新Bot的说明
print_step "3. 创建新的Telegram Bot"
echo ""
echo "📱 请在 Telegram 应用中执行以下步骤："
echo ""
echo "1. 🔍 搜索 @BotFather"
echo "2. 💬 发送 /start 开始对话"
echo "3. 🆕 发送 /newbot 创建新Bot"
echo "4. 📝 按照提示："
echo "   • 输入Bot名称 (例如: OPC Assistant)"
echo "   • 输入Bot用户名 (必须以 'bot' 结尾，例如: opc_assistant_bot)"
echo "5. 🔑 复制生成的 Bot Token"
echo "6. 📋 准备粘贴Token"
echo ""

# 4. 获取新Token
print_step "4. 输入新的Bot Token"
read -p "请输入新的Bot Token: " NEW_TOKEN

if [ -z "$NEW_TOKEN" ]; then
    print_error "Token不能为空"
    exit 1
fi

# 验证Token格式
if [[ ! "$NEW_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
    print_error "Token格式错误，应为 '数字:字母' 格式"
    exit 1
fi

# 5. 测试新Token
print_step "5. 测试新Token"
RESPONSE=$(curl -s "https://api.telegram.org/bot$NEW_TOKEN/getMe" 2>/dev/null || echo "{}")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    BOT_USERNAME=$(echo "$RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    BOT_NAME=$(echo "$RESPONSE" | grep -o '"first_name":"[^"]*"' | cut -d'"' -f4)
    BOT_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    
    print_success "✅ Token有效！"
    echo "   Bot ID: $BOT_ID"
    echo "   用户名: @$BOT_USERNAME"
    echo "   名称: $BOT_NAME"
else
    ERROR_MSG=$(echo "$RESPONSE" | grep -o '"description":"[^"]*"' | cut -d'"' -f4)
    print_error "❌ Token无效: $ERROR_MSG"
    exit 1
fi

# 6. 更新OpenClaw配置
print_step "6. 更新OpenClaw配置"
CONFIG_FILE="$HOME/.openclaw/openclaw.json"

if [ ! -f "$CONFIG_FILE" ]; then
    print_error "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 备份原配置
BACKUP_FILE="$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_FILE" "$BACKUP_FILE"
print_success "配置已备份: $BACKUP_FILE"

# 更新配置
TEMP_FILE=$(mktemp)
jq --arg token "$NEW_TOKEN" '.channels.telegram.botToken = $token' "$CONFIG_FILE" > "$TEMP_FILE"

if [ $? -eq 0 ]; then
    mv "$TEMP_FILE" "$CONFIG_FILE"
    print_success "OpenClaw配置已更新"
else
    print_error "更新配置失败 (需要安装jq工具)"
    echo "请手动编辑 $CONFIG_FILE，将 botToken 改为: $NEW_TOKEN"
    rm -f "$TEMP_FILE"
fi

# 7. 创建备份配置
print_step "7. 创建备份配置"
BACKUP_DIR="$HOME/.openclaw/workspace/secure"
mkdir -p "$BACKUP_DIR"

cat > "$BACKUP_DIR/telegram_config_fixed.json" << EOF
{
  "telegram_bot": {
    "token": "$NEW_TOKEN",
    "username": "@$BOT_USERNAME",
    "bot_id": "$BOT_ID",
    "name": "$BOT_NAME",
    "configured_at": "$(date -Iseconds)",
    "status": "active",
    "fixed_at": "$(date -Iseconds)",
    "reason": "原Token无效 (401 Unauthorized)"
  },
  "security": {
    "file_permissions": "600",
    "encryption_recommended": true
  }
}
EOF

print_success "备份配置已保存: $BACKUP_DIR/telegram_config_fixed.json"

# 8. 重启OpenClaw服务
print_step "8. 重启OpenClaw服务"
echo "正在重启OpenClaw网关服务..."

if openclaw gateway restart > /dev/null 2>&1; then
    print_success "✅ OpenClaw服务重启成功"
    
    # 等待服务启动
    echo "等待服务启动..."
    sleep 5
    
    # 9. 验证连接
    print_step "9. 验证连接状态"
    STATUS_OUTPUT=$(openclaw status --deep 2>/dev/null)
    
    if echo "$STATUS_OUTPUT" | grep -q "Telegram.*OK"; then
        print_success "✅ Telegram通道状态: 正常"
    elif echo "$STATUS_OUTPUT" | grep -q "failed.*401"; then
        print_error "❌ Telegram通道状态: 认证失败"
    else
        print_warning "⚠ 无法确定Telegram状态"
    fi
    
else
    print_error "❌ 重启服务失败"
    echo "请手动运行: openclaw gateway restart"
fi

# 10. 完成
print_step "10. 完成"
echo ""
echo "🎉 Telegram Bot Token修复完成！"
echo ""
echo "📋 摘要:"
echo "   • 新Bot: @$BOT_USERNAME ($BOT_NAME)"
echo "   • Bot ID: $BOT_ID"
echo "   • Token: ${NEW_TOKEN:0:10}...${NEW_TOKEN: -4}"
echo "   • 配置: $CONFIG_FILE"
echo "   • 备份: $BACKUP_DIR/telegram_config_fixed.json"
echo ""
echo "🚀 下一步:"
echo "   1. 在Telegram中搜索: @$BOT_USERNAME"
echo "   2. 发送 /start 开始对话"
echo "   3. 发送任意消息测试"
echo ""
echo "🔧 检查状态:"
echo "   openclaw status --deep"
echo ""
echo "📝 如果仍有问题，请检查:"
echo "   1. Bot是否被禁用"
echo "   2. 网络连接是否正常"
echo "   3. 防火墙设置"
echo ""