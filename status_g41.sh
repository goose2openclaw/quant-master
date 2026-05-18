#!/bin/bash
# G41 状态检查脚本

LOG_FILE="/home/goose/.openclaw/workspace/logs/g41.log"
PID_FILE="/tmp/g41.pid"

echo "=================================="
echo "       G41 状态检查"
echo "=================================="

# 检查进程
if pgrep -f "python3.*g41.py" > /dev/null; then
    echo "状态: ✅ 运行中"
    echo ""
    echo "进程:"
    pgrep -f "python3.*g41.py" | while read pid; do
        ps -p $pid -o pid,etime,cmd --no-headers
    done
else
    echo "状态: ❌ 未运行"
fi

echo ""
echo "最近日志:"
if [ -f "$LOG_FILE" ]; then
    tail -10 "$LOG_FILE"
else
    echo "无日志文件"
fi
