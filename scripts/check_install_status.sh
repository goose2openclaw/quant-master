#!/bin/bash

echo "🔍 安装状态检查"
echo "="*50

# 检查FFmpeg
echo "📦 FFmpeg状态:"
if command -v ffmpeg &> /dev/null; then
    echo "✅ 已安装: $(ffmpeg -version 2>/dev/null | head -1 | cut -d' ' -f1-3)"
    echo "   路径: $(which ffmpeg)"
else
    echo "❌ 未安装"
fi

echo ""

# 检查Python
echo "🐍 Python状态:"
if command -v python3 &> /dev/null; then
    echo "✅ 已安装: $(python3 --version)"
    echo "   路径: $(which python3)"
    
    # 检查pip
    if python3 -m pip --version &> /dev/null 2>/dev/null; then
        echo "✅ pip可用"
    else
        echo "⚠ pip不可用"
    fi
else
    echo "❌ 未安装"
fi

echo ""

# 检查Whisper
echo "🎙️ Whisper状态:"
if timeout 5 python3 -c "import whisper" 2>/dev/null; then
    echo "✅ 已安装"
    
    # 获取版本
    VERSION=$(python3 -c "import whisper; print(whisper.__version__)" 2>/dev/null || echo "未知")
    echo "   版本: $VERSION"
    
    # 测试模型加载
    echo "   测试模型加载..."
    if timeout 10 python3 -c "
import whisper
try:
    model = whisper.load_model('tiny')
    print('    ✅ tiny模型加载成功')
except Exception as e:
    print(f'    ❌ 模型加载失败: {e}')
" 2>/dev/null; then
        echo "    ✅ 模型加载测试通过"
    else
        echo "    ⚠ 模型加载测试超时或失败"
    fi
else
    echo "❌ 未安装 或 正在安装中"
    
    # 检查安装进程
    echo "   检查安装进程..."
    if ps aux | grep -v grep | grep -q "pip install.*whisper"; then
        echo "    🔄 Whisper正在安装中..."
        echo "    请等待安装完成（可能需要几分钟）"
    else
        echo "    ⚠ 未检测到安装进程"
        echo "    建议运行: python3 -m pip install --user openai-whisper"
    fi
fi

echo ""

# 检查音频文件
echo "📁 音频文件状态:"
AUDIO_DIR="/home/goose/.openclaw/media/inbound"
if [ -d "$AUDIO_DIR" ]; then
    COUNT=$(find "$AUDIO_DIR" -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" | wc -l)
    echo "✅ 目录存在: $AUDIO_DIR"
    echo "   文件数量: $COUNT"
    
    if [ $COUNT -gt 0 ]; then
        echo "   文件列表:"
        find "$AUDIO_DIR" -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" | while read file; do
            echo "     - $(basename "$file") ($(du -h "$file" | cut -f1))"
        done
    fi
else
    echo "❌ 目录不存在"
fi

echo ""
echo "📋 系统准备状态:"
echo "="*50

READY=true

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg: 缺失"
    READY=false
else
    echo "✅ FFmpeg: 就绪"
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3: 缺失"
    READY=false
else
    echo "✅ Python3: 就绪"
fi

if ! timeout 5 python3 -c "import whisper" 2>/dev/null; then
    echo "❌ Whisper: 缺失"
    READY=false
else
    echo "✅ Whisper: 就绪"
fi

echo ""
if $READY; then
    echo "🎉 系统已准备就绪!"
    echo "🚀 可以运行音频处理:"
    echo "   cd /home/goose/.openclaw/workspace"
    echo "   python3 scripts/quick_transcribe.py"
    echo "   或"
    echo "   ./scripts/auto_audio_processor.sh"
else
    echo "⚠ 系统未就绪，缺少依赖"
    echo "🔧 建议操作:"
    
    if ! command -v ffmpeg &> /dev/null; then
        echo "   1. 安装FFmpeg: sudo apt install ffmpeg"
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "   2. 安装Python3: sudo apt install python3 python3-pip"
    fi
    
    if ! timeout 5 python3 -c "import whisper" 2>/dev/null; then
        echo "   3. 安装Whisper: python3 -m pip install --user openai-whisper"
    fi
    
    echo ""
    echo "📝 或者，可以直接告诉我音频内容，我来帮你处理"
fi

echo ""
echo "⏰ 当前时间: $(date)"
echo "🔄 最后检查: 请等待Whisper安装完成"