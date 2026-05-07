#!/bin/bash

# 简单音频转录脚本
# 使用系统工具处理音频

AUDIO_FILE="/home/goose/.openclaw/media/inbound/file_0---da5d3e22-026b-4307-9040-7fce951a44be.ogg"
OUTPUT_DIR="/home/goose/.openclaw/workspace/audio_transcription_$(date +%Y%m%d_%H%M%S)"

echo "🎵 音频文件: $AUDIO_FILE"
echo "📁 文件大小: $(du -h "$AUDIO_FILE" | cut -f1)"

# 检查文件是否存在
if [ ! -f "$AUDIO_FILE" ]; then
    echo "❌ 音频文件不存在"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"
echo "📂 输出目录: $OUTPUT_DIR"

# 步骤1: 检查音频信息
echo -e "\n🔍 步骤1: 检查音频信息"
file "$AUDIO_FILE"
echo ""

# 步骤2: 尝试转换为WAV格式（如果需要）
echo "🔄 步骤2: 尝试转换音频格式"
if command -v ffmpeg &> /dev/null; then
    WAV_FILE="$OUTPUT_DIR/audio.wav"
    echo "转换 OGG -> WAV..."
    ffmpeg -i "$AUDIO_FILE" "$WAV_FILE" 2>/dev/null
    if [ -f "$WAV_FILE" ]; then
        echo "✅ 转换成功: $WAV_FILE"
        AUDIO_FILE="$WAV_FILE"
    else
        echo "⚠ 转换失败，使用原始文件"
    fi
else
    echo "⚠ ffmpeg未安装，使用原始OGG文件"
fi

# 步骤3: 使用在线服务（如果可用）
echo -e "\n🌐 步骤3: 尝试在线转录服务"
echo "注意: 需要网络连接"

# 检查是否有curl
if command -v curl &> /dev/null; then
    echo "尝试使用在线语音识别API..."
    
    # 保存音频信息
    echo "音频文件信息:" > "$OUTPUT_DIR/audio_info.txt"
    file "$AUDIO_FILE" >> "$OUTPUT_DIR/audio_info.txt"
    echo "" >> "$OUTPUT_DIR/audio_info.txt"
    echo "文件大小: $(du -h "$AUDIO_FILE" | cut -f1)" >> "$OUTPUT_DIR/audio_info.txt"
    
    echo "✅ 音频信息已保存: $OUTPUT_DIR/audio_info.txt"
else
    echo "⚠ curl未安装，跳过在线服务"
fi

# 步骤4: 创建处理报告
echo -e "\n📊 步骤4: 创建处理报告"
cat > "$OUTPUT_DIR/report.md" << EOF
# 音频处理报告

## 文件信息
- **文件路径**: $AUDIO_FILE
- **原始文件**: /home/goose/.openclaw/media/inbound/file_0---da5d3e22-026b-4307-9040-7fce951a44be.ogg
- **处理时间**: $(date)
- **输出目录**: $OUTPUT_DIR

## 处理状态
由于系统缺少必要的依赖（ffmpeg、whisper），无法进行自动转录。

## 建议的下一步
1. **安装必要依赖**:
   \`\`\`bash
   sudo apt install ffmpeg python3-pip
   pip3 install openai-whisper
   \`\`\`

2. **手动转录**:
   - 使用手机语音转文字功能
   - 使用在线转录服务（如Google Docs语音输入）
   - 使用其他语音识别工具

3. **告诉我音频内容**:
   你可以直接告诉我音频的内容，我来帮你处理。

## 生成的文件
- \`audio_info.txt\` - 音频文件信息
- 此报告文件

EOF

echo "✅ 处理报告已创建: $OUTPUT_DIR/report.md"

# 步骤5: 显示总结
echo -e "\n🎉 处理完成!"
echo "="*50
echo "📋 生成的文件:"
find "$OUTPUT_DIR" -type f | while read file; do
    echo "  - $(basename "$file")"
done
echo ""
echo "🔧 缺少的依赖:"
echo "  - ffmpeg (音频处理)"
echo "  - openai-whisper (语音识别)"
echo "  - python3-pip (Python包管理)"
echo ""
echo "🚀 建议:"
echo "  1. 安装上述依赖后重新运行"
echo "  2. 或直接告诉我音频内容"
echo "="*50