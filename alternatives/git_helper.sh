#!/bin/bash
# Git操作助手（替代github技能）

ACTION=$1
REPO=$2

case $ACTION in
    "clone")
        git clone "$REPO"
        ;;
    "status")
        git status
        ;;
    "pull")
        git pull
        ;;
    "push")
        git push
        ;;
    *)
        echo "用法: $0 <clone|status|pull|push> [repo_url]"
        ;;
esac
