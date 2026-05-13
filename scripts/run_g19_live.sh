#!/bin/bash
while true; do
    echo "[$(date)] G19 Live" >> /home/goose/.openclaw/workspace/logs/g19_live.out
    python3 -u /home/goose/.openclaw/workspace/scripts/hermes_g19_live.py >> /home/goose/.openclaw/workspace/logs/g19_live.out 2>&1
    echo "[$(date)] Done, sleep 300s" >> /home/goose/.openclaw/workspace/logs/g19_live.out
    sleep 300
done
