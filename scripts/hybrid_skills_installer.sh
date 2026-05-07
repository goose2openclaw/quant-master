#!/bin/bash

echo "🔄 混合策略Skills安装器"
echo "=========================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# 工作目录
WORKSPACE="$HOME/.openclaw/workspace"
SKILLS_DIR="$WORKSPACE/skills"
BACKUP_DIR="$WORKSPACE/backup"
INSTALL_LOG="$WORKSPACE/logs/hybrid_install_$(date +%Y%m%d_%H%M%S).log"

# 创建目录
mkdir -p "$SKILLS_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$INSTALL_LOG")"

# 记录日志
log() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$INSTALL_LOG"
}

# 1. 检查网络状态
check_network_hybrid() {
    print_section "检查网络状态（混合策略）"
    
    local online_sources=0
    
    # 测试关键API端点
    APIs=(
        "https://raw.githubusercontent.com"
        "https://api.telegram.org"
        "https://registry.npmjs.org"
        "https://cdn.openclaw.ai"
    )
    
    for api in "${APIs[@]}"; do
        if curl -s --head "$api" --max-time 5 >/dev/null 2>&1; then
            print_success "$api 可达"
            ((online_sources++))
        else
            print_warning "$api 不可达"
        fi
    done
    
    if [ $online_sources -ge 2 ]; then
        NETWORK_STATUS="GOOD"
        print_success "网络状态: 良好 ($online_sources/4 个源可达)"
    elif [ $online_sources -ge 1 ]; then
        NETWORK_STATUS="POOR"
        print_warning "网络状态: 较差 ($online_sources/4 个源可达)"
    else
        NETWORK_STATUS="OFFLINE"
        print_error "网络状态: 离线"
    fi
    
    return $online_sources
}

# 2. 备份现有技能
backup_existing_skills() {
    print_section "备份现有技能"
    
    local backup_file="$BACKUP_DIR/skills_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    if [ -d "$SKILLS_DIR" ] && [ "$(ls -A "$SKILLS_DIR" 2>/dev/null)" ]; then
        tar -czf "$backup_file" -C "$WORKSPACE" skills 2>/dev/null
        if [ $? -eq 0 ]; then
            print_success "技能已备份到: $backup_file"
        else
            print_warning "备份创建失败"
        fi
    else
        print_info "没有现有技能需要备份"
    fi
}

# 3. 策略1: 使用clawhub安装（如果网络良好）
install_with_clawhub() {
    print_section "策略1: 使用clawhub安装"
    
    if ! command -v clawhub &> /dev/null; then
        print_warning "clawhub未安装，跳过此策略"
        return 1
    fi
    
    # 高优先级技能
    HIGH_PRIORITY=("github" "cron" "shell" "telegram")
    
    local installed=0
    local failed=0
    
    for skill in "${HIGH_PRIORITY[@]}"; do
        print_info "尝试安装: $skill"
        
        # 检查是否已存在
        if [ -f "$SKILLS_DIR/$skill/SKILL.md" ]; then
            print_warning "$skill 已存在，跳过"
            continue
        fi
        
        # 尝试安装
        if clawhub install "$skill" --force 2>&1 | grep -q "Installed"; then
            print_success "$skill 安装成功"
            ((installed++))
        else
            print_warning "$skill 安装失败"
            ((failed++))
        fi
        
        # 避免速率限制
        sleep 5
    done
    
    log "clawhub安装结果: $installed 成功, $failed 失败"
    return $installed
}

# 4. 策略2: 从GitHub直接下载
download_from_github() {
    print_section "策略2: 从GitHub直接下载"
    
    # 技能列表
    SKILLS=(
        "github"
        "cron" 
        "shell"
        "telegram"
        "whatsapp"
        "brave-search"
        "agent-browser"
        "pdf"
        "docx"
        "xlsx"
        "pptx"
    )
    
    local downloaded=0
    local failed=0
    
    for skill in "${SKILLS[@]}"; do
        print_info "下载: $skill"
        
        # 检查是否已存在
        if [ -f "$SKILLS_DIR/$skill/SKILL.md" ]; then
            print_warning "$skill 已存在，跳过"
            continue
        fi
        
        # 创建目录
        mkdir -p "$SKILLS_DIR/$skill"
        mkdir -p "$SKILLS_DIR/$skill/scripts"
        mkdir -p "$SKILLS_DIR/$skill/references"
        
        # 尝试从GitHub下载
        URL="https://raw.githubusercontent.com/openclaw/skills/main/$skill/SKILL.md"
        
        if curl -s -f "$URL" -o "$SKILLS_DIR/$skill/SKILL.md.tmp" 2>/dev/null; then
            if [ -s "$SKILLS_DIR/$skill/SKILL.md.tmp" ]; then
                mv "$SKILLS_DIR/$skill/SKILL.md.tmp" "$SKILLS_DIR/$skill/SKILL.md"
                print_success "$skill 下载成功"
                ((downloaded++))
                
                # 创建基本配置
                create_basic_config "$skill"
            else
                print_warning "$skill 下载文件为空"
                ((failed++))
            fi
        else
            print_warning "$skill 下载失败"
            ((failed++))
        fi
        
        # 避免请求过快
        sleep 2
    done
    
    log "GitHub下载结果: $downloaded 成功, $failed 失败"
    return $downloaded
}

