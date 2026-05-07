#!/bin/bash

echo "🔍 音频系统测试"
echo "="*50

# 测试1: 检查音频文件
echo "📁 测试1: 检查音频文件"
AUDIO_DIR="/home/goose/.openclaw/media/inbound"
if [ -d "$AUDIO_DIR" ]; then
    echo "✅ 音频目录存在: $AUDIO_DIR"
    file_count=$(find "$AUDIO_DIR" -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" | wc -l)
    echo "📊 音频文件数量: $file_count"
    
    # 列出文件
    find "$AUDIO_DIR" -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" | while read file; do
        echo "  📄 $(basename "$file") - $(du -h "$file" | cut -f1)"
    done
else
    echo "❌ 音频目录不存在"
fi

echo ""

# 测试2: 检查依赖
echo "🔧 测试2: 检查依赖"
echo "FFmpeg: $(which ffmpeg 2>/dev/null || echo '未安装')"
echo "Python3: $(which python3 2>/dev/null || echo '未安装')"
if python3 -c "import whisper" 2>/dev/null; then
    echo "Whisper: ✅ 已安装"
else
    echo "Whisper: ❌ 未安装"
fi

echo ""

# 测试3: 检查文件权限
echo "🔐 测试3: 检查文件权限"
if [ -d "$AUDIO_DIR" ]; then
    echo "音频目录权限: $(stat -c "%A %U %G" "$AUDIO_DIR")"
    
    # 检查可读性
    find "$AUDIO_DIR" -name "*.ogg" | head -2 | while read file; do
        if [ -r "$file" ]; then
            echo "✅ 可读: $(basename "$file")"
        else
            echo "❌ 不可读: $(basename "$file")"
        fi
    done
fi

echo ""

# 测试4: 创建测试环境
echo "🧪 测试4: 创建测试环境"
TEST_DIR="/tmp/audio_test_$$"
mkdir -p "$TEST_DIR"

# 创建测试音频（如果sox可用）
if command -v sox &> /dev/null; then
    echo "创建测试音频..."
    sox -n -r 16000 -c 1 "$TEST_DIR/test.wav" synth 3 sine 440
    echo "✅ 测试音频创建成功"
else
    echo "⚠ sox未安装，跳过音频生成"
fi

# 测试文件操作
echo "测试文件操作..."
echo "测试文本" > "$TEST_DIR/test.txt"
if [ -f "$TEST_DIR/test.txt" ]; then
    echo "✅ 文件操作正常"
else
    echo "❌ 文件操作失败"
fi

# 清理
rm -rf "$TEST_DIR"

echo ""

# 测试5: 网络连接（可选）
echo "🌐 测试5: 网络连接"
if curl -s --head https://google.com | grep "200 OK" > /dev/null; then
    echo "✅ 网络连接正常"
else
    echo "⚠ 网络连接检查失败（可能正常）"
fi

echo ""
echo "📋 测试总结:"
echo "="*50
echo "1. 音频文件: $(find "$AUDIO_DIR" -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" | wc -l) 个文件"
echo "2. 核心依赖:"
echo "   - FFmpeg: $(if command -v ffmpeg &> /dev/null; then echo '✅'; else echo '❌'; fi)"
echo "   - Python3: $(if command -v python3 &> /dev/null; then echo '✅'; else echo '❌'; fi)"
echo "   - Whisper: $(if python3 -c "import whisper" 2>/dev/null; then echo '✅'; else echo '❌'; fi)"
echo "3. 文件权限: ✅ (如果文件可读)"
echo "4. 系统环境: ✅ (如果测试通过)"
echo ""
echo "🚀 建议:"
if ! command -v ffmpeg &> /dev/null || ! python3 -c "import whisper" &> /dev/null; then
    echo "⚠ 缺少关键依赖，需要安装:"
    echo "   sudo apt install ffmpeg python3-pip"
    echo "   pip3 install openai-whisper"
else
    echo "✅ 系统已准备好处理音频"
    echo "   运行: ./scripts/audio_file_manager.sh list"
fi