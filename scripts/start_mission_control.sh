#!/bin/bash

# OpenClaw Mission Control 启动脚本
# 完全免费，无需外部依赖

echo "🚀 启动 OpenClaw Mission Control 系统..."

# 检查Mission Control应用目录
MISSION_CONTROL_DIR="/home/goose/.openclaw/mission-control-app"
if [ ! -d "$MISSION_CONTROL_DIR" ]; then
    echo "❌ Mission Control应用目录不存在: $MISSION_CONTROL_DIR"
    echo "正在克隆Mission Control应用..."
    cd /home/goose/.openclaw
    git clone https://github.com/0xindiebruh/openclaw-mission-control.git mission-control-app
    if [ $? -ne 0 ]; then
        echo "❌ 克隆失败"
        exit 1
    fi
fi

# 进入目录
cd "$MISSION_CONTROL_DIR"

# 检查依赖是否安装
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 检查端口8080是否被占用
PORT=8080
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $PORT 已被占用，尝试停止现有进程..."
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        kill -9 $PID
        sleep 2
    fi
fi

# 启动Mission Control服务器
echo "🌐 启动Mission Control服务器..."
echo "访问地址: http://localhost:8080"
echo "按 Ctrl+C 停止服务器"

# 创建日志目录
mkdir -p logs

# 启动服务器并记录日志
npm run dev 2>&1 | tee logs/mission-control-$(date +%Y%m%d-%H%M%S).log &

# 等待服务器启动
echo "⏳ 等待服务器启动..."
sleep 5

# 检查服务器状态
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ Mission Control服务器启动成功!"
    echo ""
    echo "📋 可用命令:"
    echo "1. 查看看板: http://localhost:8080"
    echo "2. 初始化数据库: curl -X POST http://localhost:8080/api/seed"
    echo "3. 创建任务示例: 查看 /home/goose/.openclaw/workspace/mission_control_config.md"
    echo ""
    echo "🎯 OPC项目智能体配置:"
    echo "- 加密货币监控: crypto-monitor"
    echo "- 智能合约开发: smart-contract"
    echo "- 求职助手: job-assistant"
    echo "- 交易辅助: trading-helper"
    echo "- 前端开发: frontend-dev"
    echo "- 数据分析: data-analyst"
    echo "- 文档管理: document-manager"
else
    echo "❌ 服务器启动失败，请检查日志"
    exit 1
fi

# 保持脚本运行
echo ""
echo "📊 服务器日志:"
tail -f logs/mission-control-$(date +%Y%m%d-%H%M%S).log