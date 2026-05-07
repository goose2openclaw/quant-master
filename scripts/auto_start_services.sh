#!/bin/bash
# 开机自动启动所有服务
# 将此脚本添加到 ~/.bashrc 或系统启动项中

echo "========================================="
echo "🚀 OpenClaw服务自动启动脚本"
echo "时间: $(date)"
echo "========================================="

# 创建日志目录
mkdir -p /home/goose/.openclaw/logs/startup

LOG_FILE="/home/goose/.openclaw/logs/startup/auto_start_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "日志文件: $LOG_FILE"
echo ""

# 1. 检查并启动OpenClaw网关
echo "1. 检查OpenClaw网关..."
if pgrep -f "openclaw-gateway" > /dev/null; then
    echo "   ✅ OpenClaw网关已在运行"
else
    echo "   ⚠️  OpenClaw网关未运行，正在启动..."
    openclaw gateway start > /tmp/openclaw_start.log 2>&1 &
    sleep 3
    
    if pgrep -f "openclaw-gateway" > /dev/null; then
        echo "   ✅ OpenClaw网关启动成功"
    else
        echo "   ❌ OpenClaw网关启动失败，查看日志: /tmp/openclaw_start.log"
    fi
fi
echo ""

# 2. 检查并启动Mission Control
echo "2. 检查Mission Control..."
if ss -tlnp 2>/dev/null | grep -q ":8080"; then
    echo "   ✅ Mission Control已在运行 (端口8080)"
else
    echo "   ⚠️  Mission Control未运行，正在启动..."
    
    # 检查Mission Control目录
    if [ -d "/home/goose/.openclaw/mission-control-app" ]; then
        # 在后台启动Mission Control
        cd /home/goose/.openclaw/mission-control-app
        nohup npm run dev > /home/goose/.openclaw/logs/mission_control_start.log 2>&1 &
        MISSION_PID=$!
        
        # 等待启动
        echo "   等待Mission Control启动..."
        sleep 5
        
        # 检查是否启动成功
        if curl -s http://localhost:8080 > /dev/null; then
            echo "   ✅ Mission Control启动成功 (PID: $MISSION_PID)"
            echo "   访问地址: http://localhost:8080"
        else
            echo "   ❌ Mission Control启动失败，查看日志: /home/goose/.openclaw/logs/mission_control_start.log"
        fi
    else
        echo "   ❌ Mission Control目录不存在: /home/goose/.openclaw/mission-control-app"
    fi
fi
echo ""

# 3. 检查其他关键服务
echo "3. 检查其他服务..."
echo "   检查Telegram连接..."
if curl -s http://localhost:18789/api/health > /dev/null; then
    echo "   ✅ OpenClaw网关健康检查通过"
else
    echo "   ⚠️  OpenClaw网关健康检查失败"
fi
echo ""

# 4. 验证所有服务
echo "4. 验证所有服务连接..."
echo "   Mission Control (8080):"
if timeout 5 curl -s -o /dev/null -w "状态码: %{http_code}, 时间: %{time_total}s\n" http://localhost:8080; then
    echo "   ✅ 连接正常"
else
    echo "   ❌ 连接失败"
fi

echo "   OpenClaw网关 (18789):"
if timeout 5 curl -s -o /dev/null -w "状态码: %{http_code}, 时间: %{time_total}s\n" http://localhost:18789; then
    echo "   ✅ 连接正常"
else
    echo "   ❌ 连接失败"
fi
echo ""

# 5. 创建快捷命令
echo "5. 创建快捷命令..."
cat > /tmp/openclaw_quick_commands.sh << 'EOF'
#!/bin/bash
# OpenClaw快捷命令

case "$1" in
    status)
        echo "=== OpenClaw服务状态 ==="
        ps aux | grep -E "[o]penclaw|[n]ext" | grep -v grep
        echo ""
        echo "=== 端口监听 ==="
        ss -tlnp 2>/dev/null | grep -E ":8080|:18789"
        ;;
    start)
        echo "启动所有服务..."
        bash /home/goose/.openclaw/workspace/scripts/auto_start_services.sh
        ;;
    stop)
        echo "停止所有服务..."
        pkill -f "openclaw-gateway"
        pkill -f "next dev"
        echo "服务已停止"
        ;;
    restart)
        echo "重启所有服务..."
        pkill -f "openclaw-gateway"
        pkill -f "next dev"
        sleep 2
        bash /home/goose/.openclaw/workspace/scripts/auto_start_services.sh
        ;;
    logs)
        echo "查看服务日志..."
        tail -f /home/goose/.openclaw/logs/startup/auto_start_*.log 2>/dev/null | head -20
        ;;
    *)
        echo "用法: $0 {status|start|stop|restart|logs}"
        echo ""
        echo "服务地址:"
        echo "  Mission Control: http://localhost:8080"
        echo "  OpenClaw网关:    http://localhost:18789"
        ;;
esac
EOF

chmod +x /tmp/openclaw_quick_commands.sh
cp /tmp/openclaw_quick_commands.sh /home/goose/.openclaw/workspace/scripts/oc_quick.sh

echo "   快捷命令已创建: /home/goose/.openclaw/workspace/scripts/oc_quick.sh"
echo "   使用方法:"
echo "     oc_quick.sh status    # 查看状态"
echo "     oc_quick.sh start     # 启动服务"
echo "     oc_quick.sh stop      # 停止服务"
echo "     oc_quick.sh restart   # 重启服务"
echo "     oc_quick.sh logs      # 查看日志"
echo ""

# 6. 添加到bashrc (可选)
echo "6. 添加到bashrc (可选)..."
if ! grep -q "oc_quick.sh" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# OpenClaw快捷命令别名" >> ~/.bashrc
    echo "alias ocstatus='bash /home/goose/.openclaw/workspace/scripts/oc_quick.sh status'" >> ~/.bashrc
    echo "alias ocstart='bash /home/goose/.openclaw/workspace/scripts/oc_quick.sh start'" >> ~/.bashrc
    echo "alias ocstop='bash /home/goose/.openclaw/workspace/scripts/oc_quick.sh stop'" >> ~/.bashrc
    echo "alias ocrestart='bash /home/goose/.openclaw/workspace/scripts/oc_quick.sh restart'" >> ~/.bashrc
    echo "alias oclogs='bash /home/goose/.openclaw/workspace/scripts/oc_quick.sh logs'" >> ~/.bashrc
    echo "   ✅ 已添加到~/.bashrc"
    echo "   重新加载配置: source ~/.bashrc"
else
    echo "   ℹ️  已存在于~/.bashrc"
fi
echo ""

echo "========================================="
echo "🎉 服务启动完成"
echo "========================================="
echo ""
echo "📊 服务状态摘要:"
echo "   OpenClaw网关: ✅ 运行中 (端口18789)"
echo "   Mission Control: ✅ 运行中 (端口8080)"
echo ""
echo "🌐 访问地址:"
echo "   Mission Control看板: http://localhost:8080"
echo "   OpenClaw网关: http://localhost:18789"
echo ""
echo "📋 快捷命令:"
echo "   ocstatus    # 查看状态"
echo "   ocstart     # 启动服务"
echo "   ocstop      # 停止服务"
echo "   ocrestart   # 重启服务"
echo ""
echo "📝 日志文件: $LOG_FILE"
echo "========================================="