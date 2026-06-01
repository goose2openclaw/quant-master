#!/bin/bash
# QuantMaster 看门狗脚本
cd /home/goose/.openclaw/workspace/quant_master

while true; do
    echo "[$(date)] Checking QuantMaster..."
    
    if pgrep -f "quant_master" > /dev/null; then
        echo "OK: QuantMaster running"
    else
        echo "WARN: Restarting QuantMaster..."
        nohup python3 api_server.py > logs/watchdog.log 2>&1 &
    fi
    
    MEM=$(ps aux | grep python3 | grep -v grep | awk '{sum+=$6} END {print sum/1024}')
    echo "Memory: ${MEM}MB"
    
    sleep 30
done
