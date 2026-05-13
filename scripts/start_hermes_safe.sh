#!/bin/bash
# Hermes安全启动脚本 - 避免exec preflight问题
# 使用直接Python调用,不通过heredoc

WORKSPACE='/home/goose/.openclaw/workspace'
LOG_DIR="$WORKSPACE/logs"
PID_DIR="$WORKSPACE/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

echo "[$(date)] Hermes安全启动开始"

# 启动看门狗
if ! pgrep -f "watchdog_hermes.py" > /dev/null; then
    echo "启动看门狗..."
    cd "$WORKSPACE"
    nohup python3 "$WORKSPACE/scripts/watchdog_hermes.py" > "$LOG_DIR/watchdog.out" 2>&1 &
    echo $! > "$PID_DIR/watchdog_hermes.pid"
    echo "看门狗 PID: $(cat $PID_DIR/watchdog_hermes.pid)"
else
    echo "看门狗已在运行"
fi

# 启动G12自动循环(如果存在)
if [ -f "$WORKSPACE/scripts/hermes_g12_autoloop_v4.py" ]; then
    if ! pgrep -f "hermes_g12_autoloop_v4.py" > /dev/null; then
        echo "启动G12自动循环..."
        cd "$WORKSPACE"
        nohup python3 "$WORKSPACE/scripts/hermes_g12_autoloop_v4.py" > "$LOG_DIR/g12_autoloop.out" 2>&1 &
        echo $! > "$PID_DIR/hermes_g12_autoloop.pid"
        echo "G12 PID: $(cat $PID_DIR/hermes_g12_autoloop.pid)"
    else
        echo "G12已在运行"
    fi
fi

# 启动G16(如果存在)
if [ -f "$WORKSPACE/scripts/hermes_g16.py" ]; then
    if ! pgrep -f "hermes_g16.py" > /dev/null; then
        echo "启动G16..."
        cd "$WORKSPACE"
        nohup python3 "$WORKSPACE/scripts/hermes_g16.py" > "$LOG_DIR/g16.out" 2>&1 &
        echo $! > "$PID_DIR/hermes_g16.pid"
        echo "G16 PID: $(cat $PID_DIR/hermes_g16.pid)"
    else
        echo "G16已在运行"
    fi
fi

echo "[$(date)] Hermes安全启动完成"
echo ""
echo "=== 当前运行状态 ==="
ps aux | grep -E "(watchdog|hermes_g12|hermes_g16)" | grep -v grep
