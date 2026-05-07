---
name: whatsapp
description: OPC项目专用WhatsApp集成 - 支持消息、模板、媒体、自动化通知
created: 2026-02-28
updated: 2026-02-28
status: configured
version: 1.0.0
author: OPC Project Team
---

# WhatsApp技能 - OPC项目专用

## 概述
为OPC项目提供完整的WhatsApp Business API集成，支持加密货币警报、求职通知、系统状态报告等功能。

## 核心功能

### 📱 消息功能
- **文本消息**: 支持纯文本和格式化消息
- **媒体消息**: 图片、视频、音频、文档
- **模板消息**: 预审批消息模板
- **交互消息**: 快速回复、列表消息、按钮

### 🔔 通知系统
- **加密货币警报**: 价格波动超过阈值时通知
- **求职通知**: 新职位匹配时提醒
- **系统状态**: 每日运行状态报告
- **紧急警报**: 系统故障或安全事件

### 🤖 自动化
- **欢迎消息**: 新联系人自动欢迎
- **自动回复**: 非工作时间自动回复
- **定时广播**: 每日/每周摘要
- **命令处理**: 统一命令系统

### 🔗 集成功能
- **与Telegram同步**: 跨平台消息同步
- **统一命令**: 相同命令在不同平台
- **数据共享**: 用户数据跨平台共享

## 配置要求

### 必需信息
1. **WhatsApp Business Account** (business.facebook.com)
2. **Phone Number ID** (从Meta获取)
3. **Business Account ID** (从Meta获取)
4. **Permanent Access Token** (长期有效令牌)
5. **Webhook URL** (用于接收消息)

### 配置步骤
```bash
# 1. 创建WhatsApp Business账户
# 访问: https://business.facebook.com

# 2. 获取认证信息
# - Phone Number ID
# - Business Account ID  
# - Permanent Access Token

# 3. 更新配置文件
nano ~/.openclaw/workspace/config/whatsapp_config.json

# 4. 设置Webhook
# 配置webhookUrl和verifyToken

# 5. 测试连接
bash ~/opc-project/scripts/test_whatsapp.sh
```

## 配置文件
- **主配置**: `~/.openclaw/workspace/config/whatsapp_config.json`
- **技能配置**: `~/.openclaw/workspace/skills/whatsapp/config.json`

## 命令系统

### 用户命令
```
/start - 启动OPC助手
/crypto - 加密货币监控
/jobs - 求职助手
/contract - 智能合约工具
/trade - 交易辅助
/status - 系统状态
/help - 帮助信息
```

### 管理员命令
```
/admin status - 系统状态
/admin logs - 查看日志
/admin backup - 备份数据
/admin restart - 重启服务
```

## 通知类型

### 加密货币通知
```
🚨 Crypto Alert: BTC is at $45,200 (+3.2% in 24h)
📊 Volume Spike: ETH trading volume increased by 150%
⚠️ Price Drop: SOL dropped 8% to $95.50
```

### 求职通知
```
📋 New Job: Blockchain Developer at CryptoCorp
📍 Location: Singapore (Remote possible)
💰 Salary: $8,000 - $12,000
🔧 Skills: Solidity, React, Node.js
```

### 系统通知
```
✅ System Online: All services running
⚠️ Warning: High memory usage (85%)
❌ Error: Telegram connection failed
📈 Stats: 24h messages: 150, Users: 45
```

## 故障排除

### 常见问题
1. **认证失败**: 检查Access Token和Phone Number ID
2. **消息未发送**: 验证模板审批状态
3. **Webhook错误**: 检查URL可访问性和验证令牌
4. **速率限制**: 降低发送频率或申请更高限制

### 调试命令
```bash
# 检查配置
bash ~/opc-project/scripts/check_whatsapp_config.sh

# 测试连接
bash ~/opc-project/scripts/test_whatsapp_connection.sh

# 查看日志
tail -f ~/opc-project/logs/whatsapp/whatsapp.log
```

## 安全注意事项

### 必需措施
1. **加密存储**: API密钥必须加密存储
2. **访问控制**: 限制管理员访问
3. **日志审计**: 记录所有消息活动
4. **速率限制**: 防止滥用

### 推荐措施
1. **双因素认证**: 管理员账户
2. **定期轮换**: API密钥每月轮换
3. **监控告警**: 异常活动告警
4. **备份策略**: 定期备份配置和数据

## 性能优化

### 缓存策略
- 消息模板缓存: 300秒
- 联系人信息缓存: 3600秒
- 媒体文件缓存: 1800秒

### 并发处理
- 最大并发连接: 5
- 消息批处理: 10条/批
- 重试机制: 3次指数退避

## 更新日志

### v1.0.0 (2026-02-28)
- 初始版本发布
- 完整配置框架
- OPC项目集成
- 多类型通知支持

## 支持
- 文档: `~/opc-project/docs/whatsapp/`
- 问题: 创建GitHub Issue
- 紧急: 联系管理员 via Telegram

---

**状态**: ✅ 配置完成，等待认证信息
**下一步**: 配置WhatsApp Business账户并更新认证信息
