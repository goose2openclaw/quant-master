#!/bin/bash

# OpenClaw Web界面快速访问脚本
# 根据语音指令"访问web界面"创建

echo "=== OpenClaw Web界面访问 ==="
echo "时间: $(date)"
echo ""

# 检查服务状态
echo "🔍 检查Web服务状态..."
echo ""

# 1. 检查Mission Control (端口8080)
echo "1. Mission Control 任务管理系统:"
if ss -tulpn | grep -q ":8080 "; then
    echo "   ✅ 运行中 (端口: 8080)"
    echo "   📍 URL: http://localhost:8080"
    
    # 测试HTTP响应
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080)
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "   🌐 HTTP状态: $HTTP_STATUS (正常)"
        
        # 获取页面标题
        TITLE=$(curl -s http://localhost:8080 | grep -o "<title>[^<]*</title>" | sed 's/<title>//;s/<\/title>//')
        if [ -n "$TITLE" ]; then
            echo "   📄 页面标题: $TITLE"
        fi
    else
        echo "   ⚠️ HTTP状态: $HTTP_STATUS (可能有问题)"
    fi
else
    echo "   ❌ 未运行"
fi

echo ""

# 2. 检查OpenClaw Gateway (端口18789)
echo "2. OpenClaw Gateway 管理界面:"
if ss -tulpn | grep -q ":18789 "; then
    echo "   ✅ 运行中 (端口: 18789)"
    echo "   📍 URL: http://localhost:18789"
    
    # 测试API健康检查
    if curl -s -f http://localhost:18789/api/health > /dev/null 2>&1; then
        echo "   💚 健康检查: 通过"
        
        # 获取健康状态详情
        HEALTH_JSON=$(curl -s http://localhost:18789/api/health)
        STATUS=$(echo "$HEALTH_JSON" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('status', '未知'))")
        echo "   📊 系统状态: $STATUS"
    else
        echo "   ⚠️ 健康检查: 失败"
    fi
else
    echo "   ❌ 未运行"
fi

echo ""
echo "🚀 访问选项:"
echo ""

# 显示访问选项
echo "请选择访问方式:"
echo "1) 在浏览器中打开 Mission Control (任务管理)"
echo "2) 在浏览器中打开 OpenClaw Gateway (系统管理)"
echo "3) 两个都打开"
echo "4) 显示URL，手动访问"
echo "5) 测试API端点"
echo "6) 退出"
echo ""

read -p "请输入选择 (1-6): " choice

case $choice in
    1)
        echo "正在打开 Mission Control..."
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:8080
        elif command -v open > /dev/null; then
            open http://localhost:8080
        else
            echo "请手动在浏览器中访问: http://localhost:8080"
        fi
        ;;
    2)
        echo "正在打开 OpenClaw Gateway..."
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:18789
        elif command -v open > /dev/null; then
            open http://localhost:18789
        else
            echo "请手动在浏览器中访问: http://localhost:18789"
        fi
        ;;
    3)
        echo "正在打开所有Web界面..."
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:8080
            xdg-open http://localhost:18789
        elif command -v open > /dev/null; then
            open http://localhost:8080
            open http://localhost:18789
        else
            echo "请手动访问:"
            echo "Mission Control: http://localhost:8080"
            echo "OpenClaw Gateway: http://localhost:18789"
        fi
        ;;
    4)
        echo ""
        echo "📋 Web界面URL列表:"
        echo "========================"
        echo "🔧 Mission Control (任务管理)"
        echo "   URL: http://localhost:8080"
        echo "   功能: 多智能体任务管理看板"
        echo ""
        echo "⚙️ OpenClaw Gateway (系统管理)"
        echo "   URL: http://localhost:18789"
        echo "   功能: 系统状态、配置、日志"
        echo ""
        echo "🛠️ API端点:"
        echo "   Mission Control API: http://localhost:8080/api/tasks"
        echo "   Gateway健康检查: http://localhost:18789/api/health"
        echo "========================"
        ;;
    5)
        echo ""
        echo "🔧 测试API端点..."
        echo ""
        
        echo "1. Mission Control任务API:"
        curl -s http://localhost:8080/api/tasks | python3 -m json.tool 2>/dev/null | head -20 || echo "   API响应不是JSON格式或无法访问"
        
        echo ""
        echo "2. Gateway健康检查API:"
        curl -s http://localhost:18789/api/health | python3 -m json.tool 2>/dev/null || echo "   API无法访问"
        ;;
    6)
        echo "退出..."
        exit 0
        ;;
    *)
        echo "无效选择"
        ;;
esac

echo ""
echo "📚 相关文档:"
echo "   完整指南: /home/goose/.openclaw/workspace/web_interface_access.md"
echo "   创建时间: 2026-03-01 05:35"
echo "   创建原因: 响应语音指令'访问web界面'"
echo ""
echo "✅ 脚本执行完成"