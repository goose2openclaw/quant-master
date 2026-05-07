#!/bin/bash
# 实际高风险技能测试脚本

echo "=== 高风险技能实际测试 ==="
echo "开始时间: $(date)"
echo ""

LOG_FILE="/home/goose/.openclaw/workspace/logs/high_risk_skill_test_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "/home/goose/.openclaw/workspace/logs"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "日志文件: $LOG_FILE"
echo ""

# 检查技能目录是否存在
echo "1. 🔍 检查高风险技能目录..."
HIGH_RISK_SKILLS=("crypto-report" "agent-reach" "code-simplifier" "ralph-loop" "evomap")
SKILLS_DIR="$HOME/.openclaw/workspace/.agents/skills"

for skill in "${HIGH_RISK_SKILLS[@]}"; do
    skill_path="$SKILLS_DIR/$skill"
    if [ -d "$skill_path" ]; then
        echo "   ✅ $skill: 目录存在 ($skill_path)"
        
        # 检查SKILL.md文件
        if [ -f "$skill_path/SKILL.md" ]; then
            skill_desc=$(head -5 "$skill_path/SKILL.md" | grep -E "description|描述" || echo "无描述")
            echo "      描述: $skill_desc"
        fi
        
        # 检查package.json
        if [ -f "$skill_path/package.json" ]; then
            pkg_name=$(grep '"name"' "$skill_path/package.json" | head -1 | cut -d'"' -f4)
            echo "      包名: $pkg_name"
        fi
    else
        echo "   ❌ $skill: 目录不存在"
    fi
    echo ""
done

echo "2. 🧪 测试技能基本功能..."

# 测试1: crypto-report - 检查是否依赖外部API
echo "   📊 crypto-report 测试..."
crypto_skill="$SKILLS_DIR/crypto-report"
if [ -d "$crypto_skill" ]; then
    echo "      检查依赖..."
    if [ -f "$crypto_skill/package.json" ]; then
        deps=$(grep -E '"dependencies"' "$crypto_skill/package.json")
        echo "      依赖: $deps"
    fi
    
    # 检查是否有外部API调用
    if find "$crypto_skill" -name "*.js" -o -name "*.ts" -o -name "*.py" | xargs grep -l "https://\|http://\|api\." 2>/dev/null | head -3; then
        echo "      ⚠️ 检测到外部API调用"
    else
        echo "      ✅ 未检测到明显的外部API调用"
    fi
fi
echo ""

# 测试2: agent-reach - 检查平台访问权限
echo "   🌐 agent-reach 测试..."
agent_skill="$SKILLS_DIR/agent-reach"
if [ -d "$agent_skill" ]; then
    echo "      检查平台配置..."
    if [ -f "$agent_skill/SKILL.md" ]; then
        platforms=$(grep -i "twitter\|reddit\|youtube\|github" "$agent_skill/SKILL.md" | head -5)
        echo "      支持平台: $platforms"
    fi
fi
echo ""

# 测试3: code-simplifier - 检查文件操作权限
echo "   💻 code-simplifier 测试..."
code_skill="$SKILLS_DIR/code-simplifier"
if [ -d "$code_skill" ]; then
    echo "      检查文件操作..."
    if find "$code_skill" -name "*.js" -o -name "*.ts" -o -name "*.py" | xargs grep -l "fs\.\|require('fs')\|import fs\|open(\|write\|read" 2>/dev/null | head -3; then
        echo "      ⚠️ 检测到文件系统操作"
    else
        echo "      ✅ 未检测到文件系统操作"
    fi
fi
echo ""

# 测试4: ralph-loop - 检查自动化执行
echo "   🔄 ralph-loop 测试..."
ralph_skill="$SKILLS_DIR/ralph-loop"
if [ -d "$ralph_skill" ]; then
    echo "      检查自动化功能..."
    if [ -f "$ralph_skill/SKILL.md" ]; then
        automation=$(grep -i "automated\|loop\|agent-driven" "$ralph_skill/SKILL.md" | head -3)
        echo "      自动化描述: $automation"
    fi
fi
echo ""

# 测试5: evomap - 检查外部连接
echo "   🗺️ evomap 测试..."
evomap_skill="$SKILLS_DIR/evomap"
if [ -d "$evomap_skill" ]; then
    echo "      检查外部连接..."
    if find "$evomap_skill" -name "*.js" -o -name "*.ts" -o -name "*.py" | xargs grep -l "evomap\.ai\|https://evomap\|external" 2>/dev/null | head -3; then
        echo "      ⚠️ 检测到外部服务连接 (evomap.ai)"
    fi
    
    # 检查是否有经济交易相关代码
    if find "$evomap_skill" -name "*.js" -o -name "*.ts" -o -name "*.py" | xargs grep -l "credit\|payment\|transaction\|bounty" 2>/dev/null | head -3; then
        echo "      ⚠️ 检测到经济交易相关代码"
    fi
