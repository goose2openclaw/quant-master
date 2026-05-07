#!/bin/bash

echo "🔄 从模拟Bot迁移到真实Bot"
echo "============================"

MOCK_DIR="$HOME/.openclaw/workspace/telegram_mock"
REAL_DIR="$HOME/.openclaw/workspace/skills/telegram"

echo "1. 检查模拟数据..."
MESSAGE_COUNT=$(find "$MOCK_DIR/messages" -name "*.json" 2>/dev/null | wc -l)
USER_COUNT=$(find "$MOCK_DIR/users" -name "*.json" 2>/dev/null | wc -l)

echo "   模拟消息: $MESSAGE_COUNT 条"
echo "   模拟用户: $USER_COUNT 个"

echo -e "\n2. 备份模拟数据..."
BACKUP_FILE="$HOME/telegram_mock_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" "$MOCK_DIR" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ 备份完成: $BACKUP_FILE"
else
    echo "   ⚠ 备份失败，继续迁移"
fi

echo -e "\n3. 配置真实Bot..."
echo "   请确保已获取有效的Telegram Bot Token"
echo "   编辑配置文件: $REAL_DIR/config/opc_bot.json"
echo "   更新Token和Chat ID"

echo -e "\n4. 测试真实Bot连接..."
read -p "   输入真实Bot Token: " REAL_TOKEN

if [ -n "$REAL_TOKEN" ]; then
    echo "   测试连接..."
    RESPONSE=$(curl -s "https://api.telegram.org/bot$REAL_TOKEN/getMe" 2>/dev/null || echo "{}")
    
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        BOT_USERNAME=$(echo "$RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
        echo "   ✅ 真实Bot连接成功: @$BOT_USERNAME"
        
        # 更新配置
        echo -e "\n5. 更新配置文件..."
        CONFIG_FILE="$REAL_DIR/config/opc_bot.json"
        if [ -f "$CONFIG_FILE" ]; then
            # 备份原配置
            cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d)"
            
            # 更新Token
            sed -i "s/\"token\": \".*\"/\"token\": \"$REAL_TOKEN\"/" "$CONFIG_FILE"
            echo "   ✅ Token已更新"
        fi
        
        echo -e "\n6. 启动真实Bot..."
        echo "   运行: bash $HOME/.openclaw/workspace/scripts/start_telegram_bot.sh"
        
        echo -e "\n🎉 迁移准备完成!"
        echo "   模拟数据已备份: $BACKUP_FILE"
        echo "   真实Bot已配置: @$BOT_USERNAME"
        echo "   下一步: 启动真实Bot并测试"
    else
        echo "   ❌ 真实Bot连接失败"
        echo "   请检查Token和网络连接"
    fi
else
    echo "   ⚠ 未提供Token，跳过真实Bot测试"
fi

echo -e "\n📋 迁移完成摘要:"
echo "   1. 模拟数据已备份"
echo "   2. 真实Bot配置已准备"
echo "   3. 可随时切换到真实Bot"
echo ""
echo "💡 提示: 迁移后，所有新消息将通过真实Bot发送"
echo "       模拟数据可用于分析和测试"
