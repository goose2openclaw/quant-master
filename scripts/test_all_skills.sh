#!/bin/bash
echo "🧪 OpenClaw技能测试套件"
echo "========================"
echo "测试时间: $(date)"
echo ""

# 测试函数
test_skill() {
    local skill=$1
    local test_cmd=$2
    
    echo -n "测试 $skill... "
    
    if eval "$test_cmd" &> /dev/null; then
        echo "✅ 通过"
        return 0
    else
        echo "❌ 失败"
        return 1
    fi
}

# 测试列表
declare -A TESTS=(
    ["github"]="git --version"
    ["cron"]="crontab -l 2>/dev/null"
    ["shell"]="bash --version"
    ["telegram"]="python3 -c \"import requests; print('requests ok')\""
)

# 运行测试
PASSED=0
TOTAL=0

for skill in "${!TESTS[@]}"; do
    if [ -f "$HOME/.openclaw/workspace/skills/$skill/SKILL.md" ]; then
        ((TOTAL++))
        test_skill "$skill" "${TESTS[$skill]}"
        if [ $? -eq 0 ]; then
            ((PASSED++))
        fi
    fi
done

# 输出结果
echo ""
echo "📊 测试结果:"
echo "  通过: $PASSED/$TOTAL"
echo "  成功率: $((PASSED * 100 / TOTAL))%"

if [ $PASSED -eq $TOTAL ]; then
    echo "🎉 所有技能测试通过！"
else
    echo "⚠ 部分技能测试失败，请检查依赖"
fi
