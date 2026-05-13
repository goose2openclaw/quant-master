#!/bin/bash
while true; do
    echo "[$(date)] Running G19 Full (1000 agents)" >> /home/goose/.openclaw/workspace/logs/g19_loop.out
    python3 -u /home/goose/.openclaw/workspace/scripts/hermes_g19.py >> /home/goose/.openclaw/workspace/logs/g19_loop.out 2>&1
    echo "[$(date)] Completed, sleeping 600s" >> /home/goose/.openclaw/workspace/logs/g19_loop.out
    sleep 600
done
