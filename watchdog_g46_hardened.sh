#!/bin/bash
LOG="/home/goose/.openclaw/workspace/logs/watchdog.log"
SCRIPT_DIR="/home/goose/.openclaw/workspace"
CHECK_INTERVAL=30
STALE_THRESHOLD=600

log() { echo "[$(date '+%m-%d %H:%M:%S')] $1" >> $LOG; }

restart_g46_v6() {
    log "⚠️ 重启 G46 v7"
    pkill -f "g46_v8.py" 2>/dev/null; sleep 2
    cd $SCRIPT_DIR
    nohup env https_proxy=http://172.29.144.1:7897 http_proxy=http://172.29.144.1:7897 python3 -u skills/g44/g46_v8.py >> logs/g46_v8.log 2>&1 &
    log "已启动 PID=$!"
}

is_running() { pgrep -f "$1" > /dev/null 2>&1; }
is_stale() {
    [ -f "$SCRIPT_DIR/logs/${1}.log" ] || return 1
    age=$(($(date +%s) - $(stat -c %Y "$SCRIPT_DIR/logs/${1}.log" 2>/dev/null)))
    [ $age -gt $STALE_THRESHOLD ]
}

mkdir -p $SCRIPT_DIR/logs
log "看门狗强化版启动 PID=$"

while true; do
    if ! is_running "g46_v8.py"; then log "⚠️ G46已停止"; restart_g46_v6
    elif is_stale "g46_v8"; then log "⚠️ G46已僵死"; pkill -f "g46_v8.py"; sleep 2; restart_g46_v6
    fi
    sleep $CHECK_INTERVAL
done
