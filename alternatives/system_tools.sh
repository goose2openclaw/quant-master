#!/bin/bash
# 系统工具集合（替代shell技能）

cmd=$1

case $cmd in
    "disk")
        df -h
        ;;
    "memory")
        free -h
        ;;
    "process")
        ps aux | head -20
        ;;
    "network")
        netstat -tulpn
        ;;
    *)
        echo "可用命令: disk, memory, process, network"
        ;;
esac
