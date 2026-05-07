#!/bin/bash
# 服务健康检查脚本
# 定期检查服务健康状态，可添加到cron任务中

echo "========================================="
echo "🩺 OpenClaw服务健康检查"
echo "时间: $(date)"
echo "========================================="

# 创建日志目录
mkdir -p /home/goose/.openclaw/logs/health

LOG_FILE="/home/goose/.openclaw/logs/health/health_check_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "日志文件: $LOG_FILE"
echo ""

# 检查服务函数
check_service() {
    local port=$1
    local name=$2
    local url=$3
    
    echo "检查 $name (端口$port)..."
    
    # 检查端口监听
    if ss -tlnp 2>/dev/null | grep -q ":$port"; then
        echo "  ✅ 端口$port正在监听"
        PORT_OK=true
    else
        echo "  ❌ 端口$port未监听"
        PORT_OK=false
    fi
    
    # 检查HTTP连接
    if [ -n "$url" ]; then
        echo "  测试HTTP连接..."
        HTTP_CODE=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "301" ]; then
            echo "  ✅ HTTP连接正常 (状态码: $HTTP_CODE)"
            HTTP_OK=true
        else
            echo "  ❌ HTTP连接失败 (状态码: $HTTP_CODE)"
            HTTP_OK=false
        fi
    else
        HTTP_OK=true  # 如果没有URL，假设HTTP检查通过
    fi
    
    # 检查进程
    if [ "$name" = "Mission Control" ]; then
        if pgrep -f "next dev" > /dev/null; then
            echo "  ✅ 进程运行正常"
            PROCESS_OK=true
        else
            echo "  ❌ 进程未运行"
            PROCESS_OK=false
        fi
    elif [ "$name" = "OpenClaw网关" ]; then
        if pgrep -f "openclaw-gateway" > /dev/null; then
            echo "  ✅ 进程运行正常"
            PROCESS_OK=true
        else
            echo "  ❌ 进程未运行"
            PROCESS_OK=false
        fi
    else
        PROCESS_OK=true  # 其他服务不检查进程
    fi
    
    # 总体状态
    if $PORT_OK && $HTTP_OK && $PROCESS_OK; then
        echo "  🟢 $name: 健康"
        return 0
    else
        echo "  🔴 $name: 不健康"
        return 1
    fi
}

# 检查系统资源
check_resources() {
    echo ""
    echo "检查系统资源..."
    
    # 内存使用
    MEM_USAGE=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    echo "  内存使用: $MEM_USAGE"
    
    # CPU负载
    CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}')
    echo "  CPU负载: $CPU_LOAD"
    
    # 磁盘空间
    DISK_USAGE=$(df -h /home | awk 'NR==2{print $5}')
    echo "  磁盘使用: $DISK_USAGE"
    
    # OpenClaw进程资源
    echo "  OpenClaw进程资源:"
    ps aux --sort=-%mem | grep -E "[o]penclaw|[n]ext" | head -3 | while read line; do
        echo "    $line"
    done
}

# 检查网络连接
check_network() {
    echo ""
    echo "检查网络连接..."
    
    # 检查本地回环
    if ping -c 1 -W 1 127.0.0.1 > /dev/null 2>&1; then
        echo "  ✅ 本地回环正常"
    else
        echo "  ❌ 本地回环异常"
    fi
    
    # 检查网关
    GATEWAY=$(ip route show default | awk '{print $3}')
    if [ -n "$GATEWAY" ]; then
        if ping -c 1 -W 1 "$GATEWAY" > /dev/null 2>&1; then
            echo "  ✅ 网关连接正常 ($GATEWAY)"
        else
            echo "  ⚠️  网关连接异常 ($GATEWAY)"
        fi
    fi
    
    # 检查外部网络
    if ping -c 1 -W 1 8.8.8.8 > /dev/null 2>&1; then
        echo "  ✅ 外部网络正常"
    else
        echo "  ⚠️  外部网络异常"
    fi
}

