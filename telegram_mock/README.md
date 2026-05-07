# Telegram Bot模拟系统

## 概述
这是一个完整的Telegram Bot模拟系统，允许您在离线环境下开发、测试和调试Bot功能。当网络恢复后，可以无缝迁移到真实Bot。

## 功能特性

### ✅ 核心功能
- 命令处理模拟（/start, /status, /crypto, /jobs, /help）
- 消息存储系统（本地JSON文件）
- 用户管理模拟
- 完整日志记录

### ✅ 数据模拟
- 加密货币行情模拟
- 求职数据模拟
- 系统状态模拟
- 交互历史记录

### ✅ 开发支持
- 完整的Python API
- 可扩展的命令处理器
- 数据持久化存储
- 无缝迁移路径

## 快速开始

### 1. 启动模拟系统
```bash
# 首次运行初始化
bash ~/.openclaw/workspace/scripts/telegram_mock_system.sh

# 启动交互式测试
bash ~/.openclaw/workspace/scripts/test_mock_bot.sh
```

### 2. 基本使用
在模拟系统中，您可以：
- 发送命令（以 / 开头）
- 查看Bot回复
- 浏览消息历史
- 测试各种场景

### 3. 可用命令
- `/start` - 启动模拟Bot
- `/status` - 查看系统状态
- `/crypto` - 模拟加密货币行情
- `/jobs` - 模拟求职助手
- `/help` - 帮助信息

## 系统架构

### 目录结构
```
telegram_mock/
├── config.json          # 模拟系统配置
├── mock_handler.py      # 核心处理器
├── mock_bot.log         # 系统日志
├── messages/            # 存储所有消息
│   └── {chat_id}_{message_id}.json
├── users/               # 用户数据
│   └── {user_id}.json
└── logs/                # 详细日志
```

### 数据流
```
用户输入 → 命令处理器 → 响应生成 → 消息存储 → 用户显示
      ↓          ↓           ↓           ↓
   日志记录   状态更新    数据模拟    历史记录
```

## 开发指南

### 添加新命令
1. 编辑 `mock_handler.py`
2. 在 `handlers` 字典中添加新命令
3. 实现对应的处理方法
4. 测试新命令功能

### 自定义响应
修改各个命令的处理方法，自定义响应内容和格式。

### 扩展数据模拟
在相应的处理方法中添加更多模拟数据逻辑。

## 迁移到真实Bot

### 准备工作
1. 获取有效的Telegram Bot Token
2. 确保网络连接正常
3. 备份模拟数据

### 迁移步骤
```bash
# 运行迁移脚本
bash ~/.openclaw/workspace/scripts/migrate_to_real_bot.sh

# 启动真实Bot
bash ~/.openclaw/workspace/scripts/start_telegram_bot.sh
```

### 迁移后
- 所有新消息通过真实Bot发送
- 模拟数据保留供分析使用
- 配置自动更新
- 无缝切换体验

## 高级功能

### 批量测试
创建测试脚本，批量发送命令并验证响应。

### 性能监控
监控消息处理时间和系统资源使用。

### 错误处理
模拟各种错误场景，测试系统稳定性。

## 故障排除

### 常见问题

#### Q: 命令无响应
A: 检查命令拼写，或查看日志文件。

#### Q: 数据不保存
A: 检查目录权限，确保有写入权限。

#### Q: 迁移失败
A: 检查网络连接和Token有效性。

### 日志查看
```bash
# 查看系统日志
tail -f ~/.openclaw/workspace/telegram_mock/mock_bot.log

# 查看消息存储
ls -la ~/.openclaw/workspace/telegram_mock/messages/
```

## 最佳实践

### 开发阶段
1. 在模拟系统中完成所有功能开发
2. 充分测试各种交互场景
3. 确保数据持久化正常工作

### 测试阶段
1. 验证所有命令响应
2. 测试边界情况和错误处理
3. 性能压力测试

### 上线准备
1. 备份所有模拟数据
2. 准备真实Bot Token
3. 运行迁移脚本
4. 验证真实环境

## 支持与反馈

- 查看日志文件获取详细信息
- 检查配置文件确保正确设置
- 测试各个功能模块
- 网络恢复后迁移到真实Bot

---
*模拟系统版本: 1.0 | 创建时间: 2026-02-28*
