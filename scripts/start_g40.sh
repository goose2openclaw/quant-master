#!/bin/bash
# G40 启动脚本

WORKSPACE="/home/goose/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs"
PID_FILE="$WORKSPACE/.g40.pid"

mkdir -p "$LOG_DIR"

# 停止旧进程
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "停止旧进程 $OLD_PID"
        kill $OLD_PID 2>/dev/null
        sleep 1
    fi
fi

# 启动G40
cd "$WORKSPACE"
nohup python3 skills/g40/g40.py >> logs/g40.log 2>&1 &
echo $! > "$PID_FILE"
echo "G40 PID: $(cat $PID_FILE)"
