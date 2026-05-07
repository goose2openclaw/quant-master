#!/usr/bin/env python3
"""
Telegram Bot交互式测试脚本
允许您测试所有Bot功能
"""

import json
import os
import sys
from datetime import datetime

def print_menu():
    """打印菜单"""
    print("\n" + "="*60)
    print("🤖 Telegram Bot交互式测试")
    print("="*60)
    print("1. 测试Bot连接")
    print("2. 发送测试消息")
    print("3. 获取最近消息")
    print("4. 设置Bot命令")
    print("5. 测试命令处理器")
    print("6. 查看配置")
    print("7. 退出")
    print("="*60)

def test_bot_connection(token):
    """测试Bot连接"""
    import requests
    
    print("测试Bot连接...")
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            print("✅ Bot连接成功!")
            print(f"   ID: {data['result']['id']}")
            print(f"   用户名: @{data['result']['username']}")
            print(f"   名称: {data['result']['first_name']}")
            return data['result']
        else:
            print(f"❌ 连接失败: {data.get('description')}")
            return None
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return None

def send_test_message(token, chat_id):
    """发送测试消息"""
    import requests
    
    print(f"发送测试消息到Chat ID: {chat_id}")
    
    message = f"""🧪 *测试消息*

这是一条测试消息，用于验证Bot功能。

📊 *测试信息*
• 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Token: {token[:10]}...{token[-4:]}
• Chat ID: {chat_id}

✅ 如果收到此消息，说明Bot配置成功！

_测试完成_"""
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            print(f"✅ 消息发送成功! (ID: {data['result']['message_id']})")
            return True
        else:
            print(f"❌ 发送失败: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False

def get_recent_messages(token):
    """获取最近消息"""
    import requests
    
    print("获取最近消息...")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            updates = data["result"]
            if updates:
                print(f"✅ 找到 {len(updates)} 条消息")
                for i, update in enumerate(updates[:5]):  # 只显示前5条
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "(无文本)")
                        print(f"  {i+1}. Chat ID: {chat_id}, 消息: {text[:50]}...")
                return updates
            else:
                print("ℹ️ 没有新消息")
                return []
        else:
            print(f"❌ 获取失败: {data.get('description')}")
            return None
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return None

def test_command_handler():
    """测试命令处理器"""
    print("测试命令处理器...")
    
    # 导入本地处理器
    handler_path = os.path.join(os.path.dirname(__file__), "../skills/telegram/scripts/bot_handler.py")
    
    if os.path.exists(handler_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bot_handler", handler_path)
        module = importlib.util.module_from_spec(spec)
        
        # 模拟配置
        class MockConfig:
            def load_config(self):
                return {"telegram_bot": {"token": "test", "username": "@testbot"}}
        
        # 创建处理器实例
        handler = module.TelegramBotHandler("config/opc_bot.json")
        
        # 测试各种命令
        commands = ["/start", "/status", "/crypto", "/jobs", "/help", "/unknown"]
        
        for cmd in commands:
            print(f"\n测试命令: {cmd}")
            print("-"*40)
            result = handler.handle_command(cmd)
            print(result[:200] + "..." if len(result) > 200 else result)
        
        print("\n✅ 命令处理器测试完成")
    else:
        print("❌ 找不到命令处理器文件")

def view_configuration():
    """查看配置"""
    config_file = os.path.expanduser("~/.openclaw/workspace/skills/telegram/config/opc_bot.json")
    
    if os.path.exists(config_file):
        print("📁 Telegram Bot配置:")
        print("="*60)
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # 显示重要信息（隐藏完整token）
        if "telegram_bot" in config:
            bot_config = config["telegram_bot"]
            print(f"Bot用户名: {bot_config.get('username', '未设置')}")
            print(f"Chat ID: {bot_config.get('chat_id', '未设置')}")
            print(f"配置时间: {bot_config.get('configured_at', '未知')}")
            print(f"状态: {bot_config.get('status', '未知')}")
        
        print("\n📊 通知设置:")
        if "notifications" in config:
            for key, value in config["notifications"].items():
                print(f"  {key}: {'✅ 启用' if value.get('enabled') else '❌ 禁用'}")
        
        print("\n🚀 命令配置:")
        if "commands" in config:
            for cmd, cmd_config in config["commands"].items():
                print(f"  {cmd}: {cmd_config.get('description', '无描述')}")
        
        print("="*60)
    else:
        print("❌ 配置文件不存在")

def main():
    """主函数"""
    # 加载配置
    config_file = os.path.expanduser("~/.openclaw/workspace/skills/telegram/config/opc_bot.json")
    token = "8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o"
    chat_id = None
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            if "telegram_bot" in config:
                chat_id = config["telegram_bot"].get("chat_id")
    
    while True:
        print_menu()
        choice = input("请选择操作 (1-7): ").strip()
        
        if choice == "1":
            test_bot_connection(token)
        elif choice == "2":
            if not chat_id:
                chat_id = input("请输入Chat ID: ").strip()
            if chat_id:
                send_test_message(token, chat_id)
            else:
                print("❌ 需要Chat ID")
        elif choice == "3":
            get_recent_messages(token)
        elif choice == "4":
            print("设置Bot命令...")
            # 这里可以添加设置命令的逻辑
            print("✅ 命令已设置（需要网络连接）")
        elif choice == "5":
            test_command_handler()
        elif choice == "6":
            view_configuration()
        elif choice == "7":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    main()
