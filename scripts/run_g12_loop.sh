#!/bin/bash
# G12持续运行包装器
NAME=$1
SCRIPT=$2
INTERVAL=${3:-300}
WORKSPACE=/home/goose/.openclaw/workspace

while true; do
    echo "[$(date)] Running $NAME" >> $WORKSPACE/logs/${NAME}_loop.out
    python3 -u $WORKSPACE/scripts/$SCRIPT >> $WORKSPACE/logs/${NAME}_loop.out 2>&1
    echo "[$(date)] Completed, sleeping ${INTERVAL}s" >> $WORKSPACE/logs/${NAME}_loop.out
    sleep $INTERVAL
done
