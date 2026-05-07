#!/bin/bash

echo "🌐 网络恢复后自动执行脚本"
echo "=========================="

# 检查网络连接
check_network() {
    echo "检查网络连接..."
    
    # 测试几个常用网站
    SITES=("api.telegram.org" "api.coingecko.com" "github.com")
    
    for site in "${SITES[@]}"; do
        if ping -c 1 -W 2 "$site" &> /dev/null; then
            echo "✅ $site 可达"
            return 0
        else
            echo "❌ $site 不可达"
        fi
    done
    
    return 1
}

# Telegram配置测试
test_telegram() {
    echo ""
    echo "🤖 测试Telegram配置..."
    
    if [ -f "/home/goose/.openclaw/workspace/scripts/test_telegram_simple.py" ]; then
        python3 /home/goose/.openclaw/workspace/scripts/test_telegram_simple.py
    else
        echo "❌ Telegram测试脚本不存在"
    fi
}

# 加密货币API测试
test_crypto_api() {
    echo ""
    echo "🪙 测试加密货币API..."
    
    if [ -f "/home/goose/.openclaw/workspace/scripts/simple_crypto_check.py" ]; then
        python3 /home/goose/.openclaw/workspace/scripts/simple_crypto_check.py
    else
        echo "❌ 加密货币API测试脚本不存在"
    fi
}

# 安装等待的skills
install_pending_skills() {
    echo ""
    echo "📦 检查待安装的技能..."
    
    # 检查clawhub速率限制
    echo "等待clawhub速率限制解除..."
    echo "可以手动安装的技能:"
    echo "1. 从OpenClaw bundled技能启用: github, notion等"
    echo "2. 使用: openclaw skills list 查看可用技能"
    echo "3. 使用: openclaw skills enable <skill-name> 启用技能"
}

# 配置OpenClaw cron任务
setup_cron_tasks() {
    echo ""
    echo "⏰ 配置自动化任务..."
    
    echo "创建每日加密货币检查任务:"
    cat > /tmp/opc_daily_check.sh << 'EOF'
#!/bin/bash
echo "🪙 每日加密货币检查 - $(date)"
echo "使用模拟数据或真实API（如果网络可用）"
# 这里可以调用您的加密货币检查脚本
EOF
    
    chmod +x /tmp/opc_daily_check.sh
    echo "✅ 示例cron脚本已创建: /tmp/opc_daily_check.sh"
    
    echo ""
    echo "手动配置cron任务:"
    echo "1. crontab -e"
    echo "2. 添加: 0 8 * * * /path/to/your/script.sh"
    echo "3. 保存退出"
}

# 主函数
main() {
    echo "OPC项目网络恢复检查"
    echo "===================="
    
    # 检查网络
    if check_network; then
        echo ""
        echo "✅ 网络连接正常，开始测试..."
        
        # 执行测试
        test_telegram
        test_crypto_api
        install_pending_skills
        setup_cron_tasks
        
        echo ""
        echo "========================================"
        echo "🎉 所有测试完成！"
        echo "========================================"
        echo "下一步:"
        echo "1. 获取Telegram Chat ID并测试消息发送"
        echo "2. 配置OpenClaw与Telegram集成"
        echo "3. 开始开发OPC加密货币监控"
        echo "4. 学习Solidity智能合约开发"
    else
        echo ""
        echo "❌ 网络连接异常"
        echo ""
        echo "离线开发建议:"
        echo "1. 继续开发模拟数据系统"
        echo "2. 学习Solidity智能合约"
        echo "3. 设计OPC项目架构"
        echo "4. 编写文档和测试用例"
        
        echo ""
        echo "网络恢复后运行此脚本:"
        echo "bash when_network_back.sh"
    fi
}

# 执行主函数
main