# 检查配置文件
check_configs() {
    echo ""
    echo "检查配置文件..."
    
    # OpenClaw配置文件
    if [ -f "/home/goose/.openclaw/openclaw.json" ]; then
        if python3 -c "import json; json.load(open('/home/goose/.openclaw/openclaw.json'))" > /dev/null 2>&1; then
            echo "  ✅ OpenClaw配置文件格式正确"
        else
            echo "  ❌ OpenClaw配置文件格式错误"
        fi
    else
        echo "  ❌ OpenClaw配置文件不存在"
    fi
    
    # Mission Control配置文件
    if [ -f "/home/goose/.openclaw/mission-control-app/package.json" ]; then
        echo "  ✅ Mission Control配置文件存在"
    else
        echo "  ❌ Mission Control配置文件不存在"
    fi
}

# 主检查流程
echo "开始健康检查..."
echo ""

# 1. 检查关键服务
SERVICE_STATUS=0
check_service 8080 "Mission Control" "http://localhost:8080" || SERVICE_STATUS=1
echo ""
check_service 18789 "OpenClaw网关" "http://localhost:18789" || SERVICE_STATUS=1

# 2. 检查系统资源
check_resources

# 3. 检查网络连接
check_network

# 4. 检查配置文件
check_configs

# 5. 检查技能系统
echo ""
echo "检查技能系统..."
SKILLS_DIR="/home/goose/.openclaw/workspace/.agents/skills"
if [ -d "$SKILLS_DIR" ]; then
    SKILL_COUNT=$(find "$SKILLS_DIR" -maxdepth 1 -type d | wc -l)
    echo "  技能总数: $((SKILL_COUNT - 1))"
    
    # 检查高风险技能
    echo "  高风险技能状态:"
    HIGH_RISK_SKILLS=("crypto-report" "agent-reach" "code-simplifier" "ralph-loop" "evomap")
    for skill in "${HIGH_RISK_SKILLS[@]}"; do
        if [ -d "$SKILLS_DIR/$skill" ]; then
            echo "    $skill: ✅ 已安装"
        else
            echo "    $skill: ❌ 未安装"
        fi
    done
else
    echo "  ❌ 技能目录不存在"
fi

# 生成报告
echo ""
echo "========================================="
echo "📊 健康检查报告"
echo "========================================="

if [ $SERVICE_STATUS -eq 0 ]; then
    echo "🎉 所有关键服务健康"
    echo "   建议: 系统运行正常，无需操作"
else
    echo "⚠️  发现不健康服务"
    echo "   建议: 运行修复脚本或手动检查"
    echo ""
    echo "修复步骤:"
    echo "  1. 查看详细日志: $LOG_FILE"
    echo "  2. 重启服务: bash /home/goose/.openclaw/workspace/scripts/oc_quick.sh restart"
    echo "  3. 如果问题持续，检查配置文件"
fi

echo ""
echo "📋 服务状态摘要:"
echo "  Mission Control: $(check_service 8080 "" "" >/dev/null && echo "🟢" || echo "🔴")"
echo "  OpenClaw网关: $(check_service 18789 "" "" >/dev/null && echo "🟢" || echo "🔴")"
echo ""
echo "🌐 访问地址:"
echo "  Mission Control: http://localhost:8080"
echo "  OpenClaw网关: http://localhost:18789"
echo ""
echo "🔧 维护命令:"
echo "  状态检查: bash /home/goose/.openclaw/workspace/scripts/oc_quick.sh status"
echo "  重启服务: bash /home/goose/.openclaw/workspace/scripts/oc_quick.sh restart"
echo "  查看日志: bash /home/goose/.openclaw/workspace/scripts/oc_quick.sh logs"
echo ""
echo "📝 详细日志: $LOG_FILE"
echo "========================================="

# 如果发现严重问题，发送通知
if [ $SERVICE_STATUS -ne 0 ]; then
    # 这里可以添加通知逻辑，比如发送到Telegram
    echo "严重: 发现不健康服务，建议立即处理" >> "$LOG_FILE"
fi

exit $SERVICE_STATUS