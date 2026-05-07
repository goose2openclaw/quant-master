#!/bin/bash

echo "🎮 OPC项目控制中心"
echo "=================="

while true; do
    echo ""
    echo "请选择操作:"
    echo "1. 📊 查看系统状态"
    echo "2. 🛠️  管理技能"
    echo "3. ⚙️  配置设置"
    echo "4. 📈 加密货币监控"
    echo "5. 💼 求职助手"
    echo "6. 📝 智能合约开发"
    echo "7. 🔔 通知设置"
    echo "8. 🚪 退出"
    echo ""
    read -p "选择 (1-8): " choice
    
    case $choice in
        1)
            echo -e "\n📊 系统状态:"
            echo "------------"
            bash "$HOME/.openclaw/workspace/skills/shell/scripts/system_monitor.sh" all
            ;;
        2)
            echo -e "\n🛠️ 技能管理:"
            echo "------------"
            echo "已安装技能:"
            find "$HOME/.openclaw/workspace/skills" -name "SKILL.md" | xargs -I {} dirname {} | xargs -I {} basename {} | sort
            ;;
        3)
            echo -e "\n⚙️ 配置设置:"
            echo "------------"
            echo "1. 查看Telegram配置"
            echo "2. 查看GitHub配置"
            echo "3. 查看Cron配置"
            read -p "选择: " config_choice
            case $config_choice in
                1) cat "$HOME/.openclaw/workspace/skills/telegram/config.json" | jq . ;;
                2) cat "$HOME/.openclaw/workspace/skills/github/config.json" | jq . ;;
                3) cat "$HOME/.openclaw/workspace/skills/cron/config.json" | jq . ;;
            esac
            ;;
        4)
            echo -e "\n📈 加密货币监控:"
            echo "----------------"
            echo "启动加密货币监控..."
            bash "$HOME/.openclaw/workspace/skills/opc-crypto-monitor/scripts/opc-crypto-monitor_main.sh" start
            ;;
        5)
            echo -e "\n💼 求职助手:"
            echo "------------"
            echo "启动求职助手..."
            bash "$HOME/.openclaw/workspace/skills/opc-job-assistant/scripts/opc-job-assistant_main.sh" start
            ;;
        6)
            echo -e "\n📝 智能合约开发:"
            echo "----------------"
            echo "打开智能合约目录..."
            cd "$HOME/opc-project/smart-contracts" && ls -la
            ;;
        7)
            echo -e "\n🔔 通知设置:"
            echo "------------"
            echo "1. 测试Telegram通知"
            echo "2. 查看通知配置"
            read -p "选择: " notify_choice
            case $notify_choice in
                1) echo "需要Chat ID来测试" ;;
                2) cat "$HOME/.openclaw/workspace/skills/telegram/config.json" | jq '.telegram.notifications' ;;
            esac
            ;;
        8)
            echo "再见！"
            exit 0
            ;;
        *)
            echo "无效选择"
            ;;
    esac
    
    echo ""
    read -p "按回车键继续..."
done
