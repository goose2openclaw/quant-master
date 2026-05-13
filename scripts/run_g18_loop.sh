#!/bin/bash
while true; do
    echo "[$(date)] Running G18" >> /home/goose/.openclaw/workspace/logs/g18_loop.out
    python3 -u /home/goose/.openclaw/workspace/scripts/hermes_g18.py >> /home/goose/.openclaw/workspace/logs/g18_loop.out 2>&1
    echo "[$(date)] Completed, sleeping 300s" >> /home/goose/.openclaw/workspace/logs/g18_loop.out
    sleep 300
done
