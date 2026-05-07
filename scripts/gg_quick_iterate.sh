#!/bin/bash
# 快速迭代脚本 - 交易后立即调用
# 用法: bash gg_quick_iterate.sh "交易描述"
SCRIPT="$HOME/.openclaw/workspace/scripts/gg_hermes_auto_iterate.sh"
bash $SCRIPT 2>&1 | tail -20
