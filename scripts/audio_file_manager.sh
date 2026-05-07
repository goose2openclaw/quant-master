#!/bin/bash

# 音频文件管理脚本
# 功能：管理、组织和处理音频文件

AUDIO_DIR="/home/goose/.openclaw/media/inbound"
WORKSPACE_DIR="/home/goose/.openclaw/workspace"
LOG_FILE="$WORKSPACE_DIR/logs/audio_management.log"
CONFIG_FILE="$WORKSPACE_DIR/config/audio_config.json"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 创建必要目录
mkdir -p "$WORKSPACE_DIR/logs"
mkdir -p "$WORKSPACE_DIR/config"
mkdir -p "$WORKSPACE_DIR/audio_archive"
mkdir -p "$WORKSPACE_DIR/audio_processed"

# 日志函数
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO") color=$GREEN ;;
        "WARN") color=$YELLOW ;;
        "ERROR") color=$RED ;;
        "DEBUG") color=$BLUE ;;
        *) color=$NC ;;
    esac
    
    echo -e "${color}[$timestamp] [$level] $message${NC}"
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# 检查音频目录
check_audio_dir() {
    log_message "INFO" "检查音频目录: $AUDIO_DIR"
    
    if [ ! -d "$AUDIO_DIR" ]; then
        log_message "ERROR" "音频目录不存在"
        return 1
    fi
    
    local file_count=$(find "$AUDIO_DIR" -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" | wc -l)
    log_message "INFO" "找到 $file_count 个音频文件"
    
    return 0
}

# 列出音频文件
list_audio_files() {
    log_message "INFO" "列出音频文件"
    
    echo -e "\n${BLUE}📁 音频文件列表:${NC}"
    echo "="*60
    
    find "$AUDIO_DIR" -type f \( -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" \) | while read file; do
        local filename=$(basename "$file")
        local size=$(du -h "$file" | cut -f1)
        local type=$(file -b "$file" | cut -d',' -f1)
        local modified=$(date -r "$file" '+%Y-%m-%d %H:%M:%S')
        
        echo -e "${GREEN}📄 $filename${NC}"
        echo "  大小: $size | 类型: $type"
        echo "  修改时间: $modified"
        echo "  路径: $file"
        echo ""
    done
    
    echo "="*60
}

# 获取音频文件信息
get_audio_info() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        log_message "ERROR" "文件不存在: $file"
        return 1
    fi
    
    echo -e "\n${BLUE}🔍 音频文件信息:${NC}"
    echo "="*50
    
    # 基本信息
    local filename=$(basename "$file")
    local size=$(du -h "$file" | cut -f1)
    local file_info=$(file -b "$file")
    local modified=$(date -r "$file" '+%Y-%m-%d %H:%M:%S')
    
    echo "文件名: $filename"
    echo "大小: $size"
    echo "类型: $file_info"
    echo "修改时间: $modified"
    echo "完整路径: $file"
    
    # 尝试获取更多信息（如果ffmpeg可用）
    if command -v ffmpeg &> /dev/null; then
        echo -e "\n${YELLOW}详细音频信息:${NC}"
        ffmpeg -i "$file" 2>&1 | grep -E "Duration|Stream|Audio" | head -10
    fi
    
    echo "="*50
    
    # 保存到日志
    log_message "INFO" "获取文件信息: $filename"
    
    return 0
}

# 归档音频文件
archive_audio_file() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        log_message "ERROR" "文件不存在: $file"
        return 1
    fi
    
    local filename=$(basename "$file")
    local archive_dir="$WORKSPACE_DIR/audio_archive/$(date +%Y/%m/%d)"
    local archive_path="$archive_dir/$filename"
    
    mkdir -p "$archive_dir"
    
    if cp "$file" "$archive_path"; then
        log_message "INFO" "文件已归档: $filename -> $archive_path"
        echo -e "${GREEN}✅ 文件已归档到: $archive_path${NC}"
        return 0
    else
        log_message "ERROR" "归档失败: $filename"
        return 1
    fi
}

# 批量处理音频文件
batch_process_audio() {
    local pattern="$1"
    
    log_message "INFO" "开始批量处理音频文件: $pattern"
    
    find "$AUDIO_DIR" -type f -name "$pattern" | while read file; do
        local filename=$(basename "$file")
        
        echo -e "\n${BLUE}处理文件: $filename${NC}"
        
        # 获取信息
        get_audio_info "$file"
        
        # 归档
        if archive_audio_file "$file"; then
            # 移动到已处理目录
            local processed_dir="$WORKSPACE_DIR/audio_processed"
            local processed_path="$processed_dir/$filename"
            
            mkdir -p "$processed_dir"
            if mv "$file" "$processed_path"; then
                log_message "INFO" "文件已移动到已处理目录: $filename"
                echo -e "${GREEN}✅ 文件已处理并移动${NC}"
            fi
        fi
    done
    
    log_message "INFO" "批量处理完成"
}

