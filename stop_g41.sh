#!/bin/bash
# G41 停止脚本

PID_FILE="/tmp/g41.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止 G41 (PID: $PID)..."
        kill $PID
        rm -f "$PID_FILE"
        echo "✅ G41 已停止"
    else
        echo "G41 未在运行"
        rm -f "$PID_FILE"
    fi
else
    # 尝试用 pgrep 查找
    PIDS=$(pgrep -f "python3.*g41.py")
    if [ -n "$PIDS" ]; then
        echo "停止 G41 (PIDs: $PIDS)..."
        echo "$PIDS" | xargs kill
        echo "✅ G41 已停止"
    else
        echo "G41 未在运行"
    fi
fi
