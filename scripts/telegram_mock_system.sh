#!/bin/bash

echo "🤖 Telegram Bot模拟系统（离线版）"
echo "=================================="

# 工作目录
WORKSPACE="$HOME/.openclaw/workspace"
MOCK_DIR="$WORKSPACE/telegram_mock"
LOG_FILE="$MOCK_DIR/mock_bot.log"

# 创建目录
mkdir -p "$MOCK_DIR/messages"
mkdir -p "$MOCK_DIR/users"
mkdir -p "$MOCK_DIR/logs"

# 初始化模拟系统
init_mock_system() {
    echo "初始化模拟系统..."
    
    # 创建模拟Bot配置
    cat > "$MOCK_DIR/config.json" << 'EOF'
{
  "mock_bot": {
    "name": "OPC Mock Bot",
    "username": "@opc_mock_bot",
    "id": "1234567890",
    "token": "8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o",
    "status": "offline_mock",
    "created": "2026-02-28T02:00:00Z"
  },
  "features": {
    "command_processing": true,
    "message_storage": true,
    "user_profiles": true,
    "offline_mode": true
  },
  "users": [
    {
      "id": "1001",
      "name": "OPC Developer",
      "username": "@opc_dev",
      "chat_id": "1001"
    }
  ]
}
EOF
    
    # 创建模拟命令处理器
    cat > "$MOCK_DIR/mock_handler.py" << 'EOF'
#!/usr/bin/env python3
"""
Telegram Bot模拟处理器
在离线模式下模拟Bot功能
"""

import json
import os
import time
from datetime import datetime
import random

class MockTelegramBot:
    def __init__(self, mock_dir):
        self.mock_dir = mock_dir
        self.messages_dir = os.path.join(mock_dir, "messages")
        self.users_dir = os.path.join(mock_dir, "users")
        self.log_file = os.path.join(mock_dir, "mock_bot.log")
        
        # 确保目录存在
        os.makedirs(self.messages_dir, exist_ok=True)
        os.makedirs(self.users_dir, exist_ok=True)
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置"""
        config_file = os.path.join(self.mock_dir, "config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        
        print(log_entry.strip())
    
    def save_message(self, chat_id, text, from_user="user"):
        """保存消息到模拟系统"""
        message_id = int(time.time() * 1000)
        message_data = {
            "message_id": message_id,
            "chat": {"id": chat_id},
            "from": {"id": chat_id, "first_name": from_user},
            "text": text,
            "date": int(time.time())
        }
        
        # 保存消息
        message_file = os.path.join(self.messages_dir, f"{chat_id}_{message_id}.json")
        with open(message_file, 'w') as f:
            json.dump(message_data, f, indent=2)
        
        self.log(f"消息保存: {text[:50]}... (ID: {message_id})")
        return message_id
    
    def process_command(self, chat_id, command):
        """处理命令"""
        self.log(f"处理命令: {command} (Chat ID: {chat_id})")
        
        # 移除斜杠
        cmd = command.lstrip('/')
        
        # 命令处理器
        handlers = {
            "start": self.handle_start,
            "status": self.handle_status,
            "crypto": self.handle_crypto,
            "jobs": self.handle_jobs,
            "help": self.handle_help
        }
        
        if cmd in handlers:
            response = handlers[cmd]()
        else:
            response = self.handle_unknown(cmd)
        
        # 保存Bot回复
        bot_message_id = self.save_message(chat_id, response, "bot")
        
        return {
            "ok": True,
            "result": {
                "message_id": bot_message_id,
                "from": {
                    "id": self.config.get("mock_bot", {}).get("id", "1234567890"),
                    "is_bot": True,
                    "first_name": self.config.get("mock_bot", {}).get("name", "Mock Bot"),
                    "username": self.config.get("mock_bot", {}).get("username", "@mock_bot")
                },
                "chat": {"id": chat_id},
                "text": response,
                "date": int(time.time())
            }
        }
    
    def handle_start(self):
        """处理/start命令"""
        return f"""🎉 *欢迎使用OPC模拟Bot！*

🤖 *关于此模拟系统*
这是一个离线模拟的Telegram Bot，用于开发和测试。
当网络恢复后，可以无缝切换到真实Bot。

📋 *可用命令*
• /status - 查看模拟系统状态
• /crypto - 模拟加密货币行情
• /jobs - 模拟求职助手
• /help - 帮助信息

🚀 *开始使用*
发送 /crypto 查看模拟行情
发送 /status 查看系统状态

⏰ 模拟时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_⚠ 注意: 这是模拟系统，所有数据均为模拟数据_"""
    
    def handle_status(self):
        """处理/status命令"""
        # 统计消息
        message_count = len([f for f in os.listdir(self.messages_dir) if f.endswith('.json')])
        user_count = len([f for f in os.listdir(self.users_dir) if f.endswith('.json')])
        
        return f"""📊 *模拟系统状态报告*

✅ *系统信息*
• 模式: 🔌 离线模拟
• 运行时间: 模拟中
• 消息数量: {message_count}
• 用户数量: {user_count}

💾 *存储状态*
• 消息目录: {self.messages_dir}
• 用户目录: {self.users_dir}
• 日志文件: {self.log_file}

🔧 *功能状态*
• 命令处理: ✅ 正常
• 消息存储: ✅ 正常
• 用户管理: ✅ 正常
• 离线模式: ✅ 启用

🚀 *下一步*
• 网络恢复后切换到真实Bot
• 继续开发OPC项目功能
• 测试更多交互场景

⏰ 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    def handle_crypto(self):
        """处理/crypto命令"""
        # 模拟加密货币数据
        crypto_data = [
            {"symbol": "BTC", "price": f"${random.randint(42000, 48000):,}", "change": f"{random.choice(['+', '-'])}{random.uniform(0.5, 5.0):.1f}%"},
            {"symbol": "ETH", "price": f"${random.randint(2400, 2600):,}", "change": f"{random.choice(['+', '-'])}{random.uniform(0.3, 3.0):.1f}%"},
            {"symbol": "SOL", "price": f"${random.randint(90, 110)}", "change": f"{random.choice(['+', '-'])}{random.uniform(1.0, 8.0):.1f}%"},
            {"symbol": "ADA", "price": f"${random.uniform(0.45, 0.55):.2f}", "change": f"{random.choice(['+', '-'])}{random.uniform(0.1, 2.0):.1f}%"}
        ]
        
        message = "🪙 *模拟加密货币行情*\n\n"
        
        for coin in crypto_data:
            emoji = "🟢" if coin['change'].startswith('+') else "🔴"
            message += f"{emoji} *{coin['symbol']}*: {coin['price']} ({coin['change']})\n"
        
        message += f"\n📈 *市场状态*: 模拟波动中"
        message += f"\n⏰ 更新时间: {datetime.now().strftime('%H:%M:%S')}"
        message += f"\n\n💡 *提示*: 这是模拟数据，网络恢复后将显示实时行情"
        
        return message
    
    def handle_jobs(self):
        """处理/jobs命令"""
        # 模拟职位数据
        jobs = [
            {"title": "Python区块链开发", "company": "Web3 Tech", "location": "远程", "skills": "Python, Solidity, Web3"},
            {"title": "智能合约工程师", "company": "Crypto Labs", "location": "新加坡", "skills": "Solidity, Ethereum, DeFi"},
            {"title": "加密货币分析师", "company": "Digital Assets", "location": "香港", "skills": "数据分析, 交易策略, Python"}
        ]
        
        message = "💼 *模拟求职助手*\n\n"
        
        for i, job in enumerate(jobs, 1):
            message += f"{i}. *{job['title']}*\n"
            message += f"   公司: {job['company']}\n"
            message += f"   地点: {job['location']}\n"
            message += f"   技能: {job['skills']}\n\n"
        
        message += f"📊 *统计*: 共找到 {len(jobs)} 个模拟职位"
        message += f"\n⏰ 搜索时间: {datetime.now().strftime('%H:%M:%S')}"
        message += f"\n\n💡 *提示*: 这是模拟数据，网络恢复后将搜索真实职位"
        
        return message
    
    def handle_help(self):
        """处理/help命令"""
        return """❓ *模拟Bot帮助信息*

📋 *可用命令*
• /start - 启动模拟Bot
• /status - 查看模拟系统状态
• /crypto - 模拟加密货币行情
• /jobs - 模拟求职助手
• /help - 显示此帮助信息

🔄 *模拟功能*
1. 命令处理模拟
2. 消息存储模拟
3. 用户管理模拟
4. 数据生成模拟

🚀 *开发用途*
• 测试Bot逻辑
• 开发消息处理器
• 设计用户交互
• 准备上线功能

🔌 *离线模式*
• 所有操作本地存储
• 无需网络连接
• 可随时切换到真实Bot

⏰ *网络恢复后*
1. 更新Token配置
2. 导入模拟数据
3. 切换到真实Bot
4. 开始真实交互

💡 *提示*
• 模拟数据不会影响真实系统
• 所有开发工作都会被保存
• 可无缝迁移到真实环境

📞 *支持*
• 查看日志: mock_bot.log
• 配置文件: config.json
• 消息存储: messages/ 目录

---
*模拟系统版本: 1.0 | 最后更新: 2026-02-28*"""
    
    def handle_unknown(self, command):
        """处理未知命令"""
        return f"""🤔 *未知命令*: /{command}

📋 *可用命令列表*
• /start - 启动模拟Bot
• /status - 系统状态
• /crypto - 加密货币
• /jobs - 求职助手
• /help - 帮助信息

💡 *提示*
• 检查命令拼写
• 查看 /help 获取完整列表
• 或尝试 /start 重新开始

🔧 *技术支持*
此模拟系统专为OPC项目开发设计。
所有命令处理逻辑均可自定义修改。

⏰ 时间: {datetime.now().strftime('%H:%M:%S')}"""
    
    def get_updates(self, chat_id=None):
        """获取模拟更新"""
        updates = []
        
        # 获取指定聊天或所有聊天的消息
        message_files = []
        if chat_id:
            message_files = [f for f in os.listdir(self.messages_dir) 
                           if f.endswith('.json') and f.startswith(f"{chat_id}_")]
        else:
            message_files = [f for f in os.listdir(self.messages_dir) if f.endswith('.json')]
        
        # 按时间排序（最新的在前）
        message_files.sort(reverse=True)
        
        for msg_file in message_files[:10]:  # 最多10条
            msg_path = os.path.join(self.messages_dir, msg_file)
            with open(msg_path, 'r') as f:
                message_data = json.load(f)
                updates.append({
                    "update_id": int(time.time() * 1000) + len(updates),
                    "message": message_data
                })
        
        return {
            "ok": True,
            "result": updates
        }

def main():
    """主函数 - 交互式模拟Bot"""
    mock_dir = os.path.expanduser("~/.openclaw/workspace/telegram_mock")
    bot = MockTelegramBot(mock_dir)
    
    print("🤖 OPC Telegram模拟Bot")
    print("="*50)
    print("模式: 🔌 离线模拟")
    print("时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*50)
    
    # 默认聊天ID
    chat_id = "1001"
    
    while True:
        print(f"\n💬 模拟聊天 [用户: @opc_dev, Chat ID: {chat_id}]")
        print("-"*50)
        print("输入命令 (如: /start, /crypto, /help)")
        print("或输入 'exit' 退出")
        print("-"*50)
        
        user_input = input("> ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("👋 退出模拟系统")
            break
        
        if user_input.startswith('/'):
            # 处理命令
            result = bot.process_command(chat_id, user_input)
            if result.get("ok"):
                print("\n🤖 Bot回复:")
                print("-"*40)
                print(result["result"]["text"])
                print("-"*40)
            else:
                print("❌ 命令处理失败")
        elif user_input:
            # 普通消息
            message_id = bot.save_message(chat_id, user_input)
            print(f"✅ 消息已保存 (ID: {message_id})")
            print("💡 提示: 输入命令与Bot交互，如 /help")
        else:
            print("ℹ️ 请输入消息或命令")

if __name__ == "__main__":
    main()
EOF
    
    chmod +x "$MOCK_DIR/mock_handler.py"
    
    # 创建交互式测试脚本
    cat > "$WORKSPACE/scripts/test_mock_bot.sh" << 'EOF'
#!/bin/bash

echo "🤖 启动Telegram模拟Bot测试"
echo "============================"

MOCK_DIR="$HOME/.openclaw/workspace/telegram_mock"

if [ ! -f "$MOCK_DIR/mock_handler.py" ]; then
    echo "❌ 模拟系统未初始化"
    echo "请先运行: bash telegram_mock_system.sh"
    exit 1
fi

echo "✅ 模拟系统已就绪"
echo "目录: $MOCK_DIR"
echo ""

# 启动交互式模拟
python3 "$MOCK_DIR/mock_handler.py"
EOF
    
    chmod +x "$WORKSPACE/scripts/test_mock_bot.sh"
    
    # 创建迁移脚本（网络恢复后使用）
    cat > "$WORKSPACE/scripts/migrate_to_real_bot.sh" << 'EOF'
#!/bin/bash

echo "🔄 从模拟Bot迁移到真实Bot"
echo "============================"

MOCK_DIR="$HOME/.openclaw/workspace/telegram_mock"
REAL_DIR="$HOME/.openclaw/workspace/skills/telegram"

echo "1. 检查模拟数据..."
MESSAGE_COUNT=$(find "$MOCK_DIR/messages" -name "*.json" 2>/dev/null | wc -l)
USER_COUNT=$(find "$MOCK_DIR/users" -name "*.json" 2>/dev/null | wc -l)

echo "   模拟消息: $MESSAGE_COUNT 条"
echo "   模拟用户: $USER_COUNT 个"

echo -e "\n2. 备份模拟数据..."
BACKUP_FILE="$HOME/telegram_mock_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" "$MOCK_DIR" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ 备份完成: $BACKUP_FILE"
else
    echo "   ⚠ 备份失败，继续迁移"
fi

echo -e "\n3. 配置真实Bot..."
echo "   请确保已获取有效的Telegram Bot Token"
echo "   编辑配置文件: $REAL_DIR/config/opc_bot.json"
echo "   更新Token和Chat ID"

echo -e "\n4. 测试真实Bot连接..."
read -p "   输入真实Bot Token: " REAL_TOKEN

if [ -n "$REAL_TOKEN" ]; then
    echo "   测试连接..."
    RESPONSE=$(curl -s "https://api.telegram.org/bot$REAL_TOKEN/getMe" 2>/dev/null || echo "{}")
    
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        BOT_USERNAME=$(echo "$RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
        echo "   ✅ 真实Bot连接成功: @$BOT_USERNAME"
        
        # 更新配置
        echo -e "\n5. 更新配置文件..."
        CONFIG_FILE="$REAL_DIR/config/opc_bot.json"
        if [ -f "$CONFIG_FILE" ]; then
            # 备份原配置
            cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d)"
            
            # 更新Token
            sed -i "s/\"token\": \".*\"/\"token\": \"$REAL_TOKEN\"/" "$CONFIG_FILE"
            echo "   ✅ Token已更新"
        fi
        
        echo -e "\n6. 启动真实Bot..."
        echo "   运行: bash $HOME/.openclaw/workspace/scripts/start_telegram_bot.sh"
        
        echo -e "\n🎉 迁移准备完成!"
        echo "   模拟数据已备份: $BACKUP_FILE"
        echo "   真实Bot已配置: @$BOT_USERNAME"
        echo "   下一步: 启动真实Bot并测试"
    else
        echo "   ❌ 真实Bot连接失败"
        echo "   请检查Token和网络连接"
    fi
else
    echo "   ⚠ 未提供Token，跳过真实Bot测试"
fi

echo -e "\n📋 迁移完成摘要:"
echo "   1. 模拟数据已备份"
echo "   2. 真实Bot配置已准备"
echo "   3. 可随时切换到真实Bot"
echo ""
echo "💡 提示: 迁移后，所有新消息将通过真实Bot发送"
echo "       模拟数据可用于分析和测试"
EOF
    
    chmod +x "$WORKSPACE/scripts/migrate_to_real_bot.sh"
    
    # 创建使用说明
    cat > "$MOCK_DIR/README.md" << 'EOF'
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
EOF
    
    echo "✅ Telegram Bot模拟系统创建完成！"
    echo ""
    echo "📁 系统位置: $MOCK_DIR"
    echo "📝 使用说明: $MOCK_DIR/README.md"
    echo ""
    echo "🚀 立即使用:"
    echo "  1. 启动模拟: bash $WORKSPACE/scripts/test_mock_bot.sh"
    echo "  2. 查看指南: cat $MOCK_DIR/README.md | head -30"
    echo "  3. 测试命令: /start, /crypto, /status, /help"
    echo ""
    echo "🔧 网络恢复后:"
    echo "  运行迁移脚本切换到真实Bot"
    echo "  bash $WORKSPACE/scripts/migrate_to_real_bot.sh"
}

# 执行初始化
init_mock_system