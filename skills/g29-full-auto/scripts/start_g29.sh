#!/bin/bash
cd /home/goose/.openclaw/workspace
mkdir -p logs

# Kill existing instance
pkill -f g29_full.py 2>/dev/null
sleep 1

# Start new instance
nohup python3 scripts/g29_full.py > logs/g29.log 2>&1 &
echo "G29 Full Auto started"
echo "PID: $!"
echo "Logs: tail -f logs/g29.log"
