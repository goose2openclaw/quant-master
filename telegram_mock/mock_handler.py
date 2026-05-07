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
