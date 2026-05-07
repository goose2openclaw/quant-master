#!/bin/bash

# 视频文件语音转录脚本
# 支持MP4视频文件，自动提取音频并转录音频内容

echo "=== 视频文件语音转录 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: $0 <视频文件路径>"
    echo "示例: $0 /path/to/video.mp4"
    exit 1
fi

VIDEO_FILE="$1"

# 检查文件是否存在
if [ ! -f "$VIDEO_FILE" ]; then
    echo "❌ 错误: 文件不存在: $VIDEO_FILE"
    exit 1
fi

echo "📹 处理视频文件: $VIDEO_FILE"
echo ""

# 创建临时工作目录
WORK_DIR="/tmp/video_analysis_$(date +%s)_$$"
mkdir -p "$WORK_DIR"
echo "📁 工作目录: $WORK_DIR"
echo ""

# 1. 分析视频文件
echo "1. 🔍 分析视频文件信息..."
VIDEO_INFO="$WORK_DIR/video_info.txt"
ffprobe -v error -show_format -show_streams "$VIDEO_FILE" > "$VIDEO_INFO" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "   ❌ 无法分析视频文件"
    rm -rf "$WORK_DIR"
    exit 1
fi

# 提取关键信息
DURATION=$(grep "duration=" "$VIDEO_INFO" | head -1 | cut -d'=' -f2)
WIDTH=$(grep "width=" "$VIDEO_INFO" | head -1 | cut -d'=' -f2)
HEIGHT=$(grep "height=" "$VIDEO_INFO" | head -1 | cut -d'=' -f2)
VIDEO_CODEC=$(grep "codec_name=" "$VIDEO_INFO" | head -1 | cut -d'=' -f2)
AUDIO_CODEC=$(grep "codec_name=" "$VIDEO_INFO" | tail -1 | cut -d'=' -f2)

echo "   ⏱️ 时长: ${DURATION:-未知} 秒"
echo "   🖼️ 分辨率: ${WIDTH:-未知}×${HEIGHT:-未知}"
echo "   🎬 视频编码: ${VIDEO_CODEC:-未知}"
echo "   🎵 音频编码: ${AUDIO_CODEC:-未知}"
echo ""

# 2. 提取音频
echo "2. 🎵 提取音频..."
AUDIO_FILE="$WORK_DIR/audio.wav"
echo "   提取音频到: $AUDIO_FILE"

ffmpeg -i "$VIDEO_FILE" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$AUDIO_FILE" 2>/dev/null

if [ ! -f "$AUDIO_FILE" ] || [ ! -s "$AUDIO_FILE" ]; then
    echo "   ❌ 音频提取失败"
    echo "   ℹ️ 可能原因: 视频没有音频轨道，或格式不支持"
    rm -rf "$WORK_DIR"
    exit 1
fi

AUDIO_SIZE=$(ls -lh "$AUDIO_FILE" | awk '{print $5}')
echo "   ✅ 音频提取成功: $AUDIO_SIZE"
echo ""

# 3. 转录音频
echo "3. 🎤 语音识别..."
echo "   使用Google Web Speech API进行中文识别..."

# 使用Python脚本进行转录
cd /home/goose/.openclaw/workspace
TRANSCRIPTION=$(python3 -c "
import speech_recognition as sr
import sys

try:
    recognizer = sr.Recognizer()
    with sr.AudioFile('$AUDIO_FILE') as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language='zh-CN')
        print(text)
except sr.UnknownValueError:
    print('无法理解音频内容')
except sr.RequestError as e:
    print(f'识别服务错误: {e}')
except Exception as e:
    print(f'处理错误: {e}')
")

if [ -z "$TRANSCRIPTION" ] || [[ "$TRANSCRIPTION" == *"错误"* ]] || [[ "$TRANSCRIPTION" == *"无法"* ]]; then
    echo "   ❌ 语音识别失败"
    echo "   识别结果: $TRANSCRIPTION"
else
    echo "   ✅ 识别成功"
    echo ""
    echo "========================================"
    echo "📝 转录结果:"
    echo "========================================"
    echo "$TRANSCRIPTION"
    echo "========================================"
    echo ""
    
    # 保存结果
    echo "$TRANSCRIPTION" > "$WORK_DIR/transcription.txt"
    echo "📄 结果已保存到: $WORK_DIR/transcription.txt"
fi

echo ""

# 4. 安全相关关键词检查
echo "4. 🛡️ 安全关键词检查..."
SECURITY_KEYWORDS="安全 危险 警告 紧急 帮助 救命 报警 危险 威胁"

FOUND_KEYWORDS=""
for keyword in $SECURITY_KEYWORDS; do
    if echo "$TRANSCRIPTION" | grep -q "$keyword"; then
        FOUND_KEYWORDS="$FOUND_KEYWORDS '$keyword'"
    fi
done

if [ -n "$FOUND_KEYWORDS" ]; then
    echo "   ⚠️ 发现安全相关关键词: $FOUND_KEYWORDS"
    echo "   ℹ️ 建议: 关注此内容的安全性"
    
    # 记录安全事件
    SECURITY_LOG="/tmp/openclaw_security_events.log"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 视频分析发现安全关键词: $FOUND_KEYWORDS - 转录: $TRANSCRIPTION" >> "$SECURITY_LOG"
    echo "   📋 安全事件已记录到: $SECURITY_LOG"
else
    echo "   ✅ 未发现安全相关关键词"
fi

echo ""

# 5. 清理和总结
echo "5. 🧹 清理临时文件..."
# 保留工作目录供调试，实际使用时可取消注释下一行
# rm -rf "$WORK_DIR"

echo ""
echo "=== 处理完成 ==="
echo "📊 处理总结:"
echo "   视频文件: $(basename "$VIDEO_FILE")"
echo "   视频时长: ${DURATION:-未知}秒"
echo "   分辨率: ${WIDTH:-未知}×${HEIGHT:-未知}"
echo "   转录结果: ${TRANSCRIPTION:-无}"
echo "   工作目录: $WORK_DIR (临时文件)"
echo ""
echo "🔧 后续操作建议:"
if [[ "$TRANSCRIPTION" == *"安全"* ]]; then
    echo "   检测到'安全'关键词，建议:"
    echo "   1. 运行系统安全检查: bash /home/goose/.openclaw/workspace/scripts/test_telegram_response.sh"
    echo "   2. 查看安全日志: tail -f /tmp/openclaw_security_events.log"
    echo "   3. 使用安全技能: secure-code-guardian, healthcheck"
elif [ -n "$TRANSCRIPTION" ]; then
    echo "   根据转录内容 '$TRANSCRIPTION' 执行相应操作"
else
    echo "   未识别到有效内容，可能是测试视频或环境噪音"
fi

echo ""
echo "✅ 脚本执行完成"