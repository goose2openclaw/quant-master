#!/bin/bash

echo "🤖 启动Telegram模拟Bot测试"
echo "============================"

MOCK_DIR="$HOME/.openclaw/workspace/telegram_mock"

if [ ! -f "$MOCK_DIR/mock_handler.py" ]; then
    echo "❌ 模拟系统未初始化"
    echo "请先运行: bash telegram_mock_system.sh"
    exit 1
fi

echo "✅ 模拟系统已就绪"
echo "目录: $MOCK_DIR"
echo ""

# 启动交互式模拟
python3 "$MOCK_DIR/mock_handler.py"
