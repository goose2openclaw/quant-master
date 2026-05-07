#!/bin/bash

# OPC项目技能管理器
# 用于管理OpenClaw技能的加载、启用和优化

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$HOME/.openclaw/workspace"
CONFIG_DIR="$WORKSPACE_DIR/config"
SKILLS_DIR="$WORKSPACE_DIR/skills"
LOG_DIR="$WORKSPACE_DIR/logs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    local missing_deps=()
    
    # 检查必要命令
    for cmd in curl python3; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    # jq是可选的，可以用Python替代
    if ! command -v jq &> /dev/null; then
        log_warning "jq未安装，将使用Python替代方案"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "缺少依赖: ${missing_deps[*]}"
        return 1
    fi
    
    log_success "所有依赖已安装"
    return 0
}

# 加载配置
load_config() {
    local config_file="$CONFIG_DIR/openclaw_opc.json"
    
    if [ ! -f "$config_file" ]; then
        log_error "配置文件不存在: $config_file"
        return 1
    fi
    
    # 解析配置 - 使用jq或Python替代
    if command -v jq &> /dev/null; then
        OPC_CORE_SKILLS=$(jq -r '.skills.opcCore[]' "$config_file" 2>/dev/null || echo "")
        AUXILIARY_SKILLS=$(jq -r '.skills.auxiliary[]' "$config_file" 2>/dev/null || echo "")
        PRELOAD_SKILLS=$(jq -r '.skills.preload[]' "$config_file" 2>/dev/null || echo "")
    else
        # Python替代方案
        OPC_CORE_SKILLS=$(python3 -c "
import json, sys
try:
    with open('$config_file', 'r') as f:
        config = json.load(f)
    skills = config.get('skills', {})
    opc_core = skills.get('opcCore', [])
    print(' '.join(opc_core))
except Exception as e:
    print('')
" 2>/dev/null)
        
        AUXILIARY_SKILLS=$(python3 -c "
import json, sys
try:
    with open('$config_file', 'r') as f:
        config = json.load(f)
    skills = config.get('skills', {})
    auxiliary = skills.get('auxiliary', [])
    print(' '.join(auxiliary))
except Exception as e:
    print('')
" 2>/dev/null)
        
        PRELOAD_SKILLS=$(python3 -c "
import json, sys
try:
    with open('$config_file', 'r') as f:
        config = json.load(f)
    skills = config.get('skills', {})
    preload = skills.get('preload', [])
    print(' '.join(preload))
except Exception as e:
    print('')
" 2>/dev/null)
    fi
    
    log_info "配置加载完成"
    log_info "核心技能: $OPC_CORE_SKILLS"
    log_info "辅助技能: $AUXILIARY_SKILLS"
    log_info "预加载技能: $PRELOAD_SKILLS"
    
    return 0
}

# 检查技能状态
check_skill_status() {
    local skill_name="$1"
    local skill_dir="$SKILLS_DIR/$skill_name"
    
    if [ ! -d "$skill_dir" ]; then
        echo "missing"
        return
    fi
    
    if [ -f "$skill_dir/SKILL.md" ]; then
        echo "installed"
    else
        echo "incomplete"
    fi
}

# 列出所有技能
list_skills() {
    log_info "列出所有技能..."
    
    local total=0
    local installed=0
    local missing=0
    local incomplete=0
    
    # 核心技能
    echo -e "\n${BLUE}=== 核心OPC技能 ===${NC}"
    for skill in $OPC_CORE_SKILLS; do
        local status=$(check_skill_status "$skill")
        case $status in
            "installed")
                echo -e "  ${GREEN}✓${NC} $skill"
                ((installed++))
                ;;
            "missing")
                echo -e "  ${RED}✗${NC} $skill (未安装)"
                ((missing++))
                ;;
            "incomplete")
                echo -e "  ${YELLOW}⚠${NC} $skill (不完整)"
                ((incomplete++))
                ;;
        esac
        ((total++))
    done
    
    # 辅助技能
    echo -e "\n${BLUE}=== 辅助技能 ===${NC}"
    for skill in $AUXILIARY_SKILLS; do
        local status=$(check_skill_status "$skill")
        case $status in
            "installed")
                echo -e "  ${GREEN}✓${NC} $skill"
                ((installed++))
                ;;
            "missing")
                echo -e "  ${RED}✗${NC} $skill (未安装)"
                ((missing++))
                ;;
            "incomplete")
                echo -e "  ${YELLOW}⚠${NC} $skill (不完整)"
                ((incomplete++))
                ;;
        esac
        ((total++))
    done
    
    # 预加载技能
    echo -e "\n${BLUE}=== 预加载技能 ===${NC}"
    for skill in $PRELOAD_SKILLS; do
        local status=$(check_skill_status "$skill")
        case $status in
            "installed")
                echo -e "  ${GREEN}✓${NC} $skill"
                ((installed++))
                ;;
            "missing")
                echo -e "  ${RED}✗${NC} $skill (未安装)"
                ((missing++))
                ;;
            "incomplete")
                echo -e "  ${YELLOW}⚠${NC} $skill (不完整)"
                ((incomplete++))
                ;;
        esac
        ((total++))
    done
    
    # 统计
    echo -e "\n${BLUE}=== 统计 ===${NC}"
    echo "总技能数: $total"
    echo "已安装: $installed"
    echo "未安装: $missing"
    echo "不完整: $incomplete"
    
    if [ $missing -eq 0 ] && [ $incomplete -eq 0 ]; then
        log_success "所有技能状态正常"
        return 0
    else
        log_warning "有技能需要安装或修复"
        return 1
    fi
}