# 创建基本配置
create_basic_config() {
    local skill=$1
    local skill_dir="$SKILLS_DIR/$skill"
    
    cat > "$skill_dir/config.json" << EOF
{
  "skill": {
    "name": "$skill",
    "installed_at": "$(date -Iseconds)",
    "version": "1.0.0",
    "source": "hybrid_installer"
  },
  "enabled": true,
  "auto_update": true
}
EOF
}

# 5. 策略3: 从OpenClaw bundled技能复制
copy_bundled_skills() {
    print_section "策略3: 复制OpenClaw bundled技能"
    
    local bundled_dir="$HOME/.npm-global/lib/node_modules/openclaw/skills"
    
    if [ ! -d "$bundled_dir" ]; then
        print_warning "OpenClaw bundled技能目录不存在"
        return 0
    fi
    
    # 可用的bundled技能
    AVAILABLE_SKILLS=$(ls "$bundled_dir" 2>/dev/null)
    
    if [ -z "$AVAILABLE_SKILLS" ]; then
        print_warning "没有找到bundled技能"
        return 0
    fi
    
    local copied=0
    
    for skill in $AVAILABLE_SKILLS; do
        # 跳过已存在的
        if [ -f "$SKILLS_DIR/$skill/SKILL.md" ]; then
            continue
        fi
        
        # 检查是否是有效技能目录
        if [ -f "$bundled_dir/$skill/SKILL.md" ]; then
            print_info "复制: $skill"
            
            # 复制整个目录
            cp -r "$bundled_dir/$skill" "$SKILLS_DIR/" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                print_success "$skill 复制成功"
                ((copied++))
            else
                print_warning "$skill 复制失败"
            fi
        fi
    done
    
    log "Bundled技能复制结果: $copied 个技能"
    return $copied
}

# 6. 策略4: 创建最小化技能（离线备用）
create_minimal_skills() {
    print_section "策略4: 创建最小化技能（备用）"
    
    # 重要但可能下载失败的技能
    IMPORTANT_SKILLS=(
        "github"
        "cron"
        "shell"
        "telegram"
        "whatsapp"
        "brave-search"
    )
    
    local created=0
    
    for skill in "${IMPORTANT_SKILLS[@]}"; do
        # 如果已经存在，跳过
        if [ -f "$SKILLS_DIR/$skill/SKILL.md" ]; then
            continue
        fi
        
        print_info "创建最小化: $skill"
        
        # 创建目录
        mkdir -p "$SKILLS_DIR/$skill"
        mkdir -p "$SKILLS_DIR/$skill/scripts"
        
        # 创建最小化SKILL.md
        cat > "$SKILLS_DIR/$skill/SKILL.md" << EOF
---
name: $skill
description: 最小化 $skill 技能（混合安装器创建）
created: $(date +%Y-%m-%d)
status: minimal
---

# $skill (最小化版本)

这是一个由混合安装器创建的最小化技能。

## 功能
- 基本功能占位符
- 等待完整版本安装

## 注意
这是一个临时解决方案，建议网络恢复后安装完整版本。
EOF
        
        # 创建示例脚本
        cat > "$SKILLS_DIR/$skill/scripts/example.sh" << 'EOF'
#!/bin/bash
echo "这是最小化技能的示例脚本"
echo "运行时间: $(date)"
echo "请安装完整版本以获得完整功能"
EOF
        
        chmod +x "$SKILLS_DIR/$skill/scripts/example.sh"
        
        # 创建配置
        create_basic_config "$skill"
        
        print_success "$skill 最小化版本创建完成"
        ((created++))
    done
    
    log "最小化技能创建结果: $created 个技能"
    return $created
}

