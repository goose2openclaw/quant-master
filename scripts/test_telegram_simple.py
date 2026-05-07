#!/usr/bin/env python3
"""
简单的Telegram Bot测试脚本
使用您提供的Token进行测试
"""

import requests
import json
from datetime import datetime

# Telegram Bot Token（您提供的）
BOT_TOKEN = "8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def test_bot_connection():
    """测试Bot连接"""
    print("🔗 测试Telegram Bot连接...")
    
    try:
        response = requests.get(f"{BASE_URL}/getMe", timeout=10)
        data = response.json()
        
        if data.get("ok"):
            bot_info = data["result"]
            print(f"✅ Bot连接成功!")
            print(f"   Bot ID: {bot_info['id']}")
            print(f"   用户名: @{bot_info['username']}")
            print(f"   名称: {bot_info['first_name']}")
            return bot_info
        else:
            print(f"❌ Bot连接失败: {data.get('description', '未知错误')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return None

def get_updates():
    """获取最近的更新"""
    print("\n📨 获取最近的消息...")
    
    try:
        response = requests.get(f"{BASE_URL}/getUpdates", timeout=10)
        data = response.json()
        
        if data.get("ok"):
            updates = data["result"]
            if updates:
                print(f"✅ 找到 {len(updates)} 条消息")
                for i, update in enumerate(updates[:3]):  # 只显示前3条
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "(无文本)")
                        print(f"   {i+1}. Chat ID: {chat_id}, 消息: {text[:50]}...")
                return updates
            else:
                print("ℹ️ 没有新消息")
                return []
        else:
            print(f"❌ 获取消息失败: {data.get('description', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def send_test_message(chat_id=None):
    """发送测试消息"""
    if not chat_id:
        print("\n📝 需要Chat ID来发送测试消息")
        print("请从Telegram中获取你的Chat ID:")
        print("1. 在Telegram中发送消息给你的Bot")
        print("2. 运行此脚本查看Chat ID")
        print("3. 然后运行: python3 test_telegram_simple.py --send <chat_id>")
        return False
    
    print(f"\n📤 发送测试消息到 Chat ID: {chat_id}")
    
    message = f"""🚀 OPC项目测试消息

✅ Telegram Bot配置成功!
⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 状态: 系统运行正常

下一步:
1. 配置加密货币监控
2. 开发智能合约
3. 创建求职助手

这是一个自动发送的测试消息。"""

    try:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            print("✅ 测试消息发送成功!")
            print(f"   消息ID: {data['result']['message_id']}")
            return True
        else:
            print(f"❌ 发送失败: {data.get('description', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def set_commands():
    """设置Bot命令"""
    print("\n⚙️ 设置Bot命令...")
    
    commands = [
        {"command": "start", "description": "启动OPC系统"},
        {"command": "status", "description": "查看系统状态"},
        {"command": "crypto", "description": "加密货币行情"},
        {"command": "jobs", "description": "求职助手"},
        {"command": "help", "description": "帮助信息"}
    ]
    
    try:
        payload = {"commands": commands}
        response = requests.post(f"{BASE_URL}/setMyCommands", json=payload, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            print("✅ Bot命令设置成功!")
            for cmd in commands:
                print(f"   /{cmd['command']} - {cmd['description']}")
            return True
        else:
            print(f"❌ 命令设置失败: {data.get('description', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    print("="*60)
    print("🤖 OPC Telegram Bot测试工具")
    print("="*60)
    
    # 测试连接
    bot_info = test_bot_connection()
    if not bot_info:
        return
    
    # 获取更新（查看Chat ID）
    updates = get_updates()
    
    # 设置命令
    set_commands()
    
    # 如果有更新，显示如何使用
    if updates:
        print("\n💡 使用说明:")
        print("1. 从上面的消息中找到你的Chat ID")
        print("2. 运行: python3 test_telegram_simple.py --send <你的chat_id>")
        print("3. 或者在Telegram中发送 /start 命令")
    
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--send":
        if len(sys.argv) > 2:
            chat_id = sys.argv[2]
            send_test_message(chat_id)
        else:
            print("请提供Chat ID: python3 test_telegram_simple.py --send <chat_id>")
    else:
        main()