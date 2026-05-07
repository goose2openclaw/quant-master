#!/bin/bash

# 自动化音频处理器
# 监控依赖安装状态并自动处理音频文件

LOG_FILE="/home/goose/.openclaw/workspace/logs/audio_auto.log"
AUDIO_DIR="/home/goose/.openclaw/media/inbound"
PROCESSED_DIR="/home/goose/.openclaw/workspace/audio_processed"
LOCK_FILE="/tmp/audio_processor.lock"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
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

# 检查锁文件
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "WARN" "进程已在运行 (PID: $pid)"
            return 1
        else
            log "WARN" "发现陈旧的锁文件，清理中..."
            rm -f "$LOCK_FILE"
        fi
    fi
    
    # 创建锁文件
    echo $$ > "$LOCK_FILE"
    return 0
}

# 清理锁文件
cleanup() {
    if [ -f "$LOCK_FILE" ]; then
        rm -f "$LOCK_FILE"
    fi
    log "INFO" "清理完成"
}

# 检查依赖
check_dependencies() {
    log "INFO" "检查系统依赖..."
    
    local missing_deps=()
    
    # 检查ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        missing_deps+=("ffmpeg")
        log "ERROR" "FFmpeg未安装"
    else
        log "INFO" "✅ FFmpeg: $(ffmpeg -version 2>/dev/null | head -1 | cut -d' ' -f1-3)"
    fi
    
    # 检查whisper
    if ! python3 -c "import whisper" 2>/dev/null; then
        missing_deps+=("whisper")
        log "ERROR" "Whisper未安装"
    else
        log "INFO" "✅ Whisper: 已安装"
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
        log "ERROR" "Python3未安装"
    else
        log "INFO" "✅ Python3: $(python3 --version)"
    fi
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        log "INFO" "✅ 所有依赖已就绪"
        return 0
    else
        log "ERROR" "缺少依赖: ${missing_deps[*]}"
        return 1
    fi
}

# 安装依赖（如果需要）
install_dependencies() {
    log "INFO" "尝试安装缺少的依赖..."
    
    # 检查系统类型
    if command -v apt-get &> /dev/null; then
        log "INFO" "检测到APT系统"
        
        # 尝试安装ffmpeg（可能需要sudo）
        if ! command -v ffmpeg &> /dev/null; then
            log "WARN" "尝试安装FFmpeg..."
            apt-get install -y ffmpeg 2>/dev/null || log "ERROR" "FFmpeg安装失败（需要sudo）"
        fi
        
        # 尝试安装python3-pip
        if ! command -v pip3 &> /dev/null; then
            log "WARN" "尝试安装pip..."
            apt-get install -y python3-pip 2>/dev/null || log "ERROR" "pip安装失败（需要sudo）"
        fi
    fi
    
    # 安装whisper
    if ! python3 -c "import whisper" 2>/dev/null; then
        log "WARN" "安装Whisper..."
        python3 -m pip install --user openai-whisper 2>&1 | tail -5 >> "$LOG_FILE"
        
        if python3 -c "import whisper" 2>/dev/null; then
            log "INFO" "✅ Whisper安装成功"
        else
            log "ERROR" "Whisper安装失败"
        fi
    fi
    
    # 重新检查依赖
    check_dependencies
}

# 处理音频文件
process_audio_file() {
    local file="$1"
    local filename=$(basename "$file")
    
    log "INFO" "处理音频文件: $filename"
    
    # 创建处理目录
    local process_dir="$PROCESSED_DIR/$(date +%Y%m%d)"
    mkdir -p "$process_dir"
    
    # 复制文件到处理目录
    local temp_file="$process_dir/$filename"
    cp "$file" "$temp_file"
    
    # 使用Python脚本处理
    log "INFO" "开始转录..."
    
    local output_dir="$process_dir/transcriptions"
    mkdir -p "$output_dir"
    
    # 运行转录脚本
    cd /home/goose/.openclaw/workspace
    
    if [ -f "scripts/quick_transcribe.py" ]; then
        python3 scripts/quick_transcribe.py 2>&1 | tee -a "$LOG_FILE"
        
        if [ $? -eq 0 ]; then
            log "INFO" "✅ 转录完成: $filename"
            
            # 移动原始文件到归档
            local archive_dir="$process_dir/archive"
            mkdir -p "$archive_dir"
            mv "$file" "$archive_dir/$filename"
            
            return 0
        else
            log "ERROR" "❌ 转录失败: $filename"
            return 1
        fi
    else
        log "ERROR" "转录脚本不存在"
        return 1
    fi
}

# 监控新文件
monitor_and_process() {
    log "INFO" "开始监控音频目录: $AUDIO_DIR"
    
    # 初始文件列表
    declare -A processed_files
    
    while true; do
        # 检查新文件
        find "$AUDIO_DIR" -type f \( -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" \) | while read file; do
            local filename=$(basename "$file")
            
            # 如果文件未处理过
            if [ -z "${processed_files[$filename]}" ]; then
                log "INFO" "发现新文件: $filename"
                
                # 处理文件
                if process_audio_file "$file"; then
                    processed_files[$filename]=$(date +%s)
                    log "INFO" "文件处理完成: $filename"
                else
                    log "ERROR" "文件处理失败: $filename"
                fi
            fi
        done
        
        # 等待一段时间
        sleep 10
        
        # 检查是否应该退出
        if [ -f "/tmp/stop_audio_processor" ]; then
            log "INFO" "收到停止信号"
            rm -f "/tmp/stop_audio_processor"
            break
        fi
    done
}

# 主函数
main() {
    log "INFO" "自动化音频处理器启动"
    log "INFO" "PID: $$"
    
    # 设置退出时清理
    trap cleanup EXIT
    
    # 检查锁
    if ! check_lock; then
        exit 1
    fi
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$PROCESSED_DIR"
    
    # 检查依赖
    if ! check_dependencies; then
        log "WARN" "依赖不完整，尝试安装..."
        install_dependencies
        
        if ! check_dependencies; then
            log "ERROR" "无法安装所有依赖，退出"
            exit 1
        fi
    fi
    
    # 处理现有文件
    log "INFO" "处理现有音频文件..."
    find "$AUDIO_DIR" -type f \( -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" \) | while read file; do
        process_audio_file "$file"
    done
    
    # 开始监控模式
    log "INFO" "进入监控模式..."
    monitor_and_process
    
    log "INFO" "自动化音频处理器停止"
}

# 运行主函数
main "$@"