# 清理旧文件
cleanup_old_files() {
    local days=${1:-30}
    
    log_message "INFO" "清理 $days 天前的音频文件"
    
    find "$AUDIO_DIR" -type f \( -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" \) -mtime +$days | while read file; do
        local filename=$(basename "$file")
        
        if archive_audio_file "$file"; then
            rm "$file"
            log_message "INFO" "已清理旧文件: $filename"
            echo -e "${YELLOW}🗑️  已清理: $filename${NC}"
        fi
    done
    
    log_message "INFO" "清理完成"
}

# 生成报告
generate_report() {
    local report_file="$WORKSPACE_DIR/reports/audio_report_$(date +%Y%m%d_%H%M%S).md"
    
    mkdir -p "$(dirname "$report_file")"
    
    log_message "INFO" "生成音频管理报告"
    
    cat > "$report_file" << EOF
# 音频文件管理报告

## 生成时间
$(date)

## 系统信息
- 用户: $(whoami)
- 主机: $(hostname)
- 音频目录: $AUDIO_DIR

## 文件统计
$(echo "### 文件类型分布")
find "$AUDIO_DIR" -type f | grep -E "\.(ogg|mp3|wav|m4a)$" | sed 's/.*\.//' | sort | uniq -c | while read count ext; do
    echo "- $ext: $count 个文件"
done

## 存储使用
$(echo "### 目录大小")
du -sh "$AUDIO_DIR" 2>/dev/null | while read size dir; do
    echo "- $dir: $size"
done

## 最近活动
$(echo "### 最近修改的文件")
find "$AUDIO_DIR" -type f \( -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" \) -mtime -7 -exec ls -lh {} \; 2>/dev/null | head -10 | while read line; do
    echo "- $line"
done

## 管理操作
$(tail -20 "$LOG_FILE" 2>/dev/null || echo "暂无日志")

## 建议
1. 定期清理旧文件
2. 归档重要音频
3. 保持目录结构清晰
4. 监控存储使用情况

EOF
    
    echo -e "${GREEN}📊 报告已生成: $report_file${NC}"
    log_message "INFO" "报告已保存: $report_file"
}

# 显示帮助
show_help() {
    echo -e "${BLUE}🎵 音频文件管理脚本${NC}"
    echo "="*60
    echo ""
    echo "用法: $0 [命令] [参数]"
    echo ""
    echo "命令:"
    echo "  list              列出所有音频文件"
    echo "  info <文件>       获取音频文件详细信息"
    echo "  archive <文件>    归档音频文件"
    echo "  batch <模式>      批量处理文件（例如: '*.ogg'）"
    echo "  cleanup [天数]    清理旧文件（默认30天）"
    echo "  report            生成管理报告"
    echo "  monitor           监控音频目录变化"
    echo "  help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 list"
    echo "  $0 info file.ogg"
    echo "  $0 batch '*.ogg'"
    echo "  $0 cleanup 7"
    echo "  $0 report"
    echo ""
    echo "配置:"
    echo "  日志文件: $LOG_FILE"
    echo "  配置文件: $CONFIG_FILE"
    echo "  工作空间: $WORKSPACE_DIR"
    echo "="*60
}

# 监控目录变化
monitor_directory() {
    log_message "INFO" "开始监控音频目录"
    
    echo -e "${BLUE}👁️  监控音频目录: $AUDIO_DIR${NC}"
    echo "按 Ctrl+C 停止监控"
    echo ""
    
    # 初始文件列表
    declare -A files
    for file in "$AUDIO_DIR"/*; do
        if [ -f "$file" ]; then
            files["$file"]=$(stat -c %Y "$file" 2>/dev/null || echo "0")
        fi
    done
    
    while true; do
        sleep 5
        
        # 检查新文件
        for file in "$AUDIO_DIR"/*; do
            if [ -f "$file" ] && [ -z "${files[$file]}" ]; then
                local filename=$(basename "$file")
                log_message "INFO" "检测到新文件: $filename"
                echo -e "${GREEN}🆕 新文件: $filename${NC}"
                files["$file"]=$(stat -c %Y "$file" 2>/dev/null || echo "0")
            fi
        done
        
        # 检查文件修改
        for file in "${!files[@]}"; do
            if [ -f "$file" ]; then
                local old_time="${files[$file]}"
                local new_time=$(stat -c %Y "$file" 2>/dev/null || echo "0")
                
                if [ "$old_time" != "$new_time" ]; then
                    local filename=$(basename "$file")
                    log_message "INFO" "文件被修改: $filename"
                    echo -e "${YELLOW}✏️  文件修改: $filename${NC}"
                    files["$file"]=$new_time
                fi
            else
                # 文件被删除
                local filename=$(basename "$file")
                log_message "INFO" "文件被删除: $filename"
                echo -e "${RED}🗑️  文件删除: $filename${NC}"
                unset files["$file"]
            fi
        done
    done
}

# 主函数
main() {
    log_message "INFO" "音频文件管理脚本启动"
    
    # 检查音频目录
    if ! check_audio_dir; then
        exit 1
    fi
    
    # 解析参数
    case "$1" in
        "list")
            list_audio_files
            ;;
        "info")
            if [ -z "$2" ]; then
                echo -e "${RED}错误: 需要指定文件名${NC}"
                show_help
                exit 1
            fi
            get_audio_info "$AUDIO_DIR/$2"
            ;;
        "archive")
            if [ -z "$2" ]; then
                echo -e "${RED}错误: 需要指定文件名${NC}"
                show_help
                exit 1
            fi
            archive_audio_file "$AUDIO_DIR/$2"
            ;;
        "batch")
            if [ -z "$2" ]; then
                echo -e "${RED}错误: 需要指定文件模式${NC}"
                show_help
                exit 1
            fi
            batch_process_audio "$2"
            ;;
        "cleanup")
            cleanup_old_files "${2:-30}"
            ;;
        "report")
            generate_report
            ;;
        "monitor")
            monitor_directory
            ;;
        "help"|"")
            show_help
            ;;
        *)
            echo -e "${RED}未知命令: $1${NC}"
            show_help
            exit 1
            ;;
    esac
    
    log_message "INFO" "脚本执行完成"
}

# 执行主函数
main "$@"