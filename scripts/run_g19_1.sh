#!/bin/bash
while true; do
    echo "[$(date)] G19.1 Hybrid" >> /home/goose/.openclaw/workspace/logs/g19_1_loop.out
    python3 -u /home/goose/.openclaw/workspace/scripts/hermes_g19_1.py >> /home/goose/.openclaw/workspace/logs/g19_1_loop.out 2>&1
    echo "[$(date)] Done, sleep 300s" >> /home/goose/.openclaw/workspace/logs/g19_1_loop.out
    sleep 300
done