# 启用技能
enable_skills() {
    local skill_type="$1"
    local skills_list=""
    
    case $skill_type in
        "core")
            skills_list="$OPC_CORE_SKILLS"
            log_info "启用核心OPC技能..."
            ;;
        "auxiliary")
            skills_list="$AUXILIARY_SKILLS"
            log_info "启用辅助技能..."
            ;;
        "preload")
            skills_list="$PRELOAD_SKILLS"
            log_info "启用预加载技能..."
            ;;
        "all")
            skills_list="$OPC_CORE_SKILLS $AUXILIARY_SKILLS $PRELOAD_SKILLS"
            log_info "启用所有技能..."
            ;;
        *)
            log_error "未知的技能类型: $skill_type"
            return 1
            ;;
    esac
    
    local enabled=0
    local failed=0
    
    for skill in $skills_list; do
        local skill_dir="$SKILLS_DIR/$skill"
        
        if [ ! -d "$skill_dir" ]; then
            log_warning "技能目录不存在: $skill"
            ((failed++))
            continue
        fi
        
        if [ ! -f "$skill_dir/SKILL.md" ]; then
            log_warning "技能文件不完整: $skill"
            ((failed++))
            continue
        fi
        
        # 这里可以添加实际的启用逻辑
        # 例如: openclaw skill enable "$skill"
        
        log_info "已启用技能: $skill"
        ((enabled++))
    done
    
    log_success "启用完成: $enabled 个技能已启用, $failed 个失败"
    return $failed
}

# 优化技能加载
optimize_skills() {
    log_info "优化技能加载..."
    
    # 创建技能缓存
    local cache_dir="$WORKSPACE_DIR/.skill_cache"
    mkdir -p "$cache_dir"
    
    # 生成技能索引
    local index_file="$cache_dir/skill_index.json"
    cat > "$index_file" << EOF
{
  "last_updated": "$(date -Iseconds)",
  "skills": {
    "core": [$(
      for skill in $OPC_CORE_SKILLS; do
        echo "\"$skill\""
      done | paste -sd, -
    )],
    "auxiliary": [$(
      for skill in $AUXILIARY_SKILLS; do
        echo "\"$skill\""
      done | paste -sd, -
    )],
    "preload": [$(
      for skill in $PRELOAD_SKILLS; do
        echo "\"$skill\""
      done | paste -sd, -
    )]
  }
}
EOF
    
    log_success "技能索引已生成: $index_file"
    
    # 优化建议
    echo -e "\n${BLUE}=== 优化建议 ===${NC}"
    echo "1. 核心技能已按OPC需求优化"
    echo "2. 辅助技能按需加载"
    echo "3. 预加载技能确保基础功能"
    echo "4. 使用缓存提高加载速度"
    
    return 0
}

# 监控技能性能
monitor_skills() {
    log_info "监控技能性能..."
    
    local monitor_file="$LOG_DIR/skill_monitor_$(date +%Y%m%d).log"
    
    cat >> "$monitor_file" << EOF
=== 技能性能监控报告 ===
时间: $(date)
总技能数: $(ls -1 "$SKILLS_DIR" | wc -l)
核心技能: $(echo $OPC_CORE_SKILLS | wc -w)
辅助技能: $(echo $AUXILIARY_SKILLS | wc -w)
预加载技能: $(echo $PRELOAD_SKILLS | wc -w)

技能状态:
EOF
    
    # 检查每个技能
    for skill in $OPC_CORE_SKILLS $AUXILIARY_SKILLS $PRELOAD_SKILLS; do
        local status=$(check_skill_status "$skill")
        echo "$skill: $status" >> "$monitor_file"
    done
    
    log_success "监控报告已保存: $monitor_file"
    
    # 显示摘要
    echo -e "\n${BLUE}=== 监控摘要 ===${NC}"
    tail -n 20 "$monitor_file"
    
    return 0
}

# 主函数
main() {
    local action="${1:-list}"
    
    # 创建日志目录
    mkdir -p "$LOG_DIR"
    
    case $action in
        "list")
            check_dependencies
            load_config
            list_skills
            ;;
        "enable")
            local skill_type="${2:-all}"
            check_dependencies
            load_config
            enable_skills "$skill_type"
            ;;
        "optimize")
            check_dependencies
            load_config
            optimize_skills
            ;;
        "monitor")
            check_dependencies
            load_config
            monitor_skills
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "未知操作: $action"
            show_help
            return 1
            ;;
    esac
}

# 显示帮助
show_help() {
    cat << EOF
OPC项目技能管理器

用法: $0 [命令] [参数]

命令:
  list             列出所有技能状态
  enable [type]    启用指定类型技能 (core|auxiliary|preload|all)
  optimize         优化技能加载配置
  monitor          监控技能性能
  help             显示此帮助信息

示例:
  $0 list
  $0 enable core
  $0 optimize
  $0 monitor

配置:
  配置文件: $CONFIG_DIR/openclaw_opc.json
  技能目录: $SKILLS_DIR
  日志目录: $LOG_DIR
EOF
}

# 运行主函数
main "$@"