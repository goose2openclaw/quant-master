# Telegram响应速度优化指南

## 📊 优化概览

### 优化目标
- **减少响应延迟**: 从消息接收到开始处理的时间
- **提高处理速度**: 模型推理和工具调用速度
- **优化用户体验**: 更快的打字指示器和消息显示
- **降低资源使用**: 更高效的内存和CPU使用

### 优化前后对比
| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| 上下文窗口 | 64000 tokens | 32000 tokens | 减少50% |
| 响应超时 | 默认30s | 15s | 减少50% |
| 打字延迟 | 默认500ms | 300ms | 减少40% |
| 最大历史消息 | 无限制 | 20条 | 减少内存使用 |
| 缓存TTL | 无 | 5分钟 | 提高重复查询速度 |

## 🔧 实施的优化措施

### 1. 模型配置优化
```json
{
  "contextWindow": 32000,      // 减少上下文大小
  "maxTokens": 4096,           // 限制输出长度
  "temperature": 0.7,          // 平衡创造性和确定性
  "timeout": 30000,            // API调用超时30s
  "maxRetries": 2,             // 重试次数
  "retryDelay": 1000           // 重试延迟1s
}
```

### 2. Agent性能配置
```json
{
  "thinking": {
    "enabled": false,          // 禁用思考模式(减少延迟)
    "maxTokens": 512
  },
  "memory": {
    "maxContextTokens": 8000,  // 限制上下文tokens
    "maxHistoryMessages": 20,  // 限制历史消息
    "compressHistory": true    // 启用历史压缩
  },
  "response": {
    "streaming": false,        // 禁用流式(Telegram不支持)
    "maxTokens": 2048,         // 响应最大长度
    "timeoutMs": 15000         // 响应超时15s
  }
}
```

### 3. Telegram专用优化
```json
{
  "performance": {
    "typingIndicator": true,   // 启用打字指示器
    "typingDelayMs": 300,      // 300ms后显示打字
    "messageChunkSize": 4096,  // 消息分块大小
    "maxMessageLength": 4096,  // 最大消息长度
    "parseMode": "Markdown",   // 使用Markdown格式
    "disableWebPagePreview": true, // 禁用网页预览
    "replyToMessage": true     // 回复原消息
  },
  "polling": {
    "timeout": 30,             // 轮询超时
    "limit": 100,              // 每次获取消息数
    "allowedUpdates": ["message", "callback_query"],
    "dropPendingUpdates": true // 丢弃待处理更新
  },
  "cache": {
    "enabled": true,           // 启用缓存
    "ttlMs": 300000,           // 5分钟缓存
    "maxSize": 100             // 最大缓存条目
  }
}
```

### 4. 系统级优化
```json
{
  "performance": {
    "maxConcurrentSessions": 5,    // 限制并发会话
    "sessionTimeoutMinutes": 30,   // 会话超时
    "memoryLimitMb": 2048,         // 内存限制
    "cpuLimitPercent": 80,         // CPU限制
    "monitoring": {
      "enabled": true,             // 启用监控
      "intervalMs": 60000,         // 每分钟监控
      "metrics": ["cpu", "memory", "response_time"]
    }
  },
  "caching": {
    "enabled": true,               // 启用缓存
    "strategy": "memory",          // 内存缓存
    "ttlMs": 300000,               // 5分钟TTL
    "maxSize": 1000                // 最大缓存大小
  }
}
```

## 🚀 性能测试方法

### 1. 响应时间测试
```bash
# 测试脚本
bash /home/goose/.openclaw/workspace/scripts/test_telegram_response.sh

# 手动测试
time curl -s 'http://localhost:18789/api/health'
```

### 2. 资源监控
```bash
# 监控OpenClaw进程
top -b -n 1 | grep -E '(openclaw|node)'

# 监控内存使用
free -h | grep Mem

# 监控网络连接
ss -tulpn | grep -E "(18789|8080)"
```

### 3. Telegram实际测试
1. 发送简单消息: "ping"
2. 发送复杂查询: "长沙天气"
3. 发送工具调用: "使用brave-search搜索AI代理"
4. 测量从发送到收到响应的时间

## 📈 预期性能改进

### 响应时间改进
| 查询类型 | 优化前 | 优化后 | 改进幅度 |
|----------|--------|--------|----------|
| 简单回复 | 2-3s | 1-2s | 30-50% |
| 工具调用 | 5-10s | 3-6s | 40% |
| 复杂分析 | 15-30s | 8-15s | 50% |

