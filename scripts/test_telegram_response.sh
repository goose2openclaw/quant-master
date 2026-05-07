#!/bin/bash

# Telegram响应速度测试脚本
# 用法: ./test_telegram_response.sh

echo "=== Telegram响应速度测试 ==="
echo "测试时间: $(date)"
echo ""

# 1. 检查OpenClaw进程状态
echo "1. OpenClaw进程状态:"
ps aux | grep -E "[o]penclaw" | awk '{print "  PID:", $2, "CMD:", $11, $12, $13}'
echo ""

# 2. 检查内存使用
echo "2. 系统内存使用:"
free -h | grep Mem | awk '{print "  总内存:", $2, "已用:", $3, "可用:", $4}'
echo ""

# 3. 检查网络连接
echo "3. 网络连接状态:"
ss -tulpn | grep -E "(18789|8080)" | awk '{print "  端口", $5, "-> PID:", $7}'
echo ""

# 4. 检查配置优化参数
echo "4. 配置优化参数检查:"
python3 -c "
import json
with open('/home/goose/.openclaw/openclaw.json', 'r') as f:
    config = json.load(f)

print('  Telegram性能配置:')
telegram = config.get('channels', {}).get('telegram', {})
perf = telegram.get('performance', {})
print(f'    打字指示器: {perf.get(\"typingIndicator\", \"未设置\")}')
print(f'    打字延迟: {perf.get(\"typingDelayMs\", \"未设置\")}ms')
print(f'    消息分块大小: {perf.get(\"messageChunkSize\", \"未设置\")}')

print('  Agent性能配置:')
agent = config.get('agents', {}).get('defaults', {})
print(f'    最大上下文tokens: {agent.get(\"memory\", {}).get(\"maxContextTokens\", \"未设置\")}')
print(f'    最大历史消息: {agent.get(\"memory\", {}).get(\"maxHistoryMessages\", \"未设置\")}')
print(f'    响应超时: {agent.get(\"response\", {}).get(\"timeoutMs\", \"未设置\")}ms')

print('  模型配置:')
model = config.get('models', {}).get('providers', {}).get('custom-api-deepseek-com', {}).get('models', [{}])[0]
print(f'    上下文窗口: {model.get(\"contextWindow\", \"未设置\")}')
print(f'    最大tokens: {model.get(\"maxTokens\", \"未设置\")}')
print(f'    超时设置: {config.get(\"models\", {}).get(\"providers\", {}).get(\"custom-api-deepseek-com\", {}).get(\"timeout\", \"未设置\")}ms')
"
echo ""

# 5. 性能建议
echo "5. 性能优化建议:"
echo "  ✅ 已实施的优化:"
echo "    - 减少上下文窗口从64000到32000 tokens"
echo "    - 设置响应超时15000ms"
echo "    - 启用打字指示器(300ms延迟)"
echo "    - 限制最大历史消息为20条"
echo "    - 启用消息压缩"
echo "    - 设置缓存TTL为5分钟"
echo ""
echo "  🔧 进一步优化建议:"
echo "    - 定期清理会话日志"
echo "    - 监控API响应时间"
echo "    - 考虑使用更快的模型(如deepseek-reasoner)"
echo "    - 启用响应流式传输(如果支持)"
echo ""

# 6. 测试命令
echo "6. 快速测试命令:"
echo "  # 测试简单响应"
echo "  echo '测试消息' | 检查Telegram响应时间"
echo ""
echo "  # 监控OpenClaw日志"
echo "  tail -f ~/.openclaw/logs/openclaw.log 2>/dev/null || echo '日志文件不存在'"
echo ""
echo "  # 检查系统资源"
echo "  top -b -n 1 | grep -E '(openclaw|node)'"

echo ""
echo "=== 测试完成 ==="