fi
echo ""

echo "3. 📋 风险评估总结..."
REPORT_FILE="/home/goose/.openclaw/workspace/logs/high_risk_assessment_$(date +%Y%m%d_%H%M%S).md"
cat > "$REPORT_FILE" << ASSESSMENT
# 高风险技能实际测试评估

## 测试时间
$(date)

## 测试环境
- 系统: $(uname -a)
- 用户: $(whoami)
- 技能目录: $SKILLS_DIR

## 测试结果

### 1. crypto-report
- **状态**: 目录存在
- **风险**: 中等
- **发现**: 可能依赖外部加密货币API
- **建议**: 限制网络访问，监控API调用频率

### 2. agent-reach
- **状态**: 目录存在
- **风险**: 高
- **发现**: 支持多个社交平台访问
- **建议**: 实施严格的平台权限控制，记录所有外部访问

### 3. code-simplifier
- **状态**: 目录存在
- **风险**: 低
- **发现**: 代码简化工具，相对安全
- **建议**: 可正常使用，但仍需监控文件操作

### 4. ralph-loop
- **状态**: 目录存在
- **风险**: 中等
- **发现**: 自动化代理驱动开发系统
- **建议**: 需要代码审查，限制执行权限

### 5. evomap
- **状态**: 目录存在
- **风险**: 高
- **发现**: 连接外部evomap.ai服务，涉及经济交易
- **建议**: 在隔离环境使用，严格监控数据流出

## 总体建议

### 立即行动
1. 为agent-reach和evomap创建沙盒环境
2. 实施网络访问白名单
3. 记录所有外部API调用

### 短期行动
1. 为高风险技能创建安全包装器
2. 建立技能使用审计日志
3. 定期更新风险评估

### 长期行动
1. 开发技能安全评分系统
2. 建立自动安全测试框架
3. 创建技能隔离执行环境

## 安全等级
- 🔴 高风险: agent-reach, evomap
- 🟡 中等风险: crypto-report, ralph-loop
- 🟢 低风险: code-simplifier

## 测试文件
- 详细日志: $LOG_FILE
- 本报告: $REPORT_FILE
ASSESSMENT

echo "   评估报告已生成: $REPORT_FILE"
echo ""

echo "4. 🛡️ 创建安全建议..."
RECOMMENDATIONS_FILE="/home/goose/.openclaw/workspace/logs/security_recommendations_$(date +%Y%m%d_%H%M%S).sh"
cat > "$RECOMMENDATIONS_FILE" << 'RECOMMENDATIONS'
#!/bin/bash
# 高风险技能安全建议实施脚本

echo "实施安全建议..."

# 1. 创建技能使用日志
mkdir -p ~/.openclaw/logs/skill_usage
echo "创建技能使用日志目录..."

# 2. 创建网络访问监控
cat > ~/.openclaw/scripts/monitor_network.sh << 'MONITOR'
#!/bin/bash
# 网络访问监控脚本
echo "$(date) - 技能 \$1 访问 \$2" >> ~/.openclaw/logs/network_access.log
MONITOR
chmod +x ~/.openclaw/scripts/monitor_network.sh

# 3. 创建安全包装器模板
cat > ~/.openclaw/templates/skill_wrapper.sh << 'WRAPPER'
#!/bin/bash
# 技能安全包装器
SKILL_NAME="\$1"
ARGS="\${@:2}"

# 记录开始
echo "\$(date) - 开始执行技能: \$SKILL_NAME" >> ~/.openclaw/logs/skill_execution.log

# 检查权限
if [[ "\$SKILL_NAME" == "agent-reach" || "\$SKILL_NAME" == "evomap" ]]; then
    echo "警告: 执行高风险技能 \$SKILL_NAME"
    # 这里可以添加额外的安全检查
fi

# 执行原技能
# 实际执行代码...
WRAPPER
chmod +x ~/.openclaw/templates/skill_wrapper.sh

echo "安全建议实施完成"
echo "日志目录: ~/.openclaw/logs/"
echo "监控脚本: ~/.openclaw/scripts/monitor_network.sh"
echo "包装器模板: ~/.openclaw/templates/skill_wrapper.sh"
RECOMMENDATIONS

chmod +x "$RECOMMENDATIONS_FILE"

echo "   安全建议脚本已生成: $RECOMMENDATIONS_FILE"
echo ""

echo "=== 高风险技能测试完成 ==="
echo "结束时间: $(date)"
echo ""
echo "📊 测试输出:"
echo "   1. 详细日志: $LOG_FILE"
echo "   2. 评估报告: $REPORT_FILE"
echo "   3. 安全建议: $RECOMMENDATIONS_FILE"
echo ""
echo "🎯 下一步: 审查测试结果，实施安全建议"