### 资源使用改进
| 资源类型 | 优化前 | 优化后 | 节省 |
|----------|--------|--------|------|
| 内存使用 | ~1200MB | ~800MB | 33% |
| CPU使用 | 8-10% | 5-7% | 30% |
| 网络流量 | 较高 | 优化 | 20% |

## 🔍 故障排除

### 常见问题及解决方案

#### 1. 响应仍然慢
```bash
# 检查API响应时间
curl -w "@curl-format.txt" -s "https://api.deepseek.com/v1/chat/completions"

# 检查网络延迟
ping api.deepseek.com

# 检查本地资源
bash /home/goose/.openclaw/workspace/scripts/test_telegram_response.sh
```

#### 2. Telegram连接问题
```bash
# 检查Bot Token
grep "botToken" ~/.openclaw/openclaw.json

# 测试Bot API
curl -s "https://api.telegram.org/botYOUR_TOKEN/getMe"

# 检查网络连接
curl -I "https://api.telegram.org"
```

#### 3. 内存使用过高
```bash
# 检查内存泄漏
ps aux --sort=-%mem | grep openclaw

# 清理旧会话
find ~/.openclaw/sessions -type f -mtime +7 -delete

# 重启服务
bash /home/goose/.openclaw/workspace/scripts/restart_openclaw_optimized.sh
```

## 🛠️ 维护和监控

### 日常监控命令
```bash
# 健康检查
bash /home/goose/.openclaw/workspace/scripts/test_telegram_response.sh

# 性能监控
watch -n 60 "ps aux | grep openclaw"

# 日志监控
tail -f ~/.openclaw/logs/openclaw.log 2>/dev/null || echo "启用日志: openclaw gateway logs"
```

### 定期维护任务
1. **每日**: 检查系统资源使用
2. **每周**: 清理旧日志和会话
3. **每月**: 更新配置和优化参数
4. **每季度**: 全面性能评估

### 自动化监控脚本
```bash
#!/bin/bash
# 保存为 /home/goose/.openclaw/scripts/daily_monitor.sh

echo "=== 每日性能监控 ==="
echo "时间: $(date)"
echo ""

# 1. 系统资源
echo "1. 系统资源:"
free -h | grep Mem
top -b -n 1 | grep -E "(openclaw|node)" | head -5

# 2. Telegram响应测试
echo ""
echo "2. Telegram响应测试:"
echo "发送测试消息并记录响应时间"

# 3. 配置检查
echo ""
echo "3. 配置状态:"
python3 -c "
import json
with open('/home/goose/.openclaw/openclaw.json', 'r') as f:
    config = json.load(f)
print('配置版本:', config.get('meta', {}).get('lastTouchedVersion', '未知'))
print('优化目标:', config.get('meta', {}).get('optimizedFor', '未设置'))
"

echo ""
echo "=== 监控完成 ==="
```

## 📋 优化检查清单

### 已完成的优化
- [x] 减少模型上下文窗口
- [x] 设置响应超时限制
- [x] 启用打字指示器优化
- [x] 限制历史消息数量
- [x] 启用消息压缩
- [x] 配置缓存策略
- [x] 优化网络连接参数
- [x] 创建监控脚本

### 待完成的优化
- [ ] 测试deepseek-reasoner模型速度
- [ ] 实现响应流式传输
- [ ] 添加更细粒度的监控
- [ ] 创建自动化性能报告
- [ ] 优化技能加载机制

## 🎯 最佳实践

### 1. 保持配置简洁
- 只启用必要的技能
- 定期清理未使用的配置
- 使用环境变量管理敏感信息

### 2. 监控和调整
- 定期检查响应时间
- 根据使用模式调整参数
- 保持配置文档更新

### 3. 备份和恢复
```bash
# 备份配置
cp ~/.openclaw/openclaw.json ~/.openclaw/backups/openclaw_$(date +%Y%m%d).json

# 恢复配置
cp ~/.openclaw/backups/openclaw_20260301.json ~/.openclaw/openclaw.json
```

## 📞 支持信息

### 快速参考
- **测试脚本**: `scripts/test_telegram_response.sh`
- **重启脚本**: `scripts/restart_openclaw_optimized.sh`
- **配置备份**: `~/.openclaw/openclaw.json.backup.*`
- **监控脚本**: `scripts/daily_monitor.sh`

### 故障排除流程
1. 运行测试脚本检查当前状态
2. 检查日志文件中的错误信息
3. 验证网络连接和API可用性
4. 重启服务应用最新配置
5. 如果问题持续，恢复备份配置

---

**最后更新**: 2026-03-01 05:25  
**优化状态**: ✅ 配置已应用，待测试  
**下一步**: 重启OpenClaw服务并测试Telegram响应速度