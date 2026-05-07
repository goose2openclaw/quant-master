#!/usr/bin/env python3
"""
通过 @BotFather 创建新的 Telegram Bot
注意：这需要手动与 @BotFather 交互
"""

import json
import os
import sys
import time

def print_instructions():
    """打印创建Bot的步骤说明"""
    print("=" * 70)
    print("🤖 创建新的 Telegram Bot - 手动步骤")
    print("=" * 70)
    print()
    print("📱 请在 Telegram 应用中执行以下步骤：")
    print()
    print("1. 🔍 搜索 @BotFather")
    print("2. 💬 发送 /start 开始对话")
    print("3. 🆕 发送 /newbot 创建新Bot")
    print("4. 📝 按照提示：")
    print("   • 输入Bot名称 (例如: OPC Assistant)")
    print("   • 输入Bot用户名 (必须以 'bot' 结尾，例如: opc_assistant_bot)")
    print("5. 🔑 复制生成的 Bot Token")
    print("6. 📋 将Token粘贴到下面")
    print()
    print("=" * 70)

def validate_token(token):
    """验证Token格式"""
    if not token:
        return False, "Token不能为空"
    
    # 基本格式检查：数字:字母数字
    parts = token.split(':')
    if len(parts) != 2:
        return False, "Token格式错误，应为 '数字:字母' 格式"
    
    if not parts[0].isdigit():
        return False, "Token第一部分应为数字"
    
    if len(parts[1]) < 30:
        return False, "Token第二部分太短"
    
    return True, "Token格式正确"

def test_token(token):
    """测试Token是否有效"""
    import requests
    
    print(f"🔍 测试Token: {token[:10]}...{token[-4:]}")
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            print(f"✅ Token有效！")
            print(f"   Bot ID: {data['result']['id']}")
            print(f"   用户名: @{data['result']['username']}")
            print(f"   名称: {data['result']['first_name']}")
            return True, data['result']
        else:
            error_msg = data.get('description', '未知错误')
            print(f"❌ Token无效: {error_msg}")
            return False, error_msg
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False, str(e)

def update_openclaw_config(token, bot_info):
    """更新OpenClaw配置"""
    config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # 更新Telegram配置
        if 'channels' not in config:
            config['channels'] = {}
        
        if 'telegram' not in config['channels']:
            config['channels']['telegram'] = {
                'enabled': True,
                'dmPolicy': 'pairing',
                'allowFrom': [],
                'groupPolicy': 'allowlist',
                'streaming': 'off'
            }
        
        config['channels']['telegram']['botToken'] = token
        
        # 保存配置
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ OpenClaw配置已更新: {config_path}")
        
        # 创建备份配置
        backup_dir = os.path.expanduser("~/.openclaw/workspace/secure")
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_config = {
            "telegram_bot": {
                "token": token,
                "username": f"@{bot_info.get('username')}",
                "bot_id": bot_info.get('id'),
                "name": bot_info.get('first_name'),
                "configured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "status": "active"
            },
            "security": {
                "file_permissions": "600",
                "encryption_recommended": True
            }
        }
        
        backup_path = os.path.join(backup_dir, "telegram_config_new.json")
        with open(backup_path, 'w') as f:
            json.dump(backup_config, f, indent=2)
        
        print(f"✅ 备份配置已保存: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新配置失败: {e}")
        return False

def restart_openclaw():
    """重启OpenClaw服务"""
    print("\n🔄 重启OpenClaw服务...")
    
    try:
        import subprocess
        
        # 检查服务状态
        result = subprocess.run(
            ["openclaw", "gateway", "status"],
            capture_output=True,
            text=True
        )
        
        if "running" in result.stdout.lower():
            print("✅ OpenClaw网关正在运行")
            
            # 重启服务
            print("🔄 正在重启...")
            restart_result = subprocess.run(
                ["openclaw", "gateway", "restart"],
                capture_output=True,
                text=True
            )
            
            if restart_result.returncode == 0:
                print("✅ OpenClaw服务重启成功")
                return True
            else:
                print(f"❌ 重启失败: {restart_result.stderr}")
                return False
        else:
            print("⚠ OpenClaw网关未运行，尝试启动...")
            start_result = subprocess.run(
                ["openclaw", "gateway", "start"],
                capture_output=True,
                text=True
            )
            
            if start_result.returncode == 0:
                print("✅ OpenClaw服务启动成功")
                return True
            else:
                print(f"❌ 启动失败: {start_result.stderr}")
                return False
                
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return False

def verify_connection():
    """验证连接状态"""
    print("\n🔍 验证Telegram连接状态...")
    
    try:
        import subprocess
        
        result = subprocess.run(
            ["openclaw", "status", "--deep"],
            capture_output=True,
            text=True
        )
        
        if "Telegram.*OK" in result.stdout:
            print("✅ Telegram通道状态: 正常")
            return True
        elif "failed.*401" in result.stdout:
            print("❌ Telegram通道状态: 认证失败")
            return False
        else:
            print("⚠ 无法确定Telegram状态")
            print("运行 'openclaw status --deep' 查看详情")
            return None
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print_instructions()
    
    # 获取Token
    while True:
        print("\n" + "-" * 50)
        token = input("请输入新的Bot Token (或输入 'q' 退出): ").strip()
        
        if token.lower() == 'q':
            print("👋 退出")
            return
        
        # 验证格式
        valid, msg = validate_token(token)
        if not valid:
            print(f"❌ {msg}")
            continue
        
        # 测试Token
        success, result = test_token(token)
        if not success:
            print("⚠ 请检查Token是否正确，或创建新的Bot")
            retry = input("重试? (y/n): ").strip().lower()
            if retry != 'y':
                continue
        else:
            break
    
    # 更新配置
    print("\n" + "=" * 50)
    print("🔄 更新系统配置...")
    
    if update_openclaw_config(token, result):
        print("✅ 配置更新成功")
        
        # 重启服务
        if restart_openclaw():
            print("✅ 服务重启成功")
            
            # 等待服务启动
            print("⏳ 等待服务启动...")
            time.sleep(3)
            
            # 验证连接
            if verify_connection():
                print("\n" + "=" * 70)
                print("🎉 Telegram Bot配置完成！")
                print("=" * 70)
                print()
                print("✅ 已完成:")
                print(f"   • Bot名称: {result.get('first_name')}")
                print(f"   • 用户名: @{result.get('username')}")
                print(f"   • Bot ID: {result.get('id')}")
                print(f"   • Token: {token[:10]}...{token[-4:]}")
                print()
                print("🚀 下一步:")
                print("   1. 在Telegram中搜索: @" + result.get('username'))
                print("   2. 发送 /start 开始对话")
                print("   3. 发送任意消息测试")
                print()
                print("🔧 检查状态:")
                print("   openclaw status --deep")
                print()
                print("📝 配置文件:")
                print("   ~/.openclaw/openclaw.json")
                print("   ~/.openclaw/workspace/secure/telegram_config_new.json")
                print("=" * 70)
            else:
                print("\n⚠ 连接验证失败，请手动检查:")
                print("   openclaw status --deep")
        else:
            print("\n❌ 服务重启失败，请手动重启:")
            print("   openclaw gateway restart")
    else:
        print("\n❌ 配置更新失败")

if __name__ == "__main__":
    main()