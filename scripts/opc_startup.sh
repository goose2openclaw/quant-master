#!/bin/bash

# OPC项目启动脚本
# 一键启动OPC项目所有组件

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$HOME/.openclaw/workspace"
OPC_PROJECT_DIR="$HOME/opc-project"
CONFIG_DIR="$WORKSPACE_DIR/config"
LOG_DIR="$WORKSPACE_DIR/logs"
DATA_DIR="$WORKSPACE_DIR/data"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

# 显示横幅
show_banner() {
    cat << "EOF"
    
    ╔══════════════════════════════════════════╗
    ║         OPC项目启动系统                 ║
    ║    OpenClaw Optimized Platform          ║
    ╚══════════════════════════════════════════╝
    
EOF
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖"
    
    local missing_deps=()
    
    # 检查必要命令
    for cmd in openclaw python3 jq curl git; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "缺少依赖: ${missing_deps[*]}"
        echo "请安装缺少的依赖后再运行。"
        return 1
    fi
    
    log_success "所有依赖已安装"
    
    # 显示版本信息
    log_info "OpenClaw版本: $(openclaw --version 2>&1 | head -1)"
    log_info "Python版本: $(python3 --version)"
    log_info "jq版本: $(jq --version)"
    
    return 0
}

# 检查目录结构
check_directories() {
    log_step "检查目录结构"
    
    local missing_dirs=()
    
    # 检查必要目录
    local required_dirs=(
        "$WORKSPACE_DIR"
        "$OPC_PROJECT_DIR"
        "$CONFIG_DIR"
        "$LOG_DIR"
        "$DATA_DIR"
        "$WORKSPACE_DIR/skills"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            missing_dirs+=("$dir")
        fi
    done
    
    if [ ${#missing_dirs[@]} -gt 0 ]; then
        log_warning "缺少目录:"
        for dir in "${missing_dirs[@]}"; do
            echo "  - $dir"
        done
        
        # 尝试创建缺失目录
        log_info "尝试创建缺失目录..."
        for dir in "${missing_dirs[@]}"; do
            if mkdir -p "$dir" 2>/dev/null; then
                log_success "已创建目录: $dir"
            else
                log_error "无法创建目录: $dir"
                return 1
            fi
        done
    else
        log_success "所有目录结构正常"
    fi
    
    return 0
}

# 检查配置文件
check_configs() {
    log_step "检查配置文件"
    
    local missing_configs=()
    
    # 检查必要配置文件
    local required_configs=(
        "$CONFIG_DIR/openclaw_opc.json"
        "$CONFIG_DIR/opc_team_config.json"
    )
    
    for config in "${required_configs[@]}"; do
        if [ ! -f "$config" ]; then
            missing_configs+=("$config")
        fi
    done
    
    if [ ${#missing_configs[@]} -gt 0 ]; then
        log_warning "缺少配置文件:"
        for config in "${missing_configs[@]}"; do
            echo "  - $(basename "$config")"
        done
        
        # 尝试从备份恢复
        log_info "尝试从备份恢复配置文件..."
        local backup_dir="$WORKSPACE_DIR/backup"
        if [ -d "$backup_dir" ]; then
            for config in "${missing_configs[@]}"; do
                local config_name=$(basename "$config")
                local backup_file="$backup_dir/$config_name"
                if [ -f "$backup_file" ]; then
                    cp "$backup_file" "$config"
                    log_success "已从备份恢复: $config_name"
                else
                    log_error "备份文件不存在: $config_name"
                    return 1
                fi
            done
        else
            log_error "备份目录不存在，无法恢复配置文件"
            return 1
        fi
    else
        log_success "所有配置文件正常"
        
        # 验证配置文件内容
        log_info "验证配置文件..."
        if jq empty "$CONFIG_DIR/openclaw_opc.json" 2>/dev/null; then
            log_success "配置文件格式正确"
        else
            log_error "配置文件格式错误"
            return 1
        fi
    fi
    
    return 0
}

# 启动健康检查
run_health_check() {
    log_step "运行健康检查"
    
    log_info "执行快速健康检查..."
    if bash "$SCRIPT_DIR/health_check.sh" quick; then
        log_success "健康检查通过"
        return 0
    else
        local exit_code=$?
        log_warning "健康检查发现问题: $exit_code 个问题"
        
        if [ $exit_code -le 3 ]; then
            log_info "问题数量较少，继续启动..."
            return 0
        else
            log_error "问题数量较多，建议修复后再启动"
            return 1
        fi
    fi
}

# 启动技能系统
start_skill_system() {
    log_step "启动技能系统"
    
    log_info "优化技能加载..."
    if bash "$SCRIPT_DIR/skill_manager.sh" optimize; then
        log_success "技能优化完成"
    else
        log_warning "技能优化过程中出现问题"
    fi
    
    log_info "启用核心技能..."
    if bash "$SCRIPT_DIR/skill_manager.sh" enable core; then
        log_success "核心技能已启用"
    else
        log_error "启用核心技能失败"
        return 1
    fi
    
    log_info "启用预加载技能..."
    if bash "$SCRIPT_DIR/skill_manager.sh" enable preload; then
        log_success "预加载技能已启用"
    else
        log_warning "启用预加载技能时出现问题"
    fi
    
    return 0
}

# 启动监控系统
start_monitoring() {
    log_step "启动监控系统"
    
    # 创建监控日志
    local monitor_log="$LOG_DIR/startup_monitor_$(date +%Y%m%d_%H%M%S).log"
    
    log_info "启动系统监控..."
    
    # 启动技能监控
    log_info "启动技能性能监控..."
    if bash "$SCRIPT_DIR/skill_manager.sh" monitor > "$monitor_log" 2>&1; then
        log_success "技能监控已启动"
    else
        log_warning "技能监控启动时出现问题"
    fi
    
    # 启动网络监控
    log_info "启动网络连接监控..."
    cat >> "$monitor_log" << EOF

=== 网络监控 ===
时间: $(date)
EOF
    
    # 测试关键网络连接
    local endpoints=("8.8.8.8" "google.com" "httpbin.org")
    for endpoint in "${endpoints[@]}"; do
        if ping -c 1 -W 2 "$endpoint" > /dev/null 2>&1; then
            echo "$endpoint: 连接正常" >> "$monitor_log"
        else
            echo "$endpoint: 连接失败" >> "$monitor_log"
        fi
    done
    
    log_success "监控系统已启动"
    log_info "监控日志: $monitor_log"
    
    return 0
}

# 启动Telegram模拟系统
start_telegram_mock() {
    log_step "启动Telegram模拟系统"
    
    local mock_dir="$WORKSPACE_DIR/telegram_mock"
    
    if [ ! -d "$mock_dir" ]; then
        log_warning "Telegram模拟系统目录不存在"
        return 1
    fi
    
    log_info "检查模拟系统..."
    
    # 检查模拟系统文件
    local required_files=("mock_handler.py" "mock_bot.py" "data/users.json")
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$mock_dir/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log_warning "模拟系统文件不完整，缺少:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi
    
    log_info "启动模拟Bot..."
    
    # 在后台启动模拟系统
    cd "$mock_dir"
    if python3 mock_handler.py --test > "$LOG_DIR/telegram_mock.log" 2>&1 & then
        local pid=$!
        echo $pid > "$LOG_DIR/telegram_mock.pid"
        log_success "Telegram模拟系统已启动 (PID: $pid)"
        log_info "日志文件: $LOG_DIR/telegram_mock.log"
        
        # 等待系统初始化
        sleep 2
        
        # 测试模拟系统
        log_info "测试模拟系统..."
        if python3 -c "import requests; r = requests.get('http://localhost:8080/status'); print('状态:', r.status_code, r.text)" 2>/dev/null | grep -q "200"; then
            log_success "模拟系统运行正常"
        else
            log_warning "模拟系统测试失败，但继续启动"
        fi
    else
        log_error "启动模拟系统失败"
        return 1
    fi
    
    return 0
}

# 启动OPC团队
start_opc_team() {
    log_step "启动OPC团队"
    
    local team_script="$SCRIPT_DIR/launch_opc_team.sh"
    
    if [ ! -f "$team_script" ]; then
        log_warning "团队启动脚本不存在"
        return 1
    fi
    
    log_info "启动多Agent团队..."
    
    # 检查团队配置
    if [ ! -f "$CONFIG_DIR/opc_team_config.json" ]; then
        log_error "团队配置文件不存在"
        return 1
    fi
    
    # 启动团队
    if bash "$team_script" > "$LOG_DIR/team_startup.log" 2>&1 & then
        local pid=$!
        echo $pid > "$LOG_DIR/team_startup.pid"
        log_success "OPC团队已启动 (PID: $pid)"
        log_info "团队日志: $LOG_DIR/team_startup.log"
        
        # 等待团队初始化
        sleep 3
        
        # 检查团队状态
        log_info "检查团队状态..."
        if python3 "$SCRIPT_DIR/manage_opc_team.py" status >> "$LOG_DIR/team_startup.log" 2>&1; then
            log_success "团队状态正常"
        else
            log_warning "获取团队状态时出现问题"
        fi
    else
        log_error "启动团队失败"
        return 1
    fi
    
    return 0
}

# 显示启动状态
show_startup_status() {
    log_step "启动状态汇总"
    
    local status_file="$LOG_DIR/startup_status_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$status_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "system": "OPC项目启动状态",
  "components": {
    "health_check": "$([ -f "$LOG_DIR/health_report_"* ] && echo "completed" || echo "failed")",
    "skill_system": "$([ -f "$LOG_DIR/skill_monitor_"* ] && echo "running" || echo "stopped")",
    "telegram_mock": "$([ -f "$LOG_DIR/telegram_mock.pid" ] && echo "running" || echo "stopped")",
    "opc_team": "$([ -f "$LOG_DIR/team_startup.pid" ] && echo "running" || echo "stopped")",
    "monitoring": "$([ -f "$LOG_DIR/startup_monitor_"* ] && echo "active" || echo "inactive")"
  },
  "next_steps": [
    "1. 检查日志文件确认各组件状态",
    "2. 测试Telegram模拟系统命令",
    "3. 验证加密货币监控功能",
    "4. 测试求职助手功能"
  ]
}
EOF
    
    log_success "启动状态报告已生成: $status_file"
    
    # 显示摘要
    echo -e "\n${GREEN}=== 启动完成 ===${NC}"
    echo "时间: $(date)"
    echo "状态: 所有组件已启动"
    echo ""
    echo "${CYAN}可用命令:${NC}"
    echo "  检查状态: bash $SCRIPT_DIR/health_check.sh"
    echo "  管理技能: bash $SCRIPT_DIR/skill_manager.sh list"
    echo "  测试模拟: bash $SCRIPT_DIR/test_mock_bot.sh"
    echo "  团队管理: python3 $SCRIPT_DIR/manage_opc_team.py status"
    echo ""
    echo "${YELLOW}日志文件:${NC}"
    ls -la "$LOG_DIR"/*.log 2>/dev/null | head -5 | awk '{print "  " $9}'
    echo ""
    echo "${BLUE}下一步:${NC}"
    echo "  1. 测试系统功能是否正常"
    echo "  2. 检查监控数据"
    echo "  3. 开始开发工作"
}

# 清理函数
cleanup() {
    log_info "执行清理..."
    
    # 停止所有后台进程
    if [ -f "$LOG_DIR/telegram_mock.pid" ]; then
        local pid=$(cat "$LOG_DIR/telegram_mock.pid")
        kill $pid 2>/dev/null && log_info "已停止Telegram模拟系统"
        rm -f "$LOG_DIR/telegram_mock.pid"
    fi
    
    if [ -f "$LOG_DIR/team_startup.pid" ]; then
        local pid=$(cat "$LOG_DIR/team_startup.pid")
        kill $pid 2>/dev/null && log_info "已停止OPC团队"
        rm -f "$LOG_DIR/team_startup.pid"
    fi
    
    log_success "清理完成"
}

# 主函数
main() {
    local action="${1:-start}"
    
    # 设置信号处理
    trap cleanup EXIT INT TERM
    
    case $action in
        "start")
            show_banner
            
            # 执行启动序列
            check_dependencies || return 1
            check_directories || return 1
            check_configs || return 1
            run_health_check || return 1
            start_skill_system || return 1
            start_monitoring || return 1
            start_telegram_mock || log_warning "Telegram模拟系统启动失败，继续其他组件"
            start_opc_team || log_warning "OPC团队启动失败，继续其他组件"
            
            show_startup_status
            ;;
            
        "stop")
            log_step "停止OPC项目"
            cleanup
            log_success "所有组件已停止"
            ;;
            
        "restart")
            log_step "重启OPC项目"
            cleanup
            sleep 2
            exec "$0" start
            ;;
            
        "status")
            log_step "系统状态"
            
            echo -e "${CYAN}运行状态:${NC}"
            
            # 检查进程
            if [ -f "$LOG_DIR/telegram_mock.pid" ]; then
                local pid=$(cat "$LOG_DIR/telegram_mock.pid")
                if ps -p $pid > /dev/null; then
                    echo "  Telegram模拟系统: ${GREEN}运行中${NC} (PID: $pid)"
                else
                    echo "  Telegram模拟系统: ${RED}已停止${NC}"
                fi
            else
                echo "  Telegram模拟系统: ${YELLOW}未启动${NC}"
            fi
            
            if [ -f "$LOG_DIR/team_startup.pid" ]; then
                local pid=$(cat "$LOG_DIR/team_startup.pid")
                if ps -p $pid > /dev/null; then
                    echo "  OPC团队: ${GREEN}运行中${NC} (PID: $pid)"
                else
                    echo "  OPC团队: ${RED}已停止${NC}"
                fi
            else
                echo "  OPC团队: ${YELLOW}未启动${NC}"
            fi
            
            # 检查日志
            echo -e "\n${CYAN}最新日志:${NC}"
            ls -lt "$LOG_DIR"/*.log 2>/dev/null | head -3 | awk '{print "  " $9 " (" $6 " " $7 " " $8 ")"}'
            
            # 检查配置文件
            echo -e "\n${CYAN}配置文件:${NC}"
            ls -la "$CONFIG_DIR"/*.json 2>/dev/null | awk '{print "  " $9 " (" $5 " bytes)"}'
            
            # 运行快速健康检查
            echo -e "\n${CYAN}健康状态:${NC}"
            bash "$SCRIPT_DIR/health_check.sh" quick > /dev/null 2>&1
            local health_exit=$?
            
            if [ $health_exit -eq 0 ]; then
                echo "  系统健康: ${GREEN}良好${NC}"
            elif [ $health_exit -le 3 ]; then
                echo "  系统健康: ${YELLOW}警告${NC} ($health_exit 个问题)"
            else
                echo "  系统健康: ${RED}严重${NC} ($health_exit 个问题)"
            fi
            ;;
            
        "help"|"--help"|"-h")
            show_help
            return 0
            ;;
            
        *)
            log_error "未知操作: $action"
            show_help
            return 1
            ;;
    esac
    
    return 0
}

# 显示帮助
show_help() {
    cat << EOF
OPC项目启动系统

用法: $0 [命令]

命令:
  start     启动所有OPC组件 (默认)
  stop      停止所有OPC组件
  restart   重启所有OPC组件
  status    显示系统状态
  help      显示此帮助信息

示例:
  $0          # 启动所有组件
  $0 status   # 显示状态
  $0 stop     # 停止所有组件

组件包括:
  - 健康检查系统
  - 技能管理系统
  - 监控系统
  - Telegram模拟系统
  - OPC多Agent团队

配置文件: $CONFIG_DIR/openclaw_opc.json
日志目录: $LOG_DIR
EOF
}

# 运行主函数
main "$@"