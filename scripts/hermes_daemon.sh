#!/bin/bash
LOG_DIR="/tmp/hermes_daemon"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/hermes.log"
MAX_CPU=30; MAX_MEM=500; SLEEP=180
echo "Hermes v2.10.1 Daemon启动 $(date)"
while true; do
    echo "======== $(date) ========" >> $LOG_FILE
    bash ~/.openclaw/workspace/scripts/hermes_v32.sh >> $LOG_FILE 2>&1
    echo "休眠${SLEEP}秒..." >> $LOG_FILE
    sleep $SLEEP
done