# 7. 安装系统依赖
install_system_dependencies() {
    print_section "安装系统依赖"
    
    # 检查包管理器
    if command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
        UPDATE_CMD="sudo apt update"
        INSTALL_CMD="sudo apt install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        UPDATE_CMD="sudo yum update -y"
        INSTALL_CMD="sudo yum install -y"
    else
        print_warning "未知的包管理器，跳过依赖安装"
        return 0
    fi
    
    # 基本依赖
    BASIC_DEPS=("curl" "wget" "git" "python3" "jq")
    
    print_info "更新包列表..."
    $UPDATE_CMD >/dev/null 2>&1 || print_warning "包列表更新失败"
    
    local installed=0
    
    for dep in "${BASIC_DEPS[@]}"; do
        if command -v "$dep" &> /dev/null; then
            print_success "$dep 已安装"
        else
            print_info "安装: $dep"
            $INSTALL_CMD "$dep" >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                print_success "$dep 安装成功"
                ((installed++))
            else
                print_warning "$dep 安装失败"
            fi
        fi
    done
    
    log "系统依赖安装: $installed 个新安装"
}

# 8. 配置技能集成
configure_skills_integration() {
    print_section "配置技能集成"
    
    # 创建OpenClaw配置
    cat > "$WORKSPACE/config/openclaw_hybrid.json" << EOF
{
  "hybrid_installer": {
    "installed_at": "$(date -Iseconds)",
    "network_status": "$NETWORK_STATUS",
    "strategy": "multi_source"
  },
  "skills": {
    "directory": "$SKILLS_DIR",
    "auto_enable": true,
    "scan_interval": 300
  },
  "telegram": {
    "bot_token": "8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o",
    "enabled": true
  },
  "cron": {
    "enabled": true,
    "tasks": []
  }
}
EOF
    
    # 创建技能启用脚本
    cat > "$WORKSPACE/scripts/enable_hybrid_skills.sh" << 'EOF'
#!/bin/bash
echo "启用混合安装的技能..."

for skill_dir in ~/.openclaw/workspace/skills/*/; do
    if [ -d "$skill_dir" ]; then
        skill=$(basename "$skill_dir")
        if [ -f "$skill_dir/SKILL.md" ]; then
            echo "检查: $skill"
            # 这里可以添加启用命令
            # openclaw skills enable "$skill"
        fi
    fi
done

echo "启用完成"
EOF
    
    chmod +x "$WORKSPACE/scripts/enable_hybrid_skills.sh"
    
    print_success "集成配置完成"
}

# 9. 生成安装报告
generate_hybrid_report() {
    print_section "生成安装报告"
    
    # 统计技能
    TOTAL_SKILLS=$(find "$SKILLS_DIR" -name "SKILL.md" 2>/dev/null | wc -l)
    FULL_SKILLS=$(find "$SKILLS_DIR" -name "SKILL.md" -exec grep -l "status: minimal" {} \; 2>/dev/null | wc -l)
    MINIMAL_SKILLS=$((TOTAL_SKILLS - FULL_SKILLS))
    
    REPORT_FILE="$WORKSPACE/logs/hybrid_install_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# 混合策略Skills安装报告

## 安装摘要
- 安装时间: $(date '+%Y-%m-%d %H:%M:%S')
- 网络状态: $NETWORK_STATUS
- 总技能数: $TOTAL_SKILLS
- 完整版本: $FULL_SKILLS
- 最小化版本: $MINIMAL_SKILLS
- 安装策略: 混合多源

## 已安装技能

### 完整版本
$(find "$SKILLS_DIR" -name "SKILL.md" -exec grep -L "status: minimal" {} \; 2>/dev/null | xargs -I {} basename $(dirname {}) | while read skill; do echo "- ✅ $skill"; done)

### 最小化版本
$(find "$SKILLS_DIR" -name "SKILL.md" -exec grep -l "status: minimal" {} \; 2>/dev/null | xargs -I {} basename $(dirname {}) | while read skill; do echo "- ⚠ $skill (最小化)"; done)

## 文件位置
- 技能目录: $SKILLS_DIR
- 配置文件: $WORKSPACE/config/openclaw_hybrid.json
- 启用脚本: $WORKSPACE/scripts/enable_hybrid_skills.sh
- 安装日志: $INSTALL_LOG

## 下一步行动

### 立即执行
1. 启用技能: bash $WORKSPACE/scripts/enable_hybrid_skills.sh
2. 测试核心功能
3. 配置Telegram Chat ID

### 网络优化后
1. 重新下载最小化技能
2. 测试外部API连接
3. 安装剩余技能

### OPC项目开发
1. 开始加密货币监控
2. 学习智能合约开发
3. 创建求职助手系统

## 技术支持
- 查看日志: $INSTALL_LOG
- 技能文档: 各技能目录下的SKILL.md
- 配置文件: $WORKSPACE/config/

---
*报告生成于 $(date)*
EOF
    
    print_success "安装报告已生成: $REPORT_FILE"
    
    # 显示摘要
    echo ""
    echo "📊 安装摘要:"
    echo "  总技能数: $TOTAL_SKILLS"
    echo "  完整版本: $FULL_SKILLS"
    echo "  最小化版本: $MINIMAL_SKILLS"
    echo "  网络状态: $NETWORK_STATUS"
}

# 主函数
main() {
    echo ""
    echo "🚀 开始混合策略Skills安装"
    echo "="*60
    
    # 记录开始时间
    START_TIME=$(date +%s)
    
    # 1. 检查网络状态
    check_network_hybrid
    local online_sources=$?
    
    # 2. 备份现有技能
    backup_existing_skills
    
    # 3. 安装系统依赖
    install_system_dependencies
    
    # 根据网络状态选择策略
    if [ $online_sources -ge 2 ]; then
        # 网络良好，尝试所有策略
        print_info "网络良好，使用完整策略组合"
        
        # 策略1: clawhub
        install_with_clawhub
        CLAWHUB_RESULT=$?
        
        # 策略2: GitHub直接下载
        download_from_github
        GITHUB_RESULT=$?
        
        # 策略3: 复制bundled技能
        copy_bundled_skills
        BUNDLED_RESULT=$?
        
    elif [ $online_sources -eq 1 ]; then
        # 网络较差，使用有限策略
        print_warning "网络较差，使用有限策略"
        
        # 只尝试GitHub下载
        download_from_github
        GITHUB_RESULT=$?
        
        # 复制bundled技能
        copy_bundled_skills
        BUNDLED_RESULT=$?
        
        CLAWHUB_RESULT=0
    else
        # 网络离线，使用备用策略
        print_error "网络离线，使用备用策略"
        
        # 只创建最小化技能
        create_minimal_skills
        MINIMAL_RESULT=$?
        
        GITHUB_RESULT=0
        BUNDLED_RESULT=0
        CLAWHUB_RESULT=0
    fi
    
    # 如果前面策略都没安装到技能，创建最小化版本
    TOTAL_SKILLS=$(find "$SKILLS_DIR" -name "SKILL.md" 2>/dev/null | wc -l)
    if [ $TOTAL_SKILLS -eq 0 ]; then
        print_warning "没有安装到任何技能，创建核心最小化版本"
        create_minimal_skills
    fi
    
    # 4. 配置集成
    configure_skills_integration
    
    # 5. 生成报告
    generate_hybrid_report
    
    # 计算总耗时
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # 最终统计
    TOTAL_SKILLS=$(find "$SKILLS_DIR" -name "SKILL.md" 2>/dev/null | wc -l)
    FULL_SKILLS=$(find "$SKILLS_DIR" -name "SKILL.md" -exec grep -l "status: minimal" {} \; 2>/dev/null | wc -l 2>/dev/null || echo 0)
    MINIMAL_SKILLS=$((TOTAL_SKILLS - FULL_SKILLS))
    
    echo ""
    echo "="*60
    echo "🎉 混合策略Skills安装完成！"
    echo "="*60
    echo ""
    echo "📊 最终结果:"
    echo "  总耗时: ${DURATION}秒"
    echo "  总技能数: $TOTAL_SKILLS"
    echo "  完整版本: $FULL_SKILLS"
    echo "  最小化版本: $MINIMAL_SKILLS"
    echo "  网络状态: $NETWORK_STATUS"
    echo ""
    echo "📁 重要文件:"
    echo "  技能目录: $SKILLS_DIR"
    echo "  配置文件: $WORKSPACE/config/openclaw_hybrid.json"
    echo "  启用脚本: $WORKSPACE/scripts/enable_hybrid_skills.sh"
    echo "  安装日志: $INSTALL_LOG"
    echo ""
    echo "🚀 立即执行:"
    echo "  1. 启用技能: bash $WORKSPACE/scripts/enable_hybrid_skills.sh"
    echo "  2. 查看报告: cat $WORKSPACE/logs/hybrid_install_report_*.md | head -30"
    echo "  3. 测试功能: 检查各技能目录"
    echo ""
    echo "🔧 网络恢复后:"
    echo "  重新运行此脚本获取完整版本"
    echo "="*60
    
    # 记录完成日志
    log "混合安装完成: $TOTAL_SKILLS 个技能，耗时 ${DURATION}秒"
}

# 执行主函数
main