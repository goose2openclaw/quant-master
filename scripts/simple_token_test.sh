#!/bin/bash

echo "🔍 简单测试Telegram Token"
echo "========================"

TOKEN="8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o"

echo "Token: $TOKEN"
echo "长度: ${#TOKEN} 字符"
echo ""

# 检查格式
if [[ ! "$TOKEN" =~ ^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$ ]]; then
    echo "❌ Token格式不正确"
    echo "正确格式: 数字:字母数字组合(35字符)"
    exit 1
else
    echo "✅ Token格式正确"
fi

# 简单curl测试
echo -e "\n🌐 测试网络连接..."
if ping -c 1 -W 2 api.telegram.org &> /dev/null; then
    echo "✅ Telegram API可达"
    
    echo -e "\n🤖 测试Bot连接..."
    RESPONSE=$(curl -s "https://api.telegram.org/bot$TOKEN/getMe" 2>/dev/null || echo "{}")
    
    echo "原始响应:"
    echo "$RESPONSE" | head -5
    
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        echo -e "\n✅ Bot连接成功!"
        BOT_USERNAME=$(echo "$RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
        echo "Bot用户名: @$BOT_USERNAME"
    else
        ERROR=$(echo "$RESPONSE" | grep -o '"description":"[^"]*"' | cut -d'"' -f4)
        echo -e "\n❌ Bot连接失败: $ERROR"
        
        # 常见错误
        case $ERROR in
            "Unauthorized")
                echo "可能原因:"
                echo "1. Token已失效"
                echo "2. Token被撤销"
                echo "3. Bot已被删除"
                echo ""
                echo "解决方案:"
                echo "1. 在Telegram中联系 @BotFather"
                echo "2. 创建新的Bot"
                echo "3. 获取新的Token"
                ;;
            "Not Found")
                echo "可能原因: Token格式错误"
                ;;
            *)
                echo "未知错误，请检查网络和Token"
                ;;
        esac
    fi
else
    echo "❌ 无法连接到Telegram API"
    echo "请检查网络连接"
fi

echo -e "\n💡 建议:"
echo "1. 确认Token是否正确复制"
echo "2. 在Telegram中检查Bot是否还存在"
echo "3. 联系 @BotFather 获取新Token"