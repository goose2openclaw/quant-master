#!/bin/bash
# G41 Polymarket增强版启动脚本
# 用法: ./start_g41.sh

LOG_DIR="/home/goose/.openclaw/workspace/logs"
SKILL_DIR="/home/goose/.openclaw/workspace/skills/g41"
LOG_FILE="$LOG_DIR/g41.log"
PID_FILE="/tmp/g41.pid"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查是否已运行
if pgrep -f "python3.*g41.py" > /dev/null; then
    echo "G41 已在运行!"
    pgrep -f "python3.*g41.py" | xargs ps -p
    exit 1
fi

# 启动G41
echo "启动 G41 Polymarket增强版..."
cd /home/goose/.openclaw/workspace

nohup python3 "$SKILL_DIR/g41.py" > "$LOG_FILE" 2>&1 &
PID=$!

echo $PID > "$PID_FILE"
echo "G41 已启动! PID: $PID"
echo "日志文件: $LOG_FILE"

# 等待2秒检查是否启动成功
sleep 2
if ps -p $PID > /dev/null; then
    echo "✅ G41 运行正常"
    tail -5 "$LOG_FILE"
else
    echo "❌ G41 启动失败"
    exit 1
fi
