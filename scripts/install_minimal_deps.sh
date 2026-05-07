#!/bin/bash

echo "🔧 安装最小化音频处理依赖"
echo "="*50

# 检查当前用户权限
echo "👤 当前用户: $(whoami)"
echo "🔐 权限检查..."

# 尝试安装ffmpeg（可能需要sudo）
echo "📦 尝试安装ffmpeg..."
if command -v apt-get &> /dev/null; then
    echo "检测到APT系统，尝试安装..."
    # 尝试不使用sudo安装到用户目录
    if ! command -v ffmpeg &> /dev/null; then
        echo "FFmpeg未安装，尝试从源码编译..."
        
        # 创建临时目录
        mkdir -p ~/ffmpeg_build
        cd ~/ffmpeg_build
        
        # 下载预编译版本（如果可用）
        echo "尝试下载预编译版本..."
        wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz 2>/dev/null || \
        wget -q https://www.johnvansickle.com/ffmpeg/old-releases/ffmpeg-4.4.1-amd64-static.tar.xz 2>/dev/null
        
        if [ -f *.tar.xz ]; then
            echo "解压预编译版本..."
            tar xf *.tar.xz
            cd ffmpeg-*-static
            cp ffmpeg ffprobe ~/.local/bin/ 2>/dev/null || mkdir -p ~/.local/bin && cp ffmpeg ffprobe ~/.local/bin/
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            source ~/.bashrc
        else
            echo "无法下载预编译版本，需要sudo权限或手动安装"
        fi
    else
        echo "✅ FFmpeg已安装: $(ffmpeg -version | head -1)"
    fi
else
    echo "⚠ 非APT系统，请手动安装FFmpeg"
fi

# 检查Python环境
echo "🐍 检查Python环境..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3已安装: $(python3 --version)"
    
    # 检查pip
    if python3 -m pip --version &> /dev/null; then
        echo "✅ pip已安装"
    else
        echo "尝试安装pip..."
        curl -sS https://bootstrap.pypa.io/get-pip.py | python3
    fi
else
    echo "❌ Python3未安装，尝试安装..."
    # 尝试使用包管理器
    if command -v apt-get &> /dev/null; then
        echo "需要sudo权限安装Python3"
    elif command -v brew &> /dev/null; then
        brew install python@3.11
    else
        echo "请手动安装Python3: https://www.python.org/downloads/"
    fi
fi

# 尝试安装whisper（用户级别）
echo "🎙️ 尝试安装Whisper..."
if python3 -c "import whisper" &> /dev/null; then
    echo "✅ Whisper已安装"
else
    echo "安装Whisper..."
    python3 -m pip install --user openai-whisper 2>/dev/null || \
    echo "安装失败，可能需要网络连接或权限"
fi

# 验证安装
echo ""
echo "✅ 验证安装状态:"
echo "="*50

if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg: 可用"
else
    echo "❌ FFmpeg: 不可用（需要安装）"
fi

if command -v python3 &> /dev/null; then
    echo "✅ Python3: 可用"
else
    echo "❌ Python3: 不可用"
fi

if python3 -c "import whisper" &> /dev/null; then
    echo "✅ Whisper: 可用"
else
    echo "❌ Whisper: 不可用"
fi

echo ""
echo "📋 总结:"
echo "- 如果所有依赖都显示✅，系统已准备好"
echo "- 如果有❌，需要手动安装或提供sudo权限"
echo "- 替代方案：使用在线转录服务或告诉我音频内容"
echo ""
echo "🚀 下一步:"
echo "1. 如果依赖齐全，运行测试脚本"
echo "2. 如果缺少依赖，提供sudo密码或使用替代方案"
echo "3. 直接告诉我音频内容进行处理"