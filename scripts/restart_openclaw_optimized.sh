#!/bin/bash

# OpenClaw优化重启脚本
# 应用性能优化配置后重启服务

echo "=== OpenClaw优化重启 ==="
echo "时间: $(date)"
echo ""

# 1. 检查当前进程
echo "1. 停止当前OpenClaw进程..."
pkill -f "openclaw-gateway" 2>/dev/null && echo "  ✅ openclaw-gateway已停止" || echo "  ℹ️  openclaw-gateway未运行"
pkill -f "openclaw " 2>/dev/null && echo "  ✅ openclaw主进程已停止" || echo "  ℹ️  openclaw主进程未运行"
pkill -f "openclaw-logs" 2>/dev/null && echo "  ✅ openclaw-logs已停止" || echo "  ℹ️  openclaw-logs未运行"

sleep 2

# 2. 验证进程已停止
echo ""
echo "2. 验证进程状态:"
if pgrep -f "openclaw" > /dev/null; then
    echo "  ⚠️  仍有OpenClaw进程运行:"
    pgrep -f "openclaw" | xargs ps -o pid,cmd -p
    echo "  强制停止..."
    pkill -9 -f "openclaw"
    sleep 1
else
    echo "  ✅ 所有OpenClaw进程已停止"
fi

# 3. 检查配置
echo ""
echo "3. 检查优化配置:"
if [ -f ~/.openclaw/openclaw.json ]; then
    echo "  ✅ 配置文件存在"
    # 检查关键优化参数
    python3 -c "
import json
with open('/home/goose/.openclaw/openclaw.json', 'r') as f:
    config = json.load(f)
    
print('  关键优化参数:')
print(f'    Telegram打字延迟: {config.get(\"channels\", {}).get(\"telegram\", {}).get(\"performance\", {}).get(\"typingDelayMs\", \"未设置\")}ms')
print(f'    模型超时: {config.get(\"models\", {}).get(\"providers\", {}).get(\"custom-api-deepseek-com\", {}).get(\"timeout\", \"未设置\")}ms')
print(f'    响应超时: {config.get(\"agents\", {}).get(\"defaults\", {}).get(\"response\", {}).get(\"timeoutMs\", \"未设置\")}ms')
print(f'    上下文窗口: {config.get(\"models\", {}).get(\"providers\", {}).get(\"custom-api-deepseek-com\", {}).get(\"models\", [{}])[0].get(\"contextWindow\", \"未设置\")}')
"
else
    echo "  ❌ 配置文件不存在"
    exit 1
fi

# 4. 启动OpenClaw
echo ""
echo "4. 启动OpenClaw服务..."
echo "  启动网关..."
openclaw gateway start > /tmp/openclaw_start.log 2>&1 &
GATEWAY_PID=$!
sleep 3

if ps -p $GATEWAY_PID > /dev/null; then
    echo "  ✅ 网关启动成功 (PID: $GATEWAY_PID)"
else
    echo "  ❌ 网关启动失败，检查日志:"
    cat /tmp/openclaw_start.log
    exit 1
fi

# 5. 验证服务状态
echo ""
echo "5. 验证服务状态:"
sleep 2
echo "  检查进程..."
ps aux | grep -E "[o]penclaw" | awk '{print "  PID:", $2, "CMD:", $11, $12}'

echo ""
echo "  检查端口监听..."
ss -tulpn | grep -E "(18789)" | awk '{print "  端口", $5, "监听中"}'

# 6. 测试Telegram连接
echo ""
echo "6. Telegram连接测试:"
echo "  请发送一条消息到Telegram Bot测试响应速度"
echo "  预期改进:"
echo "  - 打字指示器更快显示(300ms vs 默认500ms)"
echo "  - 响应超时更短(15s vs 默认30s)"
echo "  - 上下文更小(8000 tokens vs 默认)"
echo "  - 消息分块优化(4096字符)"

# 7. 监控命令
echo ""
echo "7. 监控命令:"
echo "  # 实时监控日志"
echo "  tail -f /tmp/openclaw_start.log"
echo ""
echo "  # 检查Telegram响应时间"
echo "  time curl -s 'http://localhost:18789/api/health'"
echo ""
echo "  # 性能测试"
echo "  bash /home/goose/.openclaw/workspace/scripts/test_telegram_response.sh"

echo ""
echo "=== 重启完成 ==="
echo "优化配置已应用，请测试Telegram响应速度"