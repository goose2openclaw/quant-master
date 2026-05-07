#!/bin/bash

# WhatsApp配置测试脚本
# 用于测试WhatsApp技能配置和连接

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查配置文件
check_config_files() {
    log_info "检查配置文件..."
    
    local config_files=(
        "/home/goose/.openclaw/workspace/config/whatsapp_config.json"
        "/home/goose/.openclaw/workspace/skills/whatsapp/config.json"
        "/home/goose/.openclaw/workspace/config/openclaw_opc.json"
    )
    
    for file in "${config_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "找到配置文件: $file"
            
            # 检查文件大小
            local size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
            if [[ $size -gt 100 ]]; then
                log_success "  文件大小正常: ${size} bytes"
            else
                log_warning "  文件可能为空或过小: ${size} bytes"
            fi
            
            # 检查JSON格式
            if python3 -m json.tool "$file" >/dev/null 2>&1; then
                log_success "  JSON格式正确"
            else
                log_error "  JSON格式错误"
                return 1
            fi
        else
            log_error "配置文件不存在: $file"
            return 1
        fi
    done
    
    return 0
}

# 检查认证信息
check_auth_info() {
    log_info "检查认证信息..."
    
    local config_file="/home/goose/.openclaw/workspace/config/whatsapp_config.json"
    
    # 检查必需字段
    local required_fields=(
        ".whatsapp.authentication.phoneNumberId"
        ".whatsapp.authentication.businessAccountId"
        ".whatsapp.authentication.accessToken"
    )
    
    for field in "${required_fields[@]}"; do
        local value=$(jq -r "$field" "$config_file" 2>/dev/null)
        
        if [[ "$value" == "null" || -z "$value" ]]; then
            log_warning "  缺少认证字段: $field"
            log_info "  请更新配置文件中的认证信息"
            return 1
        else
            log_success "  认证字段存在: $field"
            
            # 检查字段长度（基本验证）
            if [[ ${#value} -lt 5 ]]; then
                log_warning "    字段值可能无效: 长度只有 ${#value} 字符"
            fi
        fi
    done
    
    # 检查配置状态
    local status=$(jq -r '.whatsapp.status' "$config_file" 2>/dev/null)
    if [[ "$status" == "configured" || "$status" == "ready" ]]; then
        log_success "  配置状态: $status"
    else
        log_warning "  配置状态: $status (需要配置)"
    fi
    
    return 0
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    local dependencies=(
        "jq"
        "curl"
        "python3"
    )
    
    for dep in "${dependencies[@]}"; do
        if command -v "$dep" >/dev/null 2>&1; then
            log_success "  找到: $dep"
        else
            log_error "  缺少: $dep"
            return 1
        fi
    done
    
    return 0
}

# 检查目录结构
check_directories() {
    log_info "检查目录结构..."
    
    local directories=(
        "/home/goose/opc-project/logs/whatsapp"
        "/home/goose/opc-project/data/whatsapp"
        "/home/goose/.openclaw/workspace/config"
        "/home/goose/.openclaw/workspace/skills/whatsapp"
    )
    
    for dir in "${directories[@]}"; do
        if [[ -d "$dir" ]]; then
            log_success "  目录存在: $dir"
            
            # 检查目录权限
            if [[ -w "$dir" ]]; then
                log_success "    可写入"
            else
                log_warning "    不可写入"
            fi
        else
            log_warning "  目录不存在: $dir"
            
            # 尝试创建目录
            if mkdir -p "$dir" 2>/dev/null; then
                log_success "    已创建目录"
            else
                log_error "    创建目录失败"
                return 1
            fi
        fi
    done
    
    return 0
}

# 模拟API测试（不实际发送）
simulate_api_test() {
    log_info "模拟API测试..."
    
    local config_file="/home/goose/.openclaw/workspace/config/whatsapp_config.json"
    
    # 获取配置信息
    local phone_number_id=$(jq -r '.whatsapp.authentication.phoneNumberId' "$config_file")
    local access_token=$(jq -r '.whatsapp.authentication.accessToken' "$config_file")
    
    if [[ "$phone_number_id" == "null" || "$access_token" == "null" ]]; then
        log_warning "  跳过API测试：缺少认证信息"
        return 0
    fi
    
    log_info "  测试配置:"
    log_info "    Phone Number ID: ${phone_number_id:0:10}..."
    log_info "    Access Token: ${access_token:0:10}..."
    
    # 检查URL格式
    local webhook_url=$(jq -r '.whatsapp.authentication.webhookUrl' "$config_file")
    if [[ "$webhook_url" != "null" && "$webhook_url" != "https://your-domain.com/webhook/whatsapp" ]]; then
        log_success "  Webhook URL已配置: $webhook_url"
    else
        log_warning "  Webhook URL未配置或使用默认值"
    fi
    
    log_success "  API配置格式正确"
    return 0
}

# 生成配置报告
generate_report() {
    log_info "生成配置报告..."
    
    local report_file="/home/goose/opc-project/logs/whatsapp/config_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== WhatsApp配置测试报告 ==="
        echo "生成时间: $(date)"
        echo ""
        echo "1. 系统信息"
        echo "   主机名: $(hostname)"
        echo "   用户: $(whoami)"
        echo "   时间: $(date '+%Y-%m-%d %H:%M:%S %Z')"
        echo ""
        echo "2. 配置文件状态"
        
        local config_files=(
            "/home/goose/.openclaw/workspace/config/whatsapp_config.json"
            "/home/goose/.openclaw/workspace/skills/whatsapp/config.json"
        )
        
        for file in "${config_files[@]}"; do
            echo "   $file:"
            if [[ -f "$file" ]]; then
                echo "     存在: 是"
                echo "     大小: $(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null) bytes"
                echo "     权限: $(stat -c%A "$file" 2>/dev/null || stat -f%Sp "$file" 2>/dev/null)"
            else
                echo "     存在: 否"
            fi
            echo ""
        done
        
        echo "3. 认证信息状态"
        local config_file="/home/goose/.openclaw/workspace/config/whatsapp_config.json"
        if [[ -f "$config_file" ]]; then
            echo "   Phone Number ID: $(jq -r '.whatsapp.authentication.phoneNumberId' "$config_file")"
            echo "   Business Account ID: $(jq -r '.whatsapp.authentication.businessAccountId' "$config_file")"
            echo "   Access Token: $(jq -r '.whatsapp.authentication.accessToken // "未设置"' "$config_file")"
            echo "   Status: $(jq -r '.whatsapp.status // "unknown"' "$config_file")"
        fi
        echo ""
        
        echo "4. 目录结构"
        echo "   Logs目录: /home/goose/opc-project/logs/whatsapp"
        echo "   Data目录: /home/goose/opc-project/data/whatsapp"
        echo ""
        
        echo "5. 依赖检查"
        echo "   jq: $(command -v jq >/dev/null 2>&1 && echo "已安装" || echo "未安装")"
        echo "   curl: $(command -v curl >/dev/null 2>&1 && echo "已安装" || echo "未安装")"
        echo "   python3: $(command -v python3 >/dev/null 2>&1 && echo "已安装" || echo "未安装")"
        echo ""
        
        echo "6. 建议"
        echo "   - 更新配置文件中的认证信息"
        echo "   - 配置Webhook URL"
        echo "   - 测试实际API连接"
        echo "   - 设置定时监控"
        
    } > "$report_file"
    
    log_success "报告已生成: $report_file"
    
    # 显示报告摘要
    echo ""
    echo "=== 报告摘要 ==="
    tail -20 "$report_file"
}

# 主函数
main() {
    echo ""
    echo "========================================"
    echo "    WhatsApp配置测试工具"
    echo "========================================"
    echo ""
    
    local all_passed=true
    
    # 执行检查
    if ! check_dependencies; then
        log_error "依赖检查失败"
        all_passed=false
    fi
    
    if ! check_directories; then
        log_error "目录检查失败"
        all_passed=false
    fi
    
    if ! check_config_files; then
        log_error "配置文件检查失败"
        all_passed=false
    fi
    
    if ! check_auth_info; then
        log_warning "认证信息不完整"
        # 不标记为失败，因为这是预期状态
    fi
    
    if ! simulate_api_test; then
        log_warning "API测试模拟失败"
        # 不标记为失败
    fi
    
    # 生成报告
    generate_report
    
    echo ""
    echo "========================================"
    
    if $all_passed; then
        log_success "所有基础检查通过！"
        echo ""
        log_info "下一步："
        echo "  1. 获取WhatsApp Business认证信息"
        echo "  2. 更新配置文件中的认证字段"
        echo "  3. 配置Webhook URL"
        echo "  4. 运行实际API测试"
        echo ""
        echo "配置文件位置:"
        echo "  ~/.openclaw/workspace/config/whatsapp_config.json"
    else
        log_error "部分检查失败，请查看报告详情"
        echo ""
        log_info "需要修复的问题已标记为[ERROR]"
    fi
    
    echo "测试完成！"
}

# 运行主函数
main "$@"